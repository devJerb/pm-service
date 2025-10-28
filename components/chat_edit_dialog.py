"""
Edit chat dialog component for PM Service application.

Provides a modal dialog to view chat details, edit title/category, and delete the chat.
"""

import streamlit as st
from server.chat_storage import ChatStorageManager


@st.dialog("Edit Conversation")
def render_edit_chat_dialog():
    """
    Render a dialog for editing an existing chat instance.
    """
    chat_id = st.session_state.get("edit_chat_id")
    if not chat_id:
        st.error("No chat selected for editing.")
        if st.button("Close", type="tertiary"):
            st.rerun()
        return

    storage_manager = ChatStorageManager()
    chat = storage_manager.get_chat(chat_id)

    if not chat:
        st.error("Chat not found or failed to load.")
        if st.button("Close", type="tertiary"):
            st.rerun()
        return

    total_messages = len(chat.messages)

    st.markdown("Update the conversation details below.")

    # Editable fields
    new_name = st.text_input(
        "Title",
        value=chat.name,
        help="Update the conversation title",
        key=f"edit_chat_name_{chat.id}",
    )

    new_category = st.selectbox(
        "Category",
        ["Lease & Contracts", "Maintenance & Repairs", "Tenant Communications"],
        index=["Lease & Contracts", "Maintenance & Repairs", "Tenant Communications"].index(chat.category)
        if chat.category in ["Lease & Contracts", "Maintenance & Repairs", "Tenant Communications"]
        else 0,
        help="Update the conversation category",
        key=f"edit_chat_category_{chat.id}",
    )

    st.divider()

    # Read-only details
    st.caption("Details")
    st.write({
        "ID": chat.id,
        "Workflow Phase": chat.workflow_phase,
        "Created At": chat.created_at,
        "Updated At": chat.updated_at,
        "Total Messages": total_messages,
    })

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Changes", type="secondary", use_container_width=True):
            name_to_save = new_name.strip() if new_name else ""
            if not name_to_save:
                st.error("Title cannot be empty.")
            else:
                ok = storage_manager.update_chat(chat.id, name=name_to_save, category=new_category)
                if ok:
                    st.success("Conversation updated.")
                    st.session_state.edit_chat_id = None
                    st.rerun()
                else:
                    st.error("Failed to update conversation.")

    with col2:
        if st.button("Cancel", type="tertiary", use_container_width=True):
            st.session_state.edit_chat_id = None
            st.rerun()

    st.divider()
    st.caption("Danger Zone")
    confirm_delete = st.checkbox("I understand this cannot be undone", key=f"del_confirm_{chat.id}")
    if st.button("Delete Conversation", type="secondary", disabled=not confirm_delete):
        ok = storage_manager.delete_chat(chat.id)
        if ok:
            st.success("Conversation deleted.")
            st.session_state.edit_chat_id = None
            st.rerun()
        else:
            st.error("Failed to delete conversation.")


