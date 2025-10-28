"""
Authentication gate for Supabase Google login.

Uses Supabase Python client directly for Google OAuth authentication.
"""

import streamlit as st
from supabase import create_client


def _store_session(session: dict) -> None:
    """Persist Supabase session in Streamlit session_state."""
    st.session_state["sb_session"] = session


def _clear_session() -> None:
    """Clear Supabase session and any cached clients."""
    if "sb_session" in st.session_state:
        del st.session_state["sb_session"]
    # Reset Supabase client so future calls do not reuse stale auth
    try:
        from server.supabase_client import SupabaseClient
        SupabaseClient.reset_client()
    except Exception:
        pass


def render_auth_gate() -> bool:
    """
    Render auth UI and return True if authenticated.
    
    Uses Supabase Python client for Google OAuth authentication.
    """
    st.sidebar.markdown("### Account")

    # Already authenticated
    if st.session_state.get("sb_session"):
        user = st.session_state["sb_session"].get("user", {})
        email = user.get("email") or "Signed in"
        with st.sidebar.expander("Profile", expanded=True):
            st.markdown(f"**{email}**")
            if st.button("Sign out", key="signout_btn"):
                _clear_session()
                st.rerun()
        return True

    # Check for OAuth callback (URL parameters: code)
    params = st.query_params
    code = params.get("code")
    if code:
        try:
            supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_ANON_KEY"])
            res = supabase.auth.exchange_code_for_session(code)
            if res and getattr(res, "session", None):
                session = {
                    "access_token": res.session.access_token,
                    "refresh_token": getattr(res.session, "refresh_token", None),
                    "user": res.user.__dict__ if getattr(res, "user", None) else {},
                }
                _store_session(session)
                st.query_params.clear()
                st.rerun()
        except Exception as e:
            st.error(f"Authentication error: {str(e)}")

    # Show Google sign-in button
    st.markdown("### Sign in with Google")
    
    try:
        # Create Supabase client for auth
        supabase_url = st.secrets["SUPABASE_URL"]
        supabase_key = st.secrets["SUPABASE_ANON_KEY"]
        
        supabase = create_client(supabase_url, supabase_key)
        
        # Determine redirect URL
        # Prefer explicit secret; fallback to Streamlit Cloud URL; then localhost dev
        redirect_url = (
            st.secrets.get("SUPABASE_REDIRECT_URL")
            or "https://pm-service.streamlit.app/"
        )

        # Get Google auth URL with proper redirect
        auth_url = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": redirect_url
            }
        })
        
        if st.button("🔐 Sign in with Google", key="google_signin"):
            st.markdown(f"[Click here to sign in with Google]({auth_url.url})")
            st.info("After signing in, you'll be redirected back to the app.")
            
    except Exception as e:
        st.error(f"Authentication setup error: {str(e)}")
        st.info(
            "Please ensure:\n"
            "1. Google provider is enabled in Supabase Dashboard\n"
            "2. Site URL is set to: https://pm-service.streamlit.app\n"
            "3. Redirect URLs include: https://pm-service.streamlit.app/"
        )

    return False


