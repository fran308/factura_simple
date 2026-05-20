# pdf_service.py
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import io
import streamlit as st

from company_config import get_company_data_from_secrets, INVOICE_STYLES, get_footer_text


def generate_pdf(invoice_data):
    """
    Genera PDF profesional usando datos de empresa desde st.secrets
    """
    
    # Cargar datos de empresa desde secrets
    company_data = get_company_data_from_secrets()
    if not company_data:
        raise ValueError("No se pudieron cargar los datos de la empresa")
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=2*cm,
        bottomMargin=2*cm,
        leftMargin=2*cm,
        rightMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # =========================================================
    # ESTILOS PERSONALIZADOS
    # =========================================================
    
    styles.add(ParagraphStyle(
        name='CompanyName',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor(INVOICE_STYLES["primary_color"]),
        alignment=TA_CENTER,
        spaceAfter=0
    ))
    
    styles.add(ParagraphStyle(
        name='Specialty',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor(INVOICE_STYLES["muted_color"]),
        alignment=TA_CENTER,
        spaceAfter=12
    ))
    
    styles.add(ParagraphStyle(
        name='InvoiceTitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor(INVOICE_STYLES["text_color"]),
        alignment=TA_RIGHT
    ))
    
    styles.add(ParagraphStyle(
        name='SectionTitle',
        parent=styles['Heading3'],
        fontSize=11,
        textColor=colors.HexColor(INVOICE_STYLES["primary_color"]),
        spaceAfter=6,
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='Label',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor(INVOICE_STYLES["muted_color"]),
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='Value',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor(INVOICE_STYLES["text_color"])
    ))
    
    # ⚠️ ESTILO FOOTER - ¡IMPORTANTE!
    styles.add(ParagraphStyle(
        name='Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor(INVOICE_STYLES["footer_color"]),
        alignment=TA_CENTER
    ))
    
    # =========================================================
    # CABECERA
    # =========================================================
    
    story.append(Paragraph(company_data["trading_name"], styles['CompanyName']))
    story.append(Paragraph(company_data["specialty"], styles['Specialty']))
    story.append(Spacer(1, 0.5*cm))
    
    # =========================================================
    # NÚMERO DE FACTURA Y FECHAS
    # =========================================================
    
    invoice_header = [
        ["", ""],
        ["", f"<b>Factura Nº:</b> {invoice_data['header']['invoice_number']}"],
        ["", f"<b>Expedición:</b> {invoice_data['header']['invoice_date']}"],
        ["", f"<b>Operación:</b> {invoice_data['header']['operation_date']}"]
    ]
    
    header_table = Table(invoice_header, colWidths=[10*cm, 6*cm])
    header_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (1, 0), (1, -1), 'TOP'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (1, 0), (1, -1), 10),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.5*cm))
    
    # =========================================================
    # CLIENTE Y EMISOR
    # =========================================================
    
    client = invoice_data["client"]
    
    # Datos del cliente
    client_text = [
        f"<b>Cliente:</b><br/>",
        f"{client.get('name', '')}<br/>",
        f"NIF/CIF: {client.get('nif', '')}<br/>",
    ]
    
    # Dirección del cliente
    client_address = client.get('full_address', '')
    if not client_address:
        parts = []
        if client.get('street'):
            street = client['street']
            if client.get('street_number'):
                street += f", {client['street_number']}"
            parts.append(street)
        if client.get('city'):
            parts.append(client['city'])
        if client.get('postal_code'):
            parts.insert(0, client['postal_code'])
        client_address = ", ".join(parts)
    
    if client_address:
        client_text.append(f"{client_address}<br/>")
    
    # Datos del emisor
    issuer_text = [
        f"<b>Emisor:</b><br/>",
        f"{company_data['legal_name']}<br/>",
        f"NIF: {company_data['nif']}<br/>",
        f"{company_data['address']}<br/>",
        f"{company_data['phone']} | {company_data['email']}"
    ]
    
    parties_data = [
        [Paragraph("".join(client_text), styles['Value']),
         Paragraph("".join(issuer_text), styles['Value'])]
    ]
    
    parties_table = Table(parties_data, colWidths=[8*cm, 8*cm])
    parties_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ]))
    story.append(parties_table)
    story.append(Spacer(1, 0.8*cm))
    
    # =========================================================
    # TABLA DE CONCEPTOS
    # =========================================================
    
    invoice_type = invoice_data["header"]["invoice_type"]
    is_simplified = invoice_type == "B2C • Factura simplificada"
    is_b2b = invoice_type == "B2B • Profesional con IRPF"
    
    if is_simplified:
        table_data = [["Concepto", "Precio sin IVA", "Tipo IVA", "Precio con IVA"]]
        for item in invoice_data["items"]:
            table_data.append([
                Paragraph(item["name"], styles['Value']),
                f"€{item['net_price']:.2f}",
                item["vat"],
                f"€{item['gross_price']:.2f}"
            ])
    else:
        table_data = [["Concepto", "Cantidad", "Precio", "Dto.", "Total"]]
        for item in invoice_data["items"]:
            cantidad = "1.00"
            descuento = f"-{item['discount_amount']:.2f}" if item['discount_amount'] > 0 else "-"
            table_data.append([
                Paragraph(item["name"], styles['Value']),
                cantidad,
                f"€{item['base_price']:.2f}",
                descuento,
                f"€{item['gross_price']:.2f}"
            ])
    
    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(INVOICE_STYLES["primary_color"])),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    story.append(table)
    story.append(Spacer(1, 0.5*cm))
    
    # =========================================================
    # TOTALES
    # =========================================================
    
    totals = invoice_data["totals"]
    
    if is_b2b:
        totals_data = [
            ["Base imponible:", f"€{totals['total_net']:.2f}"],
            [f"IVA (21%):", f"€{totals['total_vat_21']:.2f}"],
            [f"IRPF (15%):", f"-€{totals['irpf_total']:.2f}"],
            ["", ""],
            ["TOTAL:", f"€{totals['final_payable']:.2f}"]
        ]
    else:
        totals_data = [
            ["Base imponible:", f"€{totals['total_net']:.2f}"],
            [f"IVA (21%):", f"€{totals['total_vat_21']:.2f}"],
        ]
        if totals['total_vat_10'] > 0:
            totals_data.insert(2, [f"IVA (10%):", f"€{totals['total_vat_10']:.2f}"])
        totals_data.append(["", ""])
        totals_data.append(["TOTAL:", f"€{totals['total_gross']:.2f}"])
    
    totals_table = Table(totals_data, colWidths=[12*cm, 4*cm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (1, -1), 12),
        ('TEXTCOLOR', (0, -1), (1, -1), colors.HexColor(INVOICE_STYLES["primary_color"])),
        ('BACKGROUND', (0, -1), (1, -1), colors.HexColor(INVOICE_STYLES["secondary_color"])),
        ('TOPPADDING', (0, -1), (1, -1), 6),
        ('BOTTOMPADDING', (0, -1), (1, -1), 6),
    ]))
    
    story.append(totals_table)
    story.append(Spacer(1, 1*cm))
    
    # =========================================================
    # PIE DE PÁGINA
    # =========================================================
    
    footer_text = get_footer_text(invoice_type, company_data)
    story.append(Paragraph(footer_text, styles['Footer']))
    
    # =========================================================
    # GENERAR PDF
    # =========================================================
    
    doc.build(story)
    buffer.seek(0)
    
    return buffer.getvalue()
