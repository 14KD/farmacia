from ui.date_field import DateField
"""
lots_ui.py — Gestión completa de lotes farmacéuticos.
Diseño consistente con el resto del sistema.
Número de lote auto-generado: LOT-YYYYMMDD-XXXX
"""
import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime, date, timedelta
from database.connection import create_connection
from exports.excel_exporter import export_to_excel
from auth import session
from utils.logger import audit
import config

BG="#0F1117"; CARD="#1A1D27"; CARD_BORDER="#252836"
ACCENT="#3DD68C"; CYAN="#22D3EE"; TEXT="#FFFFFF"; SUBTEXT="#8B8FA8"
DANGER="#EF4444"; DANGER_H="#DC2626"; WARNING="#FFA94D"; PURPLE="#C084FC"
INPUT_BG="#23263A"; INPUT_BORDER="#2E3148"


def _tree_style(name):
    s = ttk.Style(); s.theme_use("clam")
    s.configure(f"{name}.Treeview", background="#1A1D27", foreground="#FFFFFF",
                fieldbackground="#1A1D27", borderwidth=0, font=("Arial",11), rowheight=30)
    s.configure(f"{name}.Treeview.Heading", background="#1E2130",
                foreground="#8B8FA8", font=("Arial",10,"bold"), borderwidth=0)
    s.map(f"{name}.Treeview",
          background=[("selected", "#1A2E22"), ("!selected", "#1A1D27")], foreground=[("selected", "#3DD68C"), ("!selected", "#FFFFFF")])
    return f"{name}.Treeview"


def _sync_product_cost(cur, product_id: int):
    """
    Recalcula products.cost como el costo promedio ponderado de los lotes
    activos con existencia (cost * quantity_available, ponderado por cantidad).
    Se llama cada vez que se recibe, edita, ajusta o retira un lote, ya que
    cualquiera de esas acciones cambia la mezcla de costos del inventario.
    Si no queda ningún lote activo con stock, se deja el último costo conocido
    (no se resetea a 0), para no perder la referencia de costo del producto.
    """
    cur.execute("""SELECT cost, quantity_available FROM lots
                   WHERE product_id=%s AND status='activo' AND quantity_available>0""",
                (product_id,))
    rows = cur.fetchall() or []
    total_qty = sum(int(q) for _, q in rows)
    if total_qty > 0:
        weighted = sum(float(c) * int(q) for c, q in rows) / total_qty
        cur.execute("UPDATE products SET cost=%s WHERE id=%s",
                    (round(weighted, 2), product_id))




class LotsUI:
    def __init__(self, parent):
        self.parent   = parent
        self.is_admin = session.current_role in ("admin","Administrador")

        container = ctk.CTkFrame(parent, fg_color=BG, corner_radius=0)
        container.pack(fill="both", expand=True)

        # ── Encabezado ──
        hdr = ctk.CTkFrame(container, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(20,0))
        ctk.CTkLabel(hdr, text="📦  Gestión de Lotes",
                     font=("Arial",22,"bold"), text_color=TEXT).pack(side="left")
        ctk.CTkFrame(container, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=20, pady=(10,12))

        # ── Tabs ──
        self.tabs = ctk.CTkTabview(
            container,
            fg_color=CARD, corner_radius=12,
            segmented_button_fg_color="#1E2130",
            segmented_button_selected_color=ACCENT,
            segmented_button_selected_hover_color="#2EBF7A",
            segmented_button_unselected_color="#1E2130",
            segmented_button_unselected_hover_color="#252836",
            text_color=TEXT, text_color_disabled=SUBTEXT
        )
        self.tabs.pack(fill="both", expand=True, padx=20, pady=(0,20))
        for tab in ["📥  Recepción","🔍  Consulta","⚠  Alertas","📋  Movimientos"]:
            self.tabs.add(tab)

        self._build_reception(self.tabs.tab("📥  Recepción"))
        self._build_query(self.tabs.tab("🔍  Consulta"))
        self._build_alerts(self.tabs.tab("⚠  Alertas"))
        self._build_movements(self.tabs.tab("📋  Movimientos"))

    # ═══════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════
    def _card(self, parent, title=None):
        f = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=12,
                         border_width=1, border_color=CARD_BORDER)
        f.pack(fill="x", padx=4, pady=(0,10))
        if title:
            ctk.CTkLabel(f, text=title, font=("Arial",12,"bold"),
                         text_color=SUBTEXT).pack(anchor="w", padx=16, pady=(14,2))
            ctk.CTkFrame(f, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=16, pady=(0,10))
        return f

    def _lf(self, parent, label, col, row=0, padx=(0,10)):
        """Label encima + Entry"""
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=row, column=col, padx=padx, pady=(0,10), sticky="ew")
        ctk.CTkLabel(f, text=label, font=("Arial",11), text_color=SUBTEXT).pack(anchor="w", padx=2)
        ef = ctk.CTkFrame(f, fg_color=INPUT_BG, corner_radius=8,
                           border_width=1, border_color=INPUT_BORDER)
        ef.pack(fill="x", pady=(3,0))
        e = ctk.CTkEntry(ef, border_width=0, fg_color="transparent",
                          height=38, font=("Arial",13), text_color=TEXT)
        e.pack(fill="x", padx=8); return e

    def _lf_readonly(self, parent, label, value, col, color=CYAN):
        """Campo solo lectura (para número de lote auto)"""
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=0, column=col, padx=(0,10), pady=(0,10), sticky="ew")
        ctk.CTkLabel(f, text=label, font=("Arial",11), text_color=SUBTEXT).pack(anchor="w", padx=2)
        ef = ctk.CTkFrame(f, fg_color="#0D1F14", corner_radius=8,
                           border_width=1, border_color=ACCENT)
        ef.pack(fill="x", pady=(3,0))
        lbl = ctk.CTkLabel(ef, text=value, font=("Arial",13,"bold"),
                            text_color=color, anchor="w")
        lbl.pack(fill="x", padx=12, pady=8)
        return lbl

    def _dropdown(self, parent, label, values, var, col, padx=(0,10)):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=0, column=col, padx=padx, pady=(0,10), sticky="ew")
        ctk.CTkLabel(f, text=label, font=("Arial",11), text_color=SUBTEXT).pack(anchor="w", padx=2)
        ctk.CTkOptionMenu(f, values=values, variable=var,
                          fg_color=INPUT_BG, button_color="#2A2D3A",
                          button_hover_color="#3A3D52", dropdown_fg_color="#1A1D27",
                          dropdown_hover_color="#1A2E22", text_color=TEXT,
                          font=("Arial",12), height=38, dynamic_resizing=False
                          ).pack(fill="x", pady=(3,0))

    def _load_suppliers(self):
        conn = create_connection(); cur = conn.cursor()
        cur.execute("SELECT id, name FROM suppliers ORDER BY name")
        result = {r[1]: r[0] for r in cur.fetchall()}; conn.close()
        return result

    def _kpi(self, parent, col, label, value, color):
        f = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=12,
                         border_width=1, border_color=CARD_BORDER)
        f.grid(row=0, column=col, padx=(0 if col==0 else 8,0), sticky="ew")
        ctk.CTkLabel(f, text=label, font=("Arial",10),
                     text_color=SUBTEXT).pack(anchor="w", padx=14, pady=(12,0))
        ctk.CTkLabel(f, text=value, font=("Arial",22,"bold"),
                     text_color=color).pack(anchor="w", padx=14, pady=(0,12))

    # ═══════════════════════════════════════════
    # CALENDARIO POPUP (reutilizable)
    # ═══════════════════════════════════════════
    def _open_calendar(self, entry_widget, on_pick=None):
        """Popup de calendario — pone la fecha elegida en entry_widget."""
        import tkinter as tk
        import calendar as cal_mod
        from datetime import date as _date

        try:
            current = _date.fromisoformat(entry_widget.get().strip())
        except Exception:
            current = _date.today()

        popup = ctk.CTkToplevel(self.parent)
        popup.title("Seleccionar Fecha")
        popup.resizable(False, False)
        popup.grab_set()
        popup.configure(fg_color="#0F1117")
        popup.update_idletasks()
        pw, ph = 320, 320
        sx = self.parent.winfo_rootx() + self.parent.winfo_width()  // 2 - pw // 2
        sy = self.parent.winfo_rooty() + self.parent.winfo_height() // 2 - ph // 2
        popup.geometry(f"{pw}x{ph}+{sx}+{sy}")

        state = {"year": current.year, "month": current.month}
        MONTHS = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
                  "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
        DAYS   = ["Lu","Ma","Mi","Ju","Vi","Sa","Do"]

        hdr = ctk.CTkFrame(popup, fg_color="#1A1D27", corner_radius=0)
        hdr.pack(fill="x")
        prev_btn = ctk.CTkButton(hdr, text="◀", width=36, height=36,
                                  fg_color="transparent", hover_color="#252836",
                                  text_color="#3DD68C", font=("Arial",14,"bold"))
        prev_btn.pack(side="left", padx=4, pady=6)
        month_lbl = ctk.CTkLabel(hdr, text="", font=("Arial",13,"bold"),
                                  text_color="#FFFFFF", width=200)
        month_lbl.pack(side="left", expand=True)
        next_btn = ctk.CTkButton(hdr, text="▶", width=36, height=36,
                                  fg_color="transparent", hover_color="#252836",
                                  text_color="#3DD68C", font=("Arial",14,"bold"))
        next_btn.pack(side="right", padx=4, pady=6)

        grid_f = ctk.CTkFrame(popup, fg_color="#1A1D27", corner_radius=0)
        grid_f.pack(fill="both", expand=True, padx=8, pady=(0,8))

        def build():
            for w in grid_f.winfo_children(): w.destroy()
            y, m = state["year"], state["month"]
            month_lbl.configure(text=f"{MONTHS[m-1]}  {y}")
            for i, d in enumerate(DAYS):
                c = "#EF4444" if i >= 5 else "#8B8FA8"
                ctk.CTkLabel(grid_f, text=d, font=("Arial",10,"bold"),
                             text_color=c, width=36, height=28
                             ).grid(row=0, column=i, padx=1, pady=(4,2))
            first = cal_mod.monthrange(y, m)[0]
            days_in = cal_mod.monthrange(y, m)[1]
            today = _date.today()
            day = 1
            for week in range(6):
                for wd in range(7):
                    cell = week * 7 + wd
                    if cell < first or day > days_in:
                        ctk.CTkFrame(grid_f, width=36, height=32,
                                     fg_color="transparent"
                                     ).grid(row=week+1, column=wd, padx=1, pady=1)
                        continue
                    d_obj = _date(y, m, day)
                    is_sel = (d_obj == current)
                    is_tod = (d_obj == today)
                    is_we  = (wd >= 5)
                    if is_sel:   fg, tc = "#3DD68C", "#0F1117"
                    elif is_tod: fg, tc = "#1A2E22", "#3DD68C"
                    elif is_we:  fg, tc = "transparent", "#EF4444"
                    else:        fg, tc = "transparent", "#FFFFFF"
                    ctk.CTkButton(
                        grid_f, text=str(day), width=36, height=32,
                        corner_radius=6, fg_color=fg, hover_color="#1A2E22",
                        text_color=tc, font=("Arial",11),
                        command=lambda d=day: pick(d)
                    ).grid(row=week+1, column=wd, padx=1, pady=1)
                    day += 1
                if day > days_in: break

        def pick(day):
            chosen = _date(state["year"], state["month"], day)
            entry_widget.delete(0, "end")
            entry_widget.insert(0, chosen.strftime("%Y-%m-%d"))
            if on_pick: on_pick(chosen.strftime("%Y-%m-%d"))
            popup.destroy()

        def prev_m():
            if state["month"] == 1: state["month"] = 12; state["year"] -= 1
            else: state["month"] -= 1
            build()

        def next_m():
            if state["month"] == 12: state["month"] = 1; state["year"] += 1
            else: state["month"] += 1
            build()

        prev_btn.configure(command=prev_m)
        next_btn.configure(command=next_m)
        build()

    def _validate_dates(self, expiry, received):
        """Valida formato YYYY-MM-DD y que el vencimiento no sea anterior
        a la fecha de recepción. Usar siempre antes de guardar un lote."""
        for label, val in (("Fecha de Vencimiento", expiry), ("Fecha de Recepción", received)):
            if not val:
                continue
            try:
                datetime.strptime(val, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror(
                    "Fecha inválida",
                    f"{label} no es válida ({val}). Usa el calendario 📅 "
                    f"o el formato AAAA-MM-DD.")
                return False
        if expiry and received and expiry < received:
            messagebox.showerror(
                "Fecha inválida",
                "La fecha de vencimiento no puede ser anterior a la fecha de recepción.")
            return False
        return True

    def _date_field(self, parent, label, col, row=0, padx=(0,10), value=""):
        """Campo de fecha con botón 📅 que abre el calendario popup."""
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=row, column=col, padx=padx, pady=(0,10), sticky="ew")
        ctk.CTkLabel(f, text=label, font=("Arial",11), text_color=SUBTEXT).pack(anchor="w", padx=2)
        row_f = ctk.CTkFrame(f, fg_color="transparent")
        row_f.pack(fill="x", pady=(3,0))
        ef = ctk.CTkFrame(row_f, fg_color=INPUT_BG, corner_radius=8,
                           border_width=1, border_color=INPUT_BORDER)
        ef.pack(side="left", fill="x", expand=True)
        e = ctk.CTkEntry(ef, border_width=0, fg_color="transparent",
                          height=38, font=("Arial",13), text_color=TEXT)
        if value: e.insert(0, str(value))
        e.pack(fill="x", padx=8)
        ctk.CTkButton(row_f, text="📅", width=44, height=38, corner_radius=8,
                      fg_color=INPUT_BG, hover_color="#1A2E22", text_color=ACCENT,
                      font=("Arial",16),
                      command=lambda: self._open_calendar(e)
                      ).pack(side="left", padx=(6,0))
        return e

    # ═══════════════════════════════════════════
    # TAB 1 — RECEPCIÓN
    # ═══════════════════════════════════════════
    def _build_reception(self, parent):
        # Canvas scroll manual (evita bug de CTkScrollableFrame dentro de CTkTabview)
        import tkinter as _tk
        outer = ctk.CTkFrame(parent, fg_color=BG, corner_radius=0)
        outer.pack(fill="both", expand=True)

        canvas = _tk.Canvas(outer, bg="#0F1117", highlightthickness=0)
        vsb    = ctk.CTkScrollbar(outer, command=canvas.yview,
                                   button_color=INPUT_BG,
                                   button_hover_color="#3A3D52")
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.configure(yscrollcommand=vsb.set)

        scroll = ctk.CTkFrame(canvas, fg_color=BG, corner_radius=0)
        win_id = canvas.create_window((0,0), window=scroll, anchor="nw")

        def _on_resize(event):
            canvas.itemconfig(win_id, width=event.width)
        canvas.bind("<Configure>", _on_resize)

        def _on_content(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        scroll.bind("<Configure>", _on_content)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        form = self._card(scroll, "Registrar Compra / Entrada de Mercancia")

        # ══ CABECERA: Suplidor | Fecha | N° Factura ══
        hdr_card = ctk.CTkFrame(form, fg_color="#12141C", corner_radius=8,
                                  border_width=1, border_color=CARD_BORDER)
        hdr_card.pack(fill="x", padx=16, pady=(0,8))
        ctk.CTkLabel(hdr_card, text="Datos de la Factura de Compra",
                     font=("Arial",11,"bold"), text_color=SUBTEXT
                     ).pack(anchor="w", padx=12, pady=(8,4))
        hdr_r = ctk.CTkFrame(hdr_card, fg_color="transparent")
        hdr_r.pack(fill="x", padx=12, pady=(0,10))
        hdr_r.columnconfigure((0,1,2), weight=1)

        self._suppliers_rec = self._load_suppliers()
        self.rec_supplier_var = ctk.StringVar(value="Sin proveedor")
        self._dropdown(hdr_r, "Laboratorio / Suplidor",
                       ["Sin proveedor"] + list(self._suppliers_rec.keys()),
                       self.rec_supplier_var, 0, padx=(0,8))

        self.rec_date_entry = self._date_field(
            hdr_r, "Fecha de Recepcion", 1, padx=(0,8),
            value=date.today().isoformat())

        nfac_wrap = ctk.CTkFrame(hdr_r, fg_color="transparent")
        nfac_wrap.grid(row=0, column=2, sticky="ew")
        ctk.CTkLabel(nfac_wrap, text="N de Factura de Compra",
                     font=("Arial",11), text_color=SUBTEXT).pack(anchor="w", padx=2)
        nfac_ef = ctk.CTkFrame(nfac_wrap, fg_color=INPUT_BG, corner_radius=8,
                                border_width=1, border_color=INPUT_BORDER)
        nfac_ef.pack(fill="x", pady=(3,0))
        self.rec_invoice_entry = ctk.CTkEntry(nfac_ef, border_width=0,
                                               fg_color="transparent", height=38,
                                               font=("Arial",13), text_color=TEXT,
                                               placeholder_text="FAC-2024-001")
        self.rec_invoice_entry.pack(fill="x", padx=8)

        # ══ AGREGAR PRODUCTO ══
        prod_card = ctk.CTkFrame(form, fg_color="#12141C", corner_radius=8,
                                  border_width=1, border_color=CARD_BORDER)
        prod_card.pack(fill="x", padx=16, pady=(0,8))
        ctk.CTkLabel(prod_card, text="Agregar Producto",
                     font=("Arial",11,"bold"), text_color=SUBTEXT
                     ).pack(anchor="w", padx=12, pady=(8,4))

        pc = ctk.CTkFrame(prod_card, fg_color="transparent")
        pc.pack(fill="x", padx=12, pady=(0,4))

        # Buscar Producto (fila completa)
        pf = ctk.CTkFrame(pc, fg_color="transparent")
        pf.pack(fill="x", pady=(0,6))
        ctk.CTkLabel(pf, text="Producto",
                     font=("Arial",11), text_color=SUBTEXT).pack(anchor="w", padx=2)
        sf = ctk.CTkFrame(pf, fg_color=INPUT_BG, corner_radius=8,
                           border_width=1, border_color=INPUT_BORDER)
        sf.pack(fill="x", pady=(3,0))
        srow = ctk.CTkFrame(sf, fg_color="transparent")
        srow.pack(fill="x", padx=6, pady=3)
        self.rec_product_entry = ctk.CTkEntry(
            srow, border_width=0, fg_color="transparent",
            height=34, font=("Arial",13), text_color=TEXT,
            placeholder_text="Escribir nombre o principio activo...")
        self.rec_product_entry.pack(side="left", fill="x", expand=True)
        self.rec_product_entry.bind("<KeyRelease>", self._on_product_search)
        self._rec_search_popup = ctk.CTkFrame(pf, fg_color=CARD, corner_radius=8,
                                               border_width=1, border_color=CARD_BORDER)
        self._rec_search_btns = []
        self._rec_product = None

        # Fila B: Cantidad | Descripcion | Presentacion | Costo
        rb = ctk.CTkFrame(pc, fg_color="transparent")
        rb.pack(fill="x", pady=(0,6))
        rb.columnconfigure((0,1,2,3), weight=1)
        self.rec_qty_entry = self._lf(rb, "Cantidad", 0, padx=(0,8))

        desc_w = ctk.CTkFrame(rb, fg_color="transparent")
        desc_w.grid(row=0, column=1, padx=(0,8), sticky="ew")
        ctk.CTkLabel(desc_w, text="Descripcion (opcional)",
                     font=("Arial",11), text_color=SUBTEXT).pack(anchor="w", padx=2)
        desc_ef2 = ctk.CTkFrame(desc_w, fg_color=INPUT_BG, corner_radius=8,
                                  border_width=1, border_color=INPUT_BORDER)
        desc_ef2.pack(fill="x", pady=(3,0))
        self.rec_notes_entry = ctk.CTkEntry(desc_ef2, border_width=0,
                                             fg_color="transparent", height=38,
                                             font=("Arial",12), text_color=TEXT,
                                             placeholder_text="Observacion...")
        self.rec_notes_entry.pack(fill="x", padx=8)

        pres_w = ctk.CTkFrame(rb, fg_color="transparent")
        pres_w.grid(row=0, column=2, padx=(0,8), sticky="ew")
        ctk.CTkLabel(pres_w, text="Presentacion",
                     font=("Arial",11), text_color=SUBTEXT).pack(anchor="w", padx=2)
        self.rec_unit_var  = ctk.StringVar(value="Unidad (x1)")
        self._rec_unit_map = {"Unidad (x1)": 1}
        self.rec_unit_menu = ctk.CTkOptionMenu(
            pres_w, variable=self.rec_unit_var, values=["Unidad (x1)"],
            fg_color=INPUT_BG, button_color="#2A2D3A",
            button_hover_color="#3A3D52", dropdown_fg_color="#1A1D27",
            dropdown_hover_color="#1A2E22", text_color=TEXT,
            font=("Arial",12), height=38, dynamic_resizing=False)
        self.rec_unit_menu.pack(fill="x", pady=(3,0))

        cost_w = ctk.CTkFrame(rb, fg_color="transparent")
        cost_w.grid(row=0, column=3, sticky="ew")
        ctk.CTkLabel(cost_w, text="Costo Unitario",
                     font=("Arial",11), text_color=SUBTEXT).pack(anchor="w", padx=2)
        cost_ef2 = ctk.CTkFrame(cost_w, fg_color=INPUT_BG, corner_radius=8,
                                  border_width=1, border_color=INPUT_BORDER)
        cost_ef2.pack(fill="x", pady=(3,0))
        self.rec_cost_entry = ctk.CTkEntry(cost_ef2, border_width=0,
                                            fg_color="transparent", height=38,
                                            font=("Arial",12), text_color=TEXT,
                                            placeholder_text="0.00")
        self.rec_cost_entry.pack(fill="x", padx=8)

        # Fila C: N° Lote | Fecha Vencimiento | ITBIS | Descuento%
        rc2 = ctk.CTkFrame(pc, fg_color="transparent")
        rc2.pack(fill="x", pady=(0,6))
        rc2.columnconfigure((0,1,2,3), weight=1)

        lot_w = ctk.CTkFrame(rc2, fg_color="transparent")
        lot_w.grid(row=0, column=0, padx=(0,8), sticky="ew")
        ctk.CTkLabel(lot_w, text="N de Lote",
                     font=("Arial",11), text_color=SUBTEXT).pack(anchor="w", padx=2)
        self._lot_num_entry = ctk.CTkEntry(
            lot_w, placeholder_text="LOT-2024-001",
            fg_color=INPUT_BG, border_color=ACCENT,
            text_color=TEXT, font=("Arial",12), height=38)
        self._lot_num_entry.pack(fill="x", pady=(3,0))

        self.rec_expiry_entry = self._date_field(rc2, "Fecha de Vencimiento", 1, padx=(0,8))

        _cfg_itbis = float(config.load()["billing"].get("tax_rate", 0))
        itbis_f = ctk.CTkFrame(rc2, fg_color="transparent")
        itbis_f.grid(row=0, column=2, padx=(0,8), sticky="ew")
        ctk.CTkLabel(itbis_f, text="ITBIS",
                     font=("Arial",11), text_color=SUBTEXT).pack(anchor="w", padx=2)
        self.rec_itbis_var = ctk.BooleanVar(value=_cfg_itbis > 0)
        itbis_row = ctk.CTkFrame(itbis_f, fg_color="transparent")
        itbis_row.pack(fill="x", pady=(3,0))
        ctk.CTkCheckBox(itbis_row, text="Si", variable=self.rec_itbis_var,
                        fg_color=ACCENT, hover_color="#2EBF7A",
                        checkmark_color="#0F1117", text_color=TEXT,
                        font=("Arial",12), height=36).pack(side="left")
        itbis_ef = ctk.CTkFrame(itbis_row, fg_color=INPUT_BG, corner_radius=8,
                                 border_width=1, border_color=INPUT_BORDER)
        itbis_ef.pack(side="left", fill="x", expand=True, padx=(6,0))
        self.rec_itbis_pct = ctk.CTkEntry(itbis_ef, border_width=0,
                                           fg_color="transparent", height=36,
                                           font=("Arial",12), text_color=TEXT,
                                           placeholder_text="18")
        self.rec_itbis_pct.pack(fill="x", padx=6)
        if _cfg_itbis > 0:
            self.rec_itbis_pct.insert(0, str(_cfg_itbis))

        desc_f3 = ctk.CTkFrame(rc2, fg_color="transparent")
        desc_f3.grid(row=0, column=3, sticky="ew")
        ctk.CTkLabel(desc_f3, text="Descuento %",
                     font=("Arial",11), text_color=SUBTEXT).pack(anchor="w", padx=2)
        desc_ef3 = ctk.CTkFrame(desc_f3, fg_color=INPUT_BG, corner_radius=8,
                                  border_width=1, border_color=INPUT_BORDER)
        desc_ef3.pack(fill="x", pady=(3,0))
        self.rec_discount_entry = ctk.CTkEntry(desc_ef3, border_width=0,
                                                fg_color="transparent", height=36,
                                                font=("Arial",12), text_color=TEXT,
                                                placeholder_text="0")
        self.rec_discount_entry.pack(fill="x", padx=8)

        ctk.CTkLabel(pc, text="Costo final = Costo x (1+ITBIS%) x (1-Desc%)",
                     font=("Arial",9), text_color="#3A3D52").pack(anchor="w", pady=(0,4))

        # Registro Sanitario
        rs_w = ctk.CTkFrame(pc, fg_color="transparent")
        rs_w.pack(fill="x", pady=(0,6))
        ctk.CTkLabel(rs_w, text="Registro Sanitario (opcional)",
                     font=("Arial",11), text_color=SUBTEXT).pack(anchor="w", padx=2)
        rs_ef = ctk.CTkFrame(rs_w, fg_color=INPUT_BG, corner_radius=8,
                              border_width=1, border_color=INPUT_BORDER)
        rs_ef.pack(fill="x", pady=(3,0))
        self.rec_sanitary_entry = ctk.CTkEntry(rs_ef, border_width=0,
                                                fg_color="transparent", height=36,
                                                font=("Arial",12), text_color=TEXT,
                                                placeholder_text="Numero de autorizacion sanitaria")
        self.rec_sanitary_entry.pack(fill="x", padx=8)

        ctk.CTkButton(prod_card, text="Agregar a la Factura",
                      height=40, corner_radius=8,
                      fg_color=ACCENT, hover_color="#2EBF7A",
                      text_color="#0F1117", font=("Arial",12,"bold"),
                      command=self._add_to_invoice_list
                      ).pack(fill="x", padx=12, pady=(0,10))

        # ══ TABLA DE PRODUCTOS ══
        mp_card = ctk.CTkFrame(form, fg_color="#12141C", corner_radius=8,
                                border_width=1, border_color=CARD_BORDER)
        mp_card.pack(fill="x", padx=16, pady=(0,8))
        ctk.CTkLabel(mp_card, text="Productos en esta Factura",
                     font=("Arial",11,"bold"), text_color=SUBTEXT
                     ).pack(anchor="w", padx=12, pady=(8,4))

        from tkinter import ttk as _ttv
        stv = _ttv.Style(); stv.theme_use("clam")
        stv.configure("INV.Treeview", background="#1A1D27", foreground="#FFFFFF",
                       fieldbackground="#1A1D27", borderwidth=0,
                       font=("Arial",10), rowheight=26)
        stv.configure("INV.Treeview.Heading", background="#1E2130", foreground="#8B8FA8",
                       font=("Arial",9,"bold"), borderwidth=0)
        stv.map("INV.Treeview",
                background=[("selected","#1A2E22"),("!selected","#1A1D27")],
                foreground=[("selected","#3DD68C"),("!selected","#FFFFFF")])
        self._inv_items_tree = _ttv.Treeview(
            mp_card,
            columns=("Producto","Cant","Descripcion","Presentacion","Costo","Lote","Vence","ITBIS","Desc","Total"),
            show="headings", height=4, style="INV.Treeview")
        for cn,cw,anc in [
            ("Producto",150,"w"),("Cant",50,"center"),("Descripcion",110,"w"),
            ("Presentacion",85,"center"),("Costo",75,"e"),
            ("Lote",85,"w"),("Vence",85,"center"),
            ("ITBIS",50,"center"),("Desc",50,"center"),("Total",80,"e")
        ]:
            self._inv_items_tree.heading(cn, text=cn)
            self._inv_items_tree.column(cn, width=cw, anchor=anc,
                                         stretch=(cn in ("Producto","Descripcion")))
        self._inv_items_tree.pack(fill="x", padx=8, pady=(0,4))
        self._inv_items = []

        mp_btns2 = ctk.CTkFrame(mp_card, fg_color="transparent")
        mp_btns2.pack(anchor="w", padx=12, pady=(0,10))
        ctk.CTkButton(mp_btns2, text="Quitar seleccionado",
                      height=28, corner_radius=6,
                      fg_color="#2E1A1A", hover_color="#DC2626",
                      text_color="#EF4444", font=("Arial",10),
                      command=self._remove_from_invoice_list).pack(side="left")

        # ── Botones ──
        br = ctk.CTkFrame(form, fg_color="transparent")
        br.pack(fill="x", padx=16, pady=(4,16))
        # ── Botones ──
        br = ctk.CTkFrame(form, fg_color="transparent")
        br.pack(fill="x", padx=16, pady=(4,16))
        ctk.CTkButton(br, text="Registrar Factura Completa", height=44, corner_radius=10,
                      fg_color=ACCENT, hover_color="#2EBF7A",
                      text_color="#0F1117", font=("Arial",13,"bold"),
                      command=self.register_lot).pack(side="left")
        ctk.CTkButton(br, text="Limpiar", height=44, corner_radius=10,
                      fg_color=INPUT_BG, hover_color="#2E3148",
                      text_color=SUBTEXT, font=("Arial",12),
                      command=self._clear_reception).pack(side="left", padx=(8,0))

        # ── Últimos lotes ──
        ctk.CTkLabel(scroll, text="Últimos Lotes Registrados",
                     font=("Arial",12,"bold"), text_color=SUBTEXT
                     ).pack(anchor="w", padx=4, pady=(4,6))

        tc = ctk.CTkFrame(scroll, fg_color=CARD, corner_radius=12,
                          border_width=1, border_color=CARD_BORDER)
        tc.pack(fill="x", padx=4, pady=(0,4))
        sty = _tree_style("REC")
        cols = ("ID","Producto","N° Lote","Recibidas","Disponibles","Vencimiento","Estado")
        self.rec_tree = ttk.Treeview(tc, columns=cols, show="headings", height=8, style=sty)
        try:
            self.rec_tree.configure(style=self.rec_tree["style"])
            self.rec_tree.tk.call("ttk::style", "configure", self.rec_tree["style"], "-fieldbackground", "#1A1D27")
            self.rec_tree.tk.call("ttk::style", "configure", self.rec_tree["style"], "-background", "#1A1D27")
            self.rec_tree.tk.call("ttk::style", "configure", self.rec_tree["style"], "-foreground", "#FFFFFF")
        except Exception:
            pass
        for col, w, anc in [("ID",55,"center"),("Producto",200,"w"),("N° Lote",130,"center"),
                              ("Recibidas",80,"center"),("Disponibles",90,"center"),
                              ("Vencimiento",110,"center"),("Estado",90,"center")]:
            self.rec_tree.heading(col,text=col); self.rec_tree.column(col,width=w,anchor=anc)
        self.rec_tree.tag_configure("activo",   foreground=ACCENT)
        self.rec_tree.tag_configure("agotado",  foreground=DANGER)
        self.rec_tree.tag_configure("vencido",  foreground=DANGER)
        self.rec_tree.tag_configure("retirado", foreground=SUBTEXT)
        self.rec_tree.pack(fill="x", padx=12, pady=12)
        self._load_recent_lots()

        # Enter guarda el lote, Escape limpia — no depender solo del mouse
        def _submit_lot(event=None):
            self.register_lot()
            return "break"
        for entry in (self._lot_num_entry, self.rec_qty_entry, self.rec_cost_entry,
                      self.rec_notes_entry):
            entry.bind("<Return>", _submit_lot)
            entry.bind("<Escape>", lambda e: self._clear_reception())

    def _on_product_search(self, event=None):
        q = self.rec_product_entry.get().strip()
        for b in self._rec_search_btns: b.destroy()
        self._rec_search_btns.clear()
        if not q:
            self._rec_search_popup.pack_forget(); return
        conn = create_connection(); cur = conn.cursor()
        cur.execute("SELECT id, name FROM products WHERE name LIKE ? OR CAST(id AS CHAR)=? LIMIT 6",
                    (f"%{q}%", q))
        results = cur.fetchall(); conn.close()
        if not results:
            self._rec_search_popup.pack_forget(); return
        self._rec_search_popup.pack(fill="x", pady=(2,0))
        for pid, name in results:
            btn = ctk.CTkButton(self._rec_search_popup, text=f"[{pid}]  {name}",
                                anchor="w", height=32, corner_radius=0,
                                fg_color="transparent", hover_color=HOVER if 'HOVER' in dir() else "#1A2E22",
                                text_color=TEXT, font=("Arial",12),
                                command=lambda p=(pid,name): self._select_rec_product(p))
            btn.pack(fill="x", padx=6, pady=1)
            self._rec_search_btns.append(btn)

    def _add_to_invoice_list(self):
        """Agrega el producto actual a la lista de la factura."""
        from tkinter import messagebox as _mb
        if not self._rec_product:
            _mb.showwarning("", "Selecciona un producto primero."); return
        try:
            qty_input = int(self.rec_qty_entry.get().strip())
            if qty_input <= 0: raise ValueError
        except ValueError:
            _mb.showerror("Error", "Cantidad debe ser entero positivo."); return

        lot_num = self._lot_num_entry.get().strip()
        if not lot_num:
            _mb.showerror("", "Ingresa el numero de lote."); return

        unit_label  = self.rec_unit_var.get()
        unit_factor = self._rec_unit_map.get(unit_label, 1)
        qty         = qty_input * unit_factor

        cost_raw  = float(self.rec_cost_entry.get().strip() or 0)
        itbis_pct = float(self.rec_itbis_pct.get().strip() or 0) if self.rec_itbis_var.get() else 0.0
        disc_pct  = float(self.rec_discount_entry.get().strip() or 0)
        cost_real = cost_raw * (1 + itbis_pct/100) * (1 - disc_pct/100)

        expiry_raw = self.rec_expiry_entry.get().strip() or None
        if expiry_raw:
            try:
                date.fromisoformat(expiry_raw)
            except ValueError:
                _mb.showerror("Fecha invalida",
                    f"Fecha de vencimiento '{expiry_raw}' no valida.\n"
                    "Usa el boton del calendario."); return

        item = {
            "pid":          self._rec_product["id"],
            "product_name": self._rec_product["name"],
            "lot_number":   lot_num,
            "quantity":     qty,
            "qty_input":    qty_input,
            "unit_label":   unit_label,
            "unit_factor":  unit_factor,
            "cost":         cost_raw,
            "itbis_pct":    itbis_pct,
            "disc_pct":     disc_pct,
            "cost_real":    cost_real,
            "expiry":       expiry_raw,
            "recv_date":    self.rec_date_entry.get().strip() or date.today().isoformat(),
            "supplier_var": self.rec_supplier_var.get(),
            "notes":        self.rec_notes_entry.get().strip(),
            "invoice_num":  self.rec_invoice_entry.get().strip() if hasattr(self,"rec_invoice_entry") else "",
            "sanitary":     self.rec_sanitary_entry.get().strip() if hasattr(self,"rec_sanitary_entry") else "",
        }
        self._inv_items.append(item)

        import config as _cfg
        cy = _cfg.load()["billing"].get("currency","RD$")

        expiry_disp = "—"
        if expiry_raw:
            try:
                expiry_disp = date.fromisoformat(expiry_raw).strftime("%d/%m/%Y")
            except Exception:
                expiry_disp = expiry_raw

        self._inv_items_tree.insert("","end", values=(
            item["product_name"],
            qty_input,
            item["notes"] or "—",
            unit_label,
            f"{cy}{cost_raw:,.2f}",
            lot_num,
            expiry_disp,
            f"{itbis_pct:.0f}%" if itbis_pct else "—",
            f"{disc_pct:.0f}%" if disc_pct else "—",
            f"{cy}{cost_real:,.2f}"
        ))

        from tkinter import messagebox as _mb2
        _mb2.showinfo("Agregado",
            f"Producto agregado: {item['product_name']} ({qty_input} {unit_label})")

        # Limpiar campos del producto para el siguiente
        self.rec_product_entry.delete(0,"end")
        self._rec_product = None
        self._lot_num_entry.delete(0,"end")
        self.rec_qty_entry.delete(0,"end")
        self.rec_expiry_entry.delete(0,"end")
        self.rec_cost_entry.delete(0,"end")
        self.rec_notes_entry.delete(0,"end")
        if hasattr(self,"rec_itbis_pct"):
            self.rec_itbis_pct.delete(0,"end")
            if getattr(self,"_cfg_itbis_default",0) > 0:
                self.rec_itbis_pct.insert(0,str(self._cfg_itbis_default))
        if hasattr(self,"rec_discount_entry"):
            self.rec_discount_entry.delete(0,"end")

    def _remove_from_invoice_list(self):
        """Quita el item seleccionado de la lista."""
        sel = self._inv_items_tree.selection()
        if not sel: return
        idx = self._inv_items_tree.index(sel[0])
        self._inv_items_tree.delete(sel[0])
        if 0 <= idx < len(self._inv_items):
            self._inv_items.pop(idx)

    def _register_invoice_lots(self):
        """Registra todos los lotes de la factura de una sola vez."""
        from tkinter import messagebox as _mb
        if not self._inv_items:
            _mb.showwarning("", "No hay productos en la lista."); return
        if not _mb.askyesno("Confirmar",
            f"Registrar {len(self._inv_items)} producto(s) de esta factura?"):
            return

        invoice_num = self.rec_invoice_entry.get().strip() if hasattr(self,"rec_invoice_entry") else ""
        u = session.current_user
        username = u[1] if isinstance(u,tuple) else str(u)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        errors = []; registered = 0
        conn = create_connection(); cur = conn.cursor()
        try:
            for item in self._inv_items:
                try:
                    pid       = item["pid"]
                    lot_num   = item["lot_number"]
                    qty       = item["quantity"]
                    cost_real = item["cost_real"]
                    expiry    = item.get("expiry")
                    recv_date = item.get("recv_date", date.today().isoformat())
                    sup_id    = self._suppliers_rec.get(item["supplier_var"])
                    notes_full = item.get("notes","")
                    if invoice_num:
                        notes_full = ("Factura: " + invoice_num +
                                      (" | " + notes_full if notes_full else ""))
                    if item.get("sanitary"):
                        notes_full += " | Reg.San: " + item["sanitary"]

                    cur.execute("""INSERT INTO lots
                        (product_id,lot_number,quantity_received,quantity_available,
                         cost,expiry_date,received_date,supplier_id,notes,status)
                        VALUES(?,?,?,?,?,?,?,?,?,'activo')""",
                        (pid,lot_num,qty,qty,cost_real,expiry,recv_date,sup_id,notes_full))
                    lot_id = cur.lastrowid
                    cur.execute("""INSERT INTO lot_movements
                        (lot_id,type,quantity,reason,username,timestamp)
                        VALUES(?,?,?,?,?,?)""",
                        (lot_id,"entrada",qty,"Recepcion de mercancia",username,ts))
                    cur.execute("""UPDATE products SET stock=(
                        SELECT COALESCE(SUM(quantity_available),0)
                        FROM lots WHERE product_id=? AND status='activo') WHERE id=?""",
                        (pid,pid))
                    audit("LOTE_REGISTRADO",
                          f"Producto #{pid} | Lote: {lot_num} | Qty: {qty} | Factura: {invoice_num}",
                          module="lotes")
                    registered += 1
                except Exception as e:
                    errors.append(f"{item['product_name']}: {e}")
            conn.commit()
        except Exception as ex:
            conn.rollback()
            _mb.showerror("Error general", str(ex)); return
        finally:
            conn.close()

        if errors:
            _mb.showwarning("Parcialmente registrado",
                f"{registered} lote(s) registrado(s).\n"
                "Errores:\n" + "\n".join(errors))
        else:
            _mb.showinfo("Factura Registrada",
                f"Se registraron {registered} lote(s) correctamente." +
                (f"\nFactura: {invoice_num}" if invoice_num else ""))

        self._inv_items.clear()
        for i in self._inv_items_tree.get_children():
            self._inv_items_tree.delete(i)
        self._clear_reception()
        self._load_recent_lots()

    def _select_rec_product(self, product):
        pid, name = product
        self._rec_product = {"id": pid, "name": name}
        self.rec_product_entry.delete(0,"end")
        self.rec_product_entry.insert(0, f"[{pid}]  {name}")
        for b in self._rec_search_btns: b.destroy()
        self._rec_search_btns.clear()
        self._rec_search_popup.pack_forget()
        self._load_rec_units(pid)
        self.rec_qty_entry.focus()

    def _load_rec_units(self, product_id: int):
        """Carga las presentaciones del producto en el selector de recepción."""
        try:
            conn = create_connection(); cur = conn.cursor()
            cur.execute("""SELECT unit_name, factor FROM product_units
                           WHERE product_id = %s ORDER BY factor ASC""", (product_id,))
            rows = cur.fetchall(); conn.close()
            self._rec_unit_map = {}   # label → factor
            if not rows:
                self._rec_unit_map["Unidad (×1)"] = 1
            else:
                for uname, factor in rows:
                    self._rec_unit_map[f"{uname} (×{int(factor)})"] = int(factor)
            options = list(self._rec_unit_map.keys())
            self.rec_unit_var.set(options[0])
            self.rec_unit_menu.configure(values=options)
        except Exception:
            self._rec_unit_map = {"Unidad (×1)": 1}
            self.rec_unit_var.set("Unidad (×1)")
            self.rec_unit_menu.configure(values=["Unidad (×1)"])

    def register_lot(self):
        """Registrar lote(s) — si hay items en lista, registra todos; si no, el formulario."""
        if getattr(self, "_inv_items", []):
            self._register_invoice_lots()
            return
        if not self._rec_product:
            from tkinter import messagebox as _mb
            _mb.showwarning("Sin producto",
                "Selecciona un producto y presiona 'Agregar a la Factura',\n"
                "o completa el formulario y registra un solo lote.")
            return
        # Registro de un solo producto (flujo legado)
        self._add_to_invoice_list()
        if self._inv_items:
            self._register_invoice_lots()


    def _clear_reception(self):
        self._rec_product = None
        self.rec_product_entry.delete(0,"end")
        self.rec_qty_entry.delete(0,"end")
        # Limpiar tabla de factura
        if hasattr(self,"_inv_items"):
            self._inv_items.clear()
        if hasattr(self,"_inv_items_tree"):
            for i in self._inv_items_tree.get_children():
                self._inv_items_tree.delete(i)
        for attr in ["rec_invoice_entry","rec_sanitary_entry",
                     "rec_cost_entry","rec_itbis_pct","rec_discount_entry"]:
            w = getattr(self, attr, None)
            if w:
                try: w.delete(0,"end")
                except Exception: pass
        # Restaurar ITBIS desde config
        try:
            _cfg = float(config.load()["billing"].get("tax_rate", 0))
            self.rec_itbis_var.set(_cfg > 0)
            self.rec_itbis_pct.delete(0,"end")
            if _cfg > 0:
                self.rec_itbis_pct.insert(0, str(_cfg))
        except Exception:
            pass
        self.rec_cost_entry.delete(0,"end")
        self._rec_unit_map = {"Unidad (×1)": 1}
        self.rec_unit_var.set("Unidad (×1)")
        self.rec_unit_menu.configure(values=["Unidad (×1)"])
        self.rec_expiry_entry.delete(0, 'end')
        self.rec_date_entry.delete(0,"end")
        self.rec_date_entry.insert(0, date.today().isoformat())
        self.rec_notes_entry.delete(0,"end")
        self.rec_supplier_var.set("Sin proveedor")
        self._lot_num_entry.delete(0, "end")

    def _load_recent_lots(self):
        for i in self.rec_tree.get_children(): self.rec_tree.delete(i)
        conn = create_connection()
        try:
          cur = conn.cursor()
          cur.execute("""SELECT l.id, p.name, l.lot_number, l.quantity_received,
                                l.quantity_available, l.cost, l.expiry_date, l.status
                         FROM lots l JOIN products p ON l.product_id=p.id
                         ORDER BY l.id DESC LIMIT 30""")
          cfg = config.load(); cy = cfg["billing"].get("currency","$")
          today = date.today()
          rows_recent = cur.fetchall()
        finally:
          conn.close()
        for r in rows_recent:
            st = r[7]
            exp = r[6].isoformat() if hasattr(r[6], 'isoformat') else r[6]
            if r[6] and r[6] < today and st=="activo": st="vencido"
            if r[4]==0 and st=="activo": st="agotado"
            self.rec_tree.insert("","end", tags=(st,),
                values=(r[0],r[1],r[2],r[3],r[4],
                        f"{cy}{float(r[5] or 0):,.2f}",exp or "—",st.upper()))

    # ═══════════════════════════════════════════
    # TAB 2 — CONSULTA
    # ═══════════════════════════════════════════
    def _build_query(self, parent):
        # Filtros
        fcard = self._card(parent, "🔍  Filtros")
        fr = ctk.CTkFrame(fcard, fg_color="transparent")
        fr.pack(fill="x", padx=16, pady=(0,4))
        fr.columnconfigure((0,1,2,3), weight=1)
        self.q_product  = self._lf(fr,"Producto",0)
        self.q_lot      = self._lf(fr,"N° Lote",1)
        self.q_status_var = ctk.StringVar(value="Todos")
        self._dropdown(fr,"Estado",["Todos","activo","agotado","vencido","retirado"],
                       self.q_status_var, 2)
        self.q_expiry_only = ctk.BooleanVar(value=False)
        ef = ctk.CTkFrame(fr, fg_color="transparent")
        ef.grid(row=0, column=3, padx=(0,0), sticky="ew", pady=(0,10))
        ctk.CTkLabel(ef, text=" ", font=("Arial",11), text_color=SUBTEXT).pack(anchor="w")
        ctk.CTkCheckBox(ef, text="Solo próximos a vencer",
                        variable=self.q_expiry_only, fg_color=ACCENT,
                        hover_color="#2EBF7A", checkmark_color="#0F1117",
                        font=("Arial",12), text_color=TEXT).pack(anchor="w", pady=(10,0))

        br = ctk.CTkFrame(fcard, fg_color="transparent")
        br.pack(fill="x", padx=16, pady=(0,14))
        ctk.CTkButton(br, text="🔍  Buscar", height=38, corner_radius=8,
                      fg_color=ACCENT, hover_color="#2EBF7A",
                      text_color="#0F1117", font=("Arial",12,"bold"),
                      command=self.search_lots).pack(side="left")
        ctk.CTkButton(br, text="📊  Exportar", height=38, corner_radius=8,
                      fg_color="#1A3A2A", hover_color="#2EBF7A",
                      text_color=ACCENT, font=("Arial",12),
                      command=self.export_lots).pack(side="left", padx=(8,0))
        ctk.CTkButton(br, text="✏  Editar Lote", height=38, corner_radius=8,
                      fg_color="#1A2E3A", hover_color="#1E6A9A",
                      text_color=CYAN, font=("Arial",12),
                      command=self.edit_lot).pack(side="left", padx=(8,0))
        if self.is_admin:
            ctk.CTkButton(br, text="🔄  Ajustar Cantidad", height=38, corner_radius=8,
                          fg_color="#2A1A3A", hover_color="#6B21A8",
                          text_color=PURPLE, font=("Arial",12),
                          command=self.adjust_lot).pack(side="left", padx=(8,0))
            ctk.CTkButton(br, text="🗑  Retirar Lote", height=38, corner_radius=8,
                          fg_color="#2E1A1A", hover_color=DANGER_H,
                          text_color=DANGER, font=("Arial",12),
                          command=self.retire_lot).pack(side="left", padx=(8,0))

        # Tabla
        tc = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=12,
                          border_width=1, border_color=CARD_BORDER)
        tc.pack(fill="both", expand=True, padx=4, pady=(0,4))
        ctk.CTkLabel(tc, text="💡  Selecciona un lote y usa ✏ Editar  |  Doble clic = historial",
                     font=("Arial",10), text_color="#3A3D52").pack(anchor="e", padx=16, pady=(8,2))
        sty = _tree_style("QRY")
        cols = ("ID","Producto","N° Lote","Recibidas","Disponibles",
                "Costo","Vencimiento","Proveedor","Estado")
        self.q_tree = ttk.Treeview(tc, columns=cols, show="headings", height=14, style=sty)
        try:
            self.q_tree.configure(style=self.q_tree["style"])
            self.q_tree.tk.call("ttk::style", "configure", self.q_tree["style"], "-fieldbackground", "#1A1D27")
            self.q_tree.tk.call("ttk::style", "configure", self.q_tree["style"], "-background", "#1A1D27")
            self.q_tree.tk.call("ttk::style", "configure", self.q_tree["style"], "-foreground", "#FFFFFF")
        except Exception:
            pass
        for col, w, anc in [("ID",55,"center"),("Producto",190,"w"),("N° Lote",130,"center"),
                              ("Recibidas",80,"center"),("Disponibles",90,"center"),
                              ("Vencimiento",110,"center"),
                              ("Proveedor",110,"w"),("Estado",80,"center")]:
            self.q_tree.heading(col,text=col); self.q_tree.column(col,width=w,anchor=anc)
        self.q_tree.tag_configure("activo",   foreground=ACCENT)
        self.q_tree.tag_configure("agotado",  foreground=DANGER)
        self.q_tree.tag_configure("vencido",  foreground=DANGER)
        self.q_tree.tag_configure("retirado", foreground=SUBTEXT)
        self.q_tree.bind("<Double-1>", self._lot_detail)
        self.q_tree.pack(fill="both", expand=True, padx=12, pady=(0,12))
        self.search_lots()

    def search_lots(self):
        q_prod   = self.q_product.get().strip()
        q_lot    = self.q_lot.get().strip()
        status   = self.q_status_var.get()
        exp_only = self.q_expiry_only.get()
        conn = create_connection()
        try:
            cur = conn.cursor()
            sql = """SELECT l.id,p.name,l.lot_number,l.quantity_received,
                            l.quantity_available,l.cost,l.expiry_date,
                            IFNULL(s.name,'—'),l.status
                     FROM lots l JOIN products p ON l.product_id=p.id
                     LEFT JOIN suppliers s ON l.supplier_id=s.id WHERE 1=1"""
            params = []
            if q_prod: sql+=" AND (p.name LIKE ? OR CAST(p.id AS CHAR)=?)"; params+=[f"%{q_prod}%",q_prod]
            if q_lot:  sql+=" AND l.lot_number LIKE ?"; params.append(f"%{q_lot}%")
            if status!="Todos": sql+=" AND l.status=?"; params.append(status)
            if exp_only:
                days = config.load()["inventory"].get("expiry_alert_days",30)
                td   = (date.today()+timedelta(days=days)).isoformat()
                sql += " AND l.expiry_date IS NOT NULL AND l.expiry_date<=? AND l.expiry_date>=?"
                params += [td, date.today().isoformat()]
            sql += " ORDER BY l.expiry_date ASC, l.id DESC"
            cur.execute(sql, params)
            rows_lots = cur.fetchall()
        finally:
            conn.close()
        cfg = config.load(); cy = cfg["billing"].get("currency","$")
        today = date.today()
        for i in self.q_tree.get_children(): self.q_tree.delete(i)
        for r in rows_lots:
            st = r[8]
            exp = r[6].isoformat() if hasattr(r[6], 'isoformat') else r[6]
            if r[6] and r[6]<today and st=="activo": st="vencido"
            if r[4]==0 and st=="activo": st="agotado"
            self.q_tree.insert("","end",tags=(st,),
                values=(r[0],r[1],r[2],r[3],r[4],
                        f"{cy}{float(r[5] or 0):,.2f}",exp or "—",r[7],st.upper()))

    def _lot_detail(self, event=None):
        sel = self.q_tree.selection()
        if not sel: return
        lot_id = int(self.q_tree.item(sel[0],"values")[0])
        conn = create_connection(); cur = conn.cursor()
        cur.execute("""SELECT l.*,p.name,IFNULL(s.name,'—')
                       FROM lots l JOIN products p ON l.product_id=p.id
                       LEFT JOIN suppliers s ON l.supplier_id=s.id WHERE l.id=?""", (lot_id,))
        lot = cur.fetchone()
        cur.execute("""SELECT type,quantity,reason,invoice_id,username,timestamp
                       FROM lot_movements WHERE lot_id=? ORDER BY id DESC""", (lot_id,))
        movs = cur.fetchall(); conn.close()
        if not lot: return

        cfg = config.load(); cy = cfg["billing"].get("currency","$")
        win = ctk.CTkToplevel(self.parent)
        win.title(f"Lote {lot[2]} — {lot[12]}")
        win.geometry("780x500"); win.configure(fg_color=BG); win.grab_set()
        ctk.CTkLabel(win, text=f"📦  Lote {lot[2]}  |  {lot[12]}",
                     font=("Arial",16,"bold"), text_color=TEXT).pack(padx=20, pady=(20,4), anchor="w")
        ctk.CTkFrame(win,height=1,fg_color=CARD_BORDER).pack(fill="x",padx=20,pady=(0,10))

        kr = ctk.CTkFrame(win,fg_color="transparent")
        kr.pack(fill="x",padx=20,pady=(0,10))
        kr.columnconfigure((0,1,2,3),weight=1)
        for col,(lbl,val,color) in enumerate([
            ("N° Lote",lot[2],CYAN),("Recibidas",str(lot[3]),TEXT),
            ("Disponibles",str(lot[4]),ACCENT)]):
            f=ctk.CTkFrame(kr,fg_color=CARD,corner_radius=12,border_width=1,border_color=CARD_BORDER)
            f.grid(row=0,column=col,padx=(0 if col==0 else 6,0),sticky="ew")
            ctk.CTkLabel(f,text=lbl,font=("Arial",10),text_color=SUBTEXT).pack(anchor="w",padx=12,pady=(10,0))
            ctk.CTkLabel(f,text=val,font=("Arial",15,"bold"),text_color=color).pack(anchor="w",padx=12,pady=(0,10))

        meta = ctk.CTkFrame(win,fg_color=CARD,corner_radius=10,border_width=1,border_color=CARD_BORDER)
        meta.pack(fill="x",padx=20,pady=(0,10))
        mr = ctk.CTkFrame(meta,fg_color="transparent")
        mr.pack(fill="x",padx=16,pady=10)
        exp6 = lot[6].isoformat() if hasattr(lot[6],'isoformat') else (lot[6] or "—")
        exp7 = lot[7].isoformat() if hasattr(lot[7],'isoformat') else (lot[7] or "—")
        for lbl,val in [("Vencimiento:",exp6),("Recibido:",exp7),
                         ("Proveedor:",lot[12] if len(lot)>12 else "—"),("Estado:",str(lot[10]).upper() if lot[10] else "—")]:
            ctk.CTkLabel(mr,text=f"{lbl}",font=("Arial",10),text_color=SUBTEXT).pack(side="left",padx=(0,4))
            ctk.CTkLabel(mr,text=val,font=("Arial",11,"bold"),text_color=TEXT).pack(side="left",padx=(0,20))

        ctk.CTkLabel(win,text="Movimientos del Lote",font=("Arial",12,"bold"),
                     text_color=SUBTEXT).pack(padx=20,anchor="w",pady=(0,6))
        mc=ctk.CTkFrame(win,fg_color=CARD,corner_radius=12,border_width=1,border_color=CARD_BORDER)
        mc.pack(fill="both",expand=True,padx=20,pady=(0,20))
        sty=_tree_style("DTL")
        cols=("Tipo","Cantidad","Razón","Factura","Usuario","Fecha")
        t=ttk.Treeview(mc,columns=cols,show="headings",style=sty)
        for col,w,anc in [("Tipo",80,"center"),("Cantidad",80,"center"),
                           ("Razón",210,"w"),("Factura",80,"center"),
                           ("Usuario",100,"w"),("Fecha",140,"center")]:
            t.heading(col,text=col); t.column(col,width=w,anchor=anc)
        t.tag_configure("entrada",foreground=ACCENT)
        t.tag_configure("salida", foreground=WARNING)
        t.tag_configure("ajuste", foreground=CYAN)
        t.tag_configure("retiro", foreground=DANGER)
        for m in movs:
            inv=f"#{m[3]:06d}" if m[3] else "—"
            qty=f"+{m[1]}" if m[1]>0 else str(m[1])
            t.insert("","end",tags=(m[0],),values=(m[0].upper(),qty,m[2] or "—",inv,m[4] or "—",m[5]))
        t.pack(fill="both",expand=True,padx=12,pady=12)

    def edit_lot(self):
        """Abre popup para editar todos los campos de un lote seleccionado."""
        sel = self.q_tree.selection()
        if not sel:
            messagebox.showwarning("Sin selección", "Selecciona un lote de la tabla primero.")
            return

        lot_id = int(self.q_tree.item(sel[0], "values")[0])

        # Cargar datos completos del lote
        conn = create_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT l.id, p.name, l.lot_number, l.quantity_received,
                       l.quantity_available, l.cost, l.expiry_date,
                       l.received_date, l.supplier_id, l.notes, l.status,
                       l.product_id
                FROM lots l
                JOIN products p ON l.product_id = p.id
                WHERE l.id = %s
            """, (lot_id,))
            lot = cur.fetchone()
        finally:
            conn.close()

        if not lot:
            messagebox.showerror("Error", "No se pudo cargar el lote.")
            return

        (lid, prod_name, lot_num, qty_recv, qty_avail,
         cost, expiry, recv_date, sup_id, notes, status, product_id) = lot

        # ── Popup de edición ──
        win = ctk.CTkToplevel(self.parent)
        win.title(f"Editar Lote — {lot_num}")
        win.geometry("640x560")
        win.configure(fg_color=BG)
        win.grab_set()
        win.resizable(False, False)

        # Centrar
        win.update_idletasks()
        sx = self.parent.winfo_rootx() + self.parent.winfo_width()  // 2 - 320
        sy = self.parent.winfo_rooty() + self.parent.winfo_height() // 2 - 280
        win.geometry(f"640x560+{sx}+{sy}")

        ctk.CTkLabel(win, text=f"✏  Editar Lote",
                     font=("Arial", 18, "bold"), text_color=TEXT
                     ).pack(padx=20, pady=(20, 2), anchor="w")
        ctk.CTkLabel(win, text=f"Producto: {prod_name}  |  ID Lote: {lid}",
                     font=("Arial", 11), text_color=SUBTEXT
                     ).pack(padx=20, anchor="w")
        ctk.CTkFrame(win, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=20, pady=(10, 14))

        form = ctk.CTkFrame(win, fg_color="transparent")
        form.pack(fill="x", padx=20)
        form.columnconfigure((0, 1), weight=1)

        def _entry(parent, label, row, col, value="", padx=(0, 10)):
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.grid(row=row, column=col, padx=padx, pady=(0, 10), sticky="ew")
            ctk.CTkLabel(f, text=label, font=("Arial", 11),
                         text_color=SUBTEXT).pack(anchor="w")
            ef = ctk.CTkFrame(f, fg_color=INPUT_BG, corner_radius=8,
                               border_width=1, border_color=INPUT_BORDER)
            ef.pack(fill="x", pady=(3, 0))
            e = ctk.CTkEntry(ef, border_width=0, fg_color="transparent",
                              height=38, font=("Arial", 13), text_color=TEXT)
            e.insert(0, str(value) if value is not None else "")
            e.pack(fill="x", padx=8)
            return e

        # Fila 0: N° Lote | Cantidad Disponible
        e_lot_num  = _entry(form, "N° de Lote",          0, 0, lot_num)
        e_qty_avail= _entry(form, "Cantidad Disponible",  0, 1, qty_avail, (10, 0))

        # Fila 1: Costo | Cantidad Recibida (referencia)
        e_cost     = _entry(form, "Costo Unitario",       1, 0, cost)
        e_qty_recv = _entry(form, "Cantidad Recibida",    1, 1, qty_recv, (10, 0))

        # Fila 2: Fecha Vencimiento | Fecha Recepción con botón calendario
        exp_str  = expiry.isoformat()    if hasattr(expiry,    'isoformat') else (expiry    or "")
        recv_str = recv_date.isoformat() if hasattr(recv_date, 'isoformat') else (recv_date or "")

        def _date_entry_popup(parent, label, row, col, value, padx=(0,10)):
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.grid(row=row, column=col, padx=padx, pady=(0,10), sticky="ew")
            ctk.CTkLabel(f, text=label, font=("Arial",11), text_color=SUBTEXT).pack(anchor="w")
            rf = ctk.CTkFrame(f, fg_color="transparent")
            rf.pack(fill="x", pady=(3,0))
            ef = ctk.CTkFrame(rf, fg_color=INPUT_BG, corner_radius=8,
                               border_width=1, border_color=INPUT_BORDER)
            ef.pack(side="left", fill="x", expand=True)
            e = ctk.CTkEntry(ef, border_width=0, fg_color="transparent",
                              height=38, font=("Arial",13), text_color=TEXT)
            e.insert(0, value)
            e.pack(fill="x", padx=8)
            ctk.CTkButton(rf, text="📅", width=44, height=38, corner_radius=8,
                          fg_color=INPUT_BG, hover_color="#1A2E22", text_color=ACCENT,
                          font=("Arial",16),
                          command=lambda: self._open_calendar(e)
                          ).pack(side="left", padx=(6,0))
            return e

        e_expiry   = _date_entry_popup(form, "Fecha Vencimiento", 2, 0, exp_str)
        e_recvdate = _date_entry_popup(form, "Fecha Recepción",   2, 1, recv_str, (10,0))

        # Fila 3: Estado
        sf = ctk.CTkFrame(form, fg_color="transparent")
        sf.grid(row=3, column=0, padx=(0, 10), pady=(0, 10), sticky="ew")
        ctk.CTkLabel(sf, text="Estado", font=("Arial", 11),
                     text_color=SUBTEXT).pack(anchor="w")
        status_var = ctk.StringVar(value=status)
        ctk.CTkOptionMenu(sf, variable=status_var,
                          values=["activo", "agotado", "retirado"],
                          fg_color=INPUT_BG, button_color="#2A2D3A",
                          button_hover_color="#3A3D52", dropdown_fg_color="#1A1D27",
                          dropdown_hover_color="#1A2E22", text_color=TEXT,
                          font=("Arial", 12), height=38, dynamic_resizing=False
                          ).pack(fill="x", pady=(3, 0))

        # Fila 3 col 1: Proveedor
        suppliers = self._load_suppliers()
        sup_names = ["Sin proveedor"] + list(suppliers.keys())
        # Buscar nombre del proveedor actual
        cur_sup_name = "Sin proveedor"
        for sname, sid in suppliers.items():
            if sid == sup_id:
                cur_sup_name = sname
                break
        pf = ctk.CTkFrame(form, fg_color="transparent")
        pf.grid(row=3, column=1, padx=(10, 0), pady=(0, 10), sticky="ew")
        ctk.CTkLabel(pf, text="Proveedor", font=("Arial", 11),
                     text_color=SUBTEXT).pack(anchor="w")
        sup_var = ctk.StringVar(value=cur_sup_name)
        ctk.CTkOptionMenu(pf, variable=sup_var, values=sup_names,
                          fg_color=INPUT_BG, button_color="#2A2D3A",
                          button_hover_color="#3A3D52", dropdown_fg_color="#1A1D27",
                          dropdown_hover_color="#1A2E22", text_color=TEXT,
                          font=("Arial", 12), height=38, dynamic_resizing=False
                          ).pack(fill="x", pady=(3, 0))

        # Fila 4: Notas (ancho completo)
        nf = ctk.CTkFrame(form, fg_color="transparent")
        nf.grid(row=4, column=0, columnspan=2, pady=(0, 10), sticky="ew")
        ctk.CTkLabel(nf, text="Notas / Observaciones", font=("Arial", 11),
                     text_color=SUBTEXT).pack(anchor="w")
        nef = ctk.CTkFrame(nf, fg_color=INPUT_BG, corner_radius=8,
                            border_width=1, border_color=INPUT_BORDER)
        nef.pack(fill="x", pady=(3, 0))
        e_notes = ctk.CTkEntry(nef, border_width=0, fg_color="transparent",
                                height=38, font=("Arial", 13), text_color=TEXT)
        e_notes.insert(0, notes or "")
        e_notes.pack(fill="x", padx=8)

        # ── Botones ──
        ctk.CTkFrame(win, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=20, pady=(4, 12))
        btn_row = ctk.CTkFrame(win, fg_color="transparent")
        btn_row.pack(padx=20, anchor="w")

        def _save():
            try:
                new_lot_num  = e_lot_num.get().strip()
                new_qty_avail= int(e_qty_avail.get().strip())
                new_qty_recv = int(e_qty_recv.get().strip())
                new_cost     = float(e_cost.get().strip() or 0)
                new_expiry   = e_expiry.get().strip() or None
                new_recv     = e_recvdate.get().strip() or None
                new_status   = status_var.get()
                new_sup_id   = suppliers.get(sup_var.get())
                new_notes    = e_notes.get().strip()
            except ValueError as ex:
                messagebox.showerror("Error", f"Dato inválido: {ex}")
                return

            if not new_lot_num:
                messagebox.showerror("Error", "El número de lote no puede estar vacío.")
                return
            if not self._validate_dates(new_expiry, new_recv):
                return

            try:
                conn2 = create_connection()
                cur2  = conn2.cursor()
                cur2.execute("""
                    UPDATE lots SET
                        lot_number        = %s,
                        quantity_available= %s,
                        quantity_received = %s,
                        cost              = %s,
                        expiry_date       = %s,
                        received_date     = %s,
                        status            = %s,
                        supplier_id       = %s,
                        notes             = %s
                    WHERE id = %s
                """, (new_lot_num, new_qty_avail, new_qty_recv,
                      new_cost, new_expiry, new_recv,
                      new_status, new_sup_id, new_notes, lot_id))

                # Recalcular stock del producto
                cur2.execute("""
                    UPDATE products
                    SET stock = (
                        SELECT COALESCE(SUM(quantity_available), 0)
                        FROM lots
                        WHERE product_id = %s AND status = 'activo'
                    )
                    WHERE id = %s
                """, (product_id, product_id))

                # Recalcular costo promedio ponderado del producto
                _sync_product_cost(cur2, product_id)

                conn2.commit()
                conn2.close()

                u = session.current_user
                username = u[1] if isinstance(u, tuple) else str(u)
                audit("LOTE_EDITADO",
                      f"Lote #{lot_id} '{new_lot_num}' | Qty: {qty_avail}→{new_qty_avail} | Estado: {new_status}",
                      module="lotes")

                messagebox.showinfo("✔  Guardado", f"Lote {new_lot_num} actualizado correctamente.")
                win.destroy()
                self.search_lots()

            except Exception as ex:
                messagebox.showerror("Error al guardar", str(ex))

        ctk.CTkButton(btn_row, text="💾 Guardar Cambios",
                      height=42, corner_radius=8, width=180,
                      fg_color=ACCENT, hover_color="#2EBF7A",
                      text_color="#0F1117", font=("Arial", 13, "bold"),
                      command=_save).pack(side="left", padx=(0, 10))
        ctk.CTkButton(btn_row, text="✖ Cancelar",
                      height=42, corner_radius=8, width=120,
                      fg_color=INPUT_BG, hover_color="#2E3148",
                      text_color=SUBTEXT, font=("Arial", 12),
                      command=win.destroy).pack(side="left")

    def adjust_lot(self):
        sel = self.q_tree.selection()
        if not sel: messagebox.showwarning("","Seleccione un lote."); return
        v=self.q_tree.item(sel[0],"values"); lot_id=int(v[0]); curr=int(v[4])
        win=ctk.CTkToplevel(self.parent); win.title("Ajustar Cantidad")
        win.geometry("400x300"); win.configure(fg_color=BG); win.grab_set()
        ctk.CTkLabel(win,text="🔄  Ajuste de Inventario",font=("Arial",16,"bold"),text_color=TEXT).pack(padx=20,pady=(20,4),anchor="w")
        ctk.CTkLabel(win,text=f"Lote: {v[2]}  |  {v[1]}  |  Actual: {curr} uds",font=("Arial",11),text_color=SUBTEXT).pack(padx=20,anchor="w")
        ctk.CTkFrame(win,height=1,fg_color=CARD_BORDER).pack(fill="x",padx=20,pady=(10,14))
        ctk.CTkLabel(win,text="Nueva cantidad disponible:",font=("Arial",12),text_color=TEXT).pack(padx=20,anchor="w")
        ef=ctk.CTkFrame(win,fg_color=INPUT_BG,corner_radius=8,border_width=1,border_color=INPUT_BORDER)
        ef.pack(fill="x",padx=20,pady=(4,10))
        qty_e=ctk.CTkEntry(ef,border_width=0,fg_color="transparent",height=40,font=("Arial",14),text_color=TEXT)
        qty_e.insert(0,str(curr)); qty_e.pack(fill="x",padx=8)
        ctk.CTkLabel(win,text="Razón del ajuste:",font=("Arial",12),text_color=TEXT).pack(padx=20,anchor="w")
        rf=ctk.CTkFrame(win,fg_color=INPUT_BG,corner_radius=8,border_width=1,border_color=INPUT_BORDER)
        rf.pack(fill="x",padx=20,pady=(4,16))
        reason_e=ctk.CTkEntry(rf,border_width=0,fg_color="transparent",height=38,font=("Arial",12),text_color=TEXT)
        reason_e.pack(fill="x",padx=8)
        def _confirm():
            try: new_qty=int(qty_e.get().strip())
            except ValueError: messagebox.showerror("Error","Cantidad inválida."); return
            reason=reason_e.get().strip() or "Ajuste de inventario"
            diff=new_qty-curr
            u=session.current_user; username=u[1] if isinstance(u,tuple) else str(u)
            ts=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn=create_connection(); cur2=conn.cursor()
            cur2.execute("SELECT product_id FROM lots WHERE id=?", (lot_id,))
            pid_row = cur2.fetchone()
            pid = pid_row[0] if pid_row else None
            cur2.execute("UPDATE lots SET quantity_available=?,status=? WHERE id=?",
                         (new_qty,"agotado" if new_qty==0 else "activo",lot_id))
            cur2.execute("""INSERT INTO lot_movements(lot_id,type,quantity,reason,username,timestamp)
                            VALUES(?,?,?,?,?,?)""",(lot_id,"ajuste",diff,reason,username,ts))
            cur2.execute("UPDATE products SET stock=stock+? WHERE id=?",(diff,pid))
            if pid is not None:
                _sync_product_cost(cur2, pid)
            conn.commit(); conn.close()
            audit("LOTE_AJUSTADO",f"Lote #{lot_id} | {curr}→{new_qty} | {reason}",module="lotes")
            win.destroy(); self.search_lots()
        ctk.CTkButton(win,text="✔  Confirmar",height=42,corner_radius=8,
                      fg_color=ACCENT,hover_color="#2EBF7A",text_color="#0F1117",
                      font=("Arial",13,"bold"),command=_confirm).pack(padx=20)

    def retire_lot(self):
        sel=self.q_tree.selection()
        if not sel: messagebox.showwarning("","Seleccione un lote."); return
        v=self.q_tree.item(sel[0],"values"); lot_id=int(v[0]); qty=int(v[4])
        if not messagebox.askyesno("Confirmar",f"Retirar lote '{v[2]}'? Se quitaran {qty} uds del stock."): return
        u=session.current_user; username=u[1] if isinstance(u,tuple) else str(u)
        ts=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn=create_connection(); cur=conn.cursor()
        try:
            cur.execute("SELECT product_id FROM lots WHERE id=?", (lot_id,))
            pid_row = cur.fetchone()
            pid = pid_row[0] if pid_row else None
            cur.execute("UPDATE lots SET status='retirado',quantity_available=0 WHERE id=?",(lot_id,))
            cur.execute("""INSERT INTO lot_movements(lot_id,type,quantity,reason,username,timestamp)
                           VALUES(?,?,?,?,?,?)""",(lot_id,"retiro",-qty,"Lote retirado",username,ts))
            # Recalcular stock desde lotes activos
            cur.execute("""UPDATE products SET stock=(
                SELECT COALESCE(SUM(quantity_available),0)
                FROM lots l2 WHERE l2.product_id=?
                AND l2.status='activo') WHERE id=?""",
                (pid,pid))
            if pid is not None:
                _sync_product_cost(cur, pid)
            conn.commit()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error",str(e))
        finally:
            conn.close()
        audit("LOTE_RETIRADO",f"Lote #{lot_id} '{v[2]}' | {qty} uds",module="lotes")
        self.search_lots()

    def export_lots(self):
        rows=[self.q_tree.item(i,"values") for i in self.q_tree.get_children()]
        if not rows: messagebox.showwarning("","Sin datos."); return
        export_to_excel(rows,["ID","Producto","N° Lote","Recibidas","Disponibles",
                               "Vencimiento","Proveedor","Estado"],f"lotes_{date.today()}.xlsx")

    # ═══════════════════════════════════════════
    # TAB 3 — ALERTAS
    # ═══════════════════════════════════════════
    def _build_alerts(self, parent):
        cfg=config.load(); days=cfg["inventory"].get("expiry_alert_days",30)
        today=date.today().isoformat(); td=(date.today()+timedelta(days=days)).isoformat()
        # Note: MySQL returns date objects; comparisons with isoformat strings work via implicit casting
        conn=create_connection()
        try:
            cur=conn.cursor()
            cur.execute("""SELECT l.id,p.name,l.lot_number,l.quantity_available,l.expiry_date,
                                  DATEDIFF(l.expiry_date, CURDATE())
                           FROM lots l JOIN products p ON l.product_id=p.id
                           WHERE l.status='activo' AND l.expiry_date IS NOT NULL
                           AND l.expiry_date<=? AND l.expiry_date>=?
                           ORDER BY l.expiry_date""",(td,today))
            expiring=cur.fetchall()
            cur.execute("""SELECT l.id,p.name,l.lot_number,l.expiry_date
                           FROM lots l JOIN products p ON l.product_id=p.id
                           WHERE l.status='activo' AND l.expiry_date IS NOT NULL
                           AND l.expiry_date<? ORDER BY l.expiry_date""",(today,))
            expired=cur.fetchall()
            cur.execute("""SELECT l.id,p.name,l.lot_number,l.quantity_available
                           FROM lots l JOIN products p ON l.product_id=p.id
                           WHERE l.status='activo' AND l.quantity_available=0""")
            empty=cur.fetchall()
        finally:
            conn.close()

        kr=ctk.CTkFrame(parent,fg_color="transparent")
        kr.pack(fill="x",padx=4,pady=(8,10)); kr.columnconfigure((0,1,2),weight=1)
        self._kpi(kr,0,f"📅  Vencen ≤ {days} días",str(len(expiring)),WARNING)
        self._kpi(kr,1,"⛔  Ya vencidos",str(len(expired)),DANGER)
        self._kpi(kr,2,"📭  Lotes agotados",str(len(empty)),SUBTEXT)

        scroll=ctk.CTkFrame(parent,fg_color=BG,corner_radius=0)
        scroll.pack(fill="both",expand=True,padx=0,pady=(8,0))

        def _sec(title,rows,cols,widths,color):
            c=ctk.CTkFrame(scroll,fg_color=CARD,corner_radius=12,border_width=1,border_color=CARD_BORDER)
            c.pack(fill="x",padx=4,pady=(0,8))
            hr=ctk.CTkFrame(c,fg_color="transparent"); hr.pack(fill="x",padx=16,pady=(12,2))
            ctk.CTkLabel(hr,text=title,font=("Arial",12,"bold"),text_color=color).pack(side="left")
            ctk.CTkLabel(hr,text=f"({len(rows)})",font=("Arial",11),text_color=SUBTEXT).pack(side="left",padx=8)
            ctk.CTkFrame(c,height=1,fg_color=CARD_BORDER).pack(fill="x",padx=16,pady=(0,6))
            if rows:
                sty=_tree_style(f"A{color[-3:]}")
                t=ttk.Treeview(c,columns=cols,show="headings",height=min(len(rows),5),style=sty)
                for col2,w in zip(cols,widths): t.heading(col2,text=col2); t.column(col2,width=w)
                for r in rows: t.insert("","end",values=r)
                t.pack(fill="x",padx=14,pady=(0,12))
            else:
                ctk.CTkLabel(c,text="✔  Sin alertas",font=("Arial",11),text_color=ACCENT).pack(pady=10)

        _sec(f"⚠  Próximos a vencer (≤{days} días)",
             [(r[0],r[1],r[2],r[3],r[4],f"{r[5]} días") for r in expiring],
             ["ID","Producto","N° Lote","Disponibles","Vencimiento","Días"],
             [60,200,130,80,110,70],WARNING)
        _sec("⛔  Vencidos activos en sistema",
             [(r[0],r[1],r[2],r[3]) for r in expired],
             ["ID","Producto","N° Lote","Venció el"],[60,230,130,120],DANGER)
        _sec("📭  Lotes agotados",
             [(r[0],r[1],r[2],r[3]) for r in empty],
             ["ID","Producto","N° Lote","Disponibles"],[60,260,130,80],SUBTEXT)

        all_rows=(
            [("POR VENCER",r[1],r[2],r[3],r[4],f"{r[5]} días") for r in expiring]+
            [("VENCIDO",r[1],r[2],"—",r[3],"—") for r in expired]+
            [("AGOTADO",r[1],r[2],r[3],"—","—") for r in empty])
        ctk.CTkButton(scroll,text="📊  Exportar Alertas",height=40,corner_radius=8,
                      fg_color="#1A3A2A",hover_color="#2EBF7A",text_color=ACCENT,
                      font=("Arial",12,"bold"),
                      command=lambda:export_to_excel(all_rows,["Tipo","Producto","N° Lote","Disponibles","Vencimiento","Días"],
                                                     f"alertas_lotes_{date.today()}.xlsx")
                      ).pack(padx=4,pady=(0,10))

    # ═══════════════════════════════════════════
    # TAB 4 — MOVIMIENTOS
    # ═══════════════════════════════════════════
    def _build_movements(self, parent):
        fcard=self._card(parent,"📋  Filtros de Movimientos")
        fr=ctk.CTkFrame(fcard,fg_color="transparent"); fr.pack(fill="x",padx=16,pady=(0,4))
        fr.columnconfigure((0,1,2,3),weight=1)
        self.mv_product  =self._lf(fr,"Producto",0)
        self.mv_lot      =self._lf(fr,"N° Lote",1)
        # Fechas con calendario popup
        mdf_wrap = ctk.CTkFrame(fr, fg_color="transparent")
        mdf_wrap.grid(row=0, column=2, padx=(0,10), sticky="ew")
        self.mv_date_from = DateField(mdf_wrap, label="Desde",
                                      value=date.today().replace(day=1).isoformat())
        self.mv_date_from.pack(fill="x")
        mdt_wrap = ctk.CTkFrame(fr, fg_color="transparent")
        mdt_wrap.grid(row=0, column=3, padx=(0,0), sticky="ew")
        self.mv_date_to = DateField(mdt_wrap, label="Hasta",
                                    value=date.today().isoformat())
        self.mv_date_to.pack(fill="x")
        br=ctk.CTkFrame(fcard,fg_color="transparent"); br.pack(fill="x",padx=16,pady=(0,14))
        ctk.CTkButton(br,text="🔍  Buscar",height=38,corner_radius=8,
                      fg_color=ACCENT,hover_color="#2EBF7A",text_color="#0F1117",
                      font=("Arial",12,"bold"),command=self.search_movements).pack(side="left")
        ctk.CTkButton(br,text="📊  Exportar",height=38,corner_radius=8,
                      fg_color="#1A3A2A",hover_color="#2EBF7A",text_color=ACCENT,
                      font=("Arial",12),command=self.export_movements).pack(side="left",padx=(8,0))

        tc=ctk.CTkFrame(parent,fg_color=CARD,corner_radius=12,border_width=1,border_color=CARD_BORDER)
        tc.pack(fill="both",expand=True,padx=4,pady=(0,4))
        sty=_tree_style("MVT")
        cols=("Fecha","Producto","N° Lote","Tipo","Cantidad","Razón","Factura","Usuario")
        self.mv_tree=ttk.Treeview(tc,columns=cols,show="headings",height=18,style=sty)
        try:
            self.mv_tree.configure(style=self.mv_tree["style"])
            self.mv_tree.tk.call("ttk::style", "configure", self.mv_tree["style"], "-fieldbackground", "#1A1D27")
            self.mv_tree.tk.call("ttk::style", "configure", self.mv_tree["style"], "-background", "#1A1D27")
            self.mv_tree.tk.call("ttk::style", "configure", self.mv_tree["style"], "-foreground", "#FFFFFF")
        except Exception:
            pass
        for col,w,anc in [("Fecha",130,"center"),("Producto",180,"w"),("N° Lote",130,"center"),
                           ("Tipo",80,"center"),("Cantidad",80,"center"),
                           ("Razón",180,"w"),("Factura",80,"center"),("Usuario",100,"w")]:
            self.mv_tree.heading(col,text=col); self.mv_tree.column(col,width=w,anchor=anc)
        self.mv_tree.tag_configure("entrada",foreground=ACCENT)
        self.mv_tree.tag_configure("salida", foreground=WARNING)
        self.mv_tree.tag_configure("ajuste", foreground=CYAN)
        self.mv_tree.tag_configure("retiro", foreground=DANGER)
        self.mv_tree.pack(fill="both",expand=True,padx=12,pady=12)
        self._mv_rows=[]; self.search_movements()

    def search_movements(self):
        q_prod=self.mv_product.get().strip(); q_lot=self.mv_lot.get().strip()
        df=self.mv_date_from.get().strip() or "2000-01-01"
        dt=self.mv_date_to.get().strip()   or date.today().isoformat()
        conn=create_connection(); cur=conn.cursor()
        sql="""SELECT m.timestamp,p.name,l.lot_number,m.type,m.quantity,m.reason,m.invoice_id,m.username
               FROM lot_movements m JOIN lots l ON m.lot_id=l.id JOIN products p ON l.product_id=p.id
               WHERE m.timestamp>=? AND m.timestamp<=?"""
        params=[df,dt+" 23:59:59"]
        if q_prod: sql+=" AND (p.name LIKE ? OR CAST(p.id AS CHAR)=?)"; params+=[f"%{q_prod}%",q_prod]
        if q_lot:  sql+=" AND l.lot_number LIKE ?"; params.append(f"%{q_lot}%")
        sql+=" ORDER BY m.timestamp DESC LIMIT 500"
        cur.execute(sql,params); rows=cur.fetchall(); conn.close()
        for i in self.mv_tree.get_children(): self.mv_tree.delete(i)
        self._mv_rows=[]
        for r in rows:
            inv=f"#{r[6]:06d}" if r[6] else "—"
            qty=f"+{r[4]}" if r[4]>0 else str(r[4])
            ts_str = r[0].strftime("%Y-%m-%d %H:%M:%S") if hasattr(r[0],'strftime') else str(r[0])
            self.mv_tree.insert("","end",tags=(r[3],),
                values=(ts_str,r[1],r[2],r[3].upper(),qty,r[5] or "—",inv,r[7] or "—"))
            self._mv_rows.append(r)

    def export_movements(self):
        if not self._mv_rows: messagebox.showwarning("","Sin datos."); return
        rows=[(r[0].strftime("%Y-%m-%d %H:%M:%S") if hasattr(r[0],'strftime') else str(r[0]),
               r[1],r[2],r[3].upper(),f"+{r[4]}" if r[4]>0 else str(r[4]),
               r[5] or "—",f"#{r[6]:06d}" if r[6] else "—",r[7] or "—") for r in self._mv_rows]
        export_to_excel(rows,["Fecha","Producto","N° Lote","Tipo","Cantidad","Razón","Factura","Usuario"],
                        f"movimientos_lotes_{date.today()}.xlsx")

