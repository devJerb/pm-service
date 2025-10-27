"""
Main Streamlit application for PM Service.

This is the entry point that orchestrates all components.
"""

import streamlit as st
from components import render_header, render_sidebar, render_chat_interface
from server import ChatStorageManager


def main():
    """
    Main application function that configures Streamlit and renders components.
    """
    # Configure page settings
    st.set_page_config(
        page_title="PM Companion",
        page_icon="🏠",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Initialize chat storage and session state
    storage_manager = ChatStorageManager()
    
    # No default chat creation - start with empty state
    # Users will create their first chat when they click "New Conversation"

    # Render header
    render_header()

    # Render sidebar (uses st.sidebar internally)
    render_sidebar()

    # Render chat interface in main area
    render_chat_interface()


if __name__ == "__main__":
    main()
