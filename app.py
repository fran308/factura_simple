import streamlit as st
import stripe

from datetime import (
    date,
    datetime,
    timedelta
)

import streamlit_authenticator as stauth

from styles import load_css
from session_state import initialize_session_state
from helpers import calculate_net

from calculations import (
    calculate_invoice_item,
    calculate_totals,
    calculate_irpf
)

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

load_css()

# =========================================================
# SESSION STATE
# =========================================================

initialize_session_state()

# =========================================================
# APP TITLE
# =========================================================

st.title("🐾 FacturaVET")

st.caption(
    "Stripe processes payments securely • IVA handled internally"
)

invoice_type = st.radio(
    "Invoice type",
    [
        "B2C • Factura simplificada",
        "B2C • Factura completa",
        "B2B • Profesional con IRPF"
    ],
    horizontal=False,
    disabled=len(st.session_state.invoice_items) > 0
)

requires_client_details = (
    invoice_type != "B2C • Factura simplificada"
)

is_b2b = (
    invoice_type == "B2B • Profesional con IRPF"
)

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("📄 Invoice Info")

    invoice_number = st.text_input(
        "Invoice number",
        key=f"invoice_number_{st.session_state.form_key}",
        placeholder="e.g. 2026-001",
        value=""
    )

    # -----------------------------------------------------
    # FECHA DE EMISIÓN (AUTO)
    # -----------------------------------------------------

    invoice_date = date.today()
    
    st.date_input(
        "Fecha de emisión",
        value=invoice_date,
        disabled=True
    )
    
    st.session_state.invoice_date = invoice_date
    
    # -----------------------------------------------------
    # FECHA DE OPERACIÓN
    # -----------------------------------------------------
    
    show_operation_date = (
        invoice_type != "B2C • Factura simplificada"
    )
    
    if show_operation_date:
    
        operation_date = st.date_input(
            "Fecha de operación",
            key=f"operation_date_{st.session_state.form_key}",
            value=invoice_date,
            help=(
                "Only change if the service "
                "was performed on a different day"
            )
        )
    
    else:
    
        operation_date = invoice_date
    
    st.session_state.operation_date = operation_date

    # -----------------------------------------------------
    # SAVE INVOICE NUMBER
    # -----------------------------------------------------
    
    st.session_state.invoice_number = invoice_number
    
    if invoice_number:
    
        st.success(
            f"Invoice #{invoice_number}"
        )
    
    else:
    
        st.warning(
            "⚠️ Enter invoice number"
        )

    # -----------------------------------------------------
    # CLIENT DETAILS
    # -----------------------------------------------------
    
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
    
        st.session_state.client_name = client_name
        st.session_state.client_nif = client_nif
        st.session_state.client_address = client_address

# =========================================================
# ADD PRODUCT / SERVICE
# =========================================================

st.subheader("➕ Add service or product")

with st.expander("💸 Optional discount"):

    use_discount = st.checkbox(
        "Apply discount"
    )

    discount_type = "No discount"
    discount_value = 0.0

    if use_discount:

        col3, col4 = st.columns(2)

        with col3:

            discount_type = st.selectbox(
                "Discount type",
                [
                    "Percentage (%)",
                    "Fixed amount (€)"
                ]
            )

        with col4:

            if discount_type == "Percentage (%)":

                discount_value = st.number_input(
                    "Discount %",
                    min_value=0.0,
                    max_value=100.0,
                    step=5.0,
                    format="%.1f"
                )

            elif discount_type == "Fixed amount (€)":

                discount_value = st.number_input(
                    "Discount amount (€)",
                    min_value=0.0,
                    step=1.0,
                    format="%.2f"
                )

# =========================================================
# PRODUCT FORM
# =========================================================

with st.form("add_product", clear_on_submit=True):

    name_input = st.text_input(
        "Description",
        placeholder="e.g. Ophthalmology consultation"
    )

    col1, col2 = st.columns(2)

    with col1:

        base_price = st.number_input(
            "Base price (€ IVA included)",
            min_value=0.0,
            step=1.0,
            format="%.2f"
        )

    with col2:
        
        if is_b2b:
        
            vat = st.radio(
                "IVA Rate",
                ["21%", "10%"],
                index=0,
                horizontal=True,
                disabled=True
            )
        
            st.caption(
                "🔒 B2B professional invoices use 21% IVA"
            )
        
        else:
        
            vat = st.radio(
                "IVA Rate",
                ["21%", "10%"],
                horizontal=True
            )

    submitted = st.form_submit_button(
        "Add to invoice",
        use_container_width=True
    )

    # -----------------------------------------------------
    # PROCESS ITEM
    # -----------------------------------------------------

    if submitted and name_input.strip() != "":

        item = calculate_invoice_item(
        name=name_input,
        base_price=base_price,
        vat=vat,
        discount_type=discount_type,
        discount_value=discount_value
        )
        
        st.session_state.invoice_items.append(item)
        
        st.rerun()


# =========================================================
# CURRENT INVOICE
# =========================================================

if st.session_state.invoice_items:

    st.divider()

    st.subheader("📋 Current invoice")

    totals = calculate_totals(
        st.session_state.invoice_items
    )
    
    total_gross = totals["total_gross"]
    total_net = totals["total_net"]
    total_vat_21 = totals["total_vat_21"]
    total_vat_10 = totals["total_vat_10"]
    total_vat = totals["total_vat"]

    for idx, item in enumerate(
        st.session_state.invoice_items,
        1
    ):

        col1, col2, col3, col4, col5 = st.columns(
            [3, 1.2, 1.2, 1.2, 0.6]
        )

        with col1:

            st.write(
                f"{idx}. {item['name']}"
            )

        with col2:

            st.write(
                f"€{item['gross_price']:.2f}"
            )

            if item["discount_amount"] > 0:

                st.caption(
                    f"-€{item['discount_amount']:.2f}"
                )

        with col3:

            st.write(item["vat"])

        with col4:

            st.write(
                f"(net €{item['net_price']:.2f})"
            )

        with col5:

            if st.button(
                "❌",
                key=f"delete_{idx}"
            ):

                st.session_state.invoice_items.pop(
                    idx - 1
                )

                st.rerun()

        total_gross += item["gross_price"]
        total_net += item["net_price"]

        if item["vat"] == "21%":

            total_vat_21 += item["vat_amount"]

        else:

            total_vat_10 += item["vat_amount"]

    total_vat = (
        total_vat_21 + total_vat_10
    )

    # =====================================================
    # IRPF
    # =====================================================

    irpf_data = calculate_irpf(
    total_gross,
    total_net,
    is_b2b
    )

    irpf_total = irpf_data["irpf_total"]

    final_payable = irpf_data["final_payable"]

    # =====================================================
    # TOTAL DISPLAY
    # =====================================================

    st.divider()

    if is_b2b:

        st.markdown(
            f"### 💰 Amount company pays: €{final_payable:.2f}"
        )

        st.caption(
            f"Base imponible: €{total_net:.2f} | "
            f"IVA 21%: €{total_vat_21:.2f} | "
            f"IVA 10%: €{total_vat_10:.2f} | "
            f"IRPF 15%: -€{irpf_total:.2f}"
        )

    else:

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

                st.error(
                    "❌ Enter invoice number first"
                )

            elif not st.session_state.invoice_items:

                st.error(
                    "❌ No items in invoice"
                )

            else:

                payable_items = [

                    item for item
                    in st.session_state.invoice_items

                    if item["gross_price"] > 0
                ]

                if not payable_items:

                    st.error(
                        "❌ No payable items in invoice"
                    )

                    st.stop()

                with st.spinner(
                    "Creating Stripe payment link..."
                ):

                    try:

                        line_items = []

                        # -----------------------------
                        # B2B WITH IRPF
                        # -----------------------------

                        if is_b2b:

                            line_items.append({

                                "price_data": {

                                    "currency": "eur",

                                    "unit_amount": int(
                                        round(final_payable * 100)
                                    ),

                                    "product_data": {

                                        "name": (
                                            f"Invoice "
                                            f"{st.session_state.invoice_number}"
                                        )
                                    },
                                },

                                "quantity": 1,
                            })

                        # -----------------------------
                        # NORMAL INVOICES
                        # -----------------------------

                        else:

                            for item in payable_items:

                                unit_amount_cents = int(
                                    round(
                                        item["gross_price"] * 100
                                    )
                                )

                                line_items.append({

                                    "price_data": {

                                        "currency": "eur",

                                        "unit_amount":
                                            unit_amount_cents,

                                        "product_data": {

                                            "name":
                                                f"{item['name']} "
                                                "(IVA incluido)"
                                        },
                                    },

                                    "quantity": 1,
                                })

                        # -----------------------------
                        # LINK EXPIRATION
                        # -----------------------------

                        expires_at = int(

                            (
                                datetime.utcnow()
                                + timedelta(hours=23)
                            ).timestamp()
                        )

                        # -----------------------------
                        # CREATE STRIPE SESSION
                        # -----------------------------

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

                                "invoice_number":
                                    st.session_state.invoice_number,

                                "invoice_date":
                                    st.session_state.invoice_date.isoformat(),

                                "operation_date":
                                    st.session_state.operation_date.isoformat(),

                                "total_gross":
                                    str(round(total_gross, 2)),

                                "total_net":
                                    str(round(total_net, 2)),

                                "total_vat":
                                    str(round(total_vat, 2)),

                                "irpf_total":
                                    str(round(irpf_total, 2)),

                                "final_payable":
                                    str(round(final_payable, 2)),

                                "created_by":
                                    username,

                                "client_name":
                                    st.session_state.client_name,

                                "client_nif":
                                    st.session_state.client_nif,

                                "client_address":
                                    st.session_state.client_address,
                            }
                        )

                        st.success(
                            f"✅ Payment link ready "
                            f"for Invoice "
                            f"#{st.session_state.invoice_number}"
                        )

                        if is_b2b:

                            st.info(
                                f"Company will pay "
                                f"€{final_payable:.2f}"
                            )

                        else:

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
    # START NEW INVOICE
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
    # CLEAR ITEMS
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
    "🔐 Stripe securely processes card, "
    "Apple Pay, Google Pay and Bizum payments"
)

st.caption(
    "📝 Prices entered already include IVA • "
    "Stripe is used only as payment processor"
)
