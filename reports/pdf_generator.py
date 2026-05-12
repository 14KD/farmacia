import os
import sys
import config

from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, Image
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.platypus.flowables import HRFlowable
from datetime import datetime


def generate_invoice_pdf(invoice_id, customer, cart, total, filename=None):

    cfg      = config.load()
    ph       = cfg["pharmacy"]
    bl       = cfg["billing"]

    pharmacy_name = ph["name"]    or "FarmaFactura Pro"
    address       = ph["address"] or ""
    phone         = ph["phone"]   or ""
    rnc           = ph["rnc"]     or ""
    logo_path     = ph["logo_path"]
    footer_msg    = bl["footer"]  or "Gracias por su compra."
    currency      = bl["currency"] or "$"
    tax_rate      = float(bl["tax_rate"] or 0)

    if filename is None:
        filename = f"Factura_{invoice_id}.pdf"

    doc      = SimpleDocTemplate(filename, pagesize=letter,
                                  topMargin=1.5*cm, bottomMargin=1.5*cm,
                                  leftMargin=2*cm, rightMargin=2*cm)
    styles   = getSampleStyleSheet()
    elements = []

    # ── Logo + Encabezado ────────────────────────
    header_data = []

    # Logo
    logo_cell = ""
    if logo_path and os.path.exists(logo_path):
        try:
            logo_cell = Image(logo_path, width=3*cm, height=3*cm)
        except Exception:
            logo_cell = ""

    title_style = ParagraphStyle("title", fontSize=18, fontName="Helvetica-Bold",
                                  textColor=colors.HexColor("#1A1D27"), leading=22)
    sub_style   = ParagraphStyle("sub",   fontSize=9,  fontName="Helvetica",
                                  textColor=colors.HexColor("#8B8FA8"), leading=13)

    title_block = [
        Paragraph(f"<b>{pharmacy_name}</b>", title_style),
        Paragraph(address, sub_style) if address else Spacer(1, 2),
        Paragraph(f"Tel: {phone}" if phone else "", sub_style),
        Paragraph(f"RNC: {rnc}"   if rnc   else "", sub_style),
    ]

    if logo_cell:
        header_table = Table([[logo_cell, title_block]], colWidths=[3.5*cm, None])
        header_table.setStyle(TableStyle([
            ("VALIGN",  (0,0), (-1,-1), "MIDDLE"),
            ("ALIGN",   (0,0), (0,0),   "CENTER"),
            ("LEFTPADDING",  (1,0), (1,0), 12),
        ]))
        elements.append(header_table)
    else:
        for p in title_block:
            if isinstance(p, Paragraph): elements.append(p)
    elements.append(Spacer(1, 12))

    # ── Línea divisora ───────────────────────────
    elements.append(HRFlowable(width="100%", thickness=1,
                                color=colors.HexColor("#3DD68C")))
    elements.append(Spacer(1, 10))

    # ── Info factura ─────────────────────────────
    info_style  = ParagraphStyle("info", fontSize=10, fontName="Helvetica", leading=16)
    label_style = ParagraphStyle("label", fontSize=10, fontName="Helvetica-Bold", leading=16)

    info_data = [
        [Paragraph("<b>Factura N°:</b>", label_style), Paragraph(str(invoice_id), info_style),
         Paragraph("<b>Fecha:</b>",    label_style), Paragraph(datetime.now().strftime("%d/%m/%Y %H:%M"), info_style)],
        [Paragraph("<b>Cliente:</b>",  label_style), Paragraph(customer, info_style), "", ""],
    ]
    info_table = Table(info_data, colWidths=[3*cm, 8*cm, 2.5*cm, 5*cm])
    info_table.setStyle(TableStyle([
        ("VALIGN",  (0,0), (-1,-1), "TOP"),
        ("SPAN",    (1,1), (3,1)),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 14))

    # ── Tabla de productos ───────────────────────
    header_row = ["Producto", "Cant.", f"Precio ({currency})", f"Total ({currency})"]
    if tax_rate > 0:
        header_row.append(f"ITBIS {tax_rate:.0f}%")

    data = [header_row]
    subtotal = 0.0

    for item in cart:
        row_total = item["total"]
        subtotal += row_total
        row = [
            item["name"],
            str(item["quantity"]),
            f"{currency} {item['price']:,.2f}",
            f"{currency} {row_total:,.2f}",
        ]
        if tax_rate > 0:
            itbis = row_total * tax_rate / 100
            row.append(f"{currency} {itbis:,.2f}")
        data.append(row)

    col_widths = [9*cm, 2*cm, 3.5*cm, 3.5*cm]
    if tax_rate > 0:
        col_widths.append(3*cm)

    prod_table = Table(data, colWidths=col_widths)
    prod_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  colors.HexColor("#1A1D27")),
        ("TEXTCOLOR",     (0,0), (-1,0),  colors.HexColor("#3DD68C")),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,0),  10),
        ("ALIGN",         (1,0), (-1,-1), "RIGHT"),
        ("ALIGN",         (0,0), (0,-1),  "LEFT"),
        ("FONTSIZE",      (0,1), (-1,-1), 10),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [colors.HexColor("#F8F9FA"), colors.white]),
        ("GRID",          (0,0), (-1,-1), 0.5, colors.HexColor("#E0E0E0")),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ("RIGHTPADDING",  (0,0), (-1,-1), 8),
    ]))
    elements.append(prod_table)
    elements.append(Spacer(1, 14))

    # ── Totales ──────────────────────────────────
    tax_amount  = subtotal * tax_rate / 100
    grand_total = total   # total ya viene calculado con descuentos

    totals_data = []
    if subtotal != grand_total:
        totals_data.append(["Subtotal:", f"{currency} {subtotal:,.2f}"])
        totals_data.append([f"Descuentos:", f"- {currency} {subtotal - grand_total:,.2f}"])
    if tax_rate > 0:
        totals_data.append([f"ITBIS ({tax_rate:.0f}%):", f"{currency} {tax_amount:,.2f}"])
    totals_data.append(["TOTAL:", f"{currency} {grand_total:,.2f}"])

    tot_style = ParagraphStyle("tot", fontSize=10, fontName="Helvetica")
    tot_bold  = ParagraphStyle("totb", fontSize=12, fontName="Helvetica-Bold",
                                textColor=colors.HexColor("#3DD68C"))

    tot_rows = []
    for label, value in totals_data:
        st = tot_bold if label == "TOTAL:" else tot_style
        tot_rows.append([Paragraph(label, st), Paragraph(value, st)])

    tot_table = Table(tot_rows, colWidths=[5*cm, 4*cm], hAlign="RIGHT")
    tot_table.setStyle(TableStyle([
        ("ALIGN",  (0,0), (-1,-1), "RIGHT"),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LINEABOVE", (0,-1), (-1,-1), 1, colors.HexColor("#3DD68C")),
    ]))
    elements.append(tot_table)
    elements.append(Spacer(1, 20))

    # ── Pie de página ────────────────────────────
    elements.append(HRFlowable(width="100%", thickness=0.5,
                                color=colors.HexColor("#8B8FA8")))
    elements.append(Spacer(1, 8))
    footer_style = ParagraphStyle("footer", fontSize=9, fontName="Helvetica",
                                   textColor=colors.HexColor("#8B8FA8"), alignment=1)
    elements.append(Paragraph(footer_msg, footer_style))

    doc.build(elements)
    return filename