import customtkinter as ctk
from tkinter import messagebox, BooleanVar
from database.connection import create_connection
from auth.security import verify_password
from auth import session
from ui.dashboard import Dashboard
from utils.logger import write_log
from auth.recover_password import RecoverPasswordWindow


class LoginWindow:

    def __init__(self, root):

        self.root = root
        self.root.title("FarmaFactura Pro")
        self.root.geometry("460x580")
        self.root.resizable(False, False)
        self.root.configure(fg_color="#0F1117")

        # =====================================
        # CONTENEDOR CENTRAL (tarjeta)
        # =====================================

        card = ctk.CTkFrame(
            root,
            width=380,
            height=500,
            fg_color="#1A1D27",
            corner_radius=16,
            border_width=1,
            border_color="#2A2D3A"
        )
        card.pack_propagate(False)
        card.place(relx=0.5, rely=0.5, anchor="center")

        # =====================================
        # LOGO (icono + texto)
        # =====================================

        logo_frame = ctk.CTkFrame(card, fg_color="transparent")
        logo_frame.pack(pady=(36, 4))

        icon_bg = ctk.CTkFrame(
            logo_frame,
            width=52,
            height=52,
            corner_radius=12,
            fg_color="#1E3A2F"
        )
        icon_bg.pack(side="left", padx=(0, 10))
        icon_bg.pack_propagate(False)

        icon_label = ctk.CTkLabel(
            icon_bg,
            text="✚",
            font=("Arial", 26, "bold"),
            text_color="#3DD68C"
        )
        icon_label.place(relx=0.5, rely=0.5, anchor="center")

        brand_label = ctk.CTkLabel(
            logo_frame,
            text="FarmaFactura",
            font=("Georgia", 26, "bold"),
            text_color="#FFFFFF"
        )
        brand_label.pack(side="left")

        # =====================================
        # SUBTÍTULO
        # =====================================

        subtitle = ctk.CTkLabel(
            card,
            text="Bienvenido a FarmaFactura Pro",
            font=("Arial", 14),
            text_color="#8B8FA8"
        )
        subtitle.pack(pady=(0, 24))

        # =====================================
        # CAMPO USUARIO
        # =====================================

        user_frame = ctk.CTkFrame(
            card,
            fg_color="#23263A",
            corner_radius=10,
            border_width=1,
            border_color="#2E3148"
        )
        user_frame.pack(padx=32, pady=(0, 12), fill="x")

        user_icon = ctk.CTkLabel(
            user_frame,
            text="  👤",
            width=36,
            font=("Arial", 14),
            text_color="#8B8FA8"
        )
        user_icon.pack(side="left")

        self.username_entry = ctk.CTkEntry(
            user_frame,
            placeholder_text="Nombre de Usuario (ej. Darwin)",
            border_width=0,
            fg_color="transparent",
            height=44,
            font=("Arial", 13),
            text_color="#FFFFFF",
            placeholder_text_color="#555870"
        )
        self.username_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        # =====================================
        # CAMPO CONTRASEÑA
        # =====================================

        pass_frame = ctk.CTkFrame(
            card,
            fg_color="#23263A",
            corner_radius=10,
            border_width=1,
            border_color="#2E3148"
        )
        pass_frame.pack(padx=32, pady=(0, 16), fill="x")

        pass_icon = ctk.CTkLabel(
            pass_frame,
            text="  🔒",
            width=36,
            font=("Arial", 14),
            text_color="#8B8FA8"
        )
        pass_icon.pack(side="left")

        self.password_entry = ctk.CTkEntry(
            pass_frame,
            placeholder_text="Contraseña",
            show="*",
            border_width=0,
            fg_color="transparent",
            height=44,
            font=("Arial", 13),
            text_color="#FFFFFF",
            placeholder_text_color="#555870"
        )
        self.password_entry.pack(side="left", fill="x", expand=True)

        # Botón ojo (mostrar/ocultar)
        self.show_pass = False
        eye_btn = ctk.CTkButton(
            pass_frame,
            text="👁",
            width=36,
            height=36,
            fg_color="transparent",
            hover_color="#2E3148",
            font=("Arial", 14),
            command=self.toggle_password
        )
        eye_btn.pack(side="right", padx=4)

        # =====================================
        # RECORDARME + OLVIDÉ CONTRASEÑA
        # =====================================

        options_frame = ctk.CTkFrame(card, fg_color="transparent")
        options_frame.pack(padx=32, fill="x", pady=(0, 20))

        self.remember_var = BooleanVar()
        remember_cb = ctk.CTkCheckBox(
            options_frame,
            text="Recordarme",
            variable=self.remember_var,
            font=("Arial", 12),
            text_color="#8B8FA8",
            fg_color="#3DD68C",
            hover_color="#2EBF7A",
            border_color="#555870",
            checkmark_color="#0F1117",
            width=16,
            height=16
        )
        remember_cb.pack(side="left")

        recover_btn = ctk.CTkButton(
            options_frame,
            text="¿Olvidaste tu contraseña?",
            fg_color="#1A1D27",
            hover_color="#23263A",
            font=("Arial", 12),
            text_color="#8B8FA8",
            cursor="hand2",
            command=self.open_recovery
        )
        recover_btn.pack(side="right")

        # =====================================
        # BOTÓN INICIAR SESIÓN
        # =====================================

        login_btn = ctk.CTkButton(
            card,
            text="Iniciar Sesión",
            height=46,
            corner_radius=10,
            font=("Arial", 14, "bold"),
            fg_color="#3DD68C",
            hover_color="#2EBF7A",
            text_color="#0F1117",
            command=self.login
        )
        login_btn.pack(padx=32, fill="x")

        # =====================================
        # PIE DE PÁGINA
        # =====================================

        footer = ctk.CTkLabel(
            card,
            text="Sistema de Gestión Farmacéutica v1.0",
            font=("Arial", 11),
            text_color="#3A3D52"
        )
        footer.pack(pady=(20, 0))

        # Bind Enter key
        self.root.bind("<Return>", lambda e: self.login())

    # =========================================
    # MOSTRAR / OCULTAR CONTRASEÑA
    # =========================================

    def toggle_password(self):
        self.show_pass = not self.show_pass
        self.password_entry.configure(
            show="" if self.show_pass else "*"
        )

    # =========================================
    # LOGIN
    # =========================================

    def login(self):

        username = self.username_entry.get().strip()
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
            SELECT id, username, password, role
            FROM users
            WHERE username=?
            """,
            (username,)
        )

        user = cursor.fetchone()
        conn.close()

        if user and verify_password(password, user[2]):

            # Guardar sesión completa (tupla)
            session.current_user = user
            session.current_role = user[3]

            write_log(f"Login exitoso: {username}")

            self.root.destroy()

            dashboard_root = ctk.CTk()
            dashboard_root.geometry("1200x700")
            Dashboard(dashboard_root)
            dashboard_root.after(50, lambda: dashboard_root.state("zoomed"))
            dashboard_root.mainloop()

        else:
            messagebox.showerror(
                "Error",
                "Usuario o contraseña incorrectos."
            )

    # =========================================
    # ABRIR RECUPERACIÓN
    # =========================================

    def open_recovery(self):
        recovery_root = ctk.CTkToplevel()
        RecoverPasswordWindow(recovery_root)