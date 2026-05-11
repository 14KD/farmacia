import shutil

from datetime import datetime


# =========================================
# CREAR BACKUP
# =========================================

def create_backup():

    source = "pharmacy.db"

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    destination = (
        f"backups/backup_{timestamp}.db"
    )

    shutil.copy(
        source,
        destination
    )

    return destination
# =========================================
# RESTAURAR BACKUP
# =========================================

def restore_backup(backup_file):

    destination = "pharmacy.db"

    shutil.copy(
        backup_file,
        destination
    )