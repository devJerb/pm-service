"""
Sidebar component for PM Service application.

Provides navigation, settings, and chat management options.
"""

import streamlit as st
import pandas as pd
from server import ChatStorageManager
from server.telemetry_manager import get_telemetry_collector
from .chat_edit_dialog import render_edit_chat_dialog


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
        left_col, right_col = st.columns([0.85, 0.15])

        with left_col:
            if is_active:
                # Active chat styling
                st.markdown(f"📌 **{display_name}**")
            else:
                # Inactive chat styling
                if st.button(
                    display_name,
                    key=f"chat_select_{chat.id}",
                    help=f"Switch to {chat.name}",
                    width="stretch",
                ):
                    storage_manager.set_active_chat(chat.id)
                    st.rerun()

        with right_col:
            if st.button(
                "✏️",
                key=f"chat_edit_{chat.id}",
                help="Edit conversation",
                width="stretch",
            ):
                st.session_state.edit_chat_id = chat.id
                render_edit_chat_dialog()


def show_telemetry_data():
    """
    Display real telemetry data in a collapsed expander format.
    """
    with st.expander("📈 Telemetry Data", expanded=False):
        try:
            # Get telemetry collector
            telemetry_collector = get_telemetry_collector()
            
            # Get session metrics
            metrics = telemetry_collector.get_session_metrics()
            
            st.markdown("### Usage Analytics")

            # Display metrics in columns
            col1, col2 = st.columns(2)

            with col1:
                st.metric("Messages Sent", metrics["total_messages"])
                st.metric("Total Tokens", f"{metrics['total_tokens']:,}")

            with col2:
                st.metric("Avg Response Time", f"{metrics['avg_latency_ms']:.1f}ms")
                st.metric("Success Rate", f"{metrics['success_rate']:.1f}%")

            # Cost and error metrics
            col3, col4 = st.columns(2)
            with col3:
                st.metric("Total Cost", f"${metrics['total_cost_usd']:.4f}")
            with col4:
                st.metric("Errors", metrics["error_count"])

            # Category and AI mode distribution
            if metrics["category_distribution"]:
                st.markdown("### Category Distribution")
                category_df = pd.DataFrame(
                    list(metrics["category_distribution"].items()),
                    columns=["Category", "Count"]
                )
                st.bar_chart(category_df.set_index("Category"))

            if metrics["ai_mode_distribution"]:
                st.markdown("### AI Mode Distribution")
                mode_df = pd.DataFrame(
                    list(metrics["ai_mode_distribution"].items()),
                    columns=["AI Mode", "Count"]
                )
                st.bar_chart(mode_df.set_index("AI Mode"))

            st.markdown("### Recent Activity")

            # Get recent activity
            recent_activity = telemetry_collector.get_recent_activity(limit=5)
            
            if recent_activity:
                df = pd.DataFrame(recent_activity)
                st.dataframe(df, width="stretch", hide_index=True)
            else:
                st.info("No recent activity yet.")

            st.markdown("### Performance Metrics")

            # Get performance chart data
            chart_data = telemetry_collector.get_performance_chart_data(hours=3)
            
            if chart_data["hours"] and len(chart_data["hours"]) > 1:
                perf_df = pd.DataFrame({
                    "Hour": chart_data["hours"],
                    "Messages": chart_data["messages"],
                    "Response Time (ms)": chart_data["latency"],
                })
                st.line_chart(perf_df.set_index("Hour"))
            else:
                st.info("Not enough data for performance chart yet.")

        except Exception as e:
            st.error(f"Error loading telemetry data: {str(e)}")
            st.info("Telemetry data will be available once you start using the AI assistant.")
