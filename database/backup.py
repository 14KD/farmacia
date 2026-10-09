"""
database/backup.py — Backup MariaDB via mysqldump.
Para MariaDB en XAMPP, el backup se hace exportando desde phpMyAdmin
o usando mysqldump. Esta versión muestra instrucciones al usuario.
"""
import subprocess
import os
import json
from datetime import datetime

# Ruta absoluta anclada a la raíz del proyecto (un nivel arriba de database/).
CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db_config.json"
)

def _load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {"host": "127.0.0.1", "port": 3306,
            "database": "farmafactura", "user": "farmausr", "password": "FarmaPass2024"}

def create_backup():
    """
    Intenta hacer backup con mysqldump (incluido en XAMPP).
    Retorna (ruta_absoluta: str, es_backup_real: bool).
    Si mysqldump no está disponible, es_backup_real=False y la ruta
    apunta a un archivo de instrucciones (NO es un respaldo real de datos).
    """
    cfg = _load_config()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("backups", exist_ok=True)
    dest = os.path.abspath(f"backups/backup_{ts}.sql")

    # Ruta de mysqldump en XAMPP Windows
    mysqldump_paths = [
        r"C:\xampp\mysql\bin\mysqldump.exe",
        "mysqldump",
    ]

    for mysqldump in mysqldump_paths:
        try:
            cmd = [
                mysqldump,
                f"--host={cfg['host']}",
                f"--port={cfg['port']}",
                f"--user={cfg['user']}",
                f"--password={cfg['password']}",
                cfg['database']
            ]
            with open(dest, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, timeout=60)
            if result.returncode == 0:
                return dest, True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    # Si mysqldump falla, informar al usuario (esto NO es un backup real)
    msg = os.path.abspath(f"backups/INSTRUCCIONES_{ts}.txt")
    with open(msg, 'w') as f:
        f.write("No se pudo generar el respaldo automáticamente (mysqldump no encontrado).\n\n")
        f.write("Para hacer backup de la base de datos MariaDB manualmente:\n\n")
        f.write("1. Abre http://localhost/phpmyadmin\n")
        f.write("2. Selecciona la base de datos 'farmafactura'\n")
        f.write("3. Haz clic en 'Exportar' → 'Go'\n")
        f.write("4. Guarda el archivo .sql generado\n")
    return msg, False

def restore_backup(backup_file):
    """Restaurar backup MariaDB desde archivo .sql"""
    from tkinter import messagebox
    messagebox.showinfo(
        "Restaurar Backup",
        "Para restaurar un backup MariaDB:\n\n"
        "1. Abre http://localhost/phpmyadmin\n"
        "2. Selecciona la base de datos 'farmafactura'\n"
        "3. Haz clic en 'Importar'\n"
        "4. Selecciona tu archivo .sql\n"
        "5. Haz clic en 'Go'"
    )
