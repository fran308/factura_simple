# calculations.py
from decimal import Decimal, ROUND_HALF_UP


def round_currency(value):
    """
    Redondea un valor al método fiscal español (5 o más sube).
    
    Args:
        value (float/int/str): Valor a redondear
    
    Returns:
        float: Valor redondeado a 2 decimales con ROUND_HALF_UP
    
    Examples:
        >>> round_currency(11.085)
        11.09
        >>> round_currency(11.084)
        11.08
        >>> round_currency(10.525)
        10.53
    """
    # Convertir a string para evitar problemas de precisión de float
    decimal_value = Decimal(str(value))
    # Redondear a 2 decimales con ROUND_HALF_UP (5 sube al siguiente)
    rounded = decimal_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return float(rounded)


def calculate_discount(base_price, discount_type, discount_value):
    """
    Calcula el monto del descuento según el tipo.
    
    Args:
        base_price (float): Precio base del producto
        discount_type (str): "Percentage (%)", "Fixed amount (€)", o "No discount"
        discount_value (float): Valor del descuento (porcentaje o cantidad fija)
    
    Returns:
        float: Monto del descuento redondeado
    """
    if discount_type == "Percentage (%)":
        discount_amount = base_price * (discount_value / 100)
    elif discount_type == "Fixed amount (€)":
        discount_amount = discount_value
    else:
        discount_amount = 0.0
    
    return round_currency(discount_amount)


def calculate_net(gross_price, vat_percentage):
    """
    Calcula el precio neto (sin IVA) a partir del precio bruto (con IVA).
    
    Args:
        gross_price (float): Precio con IVA incluido
        vat_percentage (float): Tipo de IVA (0.21 para 21%, 0.10 para 10%)
    
    Returns:
        float: Precio neto (sin IVA) redondeado
    
    Formula:
        net_price = gross_price / (1 + vat_percentage)
    """
    net_price = gross_price / (1 + vat_percentage)
    return round_currency(net_price)


def calculate_invoice_item(name, base_price, vat, discount_type, discount_value):
    """
    Crea un objeto item con todos los cálculos necesarios.
    
    Args:
        name (str): Nombre del producto/servicio
        base_price (float): Precio base (IVA incluido) introducido por el usuario
        vat (str): "21%" o "10%"
        discount_type (str): Tipo de descuento aplicado
        discount_value (float): Valor del descuento
    
    Returns:
        dict: Objeto item con todos los valores calculados y redondeados
    """
    
    # Calcular descuento
    discount_amount = calculate_discount(base_price, discount_type, discount_value)
    
    # Precio final bruto (con IVA) después del descuento
    final_gross_price = max(base_price - discount_amount, 0)
    final_gross_price = round_currency(final_gross_price)
    
    # Determinar tipo de IVA
    vat_rate = 0.21 if vat == "21%" else 0.10
    
    # Calcular precio neto (sin IVA)
    net_price = calculate_net(final_gross_price, vat_rate)
    
    # Calcular monto del IVA
    vat_amount = final_gross_price - net_price
    vat_amount = round_currency(vat_amount)
    
    return {
        "name": name.strip(),
        "base_price": round_currency(base_price),
        "discount_type": discount_type,
        "discount_value": round_currency(discount_value),
        "discount_amount": discount_amount,
        "gross_price": final_gross_price,
        "net_price": net_price,
        "vat": vat,
        "vat_rate": vat_rate,
        "vat_amount": vat_amount
    }


def calculate_totals(invoice_items):
    """
    Calcula los totales de la factura a partir de la lista de items.
    
    Args:
        invoice_items (list): Lista de objetos item
    
    Returns:
        dict: Totales calculados y redondeados
    """
    total_gross = 0.0
    total_net = 0.0
    total_vat_21 = 0.0
    total_vat_10 = 0.0
    
    for item in invoice_items:
        total_gross += item["gross_price"]
        total_net += item["net_price"]
        
        if item["vat"] == "21%":
            total_vat_21 += item["vat_amount"]
        else:
            total_vat_10 += item["vat_amount"]
    
    total_vat = total_vat_21 + total_vat_10
    
    return {
        "total_gross": round_currency(total_gross),
        "total_net": round_currency(total_net),
        "total_vat_21": round_currency(total_vat_21),
        "total_vat_10": round_currency(total_vat_10),
        "total_vat": round_currency(total_vat)
    }


def calculate_irpf(total_gross, total_net, is_b2b):
    """
    Calcula el IRPF y el total final a pagar para facturas B2B.
    
    Args:
        total_gross (float): Total bruto (con IVA)
        total_net (float): Total neto (sin IVA, base imponible)
        is_b2b (bool): True si es factura B2B (profesional con IRPF)
    
    Returns:
        dict: IRPF calculado y total final a pagar
    
    Nota:
        El IRPF se aplica sobre la base imponible (total_net) y es del 15%
    """
    irpf_total = 0.0
    final_payable = total_gross
    
    if is_b2b:
        irpf_total = round_currency(total_net * 0.15)
        final_payable = round_currency(total_gross - irpf_total)
    
    return {
        "irpf_total": irpf_total,
        "final_payable": final_payable
    }
