import customtkinter as ctk
from tkinter import ttk, messagebox
from database.connection import create_connection
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
INPUT_BG     = "#23263A"
INPUT_BORDER = "#2E3148"


class SuppliersUI:

    def __init__(self, parent):
        self.parent = parent
        self._selected_id = None
        self.is_admin = session.current_role in ("admin", "Administrador")

        container = ctk.CTkFrame(parent, fg_color=BG, corner_radius=0)
        container.pack(fill="both", expand=True)

        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 0))
        ctk.CTkLabel(header, text="Proveedores",
                     font=("Arial", 22, "bold"), text_color=TEXT).pack(side="left")
        ctk.CTkFrame(container, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=20, pady=(10, 16))

        form_card = ctk.CTkFrame(container, fg_color=CARD, corner_radius=12,
                                  border_width=1, border_color=CARD_BORDER)
        form_card.pack(fill="x", padx=20, pady=(0, 12))
        ctk.CTkLabel(form_card, text="Datos del Proveedor",
                     font=("Arial", 12, "bold"), text_color=SUBTEXT).pack(anchor="w", padx=16, pady=(14, 2))
        ctk.CTkFrame(form_card, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=16, pady=(0, 12))

        row1 = ctk.CTkFrame(form_card, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=(0, 8))
        row1.columnconfigure((0, 1, 2), weight=1)
        self.name_entry  = self._field(row1, "Nombre",   0)
        self.phone_entry = self._field(row1, "Telefono", 1)
        self.email_entry = self._field(row1, "Email",    2)

        row2 = ctk.CTkFrame(form_card, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=(0, 10))
        row2.columnconfigure((0, 1), weight=1)
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
        ctk.CTkLabel(table_card, text="Lista de Proveedores",
                     font=("Arial", 12, "bold"), text_color=SUBTEXT).pack(anchor="w", padx=16, pady=(14, 2))
        ctk.CTkFrame(table_card, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=16, pady=(0, 8))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("SUP.Treeview", background=CARD, foreground=TEXT,
                         fieldbackground=CARD, borderwidth=0, font=("Arial", 12), rowheight=34)
        style.configure("SUP.Treeview.Heading", background="#1E2130", foreground=SUBTEXT,
                         font=("Arial", 11, "bold"), borderwidth=0)
        style.map("SUP.Treeview", background=[("selected", "#1A2E22")], foreground=[("selected", ACCENT)])

        cols = ("ID", "Nombre", "Telefono", "Email", "Direccion", "Notas")
        self.tree = ttk.Treeview(table_card, columns=cols, show="headings",
                                  height=14, style="SUP.Treeview")
        for col, w in zip(cols, [50, 200, 120, 180, 180, 160]):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w)
        self.tree.column("ID", anchor="center")
        self.tree.pack(fill="both", expand=True, padx=16, pady=(0, 14))
        if self.is_admin:
            self.tree.bind("<<TreeviewSelect>>", self.select_supplier)
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

    def select_supplier(self, event):
        sel = self.tree.selection()
        if not sel: return
        v = self.tree.item(sel[0], "values")
        self.clear_fields()
        self._selected_id = v[0]
        for entry, val in zip([self.name_entry, self.phone_entry, self.email_entry,
                                self.address_entry, self.notes_entry], v[1:]):
            entry.insert(0, val)

    def add_supplier(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "El nombre es obligatorio."); return
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
        self.clear_fields(); self.load_suppliers()

    def delete_supplier(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Advertencia", "Seleccione un proveedor."); return
        sid  = self.tree.item(sel[0], "values")[0]
        name = self.tree.item(sel[0], "values")[1]
        if not messagebox.askyesno("Confirmar", f"Eliminar proveedor '{name}'?"): return
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute("DELETE FROM suppliers WHERE id=?", (sid,))
        conn.commit(); conn.close()
        messagebox.showinfo("Exito", "Proveedor eliminado.")
        self.clear_fields(); self.load_suppliers()

    def clear_fields(self):
        self._selected_id = None
        for e in [self.name_entry, self.phone_entry, self.email_entry,
                  self.address_entry, self.notes_entry]:
            e.delete(0, "end")