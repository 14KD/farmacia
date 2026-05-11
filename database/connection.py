import sqlite3

DATABASE_NAME = "pharmacy_pos.db"


def create_connection():
    """
    Crea y retorna una conexión a SQLite.
    """

    try:
        conn = sqlite3.connect(DATABASE_NAME)
        return conn

    except sqlite3.Error as error:
        print(f"Error al conectar con la base de datos: {error}")
        return None