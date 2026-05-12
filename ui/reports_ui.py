import customtkinter as ctk
from tkinter import ttk, messagebox
from database.connection import create_connection
from auth import session
import pandas as pd

BG          = "#0F1117"
CARD        = "#1A1D27"
CARD_BORDER = "#252836"
ACCENT      = "#3DD68C"
CYAN        = "#22D3EE"
TEXT        = "#FFFFFF"
SUBTEXT     = "#8B8FA8"
WARNING     = "#FFA94D"
INPUT_BG    = "#23263A"


class ReportsUI:

    def __init__(self, parent):
        self.parent = parent

        container = ctk.CTkFrame(parent, fg_color=BG, corner_radius=0)
        container.pack(fill="both", expand=True)

        # ── Encabezado ──
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 0))
        ctk.CTkLabel(header, text="📊  Reportes e Historial",
                     font=("Arial", 22, "bold"), text_color=TEXT).pack(side="left")
        ctk.CTkFrame(container, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=20, pady=(10, 16))

        # ── Botones de reporte ──
        actions_card = ctk.CTkFrame(container, fg_color=CARD, corner_radius=12,
                                     border_width=1, border_color=CARD_BORDER)
        actions_card.pack(fill="x", padx=20, pady=(0, 12))
        ctk.CTkLabel(actions_card, text="Acciones",
                     font=("Arial", 12, "bold"), text_color=SUBTEXT).pack(anchor="w", padx=16, pady=(14, 2))
        ctk.CTkFrame(actions_card, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=16, pady=(0, 12))

        btn_row = ctk.CTkFrame(actions_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 16))

        is_admin = session.current_role in ("admin", "Administrador")

        # Botones visibles para todos
        ctk.CTkButton(btn_row, text="🔍  Ver Detalles", height=40, corner_radius=8,
                      fg_color="#1A2E3A", hover_color="#1E6A9A", text_color=CYAN,
                      font=("Arial", 12, "bold"), command=self.show_details).pack(side="left", padx=(0, 10))

        # Botones solo para administradores
        if is_admin:
            for text, fg, hov, tc, cmd in [
                ("💰  Reporte Financiero",  "#1A3A1A", "#2EBF7A", ACCENT,    self.financial_report),
                ("📅  Ventas por Fecha",    "#2A2A1A", "#8A8A0A", WARNING,   self.sales_by_date),
                ("👤  Ventas por Empleado", "#2A1A2A", "#8A2A8A", "#C084FC", self.sales_by_employee),
            ]:
                ctk.CTkButton(btn_row, text=text, height=40, corner_radius=8,
                              fg_color=fg, hover_color=hov, text_color=tc,
                              font=("Arial", 12, "bold"), command=cmd).pack(side="left", padx=(0, 10))

        # ── Tabla historial ──
        table_card = ctk.CTkFrame(container, fg_color=CARD, corner_radius=12,
                                   border_width=1, border_color=CARD_BORDER)
        table_card.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        ctk.CTkLabel(table_card, text="Historial de Facturas",
                     font=("Arial", 12, "bold"), text_color=SUBTEXT).pack(anchor="w", padx=16, pady=(14, 2))
        ctk.CTkFrame(table_card, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=16, pady=(0, 8))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("REP.Treeview", background=CARD, foreground=TEXT,
                         fieldbackground=CARD, borderwidth=0, font=("Arial", 12), rowheight=34)
        style.configure("REP.Treeview.Heading", background="#1E2130", foreground=SUBTEXT,
                         font=("Arial", 11, "bold"), borderwidth=0)
        style.map("REP.Treeview", background=[("selected", "#1A2E22")], foreground=[("selected", ACCENT)])

        cols = ("Factura", "Cliente", "Total", "Fecha", "Empleado")
        self.tree = ttk.Treeview(table_card, columns=cols, show="headings",
                                  height=16, style="REP.Treeview")
        for col, w, anc in [("Factura", 80, "center"), ("Cliente", 220, "w"),
                              ("Total", 120, "e"), ("Fecha", 110, "center"), ("Empleado", 150, "w")]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor=anc)
        self.tree.pack(fill="both", expand=True, padx=16, pady=(0, 14))

        self.load_invoices()

    def get_connection(self): return create_connection()

    def load_invoices(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute("SELECT id, customer_name, total, purchase_date, IFNULL(employee,'—') FROM invoices ORDER BY id DESC")
        for row in cur.fetchall():
            self.tree.insert("", "end", values=(row[0], row[1], f"${row[2]:,.2f}", row[3], row[4]))
        conn.close()

    def show_details(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Advertencia", "Seleccione una factura."); return
        invoice_id = self.tree.item(sel[0], "values")[0]

        win = ctk.CTkToplevel(self.parent)
        win.title(f"Factura #{invoice_id}")
        win.geometry("700x450")
        win.configure(fg_color=BG)

        ctk.CTkLabel(win, text=f"🧾  Detalle — Factura #{invoice_id}",
                     font=("Arial", 18, "bold"), text_color=TEXT).pack(padx=20, pady=(20, 4), anchor="w")
        ctk.CTkFrame(win, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=20, pady=(0, 12))

        card = ctk.CTkFrame(win, fg_color=CARD, corner_radius=12, border_width=1, border_color=CARD_BORDER)
        card.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        style = ttk.Style()
        style.configure("DET.Treeview", background=CARD, foreground=TEXT,
                         fieldbackground=CARD, borderwidth=0, font=("Arial", 12), rowheight=32)
        style.configure("DET.Treeview.Heading", background="#1E2130", foreground=SUBTEXT,
                         font=("Arial", 11, "bold"), borderwidth=0)
        style.map("DET.Treeview", background=[("selected", "#1A2E22")], foreground=[("selected", ACCENT)])

        cols = ("Producto", "Cantidad", "Precio", "Total")
        tree = ttk.Treeview(card, columns=cols, show="headings", style="DET.Treeview")
        for col, w, anc in [("Producto", 280, "w"), ("Cantidad", 90, "center"),
                              ("Precio", 120, "e"), ("Total", 120, "e")]:
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor=anc)
        tree.pack(fill="both", expand=True, padx=14, pady=14)

        conn = self.get_connection(); cur = conn.cursor()
        cur.execute("SELECT product_name, quantity, price, total FROM invoice_items WHERE invoice_id=?", (invoice_id,))
        for row in cur.fetchall():
            tree.insert("", "end", values=(row[0], row[1], f"${row[2]:,.2f}", f"${row[3]:,.2f}"))
        conn.close()

    def financial_report(self):
        conn = create_connection()
        try:
            df = pd.read_sql_query("""
                SELECT ii.product_name, ii.quantity, p.price, p.cost,
                       (p.price - p.cost) * ii.quantity AS profit
                FROM invoice_items ii JOIN products p ON ii.product_name = p.name
            """, conn)
            total_profit = df["profit"].sum()
        except Exception:
            total_profit = 0.0
        finally:
            conn.close()

        win = ctk.CTkToplevel(self.parent)
        win.title("Reporte Financiero")
        win.geometry("420x260")
        win.configure(fg_color=BG)

        ctk.CTkLabel(win, text="💰  Reporte Financiero",
                     font=("Arial", 18, "bold"), text_color=TEXT).pack(padx=24, pady=(24, 8), anchor="w")
        ctk.CTkFrame(win, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=24, pady=(0, 20))

        card = ctk.CTkFrame(win, fg_color=CARD, corner_radius=12, border_width=1, border_color=CARD_BORDER)
        card.pack(fill="x", padx=24)
        ctk.CTkLabel(card, text="Ganancia Total Estimada",
                     font=("Arial", 12), text_color=SUBTEXT).pack(anchor="w", padx=16, pady=(16, 2))
        ctk.CTkLabel(card, text=f"${total_profit:,.2f}",
                     font=("Arial", 30, "bold"), text_color=ACCENT).pack(anchor="w", padx=16, pady=(0, 16))

    def sales_by_date(self):
        conn = create_connection()
        try:
            df = pd.read_sql_query("SELECT id, customer_name, total, purchase_date, IFNULL(employee,\'—\') as employee FROM invoices ORDER BY purchase_date DESC", conn)
            path = "reports/ventas_por_fecha.xlsx"
            df.to_excel(path, index=False)
            messagebox.showinfo("Exportado", f"Archivo generado:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            conn.close()

    def sales_by_employee(self):
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute("""
            SELECT IFNULL(employee,'Sin asignar'), COUNT(*) as facturas, SUM(total) as ventas
            FROM invoices GROUP BY employee ORDER BY ventas DESC
        """)
        data = cur.fetchall(); conn.close()

        win = ctk.CTkToplevel(self.parent)
        win.title("Ventas por Empleado")
        win.geometry("560x400")
        win.configure(fg_color=BG)

        ctk.CTkLabel(win, text="👤  Ventas por Empleado",
                     font=("Arial", 18, "bold"), text_color=TEXT).pack(padx=20, pady=(20, 4), anchor="w")
        ctk.CTkFrame(win, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=20, pady=(0, 12))

        card = ctk.CTkFrame(win, fg_color=CARD, corner_radius=12, border_width=1, border_color=CARD_BORDER)
        card.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        style = ttk.Style()
        style.configure("EMP.Treeview", background=CARD, foreground=TEXT,
                         fieldbackground=CARD, borderwidth=0, font=("Arial", 12), rowheight=34)
        style.configure("EMP.Treeview.Heading", background="#1E2130", foreground=SUBTEXT,
                         font=("Arial", 11, "bold"), borderwidth=0)
        style.map("EMP.Treeview", background=[("selected", "#1A2E22")], foreground=[("selected", ACCENT)])

        cols = ("Empleado", "Facturas", "Total Ventas")
        tree = ttk.Treeview(card, columns=cols, show="headings", style="EMP.Treeview")
        for col, w, anc in [("Empleado", 220, "w"), ("Facturas", 100, "center"), ("Total Ventas", 160, "e")]:
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor=anc)
        tree.pack(fill="both", expand=True, padx=14, pady=14)

        for row in data:
            tree.insert("", "end", values=(row[0], row[1], f"${row[2]:,.2f}"))
        if not data:
            tree.insert("", "end", values=("Sin datos", "—", "—"))