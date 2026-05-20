# pdf_service.py
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
import io
import streamlit as st

# Importar configuración de formato (pública)
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
    # ESTILOS (usando colores de configuración)
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
    
    # ... (resto de estilos similares)
    
    # =========================================================
    # CABECERA (usando datos de secrets)
    # =========================================================
    
    story.append(Paragraph(company_data["trading_name"], styles['CompanyName']))
    story.append(Paragraph(company_data["specialty"], styles['Specialty']))
    story.append(Spacer(1, 0.5*cm))
    
    # =========================================================
    # DATOS DEL EMISOR (desde secrets)
    # =========================================================
    
    # En la sección de emisor, usar company_data:
    issuer_text = [
        f"<b>Emisor:</b><br/>",
        f"{company_data['legal_name']}<br/>",
        f"NIF: {company_data['nif']}<br/>",
        f"{company_data['address']}<br/>",
        f"{company_data['phone']} | {company_data['email']}"
    ]
    
    # ... (resto del PDF igual, pero usando company_data donde corresponda)
    
    # =========================================================
    # PIE DE PÁGINA (usando función con template)
    # =========================================================
    
    invoice_type = invoice_data["header"]["invoice_type"]
    footer_text = get_footer_text(invoice_type, company_data)
    
    story.append(Paragraph(footer_text, styles['Footer']))
    
    # =========================================================
    # GENERAR PDF
    # =========================================================
    
    doc.build(story)
    buffer.seek(0)
    
    return buffer.getvalue()
