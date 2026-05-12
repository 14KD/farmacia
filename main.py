import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from datetime import date
from database.connection import create_connection
from database.schema import create_tables
from auth.login_window import LoginWindow
import config


# -------------------------------
# CONFIGURACIÓN VISUAL
# -------------------------------

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# Suprimir advertencias de callbacks pendientes de customtkinter
_original_report = tk.Tk.report_callback_exception

def _suppress_after_errors(self, exc, val, tb):
    if "invalid command name" in str(val):
        return
    _original_report(self, exc, val, tb)

tk.Tk.report_callback_exception = _suppress_after_errors


# -------------------------------
# INICIALIZAR BASE DE DATOS
# -------------------------------

def initialize_system():
    conn = create_connection()
    if conn:
        create_tables(conn)
        conn.close()
        print("Base de datos inicializada correctamente.")
    else:
        print("Error al conectar con la base de datos.")


# -------------------------------
# FUNCIÓN PRINCIPAL
# -------------------------------

def main():

    initialize_system()

    root = ctk.CTk()
    root.title("FarmaFactura Pro — Login")
    root.geometry("460x580")
    root.resizable(False, False)

    # Centrar ventana de login en pantalla
    root.update_idletasks()
    w = root.winfo_width()
    h = root.winfo_height()
    x = (root.winfo_screenwidth()  // 2) - (w // 2)
    y = (root.winfo_screenheight() // 2) - (h // 2)
    root.geometry(f"{w}x{h}+{x}+{y}")

    _show_startup_alerts(root)
    LoginWindow(root)
    root.mainloop()


def _show_startup_alerts(root):
    """Muestra alertas de stock crítico y vencimiento al iniciar si están activas."""
    cfg   = config.load()
    notif = cfg["notifications"]

    if not notif.get("alert_low_stock") and not notif.get("alert_expiry"):
        return

    msgs = []

    try:
        conn = create_connection()
        cur  = conn.cursor()

        if notif.get("alert_low_stock"):
            threshold = cfg["inventory"]["low_stock_threshold"]
            cur.execute("SELECT COUNT(*) FROM products WHERE stock > 0 AND stock <= ?", (threshold,))
            low = cur.fetchone()[0]
            if low > 0:
                msgs.append(f"⚠  {low} producto(s) con stock crítico (≤ {threshold} unidades)")

        if notif.get("alert_expiry"):
            days  = cfg["inventory"]["expiry_alert_days"]
            today = date.today().isoformat()
            cur.execute("""SELECT COUNT(*) FROM products
                            WHERE expiry_date IS NOT NULL
                            AND expiry_date != ''
                            AND expiry_date <= date(?, '+' || ? || ' days')
                            AND expiry_date >= ?""",
                        (today, days, today))
            expiring = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM products WHERE expiry_date < ? AND expiry_date != ''", (today,))
            expired = cur.fetchone()[0]
            if expiring > 0:
                msgs.append(f"📅  {expiring} producto(s) vencen en los próximos {days} días")
            if expired > 0:
                msgs.append(f"⛔  {expired} producto(s) ya vencidos")

    except Exception:
        return

    if msgs:
        tk.messagebox.showwarning(
            "Alertas del Sistema",
            "\n\n".join(msgs) + "\n\nRevisa el módulo de Inventario."
        )


# -------------------------------
# EJECUCIÓN
# -------------------------------

if __name__ == "__main__":
    main()