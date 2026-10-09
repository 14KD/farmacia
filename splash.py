"""
splash.py — Pantalla de carga de FarmaFactura Pro.
Compatible con Python 3.13 y 3.14.
"""
import tkinter as tk
import threading


class SplashScreen:

    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.configure(bg="#0F1117")
        self.root.attributes("-topmost", True)

        W, H = 480, 280
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x  = (sw - W) // 2
        y  = (sh - H) // 2
        self.root.geometry(f"{W}x{H}+{x}+{y}")

        # ── Logo ──
        logo_frame = tk.Frame(self.root, bg="#0F1117")
        logo_frame.pack(expand=True)

        tk.Label(logo_frame, text="✚", font=("Arial", 42, "bold"),
                 fg="#3DD68C", bg="#1E3A2F",
                 width=3, relief="flat", pady=6).pack(side="left", padx=(0, 12))

        tk.Label(logo_frame, text="FarmaFactura Pro",
                 font=("Georgia", 26, "bold"),
                 fg="#FFFFFF", bg="#0F1117").pack(side="left")

        tk.Label(self.root, text="Sistema de Gestión Farmacéutica",
                 font=("Arial", 12), fg="#8B8FA8", bg="#0F1117").pack()

        # ── Barra de progreso ──
        bar_bg = tk.Frame(self.root, bg="#1A1D27", width=360, height=6)
        bar_bg.pack(pady=(24, 6))
        bar_bg.pack_propagate(False)

        self.bar = tk.Frame(bar_bg, bg="#3DD68C", height=6, width=0)
        self.bar.place(x=0, y=0, height=6)

        self.status_var = tk.StringVar(value="Iniciando...")
        tk.Label(self.root, textvariable=self.status_var,
                 font=("Arial", 11), fg="#8B8FA8", bg="#0F1117").pack()

        tk.Label(self.root, text="v1.0",
                 font=("Arial", 10), fg="#2A2D3A", bg="#0F1117").pack(pady=(16, 0))

        self._done  = False
        self._error = None

    def set_status(self, text: str, progress: int):
        try:
            def _update():
                try:
                    self.status_var.set(text)
                    self.bar.config(width=int(360 * progress / 100))
                    self.root.update_idletasks()
                except Exception:
                    pass
            self.root.after(0, _update)
        except Exception:
            pass

    def run_with_loading(self, tasks: list):
        def _worker():
            n    = max(len(tasks), 1)
            prog = 0
            for label, fn in tasks:
                self.set_status(label, prog)
                try:
                    # Timeout por tarea: si tarda más de 15s se omite
                    result = [None]
                    error  = [None]

                    def _run():
                        try:
                            fn()
                        except Exception as e:
                            error[0] = e

                    t = threading.Thread(target=_run, daemon=True)
                    t.start()
                    t.join(timeout=15)   # máximo 15 segundos por tarea

                    if error[0]:
                        self._error = error[0]

                except Exception as e:
                    self._error = e

                prog = min(prog + int(100 / n), 95)

            self.set_status("¡Listo!", 100)
            self._done = True
            try:
                self.root.after(500, self.root.quit)
            except Exception:
                pass

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

        try:
            self.root.mainloop()
        except Exception:
            pass

        # Ocultar sin destruir — evita que tkinter quede inválido en Python 3.14
        try:
            self.root.withdraw()
        except Exception:
            pass

        # Solo propagar errores críticos (no de conexión)
        if self._error:
            err_str = str(self._error).lower()
            if any(x in err_str for x in ["mysql", "pool", "connection", "connect"]):
                pass  # Ignorar errores de conexión en el splash
            else:
                raise self._error
