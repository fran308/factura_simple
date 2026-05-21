# calculations.py

from helpers import calculate_net

def calculate_discount(
    base_price,
    discount_type,
    discount_value
):

    if discount_type == "Percentage (%)":

        return (
            base_price * (discount_value / 100)
        )

    elif discount_type == "Fixed amount (€)":

        return discount_value

    return 0.0


def calculate_invoice_item(
    name,
    base_price,
    vat,
    discount_type,
    discount_value
):

    discount_amount = calculate_discount(
        base_price,
        discount_type,
        discount_value
    )

    final_gross_price = max(
        base_price - discount_amount,
        0
    )

    vat_rate = 0.21 if vat == "21%" else 0.10

    net_price = calculate_net(
        final_gross_price,
        vat_rate
    )

    vat_amount = (
        final_gross_price - net_price
    )

    return {

        "name": name.strip(),

        "base_price": round(base_price, 2),

        "discount_type": discount_type,

        "discount_value": round(discount_value, 2),

        "discount_amount": round(discount_amount, 2),

        "gross_price": round(final_gross_price, 2),

        "net_price": round(net_price, 2),

        "vat": vat,

        "vat_rate": vat_rate,

        "vat_amount": round(vat_amount, 2)
    }


def calculate_totals(invoice_items):

    total_gross = 0
    total_net = 0
    total_vat_21 = 0
    total_vat_10 = 0

    for item in invoice_items:

        total_gross += item["gross_price"]

        total_net += item["net_price"]

        if item["vat"] == "21%":

            total_vat_21 += item["vat_amount"]

        else:

            total_vat_10 += item["vat_amount"]

    total_vat = (
        total_vat_21 + total_vat_10
    )

    return {
        "total_gross": round(total_gross, 2),
        "total_net": round(total_net, 2),
        "total_vat_21": round(total_vat_21, 2),
        "total_vat_10": round(total_vat_10, 2),
        "total_vat": round(total_vat, 2)
    }


def calculate_irpf(
    total_gross,
    total_net,
    is_b2b
):

    irpf_total = 0
    final_payable = total_gross

    if is_b2b:

        irpf_total = round(
            total_net * 0.15,
            2
        )

        final_payable = round(
            total_gross - irpf_total,
            2
        )

    return {
        "irpf_total": irpf_total,
        "final_payable": final_payable
    }
