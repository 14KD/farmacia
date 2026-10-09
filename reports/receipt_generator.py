"""
receipt_generator.py
Genera comprobantes de venta en formato térmico (80mm) y carta,
listos para impresión física.
"""
import os
from datetime import datetime
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable, KeepTogether
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import mm, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

import config


# ── Ancho ticket térmico 80mm ──────────────────────────────────────────────
TICKET_W = 80 * mm
TICKET_H = 297 * mm   # alto variable, se recorta al imprimir

# Colores del ticket
C_BLACK  = colors.HexColor("#0F1117")
C_DARK   = colors.HexColor("#1A1D27")
C_GREEN  = colors.HexColor("#3DD68C")
C_GRAY   = colors.HexColor("#8B8FA8")
C_WHITE  = colors.white
C_LINE   = colors.HexColor("#CCCCCC")


def _styles():
    """Estilos de párrafo del comprobante."""
    base = {"fontName": "Helvetica", "leading": 14}

    return {
        "ph_name":   ParagraphStyle("ph_name",   fontSize=14, fontName="Helvetica-Bold",
                                     alignment=TA_CENTER, spaceAfter=2, textColor=C_BLACK),
        "ph_sub":    ParagraphStyle("ph_sub",     fontSize=8,  fontName="Helvetica",
                                     alignment=TA_CENTER, spaceAfter=1, textColor=C_GRAY),
        "title":     ParagraphStyle("title",      fontSize=11, fontName="Helvetica-Bold",
                                     alignment=TA_CENTER, spaceAfter=4, textColor=C_BLACK),
        "center":    ParagraphStyle("center",     fontSize=9,  fontName="Helvetica",
                                     alignment=TA_CENTER, spaceAfter=2, textColor=C_BLACK),
        "left":      ParagraphStyle("left",       fontSize=9,  fontName="Helvetica",
                                     alignment=TA_LEFT,   spaceAfter=1, textColor=C_BLACK),
        "left_bold": ParagraphStyle("left_bold",  fontSize=9,  fontName="Helvetica-Bold",
                                     alignment=TA_LEFT,   spaceAfter=1, textColor=C_BLACK),
        "right":     ParagraphStyle("right",      fontSize=9,  fontName="Helvetica",
                                     alignment=TA_RIGHT,  spaceAfter=1, textColor=C_BLACK),
        "total_lbl": ParagraphStyle("total_lbl",  fontSize=11, fontName="Helvetica-Bold",
                                     alignment=TA_LEFT,   textColor=C_BLACK),
        "total_val": ParagraphStyle("total_val",  fontSize=13, fontName="Helvetica-Bold",
                                     alignment=TA_RIGHT,  textColor=C_BLACK),
        "footer":    ParagraphStyle("footer",     fontSize=8,  fontName="Helvetica",
                                     alignment=TA_CENTER, textColor=C_GRAY, leading=12),
    }


def _hr(width=None):
    return HRFlowable(width=width or "100%", thickness=0.5,
                      color=C_LINE, spaceAfter=4, spaceBefore=4)


def generate_receipt(invoice_id, customer, cart, total,
                     payment_method="Efectivo", cashier="—",
                     invoice_date=None, discount_pct=0.0,
                     filename=None) -> str:
    """
    Genera el comprobante de venta en PDF.

    Parámetros:
        invoice_id     : Número de factura
        customer       : Nombre del cliente
        cart           : Lista de items del carrito
        total          : Total final
        payment_method : Método de pago
        cashier        : Nombre del cajero
        invoice_date   : datetime de la factura (default: ahora)
        discount_pct   : % descuento global aplicado
        filename       : Ruta de salida (default: Comprobante_XXXX.pdf)
    """
    cfg      = config.load()
    ph       = cfg["pharmacy"]
    bl       = cfg["billing"]

    ph_name  = ph.get("name")    or "FarmaFactura Pro"
    ph_addr  = ph.get("address") or ""
    ph_phone = ph.get("phone")   or ""
    ph_rnc   = ph.get("rnc")     or ""
    footer   = bl.get("footer")  or "Gracias por su compra."
    currency = bl.get("currency") or "$"
    tax_rate = float(bl.get("tax_rate") or 0)

    if invoice_date is None:
        invoice_date = datetime.now()

    if filename is None:
        filename = f"Comprobante_{invoice_id:06d}.pdf"

    ST = _styles()
    W  = TICKET_W - 8 * mm   # margen interno
    M  = 4 * mm

    doc = SimpleDocTemplate(
        filename,
        pagesize=(TICKET_W, TICKET_H),
        leftMargin=M, rightMargin=M,
        topMargin=M,  bottomMargin=M,
    )

    elems = []

    # ── ENCABEZADO ─────────────────────────────────────────────────────────
    elems.append(Paragraph(ph_name, ST["ph_name"]))
    if ph_addr:
        elems.append(Paragraph(ph_addr, ST["ph_sub"]))
    if ph_phone:
        elems.append(Paragraph(f"Tel: {ph_phone}", ST["ph_sub"]))
    if ph_rnc:
        elems.append(Paragraph(f"RNC: {ph_rnc}", ST["ph_sub"]))

    elems.append(_hr())
    elems.append(Paragraph("COMPROBANTE DE VENTA", ST["title"]))
    elems.append(_hr())

    # ── DATOS DE LA FACTURA ────────────────────────────────────────────────
    meta = [
        [Paragraph(f"<b>N° Factura:</b>  #{invoice_id:06d}", ST["left_bold"]), ""],
        [Paragraph(f"Fecha:  {invoice_date.strftime('%d/%m/%Y')}", ST["left"]),
         Paragraph(f"Hora:  {invoice_date.strftime('%I:%M %p')}", ST["right"])],
        [Paragraph(f"Cajero:  {cashier}", ST["left"]), ""],
        [Paragraph(f"Cliente:  {customer}", ST["left"]), ""],
        [Paragraph(f"Pago:  {payment_method}", ST["left"]), ""],
    ]
    meta_tbl = Table(meta, colWidths=[W * 0.6, W * 0.4])
    meta_tbl.setStyle(TableStyle([
        ("TOPPADDING",    (0,0), (-1,-1), 1),
        ("BOTTOMPADDING", (0,0), (-1,-1), 1),
        ("LEFTPADDING",   (0,0), (-1,-1), 0),
        ("RIGHTPADDING",  (0,0), (-1,-1), 0),
        ("SPAN",          (0,0), (1,0)),
        ("SPAN",          (0,2), (1,2)),
        ("SPAN",          (0,3), (1,3)),
        ("SPAN",          (0,4), (1,4)),
    ]))
    elems.append(meta_tbl)
    elems.append(_hr())

    # ── PRODUCTOS ──────────────────────────────────────────────────────────
    h_style = ParagraphStyle("th", fontSize=8, fontName="Helvetica-Bold",
                              alignment=TA_CENTER, textColor=C_BLACK)
    header_row = [
        Paragraph("PRODUCTO",      h_style),
        Paragraph("CANT.",         h_style),
        Paragraph("P.UNIT.",       h_style),
    ]
    if tax_rate > 0:
        header_row.append(Paragraph(f"ITBIS\n{tax_rate:.0f}%", h_style))
    header_row.append(Paragraph("TOTAL", h_style))

    rows = [header_row]
    subtotal_sum = 0.0
    itbis_sum    = 0.0

    for item in cart:
        sub   = item.get("subtotal", item["quantity"] * item["price"])
        itbis = item.get("itbis", 0.0)
        subtotal_sum += sub
        itbis_sum    += itbis

        name = item["name"]
        disc = item.get("discount", 0)
        if disc > 0:
            name += f"\n  (Desc. {disc:.0f}%)"

        prod_style = ParagraphStyle("prod", fontSize=8, fontName="Helvetica",
                                     alignment=TA_LEFT, leading=10)
        num_style  = ParagraphStyle("num",  fontSize=8, fontName="Helvetica",
                                     alignment=TA_RIGHT)
        cen_style  = ParagraphStyle("cen",  fontSize=8, fontName="Helvetica",
                                     alignment=TA_CENTER)

        row = [
            Paragraph(name, prod_style),
            Paragraph(str(item["quantity"]), cen_style),
            Paragraph(f"{currency} {item['price']:,.2f}", num_style),
        ]
        if tax_rate > 0:
            row.append(Paragraph(f"{currency} {itbis:,.2f}", num_style))
        row.append(Paragraph(f"{currency} {item['total']:,.2f}", num_style))
        rows.append(row)

    # Anchos de columna según columnas disponibles
    if tax_rate > 0:
        col_w = [W*0.34, W*0.10, W*0.18, W*0.16, W*0.22]
    else:
        col_w = [W*0.38, W*0.12, W*0.22, W*0.28]

    prod_tbl = Table(rows, colWidths=col_w)
    prod_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  colors.HexColor("#E8F5EE")),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 8),
        ("TOPPADDING",    (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("LEFTPADDING",   (0,0), (-1,-1), 2),
        ("RIGHTPADDING",  (0,0), (-1,-1), 2),
        ("LINEBELOW",     (0,0), (-1,0),  0.5, C_LINE),
        ("LINEBELOW",     (0,-1),(-1,-1), 0.5, C_LINE),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [colors.white, colors.HexColor("#F8F8F8")]),
    ]))
    elems.append(prod_tbl)
    elems.append(Spacer(1, 4))

    # ── TOTALES ────────────────────────────────────────────────────────────
    disc_amt = (subtotal_sum + itbis_sum) * discount_pct / 100

    def _tot_row(label, value, bold=False, big=False):
        fn  = "Helvetica-Bold" if bold else "Helvetica"
        sz  = 10 if big else 8
        lbl = ParagraphStyle("l", fontSize=sz, fontName=fn, alignment=TA_LEFT)
        val = ParagraphStyle("v", fontSize=sz, fontName=fn, alignment=TA_RIGHT)
        return [Paragraph(label, lbl), Paragraph(value, val)]

    totals_data = [_tot_row("Subtotal:", f"{currency} {subtotal_sum:,.2f}")]
    if tax_rate > 0:
        totals_data.append(_tot_row(
            f"ITBIS ({tax_rate:.0f}%):", f"{currency} {itbis_sum:,.2f}"
        ))
    if disc_amt > 0:
        totals_data.append(_tot_row(
            f"Descuento ({discount_pct:.0f}%):", f"- {currency} {disc_amt:,.2f}"
        ))
    totals_data.append(_tot_row(
        "TOTAL A PAGAR:", f"{currency} {total:,.2f}", bold=True, big=True
    ))

    tot_tbl = Table(totals_data, colWidths=[W*0.55, W*0.45])
    tot_tbl.setStyle(TableStyle([
        ("TOPPADDING",    (0,0), (-1,-1), 2),
        ("BOTTOMPADDING", (0,0), (-1,-1), 2),
        ("LEFTPADDING",   (0,0), (-1,-1), 0),
        ("RIGHTPADDING",  (0,0), (-1,-1), 0),
        ("LINEABOVE",     (0,-1), (-1,-1), 1, C_BLACK),
    ]))
    elems.append(tot_tbl)
    elems.append(_hr())

    # ── MÉTODO DE PAGO ─────────────────────────────────────────────────────
    elems.append(Paragraph(f"<b>Forma de pago:</b>  {payment_method}", ST["left_bold"]))
    elems.append(Spacer(1, 6))

    # ── PIE ────────────────────────────────────────────────────────────────
    elems.append(_hr())
    elems.append(Paragraph(footer, ST["footer"]))
    elems.append(Paragraph(
        f"Comprobante generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        ST["footer"]
    ))
    elems.append(Spacer(1, 8))

    # Línea de corte
    elems.append(HRFlowable(width="100%", thickness=1, color=C_LINE,
                              dash=(3, 3), spaceAfter=4))
    elems.append(Paragraph("✂  Cortar aquí", ST["footer"]))

    doc.build(elems)
    return os.path.abspath(filename)
