"""
Sidebar component for PM Service application.

Provides navigation, settings, and chat management options.
"""

import streamlit as st
from server import ChatStorageManager


def render_sidebar():
    """
    Render the sidebar with navigation and settings.

    Returns:
        dict: User selections and configurations
    """
    with st.sidebar:
        st.header("PM Tools")

        # App information
        st.markdown(
            """
        Start a new conversation to discuss your property management needs.
        """
        )

        # New Chat Button
        if st.button("New Conversation", width="stretch", type="secondary"):
            from .chat_dialog import render_new_chat_dialog

            render_new_chat_dialog()

        # Conversations
        st.subheader("Conversation History")

        # Initialize storage manager
        storage_manager = ChatStorageManager()

        # Category Filter
        category_filter = st.selectbox(
            "Filter by Category",
            [
                "All",
                "Lease & Contracts",
                "Maintenance & Repairs",
                "Tenant Communications",
            ],
            help="Filter chats by work category",
            key="sidebar_category_filter",
        )

        # Update session state filter
        if category_filter == "All":
            st.session_state.category_filter = None
        else:
            st.session_state.category_filter = category_filter

        # Get filtered chats
        filtered_chats = storage_manager.get_filtered_chats()

        if not filtered_chats:
            st.info("No conversations yet.")
        else:
            # Display chat instances
            for chat in filtered_chats:
                _render_chat_item(chat, storage_manager)

        st.divider()

        # Telemetry Section (always visible, collapsed)
        st.subheader("📊 Analytics")

        show_telemetry_data()

        st.divider()

        # Clear History Button
        st.subheader("🗑️ Actions")

        active_chat = storage_manager.get_active_chat()
        if active_chat:
            # Truncate chat name for clear history button
            clear_name = (
                active_chat.name[:20] + "..."
                if len(active_chat.name) > 20
                else active_chat.name
            )
            if st.button(
                f"Clear '{clear_name}' History",
                help="Clear messages from current chat",
                width="stretch",
            ):
                storage_manager.clear_chat_messages(active_chat.id)
                st.rerun()
        else:
            st.button(
                "Clear History",
                help="No active chat to clear",
                width="stretch",
                disabled=True,
            )

    return {"work_category": "Dynamic per chat"}


def _render_chat_item(chat, storage_manager):
    """
    Render a single chat item in the sidebar.

    Args:
        chat: ChatInstance object
        storage_manager: ChatStorageManager instance
    """
    active_chat = storage_manager.get_active_chat()
    is_active = active_chat and active_chat.id == chat.id

    # Truncate chat name to prevent wrapping
    display_name = chat.name[:25] + "..." if len(chat.name) > 25 else chat.name

    # Chat container with clean styling
    with st.container():
        if is_active:
            # Active chat styling
            st.markdown(f"📌 **{display_name}**")
        else:
            # Inactive chat styling
            if st.button(
                display_name,
                key=f"chat_select_{chat.id}",
                help=f"Switch to {chat.name}",
                use_container_width=True,
            ):
                storage_manager.set_active_chat(chat.id)
                st.rerun()


def show_telemetry_data():
    """
    Display telemetry data in a collapsed expander format.
    """
    with st.expander("📈 Telemetry Data", expanded=False):
        st.markdown("### Usage Analytics")

        # Mock telemetry data
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Messages Sent", "47", "12")
            st.metric("Sessions Today", "3", "1")

        with col2:
            st.metric("Avg Response Time", "2.3s", "-0.5s")
            st.metric("Success Rate", "98.5%", "2.1%")

        st.markdown("### Recent Activity")

        # Mock activity data
        activity_data = {
            "Time": ["10:30 AM", "10:15 AM", "10:00 AM", "9:45 AM"],
            "Action": [
                "Chat Message",
                "Agent Changed",
                "Category Selected",
                "History Cleared",
            ],
            "Details": [
                "Asked about lease terms",
                "Switched to Task Manager",
                "Property Maintenance",
                "Cleared 5 messages",
            ],
        }

        import pandas as pd

        df = pd.DataFrame(activity_data)
        st.dataframe(df, width="stretch", hide_index=True)

        st.markdown("### Performance Metrics")

        # Mock performance chart data
        chart_data = pd.DataFrame(
            {
                "Hour": range(9, 12),
                "Messages": [5, 8, 12],
                "Response Time (s)": [2.1, 2.3, 2.0],
            }
        )

        st.line_chart(chart_data.set_index("Hour"))
