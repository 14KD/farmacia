import customtkinter as ctk

from auth import session
from database.connection import create_connection

from database.backup import (
    create_backup,
    restore_backup
)
from tkinter import (
    messagebox,
    filedialog
)

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import matplotlib.pyplot as plt

from ui.products_ui import ProductsUI
from ui.customers_ui import CustomersUI
from ui.invoices_ui import InvoicesUI
from ui.reports_ui import ReportsUI
from ui.users_ui import UsersUI
from ui.settings_ui import SettingsUI

from auth import session
from utils.logger import write_log


class Dashboard:

    def __init__(self, root):


        self.root = root

        # =====================================
        # CONFIGURAR VENTANA
        # =====================================

        self.root.title("Sistema POS Farmacia")

        # =====================================
        # SIDEBAR
        # =====================================

        self.sidebar = ctk.CTkFrame(
            root,
            width=260,
            corner_radius=0,
            fg_color="#1E1E2E"
        )

        self.sidebar.pack(
            side="left",
            fill="y"
        )

        # =====================================
        # AREA PRINCIPAL
        # =====================================

        self.main_frame = ctk.CTkFrame(root)

        self.main_frame.pack(
            side="right",
            expand=True,
            fill="both"
        )

        # =====================================
        # TITULO
        # =====================================

        title = ctk.CTkLabel(
            self.sidebar,
            text="FARMACIA POS",
            font=("Arial", 26, "bold")
        )

        title.pack(pady=30)

        # =====================================
        # USUARIO ACTUAL
        # =====================================

        current_user = session.current_user

        user_label = ctk.CTkLabel(
            self.sidebar,
            text=f"{current_user[1]}\n{current_user[3]}",
            font=("Arial", 14)
        )

        user_label.pack(pady=10)

        # =====================================
        # BOTONES MENU
        # =====================================

        self.products_button = ctk.CTkButton(
            self.sidebar,
            text="Productos",
            height=50,
            corner_radius=12,
            fg_color="#313244",
            hover_color="#45475A",
            font=("Arial", 16, "bold"),
            command=self.show_products

        )

        self.products_button.pack(
            pady=10,
            padx=15,
            fill="x"
        )

        self.customers_button = ctk.CTkButton(
            self.sidebar,
            text="Clientes",
            height=50,
            corner_radius=12,
            fg_color="#313244",
            hover_color="#45475A",
            font=("Arial", 16, "bold"),
            command=self.show_customers
        )

        self.customers_button.pack(
            pady=10,
            padx=15,
            fill="x"
        )

        self.invoices_button = ctk.CTkButton(
            self.sidebar,
            text="Facturación",
            height=50,
            corner_radius=12,
            fg_color="#313244",
            hover_color="#45475A",
            font=("Arial", 16, "bold"),
            command=self.show_invoices
        )

        self.invoices_button.pack(
            pady=10,
            padx=15,
            fill="x"
        )
        
        self.reports_button = ctk.CTkButton(
        self.sidebar,
        text="Historial Facturas",
        height=50,
        corner_radius=12,
        fg_color="#313244",
        hover_color="#45475A",
        font=("Arial", 16, "bold"),
        command=self.show_reports

        )

        self.reports_button.pack(
          pady=10,
          padx=15,
          fill="x"
        )

        # =====================================
        # BOTON USUARIOS
        # =====================================

        self.users_button = ctk.CTkButton(
            self.sidebar,
            text="Usuarios",
            height=50,
            corner_radius=12,
            fg_color="#313244",
            hover_color="#45475A",
            font=("Arial", 16, "bold"),
            command=self.show_users
        )

        self.users_button.pack(
            pady=10,
            padx=15,
            fill="x"
        )
      # =====================================
        # BOTON BACKUP
        # =====================================

        self.backup_button = ctk.CTkButton(
            self.sidebar,
            text="Crear Backup",
            height=50,
            corner_radius=12,
            fg_color="orange",
            hover_color="darkorange",
            font=("Arial", 16, "bold"),
            command=self.make_backup
        )

        self.backup_button.pack(
            pady=10,
            padx=15,
            fill="x"
        )

        # =====================================
        # BOTON RESTAURAR
        # =====================================

        self.restore_button = ctk.CTkButton(
            self.sidebar,
            text="Restaurar Backup",
            height=50,
            corner_radius=12,
            fg_color="red",
            hover_color="darkred",
            command=self.restore_database
        )

        self.restore_button.pack(
            pady=10,
            padx=15,
            fill="x"
        )

        # =====================================
        # BOTON CONFIGURACION
        # =====================================

        self.settings_button = ctk.CTkButton(
            self.sidebar,
            text="Configuración",
            command=self.show_settings
        )

        self.settings_button.pack(
            pady=10,
            padx=15,
            fill="x"
        )

        if session.current_role != "admin":

            self.restore_button.configure(
                state="disabled"
            )

        # =====================================
        # SOLO ADMIN
        # =====================================

        if session.current_role != "admin":

            self.backup_button.configure(
                state="disabled"
            )  

        if session.current_role != "admin":

            self.users_button.configure(
                state="disabled"
            )        

    # =========================================
    # CONFIGURACION
    # =========================================

    def show_settings(self):

        self.clear_main_frame()

        SettingsUI(self.main_frame)
    # =========================================
    # USUARIOS
    # =========================================

    def show_users(self):

        self.clear_main_frame()

        UsersUI(self.main_frame)

        # =====================================
        # CARGAR DASHBOARD INICIAL
        # =====================================

        self.show_home()


        # =========================================
        # CREAR BACKUP
        # =========================================

    def make_backup(self):

        backup_file = create_backup()

        messagebox.showinfo(
            "Backup",
            f"Backup creado:\n{backup_file}"
        )
        write_log(
            f"Backup creado: {backup_file}"
            )

        # =========================================
        # RESTAURAR BACKUP
        # =========================================

    def restore_database(self):

        backup_file = filedialog.askopenfilename(
            title="Seleccionar Backup",
            filetypes=[
            ("SQLite Database", "*.db")
            ]
            )

        if not backup_file:

             return

        restore_backup(backup_file)

        messagebox.showinfo(
             "Restaurado",
            "Backup restaurado correctamente.\n\nReinicie el sistema."
        )        

    # =========================================
    # LIMPIAR PANEL
    # =========================================

    def clear_main_frame(self):

        for widget in self.main_frame.winfo_children():
            widget.destroy()

# =========================================
# HOME
# =========================================

    def show_home(self):

        self.clear_main_frame()

    # =====================================
    # TITULO
    # =====================================

        title = ctk.CTkLabel(
            self.main_frame,
            text="Dashboard Principal",
            font=("Arial", 32, "bold")
        )

        title.pack(pady=20)

    # =====================================
    # OBTENER DATOS
    # =====================================

        conn = create_connection()
        cursor = conn.cursor()

    # Productos

        cursor.execute(
            "SELECT COUNT(*) FROM products"
        )

        total_products = cursor.fetchone()[0]

    # Clientes

        cursor.execute(
            "SELECT COUNT(*) FROM customers"
        )

        total_customers = cursor.fetchone()[0]

    # Facturas

        cursor.execute(
            "SELECT COUNT(*) FROM invoices"
        )

        total_invoices = cursor.fetchone()[0]

    # Ventas

        cursor.execute(
            "SELECT IFNULL(SUM(total), 0) FROM invoices"
        )

        total_sales = cursor.fetchone()[0]

        conn.close()
        # =====================================
        # ALERTAS INVENTARIO
        # =====================================

        cursor = create_connection().cursor()

        # Productos agotados

        cursor.execute(
            "SELECT COUNT(*) FROM products WHERE stock = 0"
        )

        out_stock = cursor.fetchone()[0]

        # Stock bajo

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM products
            WHERE stock > 0
            AND stock <= 5
            """
        )

        low_stock = cursor.fetchone()[0]

    # =====================================
    # CONTENEDOR TARJETAS
    # =====================================

        cards_frame = ctk.CTkFrame(
            self.main_frame
        )

        cards_frame.pack(
                pady=20,
                padx=20,
                fill="x"
        )
      

    # =====================================
    # TARJETA PRODUCTOS
    # =====================================

        products_card = ctk.CTkFrame(
            cards_frame,
            width=200,
            height=120
        )

        products_card.grid(
            row=0,
            column=0,
            padx=20,
            pady=20
        )

        products_title = ctk.CTkLabel(
            products_card,
            text="Productos",
            font=("Arial", 20, "bold")
        )

        products_title.pack(pady=10)

        products_value = ctk.CTkLabel(
            products_card,
            text=str(total_products),
            font=("Arial", 32)
        )

        products_value.pack(pady=10)

    # =====================================
    # TARJETA CLIENTES
    # =====================================

        customers_card = ctk.CTkFrame(
            cards_frame,
            width=200,
            height=120
        )

        customers_card.grid(
            row=0,
            column=1,
            padx=20,
            pady=20
        )

        customers_title = ctk.CTkLabel(
            customers_card,
            text="Clientes",
            font=("Arial", 20, "bold")
        )

        customers_title.pack(pady=10)

        customers_value = ctk.CTkLabel(
            customers_card,
            text=str(total_customers),
            font=("Arial", 32)
        )

        customers_value.pack(pady=10)

    # =====================================
    # TARJETA FACTURAS
    # =====================================

        invoices_card = ctk.CTkFrame(
            cards_frame,
            width=200,
            height=120
        )

        invoices_card.grid(
            row=0,
            column=2,
            padx=20,
            pady=20
        )

        invoices_title = ctk.CTkLabel(
            invoices_card,
            text="Facturas",
            font=("Arial", 20, "bold")
        )

        invoices_title.pack(pady=10)

        invoices_value = ctk.CTkLabel(
            invoices_card,
            text=str(total_invoices),
            font=("Arial", 32)
        )

        invoices_value.pack(pady=10)

    # =====================================
    # TARJETA VENTAS
    # =====================================

        sales_card = ctk.CTkFrame(
            cards_frame,
            width=200,
            height=120
        )

        sales_card.grid(
            row=0,
            column=3,
            padx=20,
            pady=20
        )

        sales_title = ctk.CTkLabel(
            sales_card,
            text="Ventas",
            font=("Arial", 20, "bold")
        )

        sales_title.pack(pady=10)

        sales_value = ctk.CTkLabel(
            sales_card,
            text=f"${total_sales:.2f}",
            font=("Arial", 28)
        )

        sales_value.pack(pady=10)

        # =====================================
        # ALERTAS
        # =====================================

        alerts_frame = ctk.CTkFrame(
            self.main_frame
        )

        alerts_frame.pack(
            pady=20,
            padx=20,
            fill="x"
        )

        alerts_title = ctk.CTkLabel(
            alerts_frame,
            text="Alertas de Inventario",
            font=("Arial", 24, "bold")
        )

        alerts_title.pack(pady=15)

        # =====================================
        # PRODUCTOS AGOTADOS
        # =====================================

        out_stock_label = ctk.CTkLabel(
            alerts_frame,
            text=f"Productos agotados: {out_stock}",
            font=("Arial", 18),
            text_color="red"
        )

        out_stock_label.pack(pady=5)

        # =====================================
        # STOCK BAJO
        # =====================================

        low_stock_label = ctk.CTkLabel(
            alerts_frame,
            text=f"Productos con stock bajo: {low_stock}",
            font=("Arial", 18),
            text_color="orange"
        )

        low_stock_label.pack(pady=5)

        # =====================================
        # GRAFICO VENTAS
        # =====================================

        conn = create_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, total
            FROM invoices
            ORDER BY id ASC
            LIMIT 10
            """
        )

        sales_data = cursor.fetchall()

        conn.close()

        if sales_data:

            invoice_ids = [
                str(item[0])
                for item in sales_data
            ]

            totals = [
                item[1]
                for item in sales_data
            ]

            figure = plt.Figure(
                figsize=(6, 4),
                dpi=100
            )

            ax = figure.add_subplot(111)

            bars = ax.bar(
                invoice_ids,
                totals
            )

            ax.set_facecolor("#313244")

            figure.set_facecolor("#1E1E2E")

            ax.tick_params(
                colors="white"
            )

            ax.xaxis.label.set_color(
                "white"
            )

            ax.yaxis.label.set_color(
                "white"
            )

            ax.title.set_color(
                "white"
            )

            for bar in bars:

                height = bar.get_height()

                ax.text(
                    bar.get_x() + bar.get_width()/2,
                    height,
                    f"{height}",
                    ha="center",
                    va="bottom",
                    color="white"
                )            

            ax.set_title("Ventas por Factura")

            ax.set_xlabel("Factura")

            ax.set_ylabel("Total")

            chart = FigureCanvasTkAgg(
                figure,
                self.main_frame
            )

            chart.get_tk_widget().pack(
                pady=20
            )

            chart.draw()

            # =====================================
            # PRODUCTOS MAS VENDIDOS
            # =====================================

            top_frame = ctk.CTkFrame(
                self.main_frame
            )

            top_frame.pack(
                pady=20,
                padx=20,
                fill="x"
            )

            top_title = ctk.CTkLabel(
                top_frame,
                text="Productos Más Vendidos",
                font=("Arial", 24, "bold")
            )

            top_title.pack(pady=15)

            conn = create_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT product_name,
                    SUM(quantity) as total_sold
                FROM invoice_items
                GROUP BY product_name
                ORDER BY total_sold DESC
                LIMIT 5
                """
            )

            top_products = cursor.fetchall()

            conn.close()

            # =====================================
            # MOSTRAR PRODUCTOS
            # =====================================

            if top_products:

                for product in top_products:

                    product_name = product[0]
                    total_sold = product[1]

                    product_label = ctk.CTkLabel(
                        top_frame,
                        text=f"{product_name}  |  Vendidos: {total_sold}",
                        font=("Arial", 18)
                    )

                    product_label.pack(pady=5)

            else:

                empty_label = ctk.CTkLabel(
                    top_frame,
                    text="No hay ventas registradas.",
                    font=("Arial", 18)
                )

                empty_label.pack(pady=10)

                # =====================================
                # VENTAS MENSUALES
                # =====================================

                monthly_frame = ctk.CTkFrame(
                    self.main_frame,
                    fg_color="#313244",
                    corner_radius=20
                )

                monthly_frame.pack(
                    pady=20,
                    padx=20,
                    fill="x"
                )

                monthly_title = ctk.CTkLabel(
                    monthly_frame,
                    text="Ventas Mensuales",
                    font=("Arial", 24, "bold")
                )

                monthly_title.pack(pady=15)

                conn = create_connection()

                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT strftime('%m', created_at),
                        SUM(total)
                    FROM invoices
                    GROUP BY strftime('%m', created_at)
                    ORDER BY strftime('%m', created_at)
                    """
                )

                monthly_sales = cursor.fetchall()

                conn.close()

                if monthly_sales:

                    months = [
                        item[0]
                        for item in monthly_sales
                    ]

                    totals = [
                        item[1]
                        for item in monthly_sales
                    ]

                    figure2 = plt.Figure(
                        figsize=(6, 4),
                        dpi=100
                    )

                    ax2 = figure2.add_subplot(111)

                    bars2 = ax2.bar(
                        months,
                        totals
                    )

                    figure2.set_facecolor("#1E1E2E")

                    ax2.set_facecolor("#313244")

                    ax2.tick_params(colors="white")

                    ax2.title.set_color("white")

                    ax2.xaxis.label.set_color(
                        "white"
                    )

                    ax2.yaxis.label.set_color(
                        "white"
                    )

                    ax2.set_title(
                        "Ventas por Mes"
                    )

                    ax2.set_xlabel("Mes")

                    ax2.set_ylabel("Ventas")

                    for bar in bars2:

                        height = bar.get_height()

                        ax2.text(
                            bar.get_x() + bar.get_width()/2,
                            height,
                            f"{height}",
                            ha="center",
                            va="bottom",
                            color="white"
                        )

                    chart2 = FigureCanvasTkAgg(
                        figure2,
                        monthly_frame
                    )

                    chart2.get_tk_widget().pack(
                        pady=15
                    )

                    chart2.draw()


                # =====================================
                # TENDENCIA DE VENTAS
                # =====================================

                trend_frame = ctk.CTkFrame(
                    self.main_frame,
                    fg_color="#313244",
                    corner_radius=20
                )

                trend_frame.pack(
                    pady=20,
                    padx=20,
                    fill="x"
                )

                trend_title = ctk.CTkLabel(
                    trend_frame,
                    text="Tendencia de Ventas",
                    font=("Arial", 24, "bold")
                )

                trend_title.pack(pady=15)

                conn = create_connection()

                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT id,
                        total
                    FROM invoices
                    ORDER BY id
                    """
                )

                trend_data = cursor.fetchall()

                conn.close()

                if trend_data:

                    x_values = [
                        item[0]
                        for item in trend_data
                    ]

                    y_values = [
                        item[1]
                        for item in trend_data
                    ]

                    figure3 = plt.Figure(
                        figsize=(6, 4),
                        dpi=100
                    )

                    ax3 = figure3.add_subplot(111)

                    ax3.plot(
                        x_values,
                        y_values,
                        marker="o"
                    )

                    figure3.set_facecolor("#1E1E2E")

                    ax3.set_facecolor("#313244")

                    ax3.tick_params(colors="white")

                    ax3.title.set_color("white")

                    ax3.xaxis.label.set_color(
                        "white"
                    )

                    ax3.yaxis.label.set_color(
                        "white"
                    )

                    ax3.set_title(
                        "Tendencia General"
                    )

                    ax3.set_xlabel(
                        "Facturas"
                    )

                    ax3.set_ylabel(
                        "Ventas"
                    )

                    chart3 = FigureCanvasTkAgg(
                        figure3,
                        trend_frame
                    )

                    chart3.get_tk_widget().pack(
                        pady=15
                    )

                    chart3.draw()                



    # =========================================
    # PRODUCTOS
    # =========================================

    def show_products(self):

        self.clear_main_frame()

        ProductsUI(self.main_frame)

    # =========================================
    # CLIENTES
    # =========================================

    def show_customers(self):

        self.clear_main_frame()

        CustomersUI(self.main_frame)
        

    # =========================================
    # FACTURAS
    # =========================================

    def show_invoices(self):

        self.clear_main_frame()

        InvoicesUI(self.main_frame)
 # =========================================
# REPORTES
# =========================================

    def show_reports(self):

        self.clear_main_frame()

        ReportsUI(self.main_frame)

    # =========================================
    # USUARIOS
    # =========================================

    def show_users(self):

        self.clear_main_frame()

        UsersUI(self.main_frame)