# Gestión de usuarios
import customtkinter as ctk

from tkinter import ttk
from tkinter import messagebox

from database.connection import create_connection


class UsersUI:

    def __init__(self, parent):

        self.parent = parent

        # =====================================
        # TITULO
        # =====================================

        title = ctk.CTkLabel(
            parent,
            text="Administración de Usuarios",
            font=("Arial", 28, "bold")
        )

        title.pack(pady=20)

        # =====================================
        # TABLA
        # =====================================

        columns = (
            "id",
            "username",
            "role"
        )
        style = ttk.Style()

        style.theme_use("default")

        style.configure(
            "Treeview",
            background="#313244",
            foreground="white",
            fieldbackground="#313244",
            rowheight=38,
            borderwidth=0,
            font=("Arial", 12)
        )

        style.map(
            "Treeview",
            background=[
                ("selected", "#89B4FA")
            ]
        )

        style.configure(
            "Treeview.Heading",
            background="#1E1E2E",
            foreground="white",
            font=("Arial", 13, "bold")
        )
        self.tree = ttk.Treeview(
            parent,
            columns=columns,
            show="headings"
        )

        self.tree.heading("id", text="ID")
        self.tree.heading("username", text="Usuario")
        self.tree.heading("role", text="Rol")

        self.tree.pack(
            expand=True,
            fill="both",
            padx=20,
            pady=20
        )

        # =====================================
        # BOTONES
        # =====================================

        button_frame = ctk.CTkFrame(parent)

        button_frame.pack(pady=10)

        admin_button = ctk.CTkButton(
            button_frame,
            text="Hacer Admin",
            command=self.make_admin
        )

        admin_button.pack(
            side="left",
            padx=10
        )

        employee_button = ctk.CTkButton(
            button_frame,
            text="Hacer Empleado",
            command=self.make_employee
        )

        employee_button.pack(
            side="left",
            padx=10
        )

        delete_button = ctk.CTkButton(
            button_frame,
            text="Eliminar Usuario",
            fg_color="red",
            hover_color="darkred",
            command=self.delete_user
        )

        delete_button.pack(
            side="left",
            padx=10
        )

        # =====================================
        # CARGAR USUARIOS
        # =====================================

        self.load_users()

    # =========================================
    # CONEXION
    # =========================================

    def get_connection(self):

        return create_connection()

    # =========================================
    # CARGAR USUARIOS
    # =========================================

    def load_users(self):

        for item in self.tree.get_children():
            self.tree.delete(item)

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id,
                   username,
                   role
            FROM users
            """
        )

        users = cursor.fetchall()

        conn.close()

        for user in users:

            self.tree.insert(
                "",
                "end",
                values=user
            )

    # =========================================
    # HACER ADMIN
    # =========================================

    def make_admin(self):

        selected = self.tree.selection()

        if not selected:

            messagebox.showwarning(
                "Advertencia",
                "Seleccione un usuario."
            )

            return

        user_id = self.tree.item(
            selected[0],
            "values"
        )[0]

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE users
            SET role='admin'
            WHERE id=?
            """,
            (user_id,)
        )

        conn.commit()

        conn.close()

        self.load_users()

        messagebox.showinfo(
            "Éxito",
            "Usuario actualizado a admin."
        )

    # =========================================
    # HACER EMPLEADO
    # =========================================

    def make_employee(self):

        selected = self.tree.selection()

        if not selected:

            messagebox.showwarning(
                "Advertencia",
                "Seleccione un usuario."
            )

            return

        user_id = self.tree.item(
            selected[0],
            "values"
        )[0]

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE users
            SET role='employee'
            WHERE id=?
            """,
            (user_id,)
        )

        conn.commit()

        conn.close()

        self.load_users()

        messagebox.showinfo(
            "Éxito",
            "Usuario actualizado a empleado."
        )

    # =========================================
    # ELIMINAR USUARIO
    # =========================================

    def delete_user(self):

        selected = self.tree.selection()

        if not selected:

            messagebox.showwarning(
                "Advertencia",
                "Seleccione un usuario."
            )

            return

        user_id = self.tree.item(
            selected[0],
            "values"
        )[0]

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM users
            WHERE id=?
            """,
            (user_id,)
        )

        conn.commit()

        conn.close()

        self.load_users()

        messagebox.showinfo(
            "Éxito",
            "Usuario eliminado."
        )