import customtkinter as ctk
from tkinter import ttk, messagebox
from database.connection import create_connection
from exports.excel_exporter import export_to_excel
from auth import session

BG          = "#0F1117"
CARD        = "#1A1D27"
CARD_BORDER = "#252836"
ACCENT      = "#3DD68C"
CYAN        = "#22D3EE"
TEXT        = "#FFFFFF"
SUBTEXT     = "#8B8FA8"
DANGER      = "#EF4444"
DANGER_H    = "#DC2626"
INPUT_BG    = "#23263A"
INPUT_BORDER= "#2E3148"


class CustomersUI:

    def __init__(self, parent):
        self.parent = parent
        self._page = 0
        self._page_size = 20
        self._all_customers = []
        self.is_admin = session.current_role in ("admin", "Administrador")

        container = ctk.CTkFrame(parent, fg_color=BG, corner_radius=0)
        container.pack(fill="both", expand=True)

        # ── Encabezado ──
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 0))
        ctk.CTkLabel(header, text="👥  Gestión de Clientes",
                     font=("Arial", 22, "bold"), text_color=TEXT).pack(side="left")

        if not self.is_admin:
            ctk.CTkLabel(header, text="🔒 Modo solo lectura / agregar",
                         font=("Arial", 11), text_color=WARNING if False else "#FFA94D").pack(side="right")

        ctk.CTkFrame(container, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=20, pady=(10, 16))

        # ── Formulario ──
        form_card = ctk.CTkFrame(container, fg_color=CARD, corner_radius=12,
                                  border_width=1, border_color=CARD_BORDER)
        form_card.pack(fill="x", padx=20, pady=(0, 12))

        ctk.CTkLabel(form_card, text="Datos del Cliente",
                     font=("Arial", 12, "bold"), text_color=SUBTEXT).pack(anchor="w", padx=16, pady=(14, 2))
        ctk.CTkFrame(form_card, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=16, pady=(0, 12))

        row1 = ctk.CTkFrame(form_card, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=(0, 10))
        row1.columnconfigure((0, 1, 2, 3), weight=1)

        self.id_entry      = self._field(row1, "🪪  ID Cliente",  0)
        self.name_entry    = self._field(row1, "👤  Nombre",      1)
        self.phone_entry   = self._field(row1, "📞  Teléfono",    2)
        self.address_entry = self._field(row1, "📍  Dirección",   3)

        # Buscador
        search_row = ctk.CTkFrame(form_card, fg_color="transparent")
        search_row.pack(fill="x", padx=16, pady=(0, 10))
        sf = ctk.CTkFrame(search_row, fg_color=INPUT_BG, corner_radius=8,
                           border_width=1, border_color=INPUT_BORDER)
        sf.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(sf, text="🔍", font=("Arial", 14), text_color=SUBTEXT, width=30).pack(side="left", padx=(8, 0))
        self.search_entry = ctk.CTkEntry(sf, placeholder_text="Buscar por nombre, ID o teléfono...",
                                          border_width=0, fg_color="transparent", height=40,
                                          font=("Arial", 13), text_color=TEXT,
                                          placeholder_text_color="#555870")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(4, 8))
        self.search_entry.bind("<KeyRelease>", self.search_customers)

        # Botones según rol
        btn_row = ctk.CTkFrame(form_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 16))

        # Agregar: disponible para todos
        ctk.CTkButton(btn_row, text="＋  Agregar", height=38, corner_radius=8,
                      fg_color=ACCENT, hover_color="#2EBF7A", text_color="#0F1117",
                      font=("Arial", 12, "bold"),
                      command=self.add_customer).pack(side="left", padx=(0, 8))

        # Solo admin
        if self.is_admin:
            ctk.CTkButton(btn_row, text="✎  Actualizar", height=38, corner_radius=8,
                          fg_color="#1A3A4A", hover_color="#1E6A9A", text_color=CYAN,
                          font=("Arial", 12, "bold"),
                          command=self.update_customer).pack(side="left", padx=(0, 8))

            ctk.CTkButton(btn_row, text="🗑  Eliminar", height=38, corner_radius=8,
                          fg_color="#2E1A1A", hover_color=DANGER_H, text_color=DANGER,
                          font=("Arial", 12, "bold"),
                          command=self.delete_customer).pack(side="left", padx=(0, 8))

            ctk.CTkButton(btn_row, text="📊  Exportar Excel", height=38, corner_radius=8,
                          fg_color="#1A3A2A", hover_color="#2EBF7A", text_color=ACCENT,
                          font=("Arial", 12, "bold"),
                          command=self.export_customers).pack(side="left", padx=(0, 8))

        ctk.CTkButton(btn_row, text="↺  Limpiar", height=38, corner_radius=8,
                      fg_color=INPUT_BG, hover_color="#2E3148", text_color=SUBTEXT,
                      font=("Arial", 12),
                      command=self.clear_fields).pack(side="left")

        # ── Tabla ──
        table_card = ctk.CTkFrame(container, fg_color=CARD, corner_radius=12,
                                   border_width=1, border_color=CARD_BORDER)
        table_card.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        ctk.CTkLabel(table_card, text="Lista de Clientes",
                     font=("Arial", 12, "bold"), text_color=SUBTEXT).pack(anchor="w", padx=16, pady=(14, 2))
        ctk.CTkFrame(table_card, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=16, pady=(0, 8))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("CLI.Treeview", background=CARD, foreground=TEXT,
                         fieldbackground=CARD, borderwidth=0, font=("Arial", 12), rowheight=34)
        style.configure("CLI.Treeview.Heading", background="#1E2130", foreground=SUBTEXT,
                         font=("Arial", 11, "bold"), borderwidth=0)
        style.map("CLI.Treeview",
                  background=[("selected", "#1A2E22")],
                  foreground=[("selected", ACCENT)])

        cols = ("ID", "Nombre", "Teléfono", "Dirección")
        self.tree = ttk.Treeview(table_card, columns=cols, show="headings",
                                  height=16, style="CLI.Treeview")
        for col, w in zip(cols, [120, 250, 150, 320]):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w)

        self.tree.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        if self.is_admin:
            self.tree.bind("<<TreeviewSelect>>", self.select_customer)

        # ── Paginación ──
        pag_row = ctk.CTkFrame(table_card, fg_color="transparent")
        pag_row.pack(fill="x", padx=16, pady=(0, 12))

        self.prev_btn = ctk.CTkButton(pag_row, text="◀  Anterior", width=110, height=32,
                                       corner_radius=8, fg_color=INPUT_BG, hover_color="#2E3148",
                                       text_color=SUBTEXT, font=("Arial", 12),
                                       command=self._prev_page)
        self.prev_btn.pack(side="left")

        self.page_lbl = ctk.CTkLabel(pag_row, text="Página 1 de 1",
                                      font=("Arial", 12), text_color=SUBTEXT)
        self.page_lbl.pack(side="left", expand=True)

        self.next_btn = ctk.CTkButton(pag_row, text="Siguiente  ▶", width=110, height=32,
                                       corner_radius=8, fg_color=INPUT_BG, hover_color="#2E3148",
                                       text_color=SUBTEXT, font=("Arial", 12),
                                       command=self._next_page)
        self.next_btn.pack(side="right")

        self.load_customers()

    def _field(self, parent, placeholder, col):
        frame = ctk.CTkFrame(parent, fg_color=INPUT_BG, corner_radius=8,
                              border_width=1, border_color=INPUT_BORDER)
        frame.grid(row=0, column=col, padx=(0, 10), sticky="ew", ipady=2)
        entry = ctk.CTkEntry(frame, placeholder_text=placeholder, border_width=0,
                              fg_color="transparent", height=42, font=("Arial", 13),
                              text_color=TEXT, placeholder_text_color="#555870")
        entry.pack(fill="x", padx=8)
        return entry

    def get_connection(self): return create_connection()

    def load_customers(self):
        self._page = 0
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute("SELECT id, name, phone, address FROM customers ORDER BY name")
        self._all_customers = cur.fetchall()
        conn.close()
        self._render_page()

    def _render_page(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        total = len(self._all_customers)
        pages = max(1, -(-total // self._page_size))
        start = self._page * self._page_size
        for row in self._all_customers[start:start + self._page_size]:
            self.tree.insert("", "end", values=row)
        if hasattr(self, "page_lbl"):
            self.page_lbl.configure(text=f"Página {self._page+1} de {pages}  ({total} clientes)")
            self.prev_btn.configure(state="normal" if self._page > 0 else "disabled")
            self.next_btn.configure(state="normal" if self._page < pages-1 else "disabled")

    def _prev_page(self):
        if self._page > 0:
            self._page -= 1
            self._render_page()

    def _next_page(self):
        pages = max(1, -(-len(self._all_customers) // self._page_size))
        if self._page < pages - 1:
            self._page += 1
            self._render_page()

    def search_customers(self, event=None):
        q = self.search_entry.get().strip()
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute("""SELECT id, name, phone, address FROM customers
                       WHERE name LIKE ? OR id LIKE ? OR phone LIKE ?
                       ORDER BY name""",
                    (f"%{q}%", f"%{q}%", f"%{q}%"))
        self._all_customers = cur.fetchall()
        conn.close()
        self._page = 0
        self._render_page()

    def select_customer(self, event):
        sel = self.tree.selection()
        if not sel: return
        v = self.tree.item(sel[0], "values")
        self.clear_fields()
        for entry, val in zip(
            [self.id_entry, self.name_entry, self.phone_entry, self.address_entry], v
        ):
            entry.insert(0, val)

    def add_customer(self):
        cid  = self.id_entry.get().strip()
        name = self.name_entry.get().strip()
        if not cid or not name:
            messagebox.showerror("Error", "ID y Nombre son obligatorios."); return
        conn = self.get_connection(); cur = conn.cursor()
        try:
            cur.execute("SELECT id FROM customers WHERE id=?", (cid,))
            if cur.fetchone():
                messagebox.showerror("Error", "El ID ya existe."); return
            cur.execute("INSERT INTO customers (id, name, phone, address) VALUES (?,?,?,?)",
                        (cid, name, self.phone_entry.get(), self.address_entry.get()))
            conn.commit()
            messagebox.showinfo("Éxito", f"Cliente '{name}' agregado.")
            self.clear_fields(); self.load_customers()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            conn.close()

    def update_customer(self):
        cid = self.id_entry.get().strip()
        if not cid:
            messagebox.showerror("Error", "Seleccione un cliente."); return
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute("UPDATE customers SET name=?, phone=?, address=? WHERE id=?",
                    (self.name_entry.get(), self.phone_entry.get(),
                     self.address_entry.get(), cid))
        conn.commit(); conn.close()
        messagebox.showinfo("Éxito", "Cliente actualizado.")
        self.load_customers(); self.clear_fields()

    def delete_customer(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Advertencia", "Seleccione un cliente."); return
        cid  = self.tree.item(sel[0], "values")[0]
        name = self.tree.item(sel[0], "values")[1]
        if not messagebox.askyesno("Confirmar", f"¿Eliminar cliente '{name}'?"): return
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute("DELETE FROM customers WHERE id=?", (cid,))
        conn.commit(); conn.close()
        messagebox.showinfo("Éxito", "Cliente eliminado.")
        self.load_customers(); self.clear_fields()

    def clear_fields(self):
        for e in [self.id_entry, self.name_entry, self.phone_entry, self.address_entry]:
            e.delete(0, "end")

    def export_customers(self):
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute("SELECT id, name, phone, address FROM customers ORDER BY name")
        rows = cur.fetchall(); conn.close()
        filename = export_to_excel(rows, ["ID", "Nombre", "Teléfono", "Dirección"], "clientes.xlsx")
        messagebox.showinfo("Éxito", f"Exportado:\n{filename}")