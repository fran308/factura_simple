# =========================================================
# INVOICE TYPE FLAGS
# =========================================================

def get_invoice_type_flags(invoice_type):

    requires_client_details = (
        invoice_type != "B2C • Factura simplificada"
    )

    is_b2b = (
        invoice_type == "B2B • Profesional con IRPF"
    )

    return (
        requires_client_details,
        is_b2b
    )


# =========================================================
# VALIDATE INVOICE
# =========================================================

def validate_invoice(
    invoice_number,
    invoice_items
):

    if not invoice_number:

        return (
            "❌ Enter invoice number first"
        )

    if not invoice_items:

        return (
            "❌ No items in invoice"
        )

    payable_items = get_payable_items(
        invoice_items
    )

    if not payable_items:

        return (
            "❌ No payable items in invoice"
        )

    return None


# =========================================================
# PAYABLE ITEMS
# =========================================================

def get_payable_items(invoice_items):

    return [

        item for item
        in invoice_items

        if item["gross_price"] > 0
    ]


# =========================================================
# TOTAL TITLE
# =========================================================

def build_total_title(
    is_b2b,
    final_payable,
    total_gross
):

    if is_b2b:

        return (
            f"### 💰 Amount company pays: "
            f"€{final_payable:.2f}"
        )

    return (
        f"### 💰 Total client pays: "
        f"€{total_gross:.2f}"
    )


# =========================================================
# TOTAL CAPTION
# =========================================================

def build_total_caption(
    is_b2b,
    total_net,
    total_vat_21,
    total_vat_10,
    irpf_total
):

    if is_b2b:

        return (
            f"Base imponible: €{total_net:.2f} | "
            f"IVA 21%: €{total_vat_21:.2f} | "
            f"IVA 10%: €{total_vat_10:.2f} | "
            f"IRPF 15%: -€{irpf_total:.2f}"
        )

    return (
        f"Net: €{total_net:.2f} | "
        f"IVA 21%: €{total_vat_21:.2f} | "
        f"IVA 10%: €{total_vat_10:.2f}"
    )
