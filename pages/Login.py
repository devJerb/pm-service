import streamlit as st
from components import render_auth_gate


def main():
    st.set_page_config(page_title="Login", page_icon="🔐", layout="wide")
    authenticated = render_auth_gate()
    if authenticated:
        st.switch_page("app.py")


if __name__ == "__main__":
    main()


