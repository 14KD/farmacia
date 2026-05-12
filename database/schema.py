from auth.security import hash_password


def create_tables(conn):

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