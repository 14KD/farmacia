"""
database/purchases.py — Lógica de negocio del módulo de Compras.
Registra encabezado (purchases) + detalle (purchase_details) y reutiliza el
mismo mecanismo de lotes/FEFO que Lotes y Ventas: cada línea de compra crea
un lote en `lots`, cuyo INSERT dispara los triggers que sincronizan
products.stock automáticamente (ver database/schema.py).
"""
from datetime import datetime
from database.connection import create_connection
from database.fefo import sync_product_cost
import config as _config


def _friendly_db_error(e: Exception) -> str:
    """Traduce errores crudos de MariaDB comunes a mensajes claros en español."""
    msg = str(e)
    if "1264" in msg or "Out of range value" in msg:
        return ("Uno de los montos de la compra es demasiado grande para guardarse. "
                "Revisa las cantidades y precios ingresados — probablemente sobra "
                "un dígito en algún campo.")
    return msg


def _invoice_already_registered(cur, supplier_id: int, invoice_number: str,
                                 exclude_purchase_id: int = None) -> bool:
    sql = "SELECT id FROM purchases WHERE supplier_id=%s AND invoice_number=%s"
    params = [supplier_id, invoice_number]
    if exclude_purchase_id:
        sql += " AND id != %s"
        params.append(exclude_purchase_id)
    cur.execute(sql, params)
    return cur.fetchone() is not None


def register_purchase(header: dict, items: list, username: str, user_id: int = None) -> dict:
    """
    header: {"supplier_id", "invoice_number", "purchase_date" ("YYYY-MM-DD HH:MM:SS"),
             "payment_method", "due_date" ("YYYY-MM-DD"|None), "subtotal", "tax",
             "discount", "total", "notes"}
    items:  [{"product_id", "product_name", "batch", "expiration_date" ("YYYY-MM-DD"|None),
              "quantity", "unit_cost", "discount", "tax", "subtotal", "total"}, ...]

    Transacción atómica: si algo falla, se revierte todo (rollback automático
    de _CompatConnection al salir del `with` por una excepción).

    Retorna {"ok": True, "purchase_id": int} o {"ok": False, "error": str}.
    """
    if not items:
        return {"ok": False, "error": "La compra no tiene productos agregados."}
    if not header.get("supplier_id"):
        return {"ok": False, "error": "Selecciona un proveedor válido de la lista."}
    if header.get("payment_method") == "Crédito" and not header.get("due_date"):
        return {"ok": False,
                "error": "La fecha de vencimiento de pago es obligatoria para compras a crédito."}

    for it in items:
        try:
            qty  = int(it["quantity"])
            cost = float(it["unit_cost"])
        except (KeyError, TypeError, ValueError):
            return {"ok": False,
                    "error": f"Datos inválidos en el producto '{it.get('product_name','?')}'."}
        if qty <= 0:
            return {"ok": False,
                    "error": f"Cantidad inválida en '{it.get('product_name','?')}': debe ser mayor que cero."}
        if cost < 0:
            return {"ok": False,
                    "error": f"Precio de compra inválido en '{it.get('product_name','?')}': no puede ser negativo."}
        if not it.get("expiration_date"):
            return {"ok": False,
                    "error": f"La fecha de vencimiento es obligatoria en '{it.get('product_name','?')}'."}

    invoice_number = (header.get("invoice_number") or "").strip()
    prevent_dup = _config.load().get("purchases", {}).get("prevent_duplicate_invoice", True)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    purchase_date = header.get("purchase_date") or ts
    try:
        received_date = datetime.strptime(purchase_date[:10], "%Y-%m-%d").date().isoformat()
    except Exception:
        received_date = purchase_date[:10]

    try:
        with create_connection() as conn:
            cur = conn.cursor()

            if prevent_dup and invoice_number:
                if _invoice_already_registered(cur, header["supplier_id"], invoice_number):
                    return {"ok": False,
                            "error": f"Ya existe una compra registrada con la factura "
                                     f"'{invoice_number}' para este proveedor."}

            cur.execute("""
                INSERT INTO purchases
                    (supplier_id, invoice_number, purchase_date, payment_method, due_date,
                     subtotal, tax, discount, total, status, user_id, notes)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'registrada',%s,%s)
            """, (header["supplier_id"], invoice_number or None, purchase_date,
                  header.get("payment_method"), header.get("due_date") or None,
                  header.get("subtotal", 0), header.get("tax", 0), header.get("discount", 0),
                  header.get("total", 0), user_id, header.get("notes", "")))
            purchase_id = cur.lastrowid

            notes_ref = f"Compra #{purchase_id}"
            if invoice_number:
                notes_ref += f" | Factura: {invoice_number}"

            for idx, it in enumerate(items, start=1):
                pid       = int(it["product_id"])
                batch     = (it.get("batch") or "").strip() or f"COMPRA-{purchase_id}-{idx:03d}"
                expiry    = it.get("expiration_date") or None
                qty       = int(it["quantity"])
                unit_cost = float(it["unit_cost"])

                # Insertar en `lots` dispara trg_lots_after_insert, que ya
                # sincroniza products.stock — mismo mecanismo que usan
                # Lotes (recepción) y Ventas (FEFO). Se crea primero para
                # poder enlazar purchase_details.lot_id (necesario al editar
                # la compra más adelante).
                cur.execute("""
                    INSERT INTO lots
                        (product_id, lot_number, quantity_received, quantity_available,
                         cost, expiry_date, received_date, supplier_id, notes, status)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'activo')
                """, (pid, batch, qty, qty, unit_cost, expiry, received_date,
                      header["supplier_id"], notes_ref))
                lot_id = cur.lastrowid

                cur.execute("""
                    INSERT INTO purchase_details
                        (purchase_id, product_id, lot_id, batch, expiration_date,
                         quantity, unit_cost, discount, tax, subtotal, total)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (purchase_id, pid, lot_id, batch, expiry, qty, unit_cost,
                      it.get("discount", 0), it.get("tax", 0),
                      it.get("subtotal", 0), it.get("total", 0)))

                cur.execute("""
                    INSERT INTO lot_movements
                        (lot_id, type, quantity, reason, username, timestamp)
                    VALUES (%s,'entrada',%s,'Compra',%s,%s)
                """, (lot_id, qty, username, ts))

                # Igual que en Lotes/Ventas: además del trigger, se sincroniza
                # stock y costo promedio explícitamente por consistencia.
                cur.execute("""
                    UPDATE products SET
                        stock = (SELECT COALESCE(SUM(quantity_available),0)
                                 FROM lots WHERE product_id=%s AND status='activo'),
                        manages_lots = 1
                    WHERE id=%s
                """, (pid, pid))
                sync_product_cost(cur, pid)

            return {"ok": True, "purchase_id": purchase_id}
    except Exception as e:
        return {"ok": False, "error": _friendly_db_error(e)}


def update_purchase(purchase_id: int, header: dict, items: list,
                     username: str, user_id: int = None) -> dict:
    """
    Edita una compra ya guardada, incluyendo cantidades/costos/lotes, con
    recálculo completo de inventario:
      - Línea existente (item con "pd_id"/"lot_id"): ajusta el MISMO lote en
        vez de crear uno nuevo. Si ya se consumió parte de ese lote (una
        venta lo usó), no se puede bajar la cantidad por debajo de lo ya
        consumido — se rechaza con un error claro.
      - Línea nueva (sin "pd_id"): crea un lote nuevo, igual que
        register_purchase().
      - Línea quitada por el usuario (existía antes, no viene en `items`):
        se retira el lote — pero solo si no tiene nada consumido; si ya se
        vendió algo de ese lote, se rechaza (hay que reducir la cantidad en
        vez de eliminar la línea).
    Transacción atómica con rollback automático ante cualquier error.

    Retorna {"ok": True, "purchase_id": int} o {"ok": False, "error": str}.
    """
    if not items:
        return {"ok": False, "error": "La compra no puede quedar sin productos."}
    if not header.get("supplier_id"):
        return {"ok": False, "error": "Selecciona un proveedor válido de la lista."}
    if header.get("payment_method") == "Crédito" and not header.get("due_date"):
        return {"ok": False,
                "error": "La fecha de vencimiento de pago es obligatoria para compras a crédito."}

    for it in items:
        try:
            qty  = int(it["quantity"])
            cost = float(it["unit_cost"])
        except (KeyError, TypeError, ValueError):
            return {"ok": False,
                    "error": f"Datos inválidos en el producto '{it.get('product_name','?')}'."}
        if qty <= 0:
            return {"ok": False,
                    "error": f"Cantidad inválida en '{it.get('product_name','?')}': debe ser mayor que cero."}
        if cost < 0:
            return {"ok": False,
                    "error": f"Precio de compra inválido en '{it.get('product_name','?')}': no puede ser negativo."}
        if not it.get("expiration_date"):
            return {"ok": False,
                    "error": f"La fecha de vencimiento es obligatoria en '{it.get('product_name','?')}'."}

    invoice_number = (header.get("invoice_number") or "").strip()
    prevent_dup = _config.load().get("purchases", {}).get("prevent_duplicate_invoice", True)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    purchase_date = header.get("purchase_date") or ts
    try:
        received_date = datetime.strptime(purchase_date[:10], "%Y-%m-%d").date().isoformat()
    except Exception:
        received_date = purchase_date[:10]

    try:
        with create_connection() as conn:
            cur = conn.cursor()

            cur.execute("SELECT id FROM purchases WHERE id=%s", (purchase_id,))
            if not cur.fetchone():
                return {"ok": False, "error": f"La compra #{purchase_id} ya no existe."}

            if prevent_dup and invoice_number:
                if _invoice_already_registered(cur, header["supplier_id"], invoice_number,
                                                exclude_purchase_id=purchase_id):
                    return {"ok": False,
                            "error": f"Ya existe otra compra registrada con la factura "
                                     f"'{invoice_number}' para este proveedor."}

            cur.execute("SELECT id, lot_id FROM purchase_details WHERE purchase_id=%s",
                        (purchase_id,))
            original = {row[0]: row[1] for row in cur.fetchall()}   # pd_id -> lot_id
            kept_pd_ids = {it["pd_id"] for it in items if it.get("pd_id")}
            removed_pd_ids = set(original.keys()) - kept_pd_ids

            affected_products = set()
            notes_ref = f"Compra #{purchase_id}"
            if invoice_number:
                notes_ref += f" | Factura: {invoice_number}"

            # 1) Líneas quitadas por el usuario: retirar el lote, solo si
            #    nada de ese lote fue consumido todavía.
            for pd_id in removed_pd_ids:
                lot_id = original.get(pd_id)
                if lot_id:
                    cur.execute("""SELECT product_id, quantity_received, quantity_available,
                                          lot_number FROM lots WHERE id=%s""", (lot_id,))
                    lot_row = cur.fetchone()
                    if lot_row:
                        lpid, qty_recv, qty_avail, lot_num = lot_row
                        consumed = int(qty_recv) - int(qty_avail)
                        if consumed > 0:
                            return {"ok": False,
                                    "error": f"No se puede quitar el lote '{lot_num}' de la compra: "
                                             f"ya se usaron/vendieron {consumed} unidad(es) de ese lote. "
                                             f"Reduce la cantidad en vez de eliminar la línea."}
                        cur.execute("""UPDATE lots SET status='retirado', quantity_available=0
                                       WHERE id=%s""", (lot_id,))
                        cur.execute("""INSERT INTO lot_movements
                                       (lot_id, type, quantity, reason, username, timestamp)
                                       VALUES (%s,'retiro',%s,%s,%s,%s)""",
                                    (lot_id, -int(qty_recv),
                                     f"Línea eliminada al editar compra #{purchase_id}",
                                     username, ts))
                        affected_products.add(lpid)
                cur.execute("DELETE FROM purchase_details WHERE id=%s", (pd_id,))

            # 2) Líneas actuales: actualizar (mismo lote) o insertar (lote nuevo).
            for idx, it in enumerate(items, start=1):
                pid       = int(it["product_id"])
                batch     = (it.get("batch") or "").strip()
                expiry    = it.get("expiration_date") or None
                qty       = int(it["quantity"])
                unit_cost = float(it["unit_cost"])
                pd_id     = it.get("pd_id")
                lot_id    = it.get("lot_id")

                if pd_id and lot_id:
                    cur.execute("""SELECT quantity_received, quantity_available, product_id
                                   FROM lots WHERE id=%s""", (lot_id,))
                    lot_row = cur.fetchone()
                    if not lot_row:
                        return {"ok": False,
                                "error": f"El lote de '{it.get('product_name','?')}' ya no existe."}
                    old_recv, old_avail, old_pid = lot_row
                    consumed = int(old_recv) - int(old_avail)
                    if qty < consumed:
                        return {"ok": False,
                                "error": f"No se puede bajar la cantidad de '{it.get('product_name','?')}' "
                                         f"(lote {batch or '—'}) a menos de {consumed}: ya se usaron/"
                                         f"vendieron esa cantidad de ese lote."}
                    new_avail   = qty - consumed
                    batch_final = batch or f"COMPRA-{purchase_id}-{idx:03d}"

                    cur.execute("""UPDATE lots SET
                            product_id=%s, lot_number=%s, quantity_received=%s,
                            quantity_available=%s, cost=%s, expiry_date=%s,
                            received_date=%s, supplier_id=%s, notes=%s, status='activo'
                        WHERE id=%s""",
                        (pid, batch_final, qty, new_avail, unit_cost, expiry,
                         received_date, header["supplier_id"], notes_ref, lot_id))

                    delta = qty - int(old_recv)
                    if delta != 0:
                        cur.execute("""INSERT INTO lot_movements
                                (lot_id, type, quantity, reason, username, timestamp)
                                VALUES (%s,'ajuste',%s,%s,%s,%s)""",
                            (lot_id, delta, f"Edición de compra #{purchase_id}", username, ts))

                    cur.execute("""UPDATE purchase_details SET
                            product_id=%s, batch=%s, expiration_date=%s, quantity=%s,
                            unit_cost=%s, discount=%s, tax=%s, subtotal=%s, total=%s
                        WHERE id=%s""",
                        (pid, batch_final, expiry, qty, unit_cost,
                         it.get("discount", 0), it.get("tax", 0),
                         it.get("subtotal", 0), it.get("total", 0), pd_id))

                    affected_products.add(pid)
                    if old_pid != pid:
                        affected_products.add(old_pid)
                else:
                    batch_final = batch or f"COMPRA-{purchase_id}-{idx:03d}"
                    cur.execute("""INSERT INTO lots
                            (product_id, lot_number, quantity_received, quantity_available,
                             cost, expiry_date, received_date, supplier_id, notes, status)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'activo')""",
                        (pid, batch_final, qty, qty, unit_cost, expiry,
                         received_date, header["supplier_id"], notes_ref))
                    new_lot_id = cur.lastrowid

                    cur.execute("""INSERT INTO lot_movements
                            (lot_id, type, quantity, reason, username, timestamp)
                        VALUES (%s,'entrada',%s,'Compra',%s,%s)""",
                        (new_lot_id, qty, username, ts))

                    cur.execute("""INSERT INTO purchase_details
                            (purchase_id, product_id, lot_id, batch, expiration_date, quantity,
                             unit_cost, discount, tax, subtotal, total)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                        (purchase_id, pid, new_lot_id, batch_final, expiry, qty, unit_cost,
                         it.get("discount", 0), it.get("tax", 0),
                         it.get("subtotal", 0), it.get("total", 0)))

                    affected_products.add(pid)

            # 3) Resincronizar stock y costo promedio de cada producto afectado.
            for pid in affected_products:
                cur.execute("""UPDATE products SET
                        stock=(SELECT COALESCE(SUM(quantity_available),0)
                               FROM lots WHERE product_id=%s AND status='activo')
                    WHERE id=%s""", (pid, pid))
                sync_product_cost(cur, pid)

            # 4) Actualizar el encabezado.
            cur.execute("""UPDATE purchases SET
                    supplier_id=%s, invoice_number=%s, purchase_date=%s, payment_method=%s,
                    due_date=%s, subtotal=%s, tax=%s, discount=%s, total=%s, notes=%s
                WHERE id=%s""",
                (header["supplier_id"], invoice_number or None, purchase_date,
                 header.get("payment_method"), header.get("due_date") or None,
                 header.get("subtotal", 0), header.get("tax", 0), header.get("discount", 0),
                 header.get("total", 0), header.get("notes", ""), purchase_id))

            return {"ok": True, "purchase_id": purchase_id}
    except Exception as e:
        return {"ok": False, "error": _friendly_db_error(e)}


def search_purchases(supplier_name: str = "", invoice_number: str = "",
                      date_from: str = None, date_to: str = None) -> list:
    """
    Busca compras registradas con filtros opcionales. Retorna filas:
    (id, purchase_date, supplier_name, invoice_number, payment_method,
     subtotal, tax, discount, total, status)
    """
    conn = create_connection()
    try:
        cur = conn.cursor()
        sql = """SELECT p.id, p.purchase_date, s.name, p.invoice_number,
                        p.payment_method, p.subtotal, p.tax, p.discount,
                        p.total, p.status
                 FROM purchases p
                 JOIN suppliers s ON p.supplier_id = s.id
                 WHERE 1=1"""
        params = []
        if supplier_name:
            sql += " AND s.name LIKE %s"; params.append(f"%{supplier_name}%")
        if invoice_number:
            sql += " AND p.invoice_number LIKE %s"; params.append(f"%{invoice_number}%")
        if date_from:
            sql += " AND p.purchase_date >= %s"; params.append(date_from)
        if date_to:
            sql += " AND p.purchase_date <= %s"; params.append(date_to + " 23:59:59")
        sql += " ORDER BY p.purchase_date DESC, p.id DESC LIMIT 500"
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        conn.close()


def get_purchase_detail(purchase_id: int):
    """
    Retorna (header, lines):
      header: (id, purchase_date, supplier_id, supplier_name, invoice_number,
                payment_method, due_date, subtotal, tax, discount, total, notes, status)
      lines:  [(pd_id, product_id, product_name, batch, expiration_date, quantity,
                 unit_cost, tax, discount, subtotal, total, lot_id), ...]
    """
    conn = create_connection()
    try:
        cur = conn.cursor()
        cur.execute("""SELECT p.id, p.purchase_date, p.supplier_id, s.name, p.invoice_number,
                              p.payment_method, p.due_date, p.subtotal, p.tax, p.discount,
                              p.total, p.notes, p.status
                       FROM purchases p
                       JOIN suppliers s ON p.supplier_id = s.id
                       WHERE p.id = %s""", (purchase_id,))
        header = cur.fetchone()
        cur.execute("""SELECT pd.id, pd.product_id, pr.name, pd.batch, pd.expiration_date,
                              pd.quantity, pd.unit_cost, pd.tax, pd.discount, pd.subtotal,
                              pd.total, pd.lot_id
                       FROM purchase_details pd
                       JOIN products pr ON pd.product_id = pr.id
                       WHERE pd.purchase_id = %s
                       ORDER BY pd.id""", (purchase_id,))
        lines = cur.fetchall()
        return header, lines
    finally:
        conn.close()
