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

        "client_name": "",

        "client_nif": "",

        "client_address": ""
    }

    for key, value in defaults.items():

        if key not in st.session_state:

            st.session_state[key] = value
