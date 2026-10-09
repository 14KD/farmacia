<<<<<<< HEAD
"""
database/schema.py — Inicialización de tablas MariaDB + Triggers FEFO.
Versión actualizada con:
  - Tabla inventory_adjustments (ajustes manuales)
  - Vista v_stock_real (stock calculado desde lotes)
  - Triggers que sincronizan products.stock automáticamente
"""
=======
>>>>>>> 79dd05f19e8d73e0fdefe1b9fbbfeb207c3cdd43
from auth.security import hash_password


def create_tables(conn):
<<<<<<< HEAD
    """
    Crea todas las tablas, vista y triggers si no existen.
    conn debe ser una conexión _CompatConnection (database/connection.py).
    """
    cursor = conn.cursor()

    # ── 1. Usuarios ──────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id       INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role     VARCHAR(50) DEFAULT 'employee'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    # ── 2. Clientes ──────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id      VARCHAR(50) PRIMARY KEY,
            name    VARCHAR(200) NOT NULL,
            phone   VARCHAR(30),
            address TEXT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    # ── 3. Proveedores ───────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            id      INT AUTO_INCREMENT PRIMARY KEY,
            name    VARCHAR(200) NOT NULL,
            phone   VARCHAR(30),
            email   VARCHAR(150),
            address TEXT,
            notes   TEXT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    # ── 4. Productos ─────────────────────────────────────────────────────────
    # manages_lots se decide desde el módulo de Lotes al recibir mercancía
    # (checkbox "¿Este producto maneja lotes?"), no desde Productos.
    # Si manages_lots=1 (default), stock lo mantienen los triggers de lotes
    # y no se edita a mano en ningún lado. Si manages_lots=0, stock es un
    # valor directo que Lotes suma al recibir mercancía sin lote.
    # track_inventory se mantiene por compatibilidad pero no tiene UI hoy.
    # expiry_date siempre es un campo propio del producto, editable a mano
    # desde Productos.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id                INT AUTO_INCREMENT PRIMARY KEY,
            name              VARCHAR(200),
            active_ingredient VARCHAR(200),
            presentation      VARCHAR(100),
            laboratory        VARCHAR(200),
            category          VARCHAR(100) DEFAULT 'General',
            stock             INT          DEFAULT 0,
            min_stock         INT          DEFAULT 10,
            price             DECIMAL(10,2) DEFAULT 0,
            cost              DECIMAL(10,2) DEFAULT 0,
            expiry_date       DATE,
            supplier_id       INT,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    # Migración de manages_lots/track_inventory/applies_itbis para bases ya
    # existentes. MariaDB viejo no soporta ADD COLUMN IF NOT EXISTS de forma
    # confiable, así que se envuelve en try/except igual que los índices
    # de abajo. applies_itbis: si el producto aplica ITBIS al venderse
    # (algunos medicamentos están exentos); se usa como valor por defecto
    # al seleccionar el producto en Ventas, pero se puede cambiar ahí mismo.
    for alter_sql in (
        "ALTER TABLE products ADD COLUMN manages_lots TINYINT(1) NOT NULL DEFAULT 1",
        "ALTER TABLE products ADD COLUMN track_inventory TINYINT(1) NOT NULL DEFAULT 1",
        "ALTER TABLE products ADD COLUMN applies_itbis TINYINT(1) NOT NULL DEFAULT 1",
        # 'active': permite "eliminar" un producto que ya tiene compras
        # registradas (no se puede borrar físicamente sin perder ese
        # historial) ocultándolo de las listas/búsquedas en vez de borrarlo.
        "ALTER TABLE products ADD COLUMN active TINYINT(1) NOT NULL DEFAULT 1",
    ):
        try:
            cursor.execute(alter_sql)
        except Exception:
            pass  # La columna ya existe

    # 'seq' en customers: número de cliente visible y consecutivo. El 'id'
    # real de customers es un código aleatorio (no sirve para saber cuál se
    # agregó último); 'seq' sí es autoincremental, así que un número más
    # alto siempre es un cliente agregado más recientemente.
    try:
        cursor.execute(
            "ALTER TABLE customers ADD COLUMN seq INT AUTO_INCREMENT UNIQUE"
        )
    except Exception:
        pass  # La columna ya existe

    # ── 5. Presentaciones de venta por producto ─────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_units (
            id            INT AUTO_INCREMENT PRIMARY KEY,
            product_id    INT NOT NULL,
            unit_name     VARCHAR(50)   NOT NULL,
            factor        INT           NOT NULL DEFAULT 1,
            price         DECIMAL(10,2) DEFAULT NULL,
            is_base       TINYINT(1)    DEFAULT 0,
            is_default    TINYINT(1)    DEFAULT 0,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
            INDEX idx_pu_product (product_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    # ── 6. Facturas ──────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id             INT AUTO_INCREMENT PRIMARY KEY,
            customer_name  VARCHAR(200) NOT NULL,
            total          DECIMAL(10,2) NOT NULL,
            purchase_date  DATETIME NOT NULL,
            employee       VARCHAR(100),
            payment_method VARCHAR(50)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    # ── 7. Ítems de factura ──────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoice_items (
            id           INT AUTO_INCREMENT PRIMARY KEY,
            invoice_id   INT,
            product_id   INT,
            product_name VARCHAR(200),
            quantity     INT,
            price        DECIMAL(10,2),
            total        DECIMAL(10,2),
            FOREIGN KEY (invoice_id) REFERENCES invoices(id)  ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id)  ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    # ── 8. Lotes ─────────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lots (
            id                 INT AUTO_INCREMENT PRIMARY KEY,
            product_id         INT NOT NULL,
            lot_number         VARCHAR(100) NOT NULL,
            quantity_received  INT          DEFAULT 0,
            quantity_available INT          DEFAULT 0,
            cost               DECIMAL(10,2) DEFAULT 0,
            expiry_date        DATE,
            received_date      DATE,
            supplier_id        INT,
            notes              TEXT,
            status             VARCHAR(20)  DEFAULT 'activo',
            FOREIGN KEY (product_id)  REFERENCES products(id)  ON DELETE CASCADE,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    # ── 9. Movimientos de lote ───────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lot_movements (
            id         INT AUTO_INCREMENT PRIMARY KEY,
            lot_id     INT NOT NULL,
            type       VARCHAR(50) NOT NULL,
            quantity   INT NOT NULL,
            reason     TEXT,
            invoice_id INT,
            username   VARCHAR(100),
            timestamp  DATETIME NOT NULL,
            FOREIGN KEY (lot_id)     REFERENCES lots(id)     ON DELETE CASCADE,
            FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    # ── 10. Ajustes de inventario (NUEVO) ─────────────────────────────────────
    # Separado de lot_movements para distinguir ventas (automáticas) de
    # ajustes manuales (conteo físico, merma, devolución, etc.)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory_adjustments (
            id         INT AUTO_INCREMENT PRIMARY KEY,
            lot_id     INT NOT NULL,
            product_id INT NOT NULL,
            type       ENUM('entrada','salida','ajuste') NOT NULL,
            quantity   INT NOT NULL,
            reason     VARCHAR(200),
            username   VARCHAR(100),
            timestamp  DATETIME DEFAULT NOW(),
            FOREIGN KEY (lot_id)     REFERENCES lots(id)     ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    # ── 11b. Compras (Encabezado) ─────────────────────────────────────────────
    # subtotal/tax/discount/total son montos (no porcentajes), consistentes
    # entre encabezado y detalle: subtotal - discount + tax = total.
    # due_date: fecha límite de pago — obligatoria en la UI solo cuando
    # payment_method='Crédito' (ver ui/purchases_ui.py); NULL en el resto.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id             INT AUTO_INCREMENT PRIMARY KEY,
            supplier_id    INT NOT NULL,
            invoice_number VARCHAR(100),
            purchase_date  DATETIME NOT NULL,
            payment_method VARCHAR(50),
            due_date       DATE,
            subtotal       DECIMAL(10,2) DEFAULT 0,
            tax            DECIMAL(10,2) DEFAULT 0,
            discount       DECIMAL(10,2) DEFAULT 0,
            total          DECIMAL(10,2) DEFAULT 0,
            status         VARCHAR(20) DEFAULT 'registrada',
            user_id        INT,
            notes          TEXT,
            created_at     DATETIME DEFAULT NOW(),
            updated_at     DATETIME DEFAULT NOW() ON UPDATE NOW(),
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE RESTRICT,
            FOREIGN KEY (user_id)     REFERENCES users(id)     ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    # Migración para instalaciones donde purchases ya existía sin due_date.
    try:
        cursor.execute("ALTER TABLE purchases ADD COLUMN due_date DATE NULL")
    except Exception:
        pass  # La columna ya existe

    # ── 11c. Detalle de Compras ────────────────────────────────────────────────
    # Cada fila también genera un lote en `lots` (product_id, batch→lot_number,
    # expiration_date→expiry_date) para reutilizar el mecanismo de stock/FEFO
    # ya existente — ver database/purchases.py. lot_id enlaza la línea con el
    # lote que generó, necesario para poder editar una compra ya guardada sin
    # perder o duplicar el lote (ajustar cantidad/costo del mismo lote en vez
    # de crear uno nuevo).
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchase_details (
            id              INT AUTO_INCREMENT PRIMARY KEY,
            purchase_id     INT NOT NULL,
            product_id      INT NOT NULL,
            lot_id          INT,
            batch           VARCHAR(100),
            expiration_date DATE,
            quantity        INT NOT NULL,
            unit_cost       DECIMAL(10,2) NOT NULL,
            discount        DECIMAL(10,2) DEFAULT 0,
            tax             DECIMAL(10,2) DEFAULT 0,
            subtotal        DECIMAL(10,2) DEFAULT 0,
            total           DECIMAL(10,2) DEFAULT 0,
            created_at      DATETIME DEFAULT NOW(),
            updated_at      DATETIME DEFAULT NOW() ON UPDATE NOW(),
            FOREIGN KEY (purchase_id) REFERENCES purchases(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id)  REFERENCES products(id)  ON DELETE RESTRICT,
            FOREIGN KEY (lot_id)      REFERENCES lots(id)      ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    # Migración para instalaciones donde purchase_details ya existía sin
    # lot_id (misma técnica que products.manages_lots más arriba).
    try:
        cursor.execute("ALTER TABLE purchase_details ADD COLUMN lot_id INT NULL")
    except Exception:
        pass  # La columna ya existe
    try:
        cursor.execute("""ALTER TABLE purchase_details
                           ADD CONSTRAINT fk_purchase_details_lot
                           FOREIGN KEY (lot_id) REFERENCES lots(id) ON DELETE SET NULL""")
    except Exception:
        pass  # La constraint ya existe

    # ── 11. Auditoría ────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id        INT AUTO_INCREMENT PRIMARY KEY,
            timestamp DATETIME,
            username  VARCHAR(100),
            operation VARCHAR(100),
            module    VARCHAR(100),
            details   TEXT,
            status    VARCHAR(20) DEFAULT 'OK'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    # ── Índices ──────────────────────────────────────────────────────────────
    indices = [
        "CREATE INDEX idx_products_name       ON products(name)",
        "CREATE INDEX idx_products_category   ON products(category)",
        "CREATE INDEX idx_products_stock      ON products(stock)",
        "CREATE INDEX idx_customers_name      ON customers(name)",
        "CREATE INDEX idx_invoices_date       ON invoices(purchase_date)",
        "CREATE INDEX idx_invoices_customer   ON invoices(customer_name)",
        "CREATE INDEX idx_items_invoice       ON invoice_items(invoice_id)",
        "CREATE INDEX idx_items_product       ON invoice_items(product_name)",
        "CREATE INDEX idx_suppliers_name      ON suppliers(name)",
        "CREATE INDEX idx_lots_product        ON lots(product_id)",
        "CREATE INDEX idx_lots_expiry         ON lots(expiry_date)",
        "CREATE INDEX idx_lots_status         ON lots(status)",
        "CREATE INDEX idx_lots_fefo           ON lots(product_id, expiry_date, status)",
        "CREATE INDEX idx_movements_lot       ON lot_movements(lot_id)",
        "CREATE INDEX idx_adjustments_product ON inventory_adjustments(product_id)",
        "CREATE INDEX idx_adjustments_lot     ON inventory_adjustments(lot_id)",
        "CREATE INDEX idx_punits_product      ON product_units(product_id)",
        "CREATE INDEX idx_purchases_supplier  ON purchases(supplier_id)",
        "CREATE INDEX idx_purchases_date      ON purchases(purchase_date)",
        "CREATE INDEX idx_purchase_details_purchase ON purchase_details(purchase_id)",
        "CREATE INDEX idx_purchase_details_product  ON purchase_details(product_id)",
        "CREATE INDEX idx_purchase_details_lot       ON purchase_details(lot_id)",
    ]
    for sql in indices:
        try:
            cursor.execute(sql)
        except Exception:
            pass  # El índice ya existe

    # ── Vista: stock real calculado desde lotes ──────────────────────────────
    # Cualquier módulo puede hacer SELECT * FROM v_stock_real
    # para obtener stock y vencimiento próximo sin cálculos manuales.
    try:
        cursor.execute("DROP VIEW IF EXISTS v_stock_real")
        cursor.execute("""
            CREATE VIEW v_stock_real AS
            SELECT
                p.id                          AS product_id,
                p.name,
                p.category,
                p.price,
                p.min_stock,
                COALESCE(SUM(l.quantity_available), 0) AS stock_total,
                MIN(l.expiry_date)            AS proxima_vencimiento,
                COUNT(l.id)                   AS lotes_activos
            FROM products p
            LEFT JOIN lots l
                ON l.product_id = p.id
               AND l.status = 'activo'
               AND l.quantity_available > 0
            GROUP BY p.id, p.name, p.category, p.price, p.min_stock
        """)
    except Exception as e:
        print(f"[Schema] Aviso creando vista v_stock_real: {e}")

    # ── Triggers FEFO ────────────────────────────────────────────────────────
    # Sincronizan products.stock automáticamente cuando cambia un lote.
    # expiry_date NO se toca aquí: es un campo editable a mano desde el
    # módulo de Productos, independiente de los lotes.
    # MariaDB no soporta CREATE OR REPLACE TRIGGER, hay que DROP + CREATE.
    triggers = [
        # Trigger 1: al INSERTAR un nuevo lote
        ("trg_lots_after_insert", """
            CREATE TRIGGER trg_lots_after_insert
            AFTER INSERT ON lots
            FOR EACH ROW
            BEGIN
                UPDATE products
                SET
                    stock = (
                        SELECT COALESCE(SUM(quantity_available), 0)
                        FROM lots
                        WHERE product_id = NEW.product_id
                          AND status = 'activo'
                    )
                WHERE id = NEW.product_id;
            END
        """),
        # Trigger 2: al ACTUALIZAR un lote (ventas, ajustes)
        ("trg_lots_after_update", """
            CREATE TRIGGER trg_lots_after_update
            AFTER UPDATE ON lots
            FOR EACH ROW
            BEGIN
                UPDATE products
                SET
                    stock = (
                        SELECT COALESCE(SUM(quantity_available), 0)
                        FROM lots
                        WHERE product_id = NEW.product_id
                          AND status = 'activo'
                    )
                WHERE id = NEW.product_id;
            END
        """),
        # Trigger 3: al ELIMINAR un lote
        ("trg_lots_after_delete", """
            CREATE TRIGGER trg_lots_after_delete
            AFTER DELETE ON lots
            FOR EACH ROW
            BEGIN
                UPDATE products
                SET
                    stock = (
                        SELECT COALESCE(SUM(quantity_available), 0)
                        FROM lots
                        WHERE product_id = OLD.product_id
                          AND status = 'activo'
                    )
                WHERE id = OLD.product_id;
            END
        """),
    ]

    for trigger_name, trigger_sql in triggers:
        try:
            cursor.execute(f"DROP TRIGGER IF EXISTS {trigger_name}")
            cursor.execute(trigger_sql)
        except Exception as e:
            print(f"[Schema] Aviso creando trigger {trigger_name}: {e}")

    # ── Usuario admin fijo ─────────────────────────────────────────────────
    # La contraseña del admin NO se puede cambiar desde ninguna pantalla de
    # la app (por seguridad) — si algún día hace falta cambiarla, se edita
    # el valor de ADMIN_PASSWORD aquí abajo y se abre el programa una vez;
    # este bloque se encarga de aplicarlo en la base de datos automáticamente.
    ADMIN_PASSWORD = "admin123"
    cursor.execute("SELECT id FROM users WHERE username=%s", ("admin",))
    if cursor.fetchone():
        cursor.execute(
            "UPDATE users SET password=%s, role=%s WHERE username=%s",
            (hash_password(ADMIN_PASSWORD), "Administrador", "admin")
        )
    else:
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
            ("admin", hash_password(ADMIN_PASSWORD), "Administrador")
        )

    # ── Unidad base para productos existentes sin presentaciones ─────────────
    try:
        cursor.execute("""
            INSERT IGNORE INTO product_units (product_id, unit_name, factor, is_base, is_default)
            SELECT p.id, 'Unidad', 1, 1, 1
            FROM products p
            WHERE p.id NOT IN (
                SELECT DISTINCT product_id FROM product_units WHERE is_base = 1
            )
        """)
    except Exception:
        pass

    conn.commit()
    cursor.close()
=======

    cursor = conn.cursor()

    # USUARIOS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role     TEXT DEFAULT 'employee'
    )""")

    # CLIENTES
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id      TEXT PRIMARY KEY,
        name    TEXT NOT NULL,
        phone   TEXT,
        address TEXT
    )""")

    # PROVEEDORES
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS suppliers (
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        name    TEXT NOT NULL,
        phone   TEXT,
        email   TEXT,
        address TEXT,
        notes   TEXT
    )""")

    # PRODUCTOS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT,
        category    TEXT DEFAULT 'General',
        stock       INTEGER,
        price       REAL,
        cost        REAL,
        expiry_date TEXT,
        supplier_id INTEGER,
        FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
    )""")

    # FACTURAS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        total         REAL NOT NULL,
        purchase_date TEXT NOT NULL,
        employee      TEXT
    )""")

    # DETALLE FACTURAS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoice_items (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id   INTEGER,
        product_id   INTEGER,
        product_name TEXT,
        quantity     INTEGER,
        price        REAL,
        total        REAL,
        FOREIGN KEY (invoice_id) REFERENCES invoices(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )""")

    # ── Migraciones ─────────────────────────────
    migrations = [
        "ALTER TABLE products ADD COLUMN cost REAL DEFAULT 0",
        "ALTER TABLE products ADD COLUMN category TEXT DEFAULT 'General'",
        "ALTER TABLE products ADD COLUMN expiry_date TEXT",
        "ALTER TABLE products ADD COLUMN supplier_id INTEGER",
        "ALTER TABLE invoices ADD COLUMN employee TEXT",
        "ALTER TABLE invoice_items ADD COLUMN product_id INTEGER",
    ]
    for sql in migrations:
        try:
            cursor.execute(sql)
        except Exception:
            pass

    # ── Índices para búsquedas rápidas ──────────
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_products_name     ON products(name)",
        "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category)",
        "CREATE INDEX IF NOT EXISTS idx_products_stock    ON products(stock)",
        "CREATE INDEX IF NOT EXISTS idx_customers_name    ON customers(name)",
        "CREATE INDEX IF NOT EXISTS idx_invoices_date     ON invoices(purchase_date)",
        "CREATE INDEX IF NOT EXISTS idx_invoices_customer ON invoices(customer_name)",
        "CREATE INDEX IF NOT EXISTS idx_items_invoice     ON invoice_items(invoice_id)",
        "CREATE INDEX IF NOT EXISTS idx_items_product     ON invoice_items(product_name)",
        "CREATE INDEX IF NOT EXISTS idx_suppliers_name    ON suppliers(name)",
    ]
    for sql in indexes:
        try:
            cursor.execute(sql)
        except Exception:
            pass

    # Admin por defecto
    cursor.execute("SELECT * FROM users WHERE username=?", ("admin",))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?,?,?)",
            ("admin", hash_password("admin123"), "Administrador")
        )

    conn.commit()
>>>>>>> 79dd05f19e8d73e0fdefe1b9fbbfeb207c3cdd43
