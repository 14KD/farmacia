import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime, date
from database.connection import create_connection
from exports.excel_exporter import export_to_excel
from auth import session

BG           = "#0F1117"
CARD         = "#1A1D27"
CARD_BORDER  = "#252836"
ACCENT       = "#3DD68C"
CYAN         = "#22D3EE"
TEXT         = "#FFFFFF"
SUBTEXT      = "#8B8FA8"
DANGER       = "#EF4444"
DANGER_H     = "#DC2626"
WARNING      = "#FFA94D"
INPUT_BG     = "#23263A"
INPUT_BORDER = "#2E3148"

CATEGORIES = ["General", "Analgésicos", "Antibióticos", "Antiinflamatorios",
               "Vitaminas", "Antihistamínicos", "Cardiovascular", "Diabetes",
               "Dermatología", "Oftalmología", "Otros"]


class ProductsUI:

    def __init__(self, parent):
        self.parent = parent
        self._selected_id = None
        self._page = 0
        self._page_size = 20
        self._all_products = []
        self.is_admin = session.current_role in ("admin", "Administrador")

        container = ctk.CTkFrame(parent, fg_color=BG, corner_radius=0)
        container.pack(fill="both", expand=True)

        # ── Encabezado ──
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 0))
        ctk.CTkLabel(header, text="📦  Inventario de Productos",
                     font=("Arial", 22, "bold"), text_color=TEXT).pack(side="left")
        ctk.CTkFrame(container, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=20, pady=(10, 16))

        # ── Formulario ──
        form_card = ctk.CTkFrame(container, fg_color=CARD, corner_radius=12,
                                  border_width=1, border_color=CARD_BORDER)
        form_card.pack(fill="x", padx=20, pady=(0, 12))

        ctk.CTkLabel(form_card, text="Datos del Producto",
                     font=("Arial", 12, "bold"), text_color=SUBTEXT).pack(anchor="w", padx=16, pady=(14, 2))
        ctk.CTkFrame(form_card, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=16, pady=(0, 12))

        # Fila 1: Nombre, Precio, Costo, Stock
        row1 = ctk.CTkFrame(form_card, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=(0, 8))
        row1.columnconfigure((0, 1, 2, 3), weight=1)

        self.name_entry  = self._field(row1, "💊  Nombre del Producto", 0)
        self.price_entry = self._field(row1, "💲  Precio Venta",        1)
        self.cost_entry  = self._field(row1, "📉  Costo",               2)
        self.stock_entry = self._field(row1, "📦  Stock",               3)

        # Fila 2: Categoría, Vencimiento, Proveedor
        row2 = ctk.CTkFrame(form_card, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=(0, 10))
        row2.columnconfigure((0, 1, 2), weight=1)

        # Categoría (dropdown)
        cat_frame = ctk.CTkFrame(row2, fg_color=INPUT_BG, corner_radius=8,
                                  border_width=1, border_color=INPUT_BORDER)
        cat_frame.grid(row=0, column=0, padx=(0, 10), sticky="ew", ipady=2)
        ctk.CTkLabel(cat_frame, text="🏷  Categoría", font=("Arial", 11),
                     text_color=SUBTEXT).pack(anchor="w", padx=10, pady=(6, 0))
        self.category_var = ctk.StringVar(value="General")
        ctk.CTkOptionMenu(cat_frame, values=CATEGORIES, variable=self.category_var,
                          fg_color="#1E2130", button_color="#2A2D3A",
                          button_hover_color="#3A3D52", dropdown_fg_color="#1A1D27",
                          dropdown_hover_color="#1A2E22", text_color=TEXT,
                          font=("Arial", 12), height=30).pack(fill="x", padx=8, pady=(2, 8))

        # Fecha de vencimiento
        self.expiry_entry = self._field(row2, "📅  Vencimiento (YYYY-MM-DD)", 1)

        # Proveedor (dropdown desde BD)
        sup_frame = ctk.CTkFrame(row2, fg_color=INPUT_BG, corner_radius=8,
                                  border_width=1, border_color=INPUT_BORDER)
        sup_frame.grid(row=0, column=2, padx=(0, 0), sticky="ew", ipady=2)
        ctk.CTkLabel(sup_frame, text="🏭  Proveedor", font=("Arial", 11),
                     text_color=SUBTEXT).pack(anchor="w", padx=10, pady=(6, 0))
        self.supplier_var = ctk.StringVar(value="Sin proveedor")
        self.supplier_menu = ctk.CTkOptionMenu(
            sup_frame, values=["Sin proveedor"], variable=self.supplier_var,
            fg_color="#1E2130", button_color="#2A2D3A",
            button_hover_color="#3A3D52", dropdown_fg_color="#1A1D27",
            dropdown_hover_color="#1A2E22", text_color=TEXT,
            font=("Arial", 12), height=30
        )
        self.supplier_menu.pack(fill="x", padx=8, pady=(2, 8))
        self._load_suppliers()

        # Buscador
        search_row = ctk.CTkFrame(form_card, fg_color="transparent")
        search_row.pack(fill="x", padx=16, pady=(0, 10))
        sf = ctk.CTkFrame(search_row, fg_color=INPUT_BG, corner_radius=8,
                           border_width=1, border_color=INPUT_BORDER)
        sf.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(sf, text="🔍", font=("Arial", 14), text_color=SUBTEXT, width=30).pack(side="left", padx=(8, 0))
        self.search_entry = ctk.CTkEntry(sf, placeholder_text="Buscar por nombre, categoría o ID...",
                                          border_width=0, fg_color="transparent", height=40,
                                          font=("Arial", 13), text_color=TEXT,
                                          placeholder_text_color="#555870")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(4, 8))
        self.search_entry.bind("<KeyRelease>", self.search_products)

        # Botones
        btn_row = ctk.CTkFrame(form_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 16))

        if self.is_admin:
            for text, fg, hov, tc, cmd in [
                ("＋  Agregar",    ACCENT,    "#2EBF7A", "#0F1117", self.add_product),
                ("✎  Actualizar", "#1A3A4A", "#1E6A9A", CYAN,      self.update_product),
                ("🗑  Eliminar",   "#2E1A1A", DANGER_H,  DANGER,    self.delete_product),
                ("↺  Limpiar",    INPUT_BG,  "#2E3148", SUBTEXT,   self.clear_fields),
                ("📊  Exportar",  "#1A3A2A", "#2EBF7A", ACCENT,    self.export_products),
            ]:
                ctk.CTkButton(btn_row, text=text, height=38, corner_radius=8,
                              fg_color=fg, hover_color=hov, text_color=tc,
                              font=("Arial", 12, "bold"), command=cmd).pack(side="left", padx=(0, 8))
        else:
            ctk.CTkLabel(btn_row, text="🔒  Solo lectura — contacte al administrador para modificar el inventario",
                         font=("Arial", 12), text_color="#FFA94D").pack(side="left")

        # Leyenda
        legend = ctk.CTkFrame(container, fg_color="transparent")
        legend.pack(fill="x", padx=20, pady=(0, 8))
        for color, label in [
            (ACCENT,  "Stock normal"),
            (WARNING, "Stock bajo (≤10)"),
            (DANGER,  "Sin stock / Vencido"),
        ]:
            ctk.CTkFrame(legend, width=10, height=10, corner_radius=5, fg_color=color).pack(side="left", padx=(0, 4))
            ctk.CTkLabel(legend, text=label, font=("Arial", 11), text_color=SUBTEXT).pack(side="left", padx=(0, 16))

        # ── Tabla ──
        table_card = ctk.CTkFrame(container, fg_color=CARD, corner_radius=12,
                                   border_width=1, border_color=CARD_BORDER)
        table_card.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        ctk.CTkLabel(table_card, text="Lista de Productos",
                     font=("Arial", 12, "bold"), text_color=SUBTEXT).pack(anchor="w", padx=16, pady=(14, 2))
        ctk.CTkFrame(table_card, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=16, pady=(0, 8))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("PRD.Treeview", background=CARD, foreground=TEXT,
                         fieldbackground=CARD, borderwidth=0, font=("Arial", 12), rowheight=34)
        style.configure("PRD.Treeview.Heading", background="#1E2130", foreground=SUBTEXT,
                         font=("Arial", 11, "bold"), borderwidth=0)
        style.map("PRD.Treeview", background=[("selected", "#1A2E22")], foreground=[("selected", ACCENT)])

        cols = ("ID", "Nombre", "Categoría", "Precio", "Costo", "Stock", "Vencimiento", "Estado")
        self.tree = ttk.Treeview(table_card, columns=cols, show="headings",
                                  height=14, style="PRD.Treeview")
        for col, w, anc in [
            ("ID",          55,  "center"),
            ("Nombre",      200, "w"),
            ("Categoría",   130, "w"),
            ("Precio",      90,  "e"),
            ("Costo",       90,  "e"),
            ("Stock",       70,  "center"),
            ("Vencimiento", 110, "center"),
            ("Estado",      130, "center"),
        ]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor=anc)

        self.tree.tag_configure("sin_stock",  foreground=DANGER)
        self.tree.tag_configure("vencido",    foreground=DANGER)
        self.tree.tag_configure("bajo_stock", foreground=WARNING)
        self.tree.tag_configure("ok_stock",   foreground=ACCENT)

        self.tree.pack(fill="both", expand=True, padx=16, pady=(0, 14))
        if self.is_admin:
            self.tree.bind("<<TreeviewSelect>>", self.select_product)

        self.load_products()

    def _field(self, parent, placeholder, col):
        frame = ctk.CTkFrame(parent, fg_color=INPUT_BG, corner_radius=8,
                              border_width=1, border_color=INPUT_BORDER)
        frame.grid(row=0, column=col, padx=(0, 10), sticky="ew", ipady=2)
        entry = ctk.CTkEntry(frame, placeholder_text=placeholder, border_width=0,
                              fg_color="transparent", height=42, font=("Arial", 13),
                              text_color=TEXT, placeholder_text_color="#555870")
        entry.pack(fill="x", padx=8)
        return entry

    def _load_suppliers(self):
        conn = create_connection(); cur = conn.cursor()
        cur.execute("SELECT id, name FROM suppliers ORDER BY name")
        self._suppliers = {row[1]: row[0] for row in cur.fetchall()}
        conn.close()
        options = ["Sin proveedor"] + list(self._suppliers.keys())
        self.supplier_menu.configure(values=options)

    def get_connection(self): return create_connection()

    def _get_status(self, stock, expiry):
        today = date.today().isoformat()
        if expiry and expiry <= today:
            return "vencido",    "⛔ Vencido"
        if stock == 0:
            return "sin_stock",  "⛔ Sin stock"
        if stock <= 10:
            return "bajo_stock", "⚠ Stock bajo"
        return "ok_stock", "✔ Normal"

    def _count_products(self, q=""):
        conn = self.get_connection(); cur = conn.cursor()
        if q:
            cur.execute("""SELECT COUNT(*) FROM products p
                           WHERE p.name LIKE ? OR p.category LIKE ? OR CAST(p.id AS TEXT) LIKE ?""",
                        (f"%{q}%", f"%{q}%", f"%{q}%"))
        else:
            cur.execute("SELECT COUNT(*) FROM products")
        return cur.fetchone()[0]

    def _fetch_page(self, q=""):
        offset = self._page * self._page_size
        conn = self.get_connection(); cur = conn.cursor()
        if q:
            cur.execute("""
                SELECT p.id, p.name, p.category, p.price, p.cost, p.stock,
                       p.expiry_date, s.name
                FROM products p LEFT JOIN suppliers s ON p.supplier_id = s.id
                WHERE p.name LIKE ? OR p.category LIKE ? OR CAST(p.id AS TEXT) LIKE ?
                ORDER BY p.name LIMIT ? OFFSET ?
            """, (f"%{q}%", f"%{q}%", f"%{q}%", self._page_size, offset))
        else:
            cur.execute("""
                SELECT p.id, p.name, p.category, p.price, p.cost, p.stock,
                       p.expiry_date, s.name
                FROM products p LEFT JOIN suppliers s ON p.supplier_id = s.id
                ORDER BY p.name LIMIT ? OFFSET ?
            """, (self._page_size, offset))
        return cur.fetchall()

    def load_products(self):
        self._page = 0
        self._search_q = ""
        self._render_page()

    def _render_page(self):
        q     = getattr(self, "_search_q", "")
        total = self._count_products(q)
        pages = max(1, -(-total // self._page_size))
        rows  = self._fetch_page(q)

        for i in self.tree.get_children(): self.tree.delete(i)
        for p in rows:
            tag, estado = self._get_status(p[5], p[6])
            expiry = p[6] or "—"
            self.tree.insert("", "end", tags=(tag,),
                             values=(p[0], p[1], p[2] or "General",
                                     f"${p[3]:,.2f}", f"${p[4]:,.2f}",
                                     p[5], expiry, estado))
        # Solo actualizar controles de paginación si ya existen
        if hasattr(self, "page_lbl"):
            self.page_lbl.configure(text=f"Página {self._page+1} de {pages}  ({total} productos)")
            self.prev_btn.configure(state="normal" if self._page > 0 else "disabled")
            self.next_btn.configure(state="normal" if self._page < pages-1 else "disabled")

    def _prev_page(self):
        if self._page > 0:
            self._page -= 1; self._render_page()

    def _next_page(self):
        q     = getattr(self, "_search_q", "")
        total = self._count_products(q)
        pages = max(1, -(-total // self._page_size))
        if self._page < pages - 1:
            self._page += 1; self._render_page()

    def search_products(self, event=None):
        self._search_q = self.search_entry.get().strip()
        self._page = 0
        self._render_page()

    def select_product(self, event):
        sel = self.tree.selection()
        if not sel: return
        v = self.tree.item(sel[0], "values")
        self._selected_id = v[0]
        self.clear_fields(keep_id=True)
        self.name_entry.insert(0, v[1])
        self.category_var.set(v[2])
        self.price_entry.insert(0, v[3].replace("$", "").replace(",", ""))
        self.cost_entry.insert(0, v[4].replace("$", "").replace(",", ""))
        self.stock_entry.insert(0, v[5])
        if v[6] != "—": self.expiry_entry.insert(0, v[6])

    def add_product(self):
        name  = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "El nombre es obligatorio."); return
        try:
            price  = float(self.price_entry.get() or 0)
            cost   = float(self.cost_entry.get()  or 0)
            stock  = int(self.stock_entry.get()   or 0)
            if price < 0 or cost < 0 or stock < 0: raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Precio, costo y stock deben ser números positivos."); return

        expiry   = self.expiry_entry.get().strip() or None
        category = self.category_var.get()
        sup_name = self.supplier_var.get()
        sup_id   = self._suppliers.get(sup_name)

        conn = self.get_connection(); cur = conn.cursor()
        cur.execute(
            "INSERT INTO products (name, category, stock, price, cost, expiry_date, supplier_id) VALUES (?,?,?,?,?,?,?)",
            (name, category, stock, price, cost, expiry, sup_id)
        )
        conn.commit(); conn.close()
        messagebox.showinfo("Éxito", f"Producto '{name}' agregado.")
        self.clear_fields(); self.load_products()

    def update_product(self):
        if not self._selected_id:
            messagebox.showerror("Error", "Seleccione un producto de la tabla."); return
        try:
            price  = float(self.price_entry.get() or 0)
            cost   = float(self.cost_entry.get()  or 0)
            stock  = int(self.stock_entry.get()   or 0)
            if price < 0 or cost < 0 or stock < 0: raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Datos inválidos."); return

        expiry   = self.expiry_entry.get().strip() or None
        category = self.category_var.get()
        sup_name = self.supplier_var.get()
        sup_id   = self._suppliers.get(sup_name)

        conn = self.get_connection(); cur = conn.cursor()
        cur.execute("""UPDATE products SET name=?, category=?, price=?, cost=?,
                       stock=?, expiry_date=?, supplier_id=? WHERE id=?""",
                    (self.name_entry.get(), category, price, cost,
                     stock, expiry, sup_id, self._selected_id))
        conn.commit(); conn.close()
        messagebox.showinfo("Éxito", "Producto actualizado.")
        self.clear_fields(); self.load_products()

    def delete_product(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Advertencia", "Seleccione un producto."); return
        pid  = self.tree.item(sel[0], "values")[0]
        name = self.tree.item(sel[0], "values")[1]
        if not messagebox.askyesno("Confirmar", f"¿Eliminar '{name}'?"): return
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute("DELETE FROM products WHERE id=?", (pid,))
        conn.commit(); conn.close()
        messagebox.showinfo("Éxito", "Producto eliminado.")
        self.clear_fields(); self.load_products()

    def clear_fields(self, keep_id=False):
        if not keep_id: self._selected_id = None
        for e in [self.name_entry, self.price_entry, self.cost_entry,
                  self.stock_entry, self.expiry_entry]:
            e.delete(0, "end")
        self.category_var.set("General")
        self.supplier_var.set("Sin proveedor")

    def export_products(self):
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute("""SELECT p.id, p.name, p.category, p.price, p.cost,
                              p.stock, p.expiry_date, s.name
                       FROM products p LEFT JOIN suppliers s ON p.supplier_id=s.id
                       ORDER BY p.name""")
        rows = cur.fetchall(); conn.close()
        filename = export_to_excel(
            rows, ["ID", "Nombre", "Categoría", "Precio", "Costo", "Stock", "Vencimiento", "Proveedor"],
            "productos.xlsx"
        )
        messagebox.showinfo("Éxito", f"Exportado:\n{filename}")