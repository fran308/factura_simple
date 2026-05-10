import streamlit as st

st.set_page_config(page_title="Test Auth", layout="centered")

if not st.user.is_logged_in:
    st.button("Login", on_click=st.login, args=("google",))
    st.stop()

st.write(f"Hola {st.user.name}")
