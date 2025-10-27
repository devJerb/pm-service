"""
Header component for PM Service application.

Displays the application title and description.
"""

import streamlit as st


def render_header():
    """
    Render the header section with title and description.

    Uses st.title() and st.markdown() for clean, simple design.
    """
    st.title("PM Companion")

    st.markdown(
        """
    Get help with property management tasks, document analysis, and maintenance requests.
    """
    )

    st.divider()
