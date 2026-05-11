# Reportes del sistema
import customtkinter as ctk
from tkinter import ttk
from tkinter import messagebox

from database.connection import create_connection
import pandas as pd

class ReportsUI:

    def __init__(self, parent):

        self.parent = parent

        # =====================================
        # TITULO
        # =====================================

        title = ctk.CTkLabel(
            parent,
            text="Historial de Facturas",
            font=("Arial", 28, "bold")
        )

        title.pack(pady=20)

        # =====================================
        # TABLA FACTURAS
        # =====================================

        table_frame = ctk.CTkFrame(parent)

        table_frame.pack(
            expand=True,
            fill="both",
            padx=20,
            pady=20
        )

        columns = (
            "id",
            "customer",
            "total",
            "date"
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )

        self.tree.heading("id", text="Factura")
        self.tree.heading("customer", text="Cliente")
        self.tree.heading("total", text="Total")
        self.tree.heading("date", text="Fecha")

        self.tree.pack(
            expand=True,
            fill="both"
        )

        # =====================================
        # BOTON VER DETALLES
        # =====================================

        details_button = ctk.CTkButton(
            parent,
            text="Ver Detalles",
            command=self.show_details
        )

        details_button.pack(pady=10)
        financial_button = ctk.CTkButton(
            parent,
            text="Reporte Financiero",
            command=self.financial_report
        )

        financial_button.pack(
            pady=10
        )
        sales_date_button = ctk.CTkButton(
            parent,
            text="Ventas por Fecha Excel",
            command=self.sales_by_date
        )

        sales_date_button.pack(
            pady=10
        )

        employee_sales_button = ctk.CTkButton(
            parent,
            text="Ventas por Empleado",
            command=self.sales_by_employee
        )

        employee_sales_button.pack(
            pady=10
        )
        # =====================================
        # CARGAR FACTURAS
        # =====================================

        self.load_invoices()

    # =========================================
    # CONEXION
    # =========================================

    def get_connection(self):

        return create_connection()

    # =========================================
    # CARGAR FACTURAS
    # =========================================

    def load_invoices(self):

        for item in self.tree.get_children():
            self.tree.delete(item)

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id,
                   customer_name,
                   total,
                   purchase_date
            FROM invoices
            ORDER BY id DESC
            """
        )

        invoices = cursor.fetchall()

        conn.close()

        for invoice in invoices:

            self.tree.insert(
                "",
                "end",
                values=invoice
            )

    # =========================================
    # VER DETALLES
    # =========================================

    def show_details(self):

        selected = self.tree.selection()

        if not selected:

            messagebox.showwarning(
                "Advertencia",
                "Seleccione una factura."
            )

            return

        values = self.tree.item(
            selected[0],
            "values"
        )

        invoice_id = values[0]

        details_window = ctk.CTkToplevel(self.parent)

        details_window.title(
            f"Factura #{invoice_id}"
        )

        details_window.geometry("700x400")

        title = ctk.CTkLabel(
            details_window,
            text=f"Detalles Factura #{invoice_id}",
            font=("Arial", 24, "bold")
        )

        title.pack(pady=20)

        # =====================================
        # TABLA DETALLES
        # =====================================

        columns = (
            "product",
            "quantity",
            "price",
            "total"
        )

        tree = ttk.Treeview(
            details_window,
            columns=columns,
            show="headings"
        )

        tree.heading("product", text="Producto")
        tree.heading("quantity", text="Cantidad")
        tree.heading("price", text="Precio")
        tree.heading("total", text="Total")

        tree.pack(
            expand=True,
            fill="both",
            padx=20,
            pady=20
        )

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT product_name,
                   quantity,
                   price,
                   total
            FROM invoice_items
            WHERE invoice_id=?
            """,
            (invoice_id,)
        )

        items = cursor.fetchall()

        conn.close()

        for item in items:

            tree.insert(
                "",
                "end",
                values=item
            )
    # =========================================
    # REPORTE FINANCIERO
    # =========================================

    def financial_report(self):

        conn = create_connection()

        query = """
        SELECT
            ii.product_name,
            ii.quantity,
            p.price,
            p.cost,
            (p.price - p.cost) * ii.quantity AS profit
        FROM invoice_items ii
        JOIN products p
            ON ii.product_name = p.name
        """

        df = pd.read_sql_query(
            query,
            conn
        )

        conn.close()

        total_profit = (
            df["profit"].sum()
        )

        report_window = ctk.CTkToplevel()

        report_window.title(
            "Reporte Financiero"
        )

        report_window.geometry(
            "500x400"
        )

        label = ctk.CTkLabel(
            report_window,
            text=f"Ganancia Total: ${total_profit}",
            font=("Arial", 24, "bold")
        )

        label.pack(pady=40)
    # =========================================
    # VENTAS POR FECHA
    # =========================================

    def sales_by_date(self):

        conn = create_connection()

        query = """
        SELECT *
        FROM invoices
        ORDER BY created_at DESC
        """

        df = pd.read_sql_query(
            query,
            conn
        )

        conn.close()

        export_path = (
            "reports/sales_by_date.xlsx"
        )

        df.to_excel(
            export_path,
            index=False
        )

        messagebox.showinfo(
            "Exportado",
            f"Archivo generado:\n{export_path}"
        )
    # =========================================
    # VENTAS POR EMPLEADO
    # =========================================

    def sales_by_employee(self):

        conn = create_connection()

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                employee,
                COUNT(*) as total_invoices,
                SUM(total) as total_sales
            FROM invoices
            GROUP BY employee
            ORDER BY total_sales DESC
            """
        )

        employee_data = cursor.fetchall()

        conn.close()

        # =====================================
        # VENTANA
        # =====================================

        report_window = ctk.CTkToplevel()

        report_window.title(
            "Ventas por Empleado"
        )

        report_window.geometry(
            "700x500"
        )

        title = ctk.CTkLabel(
            report_window,
            text="Ventas por Empleado",
            font=("Arial", 28, "bold")
        )

        title.pack(pady=20)

        # =====================================
        # MOSTRAR DATOS
        # =====================================

        if employee_data:

            for employee in employee_data:

                username = employee[0]
                invoices = employee[1]
                sales = employee[2]

                label = ctk.CTkLabel(
                    report_window,
                    text=(
                        f"Empleado: {username}  |  "
                        f"Facturas: {invoices}  |  "
                        f"Ventas: ${sales}"
                    ),
                    font=("Arial", 18)
                )

                label.pack(pady=10)

        else:

            empty_label = ctk.CTkLabel(
                report_window,
                text="No hay ventas registradas.",
                font=("Arial", 18)
            )

            empty_label.pack(pady=30)