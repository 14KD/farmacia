import customtkinter as ctk
<<<<<<< HEAD
from ui.live_search import LiveSearch
from tkinter import ttk, messagebox
from database.connection import create_connection
from auth import session
from utils.validators import validate_phone, validate_address
=======
from tkinter import ttk, messagebox
from database.connection import create_connection
from auth import session
>>>>>>> 79dd05f19e8d73e0fdefe1b9fbbfeb207c3cdd43

BG           = "#0F1117"
CARD         = "#1A1D27"
CARD_BORDER  = "#252836"
ACCENT       = "#3DD68C"
CYAN         = "#22D3EE"
TEXT         = "#FFFFFF"
SUBTEXT      = "#8B8FA8"
DANGER       = "#EF4444"
DANGER_H     = "#DC2626"
INPUT_BG     = "#23263A"
INPUT_BORDER = "#2E3148"


class SuppliersUI:

    def __init__(self, parent):
        self.parent = parent
<<<<<<< HEAD
=======
        self._selected_id = None
>>>>>>> 79dd05f19e8d73e0fdefe1b9fbbfeb207c3cdd43
        self.is_admin = session.current_role in ("admin", "Administrador")

        container = ctk.CTkFrame(parent, fg_color=BG, corner_radius=0)
        container.pack(fill="both", expand=True)

<<<<<<< HEAD
        # ── Encabezado ──
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 0))
        ctk.CTkLabel(header, text="🏭  Gestión de Proveedores",
                     font=("Arial", 22, "bold"), text_color=TEXT).pack(side="left")
        ctk.CTkFrame(container, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=20, pady=(10, 16))

        # ── Formulario ──
        form_card = ctk.CTkFrame(container, fg_color=CARD, corner_radius=12,
                                  border_width=1, border_color=CARD_BORDER)
        form_card.pack(fill="x", padx=20, pady=(0, 12))

=======
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 0))
        ctk.CTkLabel(header, text="Proveedores",
                     font=("Arial", 22, "bold"), text_color=TEXT).pack(side="left")
        ctk.CTkFrame(container, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=20, pady=(10, 16))

        form_card = ctk.CTkFrame(container, fg_color=CARD, corner_radius=12,
                                  border_width=1, border_color=CARD_BORDER)
        form_card.pack(fill="x", padx=20, pady=(0, 12))
>>>>>>> 79dd05f19e8d73e0fdefe1b9fbbfeb207c3cdd43
        ctk.CTkLabel(form_card, text="Datos del Proveedor",
                     font=("Arial", 12, "bold"), text_color=SUBTEXT).pack(anchor="w", padx=16, pady=(14, 2))
        ctk.CTkFrame(form_card, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=16, pady=(0, 12))

        row1 = ctk.CTkFrame(form_card, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=(0, 8))
        row1.columnconfigure((0, 1, 2), weight=1)
<<<<<<< HEAD

        self.name_entry    = self._field(row1, "🏭  Nombre",   0)
        self.phone_entry   = self._field(row1, "📞  Teléfono", 1)
        self.email_entry   = self._field(row1, "📧  Email",    2)
        self.phone_entry.bind("<KeyRelease>", self._limit_phone_length)
=======
        self.name_entry  = self._field(row1, "Nombre",   0)
        self.phone_entry = self._field(row1, "Telefono", 1)
        self.email_entry = self._field(row1, "Email",    2)
>>>>>>> 79dd05f19e8d73e0fdefe1b9fbbfeb207c3cdd43

        row2 = ctk.CTkFrame(form_card, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=(0, 10))
        row2.columnconfigure((0, 1), weight=1)
<<<<<<< HEAD

        self.address_entry = self._field(row2, "📍  Dirección", 0)
        self.notes_entry   = self._field(row2, "📝  Notas",     1)

        btn_row = ctk.CTkFrame(form_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 16))

        if self.is_admin:
            self.btn_agregar = ctk.CTkButton(btn_row, text="＋  Agregar", height=38, corner_radius=8,
                              fg_color=ACCENT, hover_color="#2EBF7A", text_color="#0F1117",
                              font=("Arial", 12, "bold"), command=self.add_supplier)
            self.btn_agregar.pack(side="left", padx=(0, 8))

            self.btn_actualizar = ctk.CTkButton(btn_row, text="✎  Actualizar", height=38, corner_radius=8,
                              fg_color="#1A3A4A", hover_color="#1E6A9A", text_color=CYAN,
                              font=("Arial", 12, "bold"), command=self.update_supplier)
            # Oculto por defecto, aparece al seleccionar

            ctk.CTkButton(btn_row, text="🗑  Eliminar", height=38, corner_radius=8,
                          fg_color="#2E1A1A", hover_color=DANGER_H, text_color=DANGER,
                          font=("Arial", 12, "bold"), command=self.delete_supplier).pack(side="left", padx=(0, 8))
            ctk.CTkButton(btn_row, text="↺  Limpiar", height=38, corner_radius=8,
                          fg_color=INPUT_BG, hover_color="#2E3148", text_color=SUBTEXT,
                          font=("Arial", 12, "bold"), command=self.clear_fields).pack(side="left", padx=(0, 8))
        else:
            ctk.CTkLabel(btn_row, text="🔒  Solo lectura — solo el administrador puede gestionar proveedores",
                         font=("Arial", 12), text_color="#FFA94D").pack(side="left")

        # ── Barra de búsqueda predictiva ──
        search_card = ctk.CTkFrame(container, fg_color=CARD, corner_radius=12,
                                    border_width=1, border_color=CARD_BORDER)
        search_card.pack(fill="x", padx=20, pady=(0, 8))
        sw = ctk.CTkFrame(search_card, fg_color="transparent")
        sw.pack(fill="x", padx=16, pady=12)
        self.search_entry = LiveSearch(
            sw,
            query_fn=self._suggest_suppliers,
            on_select=self._on_supplier_suggest,
            on_change=lambda t: self.search_entry.after(0, self._filter_suppliers),
            placeholder="🔍  Buscar por nombre, teléfono o email..."
        )
        self.search_entry.pack(fill="x")

        # ── Tabla ──
        table_card = ctk.CTkFrame(container, fg_color=CARD, corner_radius=12,
                                   border_width=1, border_color=CARD_BORDER)
        table_card.pack(fill="both", expand=True, padx=20, pady=(0, 20))

=======
        self.address_entry = self._field(row2, "Direccion", 0)
        self.notes_entry   = self._field(row2, "Notas",     1)

        btn_row = ctk.CTkFrame(form_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 16))
        if self.is_admin:
            for text, fg, hov, tc, cmd in [
                ("+ Agregar",    ACCENT,    "#2EBF7A", "#0F1117", self.add_supplier),
                ("Actualizar",  "#1A3A4A", "#1E6A9A", CYAN,      self.update_supplier),
                ("Eliminar",    "#2E1A1A", DANGER_H,  DANGER,    self.delete_supplier),
                ("Limpiar",     INPUT_BG,  "#2E3148", SUBTEXT,   self.clear_fields),
            ]:
                ctk.CTkButton(btn_row, text=text, height=38, corner_radius=8,
                              fg_color=fg, hover_color=hov, text_color=tc,
                              font=("Arial", 12, "bold"), command=cmd).pack(side="left", padx=(0, 8))
        else:
            ctk.CTkLabel(btn_row, text="Solo lectura",
                         font=("Arial", 12), text_color="#FFA94D").pack(side="left")

        table_card = ctk.CTkFrame(container, fg_color=CARD, corner_radius=12,
                                   border_width=1, border_color=CARD_BORDER)
        table_card.pack(fill="both", expand=True, padx=20, pady=(0, 20))
>>>>>>> 79dd05f19e8d73e0fdefe1b9fbbfeb207c3cdd43
        ctk.CTkLabel(table_card, text="Lista de Proveedores",
                     font=("Arial", 12, "bold"), text_color=SUBTEXT).pack(anchor="w", padx=16, pady=(14, 2))
        ctk.CTkFrame(table_card, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=16, pady=(0, 8))

        style = ttk.Style()
        style.theme_use("clam")
<<<<<<< HEAD
        style.configure("SUP.Treeview", background="#1A1D27", foreground="#FFFFFF",
                         fieldbackground="#1A1D27", borderwidth=0, font=("Arial", 12), rowheight=34)
        style.configure("SUP.Treeview.Heading", background="#1E2130", foreground="#8B8FA8",
                         font=("Arial", 11, "bold"), borderwidth=0)
        style.map("SUP.Treeview", background=[("selected", "#1A2E22"), ("!selected", "#1A1D27")], foreground=[("selected", "#3DD68C"), ("!selected", "#FFFFFF")])

        cols = ("ID", "Nombre", "Teléfono", "Email", "Dirección", "Notas")
        self.tree = ttk.Treeview(table_card, columns=cols, show="headings",
                                  height=14, style="SUP.Treeview")
        try:
            self.tree.configure(style=self.tree["style"])
            self.tree.tk.call("ttk::style", "configure", self.tree["style"], "-fieldbackground", "#1A1D27")
            self.tree.tk.call("ttk::style", "configure", self.tree["style"], "-background", "#1A1D27")
            self.tree.tk.call("ttk::style", "configure", self.tree["style"], "-foreground", "#FFFFFF")
        except Exception:
            pass
=======
        style.configure("SUP.Treeview", background=CARD, foreground=TEXT,
                         fieldbackground=CARD, borderwidth=0, font=("Arial", 12), rowheight=34)
        style.configure("SUP.Treeview.Heading", background="#1E2130", foreground=SUBTEXT,
                         font=("Arial", 11, "bold"), borderwidth=0)
        style.map("SUP.Treeview", background=[("selected", "#1A2E22")], foreground=[("selected", ACCENT)])

        cols = ("ID", "Nombre", "Telefono", "Email", "Direccion", "Notas")
        self.tree = ttk.Treeview(table_card, columns=cols, show="headings",
                                  height=14, style="SUP.Treeview")
>>>>>>> 79dd05f19e8d73e0fdefe1b9fbbfeb207c3cdd43
        for col, w in zip(cols, [50, 200, 120, 180, 180, 160]):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w)
        self.tree.column("ID", anchor="center")
        self.tree.pack(fill="both", expand=True, padx=16, pady=(0, 14))
        if self.is_admin:
            self.tree.bind("<<TreeviewSelect>>", self.select_supplier)
<<<<<<< HEAD

        self.load_suppliers()
        self._register_shortcuts()

    def _register_shortcuts(self):
        """Enter guarda (Agregar o Actualizar, según el modo activo);
        Escape limpia el formulario. Así no depende únicamente del mouse."""
        if not self.is_admin:
            return

        def _submit(event=None):
            if hasattr(self, "btn_actualizar") and self.btn_actualizar.winfo_ismapped():
                self.update_supplier()
            else:
                self.add_supplier()
            return "break"

        for entry in (self.name_entry, self.phone_entry, self.email_entry,
                      self.address_entry, self.notes_entry):
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

    def _suggest_suppliers(self, text):
        """Sugerencias predictivas por nombre, teléfono o email."""
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute("""SELECT id, name, IFNULL(phone,''), IFNULL(email,'')
                       FROM suppliers
                       WHERE name LIKE ? OR phone LIKE ? OR email LIKE ?
                       ORDER BY name LIMIT 8""",
                    (f"%{text}%", f"%{text}%", f"%{text}%"))
        rows = cur.fetchall(); conn.close()
        subtexts = []
        for r in rows:
            parts = [f"N° {r[0]}"] + [p for p in [r[2], r[3]] if p]
            subtexts.append((r[1], "  ·  ".join(parts), r[0]))
        return subtexts

    def _on_supplier_suggest(self, value, supplier_id=None):
        """Al seleccionar sugerencia, filtra la tabla."""
        self._filter_suppliers()

    def _filter_suppliers(self):
        """Filtra la tabla según el texto en el buscador."""
        q = self.search_entry.get().strip()
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            if q:
                cur.execute("""SELECT id, name, phone, email, address, notes FROM suppliers
                               WHERE name LIKE ? OR phone LIKE ? OR email LIKE ?
                               ORDER BY name""",
                            (f"%{q}%", f"%{q}%", f"%{q}%"))
            else:
                cur.execute("SELECT id, name, phone, email, address, notes FROM suppliers ORDER BY name")
            for row in cur.fetchall():
                self.tree.insert("", "end", values=row)
        finally:
            conn.close()

    def load_suppliers(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, name, phone, email, address, notes FROM suppliers ORDER BY name")
            for row in cur.fetchall():
                self.tree.insert("", "end", values=row)
        finally:
            conn.close()
=======
        self.load_suppliers()

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

    def load_suppliers(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute("SELECT id, name, phone, email, address, notes FROM suppliers ORDER BY name")
        for row in cur.fetchall():
            self.tree.insert("", "end", values=row)
        conn.close()
>>>>>>> 79dd05f19e8d73e0fdefe1b9fbbfeb207c3cdd43

    def select_supplier(self, event):
        sel = self.tree.selection()
        if not sel: return
        v = self.tree.item(sel[0], "values")
        self.clear_fields()
        self._selected_id = v[0]
<<<<<<< HEAD
        for entry, val in zip(
            [self.name_entry, self.phone_entry, self.email_entry, self.address_entry, self.notes_entry],
            v[1:]
        ):
            entry.insert(0, val)
        # Mostrar Actualizar, ocultar Agregar
        if hasattr(self, "btn_agregar") and hasattr(self, "btn_actualizar"):
            self.btn_agregar.pack_forget()
            self.btn_actualizar.pack(side="left", padx=(0, 8))

    def _validate_email(self, email):
        """Valida que el correo contenga @ y un dominio."""
        if not email: return True  # opcional
        if "@" not in email or "." not in email.split("@")[-1]:
            messagebox.showerror("Error", "El correo electrónico no es válido. Debe contener @ y un dominio (ej: nombre@correo.com).")
            return False
        return True
=======
        for entry, val in zip([self.name_entry, self.phone_entry, self.email_entry,
                                self.address_entry, self.notes_entry], v[1:]):
            entry.insert(0, val)
>>>>>>> 79dd05f19e8d73e0fdefe1b9fbbfeb207c3cdd43

    def add_supplier(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "El nombre es obligatorio."); return
<<<<<<< HEAD
        phone = self.phone_entry.get().strip() if hasattr(self,"phone_entry") else ""
        ok, msg = validate_phone(phone)
        if not ok:
            messagebox.showerror("Teléfono inválido", msg); return
        address = self.address_entry.get().strip() if hasattr(self,"address_entry") else ""
        ok, msg = validate_address(address, required=False)
        if not ok:
            messagebox.showerror("Dirección inválida", msg); return
        email = self.email_entry.get().strip() if hasattr(self,"email_entry") else ""
        if not self._validate_email(email): return
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute(
            "INSERT INTO suppliers (name, phone, email, address, notes) VALUES (?, ?, ?, ?, ?)",
            (name, phone, email, address, self.notes_entry.get())
        )
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        messagebox.showinfo(
            "Éxito",
            f"Proveedor '{name}' agregado con éxito.\nN° de Proveedor: {new_id}"
        )
        self.clear_fields(); self.load_suppliers()

    def update_supplier(self):
        email = self.email_entry.get().strip() if hasattr(self,"email_entry") else ""
        if not self._validate_email(email): return
        phone = self.phone_entry.get().strip() if hasattr(self,"phone_entry") else ""
        ok, msg = validate_phone(phone)
        if not ok:
            messagebox.showerror("Teléfono inválido", msg); return
        address = self.address_entry.get().strip() if hasattr(self,"address_entry") else ""
        ok, msg = validate_address(address, required=False)
        if not ok:
            messagebox.showerror("Dirección inválida", msg); return

        if not hasattr(self, '_selected_id') or not self._selected_id:
            messagebox.showerror("Error", "Seleccione un proveedor de la tabla."); return
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute(
            "UPDATE suppliers SET name=?, phone=?, email=?, address=?, notes=? WHERE id=?",
            (self.name_entry.get().strip(), phone, email, address, self.notes_entry.get(), self._selected_id)
        )
        conn.commit(); conn.close()
        messagebox.showinfo("Éxito", "Proveedor actualizado.")
=======
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute("INSERT INTO suppliers (name, phone, email, address, notes) VALUES (?,?,?,?,?)",
                    (name, self.phone_entry.get(), self.email_entry.get(),
                     self.address_entry.get(), self.notes_entry.get()))
        conn.commit(); conn.close()
        messagebox.showinfo("Exito", f"Proveedor '{name}' agregado.")
        self.clear_fields(); self.load_suppliers()

    def update_supplier(self):
        if not self._selected_id:
            messagebox.showerror("Error", "Seleccione un proveedor."); return
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute("UPDATE suppliers SET name=?, phone=?, email=?, address=?, notes=? WHERE id=?",
                    (self.name_entry.get(), self.phone_entry.get(), self.email_entry.get(),
                     self.address_entry.get(), self.notes_entry.get(), self._selected_id))
        conn.commit(); conn.close()
        messagebox.showinfo("Exito", "Proveedor actualizado.")
>>>>>>> 79dd05f19e8d73e0fdefe1b9fbbfeb207c3cdd43
        self.clear_fields(); self.load_suppliers()

    def delete_supplier(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Advertencia", "Seleccione un proveedor."); return
        sid  = self.tree.item(sel[0], "values")[0]
        name = self.tree.item(sel[0], "values")[1]
<<<<<<< HEAD
        if not messagebox.askyesno("Confirmar", f"¿Eliminar proveedor '{name}'?"): return
        conn = self.get_connection(); cur = conn.cursor()
        try:
            cur.execute("DELETE FROM suppliers WHERE id=?", (sid,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            msg = str(e)
            if "foreign key" in msg.lower() or "1451" in msg or "restrict" in msg.lower():
                messagebox.showerror(
                    "No se puede eliminar",
                    f"'{name}' no se puede eliminar porque ya tiene compras "
                    "registradas en el sistema (se necesita conservar ese historial).\n\n"
                    "Si ya no le compras, puedes dejarlo inactivo en vez de borrarlo."
                )
            elif "1205" in msg or "lock wait timeout" in msg.lower():
                messagebox.showerror(
                    "Base de datos ocupada",
                    "El sistema está tardando en responder. Espera unos segundos "
                    "e inténtalo de nuevo. Si persiste, cierra y vuelve a abrir "
                    "el programa (o reinicia MariaDB/XAMPP)."
                )
            else:
                messagebox.showerror("Error", f"No se pudo eliminar el proveedor:\n{msg}")
            return
        finally:
            conn.close()
        messagebox.showinfo("Éxito", "Proveedor eliminado.")
=======
        if not messagebox.askyesno("Confirmar", f"Eliminar proveedor '{name}'?"): return
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute("DELETE FROM suppliers WHERE id=?", (sid,))
        conn.commit(); conn.close()
        messagebox.showinfo("Exito", "Proveedor eliminado.")
>>>>>>> 79dd05f19e8d73e0fdefe1b9fbbfeb207c3cdd43
        self.clear_fields(); self.load_suppliers()

    def clear_fields(self):
        self._selected_id = None
        for e in [self.name_entry, self.phone_entry, self.email_entry,
                  self.address_entry, self.notes_entry]:
<<<<<<< HEAD
            e.delete(0, "end")
        # Restaurar botones al modo agregar
        if hasattr(self, "btn_agregar") and hasattr(self, "btn_actualizar"):
            self.btn_actualizar.pack_forget()
            self.btn_agregar.pack(side="left", padx=(0, 8))
=======
            e.delete(0, "end")
>>>>>>> 79dd05f19e8d73e0fdefe1b9fbbfeb207c3cdd43
