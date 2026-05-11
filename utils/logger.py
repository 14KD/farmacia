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