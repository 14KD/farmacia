import customtkinter as ctk
from database.connection import create_connection
from database.schema import create_tables
from auth.login_window import LoginWindow


# -------------------------------
# CONFIGURACIÓN VISUAL DEL SISTEMA
# -------------------------------

ctk.set_appearance_mode("dark")       # dark / light
ctk.set_default_color_theme("blue")  # blue / green / dark-blue


# -------------------------------
# INICIALIZAR BASE DE DATOS
# -------------------------------

def initialize_system():
    """
    Iniciala el sistema y crea las tablas necesarias.
    """

    conn = create_connection()

    if conn:
        create_tables(conn)
        conn.close()
        print("Base de datos inicializada correctamente.")
    else:
        print("Error al conectar con la base de datos.")


# -------------------------------
# FUNCIÓN PRINCIPAL
# -------------------------------

def main():

    # Crear tablas y preparar sistema
    initialize_system()

    # Crear ventana principal
    root = ctk.CTk()

    # Configuración ventana
    root.title("Sistema POS Farmacia")
    root.geometry("1200x700")
    root.minsize(1000, 600)

    # Iniciar login
    LoginWindow(root)

    # Ejecutar aplicación
    root.mainloop()


# -------------------------------
# EJECUCIÓN
# -------------------------------

if __name__ == "__main__":
    main()