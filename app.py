import streamlit as st
import stripe
from datetime import date
import streamlit_authenticator as stauth
import yaml
from io import StringIO

st.set_page_config(page_title="Vet Billing", layout="centered")

config = {
    "credentials": {
        "usernames": {
            "fran": {
                "email": "fran@ojoveterinario.es",
                "name": "fran",
                "password": st.secrets["usernames"]["fran"]["password"]
            },
            "contacto": {
                "email": "contacto@ojoveterinario.es",
                "name": "contacto",
                "password": st.secrets["usernames"]["contacto"]["password"]
            }
        }
    },
    "cookie": {
        "expiry_days": st.secrets["cookie_expiry_days"],
        "key": st.secrets["cookie_key"],
        "name": st.secrets["cookie_name"]
    },
    "preauthorized": {
        "emails": []
    }
}

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

authenticator.login()

if st.session_state["authentication_status"]:
    st.sidebar.success(f"✅ Bienvenido {st.session_state['name']}")
    authenticator.logout("Cerrar sesión", "sidebar")

elif st.session_state["authentication_status"] is False:
    st.error("❌ Usuario o contraseña incorrectos")
    st.stop()

elif st.session_state["authentication_status"] is None:
    st.title("🔐 Veterinary Billing System")
    st.caption("Secure payment link generator")
    st.warning("Introduce usuario y contraseña")
    st.stop()



# --- AQUÍ EMPIEZA TU APP DE STRIPE ---
st.title("🐾 FacturaVET")

# Load secrets from Streamlit Cloud dashboard
stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]
#TAX_21_ID = st.secrets["TAX_21_ID"] WE ARE NOT USING STRIPE TO CALCULATE TAXES, ONLY TO TAKE GROSS PAYMENTS
#TAX_10_ID = st.secrets["TAX_10_ID"] ""

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


# Session state for current invoice
if 'invoice_items' not in st.session_state:
    st.session_state.invoice_items = []

# Helper: Calculate net from gross (price includes VAT)
def calculate_net(gross_price, vat_percentage):
    return gross_price / (1 + vat_percentage)

# --- SIDEBAR: Invoice details ---
with st.sidebar:
    st.header("📄 Invoice Info")
    
    # Manual invoice number (always)
    invoice_number = st.text_input(
        "Invoice number", 
        placeholder="e.g., 2024-001, F-1245",
        help="Enter your manual invoice number"
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
            format="%.2f",
            help="Example: If client pays €50 total, enter 50"
        )
    with col2:
        vat = st.radio("VAT Rate", ["21%", "10%"], horizontal=True)
    
    submitted = st.form_submit_button("Add to invoice", use_container_width=True)
    
    if submitted and name and price_with_vat > 0:
        # Calculate net price (without VAT)
        vat_rate = 0.21 if vat == "21%" else 0.10
        net_price = calculate_net(price_with_vat, vat_rate)
        
        #tax_id = TAX_21_ID if vat == "21%" else TAX_10_ID
        
        st.session_state.invoice_items.append({
            "name": name,
            "gross_price": price_with_vat,  # What client pays
            "net_price": net_price,          # Without VAT
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
    
    # Calculate totals
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
    
    # --- Action buttons ---
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 Generate Stripe link", type="primary", use_container_width=True):
            if not invoice_number:
                st.error("❌ Enter invoice number in sidebar first")
            elif not st.session_state.invoice_items:
                st.error("❌ No items in invoice")
            else:
                with st.spinner("Creating payment link..."):
                    try:
                        # Create line items for Checkout Session
                        line_items = []
                        for item in st.session_state.invoice_items:
                            # Convert gross price to cents
                            unit_amount_cents = int(round(item['gross_price'] * 100))

                            line_items.append({
                                "price_data": {
                                    "currency": "eur",
                                    "unit_amount": unit_amount_cents,
                                    "product_data": {"name": item['name']},
                                    #"tax_behavior": "inclusive",  # <--- CRITICAL: This tells Stripe tax is already in the price - I know, but stripe won't calculate it.
                                },
                                "quantity": 1,
                                #"tax_rates": [item['tax_id']], ALSO DELETED BECAUSE STRIPE WONT USE IT
                            })
                        
                           # Convert gross price to cents
                           # unit_amount_cents = int(item['gross_price'] * 100)
                           # 
                           # line_items.append({
                           #     "price_data": {
                           #         "currency": "eur",
                           #         "unit_amount": unit_amount_cents,  # Gross price
                           #         "product_data": {"name": item['name']},
                           #     },
                           #     "quantity": 1,
                           #     "tax_rates": [item['tax_id']],  # This works in Checkout Sessions!
                           # })
                         
                        
                        # Create Checkout Session (not Payment Link)
                        checkout_session = stripe.checkout.Session.create(
                            line_items=line_items,
                            mode="payment",
                            success_url="https://ojoveterinario.es",  # Update this
                            cancel_url="https://bbc.co.uk",    # Update this
                            tax_id_collection={"enabled": False},  # Collect customer NIF
                            metadata={
                                "invoice_number": invoice_number,
                                "invoice_date": invoice_date.isoformat(),
                                "total_gross": total_gross,
                                "total_net": total_net
                            }
                        )
                        
                        st.success(f"✅ Payment link ready for Invoice #{invoice_number}")
                        st.info(f"Client will be charged: **€{total_gross:.2f}** (includes {total_vat:.2f} VAT)")
                        st.markdown("**Send this link to your client:**")
                        st.code(checkout_session.url, language="text")
                        
                        # Offer to reset after generation
                        if st.button("🔄 Start new invoice"):
                            st.session_state.invoice_items = []
                            st.rerun()
                            
                    except Exception as e:
                        st.error(f"Stripe error: {str(e)}")
    
    with col2:
        if st.button("🗑 Clear all items", use_container_width=True):
            st.session_state.invoice_items = []
            st.rerun()

else:
    st.info("💡 Add your first product or service using the form above")

# --- Footer ---
st.divider()
st.caption("🔐 Stripe processes payments | Spanish VAT 21% / 10%")
st.caption("📝 Prices you enter include VAT | Client pays exactly what you type")
