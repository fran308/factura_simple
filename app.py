import streamlit as st
import stripe
from datetime import date

st.set_page_config(page_title="Vet Billing", layout="centered")


# ===== AUTHENTICATION =====
if not st.user.is_logged_in:
    st.title("🔐 Veterinary Billing System")
    if st.button("Login with Google"):
        st.login("google")
    st.stop()

# User is logged in
user = st.user

# Domain restriction
if not user.email.endswith("@ojoveterinario.es"):
    st.error(f"Access denied: {user.email} is not authorized")
    if st.button("Logout"):
        st.logout()
    st.stop()

# Sidebar
with st.sidebar:
    st.write(f"👤 {user.name}")
    st.button("Logout", on_click=st.logout)


#========================================================================================Auth finished

st.write(f"Hola {st.user.name}")
