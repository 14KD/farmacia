import customtkinter as ctk

from tkinter import messagebox


class SettingsUI:

    def __init__(self, parent):

        self.parent = parent

        # =====================================
        # TITULO
        # =====================================

        title = ctk.CTkLabel(
            parent,
            text="Configuración",
            font=("Arial", 28, "bold")
        )

        title.pack(pady=30)

        # =====================================
        # BOTON MODO OSCURO
        # =====================================

        dark_button = ctk.CTkButton(
            parent,
            text="Modo Oscuro",
            command=self.dark_mode
        )

        dark_button.pack(
            pady=20,
            padx=20
        )

        # =====================================
        # BOTON MODO CLARO
        # =====================================

        light_button = ctk.CTkButton(
            parent,
            text="Modo Claro",
            command=self.light_mode
        )

        light_button.pack(
            pady=20,
            padx=20
        )

    # =========================================
    # MODO OSCURO
    # =========================================

    def dark_mode(self):

        ctk.set_appearance_mode(
            "dark"
        )

        messagebox.showinfo(
            "Tema",
            "Modo oscuro activado."
        )

    # =========================================
    # MODO CLARO
    # =========================================

    def light_mode(self):

        ctk.set_appearance_mode(
            "light"
        )

        messagebox.showinfo(
            "Tema",
            "Modo claro activado."
        )