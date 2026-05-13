import streamlit as st
import stripe
from datetime import date, datetime, timedelta
import streamlit_authenticator as stauth

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="FacturaVET • Ojo Veterinario",
    layout="centered"
)

# =========================================================
# AUTHENTICATION
# =========================================================

config = {
    "credentials": {
        "usernames": {
            "fran": {
                "email": "fran@ojoveterinario.es",
                "name": "Fran",
                "password": st.secrets["usernames"]["fran"]["password"]
            },
            "contacto": {
                "email": "contacto@ojoveterinario.es",
                "name": "Contacto",
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
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"]
)

authenticator.login(location="main")

if st.session_state["authentication_status"]:
    st.sidebar.success(
        f"✅ Bienvenido {st.session_state['name']}"
    )

    authenticator.logout(
        "Cerrar sesión",
        location="sidebar"
    )

elif st.session_state["authentication_status"] is False:

    st.error("❌ Usuario o contraseña incorrectos")
    st.stop()

elif st.session_state["authentication_status"] is None:

    st.title("🔐 FacturaVET")
    st.caption("Secure veterinary payment link generator")
    st.warning("Introduce usuario y contraseña")
    st.stop()

username = st.session_state["username"]

# =========================================================
# STRIPE CONFIG
# =========================================================

stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]

# =========================================================
# CUSTOM CSS
# =========================================================

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

# =========================================================
# SESSION STATE
# =========================================================

if "invoice_items" not in st.session_state:
    st.session_state.invoice_items = []

if "client_name" not in st.session_state:
    st.session_state.client_name = ""

if "client_nif" not in st.session_state:
    st.session_state.client_nif = ""

if "client_address" not in st.session_state:
    st.session_state.client_address = ""

if "invoice_number" not in st.session_state:
    st.session_state.invoice_number = ""

if "invoice_date" not in st.session_state:
    st.session_state.invoice_date = date.today()

if "form_key" not in st.session_state:
    st.session_state.form_key = 0

# =========================================================
# APP TITLE
# =========================================================

st.title("🐾 FacturaVET")
st.caption("Stripe processes payments securely • IVA handled internally")
invoice_type = st.radio(
    "Invoice type",
    [
        "B2C • Factura simplificada",
        "B2C • Factura completa",
        "B2B • Profesional con IRPF"
    ],
    horizontal=False
)
requires_client_details = (
    invoice_type != "B2C • Factura simplificada"
)


# =========================================================
# HELPERS
# =========================================================

def calculate_net(gross_price, vat_percentage):
    return gross_price / (1 + vat_percentage)

# =========================================================
# SIDEBAR - INVOICE INFO
# =========================================================

with st.sidebar:

    st.header("📄 Invoice Info")

    invoice_number = st.text_input(
        "Invoice number",
        key=f"invoice_number_{st.session_state.form_key}",
        placeholder="e.g. 2026-001",
        value=st.session_state.invoice_number if not st.session_state.form_key else ""
    )

    invoice_date = st.date_input(
        "Invoice date",
        key=f"invoice_date_{st.session_state.form_key}",
        value=st.session_state.invoice_date if not st.session_state.form_key else date.today()
    )

    # =====================================================
    # CLIENT DETAILS
    # =====================================================

    if requires_client_details:

        st.divider()
        st.subheader("👤 Client details")
    
        client_name = st.text_input(
            "Full name / Company name",
            key=f"client_name_{st.session_state.form_key}"
        )
    
        client_nif = st.text_input(
            "Tax ID (DNI/NIF/CIF/NIE)",
            key=f"client_nif_{st.session_state.form_key}"
        )
    
        client_address = st.text_area(
            "Fiscal address",
            key=f"client_address_{st.session_state.form_key}",
            height=80
        )
    
        if invoice_number:
            st.session_state.invoice_number = invoice_number
            st.success(f"Invoice #{invoice_number}")
        else:
            st.warning("⚠️ Enter invoice number")
        
        st.session_state.invoice_date = invoice_date

# =========================================================
# ADD PRODUCT / SERVICE
# =========================================================

# 1. Place Discount logic OUTSIDE and BEFORE the form for interactivity
st.subheader("➕ Add service or product")

# These will now trigger an immediate UI change
use_discount = st.checkbox("Apply discount")
discount_type = "No discount"
discount_value = 0.0

if use_discount:
    col3, col4 = st.columns(2)
    with col3:
        discount_type = st.selectbox("Discount type", ["Percentage (%)", "Fixed amount (€)"])
    with col4:
        if discount_type == "Percentage (%)":
            discount_value = st.number_input("Discount %", min_value=0.0, max_value=100.0, step=5.0)
        elif discount_type == "Fixed amount (€)":
            discount_value = st.number_input("Discount amount (€)", min_value=0.0, step=1.0)

# 2. Now start the form for the main product details
with st.form("add_product", clear_on_submit=True):

    name_input = st.text_input("Description", placeholder="e.g. Ophthalmology consultation")

    col1, col2 = st.columns(2)
    with col1:
        base_price = st.number_input("Base price (€ IVA included)", min_value=0.0, step=1.0, format="%.2f")
    with col2:
        vat = st.radio("IVA Rate", ["21%", "10%"], horizontal=True)

    submitted = st.form_submit_button("Add to Invoice", use_container_width=True)

    # 3. PROCESS ITEM (Inside the form)
    if submitted and name_input.strip() != "":
        # Logic remains the same, it uses the discount_type/value defined above
        if discount_type == "Percentage (%)":
            discount_amount = base_price * (discount_value / 100)
        elif discount_type == "Fixed amount (€)":
            discount_amount = discount_value
        else:
            discount_amount = 0.0

        final_gross_price = max(base_price - discount_amount, 0)
        vat_rate = 0.21 if vat == "21%" else 0.10
        net_price = calculate_net(final_gross_price, vat_rate)
        vat_amount = final_gross_price - net_price

        st.session_state.invoice_items.append({
            "name": name_input.strip(),
            "base_price": round(base_price, 2),
            "discount_type": discount_type,
            "discount_value": round(discount_value, 2),
            "discount_amount": round(discount_amount, 2),
            "gross_price": round(final_gross_price, 2),
            "net_price": round(net_price, 2),
            "vat": vat,
            "vat_rate": vat_rate,
            "vat_amount": round(vat_amount, 2)
        })
        st.rerun()
# =========================================================
# ADD PRODUCT / SERVICE
# =========================================================
'''
with st.form("add_product", clear_on_submit=True):

    st.subheader("➕ Add service or product")

    name_input = st.text_input("Description", placeholder="e.g. Ophthalmology consultation")

    col1, col2 = st.columns(2)
    with col1:
        base_price = st.number_input("Base price (€ IVA included)", min_value=0.0, step=1.0, format="%.2f")
    with col2:
        vat = st.radio("IVA Rate", ["21%", "10%"], horizontal=True)

    # Move Discount logic ABOVE the button
    st.divider()
    use_discount = st.checkbox("Apply discount")
    
    discount_type = "No discount"
    discount_value = 0.0
    
    if use_discount:
        col3, col4 = st.columns(2)
        with col3:
            discount_type = st.selectbox("Discount type", ["Percentage (%)", "Fixed amount (€)"])
        with col4:
            if discount_type == "Percentage (%)":
                discount_value = st.number_input("Discount %", min_value=0.0, max_value=100.0, step=5.0)
            elif discount_type == "Fixed amount (€)":
                discount_value = st.number_input("Discount amount (€)", min_value=0.0, step=1.0)

    # NOW place the button at the bottom
    submitted = st.form_submit_button("Add to Invoice", use_container_width=True)



    # =====================================================
    # PROCESS ITEM
    # =====================================================

    if submitted and name_input.strip() != "":

        # -------------------------------------------------
        # APPLY DISCOUNT
        # -------------------------------------------------

        if discount_type == "Percentage (%)":

            discount_amount = (
                base_price * (discount_value / 100)
            )

        elif discount_type == "Fixed amount (€)":

            discount_amount = discount_value

        else:

            discount_amount = 0.0

        # Prevent negative totals
        final_gross_price = max(
            base_price - discount_amount,
            0
        )

        # -------------------------------------------------
        # VAT CALCULATION
        # -------------------------------------------------

        vat_rate = 0.21 if vat == "21%" else 0.10

        net_price = calculate_net(
            final_gross_price,
            vat_rate
        )

        vat_amount = final_gross_price - net_price

        # -------------------------------------------------
        # SAVE ITEM
        # -------------------------------------------------

        st.session_state.invoice_items.append({

            "name": name_input.strip(),

            "base_price": round(base_price, 2),

            "discount_type": discount_type,

            "discount_value": round(discount_value, 2),

            "discount_amount": round(discount_amount, 2),

            "gross_price": round(final_gross_price, 2),

            "net_price": round(net_price, 2),

            "vat": vat,

            "vat_rate": vat_rate,

            "vat_amount": round(vat_amount, 2)
        })

        # -------------------------------------------------
        # SUCCESS MESSAGE
        # -------------------------------------------------

        if discount_amount > 0:

            st.success(
                f"✓ Added: {name_input} • "
                f"€{final_gross_price:.2f} "
                f"(discount applied: €{discount_amount:.2f})"
            )

        else:

            st.success(
                f"✓ Added: {name_input} - "
                f"€{final_gross_price:.2f}"
            )

        st.rerun()
'''
# =========================================================
# CURRENT INVOICE
# =========================================================

if st.session_state.invoice_items:

    st.divider()
    st.subheader("📋 Current invoice")

    total_gross = 0
    total_net = 0
    total_vat_21 = 0
    total_vat_10 = 0

    for idx, item in enumerate(st.session_state.invoice_items, 1):

        col1, col2, col3, col4, col5 = st.columns(
            [3, 1.2, 1.2, 1.2, 0.6]
        )

        with col1:
            st.write(f"{idx}. {item['name']}")

        with col2:
        
            if item["discount_amount"] > 0:
        
                st.write(
                    f"€{item['gross_price']:.2f}"
                )
        
                st.caption(
                    f"-€{item['discount_amount']:.2f}"
                )
        
            else:
        
                st.write(
                    f"€{item['gross_price']:.2f}"
                )

        with col3:
            st.write(item["vat"])

        with col4:
            st.write(f"(net €{item['net_price']:.2f})")

        with col5:
            if st.button("❌", key=f"delete_{idx}"):
                st.session_state.invoice_items.pop(idx - 1)
                st.rerun()

        total_gross += item["gross_price"]
        total_net += item["net_price"]

        if item["vat"] == "21%":
            total_vat_21 += item["vat_amount"]
        else:
            total_vat_10 += item["vat_amount"]

    total_vat = total_vat_21 + total_vat_10

    st.divider()

    st.markdown(
        f"### 💰 Total client pays: €{total_gross:.2f}"
    )

    st.caption(
        f"Net: €{total_net:.2f} | "
        f"IVA 21%: €{total_vat_21:.2f} | "
        f"IVA 10%: €{total_vat_10:.2f}"
    )

    # =====================================================
    # ACTION BUTTONS
    # =====================================================

    col1, col2, col3 = st.columns(3)

    # -----------------------------------------------------
    # GENERATE STRIPE LINK
    # -----------------------------------------------------

    with col1:

        if st.button(
            "🚀 Generate Stripe link",
            type="primary",
            use_container_width=True
        ):

            if not st.session_state.invoice_number:

                st.error("❌ Enter invoice number first")

            elif not st.session_state.invoice_items:

                st.error("❌ No items in invoice")

            else:

                with st.spinner("Creating Stripe payment link..."):

                    try:

                        line_items = []

                        for item in st.session_state.invoice_items:
                            # Skip zero-price informational items for Stripe
                            if item["gross_price"] == 0:
                                continue
                            

                            unit_amount_cents = int(
                                round(item["gross_price"] * 100)
                            )

                            line_items.append({
                                "price_data": {
                                    "currency": "eur",
                                    "unit_amount": unit_amount_cents,
                                    "product_data": {
                                        "name": f"{item['name']} (IVA incluido)"
                                    },
                                },
                                "quantity": 1,
                            })

                        # Expire after 48h
                        expires_at = int(
                            (
                                datetime.utcnow() + timedelta(hours=23)
                            ).timestamp()
                        )

                        checkout_session = stripe.checkout.Session.create(

                            line_items=line_items,

                            mode="payment",

                            success_url=(
                                "https://ojoveterinario.es/"
                                "thankyou-payment"
                            ),

                            cancel_url=(
                                "https://ojoveterinario.es/"
                                "payment-cancelled"
                            ),

                            billing_address_collection="auto",

                            phone_number_collection={
                                "enabled": True
                            },

                            customer_creation="always",

                            expires_at=expires_at,

                            metadata={
                                "invoice_number": st.session_state.invoice_number,
                                "invoice_date": st.session_state.invoice_date.isoformat(),
                                "total_gross": str(round(total_gross, 2)),
                                "total_net": str(round(total_net, 2)),
                                "total_vat": str(round(total_vat, 2)),
                                "created_by": username,
                                "client_name": st.session_state.client_name,
                                "client_nif": st.session_state.client_nif,
                                "client_address": st.session_state.client_address,
                            }
                        )

                        st.success(
                            f"✅ Payment link ready "
                            f"for Invoice #{st.session_state.invoice_number}"
                        )

                        st.info(
                            f"Client will pay "
                            f"€{total_gross:.2f}"
                        )

                        st.markdown(
                            "**Send this secure payment "
                            "link to your client:**"
                        )

                        st.code(
                            checkout_session.url,
                            language="text"
                        )

                    except Exception as e:

                        st.error(
                            f"Stripe error: {str(e)}"
                        )

    # -----------------------------------------------------
    # START NEW INVOICE (FIXED)
    # -----------------------------------------------------

    with col2:
        if st.button(
            "🔄 Start new invoice",
            use_container_width=True
        ):
            st.session_state.invoice_items = []
            st.session_state.form_key += 1
            st.rerun()

    # -----------------------------------------------------
    # CLEAR ALL ITEMS
    # -----------------------------------------------------

    with col3:
        if st.button(
            "🗑 Clear all items",
            use_container_width=True
        ):
            st.session_state.invoice_items = []
            st.rerun()

# =========================================================
# EMPTY STATE
# =========================================================

else:

    st.info(
        "💡 Add your first product or service above"
    )

# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "🔐 Stripe securely processes card, Apple Pay, "
    "Google Pay and Bizum payments"
)

st.caption(
    "📝 Prices entered already include IVA • "
    "Stripe is used only as payment processor"
)
