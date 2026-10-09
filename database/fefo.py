"""
database/fefo.py — Lógica FEFO (First Expired, First Out) para FarmaFactura Pro.
Descuenta stock consumiendo primero el lote que vence antes.
Usado por: cash_register_ui.py al confirmar ventas.
"""
from database.connection import create_connection
from auth import session


def sync_product_cost(cur, product_id: int):
    """
    Recalcula products.cost como el costo promedio ponderado de los lotes
    activos con existencia (cost * quantity_available, ponderado por cantidad).
    Se llama cada vez que se recibe, edita, ajusta o retira un lote —o se
    registra una compra—, ya que cualquiera de esas acciones cambia la mezcla
    de costos del inventario.
    Si no queda ningún lote activo con stock, se deja el último costo conocido
    (no se resetea a 0), para no perder la referencia de costo del producto.
    """
    cur.execute("""SELECT cost, quantity_available FROM lots
                   WHERE product_id=%s AND status='activo' AND quantity_available>0""",
                (product_id,))
    rows = cur.fetchall() or []
    total_qty = sum(int(q) for _, q in rows)
    if total_qty > 0:
        weighted = sum(float(c) * int(q) for c, q in rows) / total_qty
        cur.execute("UPDATE products SET cost=%s WHERE id=%s",
                    (round(weighted, 2), product_id))


def get_stock_total(product_id: int) -> int:
    """Retorna el stock total disponible de un producto sumando todos sus lotes activos."""
    with create_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT COALESCE(SUM(quantity_available), 0)
            FROM lots
            WHERE product_id = %s
              AND status = 'activo'
              AND quantity_available > 0
        """, (product_id,))
        row = cur.fetchone()
        return int(row[0]) if row else 0


def get_proxima_vencimiento(product_id: int):
    """Retorna la fecha de vencimiento más próxima entre los lotes activos de un producto."""
    with create_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT MIN(expiry_date)
            FROM lots
            WHERE product_id = %s
              AND status = 'activo'
              AND quantity_available > 0
        """, (product_id,))
        row = cur.fetchone()
        return row[0] if row else None


def descontar_stock_fefo(product_id: int, cantidad: int,
                         invoice_id: int = None, username: str = None) -> dict:
    """
    Descuenta 'cantidad' unidades del producto usando FEFO:
    el lote que vence antes se consume primero.

    Retorna:
        {"ok": True,  "lotes_usados": [...]}
        {"ok": False, "error": "mensaje"}
    """
    if username is None:
        u = session.current_user
        username = u[1] if isinstance(u, tuple) and len(u) > 1 else str(u or "sistema")

    with create_connection() as conn:
        cur = conn.cursor()

        # 1. Verificar stock total
        cur.execute("""
            SELECT COALESCE(SUM(quantity_available), 0)
            FROM lots
            WHERE product_id = %s AND status = 'activo'
        """, (product_id,))
        stock_total = int(cur.fetchone()[0])

        if stock_total < cantidad:
            return {
                "ok": False,
                "error": (f"Stock insuficiente. "
                          f"Disponible: {stock_total}, solicitado: {cantidad}")
            }

        # 2. Lotes ordenados FEFO: el que vence antes es el primero
        cur.execute("""
            SELECT id, lot_number, quantity_available, expiry_date
            FROM lots
            WHERE product_id = %s
              AND status = 'activo'
              AND quantity_available > 0
            ORDER BY expiry_date ASC
        """, (product_id,))
        lotes = cur.fetchall()

        # 3. Consumir lotes en orden hasta cubrir la cantidad
        restante = cantidad
        lotes_usados = []

        for lot_id, lot_number, qty_disp, expiry in lotes:
            if restante <= 0:
                break

            consumido       = min(restante, int(qty_disp))
            nuevo_disp      = int(qty_disp) - consumido
            nuevo_status    = "agotado" if nuevo_disp == 0 else "activo"

            cur.execute("""
                UPDATE lots
                SET quantity_available = %s, status = %s
                WHERE id = %s
            """, (nuevo_disp, nuevo_status, lot_id))

            # Registrar movimiento de auditoría
            cur.execute("""
                INSERT INTO lot_movements
                    (lot_id, type, quantity, reason, invoice_id, username, timestamp)
                VALUES (%s, 'salida', %s, 'Venta FEFO', %s, %s, NOW())
            """, (lot_id, consumido, invoice_id, username))

            lotes_usados.append({
                "lot_id":      lot_id,
                "lot_number":  lot_number,
                "consumido":   consumido,
                "expiry_date": str(expiry) if expiry else "—"
            })
            restante -= consumido

        # 4. Sincronizar products.stock con la suma real de lotes
        cur.execute("""
            UPDATE products
            SET stock = (
                SELECT COALESCE(SUM(quantity_available), 0)
                FROM lots
                WHERE product_id = %s AND status = 'activo'
            )
            WHERE id = %s
        """, (product_id, product_id))

        # conn.__exit__ hace commit automático gracias a _CompatConnection
        return {"ok": True, "lotes_usados": lotes_usados}


def reponer_stock_fefo(product_id: int, cantidad: int,
                       lot_id: int = None, username: str = None) -> dict:
    """
    Revierte una salida FEFO (por cancelación de venta, por ejemplo).
    Si se da lot_id, devuelve al lote específico; si no, al lote más reciente.
    """
    if username is None:
        u = session.current_user
        username = u[1] if isinstance(u, tuple) and len(u) > 1 else str(u or "sistema")

    with create_connection() as conn:
        cur = conn.cursor()

        if lot_id:
            cur.execute("""
                UPDATE lots
                SET quantity_available = quantity_available + %s,
                    status = 'activo'
                WHERE id = %s
            """, (cantidad, lot_id))
        else:
            # Reponer al lote activo más reciente del producto
            cur.execute("""
                SELECT id FROM lots
                WHERE product_id = %s AND status IN ('activo','agotado')
                ORDER BY received_date DESC LIMIT 1
            """, (product_id,))
            row = cur.fetchone()
            if not row:
                return {"ok": False, "error": "No se encontró lote para reponer"}
            lot_id = row[0]
            cur.execute("""
                UPDATE lots
                SET quantity_available = quantity_available + %s, status = 'activo'
                WHERE id = %s
            """, (cantidad, lot_id))

        cur.execute("""
            INSERT INTO lot_movements
                (lot_id, type, quantity, reason, username, timestamp)
            VALUES (%s, 'entrada', %s, 'Reversión de venta', %s, NOW())
        """, (lot_id, cantidad, username))

        cur.execute("""
            UPDATE products
            SET stock = (
                SELECT COALESCE(SUM(quantity_available), 0)
                FROM lots WHERE product_id = %s AND status = 'activo'
            )
            WHERE id = %s
        """, (product_id, product_id))

        return {"ok": True}
