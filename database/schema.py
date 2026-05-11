from auth.security import hash_password


def create_tables(conn):

    cursor = conn.cursor()

    # -----------------------------
    # TABLA USUARIOS
    # -----------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT 'employee'
    )
    """)

    # -----------------------------
    # TABLA CLIENTES
    # -----------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (

        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        phone TEXT,
        address TEXT

    )
    """)

    # -----------------------------
    # TABLA PRODUCTOS
    # -----------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            stock INTEGER,
            price REAL,
            cost REAL
        )
    """)

    # -----------------------------
    # TABLA FACTURAS
    # -----------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoices (

        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        total REAL NOT NULL,
        purchase_date TEXT NOT NULL

    )
    """)

    # -----------------------------
    # TABLA DETALLE FACTURAS
    # -----------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoice_items (

        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER,
        product_name TEXT,
        quantity INTEGER,
        price REAL,
        total REAL

    )
    """)

    # -----------------------------
    # CREAR ADMIN POR DEFECTO
    # -----------------------------

    cursor.execute(
        "SELECT * FROM users WHERE username=?",
        ("admin",)
    )

    admin = cursor.fetchone()

    if not admin:

        encrypted_password = hash_password("admin123")

        cursor.execute(
            """
            INSERT INTO users
            (username, password, role)
            VALUES (?, ?, ?)
            """,
            ("admin", encrypted_password, "Administrador")
        )

    conn.commit()