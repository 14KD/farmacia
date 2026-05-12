import customtkinter as ctk
from tkinter import ttk, messagebox
from database.connection import create_connection
from auth.security import hash_password

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


class UsersUI:

    def __init__(self, parent):
        self.parent = parent

        container = ctk.CTkFrame(parent, fg_color=BG, corner_radius=0)
        container.pack(fill="both", expand=True)

        # ── Encabezado ──
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 0))
        ctk.CTkLabel(header, text="👤  Administración de Usuarios",
                     font=("Arial", 22, "bold"), text_color=TEXT).pack(side="left")
        ctk.CTkFrame(container, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=20, pady=(10, 16))

        # ══════════════════════════════════════
        # TARJETA: CREAR NUEVO USUARIO
        # ══════════════════════════════════════

        form_card = ctk.CTkFrame(container, fg_color=CARD, corner_radius=12,
                                  border_width=1, border_color=CARD_BORDER)
        form_card.pack(fill="x", padx=20, pady=(0, 12))

        ctk.CTkLabel(form_card, text="Crear Nuevo Usuario",
                     font=("Arial", 12, "bold"), text_color=SUBTEXT).pack(anchor="w", padx=16, pady=(14, 2))
        ctk.CTkFrame(form_card, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=16, pady=(0, 12))

        # Fila de campos
        fields_row = ctk.CTkFrame(form_card, fg_color="transparent")
        fields_row.pack(fill="x", padx=16, pady=(0, 10))
        fields_row.columnconfigure((0, 1, 2, 3), weight=1)

        self.new_username  = self._field(fields_row, "👤  Nombre de Usuario", 0)
        self.new_password  = self._field(fields_row, "🔒  Contraseña",        1, show="*")
        self.new_password2 = self._field(fields_row, "🔒  Confirmar Contraseña", 2, show="*")

        # Selector de rol
        role_frame = ctk.CTkFrame(fields_row, fg_color=INPUT_BG, corner_radius=8,
                                   border_width=1, border_color=INPUT_BORDER)
        role_frame.grid(row=0, column=3, padx=(0, 0), sticky="ew", ipady=2)

        ctk.CTkLabel(role_frame, text="🎭  Rol", font=("Arial", 12),
                     text_color=SUBTEXT).pack(anchor="w", padx=12, pady=(6, 0))

        self.role_var = ctk.StringVar(value="employee")
        role_menu = ctk.CTkOptionMenu(
            role_frame,
            values=["employee", "Administrador"],
            variable=self.role_var,
            fg_color="#1E2130",
            button_color="#2A2D3A",
            button_hover_color="#3A3D52",
            dropdown_fg_color="#1A1D27",
            dropdown_hover_color="#1A2E22",
            dropdown_text_color=TEXT,
            text_color=TEXT,
            font=("Arial", 12),
            height=30
        )
        role_menu.pack(fill="x", padx=8, pady=(2, 8))

        # Botón crear
        btn_row = ctk.CTkFrame(form_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 16))

        ctk.CTkButton(
            btn_row, text="＋  Crear Usuario",
            height=40, corner_radius=8,
            fg_color=ACCENT, hover_color="#2EBF7A",
            text_color="#0F1117", font=("Arial", 13, "bold"),
            command=self.create_user
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row, text="↺  Limpiar",
            height=40, corner_radius=8,
            fg_color=INPUT_BG, hover_color="#2E3148",
            text_color=SUBTEXT, font=("Arial", 13),
            command=self.clear_form
        ).pack(side="left")

        # ══════════════════════════════════════
        # LAYOUT: TABLA | PANEL ACCIONES
        # ══════════════════════════════════════

        body = ctk.CTkFrame(container, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # ── Tabla ──
        table_card = ctk.CTkFrame(body, fg_color=CARD, corner_radius=12,
                                   border_width=1, border_color=CARD_BORDER)
        table_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(table_card, text="Usuarios Registrados",
                     font=("Arial", 12, "bold"), text_color=SUBTEXT).pack(anchor="w", padx=16, pady=(14, 2))
        ctk.CTkFrame(table_card, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=16, pady=(0, 8))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("USR.Treeview", background=CARD, foreground=TEXT,
                         fieldbackground=CARD, borderwidth=0, font=("Arial", 12), rowheight=36)
        style.configure("USR.Treeview.Heading", background="#1E2130", foreground=SUBTEXT,
                         font=("Arial", 11, "bold"), borderwidth=0)
        style.map("USR.Treeview",
                  background=[("selected", "#1A2E22")],
                  foreground=[("selected", ACCENT)])

        cols = ("ID", "Usuario", "Rol")
        self.tree = ttk.Treeview(table_card, columns=cols, show="headings",
                                  height=12, style="USR.Treeview")
        for col, w, anc in [("ID", 60, "center"), ("Usuario", 240, "w"), ("Rol", 160, "w")]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor=anc)
        self.tree.pack(fill="both", expand=True, padx=16, pady=(0, 14))
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # ── Panel acciones ──
        actions_card = ctk.CTkFrame(body, fg_color=CARD, corner_radius=12,
                                     border_width=1, border_color=CARD_BORDER)
        actions_card.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(actions_card, text="Acciones",
                     font=("Arial", 12, "bold"), text_color=SUBTEXT).pack(anchor="w", padx=16, pady=(14, 2))
        ctk.CTkFrame(actions_card, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=16, pady=(0, 12))

        # Info usuario seleccionado
        info_box = ctk.CTkFrame(actions_card, fg_color=INPUT_BG, corner_radius=8)
        info_box.pack(fill="x", padx=14, pady=(0, 12))
        self.selected_lbl = ctk.CTkLabel(
            info_box, text="Ningún usuario\nseleccionado",
            font=("Arial", 12), text_color=SUBTEXT, justify="center"
        )
        self.selected_lbl.pack(pady=14, padx=10)

        ctk.CTkFrame(actions_card, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=16, pady=(0, 12))

        # Botones de acción sobre usuario seleccionado
        for text, fg, hov, tc, cmd in [
            ("⭐  Hacer Administrador", "#1A3A2A", "#2EBF7A", ACCENT,  self.make_admin),
            ("👷  Hacer Empleado",      "#1A2E3A", "#1E6A9A", CYAN,    self.make_employee),
            ("🔑  Resetear Contraseña", "#2A2A1A", "#7A6A0A", "#FFD43B", self.reset_password),
            ("🗑  Eliminar Usuario",    "#2E1A1A", DANGER_H,  DANGER,  self.delete_user),
        ]:
            ctk.CTkButton(
                actions_card, text=text, height=42, corner_radius=8,
                fg_color=fg, hover_color=hov, text_color=tc,
                font=("Arial", 12, "bold"), anchor="w",
                command=cmd
            ).pack(fill="x", padx=14, pady=(0, 8))

        # Leyenda de roles
        ctk.CTkFrame(actions_card, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=16, pady=(4, 12))
        ctk.CTkLabel(actions_card, text="ℹ  Roles",
                     font=("Arial", 11, "bold"), text_color=SUBTEXT).pack(anchor="w", padx=16)

        for rol, desc, color in [
            ("Administrador", "Acceso total al sistema", ACCENT),
            ("employee",      "Acceso limitado",         CYAN),
        ]:
            row = ctk.CTkFrame(actions_card, fg_color=INPUT_BG, corner_radius=8)
            row.pack(fill="x", padx=14, pady=(6, 0))
            dot_row = ctk.CTkFrame(row, fg_color="transparent")
            dot_row.pack(anchor="w", padx=10, pady=(8, 0))
            ctk.CTkFrame(dot_row, width=8, height=8, corner_radius=4, fg_color=color).pack(side="left", padx=(0, 6))
            ctk.CTkLabel(dot_row, text=rol, font=("Arial", 11, "bold"), text_color=TEXT).pack(side="left")
            ctk.CTkLabel(row, text=desc, font=("Arial", 10), text_color=SUBTEXT).pack(anchor="w", padx=10, pady=(0, 8))

        self.load_users()

    # ─── Helper campo ─────────────────────────

    def _field(self, parent, placeholder, col, show=""):
        frame = ctk.CTkFrame(parent, fg_color=INPUT_BG, corner_radius=8,
                              border_width=1, border_color=INPUT_BORDER)
        frame.grid(row=0, column=col, padx=(0, 10), sticky="ew", ipady=2)
        entry = ctk.CTkEntry(
            frame, placeholder_text=placeholder, border_width=0,
            fg_color="transparent", height=42, font=("Arial", 13),
            text_color=TEXT, placeholder_text_color="#555870",
            show=show
        )
        entry.pack(fill="x", padx=8)
        return entry

    def _on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            self.selected_lbl.configure(text="Ningún usuario\nseleccionado")
            return
        v = self.tree.item(sel[0], "values")
        self.selected_lbl.configure(text=f"ID: {v[0]}\n👤 {v[1]}\n🎭 {v[2]}")

    def get_connection(self): return create_connection()

    # ─── Cargar usuarios ──────────────────────

    def load_users(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute("SELECT id, username, role FROM users ORDER BY id")
        for row in cur.fetchall():
            self.tree.insert("", "end", values=row)
        conn.close()

    # ─── Crear usuario ────────────────────────

    def create_user(self):
        username = self.new_username.get().strip()
        password = self.new_password.get()
        password2 = self.new_password2.get()
        role = self.role_var.get()

        if not username or not password:
            messagebox.showerror("Error", "Usuario y contraseña son obligatorios.")
            return

        if len(username) < 3:
            messagebox.showerror("Error", "El usuario debe tener al menos 3 caracteres.")
            return

        if len(password) < 4:
            messagebox.showerror("Error", "La contraseña debe tener al menos 4 caracteres.")
            return

        if password != password2:
            messagebox.showerror("Error", "Las contraseñas no coinciden.")
            return

        conn = self.get_connection(); cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username=?", (username,))
        if cur.fetchone():
            messagebox.showerror("Error", f"El usuario '{username}' ya existe.")
            conn.close()
            return

        try:
            cur.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, hash_password(password), role)
            )
            conn.commit()
            messagebox.showinfo("Éxito", f"Usuario '{username}' creado con rol '{role}'.")
            self.clear_form()
            self.load_users()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            conn.close()

    # ─── Limpiar formulario ───────────────────

    def clear_form(self):
        self.new_username.delete(0, "end")
        self.new_password.delete(0, "end")
        self.new_password2.delete(0, "end")
        self.role_var.set("employee")

    # ─── Obtener ID seleccionado ──────────────

    def _get_selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Advertencia", "Seleccione un usuario de la tabla.")
            return None
        return self.tree.item(sel[0], "values")[0]

    # ─── Cambiar rol ──────────────────────────

    def make_admin(self):
        uid = self._get_selected_id()
        if not uid: return
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute("UPDATE users SET role='Administrador' WHERE id=?", (uid,))
        conn.commit(); conn.close()
        messagebox.showinfo("Éxito", "Usuario actualizado a Administrador.")
        self.load_users()

    def make_employee(self):
        uid = self._get_selected_id()
        if not uid: return
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute("UPDATE users SET role='employee' WHERE id=?", (uid,))
        conn.commit(); conn.close()
        messagebox.showinfo("Éxito", "Usuario actualizado a Empleado.")
        self.load_users()

    # ─── Resetear contraseña ──────────────────

    def reset_password(self):
        uid = self._get_selected_id()
        if not uid: return

        sel = self.tree.selection()
        username = self.tree.item(sel[0], "values")[1]

        # Ventana modal para nueva contraseña
        win = ctk.CTkToplevel(self.parent)
        win.title("Resetear Contraseña")
        win.geometry("400x300")
        win.configure(fg_color=BG)
        win.grab_set()

        ctk.CTkLabel(win, text="🔑  Nueva Contraseña",
                     font=("Arial", 16, "bold"), text_color=TEXT).pack(padx=20, pady=(24, 4), anchor="w")
        ctk.CTkLabel(win, text=f"Usuario: {username}",
                     font=("Arial", 12), text_color=SUBTEXT).pack(padx=20, anchor="w")
        ctk.CTkFrame(win, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=20, pady=(10, 16))

        card = ctk.CTkFrame(win, fg_color=CARD, corner_radius=12,
                             border_width=1, border_color=CARD_BORDER)
        card.pack(fill="x", padx=20)

        f1 = ctk.CTkFrame(card, fg_color=INPUT_BG, corner_radius=8,
                           border_width=1, border_color=INPUT_BORDER)
        f1.pack(fill="x", padx=14, pady=(14, 8))
        pwd1 = ctk.CTkEntry(f1, placeholder_text="🔒  Nueva contraseña", show="*",
                             border_width=0, fg_color="transparent", height=42,
                             font=("Arial", 13), text_color=TEXT)
        pwd1.pack(fill="x", padx=8)

        f2 = ctk.CTkFrame(card, fg_color=INPUT_BG, corner_radius=8,
                           border_width=1, border_color=INPUT_BORDER)
        f2.pack(fill="x", padx=14, pady=(0, 14))
        pwd2 = ctk.CTkEntry(f2, placeholder_text="🔒  Confirmar contraseña", show="*",
                             border_width=0, fg_color="transparent", height=42,
                             font=("Arial", 13), text_color=TEXT)
        pwd2.pack(fill="x", padx=8)

        def confirm():
            p1, p2 = pwd1.get(), pwd2.get()
            if not p1:
                messagebox.showerror("Error", "Ingrese la nueva contraseña."); return
            if len(p1) < 4:
                messagebox.showerror("Error", "Mínimo 4 caracteres."); return
            if p1 != p2:
                messagebox.showerror("Error", "Las contraseñas no coinciden."); return
            conn = self.get_connection(); cur = conn.cursor()
            cur.execute("UPDATE users SET password=? WHERE id=?", (hash_password(p1), uid))
            conn.commit(); conn.close()
            messagebox.showinfo("Éxito", f"Contraseña de '{username}' actualizada.")
            win.destroy()

        ctk.CTkButton(win, text="✔  Confirmar Cambio", height=42, corner_radius=8,
                      fg_color=ACCENT, hover_color="#2EBF7A", text_color="#0F1117",
                      font=("Arial", 13, "bold"), command=confirm).pack(fill="x", padx=20, pady=(12, 0))

    # ─── Eliminar usuario ─────────────────────

    def delete_user(self):
        uid = self._get_selected_id()
        if not uid: return
        sel = self.tree.selection()
        username = self.tree.item(sel[0], "values")[1]
        if username == "admin":
            messagebox.showerror("Error", "No se puede eliminar el usuario admin."); return
        if not messagebox.askyesno("Confirmar", f"¿Eliminar al usuario '{username}'?\nEsta acción no se puede deshacer."): return
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE id=?", (uid,))
        conn.commit(); conn.close()
        messagebox.showinfo("Éxito", f"Usuario '{username}' eliminado.")
        self.load_users()
        self.selected_lbl.configure(text="Ningún usuario\nseleccionado")