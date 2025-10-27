"""
New chat dialog component for PM Service application.

Provides a modal dialog for creating new chat instances with custom names and categories.
"""

import streamlit as st
from server.chat_storage import ChatStorageManager


@st.dialog("Create New Chat")
def render_new_chat_dialog():
    """
    Render a dialog for creating new chat instances using @st.dialog decorator.
    """
    st.markdown("Start a new conversation for your property management tasks.")

    # Form fields
    chat_name = st.text_input(
        "Chat Name",
        placeholder="e.g., Lease Review Discussion",
        help="Give your conversation a descriptive name",
        key="new_chat_name",
    )

    work_category = st.selectbox(
        "Work Category",
        ["Lease & Contracts", "Maintenance & Repairs", "Tenant Communications"],
        help="Select the type of property management work",
        key="new_chat_category",
    )

    st.divider()

    # Action buttons
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Create Conversation", type="secondary", width="stretch"):
            if _create_new_chat(chat_name, work_category):
                st.rerun()  # Close dialog and rerun app

    with col2:
        if st.button("Cancel", type="tertiary", width="stretch"):
            st.rerun()  # Close dialog and rerun app


def _create_new_chat(name: str, category: str) -> bool:
    """
    Create a new conversation instance.

    Args:
        name: Conversation name
        category: Work category

    Returns:
        bool: True if successful, False if validation failed
    """
    # Validate inputs
    if not name or not name.strip():
        st.error("Please enter a conversation name.")
        return False

    if not category:
        st.error("Please select a work category.")
        return False

    # Create chat using storage manager
    try:
        storage_manager = ChatStorageManager()
        chat_id = storage_manager.create_chat(name.strip(), category)

        # Switch to the new chat
        storage_manager.set_active_chat(chat_id)

        return True

    except Exception as e:
        st.error(f"Failed to create chat: {str(e)}")
        return False
