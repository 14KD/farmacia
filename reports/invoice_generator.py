"""
reports/invoice_generator.py — Factura de venta en texto plano (.txt),
formato profesional compatible con impresoras térmicas de 80 mm.

Este módulo SOLO controla el formato de salida del .txt. No participa en el
cálculo de subtotal/ITBIS/descuento/total (eso ya viene resuelto en `cart` y
`total` desde ui/invoices_ui.py) ni toca la base de datos con escrituras —
solo hace un SELECT de solo lectura para completar teléfono/dirección del
cliente cuando no se pasan explícitamente.
"""
import config
from datetime import datetime
from textwrap import wrap
from auth import session
from database.connection import create_connection

W = 48  # ancho de línea — coincide con el ancho estándar de 48 columnas
        # (Font A) de las impresoras térmicas de 80mm.


def _cashier_from_session() -> str:
    u = session.current_user
    if isinstance(u, tuple) and len(u) > 1:
        return u[1]
    return str(u) if u else "—"


def _lookup_customer(name: str):
    """Busca teléfono/dirección del cliente por nombre exacto. Solo lectura;
    si no se encuentra o falla la conexión, retorna cadenas vacías."""
    try:
        conn = create_connection()
        cur = conn.cursor()
        cur.execute("SELECT phone, address FROM customers WHERE name=%s LIMIT 1",
                    (name,))
        row = cur.fetchone()
        conn.close()
        if row:
            return row[0] or "", row[1] or ""
    except Exception:
        pass
    return "", ""


def generate_invoice_txt(invoice_id, customer, cart, total, filename=None, *,
                          cashier=None, invoice_date=None,
                          customer_phone=None, customer_address=None,
                          discount_pct=0.0):
    """
    Genera la factura de venta en formato de texto plano (.txt).

    Firma original sin cambios: invoice_id, customer, cart, total, filename
    — el llamado ya existente en ui/invoices_ui.py sigue funcionando igual,
    sin tocar el proceso de venta.

    Parámetros nuevos, todos opcionales:
        cashier          : nombre del cajero; si no se pasa, se toma de la
                           sesión activa (auth.session.current_user).
        invoice_date      : datetime de la factura (default: ahora).
        customer_phone    : teléfono del cliente; si no se pasa, se busca en
                           `customers` por nombre exacto.
        customer_address  : dirección del cliente; igual que arriba.
        discount_pct      : % de descuento global aplicado al carrito
                           (mismo valor que ya usa reports/receipt_generator.py).
    """
    if invoice_date is None:
        invoice_date = datetime.now()
    if cashier is None:
        cashier = _cashier_from_session()
    if customer_phone is None or customer_address is None:
        looked_phone, looked_addr = _lookup_customer(customer)
        if customer_phone is None:
            customer_phone = looked_phone
        if customer_address is None:
            customer_address = looked_addr
    if filename is None:
        filename = f"Factura_{invoice_id}.txt"

    cfg      = config.load()
    ph = cfg["pharmacy"]
    pharmacy_name  = ph.get("name")  or "FarmaFactura Pro"
    pharmacy_rnc   = ph.get("rnc")   or ""
    pharmacy_phone = ph.get("phone") or ""
    bl       = cfg["billing"]
    currency = bl.get("currency") or "RD$"

    lines = []

    def rule(ch="-"):
        lines.append(ch * W)

    def center(text=""):
        lines.append(text.center(W))

    def money(value):
        return f"{currency}{value:,.2f}"

    def labeled(label, value, width=9):
        lines.append(f"{label:<{width}}: {value}")

    def total_row(label, value):
        lines.append(f"{label:<20}{value:>{W - 20}}")

    def row3(desc, itbis, valor, mark=""):
        # Espacios explícitos entre columnas (no solo ancho fijo): si un
        # monto llena exactamente su columna, igual queda separado del
        # siguiente en vez de pegarse (ej. "RD$745.20RD$4,885.20").
        seg = f"{desc:<18} {itbis:>11} {valor:>10}"
        if mark:
            seg += f" {mark}"
        lines.append(seg)

    # ── Nombre de la farmacia ────────────────────────────────────────────────
    center(pharmacy_name)
    if pharmacy_rnc:   center(f"RNC: {pharmacy_rnc}")
    if pharmacy_phone: center(f"Tel: {pharmacy_phone}")
    rule()

    # ── Fecha / Cajero ───────────────────────────────────────────────────────
    hour12 = invoice_date.strftime("%I:%M:%S")
    ampm   = "a.m." if invoice_date.hour < 12 else "p.m."
    lines.append(f"Fecha: {invoice_date.strftime('%d/%m/%Y')} {hour12} {ampm}")
    labeled("Cajero", cashier)
    rule()

    # ── Datos del cliente ────────────────────────────────────────────────────
    center("DATOS DEL CLIENTE")
    rule()
    labeled("CLIENTE", customer)
    labeled("TELEFONO", customer_phone or "—")
    labeled("DIRECCION", customer_address or "—")
    rule()

    # ── Detalle ──────────────────────────────────────────────────────────────
    row3("DESCRIPCION", "ITBIS", "VALOR")
    rule()

    subtotal_sum = 0.0
    itbis_sum    = 0.0

    for item in cart:
        qty        = item["quantity"]
        unit_price = item.get("price", 0)
        line_itbis = item.get("itbis", 0.0)
        line_total = item.get("total", qty * unit_price + line_itbis)
        line_sub   = item.get("subtotal", qty * unit_price)
        tax_flag   = "G" if item.get("applies_itbis", True) else "E"

        subtotal_sum += line_sub
        itbis_sum    += line_itbis

        name_lines = wrap(item["name"].upper(), width=W) or [""]
        for extra in name_lines[:-1]:
            lines.append(extra)
        lines.append(name_lines[-1] + "*")

        desc = f"{qty} x {money(unit_price)}"
        row3(desc, money(line_itbis), money(line_total), tax_flag)

    rule()

    # ── Totales ──────────────────────────────────────────────────────────────
    grand_total = total  # ya viene calculado (incluye el descuento global)
    disc_amt    = (subtotal_sum + itbis_sum) * discount_pct / 100

    total_row("SUBTOTAL", money(subtotal_sum))
    total_row(f"DESCUENTO {discount_pct:.0f}%", money(disc_amt))
    total_row("ITBIS", money(itbis_sum))
    total_row("TOTAL A PAGAR", money(grand_total))

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return filename
