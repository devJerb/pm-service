"""
Chat instance storage management for PM Service application.

Handles chat instance data with Supabase PostgreSQL database storage.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import streamlit as st
from .supabase_client import get_supabase_client


@dataclass
class ChatInstance:
    """Data model for chat instances."""

    id: str
    name: str
    category: str
    messages: List[Dict]
    created_at: datetime
    updated_at: datetime
    workflow_phase: str = "assessment"  # Current workflow step
    email_drafts: List[Dict] = None  # Store generated email drafts
    action_plans: List[Dict] = None  # Store generated action plans

    def __post_init__(self):
        """Initialize default values for mutable fields."""
        if self.email_drafts is None:
            self.email_drafts = []
        if self.action_plans is None:
            self.action_plans = []

    def to_dict(self) -> Dict:
        """Convert to dictionary for database storage."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "ChatInstance":
        """Create instance from dictionary."""
        return cls(**data)


class ChatStorageManager:
    """
    Manages chat instances using Supabase PostgreSQL database.

    Provides persistent storage for chat instances, messages, and related data.
    """

    def __init__(self):
        """Initialize storage manager."""
        self.supabase = get_supabase_client()
        self._ensure_session_state()

    def _ensure_session_state(self):
        """Ensure required session state variables exist for UI state."""
        if "active_chat_id" not in st.session_state:
            st.session_state.active_chat_id = None

        if "category_filter" not in st.session_state:
            st.session_state.category_filter = None

    def create_chat(self, name: str, category: str) -> str:
        """
        Create a new chat instance.

        Args:
            name: User-provided chat name
            category: Work category for the chat

        Returns:
            str: Generated chat ID
        """
        try:
            # Insert chat instance into database
            # If authenticated, pass user_id; RLS will also enforce WITH CHECK
            user_id = None
            try:
                if st.session_state.get("sb_session") and st.session_state["sb_session"].get("user"):
                    user_id = st.session_state["sb_session"]["user"].get("id")
            except Exception:
                pass

            payload = {
                "name": name,
                "category": category,
                "workflow_phase": "assessment",
            }
            if user_id:
                payload["user_id"] = user_id

            result = self.supabase.table("chat_instances").insert(payload).execute()

            if not result.data:
                raise Exception("Failed to create chat instance")

            chat_id = result.data[0]["id"]

            # Set as active chat if it's the first one
            if st.session_state.active_chat_id is None:
                st.session_state.active_chat_id = chat_id

            return chat_id

        except Exception as e:
            st.error(f"Failed to create chat: {str(e)}")
            raise

    def get_chat(self, chat_id: str) -> Optional[ChatInstance]:
        """
        Get a chat instance by ID.

        Args:
            chat_id: Chat instance ID

        Returns:
            Optional[ChatInstance]: Chat instance or None if not found
        """
        try:
            # Get chat instance
            chat_result = self.supabase.table("chat_instances").select("*").eq("id", chat_id).execute()
            
            if not chat_result.data:
                return None

            chat_data = chat_result.data[0]

            # Get messages for this chat
            messages_result = self.supabase.table("chat_messages").select("*").eq("chat_id", chat_id).order("created_at").execute()
            messages = [{"role": msg["role"], "content": msg["content"]} for msg in messages_result.data]

            # Get email drafts
            drafts_result = self.supabase.table("email_drafts").select("*").eq("chat_id", chat_id).order("created_at").execute()
            email_drafts = [{"subject": draft["subject"], "recipient": draft["recipient"], "body": draft["body"], "metadata": draft["metadata"]} for draft in drafts_result.data]

            # Get action plans
            plans_result = self.supabase.table("action_plans").select("*").eq("chat_id", chat_id).order("created_at").execute()
            action_plans = [{"title": plan["title"], "checklist": plan["checklist"], "key_considerations": plan["key_considerations"]} for plan in plans_result.data]

            return ChatInstance(
                id=chat_data["id"],
                name=chat_data["name"],
                category=chat_data["category"],
                messages=messages,
                created_at=datetime.fromisoformat(chat_data["created_at"].replace('Z', '+00:00')),
                updated_at=datetime.fromisoformat(chat_data["updated_at"].replace('Z', '+00:00')),
                workflow_phase=chat_data["workflow_phase"],
                email_drafts=email_drafts,
                action_plans=action_plans
            )

        except Exception as e:
            st.error(f"Failed to get chat: {str(e)}")
            return None

    def update_chat(self, chat_id: str, **kwargs) -> bool:
        """
        Update a chat instance.

        Args:
            chat_id: Chat instance ID
            **kwargs: Fields to update

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Only update allowed fields
            allowed_fields = ["name", "category", "workflow_phase"]
            update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}

            if not update_data:
                return True

            result = self.supabase.table("chat_instances").update(update_data).eq("id", chat_id).execute()
            return bool(result.data)

        except Exception as e:
            st.error(f"Failed to update chat: {str(e)}")
            return False

    def delete_chat(self, chat_id: str) -> bool:
        """
        Delete a chat instance and all related data.

        Args:
            chat_id: Chat instance ID

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Delete chat instance (CASCADE will handle related records)
            result = self.supabase.table("chat_instances").delete().eq("id", chat_id).execute()
            
            # Clear active chat if it was deleted
            if st.session_state.active_chat_id == chat_id:
                st.session_state.active_chat_id = None

            return bool(result.data)

        except Exception as e:
            st.error(f"Failed to delete chat: {str(e)}")
            return False

    def get_all_chats(self) -> List[ChatInstance]:
        """
        Get all chat instances.

        Returns:
            List[ChatInstance]: List of all chat instances
        """
        try:
            result = self.supabase.table("chat_instances").select("*").order("created_at", desc=True).execute()
            
            chats = []
            for chat_data in result.data:
                # Get message count for each chat
                messages_result = self.supabase.table("chat_messages").select("id").eq("chat_id", chat_data["id"]).execute()
                message_count = len(messages_result.data)

                chat = ChatInstance(
                    id=chat_data["id"],
                    name=chat_data["name"],
                    category=chat_data["category"],
                    messages=[],  # Don't load all messages for list view
                    created_at=datetime.fromisoformat(chat_data["created_at"].replace('Z', '+00:00')),
                    updated_at=datetime.fromisoformat(chat_data["updated_at"].replace('Z', '+00:00')),
                    workflow_phase=chat_data["workflow_phase"],
                    email_drafts=[],
                    action_plans=[]
                )
                chats.append(chat)

            return chats

        except Exception as e:
            st.error(f"Failed to get all chats: {str(e)}")
            return []

    def get_filtered_chats(self) -> List[ChatInstance]:
        """
        Get chat instances filtered by category.

        Returns:
            List[ChatInstance]: List of filtered chat instances
        """
        try:
            query = self.supabase.table("chat_instances").select("*").order("created_at", desc=True)
            
            # Apply category filter if set
            if st.session_state.category_filter:
                query = query.eq("category", st.session_state.category_filter)

            result = query.execute()
            
            chats = []
            for chat_data in result.data:
                chat = ChatInstance(
                    id=chat_data["id"],
                    name=chat_data["name"],
                    category=chat_data["category"],
                    messages=[],  # Don't load all messages for list view
                    created_at=datetime.fromisoformat(chat_data["created_at"].replace('Z', '+00:00')),
                    updated_at=datetime.fromisoformat(chat_data["updated_at"].replace('Z', '+00:00')),
                    workflow_phase=chat_data["workflow_phase"],
                    email_drafts=[],
                    action_plans=[]
                )
                chats.append(chat)

            return chats

        except Exception as e:
            st.error(f"Failed to get filtered chats: {str(e)}")
            return []

    def set_active_chat(self, chat_id: str) -> bool:
        """
        Set the active chat instance.

        Args:
            chat_id: Chat instance ID

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Verify chat exists
            chat = self.get_chat(chat_id)
            if chat:
                st.session_state.active_chat_id = chat_id
                return True
            return False

        except Exception as e:
            st.error(f"Failed to set active chat: {str(e)}")
            return False

    def get_active_chat(self) -> Optional[ChatInstance]:
        """
        Get the currently active chat instance.

        Returns:
            Optional[ChatInstance]: Active chat instance or None
        """
        if not st.session_state.active_chat_id:
            return None

        return self.get_chat(st.session_state.active_chat_id)

    def add_message(self, chat_id: str, message: Dict) -> bool:
        """
        Add a message to a chat instance.

        Args:
            chat_id: Chat instance ID
            message: Message dictionary with 'role' and 'content'

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            result = self.supabase.table("chat_messages").insert({
                "chat_id": chat_id,
                "role": message["role"],
                "content": message["content"]
            }).execute()

            return bool(result.data)

        except Exception as e:
            st.error(f"Failed to add message: {str(e)}")
            return False

    def clear_chat_messages(self, chat_id: str) -> bool:
        """
        Clear all messages from a chat instance.

        Args:
            chat_id: Chat instance ID

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            result = self.supabase.table("chat_messages").delete().eq("chat_id", chat_id).execute()
            return True

        except Exception as e:
            st.error(f"Failed to clear messages: {str(e)}")
            return False

    def add_email_draft(self, chat_id: str, subject: str, recipient: str, body: str, metadata: Dict = None) -> bool:
        """
        Add an email draft to a chat instance.

        Args:
            chat_id: Chat instance ID
            subject: Email subject
            recipient: Email recipient
            body: Email body
            metadata: Additional metadata

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            result = self.supabase.table("email_drafts").insert({
                "chat_id": chat_id,
                "subject": subject,
                "recipient": recipient,
                "body": body,
                "metadata": metadata or {}
            }).execute()

            return bool(result.data)

        except Exception as e:
            st.error(f"Failed to add email draft: {str(e)}")
            return False

    def add_action_plan(self, chat_id: str, title: str, checklist: List, key_considerations: List = None) -> bool:
        """
        Add an action plan to a chat instance.

        Args:
            chat_id: Chat instance ID
            title: Action plan title
            checklist: List of checklist items
            key_considerations: List of key considerations

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            result = self.supabase.table("action_plans").insert({
                "chat_id": chat_id,
                "title": title,
                "checklist": checklist,
                "key_considerations": key_considerations or []
            }).execute()

            return bool(result.data)

        except Exception as e:
            st.error(f"Failed to add action plan: {str(e)}")
            return False