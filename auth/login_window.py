import customtkinter as ctk

from tkinter import messagebox

from database.connection import create_connection

from auth.security import verify_password

from auth import session

from ui.dashboard import Dashboard
from utils.logger import write_log
from auth.recover_password import (
    RecoverPasswordWindow
)


class LoginWindow:

    def __init__(self, root):

        self.root = root

        self.root.title("Login")

        self.root.geometry("400x500")

        # =====================================
        # TITULO
        # =====================================

        title = ctk.CTkLabel(
            root,
            text="Farmacia POS",
            font=("Arial", 30, "bold")
        )

        title.pack(pady=40)

        # =====================================
        # USERNAME
        # =====================================

        self.username_entry = ctk.CTkEntry(
            root,
            placeholder_text="Usuario",
            width=250,
            height=40
        )

        self.username_entry.pack(pady=20)

        # =====================================
        # PASSWORD
        # =====================================

        self.password_entry = ctk.CTkEntry(
            root,
            placeholder_text="Contraseña",
            show="*",
            width=250,
            height=40
        )

        self.password_entry.pack(pady=20)

        # =====================================
        # BOTON LOGIN
        # =====================================

        login_button = ctk.CTkButton(
            root,
            text="Iniciar Sesión",
            width=250,
            height=45,
            command=self.login
        )

        login_button.pack(pady=30)

        recover_button = ctk.CTkButton(
            root,
            text="Recuperar Contraseña",
            fg_color="orange",
            hover_color="darkorange",
            command=self.open_recovery
        )

        recover_button.pack(pady=10)

    # =========================================
    # LOGIN
    # =========================================

    def login(self):

        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:

            messagebox.showerror(
                "Error",
                "Complete todos los campos."
            )

            return

        conn = create_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id,
                   username,
                   password,
                   role
            FROM users
            WHERE username=?
            """,
            (username,)
        )

        user = cursor.fetchone()

        conn.close()

        # =====================================
        # VALIDAR PASSWORD
        # =====================================

        if user and verify_password(
            password,
            user[2]
        ):

            session.current_user = username

            session.current_role = user[3]

            messagebox.showinfo(
                "Éxito",
                "Inicio de sesión exitoso."
            )

            write_log(
                f"Login exitoso: {username}"
            )

            self.root.destroy()

            dashboard_root = ctk.CTk()

            Dashboard(dashboard_root)

            dashboard_root.mainloop()

        else:

            messagebox.showerror(
                "Error",
                "Usuario o contraseña incorrectos."
            )
    # =========================================
    # ABRIR RECUPERACION
    # =========================================

    def open_recovery(self):

        recovery_root = ctk.CTkToplevel()

        RecoverPasswordWindow(
            recovery_root
        )