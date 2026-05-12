import sqlite3

DATABASE_NAME = "pharmacy_pos.db"

_connection = None


def create_connection():
    """
    Retorna una conexión persistente a SQLite.
    Reutiliza la misma conexión durante toda la sesión
    para evitar el overhead de abrir/cerrar en cada operación.
    """
    global _connection

    try:
        # Verificar si la conexión sigue activa
        if _connection is not None:
            _connection.execute("SELECT 1")
            return _connection
    except Exception:
        _connection = None

    try:
        _connection = sqlite3.connect(
            DATABASE_NAME,
            check_same_thread=False   # permite uso desde distintos frames
        )
        # Optimizaciones de SQLite
        _connection.execute("PRAGMA journal_mode=WAL")   # escrituras más rápidas
        _connection.execute("PRAGMA synchronous=NORMAL") # menos fsync, más rápido
        _connection.execute("PRAGMA cache_size=10000")   # caché de 10k páginas
        _connection.execute("PRAGMA temp_store=MEMORY")  # temporales en RAM
        return _connection
    except sqlite3.Error as e:
        print(f"Error al conectar con la base de datos: {e}")
        return None


def close_connection():
    """Cierra la conexión al salir del sistema."""
    global _connection
    if _connection:
        _connection.close()
        _connection = None