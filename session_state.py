# session_state.py
import streamlit as st
from datetime import date

def initialize_session_state():
    defaults = {
        "operation_date": date.today(),
        "invoice_items": [],
        "invoice_number": "",
        "invoice_date": date.today(),
        "form_key": 0,
        
        # NUEVO: Cliente como diccionario flexible
        "client": {
            "name": "",
            "nif": "",
            "address": "",  # legacy, para compatibilidad
            "street": "",
            "street_number": "",
            "city": "",
            "postal_code": "",
            "province": "",
            "country": "España",
            "phone": "",
            "email": "",
            "notes": ""
        },
        
        # Para la migración de datos antiguos
        "client_name": "",  # legacy
        "client_nif": "",   # legacy
        "client_address": "", # legacy
        
        "generated_pdf": None,
        "invoice_status": "DRAFT"
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # MIGRACIÓN: Si hay datos antiguos, pasarlos al nuevo formato
    if st.session_state.client_name and not st.session_state.client["name"]:
        st.session_state.client["name"] = st.session_state.client_name
        st.session_state.client["nif"] = st.session_state.client_nif
        st.session_state.client["address"] = st.session_state.client_address
