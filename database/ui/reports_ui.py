import os
import customtkinter as ctk
from ui.date_field import DateField
from tkinter import ttk, messagebox
from datetime import date, timedelta
from database.connection import create_connection
from exports.excel_exporter import export_to_excel
from auth import session
import config

BG="#0F1117"; CARD="#1A1D27"; CARD_BORDER="#252836"
ACCENT="#3DD68C"; CYAN="#22D3EE"; TEXT="#FFFFFF"; SUBTEXT="#8B8FA8"
DANGER="#EF4444"; WARNING="#FFA94D"; PURPLE="#C084FC"
INPUT_BG="#23263A"; INPUT_BORDER="#2E3148"



def _fmt_date(v):
    """Convierte fecha MySQL (datetime/date obj o string) a YYYY-MM-DD."""
    if v is None: return "—"
    if hasattr(v, "strftime"): return v.strftime("%Y-%m-%d")
    s = str(v); return s[:10] if len(s) >= 10 else s

def _fmt_time(v):
    """Extrae HH:MM de fecha MySQL (datetime obj o string)."""
    if v is None: return "—"
    if hasattr(v, "strftime"): return v.strftime("%H:%M")
    s = str(v); return s[11:16] if len(s) >= 16 else "—"


class ReportsUI:
    def __init__(self, parent):
        self.parent = parent
        self.is_admin = session.current_role in ("admin","Administrador")
        container = ctk.CTkFrame(parent, fg_color=BG, corner_radius=0)
        container.pack(fill="both", expand=True)

        hdr = ctk.CTkFrame(container, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(20,0))
        ctk.CTkLabel(hdr, text="📊  Reportes", font=("Arial",22,"bold"), text_color=TEXT).pack(side="left")
        ctk.CTkFrame(container, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=20, pady=(10,16))

        # ── Filtro de fechas global ──
        date_card = ctk.CTkFrame(container, fg_color=CARD, corner_radius=12,
                                  border_width=1, border_color=CARD_BORDER)
        date_card.pack(fill="x", padx=20, pady=(0,12))
        ctk.CTkLabel(date_card, text="Rango de Fechas",
                     font=("Arial",12,"bold"), text_color=SUBTEXT).pack(anchor="w", padx=16, pady=(12,2))
        ctk.CTkFrame(date_card, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=16, pady=(0,10))

        dr = ctk.CTkFrame(date_card, fg_color="transparent")
        dr.pack(fill="x", padx=16, pady=(0,12))
        dr.columnconfigure((0,1), weight=1)

        self.date_from = self._lf(dr, "Desde", 0)
        self.date_to   = self._lf(dr, "Hasta",  1)

        today = date.today()
        self.date_from.insert(0, today.replace(day=1).strftime("%Y-%m-%d"))
        self.date_to.insert(0, today.strftime("%Y-%m-%d"))

        qr = ctk.CTkFrame(date_card, fg_color="transparent")
        qr.pack(fill="x", padx=16, pady=(0,12))
        for label, fn in [
            ("Hoy",            lambda: self._range(0,0)),
            ("Ultimos 7 dias", lambda: self._range(7,0)),
            ("Ultimos 30 dias",lambda: self._range(30,0)),
            ("Ultimos 90 dias",lambda: self._range(90,0)),
            ("Este ano",       lambda: self._range(-2,0)),
        ]:
            ctk.CTkButton(qr, text=label, height=30, width=90, corner_radius=6,
                          fg_color=INPUT_BG, hover_color="#1A2E22",
                          text_color=SUBTEXT, font=("Arial",11), command=fn
                          ).pack(side="left", padx=(0,6))

        # ── Botones de reportes ──
        btn_card = ctk.CTkFrame(container, fg_color=CARD, corner_radius=12,
                                 border_width=1, border_color=CARD_BORDER)
        btn_card.pack(fill="x", padx=20, pady=(0,12))
        ctk.CTkLabel(btn_card, text="Generar Reporte",
                     font=("Arial",12,"bold"), text_color=SUBTEXT).pack(anchor="w", padx=16, pady=(12,2))
        ctk.CTkFrame(btn_card, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=16, pady=(0,12))

        btn_row = ctk.CTkFrame(btn_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0,16))

        btns = [
            ("🔍  Ver Detalle",      "#1A2E3A","#1E6A9A", CYAN,    self.show_details,      True),
            ("🏆  Top 10 Vendidos",  "#1A3A2A","#2EBF7A", ACCENT,  self.top10_report,      True),
            ("⚠  Alertas Operativas","#2A1A0A","#8A5A0A", WARNING, self.alerts_report,     True),
            ("💰  Financiero",       "#1A3A1A","#2EBF7A", ACCENT,  self.financial_report,  self.is_admin),
            ("📦  Valorización",     "#2A1A2A","#8A2A8A", PURPLE,  self.valuation_report,  self.is_admin),
            ("📅  Por Fecha",        "#2A2A1A","#8A8A0A", WARNING, self.sales_by_date,     self.is_admin),
            ("👤  Por Empleado",     "#1A2A3A","#1E6A9A", CYAN,    self.sales_by_employee, self.is_admin),
        ]

        for text, fg, hov, tc, cmd, visible in btns:
            if visible:
                ctk.CTkButton(btn_row, text=text, height=40, corner_radius=8,
                              fg_color=fg, hover_color=hov, text_color=tc,
                              font=("Arial",12,"bold"), command=cmd
                              ).pack(side="left", padx=(0,8))

        # ── Tabla de historial ──
        tc = ctk.CTkFrame(container, fg_color=CARD, corner_radius=12,
                          border_width=1, border_color=CARD_BORDER)
        tc.pack(fill="both", expand=True, padx=20, pady=(0,20))
        ctk.CTkLabel(tc, text="Historial de Facturas",
                     font=("Arial",12,"bold"), text_color=SUBTEXT).pack(anchor="w", padx=16, pady=(14,2))
        ctk.CTkFrame(tc, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=16, pady=(0,8))

        style = ttk.Style(); style.theme_use("clam")
        style.configure("REP.Treeview", background="#1A1D27", foreground="#FFFFFF",
                         fieldbackground="#1A1D27", borderwidth=0, font=("Arial",12), rowheight=30)
        style.configure("REP.Treeview.Heading", background="#1E2130",
                         foreground="#8B8FA8", font=("Arial",11,"bold"), borderwidth=0)
        style.map("REP.Treeview", background=[("selected", "#1A2E22"), ("!selected", "#1A1D27")], foreground=[("selected", "#3DD68C"), ("!selected", "#FFFFFF")])

        cols = ("Factura","Cliente","Total","Fecha","Método","Empleado")
        self.tree = ttk.Treeview(tc, columns=cols, show="headings", height=14, style="REP.Treeview")
        try:
            self.tree.configure(style=self.tree["style"])
            self.tree.tk.call("ttk::style", "configure", self.tree["style"], "-fieldbackground", "#1A1D27")
            self.tree.tk.call("ttk::style", "configure", self.tree["style"], "-background", "#1A1D27")
            self.tree.tk.call("ttk::style", "configure", self.tree["style"], "-foreground", "#FFFFFF")
        except Exception:
            pass
        for col, w, anc in [("Factura",80,"center"),("Cliente",220,"w"),
                              ("Total",110,"e"),("Fecha",100,"center"),
                              ("Método",130,"w"),("Empleado",130,"w")]:
            self.tree.heading(col,text=col); self.tree.column(col,width=w,anchor=anc)
        self.tree.pack(fill="both", expand=True, padx=16, pady=(0,14))
        self.load_invoices()

    def _lf(self, parent, label, col):
        """Campo de fecha con calendario popup."""
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.grid(row=0, column=col, padx=(0,10), sticky="ew")
        field = DateField(wrap, label=label,
                          on_change=lambda _: self.load_invoices())
        field.pack(fill="x")
        return field

    def _open_calendar(self, entry_widget):
        """Mantenido por compatibilidad — DateField lo maneja internamente."""
        pass

    def _range(self, days, _=0):
        today = date.today()
        if days == 0:    from_d = to_d = today
        elif days == -2: from_d = today.replace(month=1,day=1); to_d = today
        else:            from_d = today - timedelta(days=days); to_d = today
        for field, val in [(self.date_from, from_d),(self.date_to, to_d)]:
            dstr = val.strftime("%Y-%m-%d")
            if hasattr(field,"set"): field.set(dstr)
            else: field.delete(0,"end"); field.insert(0, dstr)
        self.load_invoices()

    def _get_range(self):
        df = self.date_from.get().strip() or "2000-01-01"
        dt = self.date_to.get().strip()   or date.today().isoformat()
        return df, dt + " 23:59:59"

    def get_connection(self): return create_connection()

    def load_invoices(self):
        df, dt = self._get_range()
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""SELECT id,customer_name,total,purchase_date,
                                  IFNULL(payment_method,'—'),IFNULL(employee,'—')
                           FROM invoices WHERE purchase_date>=? AND purchase_date<=?
                           ORDER BY id DESC""", (df, dt))
            cfg = config.load(); cy = cfg["billing"].get("currency","$")
            for r in cur.fetchall():
                self.tree.insert("","end", values=(
                    f"#{r[0]:06d}", r[1], f"{cy} {r[2]:,.2f}",
                    _fmt_date(r[3]), r[4], r[5]))
        finally:
            conn.close()

    def show_details(self):
        sel = self.tree.selection()
        if not sel: messagebox.showwarning("Advertencia","Seleccione una factura."); return
        inv_id = int(self.tree.item(sel[0],"values")[0].replace("#",""))
        self._detail_window(inv_id)

    def _detail_window(self, inv_id):
        win = ctk.CTkToplevel(self.parent)
        win.title(f"Factura #{inv_id:06d}")
        win.geometry("700x420"); win.configure(fg_color=BG); win.grab_set()
        ctk.CTkLabel(win, text=f"🧾  Detalle — Factura #{inv_id:06d}",
                     font=("Arial",18,"bold"), text_color=TEXT).pack(padx=20, pady=(20,4), anchor="w")
        ctk.CTkFrame(win, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=20, pady=(0,12))
        card = ctk.CTkFrame(win, fg_color=CARD, corner_radius=12,
                             border_width=1, border_color=CARD_BORDER)
        card.pack(fill="both", expand=True, padx=20, pady=(0,20))
        style = ttk.Style()
        style.configure("DT.Treeview", background="#1A1D27", foreground="#FFFFFF",
                         fieldbackground="#1A1D27", borderwidth=0, font=("Arial",12), rowheight=30)
        style.configure("DT.Treeview.Heading", background="#1E2130",
                         foreground="#8B8FA8", font=("Arial",11,"bold"), borderwidth=0)
        style.map("DT.Treeview", background=[("selected", "#1A2E22"), ("!selected", "#1A1D27")], foreground=[("selected", "#3DD68C"), ("!selected", "#FFFFFF")])
        cols = ("Producto","Cantidad","Precio","Total")
        t = ttk.Treeview(card, columns=cols, show="headings", style="DT.Treeview")
        for col, w, anc in [("Producto",280,"w"),("Cantidad",90,"center"),
                              ("Precio",130,"e"),("Total",130,"e")]:
            t.heading(col,text=col); t.column(col,width=w,anchor=anc)
        t.pack(fill="both", expand=True, padx=14, pady=14)
        cfg = config.load(); cy = cfg["billing"].get("currency","$")
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute("SELECT product_name,quantity,price,total FROM invoice_items WHERE invoice_id=?", (inv_id,))
        for item in cur.fetchall():
            t.insert("","end", values=(item[0],item[1],f"{cy} {item[2]:,.2f}",f"{cy} {item[3]:,.2f}"))
        conn.close()

    # ── TOP 10 MÁS VENDIDOS ──
    def top10_report(self):
        df, dt = self._get_range()
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""SELECT ii.product_name, SUM(ii.quantity) q, SUM(ii.total) t
                           FROM invoice_items ii JOIN invoices i ON ii.invoice_id=i.id
                           WHERE DATE(i.purchase_date)>=? AND DATE(i.purchase_date)<=?
                           GROUP BY ii.product_name ORDER BY q DESC LIMIT 10""", (df, dt))
            rows = cur.fetchall()
        finally:
            conn.close()
        cfg = config.load(); cy = cfg["billing"].get("currency","$")
        self._table_window("🏆  Top 10 Medicamentos Más Vendidos",
            ["#","Medicamento","Unidades Vendidas","Total Generado"],
            [(i+1, r[0], r[1], f"{cy} {r[2]:,.2f}") for i, r in enumerate(rows)],
            [40, 280, 130, 130])

    # ── ALERTAS OPERATIVAS ──
    def alerts_report(self):
        cfg   = config.load()
        conn  = self.get_connection()
        try:
            cur = conn.cursor()

            # Agotados
            cur.execute("SELECT name,active_ingredient,stock,min_stock FROM products WHERE stock=0")
            out_of_stock = cur.fetchall()

            # Stock bajo (usando min_stock por producto)
            cur.execute("SELECT name,active_ingredient,stock,min_stock FROM products WHERE stock>0 AND stock<=min_stock")
            low_stock = cur.fetchall()

            # Por vencer
            days  = cfg["inventory"].get("expiry_alert_days", 30)
            today = date.today().isoformat()
            cur.execute("""SELECT name,active_ingredient,stock,expiry_date FROM products
                           WHERE expiry_date IS NOT NULL AND expiry_date!=''
                           AND expiry_date <= DATE_ADD(?, INTERVAL ? DAY)
                           AND expiry_date >= ? ORDER BY expiry_date""",
                        (today, days, today))
            expiring = cur.fetchall()

            # Vencidos
            cur.execute("""SELECT name,active_ingredient,stock,expiry_date FROM products
                           WHERE expiry_date<? AND expiry_date!='' ORDER BY expiry_date""", (today,))
            expired = cur.fetchall()
        finally:
            conn.close()

        win = ctk.CTkToplevel(self.parent)
        win.title("Alertas Operativas")
        win.geometry("780x600"); win.configure(fg_color=BG); win.grab_set()

        ctk.CTkLabel(win, text="⚠  Reporte de Alertas Operativas",
                     font=("Arial",18,"bold"), text_color=TEXT).pack(padx=20, pady=(20,4), anchor="w")
        ctk.CTkFrame(win, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=20, pady=(0,10))

        scroll = ctk.CTkScrollableFrame(win, fg_color=BG, corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=0)

        def _section(title, rows, color, cols, widths):
            card = ctk.CTkFrame(scroll, fg_color=CARD, corner_radius=12,
                                 border_width=1, border_color=CARD_BORDER)
            card.pack(fill="x", padx=20, pady=(0,10))
            hrow = ctk.CTkFrame(card, fg_color="transparent")
            hrow.pack(fill="x", padx=14, pady=(12,2))
            ctk.CTkLabel(hrow, text=title, font=("Arial",12,"bold"), text_color=color).pack(side="left")
            ctk.CTkLabel(hrow, text=f"({len(rows)} productos)",
                         font=("Arial",11), text_color=SUBTEXT).pack(side="left", padx=8)
            ctk.CTkFrame(card, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=14, pady=(0,6))

            if rows:
                style = ttk.Style()
                style.configure("ALR.Treeview", background="#1A1D27", foreground="#FFFFFF",
                                 fieldbackground="#1A1D27", borderwidth=0, font=("Arial",11), rowheight=28)
                style.configure("ALR.Treeview.Heading", background="#1E2130",
                                 foreground="#8B8FA8", font=("Arial",10,"bold"), borderwidth=0)
                style.map("ALR.Treeview", background=[("selected", "#1A2E22"), ("!selected", "#1A1D27")], foreground=[("selected", "#3DD68C"), ("!selected", "#FFFFFF")])
                t = ttk.Treeview(card, columns=cols, show="headings",
                                  height=min(len(rows),5), style="ALR.Treeview")
                for col, w in zip(cols, widths):
                    t.heading(col,text=col); t.column(col,width=w)
                for r in rows: t.insert("","end", values=r)
                t.pack(fill="x", padx=14, pady=(0,12))
            else:
                ctk.CTkLabel(card, text="✔  Sin alertas en esta categoría",
                             font=("Arial",11), text_color=ACCENT).pack(pady=10)

        _section(f"⛔  Productos Agotados",
                 [(r[0],r[1] or "—",r[2],r[3]) for r in out_of_stock],
                 DANGER, ["Nombre","Principio Activo","Stock","Stock Mín"], [200,150,80,80])

        _section(f"⚠  Stock Bajo (bajo mínimo por producto)",
                 [(r[0],r[1] or "—",r[2],r[3]) for r in low_stock],
                 WARNING, ["Nombre","Principio Activo","Stock Actual","Stock Mín"], [200,150,100,80])

        _section(f"📅  Próximos a Vencer (<{days} días)",
                 [(r[0],r[1] or "—",r[2],r[3]) for r in expiring],
                 WARNING, ["Nombre","Principio Activo","Stock","Vencimiento"], [200,150,80,100])

        _section("🗑  Productos Vencidos",
                 [(r[0],r[1] or "—",r[2],r[3]) for r in expired],
                 DANGER, ["Nombre","Principio Activo","Stock","Venció"], [200,150,80,100])

        # Exportar
        all_rows = (
            [("AGOTADO", r[0], r[1] or "—", r[2], r[3], "") for r in out_of_stock] +
            [("STOCK BAJO", r[0], r[1] or "—", r[2], r[3], "") for r in low_stock] +
            [("POR VENCER", r[0], r[1] or "—", r[2], "", r[3]) for r in expiring] +
            [("VENCIDO", r[0], r[1] or "—", r[2], "", r[3]) for r in expired]
        )
        ctk.CTkButton(win, text="📊  Exportar Excel", height=38, corner_radius=8,
                      fg_color="#1A3A2A", hover_color="#2EBF7A", text_color=ACCENT,
                      font=("Arial",12,"bold"),
                      command=lambda: export_to_excel(all_rows,
                          ["Tipo","Nombre","Principio Activo","Stock","Stock Mín","Vencimiento"],
                          f"alertas_operativas_{date.today()}.xlsx")
                      ).pack(padx=20, pady=(0,16))

    # ── VALORIZACIÓN DE INVENTARIO ──
    def valuation_report(self):
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""SELECT name, active_ingredient, stock, cost, price,
                                  (stock*cost) val_costo, (stock*price) val_venta,
                                  (stock*(price-cost)) margen
                           FROM products WHERE stock>0 ORDER BY val_venta DESC""")
            rows = cur.fetchall()
        finally:
            conn.close()
        cfg = config.load(); cy = cfg["billing"].get("currency","$")

        total_costo = sum(float(r[5] or 0) for r in rows)
        total_venta = sum(float(r[6] or 0) for r in rows)
        total_margen= sum(float(r[7] or 0) for r in rows)

        win = ctk.CTkToplevel(self.parent)
        win.title("Valorización de Inventario")
        win.geometry("900x580"); win.configure(fg_color=BG); win.grab_set()

        ctk.CTkLabel(win, text="📦  Valorización de Inventario",
                     font=("Arial",18,"bold"), text_color=TEXT).pack(padx=20, pady=(20,4), anchor="w")

        # KPIs
        kpi_row = ctk.CTkFrame(win, fg_color="transparent")
        kpi_row.pack(fill="x", padx=20, pady=(4,12))
        kpi_row.columnconfigure((0,1,2), weight=1)
        for col, lbl, val, color in [
            (0,"💰 Valor al Costo",   f"{cy} {total_costo:,.2f}", WARNING),
            (1,"💵 Valor de Venta",   f"{cy} {total_venta:,.2f}", ACCENT),
            (2,"📈 Margen Potencial", f"{cy} {total_margen:,.2f}", CYAN),
        ]:
            f = ctk.CTkFrame(kpi_row, fg_color=CARD, corner_radius=12,
                              border_width=1, border_color=CARD_BORDER)
            f.grid(row=0, column=col, padx=(0 if col==0 else 8,0), sticky="ew")
            ctk.CTkLabel(f, text=lbl, font=("Arial",11), text_color=SUBTEXT).pack(anchor="w", padx=14, pady=(10,0))
            ctk.CTkLabel(f, text=val, font=("Arial",18,"bold"), text_color=color).pack(anchor="w", padx=14, pady=(0,10))

        ctk.CTkFrame(win, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=20, pady=(0,8))

        card = ctk.CTkFrame(win, fg_color=CARD, corner_radius=12,
                             border_width=1, border_color=CARD_BORDER)
        card.pack(fill="both", expand=True, padx=20, pady=(0,16))

        style = ttk.Style()
        style.configure("VAL.Treeview", background="#1A1D27", foreground="#FFFFFF",
                         fieldbackground="#1A1D27", borderwidth=0, font=("Arial",11), rowheight=28)
        style.configure("VAL.Treeview.Heading", background="#1E2130",
                         foreground="#8B8FA8", font=("Arial",10,"bold"), borderwidth=0)
        style.map("VAL.Treeview", background=[("selected", "#1A2E22"), ("!selected", "#1A1D27")], foreground=[("selected", "#3DD68C"), ("!selected", "#FFFFFF")])

        cols = ("Nombre","Principio Activo","Stock","Costo","Precio","Val.Costo","Val.Venta","Margen")
        t = ttk.Treeview(card, columns=cols, show="headings", height=16, style="VAL.Treeview")
        for col, w, anc in [("Nombre",180,"w"),("Principio Activo",130,"w"),
                              ("Stock",60,"center"),("Costo",90,"e"),("Precio",90,"e"),
                              ("Val.Costo",100,"e"),("Val.Venta",100,"e"),("Margen",100,"e")]:
            t.heading(col,text=col); t.column(col,width=w,anchor=anc)
        for r in rows:
            t.insert("","end", values=(
                r[0], r[1] or "—", r[2],
                f"{cy}{float(r[3] or 0):,.2f}", f"{cy}{float(r[4] or 0):,.2f}",
                f"{cy}{float(r[5] or 0):,.2f}", f"{cy}{float(r[6] or 0):,.2f}", f"{cy}{float(r[7] or 0):,.2f}"))
        t.pack(fill="both", expand=True, padx=14, pady=14)

        ctk.CTkButton(win, text="📊 Exportar Excel", height=38, corner_radius=8,
                      fg_color="#1A3A2A", hover_color="#2EBF7A", text_color=ACCENT,
                      font=("Arial",12,"bold"),
                      command=lambda: export_to_excel(
                          [(r[0],r[1] or "—",r[2],f"{cy}{r[3]:,.2f}",f"{cy}{r[4]:,.2f}",
                            f"{cy}{r[5]:,.2f}",f"{cy}{r[6]:,.2f}",f"{cy}{r[7]:,.2f}") for r in rows],
                          ["Nombre","Principio Activo","Stock","Costo","Precio",
                           "Val.Costo","Val.Venta","Margen"],
                          f"valorizacion_{date.today()}.xlsx")
                      ).pack(padx=20, pady=(0,16))

    # ── FINANCIERO ──
    def financial_report(self):
        df, dt = self._get_range()
        conn = create_connection()
        try:
            import pandas as pd
            q = f"""SELECT ii.product_name, ii.quantity, p.price, p.cost,
                           (p.price-p.cost)*ii.quantity profit
                    FROM invoice_items ii
                    JOIN products p ON ii.product_name=p.name
                    JOIN invoices i ON ii.invoice_id=i.id
                    WHERE i.purchase_date>='{df}' AND i.purchase_date<='{dt}'"""
            df_data = pd.read_sql_query(q, conn._conn)
            total_profit = df_data["profit"].sum() if not df_data.empty else 0
        except Exception:
            total_profit = 0
        finally:
            conn.close()
        cfg = config.load(); cy = cfg["billing"].get("currency","$")
        win = ctk.CTkToplevel(self.parent)
        win.title("Reporte Financiero"); win.geometry("420x200")
        win.configure(fg_color=BG); win.grab_set()
        ctk.CTkLabel(win, text="💰  Reporte Financiero",
                     font=("Arial",18,"bold"), text_color=TEXT).pack(padx=24, pady=(24,8), anchor="w")
        card = ctk.CTkFrame(win, fg_color=CARD, corner_radius=12,
                             border_width=1, border_color=CARD_BORDER)
        card.pack(fill="x", padx=24)
        ctk.CTkLabel(card, text="Ganancia Total Estimada",
                     font=("Arial",12), text_color=SUBTEXT).pack(anchor="w", padx=16, pady=(16,2))
        ctk.CTkLabel(card, text=f"{cy} {total_profit:,.2f}",
                     font=("Arial",28,"bold"), text_color=ACCENT).pack(anchor="w", padx=16, pady=(0,16))

    # ── POR FECHA ──
    def sales_by_date(self):
        df, dt = self._get_range()
        conn = create_connection()
        try:
            import pandas as pd
            data = pd.read_sql_query(
                f"""SELECT id,customer_name,total,purchase_date,
                          IFNULL(employee,'—') employee
                   FROM invoices WHERE purchase_date>='{df}' AND purchase_date<='{dt}'
                   ORDER BY purchase_date DESC""",
                conn._conn)
            path = f"ventas_{date.today()}.xlsx"
            data.to_excel(path, index=False)
            from exports.excel_exporter import _open_file
            _open_file(path)
            messagebox.showinfo("Exportado", f"Archivo: {os.path.abspath(path)}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            conn.close()

    # ── POR EMPLEADO ──
    def sales_by_employee(self):
        df, dt = self._get_range()
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""SELECT IFNULL(employee,'Sin asignar'), COUNT(*), SUM(total)
                           FROM invoices WHERE purchase_date>=? AND purchase_date<=?
                           GROUP BY employee ORDER BY SUM(total) DESC""", (df, dt))
            data = cur.fetchall()
        finally:
            conn.close()
        cfg = config.load(); cy = cfg["billing"].get("currency","$")
        self._table_window("👤  Ventas por Empleado",
            ["Empleado","Facturas","Total Ventas"],
            [(r[0], r[1], f"{cy} {r[2]:,.2f}") for r in data],
            [220, 100, 160])

    def _table_window(self, title, cols, rows, widths):
        win = ctk.CTkToplevel(self.parent)
        win.title(title); win.geometry("700x420")
        win.configure(fg_color=BG); win.grab_set()
        ctk.CTkLabel(win, text=title, font=("Arial",16,"bold"),
                     text_color=TEXT).pack(padx=20, pady=(20,4), anchor="w")
        ctk.CTkFrame(win, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=20, pady=(0,12))
        card = ctk.CTkFrame(win, fg_color=CARD, corner_radius=12,
                             border_width=1, border_color=CARD_BORDER)
        card.pack(fill="both", expand=True, padx=20, pady=(0,16))
        style = ttk.Style()
        style.configure("TBL.Treeview", background="#1A1D27", foreground="#FFFFFF",
                         fieldbackground="#1A1D27", borderwidth=0, font=("Arial",12), rowheight=30)
        style.configure("TBL.Treeview.Heading", background="#1E2130",
                         foreground="#8B8FA8", font=("Arial",11,"bold"), borderwidth=0)
        style.map("TBL.Treeview", background=[("selected", "#1A2E22"), ("!selected", "#1A1D27")], foreground=[("selected", "#3DD68C"), ("!selected", "#FFFFFF")])
        t = ttk.Treeview(card, columns=cols, show="headings", style="TBL.Treeview")
        for col, w in zip(cols, widths):
            t.heading(col,text=col); t.column(col,width=w)
        for r in rows: t.insert("","end", values=r)
        if not rows: t.insert("","end", values=["Sin datos"]+["—"]*(len(cols)-1))
        t.pack(fill="both", expand=True, padx=14, pady=14)
        ctk.CTkButton(win, text="📊 Exportar", height=38, corner_radius=8,
                      fg_color="#1A3A2A", hover_color="#2EBF7A", text_color=ACCENT,
                      font=("Arial",12,"bold"),
                      command=lambda: export_to_excel(rows, cols, "reporte.xlsx")
                      ).pack(padx=20, pady=(0,16))
