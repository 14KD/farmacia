import tkinter as tk
from tkinter import messagebox


# ─── Suprimir warnings de customtkinter ───────────────────────────────────
_orig_report = tk.Tk.report_callback_exception

def _suppress(self, exc, val, tb):
    if "invalid command name" in str(val):
        return
    try:
        import traceback, logging
        logging.getLogger("farmafactura").error(
            "".join(traceback.format_exception(exc, val, tb))
        )
    except Exception:
        pass
    _orig_report(self, exc, val, tb)

tk.Tk.report_callback_exception = _suppress

import threading
def _thread_exception_handler(args):
    try:
        import traceback, logging
        logging.getLogger("farmafactura").error(
            "".join(traceback.format_exception(
                args.exc_type, args.exc_value, args.exc_traceback))
        )
    except Exception:
        pass
threading.excepthook = _thread_exception_handler


# ─── Splash Screen ────────────────────────────────────────────────────────
def _run_splash():
    from splash import SplashScreen
    splash = SplashScreen()

    def load_customtkinter():
        import customtkinter as ctk
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

    def load_matplotlib():
        import matplotlib
        matplotlib.use("TkAgg")
        import matplotlib.pyplot as plt
        plt.style.use("dark_background")

    def load_pandas():
        import pandas  # noqa

    def load_reportlab():
        import reportlab  # noqa

    def init_database():
        try:
            from database.connection import create_connection
            from database.schema import create_tables
            conn = create_connection()
            if conn:
                create_tables(conn)
                conn.close()
        except Exception as e:
            import logging
            logging.getLogger("farmafactura").warning(f"DB init: {e}")

    def check_alerts():
        try:
            from datetime import date
            import config
            cfg   = config.load()
            notif = cfg.get("notifications", {})
            msgs  = []
            from database.connection import create_connection
            conn = create_connection()
            try:
                cur = conn.cursor()
                if notif.get("alert_low_stock"):
                    threshold = cfg["inventory"]["low_stock_threshold"]
                    cur.execute(
                        "SELECT COUNT(*) FROM products WHERE stock > 0 AND stock <= ?",
                        (threshold,)
                    )
                    low = cur.fetchone()[0]
                    if low > 0:
                        msgs.append(f"⚠  {low} producto(s) con stock crítico (≤ {threshold} unidades)")
                if notif.get("alert_expiry"):
                    days  = cfg["inventory"]["expiry_alert_days"]
                    today = date.today().isoformat()
                    cur.execute(
                        """SELECT COUNT(*) FROM products
                           WHERE expiry_date IS NOT NULL AND expiry_date != ''
                           AND expiry_date <= DATE_ADD(?, INTERVAL ? DAY)
                           AND expiry_date >= ?""",
                        (today, days, today)
                    )
                    expiring = cur.fetchone()[0]
                    cur.execute(
                        "SELECT COUNT(*) FROM products WHERE expiry_date < ? AND expiry_date != ''",
                        (today,)
                    )
                    expired = cur.fetchone()[0]
                    if expiring > 0:
                        msgs.append(f"📅  {expiring} producto(s) vencen en menos de {days} días")
                    if expired > 0:
                        msgs.append(f"⛔  {expired} producto(s) ya vencidos")
            finally:
                conn.close()
            if msgs:
                messagebox.showwarning(
                    "Alertas del Sistema",
                    "\n\n".join(msgs) + "\n\nRevisa el módulo de Inventario."
                )
        except Exception:
            pass

    def load_ui_modules():
        modules = [
            "ui.products_ui", "ui.customers_ui", "ui.suppliers_ui",
            "ui.invoices_ui", "ui.reports_ui", "ui.users_ui",
            "ui.settings_ui", "ui.cash_register_ui", "ui.sales_history_ui",
            "ui.lots_ui", "ui.date_picker", "ui.predictive_search",
        ]
        for mod in modules:
            try:
                __import__(mod)
            except Exception:
                pass

    tasks = [
        ("Cargando interfaz...",            load_customtkinter),
        ("Cargando gráficos...",            load_matplotlib),
        ("Cargando pandas...",              load_pandas),
        ("Cargando reportes PDF...",        load_reportlab),
        ("Inicializando base de datos...",  init_database),
        ("Cargando módulos del sistema...", load_ui_modules),
        ("Verificando alertas...",          check_alerts),
    ]

    splash.run_with_loading(tasks)


# ─── Estado global de navegación ──────────────────────────────────────────
_go_to_login     = True   # True  → mostrar login
_exit_program    = False  # True  → salir del programa


# ─── Main ─────────────────────────────────────────────────────────────────
def main():
    global _go_to_login, _exit_program

    import customtkinter as ctk
    from auth.login_window import LoginWindow
    from ui.dashboard import Dashboard
    from auth import session

    _run_splash()

    root = ctk.CTk()

    # ── helpers ──────────────────────────────────────────────────────────

    def _center(w, h):
        root.update_idletasks()
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _clear_widgets():
        """Destruye todos los widgets hijos de root."""
        for child in list(root.winfo_children()):
            try:
                child.destroy()
            except Exception:
                pass

    def _on_login_x():
        """X presionada en la pantalla de login → salir del programa."""
        global _exit_program
        _exit_program = True
        root.quit()

    def _on_dashboard_x():
        """X presionada en el dashboard → volver al login sin confirmación."""
        _logout_and_back()

    def _logout_and_back():
        """Cierra el dashboard limpiamente y vuelve al login."""
        # 1. Cancelar tareas after() del dashboard para evitar crashes
        try:
            dashboard_inst = getattr(root, '_dashboard_instance', None)
            if dashboard_inst:
                for aid in getattr(dashboard_inst, '_after_ids', []):
                    try:
                        root.after_cancel(aid)
                    except Exception:
                        pass
                dashboard_inst._after_ids = []
        except Exception:
            pass

        # 2. Limpiar sesión
        session.current_user = None
        session.current_role = None

        # 3. Salir del mainloop del dashboard → el while vuelve al login
        root.quit()

    # ── Pantalla de login ─────────────────────────────────────────────────

    def show_login():
        _clear_widgets()
        root.title("FarmaFactura Pro — Iniciar Sesión")
        root.resizable(False, False)
        try:
            root.state("normal")
        except Exception:
            pass
        root.minsize(1, 1)
        _center(460, 580)

        lw = LoginWindow(root)
        root.protocol("WM_DELETE_WINDOW", _on_login_x)
        return lw

    # ── Pantalla de dashboard ─────────────────────────────────────────────

    def show_dashboard():
        _clear_widgets()
        root.title("FarmaFactura Pro")
        root.resizable(True, True)
        root.minsize(1000, 640)

        dash = Dashboard(root)
        # Guardar referencia para poder cancelar sus after() al cerrar
        root._dashboard_instance = dash

        # Sobreescribir el WM_DELETE_WINDOW del dashboard (lo pone en __init__)
        root.protocol("WM_DELETE_WINDOW", _on_dashboard_x)

        # También sobreescribir el método logout del dashboard para
        # que use nuestra función de limpieza
        dash.logout = _logout_with_confirm

        root.after(50, lambda: root.state("zoomed"))

    def _logout_with_confirm():
        """Cierra sesión con confirmación (botón Cerrar Sesión)."""
        if not messagebox.askyesno(
            "Cerrar Sesión",
            "¿Seguro que deseas cerrar sesión?"
        ):
            return
        _logout_and_back()

    # ── Loop principal ────────────────────────────────────────────────────

    while True:
        lw = show_login()
        root.mainloop()

        # ¿Salió por la X del login?
        if _exit_program:
            break

        # ¿Login exitoso?
        if not getattr(lw, 'login_success', False):
            # Cerró el login sin hacer login → salir
            break

        # Mostrar dashboard
        show_dashboard()
        root.mainloop()

        # Al salir del mainloop del dashboard (X o Cerrar Sesión):
        # el while continúa y muestra el login de nuevo
        # a menos que _exit_program sea True
        if _exit_program:
            break

    # Cerrar la ventana definitivamente
    try:
        root.destroy()
    except Exception:
        pass


if __name__ == "__main__":
    main()
