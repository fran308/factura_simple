from calculations import (
    calculate_invoice_item,
    calculate_totals,
    calculate_irpf
)

# =========================================================
# HELPERS
# =========================================================

def build_item(name, price, vat, discount_type="No discount", discount_value=0):
    return calculate_invoice_item(
        name=name,
        base_price=price,
        vat=vat,
        discount_type=discount_type,
        discount_value=discount_value
    )

# =========================================================
# TEST 1 - SIMPLE CONSULTATION (21%)
# =========================================================

def test_simple_consultation_21():
    item = build_item("Consulta", 100, "21%")

    assert item["gross_price"] > 0
    assert item["vat"] == "21%"
    assert item["discount_amount"] == 0


# =========================================================
# TEST 2 - MIXED VAT INVOICE (REALISTIC B2C CASE)
# consultation + food
# =========================================================

def test_mixed_vat_b2c():
    items = [
        build_item("Consulta domicilio", 100, "21%"),
        build_item("Pienso premium", 50, "10%", "Fixed amount (€)", 10)
    ]

    totals = calculate_totals(items)

    assert totals["total_gross"] > 0
    assert totals["total_vat_21"] > 0
    assert totals["total_vat_10"] > 0


# =========================================================
# TEST 3 - PERCENTAGE DISCOUNT
# =========================================================

def test_percentage_discount():
    item = build_item("Seguimiento", 100, "21%", "Percentage (%)", 10)

    assert item["discount_amount"] == 10  # 10% of 100


# =========================================================
# TEST 4 - FIXED DISCOUNT
# =========================================================

def test_fixed_discount():
    item = build_item("Producto", 100, "21%", "Fixed amount (€)", 10)

    assert item["discount_amount"] == 10


# =========================================================
# TEST 5 - B2B IRPF SCENARIO
# =========================================================

def test_b2b_irpf():
    items = [
        build_item("Consulta", 100, "21%"),
        build_item("Seguimiento", 50, "21%")
    ]

    totals = calculate_totals(items)

    irpf = calculate_irpf(
        totals["total_gross"],
        totals["total_net"],
        True
    )

    assert irpf["irpf_total"] > 0
    assert irpf["final_payable"] < totals["total_gross"]


# =========================================================
# TEST 6 - ZERO DISCOUNT DEFAULT
# =========================================================

def test_no_discount():
    item = build_item("Consulta", 100, "21%")

    assert item["discount_amount"] == 0


# =========================================================
# TEST 7 - FULL INVOICE FLOW (REAL SCENARIO 1)
# =========================================================

def test_real_b2b_complex():
    items = [
        build_item("Consulta", 120, "21%"),
        build_item("Seguimiento", 80, "21%", "Percentage (%)", 10),
        build_item("Urgencia", 150, "21%")
    ]

    totals = calculate_totals(items)

    irpf = calculate_irpf(
        totals["total_gross"],
        totals["total_net"],
        True
    )

    assert totals["total_gross"] > 0
    assert irpf["final_payable"] > 0


# =========================================================
# TEST 8 - EDGE CASE: HIGH DISCOUNT
# =========================================================

def test_high_discount():
    item = build_item("Promo", 100, "21%", "Fixed amount (€)", 200)

    # should NOT break system (depends on your logic)
    assert item["discount_amount"] >= 0
