"""
sales_history_ui.py — Historial y auditoría de ventas.
Busca y filtra facturas emitidas con rango de fechas, cliente y cajero.
"""
import customtkinter as ctk
from ui.date_field import DateField
from ui.live_search import LiveSearch
from tkinter import ttk, messagebox
from datetime import date, timedelta
from database.connection import create_connection
from exports.excel_exporter import export_to_excel
import config

BG="#0F1117"; CARD="#1A1D27"; CARD_BORDER="#252836"
ACCENT="#3DD68C"; CYAN="#22D3EE"; TEXT="#FFFFFF"; SUBTEXT="#8B8FA8"
DANGER="#EF4444"; WARNING="#FFA94D"; INPUT_BG="#23263A"; INPUT_BORDER="#2E3148"



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


class SalesHistoryUI:
    def __init__(self, parent):
        self.parent = parent
        container = ctk.CTkFrame(parent, fg_color=BG, corner_radius=0)
        container.pack(fill="both", expand=True)

        # ── Encabezado ──
        hdr = ctk.CTkFrame(container, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(20, 0))
        ctk.CTkLabel(hdr, text="🗂  Historial de Ventas",
                     font=("Arial", 22, "bold"), text_color=TEXT).pack(side="left")
        ctk.CTkFrame(container, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=20, pady=(10, 16))

        # ── Filtros ──
        filt = ctk.CTkFrame(container, fg_color=CARD, corner_radius=12,
                             border_width=1, border_color=CARD_BORDER)
        filt.pack(fill="x", padx=20, pady=(0, 10))
        ctk.CTkLabel(filt, text="Filtros de Búsqueda",
                     font=("Arial", 12, "bold"), text_color=SUBTEXT).pack(anchor="w", padx=16, pady=(12,2))
        ctk.CTkFrame(filt, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=16, pady=(0,10))

        fr = ctk.CTkFrame(filt, fg_color="transparent")
        fr.pack(fill="x", padx=16, pady=(0, 10))
        fr.columnconfigure((0,1,2,3,4), weight=1)

        # Desde
        df_wrap = ctk.CTkFrame(fr, fg_color="transparent")
        df_wrap.grid(row=0, column=0, padx=(0,10), sticky="ew")
        self.date_from = DateField(df_wrap, label="Desde")
        self.date_from.pack(fill="x")
        # Hasta
        dt_wrap = ctk.CTkFrame(fr, fg_color="transparent")
        dt_wrap.grid(row=0, column=1, padx=(0,10), sticky="ew")
        self.date_to = DateField(dt_wrap, label="Hasta")
        self.date_to.pack(fill="x")
        # Cliente con sugerencias predictivas
        cw = ctk.CTkFrame(fr, fg_color="transparent")
        cw.grid(row=0, column=2, padx=(0,8), sticky="ew")
        ctk.CTkLabel(cw, text="Cliente", font=("Arial",11), text_color=SUBTEXT).pack(anchor="w")
        self.customer_f = LiveSearch(cw,
            query_fn=self._suggest_customers,
            on_change=lambda t: None,
            placeholder="🔍  Nombre del cliente...",
            debounce_ms=200)
        self.customer_f.pack(fill="x", pady=(3,0))

        # Cajero con sugerencias predictivas
        ew = ctk.CTkFrame(fr, fg_color="transparent")
        ew.grid(row=0, column=3, padx=(0,0), sticky="ew")
        ctk.CTkLabel(ew, text="Cajero", font=("Arial",11), text_color=SUBTEXT).pack(anchor="w")
        self.cashier_f = LiveSearch(ew,
            query_fn=self._suggest_cashiers,
            on_change=lambda t: None,
            placeholder="🔍  Nombre del cajero...",
            debounce_ms=200)
        self.cashier_f.pack(fill="x", pady=(3,0))

        # Método de pago
        pw = ctk.CTkFrame(fr, fg_color="transparent")
        pw.grid(row=0, column=4, padx=(0,0), sticky="ew")
        ctk.CTkLabel(pw, text="Método de Pago", font=("Arial",11),
                     text_color=SUBTEXT).pack(anchor="w")
        self.payment_var = ctk.StringVar(value="Todos")
        ctk.CTkOptionMenu(pw, values=["Todos","Efectivo","Tarjeta de Crédito",
                                       "Tarjeta de Débito","Transferencia Bancaria",
                                       "Pago Móvil","Cheque"],
                          variable=self.payment_var,
                          fg_color=INPUT_BG, button_color="#2A2D3A",
                          button_hover_color="#3A3D52", dropdown_fg_color="#1A1D27",
                          dropdown_hover_color="#1A2E22", text_color=TEXT,
                          font=("Arial",12), height=38, dynamic_resizing=False
                          ).pack(fill="x", pady=(3,0))

        # Valores por defecto: último mes
        today = date.today()
        self.date_from.insert(0, (today - timedelta(days=30)).strftime("%Y-%m-%d"))
        self.date_to.insert(0, today.strftime("%Y-%m-%d"))

        # Botones rápidos de rango
        qr = ctk.CTkFrame(filt, fg_color="transparent")
        qr.pack(fill="x", padx=16, pady=(0, 12))
        for label, days in [("Hoy",0),("Ayer",1),("7 días",7),("30 días",30),("Este mes",-1)]:
            ctk.CTkButton(qr, text=label, height=30, width=80, corner_radius=6,
                          fg_color=INPUT_BG, hover_color="#1A2E22",
                          text_color=SUBTEXT, font=("Arial",11),
                          command=lambda d=days, l=label: self._quick_range(d, l)
                          ).pack(side="left", padx=(0,6))
        ctk.CTkButton(qr, text="🔍  Buscar", height=34, corner_radius=8,
                      fg_color=ACCENT, hover_color="#2EBF7A",
                      text_color="#0F1117", font=("Arial",12,"bold"),
                      command=self.search).pack(side="right")
        ctk.CTkButton(qr, text="📊  Exportar", height=34, corner_radius=8,
                      fg_color="#1A3A2A", hover_color="#2EBF7A",
                      text_color=ACCENT, font=("Arial",12),
                      command=self.export).pack(side="right", padx=(0,8))

        # ── KPIs ──
        kpi_row = ctk.CTkFrame(container, fg_color="transparent")
        kpi_row.pack(fill="x", padx=20, pady=(0,8))
        kpi_row.columnconfigure((0,1,2,3), weight=1)
        self._kpi_frames = []
        for col, label, color in [(0,"🧾 Facturas",TEXT),(1,"💰 Total",ACCENT),
                                   (2,"📦 Productos",CYAN),(3,"💳 Método principal",WARNING)]:
            f = ctk.CTkFrame(kpi_row, fg_color=CARD, corner_radius=12,
                              border_width=1, border_color=CARD_BORDER)
            f.grid(row=0, column=col, padx=(0 if col==0 else 6,0), sticky="ew")
            ctk.CTkLabel(f, text=label, font=("Arial",10), text_color=SUBTEXT).pack(anchor="w", padx=12, pady=(10,0))
            lbl = ctk.CTkLabel(f, text="—", font=("Arial",18,"bold"), text_color=color)
            lbl.pack(anchor="w", padx=12, pady=(0,10))
            self._kpi_frames.append(lbl)

        # ── Tabla ──
        tc = ctk.CTkFrame(container, fg_color=CARD, corner_radius=12,
                          border_width=1, border_color=CARD_BORDER)
        tc.pack(fill="both", expand=True, padx=20, pady=(0,20))
        ctk.CTkLabel(tc, text="Facturas Encontradas",
                     font=("Arial",12,"bold"), text_color=SUBTEXT).pack(anchor="w", padx=16, pady=(12,2))
        ctk.CTkFrame(tc, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=16, pady=(0,8))

        style = ttk.Style(); style.theme_use("clam")
        style.configure("HST.Treeview", background="#1A1D27", foreground="#FFFFFF",
                         fieldbackground="#1A1D27", borderwidth=0, font=("Arial",11), rowheight=30)
        style.configure("HST.Treeview.Heading", background="#1E2130",
                         foreground="#8B8FA8", font=("Arial",10,"bold"), borderwidth=0)
        style.map("HST.Treeview", background=[("selected", "#1A2E22"), ("!selected", "#1A1D27")], foreground=[("selected", "#3DD68C"), ("!selected", "#FFFFFF")])

        cols = ("N°","Cliente","Fecha","Hora","Cajero","Método","Total")
        self.tree = ttk.Treeview(tc, columns=cols, show="headings", height=16, style="HST.Treeview")
        try:
            self.tree.configure(style=self.tree["style"])
            self.tree.tk.call("ttk::style", "configure", self.tree["style"], "-fieldbackground", "#1A1D27")
            self.tree.tk.call("ttk::style", "configure", self.tree["style"], "-background", "#1A1D27")
            self.tree.tk.call("ttk::style", "configure", self.tree["style"], "-foreground", "#FFFFFF")
        except Exception:
            pass
        for col, w, anc in [("N°",75,"center"),("Cliente",200,"w"),("Fecha",90,"center"),
                              ("Hora",65,"center"),("Cajero",110,"w"),
                              ("Método",140,"w"),("Total",100,"e")]:
            self.tree.heading(col, text=col); self.tree.column(col, width=w, anchor=anc)
        self.tree.pack(fill="both", expand=True, padx=16, pady=(0,12))
        self.tree.bind("<Double-1>", self._open_detail)

        ctk.CTkLabel(tc, text="💡 Doble clic en una factura para ver su detalle",
                     font=("Arial",10), text_color="#3A3D52").pack(anchor="e", padx=16, pady=(0,8))

        self.search()

    def _lf(self, parent, label, col):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=0, column=col, padx=(0,8), sticky="ew")
        ctk.CTkLabel(f, text=label, font=("Arial",11), text_color=SUBTEXT).pack(anchor="w")
        ef = ctk.CTkFrame(f, fg_color=INPUT_BG, corner_radius=8, border_width=1, border_color=INPUT_BORDER)
        ef.pack(fill="x", pady=(3,0))
        e = ctk.CTkEntry(ef, border_width=0, fg_color="transparent",
                         height=38, font=("Arial",13), text_color=TEXT)
        e.pack(fill="x", padx=8); return e

    def _quick_range(self, days, label):
        today = date.today()
        if label == "Este mes":
            from_d = today.replace(day=1); to_d = today
        elif days == 0:
            from_d = to_d = today
        elif days == 1:
            from_d = to_d = today - timedelta(days=1)
        else:
            from_d = today - timedelta(days=days); to_d = today
        self.date_from.delete(0,"end"); self.date_from.insert(0, from_d.strftime("%Y-%m-%d"))
        self.date_to.delete(0,"end");   self.date_to.insert(0,   to_d.strftime("%Y-%m-%d"))
        self.search()

    def _suggest_customers(self, text):
        conn = create_connection()
        try:
            cur = conn.cursor()
            cur.execute("""SELECT DISTINCT customer_name FROM invoices
                           WHERE customer_name LIKE ? ORDER BY customer_name LIMIT 8""",
                        (f"%{text}%",))
            rows = cur.fetchall()
        finally:
            conn.close()
        return [(r[0], "") for r in rows]

    def _suggest_cashiers(self, text):
        """Sugiere todos los usuarios registrados en el sistema."""
        conn = create_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT username, role FROM users
                WHERE username LIKE ? OR role LIKE ?
                ORDER BY username
            """, (f"%{text}%", f"%{text}%"))
            rows = cur.fetchall()
        finally:
            conn.close()
        return [(r[0], f"Rol: {r[1]}") for r in rows]

    def search(self):
        df  = self.date_from.get().strip() or "2000-01-01"
        dt  = self.date_to.get().strip()   or date.today().isoformat()
        cli = self.customer_f.get().strip()
        caj = self.cashier_f.get().strip()
        pay = self.payment_var.get()

        conn = create_connection()
        try:
            cur = conn.cursor()
            sql  = """SELECT id, customer_name, purchase_date,
                             IFNULL(employee,'—'), IFNULL(payment_method,'Efectivo'), total
                      FROM invoices
                      WHERE purchase_date >= ? AND purchase_date <= ?"""
            params = [df, dt + " 23:59:59"]
            if cli: sql += " AND customer_name LIKE ?"; params.append(f"%{cli}%")
            if caj: sql += " AND employee LIKE ?";       params.append(f"%{caj}%")
            if pay != "Todos": sql += " AND payment_method=?"; params.append(pay)
            sql += " ORDER BY id DESC"
            cur.execute(sql, params)
            self._rows = cur.fetchall()

            # KPIs
            total_amt = sum(float(r[5] or 0) for r in self._rows)
            cur.execute("""SELECT IFNULL(SUM(ii.quantity),0) FROM invoice_items ii
                           JOIN invoices i ON ii.invoice_id=i.id
                           WHERE i.purchase_date>=? AND i.purchase_date<=?""",
                        [df, dt+" 23:59:59"])
            total_items = cur.fetchone()[0]

            # Método dominante
            methods = {}
            for r in self._rows:
                m = r[4]; methods[m] = methods.get(m,0) + 1
            top_method = max(methods, key=methods.get) if methods else "—"
        finally:
            conn.close()

        cfg = config.load(); cy = cfg["billing"].get("currency","$")
        self._kpi_frames[0].configure(text=str(len(self._rows)))
        self._kpi_frames[1].configure(text=f"{cy} {total_amt:,.2f}")
        self._kpi_frames[2].configure(text=str(int(total_items)))
        self._kpi_frames[3].configure(text=top_method)

        # Tabla
        for i in self.tree.get_children(): self.tree.delete(i)
        for r in self._rows:
            fecha = _fmt_date(r[2])
            hora  = _fmt_time(r[2])
            self.tree.insert("","end", values=(
                f"#{r[0]:06d}", r[1], fecha, hora, r[3], r[4],
                f"{cy} {r[5]:,.2f}"
            ))

    def _open_detail(self, event=None):
        sel = self.tree.selection()
        if not sel: return
        v   = self.tree.item(sel[0],"values")
        inv_id = int(v[0].replace("#",""))

        win = ctk.CTkToplevel(self.parent)
        win.title(f"Factura #{inv_id:06d}")
        win.geometry("700x480")
        win.configure(fg_color=BG)
        win.grab_set()

        ctk.CTkLabel(win, text=f"🧾  Detalle — Factura #{inv_id:06d}",
                     font=("Arial",18,"bold"), text_color=TEXT).pack(padx=20, pady=(20,2), anchor="w")
        ctk.CTkLabel(win, text=f"Cliente: {v[1]}   |   {v[2]} {v[3]}   |   {v[5]}   |   Total: {v[6]}",
                     font=("Arial",11), text_color=SUBTEXT).pack(padx=20, anchor="w")
        ctk.CTkFrame(win, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=20, pady=(10,10))

        card = ctk.CTkFrame(win, fg_color=CARD, corner_radius=12,
                             border_width=1, border_color=CARD_BORDER)
        card.pack(fill="both", expand=True, padx=20, pady=(0,20))

        style = ttk.Style()
        style.configure("DET.Treeview", background="#1A1D27", foreground="#FFFFFF",
                         fieldbackground="#1A1D27", borderwidth=0, font=("Arial",12), rowheight=30)
        style.configure("DET.Treeview.Heading", background="#1E2130",
                         foreground="#8B8FA8", font=("Arial",11,"bold"), borderwidth=0)
        style.map("DET.Treeview", background=[("selected", "#1A2E22"), ("!selected", "#1A1D27")], foreground=[("selected", "#3DD68C"), ("!selected", "#FFFFFF")])

        cols = ("Producto","Cantidad","Precio Unit.","Total")
        t = ttk.Treeview(card, columns=cols, show="headings", style="DET.Treeview")
        for col, w, anc in [("Producto",280,"w"),("Cantidad",90,"center"),
                              ("Precio Unit.",130,"e"),("Total",130,"e")]:
            t.heading(col,text=col); t.column(col,width=w,anchor=anc)
        t.pack(fill="both", expand=True, padx=14, pady=14)

        cfg = config.load(); cy = cfg["billing"].get("currency","$")
        conn = create_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT product_name,quantity,price,total FROM invoice_items WHERE invoice_id=?", (inv_id,))
            for item in cur.fetchall():
                t.insert("","end", values=(item[0], item[1], f"{cy} {item[2]:,.2f}", f"{cy} {item[3]:,.2f}"))
        finally:
            conn.close()

    def export(self):
        if not self._rows: messagebox.showwarning("Sin datos","Realice una búsqueda primero."); return
        cfg = config.load(); cy = cfg["billing"].get("currency","$")
        rows = [(f"#{r[0]:06d}", r[1],
                 _fmt_date(r[2]),
                 _fmt_time(r[2]),
                 r[3], r[4], f"{cy} {r[5]:,.2f}") for r in self._rows]
        export_to_excel(rows, ["N° Factura","Cliente","Fecha","Hora","Cajero","Método","Total"],
                        f"historial_ventas_{date.today()}.xlsx")
