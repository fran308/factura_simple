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
        placeholder="e.g. 2026-001"
    )

    invoice_date = st.date_input(
        "Invoice date",
        value=date.today()
    )

    if invoice_number:
        st.success(f"Invoice #{invoice_number}")
    else:
        st.warning("⚠️ Enter invoice number")

# =========================================================
# ADD PRODUCT / SERVICE
# =========================================================

with st.form("add_product", clear_on_submit=True):

    st.subheader("➕ Add service or product")

    name_input = st.text_input(
        "Description",
        placeholder="e.g. Ophthalmology consultation"
    )

    col1, col2 = st.columns(2)

    with col1:
        gross_price = st.number_input(
            "Price to charge (€ including IVA)",
            min_value=0.0,
            step=1.0,
            format="%.2f"
        )

    with col2:
        vat = st.radio(
            "IVA Rate",
            ["21%", "10%"],
            horizontal=True
        )

    submitted = st.form_submit_button(
        "Add to invoice",
        use_container_width=True
    )

    if submitted and name_input and gross_price > 0:

        vat_rate = 0.21 if vat == "21%" else 0.10

        net_price = calculate_net(gross_price, vat_rate)
        vat_amount = gross_price - net_price

        st.session_state.invoice_items.append({
            "name": name_input.strip(),
            "gross_price": round(gross_price, 2),
            "net_price": round(net_price, 2),
            "vat": vat,
            "vat_rate": vat_rate,
            "vat_amount": round(vat_amount, 2)
        })

        st.success(
            f"✓ Added: {name_input} - €{gross_price:.2f}"
        )

        st.rerun()

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
            st.write(f"€{item['gross_price']:.2f}")

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

    col1, col2 = st.columns(2)

    # -----------------------------------------------------
    # GENERATE STRIPE LINK
    # -----------------------------------------------------

    with col1:

        if st.button(
            "🚀 Generate Stripe link",
            type="primary",
            use_container_width=True
        ):

            if not invoice_number:

                st.error("❌ Enter invoice number first")

            elif not st.session_state.invoice_items:

                st.error("❌ No items in invoice")

            else:

                with st.spinner("Creating Stripe payment link..."):

                    try:

                        line_items = []

                        for item in st.session_state.invoice_items:

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

                                "invoice_number": invoice_number,

                                "invoice_date":
                                    invoice_date.isoformat(),

                                "total_gross":
                                    str(round(total_gross, 2)),

                                "total_net":
                                    str(round(total_net, 2)),

                                "total_vat":
                                    str(round(total_vat, 2)),

                                "created_by":
                                    username
                            }
                        )

                        st.success(
                            f"✅ Payment link ready "
                            f"for Invoice #{invoice_number}"
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

                        if st.button(
                            "🔄 Start new invoice"
                        ):
                            st.session_state.invoice_items = []
                            st.rerun()

                    except Exception as e:

                        st.error(
                            f"Stripe error: {str(e)}"
                        )

    # -----------------------------------------------------
    # CLEAR INVOICE
    # -----------------------------------------------------

    with col2:

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
