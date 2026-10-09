"""
ui/inventory_ui.py — Inventario General (visión gerencial y control).
Responsabilidades exclusivas de este módulo:
  1. Stock consolidado por producto con KPIs
  2. Vista resumen de todos los lotes activos y sus vencimientos
  3. Alertas de stock bajo / agotado
  4. Ajustes manuales (merma, conteo físico, devoluciones)
  5. Historial de ajustes manuales

Lo que NO hace (ya está en Lotes, con más detalle):
  - Recepción de mercancía
  - Edición / retiro de lotes individuales
  - Movimientos por lote
"""
import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime, date
from database.connection import create_connection
from exports.excel_exporter import export_to_excel
from auth import session
from utils.logger import audit, log_stock_change
import config

# ── Paleta de colores ────────────────────────────────────────────────────────
BG          = "#0F1117"
CARD        = "#1A1D27"
CARD_BORDER = "#252836"
ACCENT      = "#3DD68C"
CYAN        = "#22D3EE"
TEXT        = "#FFFFFF"
SUBTEXT     = "#8B8FA8"
DANGER      = "#EF4444"
DANGER_H    = "#DC2626"
WARNING     = "#FFA94D"
PURPLE      = "#C084FC"
INPUT_BG    = "#23263A"
INPUT_BORDER= "#2E3148"

ADJUSTMENT_REASONS = [
    "Conteo físico",
    "Producto dañado",
    "Producto vencido retirado",
    "Devolución de cliente",
    "Error de registro",
    "Merma / robo",
    "Donación",
    "Otro",
]


def _tree_style(name: str) -> str:
    s = ttk.Style()
    s.theme_use("clam")
    s.configure(f"{name}.Treeview",
                background="#1A1D27",
                foreground="#FFFFFF",
                fieldbackground="#1A1D27",
                borderwidth=0,
                relief="flat",
                font=("Arial", 11),
                rowheight=30)
    s.configure(f"{name}.Treeview.Heading",
                background="#1E2130",
                foreground="#8B8FA8",
                font=("Arial", 10, "bold"),
                borderwidth=0,
                relief="flat")
    s.map(f"{name}.Treeview",
          background=[("selected", "#1A2E22"), ("!selected", "#1A1D27")],
          foreground=[("selected", "#3DD68C"), ("!selected", "#FFFFFF")],
          fieldbackground=[("selected", "#1A2E22"), ("!selected", "#1A1D27")])
    return f"{name}.Treeview"


def _fmt_date(v) -> str:
    if v is None:
        return "—"
    if hasattr(v, "strftime"):
        return v.strftime("%d/%m/%Y")
    s = str(v)
    return s[:10] if len(s) >= 10 else s


class InventoryUI:
    def __init__(self, parent):
        self.parent   = parent
        self.is_admin = session.current_role in ("admin", "Administrador")
        self._sel_product_id   = None
        self._sel_product_name = ""
        self._search_q = ""
        self._lot_map  = {}

        cfg = config.load()
        self._low_stock_threshold = cfg.get("inventory", {}).get("low_stock_threshold", 10)

        container = ctk.CTkFrame(parent, fg_color=BG, corner_radius=0)
        container.pack(fill="both", expand=True)

        # ── Encabezado ──────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(container, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(20, 0))
        ctk.CTkLabel(hdr, text="📊  Inventario General",
                     font=("Arial", 22, "bold"), text_color=TEXT).pack(side="left")

        ctk.CTkButton(hdr, text="🔄 Actualizar", width=110, height=34,
                      corner_radius=8, fg_color=INPUT_BG,
                      hover_color="#2E3148", text_color=SUBTEXT,
                      font=("Arial", 12), command=self._refresh_all
                      ).pack(side="right", padx=(4, 0))
        ctk.CTkButton(hdr, text="📥 Exportar Excel", width=140, height=34,
                      corner_radius=8, fg_color="#1A2E22",
                      hover_color="#2EBF7A", text_color=ACCENT,
                      font=("Arial", 12), command=self._export_excel
                      ).pack(side="right")

        ctk.CTkFrame(container, height=1, fg_color=CARD_BORDER
                     ).pack(fill="x", padx=20, pady=(10, 12))

        # ── KPI cards ───────────────────────────────────────────────────────
        self._kpi_frame = ctk.CTkFrame(container, fg_color="transparent")
        self._kpi_frame.pack(fill="x", padx=20, pady=(0, 12))
        self._kpi_labels = {}
        kpi_defs = [
            ("total_productos", "Total Productos",  TEXT,    "📦"),
            ("stock_bajo",      "Stock Bajo",        WARNING, "⚠"),
            ("agotados",        "Agotados",          DANGER,  "❌"),
            ("valor_inventario","Valor Inventario",  CYAN,    "💰"),
        ]
        for i, (key, label, color, icon) in enumerate(kpi_defs):
            card = ctk.CTkFrame(self._kpi_frame, fg_color=CARD, corner_radius=12,
                                border_width=1, border_color=CARD_BORDER)
            card.grid(row=0, column=i, padx=(0, 10) if i < 3 else 0, sticky="ew")
            self._kpi_frame.columnconfigure(i, weight=1)
            ctk.CTkLabel(card, text=f"{icon}  {label}",
                         font=("Arial", 11), text_color=SUBTEXT
                         ).pack(anchor="w", padx=14, pady=(12, 2))
            lbl = ctk.CTkLabel(card, text="—",
                               font=("Arial", 22, "bold"), text_color=color)
            lbl.pack(anchor="w", padx=14, pady=(0, 12))
            self._kpi_labels[key] = lbl

        # ── Tabs ─────────────────────────────────────────────────────────────
        self.tabs = ctk.CTkTabview(
            container,
            fg_color=CARD, corner_radius=12,
            segmented_button_fg_color="#1E2130",
            segmented_button_selected_color=ACCENT,
            segmented_button_selected_hover_color="#2EBF7A",
            segmented_button_unselected_color="#1E2130",
            segmented_button_unselected_hover_color="#252836",
            text_color=TEXT, text_color_disabled=SUBTEXT,
        )
        self.tabs.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        for tab in ["📋  Stock General", "🗓  Lotes y Vencimientos", "⚠  Stock Bajo",
                    "🔧  Ajustes", "📜  Historial Ajustes"]:
            self.tabs.add(tab)

        self._build_tab_general(self.tabs.tab("📋  Stock General"))
        self._build_tab_lotes(self.tabs.tab("🗓  Lotes y Vencimientos"))
        self._build_tab_stock_bajo(self.tabs.tab("⚠  Stock Bajo"))
        self._build_tab_ajustes(self.tabs.tab("🔧  Ajustes"))
        self._build_tab_historial(self.tabs.tab("📜  Historial Ajustes"))

        # Cargar datos después de que la UI esté completamente renderizada
        container.after(100, self._refresh_all)

    # ═══════════════════════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════════════════════

    def _lf(self, parent, label: str, col: int, row: int = 0, padx=(0, 10)):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=row, column=col, padx=padx, pady=(0, 10), sticky="ew")
        ctk.CTkLabel(f, text=label, font=("Arial", 11),
                     text_color=SUBTEXT).pack(anchor="w")
        entry = ctk.CTkEntry(f, fg_color=INPUT_BG, border_color=INPUT_BORDER,
                             text_color=TEXT, font=("Arial", 12), height=36)
        entry.pack(fill="x", pady=(3, 0))
        return entry

    # ═══════════════════════════════════════════════════════════════════════
    # TAB 1 — STOCK GENERAL
    # ═══════════════════════════════════════════════════════════════════════

    def _build_tab_general(self, parent):
        # Barra de búsqueda y filtro categoría
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.pack(fill="x", padx=4, pady=(10, 6))

        self._search_entry = ctk.CTkEntry(
            bar, placeholder_text="🔍  Buscar producto...",
            fg_color=INPUT_BG, border_color=INPUT_BORDER,
            text_color=TEXT, font=("Arial", 12), height=36, width=320)
        self._search_entry.pack(side="left")
        self._search_entry.bind("<KeyRelease>", self._on_search)

        ctk.CTkLabel(bar, text="Categoría:", font=("Arial", 11),
                     text_color=SUBTEXT).pack(side="left", padx=(16, 4))
        self._cat_var = ctk.StringVar(value="Todas")
        self._cat_menu = ctk.CTkOptionMenu(
            bar, variable=self._cat_var,
            values=["Todas"],
            fg_color=INPUT_BG, button_color="#2A2D3A",
            button_hover_color="#3A3D52", dropdown_fg_color=CARD,
            dropdown_hover_color="#1A2E22", text_color=TEXT,
            font=("Arial", 12), height=36, width=160,
            dynamic_resizing=False,
            command=lambda _: self._load_general(),
        )
        self._cat_menu.pack(side="left")

        # Tabla — tk.Frame nativo como contenedor (fix Windows para colores)
        import tkinter as tk
        tree_outer = ctk.CTkFrame(parent, fg_color="#1A1D27", corner_radius=8,
                                  border_width=1, border_color=CARD_BORDER)
        tree_outer.pack(fill="both", expand=True, padx=4, pady=(0, 4))

        tree_frame = tk.Frame(tree_outer, bg="#1A1D27", bd=0, highlightthickness=0)
        tree_frame.pack(fill="both", expand=True, padx=1, pady=1)
        self._tree_frame_ref = tree_frame

        cols = ("id", "Producto", "Categoría", "Stock", "Mín",
                "Estado", "Precio", "Costo", "Lotes Activos")
        style = _tree_style("InvG")
        self._tree_gen = ttk.Treeview(tree_frame, columns=cols, show="headings",
                                      style=style, selectmode="browse")
        widths = {"id": 50, "Producto": 230, "Categoría": 120, "Stock": 70,
                  "Mín": 60, "Estado": 100, "Precio": 100, "Costo": 100,
                  "Lotes Activos": 90}
        for c in cols:
            self._tree_gen.heading(c, text=c, anchor="w")
            self._tree_gen.column(c, width=widths.get(c, 100), anchor="w",
                                  stretch=(c == "Producto"))

        # Tags con background explícito — Windows respeta tags aunque ignore Style
        self._tree_gen.tag_configure("ok",      foreground="#FFFFFF",  background="#1A1D27")
        self._tree_gen.tag_configure("low",     foreground="#FFA94D",  background="#1A1D27")
        self._tree_gen.tag_configure("agotado", foreground="#EF4444",  background="#1A1D27")
        self._tree_gen.tag_configure("row_bg",  background="#1A1D27")

        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree_gen.yview)
        self._tree_gen.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._tree_gen.pack(side="left", fill="both", expand=True)

        self._tree_gen.bind("<<TreeviewSelect>>", self._on_gen_select)

        # Windows fix: aplicar colores después de que el widget esté renderizado
        def _force_tree_bg():
            try:
                sty = self._tree_gen["style"]
                self._tree_gen.tk.call("ttk::style", "configure", sty,
                                       "-background",      "#1A1D27")
                self._tree_gen.tk.call("ttk::style", "configure", sty,
                                       "-fieldbackground", "#1A1D27")
                self._tree_gen.tk.call("ttk::style", "configure", sty,
                                       "-foreground",      "#FFFFFF")
                # Forzar redibujado
                self._tree_gen.update_idletasks()
            except Exception:
                pass
        self._tree_gen.after(200, _force_tree_bg)

        # Leyenda
        leg = ctk.CTkFrame(parent, fg_color="transparent")
        leg.pack(anchor="w", padx=6, pady=(2, 0))
        for color, txt in [(ACCENT, "● Stock normal"), (WARNING, "● Stock bajo"), (DANGER, "● Agotado")]:
            ctk.CTkLabel(leg, text=txt, font=("Arial", 10),
                         text_color=color).pack(side="left", padx=(0, 12))

    def _on_search(self, event=None):
        self._search_q = self._search_entry.get().strip()
        self._load_general()

    def _on_gen_select(self, event=None):
        sel = self._tree_gen.selection()
        if not sel:
            return
        vals = self._tree_gen.item(sel[0], "values")
        self._sel_product_id   = int(vals[0])
        self._sel_product_name = vals[1]
        self._adj_prod_lbl.configure(
            text=f"Producto seleccionado:  {self._sel_product_name}")
        self._load_lots_for_adjustment()
        # Ir a la pestaña de ajustes automáticamente
        self.tabs.set("🔧  Ajustes")

    def _load_general(self):
        for row in self._tree_gen.get_children():
            self._tree_gen.delete(row)

        cat_filter = self._cat_var.get()
        search     = self._search_q.lower().strip()

        try:
            cy = config.load()["billing"].get("currency", "RD$")
        except Exception:
            cy = "RD$"

        try:
            conn = create_connection()
            cur  = conn.cursor()
            cur.execute("""
                SELECT
                    p.id,
                    p.name,
                    IFNULL(p.category, 'General') AS category,
                    CAST(COALESCE(SUM(CASE WHEN l.status='activo'
                                          THEN l.quantity_available
                                          ELSE 0 END), 0) AS SIGNED) AS stock_total,
                    IFNULL(p.min_stock, 0) AS min_stock,
                    IFNULL(p.price, 0)     AS price,
                    IFNULL(p.cost,  0)     AS cost,
                    COUNT(CASE WHEN l.status='activo' AND l.quantity_available > 0
                               THEN 1 END) AS lotes_activos
                FROM products p
                LEFT JOIN lots l ON l.product_id = p.id
                GROUP BY p.id, p.name, p.category, p.min_stock, p.price, p.cost
                ORDER BY p.name
            """)
            rows = cur.fetchall()
            conn.close()
        except Exception as e:
            messagebox.showerror("Error BD", str(e))
            return

        cats = sorted({str(r[2]) for r in rows if r[2]})
        self._cat_menu.configure(values=["Todas"] + cats)

        total_prods = 0
        stock_bajo  = 0
        agotados    = 0
        valor_total = 0.0

        for row in rows:
            pid           = int(row[0])
            name          = str(row[1] or "Sin nombre")
            cat           = str(row[2] or "General")
            stock         = int(row[3] or 0)
            min_stk       = int(row[4] or 0)
            price         = float(row[5] or 0)
            cost          = float(row[6] or 0)
            lotes_activos = int(row[7] or 0)

            if cat_filter != "Todas" and cat != cat_filter:
                continue
            if search and search not in name.lower():
                continue

            if stock == 0:
                estado = "❌ Agotado"
                tag    = "agotado"
                agotados += 1
            elif min_stk > 0 and stock <= min_stk:
                estado = "⚠ Stock Bajo"
                tag    = "low"
                stock_bajo += 1
            else:
                estado = "✅ Normal"
                tag    = "ok"

            valor_total += stock * cost
            total_prods += 1

            self._tree_gen.insert("", "end", tags=(tag,), values=(
                pid, name, cat, stock, min_stk,
                estado,
                f"{cy} {price:,.2f}",
                f"{cy} {cost:,.2f}",
                lotes_activos,
            ))

        self._kpi_labels["total_productos"].configure(text=str(total_prods))
        self._kpi_labels["stock_bajo"].configure(text=str(stock_bajo))
        self._kpi_labels["agotados"].configure(text=str(agotados))
        self._kpi_labels["valor_inventario"].configure(
            text=f"RD$ {valor_total:,.0f}")

    # ═══════════════════════════════════════════════════════════════════════
    # TAB — LOTES Y VENCIMIENTOS
    # ═══════════════════════════════════════════════════════════════════════
    # Vista consolidada de TODOS los lotes activos con existencia, para ver
    # de un vistazo qué se tiene y cuándo vence, sin salir de Inventario.

    def _build_tab_lotes(self, parent):
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.pack(fill="x", padx=4, pady=(10, 6))

        self._lot_search_entry = ctk.CTkEntry(
            bar, placeholder_text="🔍  Buscar producto o N° de lote...",
            fg_color=INPUT_BG, border_color=INPUT_BORDER,
            text_color=TEXT, font=("Arial", 12), height=36, width=280)
        self._lot_search_entry.pack(side="left")
        self._lot_search_entry.bind("<KeyRelease>", lambda e: self._load_lotes_tab())

        self._lot_exp_only_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            bar, text="Solo próximos a vencer / vencidos",
            variable=self._lot_exp_only_var, fg_color=ACCENT,
            hover_color="#2EBF7A", checkmark_color="#0F1117",
            font=("Arial", 12), text_color=TEXT,
            command=self._load_lotes_tab
        ).pack(side="left", padx=(14, 0))

        ctk.CTkButton(bar, text="📥 Exportar Excel", width=140, height=34,
                      corner_radius=8, fg_color="#1A2E22",
                      hover_color="#2EBF7A", text_color=ACCENT,
                      font=("Arial", 12), command=self._export_lotes_tab
                      ).pack(side="right")

        cols = ("Producto", "N° Lote", "Disponible", "Vencimiento", "Días", "Proveedor", "Estado")
        style = _tree_style("InvLots")
        self._tree_lotes = ttk.Treeview(parent, columns=cols, show="headings",
                                        style=style, selectmode="none")
        widths = {"Producto": 210, "N° Lote": 140, "Disponible": 90,
                  "Vencimiento": 110, "Días": 90, "Proveedor": 150, "Estado": 100}
        for c in cols:
            self._tree_lotes.heading(c, text=c, anchor="w")
            self._tree_lotes.column(c, width=widths.get(c, 100), anchor="w",
                                    stretch=(c == "Producto"))

        self._tree_lotes.tag_configure("vencido", foreground=DANGER)
        self._tree_lotes.tag_configure("por_vencer", foreground=WARNING)
        self._tree_lotes.tag_configure("ok", foreground="#FFFFFF")

        sb = ttk.Scrollbar(parent, orient="vertical", command=self._tree_lotes.yview)
        self._tree_lotes.configure(yscrollcommand=sb.set)
        self._tree_lotes.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        sb.pack(side="right", fill="y")

        leg = ctk.CTkFrame(parent, fg_color="transparent")
        leg.pack(anchor="w", padx=6, pady=(2, 4))
        for color, txt in [(DANGER, "● Vencido"), (WARNING, "● Próximo a vencer"),
                            ("#FFFFFF", "● Vigente")]:
            ctk.CTkLabel(leg, text=txt, font=("Arial", 10),
                         text_color=color).pack(side="left", padx=(0, 12))

    def _load_lotes_tab(self):
        for row in self._tree_lotes.get_children():
            self._tree_lotes.delete(row)

        search   = self._lot_search_entry.get().strip().lower() if hasattr(self, "_lot_search_entry") else ""
        exp_only = self._lot_exp_only_var.get() if hasattr(self, "_lot_exp_only_var") else False
        alert_days = config.load().get("inventory", {}).get("expiry_alert_days", 30)

        try:
            with create_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT p.name, l.lot_number, l.quantity_available, l.expiry_date,
                           IFNULL(s.name, '—')
                    FROM lots l
                    JOIN products p ON p.id = l.product_id
                    LEFT JOIN suppliers s ON s.id = l.supplier_id
                    WHERE l.status = 'activo' AND l.quantity_available > 0
                    ORDER BY l.expiry_date IS NULL, l.expiry_date ASC, p.name ASC
                """)
                rows = cur.fetchall()
        except Exception as e:
            messagebox.showerror("Error BD", str(e))
            return

        today = date.today()
        for name, lot_num, qty, exp, supplier in rows:
            if search and search not in str(name).lower() and search not in str(lot_num).lower():
                continue

            if exp is not None:
                exp_date = exp if hasattr(exp, "year") else datetime.strptime(str(exp)[:10], "%Y-%m-%d").date()
                dias = (exp_date - today).days
                if dias < 0:
                    estado, tag = "❌ Vencido", "vencido"
                elif dias <= alert_days:
                    estado, tag = "⚠ Por vencer", "por_vencer"
                else:
                    estado, tag = "✔ Vigente", "ok"
                dias_txt = str(dias)
            else:
                dias_txt, estado, tag = "—", "— Sin fecha", "ok"

            if exp_only and tag not in ("vencido", "por_vencer"):
                continue

            self._tree_lotes.insert("", "end", tags=(tag,), values=(
                name, lot_num, int(qty or 0), _fmt_date(exp), dias_txt, supplier, estado
            ))

    def _export_lotes_tab(self):
        rows = [self._tree_lotes.item(i, "values") for i in self._tree_lotes.get_children()]
        if not rows:
            messagebox.showwarning("Sin datos", "No hay lotes para exportar.")
            return
        export_to_excel(
            rows,
            ["Producto", "N° Lote", "Disponible", "Vencimiento", "Días", "Proveedor", "Estado"],
            f"lotes_vencimientos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )

    # ═══════════════════════════════════════════════════════════════════════
    # TAB 2 — STOCK BAJO
    # ═══════════════════════════════════════════════════════════════════════

    def _build_tab_stock_bajo(self, parent):
        ctk.CTkLabel(
            parent,
            text="Productos cuyo stock actual es menor o igual al stock mínimo configurado.",
            font=("Arial", 11), text_color=SUBTEXT
        ).pack(anchor="w", padx=4, pady=(10, 6))

        cols = ("Producto", "Categoría", "Stock Actual", "Stock Mínimo",
                "Déficit", "Precio", "Proveedor")
        style = _tree_style("InvLow")
        self._tree_low = ttk.Treeview(parent, columns=cols, show="headings",
                                      style=style, selectmode="none")
        widths = {"Producto": 220, "Categoría": 120, "Stock Actual": 90,
                  "Stock Mínimo": 90, "Déficit": 80, "Precio": 100, "Proveedor": 160}
        for c in cols:
            self._tree_low.heading(c, text=c, anchor="w")
            self._tree_low.column(c, width=widths.get(c, 100), anchor="w",
                                  stretch=(c == "Producto"))

        self._tree_low.tag_configure("agotado", foreground=DANGER)
        self._tree_low.tag_configure("bajo",    foreground=WARNING)

        sb = ttk.Scrollbar(parent, orient="vertical", command=self._tree_low.yview)
        self._tree_low.configure(yscrollcommand=sb.set)
        self._tree_low.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        sb.pack(side="right", fill="y")

        ctk.CTkButton(
            parent, text="📥 Exportar Excel", height=34, width=140,
            corner_radius=8, fg_color="#1A2E22",
            hover_color="#2EBF7A", text_color=ACCENT,
            font=("Arial", 12), command=self._export_stock_bajo
        ).pack(anchor="w", padx=4, pady=(4, 0))

    def _load_stock_bajo(self):
        for row in self._tree_low.get_children():
            self._tree_low.delete(row)

        try:
            with create_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT p.name, p.category,
                           COALESCE(SUM(l.quantity_available), 0) AS stock,
                           p.min_stock, p.price,
                           IFNULL(s.name, '—')
                    FROM products p
                    LEFT JOIN lots l
                        ON l.product_id = p.id AND l.status = 'activo'
                    LEFT JOIN suppliers s ON s.id = p.supplier_id
                    GROUP BY p.id, p.name, p.category,
                             p.min_stock, p.price, s.name
                    HAVING stock <= p.min_stock
                    ORDER BY stock ASC
                """)
                rows = cur.fetchall()
        except Exception as e:
            messagebox.showerror("Error BD", str(e))
            return

        cy = config.load()["billing"].get("currency", "RD$")
        for name, cat, stock, min_stk, price, supplier in rows:
            stock   = int(stock or 0)
            min_stk = int(min_stk or 0)
            deficit = min_stk - stock
            tag = "agotado" if stock == 0 else "bajo"
            self._tree_low.insert("", "end", tags=(tag,), values=(
                name, cat or "—", stock, min_stk, deficit,
                f"{cy} {float(price or 0):,.2f}", supplier
            ))

    def _export_stock_bajo(self):
        rows = [self._tree_low.item(i, "values")
                for i in self._tree_low.get_children()]
        if not rows:
            messagebox.showwarning("Sin datos", "No hay productos con stock bajo.")
            return
        export_to_excel(
            rows,
            ["Producto", "Categoría", "Stock Actual", "Stock Mínimo",
             "Déficit", "Precio", "Proveedor"],
            f"stock_bajo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )

    # ═══════════════════════════════════════════════════════════════════════
    # TAB 3 — AJUSTES MANUALES
    # ═══════════════════════════════════════════════════════════════════════

    def _build_tab_ajustes(self, parent):
        ctk.CTkLabel(
            parent,
            text="Selecciona un producto en la pestaña 'Stock General' — se abrirá aquí automáticamente.",
            font=("Arial", 11), text_color=SUBTEXT
        ).pack(anchor="w", padx=4, pady=(10, 4))

        # Producto seleccionado
        self._adj_prod_lbl = ctk.CTkLabel(
            parent, text="Producto seleccionado:  (ninguno — ve a Stock General y haz clic en uno)",
            font=("Arial", 12, "bold"), text_color=CYAN)
        self._adj_prod_lbl.pack(anchor="w", padx=4, pady=(0, 10))

        # Formulario
        card = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=12,
                            border_width=1, border_color=CARD_BORDER)
        card.pack(fill="x", padx=4, pady=(0, 10))
        ctk.CTkLabel(card, text="Datos del Ajuste",
                     font=("Arial", 12, "bold"), text_color=SUBTEXT
                     ).pack(anchor="w", padx=16, pady=(14, 2))
        ctk.CTkFrame(card, height=1, fg_color=CARD_BORDER
                     ).pack(fill="x", padx=16, pady=(0, 10))

        row1 = ctk.CTkFrame(card, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=(0, 8))
        row1.columnconfigure((0, 1, 2, 3), weight=1)

        # Lote
        lf_lot = ctk.CTkFrame(row1, fg_color="transparent")
        lf_lot.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        ctk.CTkLabel(lf_lot, text="Lote a ajustar", font=("Arial", 11),
                     text_color=SUBTEXT).pack(anchor="w")
        self._adj_lot_var = ctk.StringVar(value="— selecciona producto primero —")
        self._adj_lot_menu = ctk.CTkOptionMenu(
            lf_lot, variable=self._adj_lot_var,
            values=["— selecciona producto primero —"],
            fg_color=INPUT_BG, button_color="#2A2D3A",
            button_hover_color="#3A3D52", dropdown_fg_color=CARD,
            dropdown_hover_color="#1A2E22", text_color=TEXT,
            font=("Arial", 12), height=36, dynamic_resizing=False,
        )
        self._adj_lot_menu.pack(fill="x", pady=(3, 0))

        # Tipo
        lf_type = ctk.CTkFrame(row1, fg_color="transparent")
        lf_type.grid(row=0, column=1, padx=(0, 10), sticky="ew")
        ctk.CTkLabel(lf_type, text="Tipo de ajuste", font=("Arial", 11),
                     text_color=SUBTEXT).pack(anchor="w")
        self._adj_type_var = ctk.StringVar(value="ajuste")
        ctk.CTkOptionMenu(
            lf_type, variable=self._adj_type_var,
            values=["ajuste", "entrada", "salida"],
            fg_color=INPUT_BG, button_color="#2A2D3A",
            button_hover_color="#3A3D52", dropdown_fg_color=CARD,
            dropdown_hover_color="#1A2E22", text_color=TEXT,
            font=("Arial", 12), height=36, dynamic_resizing=False,
        ).pack(fill="x", pady=(3, 0))

        # Cantidad
        self._adj_qty_entry = self._lf(row1, "Cantidad", 2)

        # Motivo
        lf_reason = ctk.CTkFrame(row1, fg_color="transparent")
        lf_reason.grid(row=0, column=3, sticky="ew")
        ctk.CTkLabel(lf_reason, text="Motivo", font=("Arial", 11),
                     text_color=SUBTEXT).pack(anchor="w")
        self._adj_reason_var = ctk.StringVar(value=ADJUSTMENT_REASONS[0])
        ctk.CTkOptionMenu(
            lf_reason, variable=self._adj_reason_var,
            values=ADJUSTMENT_REASONS,
            fg_color=INPUT_BG, button_color="#2A2D3A",
            button_hover_color="#3A3D52", dropdown_fg_color=CARD,
            dropdown_hover_color="#1A2E22", text_color=TEXT,
            font=("Arial", 12), height=36, dynamic_resizing=False,
        ).pack(fill="x", pady=(3, 0))

        # Info del lote seleccionado
        self._adj_stock_lbl = ctk.CTkLabel(
            card, text="", font=("Arial", 11), text_color=SUBTEXT)
        self._adj_stock_lbl.pack(anchor="w", padx=16, pady=(0, 6))

        # Botones
        btns = ctk.CTkFrame(card, fg_color="transparent")
        btns.pack(anchor="w", padx=16, pady=(0, 14))
        ctk.CTkButton(
            btns, text="✔ Aplicar Ajuste", command=self._apply_adjustment,
            fg_color=ACCENT, hover_color="#2EBF7A", text_color="#0F1117",
            font=("Arial", 12, "bold"), height=36, corner_radius=8, width=160,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            btns, text="✖ Limpiar", command=self._clear_adjustment,
            fg_color=INPUT_BG, hover_color="#2E3148", text_color=SUBTEXT,
            font=("Arial", 12), height=36, corner_radius=8, width=100,
        ).pack(side="left")

        self._adj_lot_var.trace_add("write", self._on_lot_selected)

    def _load_lots_for_adjustment(self):
        if not self._sel_product_id:
            return
        try:
            with create_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT id, lot_number, quantity_available, expiry_date
                    FROM lots
                    WHERE product_id = %s AND status = 'activo'
                    ORDER BY expiry_date ASC
                """, (self._sel_product_id,))
                rows = cur.fetchall()
        except Exception as e:
            messagebox.showerror("Error BD", str(e))
            return

        self._lot_map = {}
        if not rows:
            self._adj_lot_menu.configure(values=["(sin lotes activos)"])
            self._adj_lot_var.set("(sin lotes activos)")
            self._adj_stock_lbl.configure(text="Este producto no tiene lotes activos. Registra uno en el módulo Lotes.")
            return

        options = []
        for lot_id, lot_num, qty, exp in rows:
            label = f"{lot_num}  |  Disp: {int(qty or 0)}  |  Venc: {_fmt_date(exp)}"
            options.append(label)
            self._lot_map[label] = (lot_id, int(qty or 0))

        self._adj_lot_menu.configure(values=options)
        self._adj_lot_var.set(options[0])

    def _on_lot_selected(self, *_):
        key = self._adj_lot_var.get()
        if key in self._lot_map:
            _, qty = self._lot_map[key]
            self._adj_stock_lbl.configure(
                text=f"Disponible en este lote: {qty} unidades")
        else:
            self._adj_stock_lbl.configure(text="")

    def _apply_adjustment(self):
        if not self._sel_product_id:
            messagebox.showwarning("Sin producto",
                                   "Selecciona primero un producto en la pestaña 'Stock General'.")
            return

        lot_key = self._adj_lot_var.get()
        if lot_key not in self._lot_map:
            messagebox.showwarning("Sin lote", "Selecciona un lote válido.")
            return

        lot_id, stock_actual = self._lot_map[lot_key]
        adj_type = self._adj_type_var.get()
        reason   = self._adj_reason_var.get()

        qty_str = self._adj_qty_entry.get().strip()
        if not qty_str.isdigit() or int(qty_str) <= 0:
            messagebox.showerror("Cantidad inválida", "Ingresa una cantidad entera mayor a 0.")
            return
        qty = int(qty_str)

        if adj_type == "salida" and qty > stock_actual:
            messagebox.showerror("Stock insuficiente",
                                 f"El lote solo tiene {stock_actual} unidades disponibles.")
            return

        confirm = messagebox.askyesno(
            "Confirmar ajuste",
            f"¿Aplicar {adj_type.upper()} de {qty} unidades\n"
            f"al lote: {lot_key.split('|')[0].strip()}?\n\n"
            f"Motivo: {reason}"
        )
        if not confirm:
            return

        try:
            u = session.current_user
            username = u[1] if isinstance(u, tuple) and len(u) > 1 else str(u or "sistema")

            with create_connection() as conn:
                cur = conn.cursor()

                if adj_type == "entrada":
                    nuevo_disp = stock_actual + qty
                elif adj_type == "salida":
                    nuevo_disp = stock_actual - qty
                else:  # ajuste: establece la cantidad exacta
                    nuevo_disp = qty

                nuevo_status = "agotado" if nuevo_disp == 0 else "activo"

                cur.execute("""
                    UPDATE lots
                    SET quantity_available = %s, status = %s
                    WHERE id = %s
                """, (nuevo_disp, nuevo_status, lot_id))

                # Sincronizar products.stock (respaldo si no hay trigger activo)
                cur.execute("""
                    UPDATE products
                    SET stock = (
                        SELECT COALESCE(SUM(quantity_available), 0)
                        FROM lots
                        WHERE product_id = %s AND status = 'activo'
                    )
                    WHERE id = %s
                """, (self._sel_product_id, self._sel_product_id))

                # Registrar en inventory_adjustments
                cur.execute("""
                    INSERT INTO inventory_adjustments
                        (lot_id, product_id, type, quantity, reason, username, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW())
                """, (lot_id, self._sel_product_id, adj_type, qty, reason, username))

            audit(
                f"AJUSTE_{adj_type.upper()}",
                f"Producto #{self._sel_product_id} '{self._sel_product_name}' | "
                f"Lote ID {lot_id} | Cantidad: {qty} | Motivo: {reason}",
                module="inventario"
            )
            log_stock_change(self._sel_product_id, self._sel_product_name,
                             stock_actual, nuevo_disp, f"Ajuste manual: {reason}")

            messagebox.showinfo("Ajuste aplicado",
                                f"Ajuste {adj_type} de {qty} unidades aplicado.\n"
                                f"Stock anterior: {stock_actual}  →  Nuevo: {nuevo_disp}")
            self._clear_adjustment()
            self._refresh_all()

        except Exception as e:
            messagebox.showerror("Error al ajustar", str(e))

    def _clear_adjustment(self):
        self._adj_qty_entry.delete(0, "end")
        self._adj_type_var.set("ajuste")
        self._adj_reason_var.set(ADJUSTMENT_REASONS[0])
        self._adj_stock_lbl.configure(text="")

    # ═══════════════════════════════════════════════════════════════════════
    # TAB 4 — HISTORIAL DE AJUSTES
    # ═══════════════════════════════════════════════════════════════════════

    def _build_tab_historial(self, parent):
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.pack(fill="x", padx=4, pady=(10, 6))

        ctk.CTkLabel(bar, text="Tipo:", font=("Arial", 11),
                     text_color=SUBTEXT).pack(side="left", padx=(0, 6))
        self._hist_type_var = ctk.StringVar(value="Todos")
        ctk.CTkOptionMenu(
            bar, variable=self._hist_type_var,
            values=["Todos", "entrada", "salida", "ajuste"],
            fg_color=INPUT_BG, button_color="#2A2D3A",
            button_hover_color="#3A3D52", dropdown_fg_color=CARD,
            dropdown_hover_color="#1A2E22", text_color=TEXT,
            font=("Arial", 12), height=34, width=120, dynamic_resizing=False,
            command=lambda _: self._load_historial(),
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(bar, text="🔄 Actualizar", width=110, height=34,
                      corner_radius=8, fg_color=INPUT_BG,
                      hover_color="#2E3148", text_color=SUBTEXT,
                      font=("Arial", 12), command=self._load_historial,
                      ).pack(side="left")

        cols = ("Fecha", "Producto", "Lote ID", "Tipo", "Cantidad", "Motivo", "Usuario")
        style = _tree_style("InvHist")
        self._tree_hist = ttk.Treeview(parent, columns=cols, show="headings",
                                       style=style, selectmode="none")
        widths = {"Fecha": 140, "Producto": 210, "Lote ID": 70,
                  "Tipo": 80, "Cantidad": 80, "Motivo": 200, "Usuario": 120}
        for c in cols:
            self._tree_hist.heading(c, text=c, anchor="w")
            self._tree_hist.column(c, width=widths.get(c, 100), anchor="w",
                                   stretch=(c == "Producto"))

        self._tree_hist.tag_configure("entrada", foreground=ACCENT)
        self._tree_hist.tag_configure("salida",  foreground=DANGER)
        self._tree_hist.tag_configure("ajuste",  foreground=CYAN)

        sb = ttk.Scrollbar(parent, orient="vertical", command=self._tree_hist.yview)
        self._tree_hist.configure(yscrollcommand=sb.set)
        self._tree_hist.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        sb.pack(side="right", fill="y")

    def _load_historial(self):
        for row in self._tree_hist.get_children():
            self._tree_hist.delete(row)

        tipo_filter = self._hist_type_var.get()
        try:
            with create_connection() as conn:
                cur = conn.cursor()
                sql = """
                    SELECT a.timestamp, p.name, a.lot_id,
                           a.type, a.quantity, a.reason, a.username
                    FROM inventory_adjustments a
                    JOIN products p ON p.id = a.product_id
                """
                params = []
                if tipo_filter != "Todos":
                    sql += " WHERE a.type = %s"
                    params.append(tipo_filter)
                sql += " ORDER BY a.timestamp DESC LIMIT 300"
                cur.execute(sql, params)

                for ts, prod, lot_id, tipo, qty, reason, usr in cur.fetchall():
                    ts_fmt = (ts.strftime("%d/%m/%Y %H:%M")
                              if hasattr(ts, "strftime") else str(ts))
                    self._tree_hist.insert("", "end", tags=(tipo,), values=(
                        ts_fmt, prod, lot_id, tipo, qty, reason or "—", usr or "—"
                    ))
        except Exception as e:
            messagebox.showerror("Error BD", str(e))

    # ═══════════════════════════════════════════════════════════════════════
    # REFRESH GLOBAL + EXPORTACIÓN
    # ═══════════════════════════════════════════════════════════════════════

    def _refresh_all(self):
        self._load_general()
        self._load_lotes_tab()
        self._load_stock_bajo()
        self._load_historial()

    def _export_excel(self):
        try:
            with create_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT p.id, p.name, p.category, p.active_ingredient,
                           p.presentation, p.laboratory,
                           COALESCE(SUM(l.quantity_available), 0) AS stock,
                           p.min_stock, p.price, p.cost,
                           COUNT(CASE WHEN l.status='activo' AND l.quantity_available>0
                                      THEN 1 END) AS lotes
                    FROM products p
                    LEFT JOIN lots l ON l.product_id = p.id
                    GROUP BY p.id, p.name, p.category, p.active_ingredient,
                             p.presentation, p.laboratory,
                             p.min_stock, p.price, p.cost
                    ORDER BY p.name
                """)
                rows = cur.fetchall()

            data = [
                (r[0], r[1], r[2], r[3], r[4], r[5],
                 int(r[6] or 0), int(r[7] or 0),
                 float(r[8] or 0), float(r[9] or 0),
                 int(r[10] or 0))
                for r in rows
            ]
            export_to_excel(
                data,
                ["ID", "Producto", "Categoría", "Principio Activo",
                 "Presentación", "Laboratorio", "Stock", "Stock Mín",
                 "Precio", "Costo", "Lotes Activos"],
                f"inventario_general_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            )
        except Exception as e:
            messagebox.showerror("Error exportando", str(e))
