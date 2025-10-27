"""
Supabase client for PM Service application.

Handles database connection and provides singleton access to Supabase client.
"""

import os
from typing import Optional
import streamlit as st
from supabase import create_client, Client


class SupabaseClient:
    """
    Singleton class for Supabase client management.
    
    Provides a single instance of the Supabase client across the application.
    Handles credential loading from environment variables or Streamlit secrets.
    """
    
    _instance: Optional[Client] = None
    
    @classmethod
    def get_client(cls) -> Client:
        """
        Get or create the Supabase client instance.
        
        Returns:
            Client: Supabase client instance
            
        Raises:
            ValueError: If Supabase credentials are not found
        """
        if cls._instance is None:
            # Try to get credentials from Streamlit secrets first, then environment variables
            supabase_url = None
            supabase_key = None
            
            try:
                # Check if we're in a Streamlit context and secrets are available
                if hasattr(st, 'secrets'):
                    try:
                        supabase_url = st.secrets["SUPABASE_URL"]
                        supabase_key = st.secrets["SUPABASE_ANON_KEY"]
                    except (KeyError, AttributeError):
                        # Secrets not available, fall back to environment variables
                        pass
                
                # Fallback to environment variables if secrets not available
                if not supabase_url:
                    supabase_url = os.getenv("SUPABASE_URL")
                if not supabase_key:
                    supabase_key = os.getenv("SUPABASE_ANON_KEY")
                    
            except Exception:
                # Handle case where secrets.toml doesn't exist or is malformed
                pass
            
            if not supabase_url or not supabase_key:
                raise ValueError(
                    "Supabase credentials not found. Please:\n"
                    "1. Copy .streamlit/secrets.toml.template to .streamlit/secrets.toml\n"
                    "2. Add your Supabase URL and KEY to the secrets file\n"
                    "3. Or set SUPABASE_URL and SUPABASE_ANON_KEY environment variables\n\n"
                    "Get your credentials from: https://supabase.com/dashboard/project/[your-project]/settings/api"
                )
            
            # Check if using placeholder values
            if supabase_url == "your-supabase-project-url-here" or supabase_key == "your-supabase-anon-key-here":
                raise ValueError(
                    "Please update your Supabase credentials in .streamlit/secrets.toml:\n"
                    "1. Replace 'your-supabase-project-url-here' with your actual Supabase URL\n"
                    "2. Replace 'your-supabase-anon-key-here' with your actual Supabase anon key\n\n"
                    "Get your credentials from: https://supabase.com/dashboard/project/[your-project]/settings/api"
                )
            
            cls._instance = create_client(supabase_url, supabase_key)
        
        return cls._instance
    
    @classmethod
    def reset_client(cls):
        """
        Reset the client instance (useful for testing or credential changes).
        """
        cls._instance = None
    
    @classmethod
    def is_connected(cls) -> bool:
        """
        Check if the client is properly connected.
        
        Returns:
            bool: True if client is connected, False otherwise
        """
        try:
            client = cls.get_client()
            # Try a simple query to test connection
            client.table("chat_instances").select("id").limit(1).execute()
            return True
        except Exception:
            return False


def get_supabase_client() -> Client:
    """
    Convenience function to get the Supabase client.
    
    Returns:
        Client: Supabase client instance
    """
    return SupabaseClient.get_client()
