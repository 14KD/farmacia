# Registro de usuarios
# Se implementará más adelante

import customtkinter as ctk

from tkinter import messagebox

from database.connection import create_connection

from auth.security import hash_password


class RegisterWindow:

    def __init__(self, root):

        self.root = root

        self.root.title("Registro")

        self.root.geometry("400x500")

        # =====================================
        # TITULO
        # =====================================

        title = ctk.CTkLabel(
            root,
            text="Crear Usuario",
            font=("Arial", 28, "bold")
        )

        title.pack(pady=30)

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
        # BOTON REGISTRO
        # =====================================

        register_button = ctk.CTkButton(
            root,
            text="Registrar",
            width=250,
            height=45,
            command=self.register
        )

        register_button.pack(pady=30)

    # =========================================
    # REGISTRO
    # =========================================

    def register(self):

        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:

            messagebox.showerror(
                "Error",
                "Complete todos los campos."
            )

            return

        hashed_password = hash_password(password)

        conn = create_connection()
        cursor = conn.cursor()

        # =====================================
        # VALIDAR USUARIO EXISTENTE
        # =====================================

        cursor.execute(
            """
            SELECT username
            FROM users
            WHERE username=?
            """,
            (username,)
        )

        existing_user = cursor.fetchone()

        if existing_user:

            messagebox.showerror(
                "Error",
                "El usuario ya existe."
            )

            conn.close()

            return

        # =====================================
        # INSERTAR USUARIO
        # =====================================

        cursor.execute(
            """
            INSERT INTO users (
                username,
                password,
                role
            )
            VALUES (?, ?, ?)
            """,
            (
                username,
                hashed_password,
                "employee"
            )
        )

        conn.commit()

        conn.close()

        messagebox.showinfo(
            "Éxito",
            "Usuario registrado."
        )

        self.root.destroy()