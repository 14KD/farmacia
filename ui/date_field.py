"""
ui/date_field.py — Campo de fecha reutilizable con calendario popup.
Uso:
    from ui.date_field import DateField
    self.date_from = DateField(parent, label="Desde", value="2024-01-01")
    self.date_from.grid(row=0, column=0, sticky="ew")
    valor = self.date_from.get()   # retorna "YYYY-MM-DD"
    self.date_from.set("2024-06-01")
    self.date_from.clear()
"""
import customtkinter as ctk
from tkinter import ttk
import calendar as cal_mod
from datetime import date as _date

BG          = "#0F1117"
CARD        = "#1A1D27"
CARD_BORDER = "#252836"
ACCENT      = "#3DD68C"
TEXT        = "#FFFFFF"
SUBTEXT     = "#8B8FA8"
INPUT_BG    = "#23263A"
INPUT_BORDER= "#2E3148"

MONTHS_ES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
             "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
DAYS_ES   = ["Lu","Ma","Mi","Ju","Vi","Sa","Do"]


class DateField(ctk.CTkFrame):
    """
    Widget de fecha con entry + botón 📅 que abre un calendario popup.
    Compatible como reemplazo directo de CTkEntry para fechas.
    """
    def __init__(self, parent, label: str = "", value: str = "",
                 on_change=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._on_change = on_change

        if label:
            ctk.CTkLabel(self, text=label, font=("Arial", 11),
                         text_color=SUBTEXT).pack(anchor="w", padx=2)

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", pady=(3, 0))

        ef = ctk.CTkFrame(row, fg_color=INPUT_BG, corner_radius=8,
                          border_width=1, border_color=INPUT_BORDER)
        ef.pack(side="left", fill="x", expand=True)

        self._entry = ctk.CTkEntry(
            ef, border_width=0, fg_color="transparent",
            height=38, font=("Arial", 13), text_color=TEXT)
        if value:
            self._entry.insert(0, str(value))
        self._entry.pack(fill="x", padx=8)

        ctk.CTkButton(
            row, text="📅", width=44, height=38, corner_radius=8,
            fg_color=INPUT_BG, hover_color="#1A2E22",
            text_color=ACCENT, font=("Arial", 16),
            command=self._open_calendar
        ).pack(side="left", padx=(6, 0))

    # ── Interfaz pública ─────────────────────────────────────────────
    def get(self) -> str:
        return self._entry.get().strip()

    def set(self, value: str):
        self._entry.delete(0, "end")
        self._entry.insert(0, str(value))

    def clear(self):
        self._entry.delete(0, "end")

    def insert(self, idx, value: str):
        """Compatibilidad con CTkEntry."""
        self._entry.delete(0, "end")
        self._entry.insert(0, str(value))

    def delete(self, start, end):
        """Compatibilidad con CTkEntry."""
        self._entry.delete(start, end)

    def focus(self):
        self._entry.focus()

    # ── Calendario popup ─────────────────────────────────────────────
    def _open_calendar(self):
        try:
            current = _date.fromisoformat(self._entry.get().strip())
        except Exception:
            current = _date.today()

        # Buscar la ventana raíz
        root = self.winfo_toplevel()

        popup = ctk.CTkToplevel(root)
        popup.title("Seleccionar Fecha")
        popup.resizable(False, False)
        popup.grab_set()
        popup.configure(fg_color="#0F1117")

        # Centrar sobre la ventana padre
        popup.update_idletasks()
        pw, ph = 340, 330
        rx = root.winfo_rootx() + root.winfo_width()  // 2 - pw // 2
        ry = root.winfo_rooty() + root.winfo_height() // 2 - ph // 2
        popup.geometry(f"{pw}x{ph}+{rx}+{ry}")

        state = {"year": current.year, "month": current.month, "selected": current}

        # Header
        hdr = ctk.CTkFrame(popup, fg_color="#1A1D27", corner_radius=0)
        hdr.pack(fill="x")

        prev_btn = ctk.CTkButton(hdr, text="◀", width=36, height=36,
                                  fg_color="transparent", hover_color="#252836",
                                  text_color=ACCENT, font=("Arial", 14, "bold"))
        prev_btn.pack(side="left", padx=4, pady=6)

        next_btn = ctk.CTkButton(hdr, text="▶", width=36, height=36,
                                  fg_color="transparent", hover_color="#252836",
                                  text_color=ACCENT, font=("Arial", 14, "bold"))
        next_btn.pack(side="right", padx=4, pady=6)

        # Selectores rápidos de mes y año: para no tener que darle a ◀▶
        # decenas de veces para llegar a una fecha lejana (ej. vencimientos
        # a 1-2 años). Mismo estilo oscuro que el resto del calendario.
        picker_row = ctk.CTkFrame(hdr, fg_color="transparent")
        picker_row.pack(side="left", expand=True)

        _years = [str(y) for y in range(_date.today().year - 5, _date.today().year + 16)]

        month_menu = ctk.CTkOptionMenu(
            picker_row, values=MONTHS_ES, width=118, height=30,
            fg_color=INPUT_BG, button_color="#2A2D3A",
            button_hover_color="#3A3D52", dropdown_fg_color="#1A1D27",
            dropdown_hover_color="#1A2E22", text_color=TEXT,
            font=("Arial", 11))
        month_menu.pack(side="left", padx=(0, 4))

        year_menu = ctk.CTkOptionMenu(
            picker_row, values=_years, width=80, height=30,
            fg_color=INPUT_BG, button_color="#2A2D3A",
            button_hover_color="#3A3D52", dropdown_fg_color="#1A1D27",
            dropdown_hover_color="#1A2E22", text_color=TEXT,
            font=("Arial", 11))
        year_menu.pack(side="left")

        # Grid de días
        grid_f = ctk.CTkFrame(popup, fg_color="#1A1D27", corner_radius=0)
        grid_f.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        def build():
            for w in grid_f.winfo_children():
                w.destroy()
            y, m = state["year"], state["month"]
            month_menu.set(MONTHS_ES[m - 1])
            year_menu.set(str(y))

            # Cabecera días
            for i, d in enumerate(DAYS_ES):
                color = "#EF4444" if i >= 5 else "#8B8FA8"
                ctk.CTkLabel(grid_f, text=d, font=("Arial", 10, "bold"),
                             text_color=color, width=36, height=28
                             ).grid(row=0, column=i, padx=1, pady=(4, 2))

            first   = cal_mod.monthrange(y, m)[0]
            days_in = cal_mod.monthrange(y, m)[1]
            today   = _date.today()
            day = 1

            for week in range(6):
                for wd in range(7):
                    cell = week * 7 + wd
                    if cell < first or day > days_in:
                        ctk.CTkFrame(grid_f, width=36, height=32,
                                     fg_color="transparent"
                                     ).grid(row=week+1, column=wd, padx=1, pady=1)
                        continue

                    d_obj    = _date(y, m, day)
                    is_sel   = (d_obj == state["selected"])
                    is_today = (d_obj == today)
                    is_we    = (wd >= 5)

                    if is_sel:       fg, tc = "#3DD68C", "#0F1117"
                    elif is_today:   fg, tc = "#1A2E22", "#3DD68C"
                    elif is_we:      fg, tc = "transparent", "#EF4444"
                    else:            fg, tc = "transparent", "#FFFFFF"

                    ctk.CTkButton(
                        grid_f, text=str(day), width=36, height=32,
                        corner_radius=6, fg_color=fg, hover_color="#1A2E22",
                        text_color=tc, font=("Arial", 11),
                        command=lambda d=day: pick(d)
                    ).grid(row=week+1, column=wd, padx=1, pady=1)
                    day += 1
                if day > days_in:
                    break

        def pick(day):
            chosen = _date(state["year"], state["month"], day)
            state["selected"] = chosen
            self._entry.delete(0, "end")
            self._entry.insert(0, chosen.strftime("%Y-%m-%d"))
            if self._on_change:
                self._on_change(chosen.strftime("%Y-%m-%d"))
            popup.destroy()

        def prev_m():
            if state["month"] == 1:
                state["month"] = 12; state["year"] -= 1
            else:
                state["month"] -= 1
            build()

        def next_m():
            if state["month"] == 12:
                state["month"] = 1; state["year"] += 1
            else:
                state["month"] += 1
            build()

        def pick_month(name):
            state["month"] = MONTHS_ES.index(name) + 1
            build()

        def pick_year(y):
            state["year"] = int(y)
            build()

        month_menu.configure(command=pick_month)
        year_menu.configure(command=pick_year)

        prev_btn.configure(command=prev_m)
        next_btn.configure(command=next_m)
        build()
