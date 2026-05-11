from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter

from reportlab.platypus.flowables import HRFlowable

from datetime import datetime


def generate_invoice_pdf(
    invoice_id,
    customer,
    cart,
    total
):

    filename = f"Factura_{invoice_id}.pdf"

    pdf = SimpleDocTemplate(
        filename,
        pagesize=letter
    )

    elements = []

    styles = getSampleStyleSheet()

    # =====================================
    # TITULO
    # =====================================

    title = Paragraph(
        "<b>FARMACIA POS</b>",
        styles["Title"]
    )

    elements.append(title)

    elements.append(Spacer(1, 12))

    # =====================================
    # INFORMACION FACTURA
    # =====================================

    invoice_info = Paragraph(
        f'''
        <b>Factura:</b> #{invoice_id}<br/>
        <b>Cliente:</b> {customer}<br/>
        <b>Fecha:</b> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        ''',
        styles["BodyText"]
    )

    elements.append(invoice_info)

    elements.append(Spacer(1, 12))

    elements.append(HRFlowable())

    elements.append(Spacer(1, 12))

    # =====================================
    # TABLA PRODUCTOS
    # =====================================

    data = [
        [
            "Producto",
            "Cantidad",
            "Precio",
            "Total"
        ]
    ]

    for item in cart:

        data.append([
            item["name"],
            item["quantity"],
            f"${item['price']:.2f}",
            f"${item['total']:.2f}"
        ])

    table = Table(data)

    table.setStyle(TableStyle([

        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),

        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),

        ("ALIGN", (0, 0), (-1, -1), "CENTER"),

        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),

        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),

        ("GRID", (0, 0), (-1, -1), 1, colors.black)

    ]))

    elements.append(table)

    elements.append(Spacer(1, 20))

    # =====================================
    # TOTAL
    # =====================================

    total_text = Paragraph(
        f"<b>TOTAL: ${total:.2f}</b>",
        styles["Heading2"]
    )

    elements.append(total_text)

    pdf.build(elements)

    return filename