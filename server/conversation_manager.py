"""
Conversation manager for property management AI assistant.

Handles conversation flow with memory using LangChain v1.0 LCEL approach.
"""

from langchain_core.messages import HumanMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from typing import List
from .config import get_gemini_llm, initialize_langsmith_tracing
from .prompts import (
    get_email_generation_prompt,
    get_chat_prompt,
    get_action_plan_prompt,
    get_questions_prompt,
)
from .telemetry_manager import get_telemetry_collector
from typing import Dict, List
from pydantic import BaseModel, Field
import time


class InMemoryChatMessageHistory(BaseChatMessageHistory, BaseModel):
    """Simple in-memory chat message history for session management."""

    messages: List[BaseMessage] = Field(default_factory=list)

    def add_messages(self, messages: List[BaseMessage]) -> None:
        """Add a list of messages to the history."""
        self.messages.extend(messages)

    def clear(self) -> None:
        """Clear all messages from history."""
        self.messages = []


class ConversationManager:
    """
    Manages AI conversations with memory for property management tasks.

    Uses LangChain v1.0 LCEL approach with RunnableWithMessageHistory.
    """

    def __init__(self):
        """Initialize conversation manager with Gemini LLM and memory."""
        self.llm = get_gemini_llm()
        self.session_store: Dict[str, InMemoryChatMessageHistory] = {}
        self.telemetry_collector = get_telemetry_collector()

        # Initialize LangSmith tracing
        initialize_langsmith_tracing()

        # Create the prompt template with message history
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "{system_prompt}"),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}"),
            ]
        )

        # Create the chain
        self.chain = self.prompt | self.llm

    def _get_session_history(self, session_id: str) -> InMemoryChatMessageHistory:
        """Get or create session history."""
        if session_id not in self.session_store:
            self.session_store[session_id] = InMemoryChatMessageHistory()
        return self.session_store[session_id]

    def get_response(
        self,
        user_input: str,
        work_category: str = "Lease & Contracts",
        session_id: str = "default",
        conversation_history: List[Dict] = None,
        ai_mode: str = "💬 Chat",
    ) -> str:
        """
        Generate AI response with conversation context and work category specialization.

        Args:
            user_input (str): User's message
            work_category (str): Selected work category
            session_id (str): Session identifier for memory
            conversation_history (List[Dict]): Optional conversation history for workflow analysis

        Returns:
            str: AI assistant's response
        """
        # Get conversation history from session if not provided
        if conversation_history is None:
            session_history = self._get_session_history(session_id)
            conversation_history = [
                {
                    "role": "user" if isinstance(msg, HumanMessage) else "assistant",
                    "content": msg.content,
                }
                for msg in session_history.messages
            ]

        # Check if user wants email generation
        # Determine prompt based on AI mode
        if ai_mode == "✉️ Draft":
            contextual_prompt = get_email_generation_prompt(
                work_category, conversation_history
            )
        elif ai_mode == "📋 Plan":
            contextual_prompt = get_action_plan_prompt(
                work_category, conversation_history
            )
        elif ai_mode == "❓ Ask":
            contextual_prompt = get_questions_prompt(
                work_category, conversation_history
            )
        else:  # Default to Chat mode
            contextual_prompt = get_chat_prompt(work_category, conversation_history)

        # Start timing for telemetry
        start_time = time.time()

        try:
            # Create the chain with message history
            chain_with_history = RunnableWithMessageHistory(
                self.chain,
                self._get_session_history,
                input_messages_key="input",
                history_messages_key="history",
            )

            # Prepare input for the chain
            chain_input = {"system_prompt": contextual_prompt, "input": user_input}

            # Invoke the chain
            response = chain_with_history.invoke(
                chain_input,
                config={"configurable": {"session_id": session_id}},
            )

            # Calculate latency
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000

            # Track successful telemetry event
            self.telemetry_collector.track_event(
                chat_id=session_id,
                category=work_category,
                ai_mode=ai_mode,
                latency_ms=latency_ms,
                input_text=user_input,
                response_text=response.content,
                model_name=getattr(self.llm, "model", "gemini-flash-latest"),
                status="success",
            )

            return response.content

        except Exception as e:
            # Calculate latency for error case
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000

            # Track error telemetry event
            self.telemetry_collector.track_event(
                chat_id=session_id,
                category=work_category,
                ai_mode=ai_mode,
                latency_ms=latency_ms,
                input_text=user_input,
                response_text="",
                model_name=getattr(self.llm, "model", "gemini-flash-latest"),
                status="error",
                error_message=str(e),
            )

            return f"I apologize, but I encountered an error processing your request: {str(e)}. Please try again."

    def clear_memory(self, session_id: str = "default"):
        """Clear conversation memory for a specific session."""
        if session_id in self.session_store:
            self.session_store[session_id].clear()

    def get_memory_summary(self, session_id: str = "default") -> str:
        """
        Get a summary of the conversation history for a session.

        Returns:
            str: Summary of conversation context
        """
        if session_id not in self.session_store:
            return "No conversation history yet."

        session_history = self.session_store[session_id]
        if not session_history.messages:
            return "No conversation history yet."

        # Get recent messages for context
        recent_messages = session_history.messages[-4:]  # Last 4 messages
        summary = "Recent conversation context:\n"
        for msg in recent_messages:
            role = "User" if isinstance(msg, HumanMessage) else "Assistant"
            content = msg.content[:100] if hasattr(msg, "content") else str(msg)[:100]
            summary += f"{role}: {content}...\n"

        return summary
