"""
Chat interface component for PM Service application.

Handles message display, input, and session state management.
"""

import streamlit as st
from server import ConversationManager, ChatStorageManager


def render_chat_interface():
    """
    Render the chat interface with message history and input.

    Manages chat messages in session state for persistence.
    """
    # Initialize storage manager
    storage_manager = ChatStorageManager()

    # Initialize AI components in session state if not exists
    if "conversation_manager" not in st.session_state:
        st.session_state.conversation_manager = ConversationManager()

    # Get active chat
    active_chat = storage_manager.get_active_chat()

    if not active_chat:
        # No active chat - show empty state
        _render_empty_state()
        return

    # Display active chat info
    st.markdown(f"### 💬 {active_chat.name}")

    # Category badge
    category_emoji = {
        "Lease & Contracts": "📄",
        "Maintenance & Repairs": "🔧",
        "Tenant Communications": "💬",
    }.get(active_chat.category, "📋")

    st.info(f"{category_emoji} **{active_chat.category}**")

    # Display chat messages
    for message in active_chat.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # AI Mode Selection Pills (above chat input)
    ai_mode = st.pills(
        "PM Action",
        ["♾️ Ask", "📋 Plan", "✉️ Draft"],
        selection_mode="single",
        default="♾️ Ask",
        key=f"ai_mode_{active_chat.id}",
    )

    # Store AI mode in session state
    st.session_state.ai_mode = ai_mode

    # Chat input
    if prompt := st.chat_input("Ask me about property management..."):
        # Add user message to chat instance
        user_message = {"role": "user", "content": prompt}
        storage_manager.add_message(active_chat.id, user_message)

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate assistant response using LangChain
        with st.chat_message("assistant"):
            # Show loading spinner while AI processes
            with st.spinner(""):
                # Get AI response with conversation context and work category specialization
                response = st.session_state.conversation_manager.get_response(
                    user_input=prompt,
                    work_category=active_chat.category,
                    session_id=active_chat.id,  # Use chat ID as session ID
                    conversation_history=active_chat.messages,  # Pass conversation history for workflow analysis
                    ai_mode=st.session_state.ai_mode,  # Pass selected AI mode
                )

            st.markdown(response)

        # Add assistant response to chat instance
        assistant_message = {"role": "assistant", "content": response}
        storage_manager.add_message(active_chat.id, assistant_message)
        st.rerun()


def _render_empty_state():
    """
    Render empty state when no chat is active.
    """
    st.markdown("### Welcome!")

    st.markdown(
        """
        Get started by creating a new conversation to discuss your property management needs.
        
        **Available Work Categories:**
        - 📄 **Lease & Contracts** - Document analysis and review
        - 🔧 **Maintenance & Repairs** - Work orders and facility management  
        - 💬 **Tenant Communications** - Professional messaging and notices
        """
    )

    # Show some example prompts
    st.markdown("### Examples")

    st.markdown(
        """
        Get started by creating a new conversation to discuss your property management needs.
        
        **Available Work Categories:**
        - Help me review this lease agreement for potential issues
        - Draft a maintenance request template for tenants 
        - Create a professional notice about upcoming building maintenance
        
        Click the **"New Conversation"** button in the sidebar to begin!
        """
    )
