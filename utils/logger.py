<<<<<<< HEAD
"""
logger.py — Sistema de auditoría con trazabilidad completa.
Registra usuario, operación, datos y timestamp en:
  - Archivo: logs/farmafactura.log
  - BD: tabla audit_log (para consulta desde la app)
"""
import os
import logging
from datetime import datetime
from database.connection import create_connection
from auth import session

LOG_DIR  = "logs"
LOG_FILE = os.path.join(LOG_DIR, "farmafactura.log")

os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename  = LOG_FILE,
    level     = logging.INFO,
    format    = "%(asctime)s | %(levelname)s | %(message)s",
    datefmt   = "%Y-%m-%d %H:%M:%S",
    encoding  = "utf-8",
)

_logger = logging.getLogger("farmafactura")


def _get_user() -> str:
    """Retorna el nombre del usuario activo."""
    u = session.current_user
    if isinstance(u, tuple) and len(u) > 1:
        return u[1]
    return str(u) if u else "sistema"


def _ensure_audit_table():
    """Crea la tabla de auditoría si no existe (MariaDB)."""
    try:
        conn = create_connection(); cur = conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS audit_log (
            id        INT AUTO_INCREMENT PRIMARY KEY,
            timestamp DATETIME,
            username  VARCHAR(100) NOT NULL,
            operation VARCHAR(100) NOT NULL,
            module    VARCHAR(100),
            details   TEXT,
            status    VARCHAR(20) DEFAULT 'OK'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")
        conn.commit()
        conn.close()
    except Exception:
        pass


_ensure_audit_table()


def write_log(message: str, module: str = "general", level: str = "info"):
    """Log informativo estándar (retrocompatible)."""
    user = _get_user()
    full = f"[{user}] {message}"
    if level == "error":
        _logger.error(full)
    elif level == "warning":
        _logger.warning(full)
    else:
        _logger.info(full)


def audit(operation: str, details: str = "", module: str = "general", status: str = "OK"):
    """
    Registra una operación crítica en el log de auditoría.
    Guarda en archivo + BD para trazabilidad completa.

    Uso:
        audit("VENTA", f"Factura #{inv_id} | Cliente: {customer} | Total: ${total}")
        audit("PRECIO_CAMBIADO", f"Producto #{pid}: ${old} → ${new}", module="inventario")
        audit("LOGIN", f"Usuario: {username}", module="auth")
    """
    user = _get_user()
    ts   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Archivo de log
    _logger.info(f"[AUDIT] [{module.upper()}] [{operation}] [{user}] {details} | {status}")

    # Base de datos
    try:
        conn = create_connection(); cur = conn.cursor()
        cur.execute("""INSERT INTO audit_log
            (timestamp, username, operation, module, details, status)
            VALUES (?,?,?,?,?,?)""",
            (ts, user, operation, module, details, status))
        conn.commit()
        conn.close()
    except Exception as e:
        _logger.error(f"[AUDIT_SAVE_FAIL] {e}")


def log_sale(invoice_id: int, customer: str, total: float, payment: str, items: list):
    """Log específico para ventas."""
    details = (f"Factura #{invoice_id:06d} | Cliente: {customer} | "
               f"Total: ${total:,.2f} | Pago: {payment} | "
               f"Items: {len(items)}")
    audit("VENTA", details, module="facturacion")


def log_stock_change(product_id: int, name: str, old_stock: int, new_stock: int, reason: str = ""):
    """Log de cambio de stock."""
    details = (f"Producto #{product_id} '{name}' | "
               f"Stock: {old_stock} → {new_stock} | {reason}")
    audit("STOCK_CAMBIADO", details, module="inventario")


def log_price_change(product_id: int, name: str, old_price: float, new_price: float):
    """Log de cambio de precio."""
    details = f"Producto #{product_id} '{name}' | Precio: ${old_price:,.2f} → ${new_price:,.2f}"
    audit("PRECIO_CAMBIADO", details, module="inventario")


def log_login(username: str, success: bool):
    """Log de inicio de sesión."""
    status = "OK" if success else "FALLIDO"
    audit("LOGIN", f"Usuario: {username}", module="auth", status=status)


def log_user_action(action: str, target_user: str):
    """Log de gestión de usuarios."""
    audit(f"USUARIO_{action}", f"Afectado: {target_user}", module="usuarios")
=======
from datetime import datetime


# =========================================
# GUARDAR LOG
# =========================================

def write_log(message):

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    log_message = (
        f"[{timestamp}] {message}\n"
    )

    with open(
        "logs/system.log",
        "a",
        encoding="utf-8"
    ) as file:

        file.write(log_message)
>>>>>>> 79dd05f19e8d73e0fdefe1b9fbbfeb207c3cdd43
