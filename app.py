import streamlit as st
import stripe
from datetime import date

st.set_page_config(page_title="Vet Billing", layout="centered")

# ===== AUTHENTICATION BLOCK =====
if not st.user.is_logged_in:
    st.title("🔐 Veterinary Billing System")
    st.caption("Secure payment link generator")
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("🔑 Login with Google", use_container_width=True):
            st.login("google")
    st.stop()

# Get user info
user = st.user

# === RESTRICT TO @ojoveterinario.es DOMAIN ONLY ===
if not user.email.endswith("@ojoveterinario.es"):
    st.error(f"❌ Acceso denegado. {user.email} no está autorizado.")
    if st.button("Cerrar sesión"):
        st.logout()
    st.stop()

# Sidebar Logout
with st.sidebar:
    st.write(f"👤 {user.name}")
    if st.button("Logout"):
        st.logout()
        st.stop() # Use stop instead of rerun for a cleaner exit

#========================================================================================Auth finished

st.write(f"Hola {st.user.name}")
