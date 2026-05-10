import streamlit as st
import stripe
from datetime import date

st.set_page_config(page_title="Vet Billing", layout="centered")

# Mobile-friendly styling
st.markdown("""
    <style>
        .stButton button {
            font-size: 18px !important;
            padding: 0.6rem !important;
        }
        input, .stNumberInput input {
            font-size: 16px !important;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🐾 Vet Quick-Pay")
st.caption("Generate Stripe payment links with Spanish VAT")

# Session state for current invoice
if 'invoice_items' not in st.session_state:
    st.session_state.invoice_items = []

# Helper: Calculate net from gross (price includes VAT)
def calculate_net(gross_price, vat_percentage):
    return gross_price / (1 + vat_percentage)

# --- SIDEBAR: Invoice details ---
with st.sidebar:
    st.header("📄 Invoice Info")
    
    invoice_number = st.text_input(
        "Invoice number", 
        placeholder="e.g., 2024-001, F-1245"
    )
    
    invoice_date = st.date_input(
        "Invoice date",
        value=date.today()
    )
    
    if invoice_number:
        st.success(f"Invoice #{invoice_number}")
    else:
        st.warning("⚠️ Enter invoice number before generating payment link")

# --- Main form: Add products ---
with st.form("add_product", clear_on_submit=True):
    st.subheader("➕ Add service or product")
    
    name = st.text_input("Description", placeholder="e.g., Surgery, Vaccine, Consultation")
    
    col1, col2 = st.columns(2)
    with col1:
        price_with_vat = st.number_input(
            "Price to charge (€ including VAT)", 
            min_value=0.0, 
            step=1.0, 
            format="%.2f"
        )
    with col2:
        vat = st.radio("VAT Rate", ["21%", "10%"], horizontal=True)
    
    submitted = st.form_submit_button("Add to invoice", use_container_width=True)
    
    if submitted and name and price_with_vat > 0:
        vat_rate = 0.21 if vat == "21%" else 0.10
        net_price = calculate_net(price_with_vat, vat_rate)
        
        st.session_state.invoice_items.append({
            "name": name,
            "gross_price": price_with_vat,
            "net_price": net_price,
            "vat": vat,
            "vat_rate": vat_rate,
            "vat_amount": price_with_vat - net_price,
        })
        
        st.success(f"✓ Added: {name} - €{price_with_vat:.2f} (includes {vat} VAT)")
        st.rerun()

# --- Display current invoice ---
if st.session_state.invoice_items:
    st.divider()
    st.subheader("📋 Current invoice")
    
    total_gross = 0
    total_net = 0
    total_vat_21 = 0
    total_vat_10 = 0
    
    for idx, item in enumerate(st.session_state.invoice_items, 1):
        col1, col2, col3, col4, col5 = st.columns([3, 1.2, 1.2, 1.2, 0.6])
        with col1:
            st.write(f"{idx}. {item['name']}")
        with col2:
            st.write(f"€{item['gross_price']:.2f}")
        with col3:
            st.write(f"{item['vat']}")
        with col4:
            st.write(f"(net: €{item['net_price']:.2f})")
        with col5:
            if st.button("❌", key=f"del_{idx}"):
                st.session_state.invoice_items.pop(idx-1)
                st.rerun()
        
        total_gross += item['gross_price']
        total_net += item['net_price']
        if item['vat'] == "21%":
            total_vat_21 += item['vat_amount']
        else:
            total_vat_10 += item['vat_amount']
    
    total_vat = total_vat_21 + total_vat_10
    
    st.divider()
    st.markdown(f"**💰 Total client pays (includes VAT):** €{total_gross:.2f}")
    st.caption(f"Net: €{total_net:.2f} + VAT 21%: €{total_vat_21:.2f} + VAT 10%: €{total_vat_10:.2f} = €{total_gross:.2f}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔧 Generate Stripe link (will work after adding secrets)", type="primary", use_container_width=True):
            st.warning("⚠️ Stripe not configured yet. Add secrets in Settings → Secrets")
    with col2:
        if st.button("🗑 Clear all items", use_container_width=True):
            st.session_state.invoice_items = []
            st.rerun()
else:
    st.info("💡 Add your first product or service using the form above")

st.divider()
st.caption("🔐 After deployment: Go to Settings → Secrets to add Stripe keys")
