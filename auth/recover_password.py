import customtkinter as ctk

from tkinter import messagebox

from database.connection import create_connection

from auth.security import hash_password


class RecoverPasswordWindow:

    def __init__(self, root):

        self.root = root

        self.root.title(
            "Recuperar Contraseña"
        )

        self.root.geometry("400x400")

        # =====================================
        # TITULO
        # =====================================

        title = ctk.CTkLabel(
            root,
            text="Recuperar Contraseña",
            font=("Arial", 28, "bold")
        )

        title.pack(pady=30)

        # =====================================
        # USUARIO
        # =====================================

        self.username_entry = ctk.CTkEntry(
            root,
            placeholder_text="Usuario",
            width=250,
            height=40
        )

        self.username_entry.pack(pady=20)

        # =====================================
        # NUEVA PASSWORD
        # =====================================

        self.password_entry = ctk.CTkEntry(
            root,
            placeholder_text="Nueva Contraseña",
            show="*",
            width=250,
            height=40
        )

        self.password_entry.pack(pady=20)

        # =====================================
        # BOTON
        # =====================================

        reset_button = ctk.CTkButton(
            root,
            text="Cambiar Contraseña",
            width=250,
            height=45,
            command=self.reset_password
        )

        reset_button.pack(pady=30)

    # =========================================
    # RECUPERAR PASSWORD
    # =========================================

    def reset_password(self):

        username = self.username_entry.get()

        new_password = (
            self.password_entry.get()
        )

        if not username or not new_password:

            messagebox.showerror(
                "Error",
                "Complete todos los campos."
            )

            return

        conn = create_connection()

        cursor = conn.cursor()

        # =====================================
        # VALIDAR USUARIO
        # =====================================

        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE username=?
            """,
            (username,)
        )

        user = cursor.fetchone()

        if not user:

            messagebox.showerror(
                "Error",
                "Usuario no encontrado."
            )

            conn.close()

            return

        # =====================================
        # ACTUALIZAR PASSWORD
        # =====================================

        hashed_password = hash_password(
            new_password
        )

        cursor.execute(
            """
            UPDATE users
            SET password=?
            WHERE username=?
            """,
            (
                hashed_password,
                username
            )
        )

        conn.commit()

        conn.close()

        messagebox.showinfo(
            "Éxito",
            "Contraseña actualizada."
        )

        self.root.destroy()