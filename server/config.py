"""
LLM configuration for Google Gemini integration.

Handles Gemini model initialization and configuration parameters.
"""

import os
import streamlit as st
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables as fallback
load_dotenv()


def get_gemini_llm():
    """
    Initialize and configure Google Gemini LLM.

    Returns:
        ChatGoogleGenerativeAI: Configured Gemini model instance

    Raises:
        ValueError: If GEMINI_API_KEY is not found in secrets or environment
    """
    # Try to get API key from Streamlit secrets first
    api_key = None
    
    try:
        # Check if we're in a Streamlit context
        if hasattr(st, 'secrets') and hasattr(st.secrets, 'GEMINI_API_KEY'):
            api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        # Fallback to environment variable if secrets not available
        api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY not found in Streamlit secrets or environment variables. "
            "Please set your Google API key in .streamlit/secrets.toml or .env file."
        )

    # Configure Gemini model with property management optimized settings
    llm = ChatGoogleGenerativeAI(
        model="gemini-flash-latest",  # Optimized for vision and multimodal tasks
        google_api_key=api_key,
        temperature=0.3,  # Lower temperature for more consistent, professional responses
        max_output_tokens=2048,  # Sufficient for detailed property management responses
        convert_system_message_to_human=True,  # Ensure system prompts work properly
    )

    return llm
