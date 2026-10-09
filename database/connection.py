"""
database/connection.py — Conexión a MariaDB (XAMPP)
Pool aumentado a 20 conexiones para soportar múltiples módulos simultáneos.
"""

import re
import mysql.connector
from mysql.connector import pooling
import json
import os

_pool = None
# Ruta absoluta anclada a la raíz del proyecto (un nivel arriba de database/),
# para que no dependa del directorio de trabajo con el que se abra el programa.
CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db_config.json"
)

DEFAULT_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "database": "farmafactura",
    "user": "farmausr",
    "password": "FarmaPass2024"
}

_PLACEHOLDER_RE = re.compile(r"\?")


def _convert_query(sql: str) -> str:
    return _PLACEHOLDER_RE.sub("%s", sql)


class _CompatCursor:
    def __init__(self, mysql_cursor):
        self._cur = mysql_cursor

    def execute(self, sql: str, params=None):
        sql = _convert_query(sql)
        if params is not None:
            self._cur.execute(sql, params)
        else:
            self._cur.execute(sql)

    def executemany(self, sql: str, seq_of_params):
        self._cur.executemany(_convert_query(sql), seq_of_params)

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()

    def fetchmany(self, size=None):
        return self._cur.fetchmany(size)

    @property
    def lastrowid(self):
        return self._cur.lastrowid

    @property
    def rowcount(self):
        return self._cur.rowcount

    @property
    def description(self):
        return self._cur.description

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        try:
            self._cur.close()
        except Exception:
            pass


class _CompatConnection:
    def __init__(self, mysql_conn):
        self._conn = mysql_conn
        self._closed = False

    def cursor(self):
        return _CompatCursor(self._conn.cursor())

    def execute(self, sql: str, params=None):
        cur = self.cursor()
        cur.execute(sql, params)
        return cur

    def commit(self):
        if not self._closed:
            self._conn.commit()

    def rollback(self):
        if not self._closed:
            try:
                self._conn.rollback()
            except Exception:
                pass

    def close(self):
        if not self._closed:
            self._closed = True
            try:
                self._conn.close()
            except Exception:
                pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()


def _load_db_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            merged = DEFAULT_CONFIG.copy()
            merged.update(cfg)
            return merged
        except Exception as e:
            print(f"[DB] Error leyendo db_config.json: {e}")
    return DEFAULT_CONFIG.copy()


def _create_pool():
    global _pool
    if _pool is not None:
        return _pool

    cfg = _load_db_config()
    try:
        _pool = pooling.MySQLConnectionPool(
            pool_name="farmapool",
            pool_size=20,          # ← Aumentado de 5 a 20
            pool_reset_session=True,
            host=cfg["host"],
            port=cfg["port"],
            database=cfg["database"],
            user=cfg["user"],
            password=cfg["password"],
            charset="utf8mb4",
            autocommit=False,
            connection_timeout=10
        )
        print(f"[DB] Conectado a MariaDB → {cfg['host']}:{cfg['port']}/{cfg['database']} (pool=20)")
        return _pool
    except mysql.connector.Error as e:
        print(f"[DB] ERROR al conectar MariaDB: {e}")
        return None


def create_connection() -> _CompatConnection:
    pool = _create_pool()
    if pool is None:
        raise RuntimeError(
            "No se pudo conectar a MariaDB.\n"
            "Verifica que XAMPP esté corriendo y db_config.json sea correcto."
        )
    try:
        return _CompatConnection(pool.get_connection())
    except mysql.connector.Error as e:
        raise RuntimeError(f"Error obteniendo conexión del pool: {e}")


def close_connection():
    pass


def test_connection() -> tuple:
    try:
        conn = create_connection()
        cur = conn.cursor()
        cur.execute("SELECT VERSION(), DATABASE()")
        version, db = cur.fetchone()
        cur.close()
        conn.close()
        return True, f"Conectado a MariaDB {version} — BD: {db}"
    except Exception as e:
        return False, str(e)
