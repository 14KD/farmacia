import customtkinter as ctk
from ui.live_search import LiveSearch
from tkinter import ttk, messagebox
from database.connection import create_connection
from exports.excel_exporter import export_to_excel
from auth import session
from utils.validators import validate_phone, validate_address

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
        row1.columnconfigure((0, 1, 2), weight=1)

        # ID interno del cliente seleccionado (sin mostrar en el formulario)
        self.id_entry = ctk.CTkEntry(row1)
        self.id_entry.configure(state="disabled", fg_color="#1A1D27", text_color="#8B8FA8")
        self.name_entry    = self._field(row1, "👤  Nombre",      0)
        self.phone_entry   = self._field(row1, "📞  Teléfono",    1)
        self.address_entry = self._field(row1, "📍  Dirección",   2)
        self.phone_entry.bind("<KeyRelease>", self._limit_phone_length)

        # Buscador
        search_row = ctk.CTkFrame(form_card, fg_color="transparent")
        search_row.pack(fill="x", padx=16, pady=(0, 10))
        self.search_entry = LiveSearch(
            search_row,
            query_fn=self._suggest_customers,
            on_select=self._on_customer_suggest,
            on_change=lambda t: self.search_entry.after(0, self.search_customers),
            placeholder="🔍  Buscar por nombre, ID o teléfono..."
        )
        self.search_entry.pack(fill="x")

        # Botones según rol
        btn_row = ctk.CTkFrame(form_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 16))

        # Botón Agregar (visible por defecto)
        self.btn_agregar = ctk.CTkButton(btn_row, text="＋  Agregar", height=38, corner_radius=8,
                      fg_color=ACCENT, hover_color="#2EBF7A", text_color="#0F1117",
                      font=("Arial", 12, "bold"),
                      command=self.add_customer)
        self.btn_agregar.pack(side="left", padx=(0, 8))

        # Botón Actualizar (oculto por defecto, visible al seleccionar cliente)
        self.btn_actualizar = ctk.CTkButton(btn_row, text="✎  Actualizar", height=38, corner_radius=8,
                      fg_color="#1A3A4A", hover_color="#1E6A9A", text_color=CYAN,
                      font=("Arial", 12, "bold"),
                      command=self.update_customer)
        # No se empaca aún — aparece al seleccionar un cliente

        if self.is_admin:
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
        style.configure("CLI.Treeview", background="#1A1D27", foreground="#FFFFFF",
                         fieldbackground="#1A1D27", borderwidth=0, font=("Arial", 12), rowheight=34)
        style.configure("CLI.Treeview.Heading", background="#1E2130", foreground="#8B8FA8",
                         font=("Arial", 11, "bold"), borderwidth=0)
        style.map("CLI.Treeview",
                  background=[("selected", "#1A2E22"), ("!selected", "#1A1D27")],
                  foreground=[("selected", "#3DD68C"), ("!selected", "#FFFFFF")])

        cols = ("ID", "Nombre", "Teléfono", "Dirección")
        self.tree = ttk.Treeview(table_card, columns=cols, show="headings",
                                  height=16, style="CLI.Treeview")
        try:
            self.tree.configure(style=self.tree["style"])
            self.tree.tk.call("ttk::style", "configure", self.tree["style"], "-fieldbackground", "#1A1D27")
            self.tree.tk.call("ttk::style", "configure", self.tree["style"], "-background", "#1A1D27")
            self.tree.tk.call("ttk::style", "configure", self.tree["style"], "-foreground", "#FFFFFF")
        except Exception:
            pass
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
        self._register_shortcuts()

    def _register_shortcuts(self):
        """Enter guarda (Agregar o Actualizar, según el modo activo);
        Escape limpia el formulario. Así no depende únicamente del mouse."""
        def _submit(event=None):
            if self.is_admin and hasattr(self, "btn_actualizar") \
                    and self.btn_actualizar.winfo_ismapped():
                self.update_customer()
            else:
                self.add_customer()
            return "break"

        for entry in (self.name_entry, self.phone_entry, self.address_entry):
            entry.bind("<Return>", _submit)
            entry.bind("<Escape>", lambda e: self.clear_fields())

    def _field(self, parent, placeholder, col, span=None, show=""):
        """Campo con etiqueta arriba del input."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        if span:
            frame.grid(row=0, column=col, columnspan=span,
                       padx=(0, 10), pady=(0, 8), sticky="ew")
        else:
            frame.grid(row=0, column=col, padx=(0, 10), pady=(0, 8), sticky="ew")

        # Etiqueta arriba
        # Limpiar icono emoji del label si lo tiene
        label_text = placeholder.replace("  ", " ").strip()
        ctk.CTkLabel(frame, text=label_text, font=("Arial", 11),
                     text_color=SUBTEXT, anchor="w").pack(fill="x", padx=2)

        # Campo de entrada sin placeholder
        ef = ctk.CTkFrame(frame, fg_color=INPUT_BG, corner_radius=8,
                          border_width=1, border_color=INPUT_BORDER)
        ef.pack(fill="x", pady=(3, 0))
        entry = ctk.CTkEntry(ef, border_width=0, fg_color="transparent",
                              height=38, font=("Arial", 13),
                              text_color=TEXT, show=show)
        entry.pack(fill="x", padx=8)
        return entry

    def _limit_phone_length(self, event=None):
        """Limita el campo de teléfono a un máximo de 10 caracteres."""
        value = self.phone_entry.get()
        if len(value) > 10:
            self.phone_entry.delete(10, "end")

    def get_connection(self): return create_connection()

    def load_customers(self):
        self._page = 0
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, name, phone, address, seq FROM customers ORDER BY seq ASC")
            self._all_customers = cur.fetchall()
        finally:
            conn.close()
        self._render_page()

    def _render_page(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        total = len(self._all_customers)
        pages = max(1, -(-total // self._page_size))
        start = self._page * self._page_size
        for row in self._all_customers[start:start + self._page_size]:
            self.tree.insert("", "end", values=row[:4])
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

    def _suggest_customers(self, text):
        """Retorna sugerencias para el LiveSearch."""
        conn = create_connection(); cur = conn.cursor()
        cur.execute("""SELECT name, IFNULL(phone,''), seq FROM customers
                       WHERE name LIKE ? OR id LIKE ? OR phone LIKE ?
                       ORDER BY seq ASC LIMIT 8""",
                    (f"%{text}%", f"%{text}%", f"%{text}%"))
        rows = cur.fetchall(); conn.close()
        return [(r[0], f"Tel: {r[1]}" if r[1] else "", r[2]) for r in rows]

    def _on_customer_suggest(self, value, seq=None):
        """Al seleccionar sugerencia, busca ese cliente."""
        self.search_customers()

    def search_customers(self, event=None):
        q = self.search_entry.get().strip()
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""SELECT id, name, phone, address, seq FROM customers
                           WHERE name LIKE ? OR id LIKE ? OR phone LIKE ?
                           ORDER BY seq ASC""",
                        (f"%{q}%", f"%{q}%", f"%{q}%"))
            self._all_customers = cur.fetchall()
        finally:
            conn.close()
        self._page = 0
        self._render_page()

    def select_customer(self, event):
        sel = self.tree.selection()
        if not sel: return
        v = self.tree.item(sel[0], "values")
        self.clear_fields()
        self.id_entry.configure(state="normal")
        self.id_entry.insert(0, v[0])
        self.id_entry.configure(state="disabled")
        for entry, val in zip(
            [self.name_entry, self.phone_entry, self.address_entry], v[1:]
        ):
            entry.insert(0, val)
        # Mostrar botón Actualizar — ocultar Agregar
        if hasattr(self, "btn_agregar"):
            self.btn_agregar.pack_forget()
        if hasattr(self, "btn_actualizar"):
            try: self.btn_actualizar.pack_forget()
            except Exception: pass
            self.btn_actualizar.pack(side="left", padx=(0,8))
        # Indicador visual de modo edición
        if hasattr(self, "id_entry"):
            self.id_entry.configure(border_color=CYAN)

    def add_customer(self):
        import uuid
        name  = self.name_entry.get().strip()
        phone = self.phone_entry.get().strip()
        address = self.address_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "El nombre es obligatorio."); return
        ok, msg = validate_phone(phone)
        if not ok:
            messagebox.showerror("Teléfono inválido", msg); return
        ok, msg = validate_address(address)
        if not ok:
            messagebox.showerror("Dirección inválida", msg); return

        conn = self.get_connection(); cur = conn.cursor()
        try:
            # Generar ID automático único (reintenta en el rarísimo caso de colisión)
            for _ in range(5):
                cid = str(uuid.uuid4())[:8].upper()
                cur.execute("SELECT id FROM customers WHERE id=?", (cid,))
                if not cur.fetchone():
                    break
            else:
                messagebox.showerror("Error", "No se pudo generar un ID único. Intenta de nuevo.")
                return
            cur.execute("INSERT INTO customers (id, name, phone, address) VALUES (?,?,?,?)",
                        (cid, name, phone, address))
            conn.commit()
            messagebox.showinfo("Éxito", f"Cliente '{name}' agregado.")
            self.clear_fields(); self.load_customers()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            conn.close()

    def update_customer(self):
        cid   = self.id_entry.get().strip()
        phone = self.phone_entry.get().strip()
        address = self.address_entry.get().strip()
        if not cid:
            messagebox.showerror("Error", "Seleccione un cliente."); return
        ok, msg = validate_phone(phone)
        if not ok:
            messagebox.showerror("Teléfono inválido", msg); return
        ok, msg = validate_address(address)
        if not ok:
            messagebox.showerror("Dirección inválida", msg); return
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute("UPDATE customers SET name=?, phone=?, address=? WHERE id=?",
                    (self.name_entry.get().strip(), phone, address, cid))
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
        try:
            cur.execute("DELETE FROM customers WHERE id=?", (cid,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            msg = str(e)
            if "foreign key" in msg.lower() or "1451" in msg or "restrict" in msg.lower():
                messagebox.showerror(
                    "No se puede eliminar",
                    f"'{name}' no se puede eliminar porque tiene registros "
                    "asociados en el sistema (ej. facturas)."
                )
            elif "1205" in msg or "lock wait timeout" in msg.lower():
                messagebox.showerror(
                    "Base de datos ocupada",
                    "El sistema está tardando en responder. Espera unos segundos "
                    "e inténtalo de nuevo. Si persiste, cierra y vuelve a abrir "
                    "el programa (o reinicia MariaDB/XAMPP)."
                )
            else:
                messagebox.showerror("Error", f"No se pudo eliminar el cliente:\n{msg}")
            return
        finally:
            conn.close()
        messagebox.showinfo("Éxito", "Cliente eliminado.")
        self.load_customers(); self.clear_fields()

    def clear_fields(self):
        self.id_entry.configure(state="normal")
        self.id_entry.delete(0, "end")
        self.id_entry.configure(state="disabled", border_color=INPUT_BORDER)
        for e in [self.name_entry, self.phone_entry, self.address_entry]:
            e.delete(0, "end")
        # Volver al modo agregar
        if hasattr(self, "btn_actualizar"):
            try: self.btn_actualizar.pack_forget()
            except Exception: pass
        if hasattr(self, "btn_agregar"):
            try: self.btn_agregar.pack_forget()
            except Exception: pass
            self.btn_agregar.pack(side="left", padx=(0,8))


    def export_customers(self):
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, name, phone, address FROM customers ORDER BY name")
            rows = cur.fetchall()
        finally:
            conn.close()
        filename = export_to_excel(rows, ["ID", "Nombre", "Teléfono", "Dirección"], "clientes.xlsx")
        messagebox.showinfo("Éxito", f"Exportado:\n{filename}")
