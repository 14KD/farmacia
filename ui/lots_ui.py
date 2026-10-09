from ui.date_field import DateField
"""
lots_ui.py — Consulta, alertas y movimientos de lotes farmacéuticos.
El alta de mercancía (registrar compra / entrada de lotes) vive ahora en
ui/purchases_ui.py (módulo Compras) — ver database/purchases.py.
Diseño consistente con el resto del sistema.
"""
import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime, date, timedelta
from database.connection import create_connection
from database.fefo import sync_product_cost as _sync_product_cost
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
        # Altura fija y generosa (en vez de recalcularla contra el tamaño de
        # ventana con after()/<Configure>): esa sincronización dinámica causó
        # crashes nativos (segfault) reproducibles al navegar a Lotes, y aun
        # ajustada quedaba con margen impreciso. Con una altura fija, ninguna
        # pestaña necesita su propio scroll interno y el ÚNICO scroll de
        # toda la página lo maneja el CTkScrollableFrame del dashboard
        # (main_frame) — igual que el resto de las secciones de la app.
        self.tabs = ctk.CTkTabview(
            container,
            height=1150,
            fg_color=CARD, corner_radius=12,
            segmented_button_fg_color="#1E2130",
            segmented_button_selected_color=ACCENT,
            segmented_button_selected_hover_color="#2EBF7A",
            segmented_button_unselected_color="#1E2130",
            segmented_button_unselected_hover_color="#252836",
            text_color=TEXT, text_color_disabled=SUBTEXT
        )
        self.tabs.pack(fill="both", expand=True, padx=20, pady=(0,20))
        for tab in ["🔍  Consulta","⚠  Alertas","📋  Movimientos"]:
            self.tabs.add(tab)

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

    # ═══════════════════════════════════════════
    # TAB 1 — CONSULTA
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
                              ("Costo",90,"e"),
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
    # TAB 2 — ALERTAS
    # ═══════════════════════════════════════════
    def _build_alerts(self, parent):
        cfg=config.load(); days=cfg["inventory"].get("expiry_alert_days",30)
        today=date.today().isoformat(); td=(date.today()+timedelta(days=days)).isoformat()
        # Note: MariaDB returns date objects; comparisons with isoformat strings work via implicit casting
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
    # TAB 3 — MOVIMIENTOS
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

