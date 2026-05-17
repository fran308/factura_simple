from invoice_service import (
    get_initial_invoice_status,
    requires_verifactu_submission
)


# =========================================================
# BUILD INVOICE OBJECT
# =========================================================

def build_invoice_object(
    session_state,
    invoice_type,
    invoice_items,
    totals,
    irpf_data,
    username,
    is_b2b
):

    # -----------------------------------------------------
    # TOTALS
    # -----------------------------------------------------

    total_gross = totals["total_gross"]
    total_net = totals["total_net"]
    total_vat = totals["total_vat"]

    total_vat_21 = totals["total_vat_21"]
    total_vat_10 = totals["total_vat_10"]

    irpf_total = irpf_data["irpf_total"]

    final_payable = irpf_data["final_payable"]

    # -----------------------------------------------------
    # VERIFACTU PLACEHOLDER
    # -----------------------------------------------------

    verifactu_required = (
        requires_verifactu_submission(
            is_b2b=is_b2b,
            total_gross=total_gross,
            client_requested_invoice=(
                invoice_type !=
                "B2C • Factura simplificada"
            )
        )
    )

    # -----------------------------------------------------
    # BUILD OBJECT
    # -----------------------------------------------------

    invoice_data = {

        # -------------------------------------------------
        # HEADER
        # -------------------------------------------------

        "header": {

            "invoice_number":
                session_state.invoice_number,

            "invoice_type":
                invoice_type,

            "invoice_date":
                session_state.invoice_date.isoformat(),

            "operation_date":
                session_state.operation_date.isoformat(),

            "created_by":
                username,
        },

        # -------------------------------------------------
        # CLIENT
        # -------------------------------------------------

        "client": {

            "name":
                session_state.client_name,

            "nif":
                session_state.client_nif,

            "address":
                session_state.client_address,
        },

        # -------------------------------------------------
        # ITEMS
        # -------------------------------------------------

        "items":
            invoice_items,

        # -------------------------------------------------
        # TOTALS
        # -------------------------------------------------

        "totals": {

            "total_gross":
                round(total_gross, 2),

            "total_net":
                round(total_net, 2),

            "total_vat":
                round(total_vat, 2),

            "total_vat_21":
                round(total_vat_21, 2),

            "total_vat_10":
                round(total_vat_10, 2),

            "irpf_total":
                round(irpf_total, 2),

            "final_payable":
                round(final_payable, 2),
        },

        # -------------------------------------------------
        # STATUS
        # -------------------------------------------------

        "status": {

            "invoice_status":
                get_initial_invoice_status(),

            "verifactu_required":
                verifactu_required,

            "verifactu_submitted":
                False,

            "payment_link_created":
                False,

            "paid":
                False,
        }
    }

    return invoice_data
