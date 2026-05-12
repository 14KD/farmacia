import customtkinter as ctk
from tkinter import messagebox, filedialog, ttk
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from auth import session
from database.connection import create_connection
from database.backup import create_backup, restore_backup
from ui.products_ui import ProductsUI
from ui.customers_ui import CustomersUI
from ui.invoices_ui import InvoicesUI
from ui.reports_ui import ReportsUI
from ui.users_ui import UsersUI
from ui.settings_ui import SettingsUI
from ui.suppliers_ui import SuppliersUI
from utils.logger import write_log


# ─── Paleta de colores ───────────────────────────
BG          = "#0F1117"
SIDEBAR_BG  = "#12141C"
CARD        = "#1A1D27"
CARD_BORDER = "#252836"
ACCENT      = "#3DD68C"
CYAN        = "#22D3EE"
TEXT        = "#FFFFFF"
SUBTEXT     = "#8B8FA8"
WARNING     = "#FFA94D"
DANGER      = "#FF6B6B"


class Dashboard:

    def __init__(self, root):

        self.root = root
        self.root.title("FarmaFactura Pro")
        self.root.configure(fg_color=BG)
        self.nav_buttons = {}
        self._section_frames = {}   # cache de frames por sección
        self._chart_cache   = {}   # cache de datos para gráficos

        self._build_sidebar()
        self._build_main_area()
        self.show_home()

    # ═════════════════════════════════════════════
    # SIDEBAR
    # ═════════════════════════════════════════════

    def _build_sidebar(self):

        self.sidebar = ctk.CTkFrame(
            self.root, width=190, corner_radius=0, fg_color=SIDEBAR_BG
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo
        logo_row = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_row.pack(pady=(22, 16), padx=14, fill="x")

        icon_box = ctk.CTkFrame(logo_row, width=34, height=34, corner_radius=8, fg_color="#1E3A2F")
        icon_box.pack(side="left", padx=(0, 8))
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text="✚", font=("Arial", 17, "bold"), text_color=ACCENT).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(logo_row, text="FarmaFactura", font=("Georgia", 13, "bold"), text_color=TEXT).pack(side="left")

        # Divisor
        ctk.CTkFrame(self.sidebar, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=14, pady=(0, 10))

        # Items de navegación
        is_admin = session.current_role in ("admin", "Administrador")

        nav_items = [
            ("🏠", "Resumen",    self.show_home,     True),
            ("🧾", "Ventas",     self.show_invoices,  True),
            ("📦", "Inventario", self.show_products,  True),
            ("🏭", "Proveedores",self.show_suppliers, True),
            ("👥", "Clientes",   self.show_customers, True),
            ("📊", "Reportes",   self.show_reports,   is_admin),
            ("👤", "Usuarios",   self.show_users,     is_admin),
            ("⚙",  "Ajustes",   self.show_settings,  True),
        ]

        for icon, label, cmd, visible in nav_items:
            if not visible:
                continue
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"  {icon}   {label}",
                anchor="w",
                height=40,
                corner_radius=8,
                fg_color="transparent",
                hover_color="#1C1F2E",
                text_color=SUBTEXT,
                font=("Arial", 13),
                command=lambda lbl=label, c=cmd: self._activate(lbl, c)
            )
            btn.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[label] = btn

        # Botones inferiores
        bottom = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", padx=10, pady=14)

        ctk.CTkFrame(self.sidebar, height=1, fg_color=CARD_BORDER).pack(side="bottom", fill="x", padx=14, pady=4)

        # Cerrar sesión
        ctk.CTkButton(
            bottom, text="🚪  Cerrar Sesión", height=38, corner_radius=8,
            fg_color="#2A1A2E", hover_color="#6B21A8",
            text_color="#C084FC", font=("Arial", 12, "bold"),
            command=self.logout
        ).pack(fill="x", pady=(0, 6))

        ctk.CTkButton(
            bottom, text="💾  Backup", height=34, corner_radius=8,
            fg_color="#1A2E22", hover_color="#2EBF7A",
            text_color=ACCENT, font=("Arial", 12),
            command=self.make_backup
        ).pack(fill="x", pady=(0, 6))

        restore_btn = ctk.CTkButton(
            bottom, text="🔄  Restaurar", height=34, corner_radius=8,
            fg_color="#2E1A1A", hover_color="#BF2E2E",
            text_color=DANGER, font=("Arial", 12),
            command=self.restore_database
        )
        restore_btn.pack(fill="x")

        if session.current_role not in ("admin", "Administrador"):
            restore_btn.configure(state="disabled")

    def _activate(self, label, cmd):
        for btn in self.nav_buttons.values():
            btn.configure(fg_color="transparent", text_color=SUBTEXT)
        self.nav_buttons[label].configure(fg_color="#1A2E22", text_color=ACCENT)
        cmd()

    # ═════════════════════════════════════════════
    # ÁREA PRINCIPAL
    # ═════════════════════════════════════════════

    def _build_main_area(self):

        wrapper = ctk.CTkFrame(self.root, fg_color=BG, corner_radius=0)
        wrapper.pack(side="right", fill="both", expand=True)

        # ── Topbar ──
        topbar = ctk.CTkFrame(wrapper, fg_color=SIDEBAR_BG, height=54, corner_radius=0)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        self.topbar_title = ctk.CTkLabel(
            topbar, text="", font=("Arial", 14, "bold"), text_color=TEXT
        )
        self.topbar_title.pack(side="left", padx=20)

        # Reloj
        self.clock_lbl = ctk.CTkLabel(topbar, text="", font=("Arial", 13), text_color=SUBTEXT)
        self.clock_lbl.pack(side="right", padx=20)
        self._tick()

        # Saludo usuario
        user = session.current_user
        username = user[1] if isinstance(user, tuple) else str(user)
        ctk.CTkLabel(
            topbar, text=f"¡Hola, {username}!",
            font=("Arial", 13, "bold"), text_color=ACCENT
        ).pack(side="right", padx=(0, 6))

        ctk.CTkLabel(topbar, text="🔔", font=("Arial", 16), text_color=SUBTEXT).pack(side="right", padx=10)

        # ── Área de contenido scrollable ──
        self.main_frame = ctk.CTkScrollableFrame(
            wrapper, fg_color=BG, corner_radius=0,
            scrollbar_button_color="#252836",
            scrollbar_button_hover_color="#3A3D52"
        )
        self.main_frame.pack(fill="both", expand=True)

    def _tick(self):
        self.clock_lbl.configure(text=datetime.now().strftime("%I:%M %p"))
        self.root.after(60000, self._tick)

    # ═════════════════════════════════════════════
    # UTILIDADES DE TARJETAS
    # ═════════════════════════════════════════════

    def _card(self, parent, **grid_kw):
        f = ctk.CTkFrame(
            parent, fg_color=CARD, corner_radius=12,
            border_width=1, border_color=CARD_BORDER
        )
        f.grid(**grid_kw, padx=7, pady=7, sticky="nsew")
        return f

    def _card_header(self, parent, text):
        ctk.CTkLabel(
            parent, text=text,
            font=("Arial", 11, "bold"), text_color=SUBTEXT
        ).pack(anchor="w", padx=14, pady=(12, 2))
        ctk.CTkFrame(parent, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=14, pady=(0, 6))

    # ═════════════════════════════════════════════
    # RESUMEN / HOME
    # ═════════════════════════════════════════════

    def show_home(self):

        # Dashboard siempre muestra datos frescos
        key = "home"
        if key in self._section_frames:
            self._section_frames[key].destroy()
            del self._section_frames[key]
        self.clear_main_frame()
        home_frame = self._get_section_frame(key)
        home_frame.pack(fill="both", expand=True)
        self._build_home(home_frame)

    def _build_home(self, parent):
        self.topbar_title.configure(text=f"Panel de Control  —  {datetime.now().strftime('%d de %B de %Y')}")

        for b in self.nav_buttons.values():
            b.configure(fg_color="transparent", text_color=SUBTEXT)
        self.nav_buttons["Resumen"].configure(fg_color="#1A2E22", text_color=ACCENT)

        # ── Consultas ──
        conn = create_connection()
        cur  = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")

        cur.execute("SELECT IFNULL(SUM(total),0) FROM invoices WHERE purchase_date LIKE ?", (f"{today}%",))
        sales_today = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM invoices WHERE purchase_date LIKE ?", (f"{today}%",))
        invoices_today = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM products")
        total_products = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM customers")
        total_customers = cur.fetchone()[0]

        cur.execute("SELECT name, stock, 10 FROM products WHERE stock > 0 AND stock <= 10 ORDER BY stock ASC LIMIT 6")
        low_stock = cur.fetchall()

        cur.execute("""
            SELECT product_name, SUM(quantity) q
            FROM invoice_items GROUP BY product_name ORDER BY q DESC LIMIT 7
        """)
        top_products = cur.fetchall()

        cur.execute("SELECT id, customer_name, total, purchase_date FROM invoices ORDER BY id DESC LIMIT 6")
        recent_inv = cur.fetchall()

        # Últimos 7 días
        cur.execute("""
            SELECT purchase_date, IFNULL(SUM(total),0)
            FROM invoices
            WHERE purchase_date >= date('now','-6 days')
            GROUP BY purchase_date
            ORDER BY purchase_date
        """)
        weekly = cur.fetchall()

        # Ventas por mes (año actual)
        cur.execute("""
            SELECT strftime('%m', purchase_date) mes, IFNULL(SUM(total),0)
            FROM invoices
            WHERE strftime('%Y', purchase_date) = strftime('%Y','now')
            GROUP BY mes ORDER BY mes
        """)
        monthly = cur.fetchall()

        conn.close()

        # ══════════════════════════════════════════
        # FILA 0 — 4 TARJETAS ESTADÍSTICAS
        # ══════════════════════════════════════════
        stats_row = ctk.CTkFrame(parent, fg_color="transparent")
        stats_row.pack(fill="x", padx=6, pady=(6, 0))
        stats_row.columnconfigure((0,1,2,3), weight=1)

        for col, icon, label, value, color in [
            (0, "💰", "Ventas Hoy",        f"${sales_today:,.2f}", ACCENT),
            (1, "🧾", "Facturas Hoy",      str(invoices_today),    CYAN),
            (2, "📦", "Total Productos",   str(total_products),    "#C084FC"),
            (3, "👥", "Total Clientes",    str(total_customers),   WARNING),
        ]:
            c = ctk.CTkFrame(stats_row, fg_color=CARD, corner_radius=12,
                              border_width=1, border_color=CARD_BORDER)
            c.grid(row=0, column=col, padx=7, pady=7, sticky="ew")
            top_r = ctk.CTkFrame(c, fg_color="transparent")
            top_r.pack(fill="x", padx=14, pady=(14, 2))
            ctk.CTkLabel(top_r, text=icon, font=("Arial", 18), text_color=color).pack(side="left")
            ctk.CTkLabel(top_r, text=label, font=("Arial", 11), text_color=SUBTEXT).pack(side="left", padx=6)
            ctk.CTkLabel(c, text=value, font=("Arial", 22, "bold"), text_color=color).pack(anchor="w", padx=14, pady=(0, 14))

        # ══════════════════════════════════════════
        # GRID PRINCIPAL — 3 columnas
        # ══════════════════════════════════════════
        grid = ctk.CTkFrame(parent, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=6, pady=0)
        grid.columnconfigure(0, weight=3)
        grid.columnconfigure(1, weight=3)
        grid.columnconfigure(2, weight=2)

        # ── [0,0] Gráfico 7 días ─────────────────
        c_week = self._card(grid, row=0, column=0)
        self._card_header(c_week, "📈  Ventas — Últimos 7 Días")

        fig1, ax1 = plt.subplots(figsize=(3.4, 2.0))
        fig1.patch.set_facecolor(CARD)
        ax1.set_facecolor(CARD)
        if weekly:
            days  = [w[0][5:] for w in weekly]   # MM-DD
            vals  = [w[1] for w in weekly]
            bars  = ax1.bar(days, vals, color=ACCENT, width=0.5)
            ax1.tick_params(colors=SUBTEXT, labelsize=7)
            ax1.spines[:].set_visible(False)
            ax1.yaxis.set_visible(False)
            for bar, val in zip(bars, vals):
                ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(vals)*0.02,
                         f"${val:,.0f}", ha="center", color=SUBTEXT, fontsize=6)
        else:
            ax1.text(0.5, 0.5, "Sin ventas esta semana", ha="center", va="center",
                     color=SUBTEXT, transform=ax1.transAxes, fontsize=9)
            ax1.axis("off")
        fig1.tight_layout(pad=0.4)
        cv1 = FigureCanvasTkAgg(fig1, c_week)
        cv1.get_tk_widget().pack(padx=10, pady=(0, 10), fill="x")
        cv1.draw()
        plt.close(fig1)

        # ── [0,1] Gráfico mensual ────────────────
        c_month = self._card(grid, row=0, column=1)
        self._card_header(c_month, "📅  Ventas Mensuales (Año Actual)")

        MONTH_NAMES = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
        fig2, ax2 = plt.subplots(figsize=(3.4, 2.0))
        fig2.patch.set_facecolor(CARD)
        ax2.set_facecolor(CARD)
        if monthly:
            meses = [MONTH_NAMES[int(m[0])-1] for m in monthly]
            mvals = [m[1] for m in monthly]
            ax2.bar(meses, mvals, color=CYAN, width=0.5)
            ax2.tick_params(colors=SUBTEXT, labelsize=7)
            ax2.spines[:].set_visible(False)
            ax2.yaxis.set_visible(False)
        else:
            ax2.text(0.5, 0.5, "Sin ventas este año", ha="center", va="center",
                     color=SUBTEXT, transform=ax2.transAxes, fontsize=9)
            ax2.axis("off")
        fig2.tight_layout(pad=0.4)
        cv2 = FigureCanvasTkAgg(fig2, c_month)
        cv2.get_tk_widget().pack(padx=10, pady=(0, 10), fill="x")
        cv2.draw()
        plt.close(fig2)

        # ── [0,2] Inventario Crítico ─────────────
        c_inv = self._card(grid, row=0, column=2)
        self._card_header(c_inv, "⚠  Inventario Crítico")
        self._treeview_stock(c_inv, low_stock)

        # ── [1,0] Productos más vendidos ─────────
        c_top = self._card(grid, row=1, column=0)
        self._card_header(c_top, "🏆  Productos Más Vendidos")

        if top_products:
            fig3, ax3 = plt.subplots(figsize=(3.2, 2.2))
            fig3.patch.set_facecolor(CARD)
            ax3.set_facecolor(CARD)
            names = [p[0][:20] for p in top_products]
            qtys  = [p[1] for p in top_products]
            bars  = ax3.barh(names[::-1], qtys[::-1], color=CYAN, height=0.5)
            ax3.tick_params(colors=SUBTEXT, labelsize=8)
            ax3.spines[:].set_visible(False)
            ax3.xaxis.set_visible(False)
            for bar, val in zip(bars, qtys[::-1]):
                ax3.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
                         str(val), va="center", color=SUBTEXT, fontsize=8)
            fig3.tight_layout(pad=0.4)
            cv3 = FigureCanvasTkAgg(fig3, c_top)
            cv3.get_tk_widget().pack(padx=10, pady=(0, 10), fill="x")
            cv3.draw()
            plt.close(fig3)
        else:
            ctk.CTkLabel(c_top, text="Sin ventas registradas aún.",
                         text_color=SUBTEXT, font=("Arial", 12)).pack(pady=24)

        # ── [1,1] Alertas + Facturas recientes ───
        mid_col = ctk.CTkFrame(grid, fg_color="transparent")
        mid_col.grid(row=1, column=1, padx=7, pady=7, sticky="nsew")

        alert_card = ctk.CTkFrame(mid_col, fg_color=CARD, corner_radius=12,
                                   border_width=1, border_color=CARD_BORDER)
        alert_card.pack(fill="x", pady=(0, 7))
        self._card_header(alert_card, "🔔  Alertas")
        inner = ctk.CTkFrame(alert_card, fg_color="#2A1A0A", corner_radius=8)
        inner.pack(fill="x", padx=12, pady=(0, 12))
        ctk.CTkLabel(inner,
                     text=f"  ⚠  {len(low_stock)} productos con stock crítico",
                     font=("Arial", 12), text_color=WARNING).pack(anchor="w", padx=8, pady=10)

        # ── [1,2] Facturas recientes (clickeable) ─
        inv_card = ctk.CTkFrame(grid, fg_color=CARD, corner_radius=12,
                                 border_width=1, border_color=CARD_BORDER)
        inv_card.grid(row=1, column=2, padx=7, pady=7, sticky="nsew")
        self._card_header(inv_card, "🧾  Facturas Recientes  (doble clic = detalle)")
        self._treeview_invoices(inv_card, recent_inv)

    # ─── Treeview: Stock crítico ─────────────────

    def _treeview_stock(self, parent, items):

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("FF.Treeview",
            background=CARD, foreground=TEXT, fieldbackground=CARD,
            borderwidth=0, font=("Arial", 11), rowheight=26
        )
        style.configure("FF.Treeview.Heading",
            background="#1E2130", foreground=SUBTEXT,
            font=("Arial", 10, "bold"), borderwidth=0
        )
        style.map("FF.Treeview",
            background=[("selected", "#1A2E22")],
            foreground=[("selected", ACCENT)]
        )

        cols = ("Medicamento", "Stock Actual", "Mín")
        tree = ttk.Treeview(parent, columns=cols, show="headings", height=6, style="FF.Treeview")
        tree.heading("Medicamento",  text="Medicamento")
        tree.heading("Stock Actual", text="Stock Actual")
        tree.heading("Mín",          text="Stock Mínimo")
        tree.column("Medicamento",  width=140)
        tree.column("Stock Actual", width=80,  anchor="center")
        tree.column("Mín",          width=80,  anchor="center")

        for row in items:
            tree.insert("", "end", values=(row[0], row[1], row[2]))
        if not items:
            tree.insert("", "end", values=("✔ Sin alertas críticas", "—", "—"))

        tree.pack(padx=10, pady=(0, 12), fill="x")

    # ─── Treeview: Facturas recientes ────────────

    def _treeview_invoices(self, parent, invoices):

        style = ttk.Style()
        style.configure("FF.Treeview",
            background=CARD, foreground=TEXT, fieldbackground=CARD,
            borderwidth=0, font=("Arial", 11), rowheight=26
        )
        style.configure("FF.Treeview.Heading",
            background="#1E2130", foreground=SUBTEXT,
            font=("Arial", 10, "bold"), borderwidth=0
        )
        style.map("FF.Treeview",
            background=[("selected", "#1A2E22")],
            foreground=[("selected", ACCENT)]
        )

        cols = ("ID", "Cliente", "Total", "Fecha")
        tree = ttk.Treeview(parent, columns=cols, show="headings", height=6, style="FF.Treeview")
        tree.heading("ID",      text="ID")
        tree.heading("Cliente", text="Cliente")
        tree.heading("Total",   text="Total")
        tree.heading("Fecha",   text="Fecha")
        tree.column("ID",      width=45,  anchor="center")
        tree.column("Cliente", width=100)
        tree.column("Total",   width=90,  anchor="e")
        tree.column("Fecha",   width=85,  anchor="center")

        for inv in invoices:
            fecha = inv[3][:10] if inv[3] else "—"
            tree.insert("", "end", values=(inv[0], inv[1], f"${inv[2]:,.2f}", fecha))
        if not invoices:
            tree.insert("", "end", values=("—", "Sin registros", "—", "—"))

        tree.pack(padx=10, pady=(0, 4), fill="x")

        hint = ctk.CTkLabel(parent, text="💡 Doble clic para ver detalle",
                             font=("Arial", 10), text_color="#3A3D52")
        hint.pack(anchor="e", padx=14, pady=(0, 8))

        tree.bind("<Double-1>", lambda e: self._open_invoice_detail(tree))

    def _open_invoice_detail(self, tree):
        sel = tree.selection()
        if not sel: return
        vals = tree.item(sel[0], "values")
        invoice_id = vals[0]
        if invoice_id == "—": return

        win = ctk.CTkToplevel(self.root)
        win.title(f"Factura #{invoice_id}")
        win.geometry("680x460")
        win.configure(fg_color=BG)
        win.grab_set()

        ctk.CTkLabel(win, text=f"🧾  Detalle — Factura #{invoice_id}",
                     font=("Arial", 18, "bold"), text_color=TEXT).pack(padx=20, pady=(20,4), anchor="w")
        ctk.CTkLabel(win, text=f"Cliente: {vals[1]}   |   Total: {vals[2]}   |   Fecha: {vals[3]}",
                     font=("Arial", 12), text_color=SUBTEXT).pack(padx=20, anchor="w")
        ctk.CTkFrame(win, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=20, pady=(10,12))

        card = ctk.CTkFrame(win, fg_color=CARD, corner_radius=12,
                             border_width=1, border_color=CARD_BORDER)
        card.pack(fill="both", expand=True, padx=20, pady=(0,20))

        style2 = ttk.Style()
        style2.configure("DET2.Treeview", background=CARD, foreground=TEXT,
                          fieldbackground=CARD, borderwidth=0, font=("Arial", 12), rowheight=32)
        style2.configure("DET2.Treeview.Heading", background="#1E2130", foreground=SUBTEXT,
                          font=("Arial", 11, "bold"), borderwidth=0)
        style2.map("DET2.Treeview", background=[("selected","#1A2E22")], foreground=[("selected",ACCENT)])

        cols2 = ("Producto", "Cantidad", "Precio Unit.", "Total")
        t2 = ttk.Treeview(card, columns=cols2, show="headings", style="DET2.Treeview")
        for col, w, anc in [("Producto",280,"w"),("Cantidad",90,"center"),
                              ("Precio Unit.",130,"e"),("Total",130,"e")]:
            t2.heading(col, text=col)
            t2.column(col, width=w, anchor=anc)
        t2.pack(fill="both", expand=True, padx=14, pady=14)

        conn = create_connection(); cur = conn.cursor()
        cur.execute("""SELECT product_name, quantity, price, total
                       FROM invoice_items WHERE invoice_id=?""", (invoice_id,))
        items = cur.fetchall()
        conn.close()

        for item in items:
            t2.insert("", "end", values=(item[0], item[1],
                                          f"${item[2]:,.2f}", f"${item[3]:,.2f}"))
        if not items:
            t2.insert("", "end", values=("Sin productos", "—", "—", "—"))

    # ═════════════════════════════════════════════
    # UTILIDADES
    # ═════════════════════════════════════════════

    def clear_main_frame(self):
        """Oculta todos los frames de sección sin destruirlos."""
        for frame in self._section_frames.values():
            frame.pack_forget()

    def _get_section_frame(self, key):
        """Retorna el frame de una sección, creándolo si no existe."""
        if key not in self._section_frames:
            f = ctk.CTkFrame(self.main_frame, fg_color=BG, corner_radius=0)
            self._section_frames[key] = f
        return self._section_frames[key]

    def _show_section(self, key, builder_fn):
        """Muestra una sección, construyéndola solo la primera vez."""
        self.clear_main_frame()
        frame = self._get_section_frame(key)
        frame.pack(fill="both", expand=True)
        if not frame.winfo_children():   # solo construir una vez
            builder_fn(frame)

    # ═════════════════════════════════════════════
    # NAVEGACIÓN
    # ═════════════════════════════════════════════

    def show_suppliers(self):
        self.topbar_title.configure(text="Proveedores")
        self._show_section("suppliers", lambda f: SuppliersUI(f))

    def show_products(self):
        self.topbar_title.configure(text="Inventario de Productos")
        self._show_section("products", lambda f: ProductsUI(f))

    def show_customers(self):
        self.topbar_title.configure(text="Gestión de Clientes")
        self._show_section("customers", lambda f: CustomersUI(f))

    def show_invoices(self):
        self.topbar_title.configure(text="Ventas / Facturación")
        # Facturación siempre se reconstruye (carrito limpio)
        key = "invoices"
        if key in self._section_frames:
            self._section_frames[key].destroy()
            del self._section_frames[key]
        self._show_section(key, lambda f: InvoicesUI(f))

    def show_reports(self):
        self.topbar_title.configure(text="Reportes")
        self._show_section("reports", lambda f: ReportsUI(f))

    def show_users(self):
        self.topbar_title.configure(text="Usuarios del Sistema")
        self._show_section("users", lambda f: UsersUI(f))

    def show_settings(self):
        self.topbar_title.configure(text="Ajustes")
        self._show_section("settings", lambda f: SettingsUI(f))

    # ═════════════════════════════════════════════
    # BACKUP
    # ═════════════════════════════════════════════

    def logout(self):
        if not messagebox.askyesno("Cerrar Sesión", "¿Seguro que deseas cerrar sesión?"):
            return
        session.current_user = None
        session.current_role = None
        self.root.destroy()
        import customtkinter as ctk2
        from auth.login_window import LoginWindow
        login_root = ctk2.CTk()
        login_root.title("FarmaFactura Pro — Login")
        login_root.geometry("460x580")
        login_root.resizable(False, False)
        login_root.update_idletasks()
        w, h = 460, 580
        x = (login_root.winfo_screenwidth()  // 2) - (w // 2)
        y = (login_root.winfo_screenheight() // 2) - (h // 2)
        login_root.geometry(f"{w}x{h}+{x}+{y}")
        LoginWindow(login_root)
        login_root.mainloop()

    def make_backup(self):
        backup_file = create_backup()
        messagebox.showinfo("Backup", f"Backup creado:\n{backup_file}")
        write_log(f"Backup creado: {backup_file}")

    def restore_database(self):
        backup_file = filedialog.askopenfilename(
            title="Seleccionar Backup",
            filetypes=[("SQLite Database", "*.db")]
        )
        if not backup_file:
            return
        restore_backup(backup_file)
        messagebox.showinfo("Restaurado", "Backup restaurado.\n\nReinicie el sistema.")