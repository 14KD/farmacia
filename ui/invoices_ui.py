import customtkinter as ctk
from tkinter import ttk
from tkinter import messagebox

from database.connection import create_connection

from datetime import datetime
from reports.pdf_generator import generate_invoice_pdf

from auth import session
from utils.notifications import (
    success_message,
    error_message,
    warning_message

)
from utils.logger import write_log

class InvoicesUI:

    def __init__(self, parent):

        self.parent = parent

        self.cart = []

        # =====================================
        # TITULO
        # =====================================

        title = ctk.CTkLabel(
            parent,
            text="Facturación",
            font=("Arial", 28, "bold")
        )

        title.pack(pady=20)

        # =====================================
        # FRAME FORMULARIO
        # =====================================

        form_frame = ctk.CTkFrame(parent)

        form_frame.pack(
            padx=20,
            pady=10,
            fill="x"
        )

        # =====================================
        # CLIENTE
        # =====================================

        self.customer_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Nombre Cliente",
            width=250
        )

        self.customer_entry.grid(
            row=0,
            column=0,
            padx=10,
            pady=10
        )

        # =====================================
        # PRODUCTO
        # =====================================

        self.product_id_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="ID Producto",
            width=250
        )

        self.product_id_entry.grid(
            row=0,
            column=1,
            padx=10,
            pady=10
        )

        # =====================================
        # CANTIDAD
        # =====================================

        self.quantity_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Cantidad",
            width=250
        )

        self.quantity_entry.grid(
            row=1,
            column=0,
            padx=10,
            pady=10
        )

        # =====================================
        # BOTON AGREGAR
        # =====================================

        add_button = ctk.CTkButton(
            form_frame,
            text="Agregar Producto",
            command=self.add_to_cart
        )

        add_button.grid(
            row=1,
            column=1,
            padx=10,
            pady=10
        )

        # =====================================
        # TABLA FACTURA
        # =====================================

        table_frame = ctk.CTkFrame(parent)

        table_frame.pack(
            expand=True,
            fill="both",
            padx=20,
            pady=20
        )

        columns = (
            "product",
            "quantity",
            "price",
            "total"
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
            table_frame,
            columns=columns,
            show="headings"
        )

        self.tree.heading("product", text="Producto")
        self.tree.heading("quantity", text="Cantidad")
        self.tree.heading("price", text="Precio")
        self.tree.heading("total", text="Total")

        self.tree.pack(
            expand=True,
            fill="both"
        )

        # =====================================
        # TOTAL
        # =====================================

        self.total_label = ctk.CTkLabel(
            parent,
            text="TOTAL: $0.00",
            font=("Arial", 24, "bold")
        )

        self.total_label.pack(pady=10)

        # =====================================
        # BOTON ELIMINAR PRODUCTO
        # =====================================

        remove_button = ctk.CTkButton(
            parent,
            text="Eliminar Producto",
            fg_color="red",
            hover_color="darkred",
            command=self.remove_product
        )

        remove_button.pack(pady=10)

        # =====================================
        # BOTON FACTURAR
        # =====================================

        invoice_button = ctk.CTkButton(
            parent,
            text="Generar Factura",
            height=45,
            command=self.generate_invoice
        )

        invoice_button.pack(pady=20)

    # =========================================
    # CONEXION
    # =========================================

    def get_connection(self):

        return create_connection()

    # =========================================
    # AGREGAR AL CARRITO
    # =========================================

    def add_to_cart(self):

        product_id = self.product_id_entry.get()
        quantity = self.quantity_entry.get()

        if not product_id or not quantity:

            error_message(
                "Error",
                "Complete todos los campos."
            )

            return

        try:

            quantity = int(quantity)

        except:

            messagebox.showerror(
                "Error",
                "Cantidad inválida."
            )

            return

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT name, price, stock
            FROM products
            WHERE id=?
            """,
            (product_id,)
        )

        product = cursor.fetchone()

        conn.close()

        if not product:

            messagebox.showerror(
                "Error",
                "Producto no encontrado."
            )

            return

        name = product[0]
        price = product[1]
        stock = product[2]

        if quantity > stock:

            messagebox.showerror(
                "Error",
                "Stock insuficiente."
            )

            return

        total = quantity * price

        self.cart.append({
            "product_id": product_id,
            "name": name,
            "quantity": quantity,
            "price": price,
            "total": total
        })

        self.tree.insert(
            "",
            "end",
            values=(
                name,
                quantity,
                price,
                total
            )
        )

        self.update_total()

        self.product_id_entry.delete(0, "end")
        self.quantity_entry.delete(0, "end")

    # =========================================
    # ACTUALIZAR TOTAL
    # =========================================

    def update_total(self):

        total = sum(item["total"] for item in self.cart)

        self.total_label.configure(
            text=f"TOTAL: ${total:.2f}"
        )

    # =========================================
    # GENERAR FACTURA
    # =========================================

    def generate_invoice(self):

        customer = self.customer_entry.get()

        if not customer:

            messagebox.showerror(
                "Error",
                "Ingrese cliente."
            )

            return

        if not self.cart:

            messagebox.showerror(
                "Error",
                "No hay productos."
            )

            return

        total = sum(item["total"] for item in self.cart)

        conn = self.get_connection()
        cursor = conn.cursor()

        # =====================================
        # GUARDAR FACTURA
        # =====================================

        cursor.execute(
            """
                INSERT INTO invoices
                (
                    customer_name,
                    total,
                    purchase_date,
                    employee
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    customer,
                    total,
                    datetime.now().strftime("%Y-%m-%d"),
                    session.current_user
                )
        )

        invoice_id = cursor.lastrowid

        # =====================================
        # GUARDAR DETALLES
        # =====================================

        for item in self.cart:

            cursor.execute(
                """
                INSERT INTO invoice_items
                (
                    invoice_id,
                    product_name,
                    quantity,
                    price,
                    total
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    invoice_id,
                    item["name"],
                    item["quantity"],
                    item["price"],
                    item["total"]
                )
            )

            # =================================
            # DESCONTAR STOCK
            # =================================

            cursor.execute(
                """
                UPDATE products
                SET stock = stock - ?
                WHERE id=?
                """,
                (
                    item["quantity"],
                    item["product_id"]
                )
            )

        conn.commit()
        conn.close()

        # =====================================
# GENERAR PDF
# =====================================

        pdf_file = generate_invoice_pdf(
            invoice_id,
            customer,
            self.cart,
            total
        )

        success_message(           
             "Éxito",
            f"Factura #{invoice_id} generada.\n\nPDF creado:\n{pdf_file}"
        )
        write_log(
            f"Factura generada: #{invoice_id} | Cliente: {customer} | Total: {total}"
        )   

        self.clear_invoice()

    # =========================================
    # LIMPIAR FACTURA
    # =========================================

    def clear_invoice(self):

        self.customer_entry.delete(0, "end")

        self.cart.clear()

        for item in self.tree.get_children():
            self.tree.delete(item)

        self.update_total()
    
    # =========================================
# ELIMINAR PRODUCTO DEL CARRITO
# =========================================

def remove_product(self):

    selected = self.tree.selection()

    if not selected:

        warning_message(
            "Advertencia",
            "Seleccione un producto."
        )

        return

    item = selected[0]

    values = self.tree.item(
        item,
        "values"
    )

    product_name = values[0]

    # =====================================
    # ELIMINAR DEL CARRITO
    # =====================================

    for product in self.cart:

        if product["name"] == product_name:

            self.cart.remove(product)

            break

    # =====================================
    # ELIMINAR DE TABLA
    # =====================================

    self.tree.delete(item)

    # =====================================
    # ACTUALIZAR TOTAL
    # =====================================

    self.update_total()

    messagebox.showinfo(
        "Éxito",
        "Producto eliminado."
    )