import customtkinter as ctk
from tkinter import ttk
from tkinter import messagebox

from database.connection import create_connection

from exports.excel_exporter import export_to_excel

class CustomersUI:

    def __init__(self, parent):

        self.parent = parent

        # =====================================
        # TITULO
        # =====================================

        title = ctk.CTkLabel(
            parent,
            text="Gestión de Clientes",
            font=("Arial", 28, "bold")
        )

        title.pack(pady=20)

        # =====================================
        # FORMULARIO
        # =====================================

        form_frame = ctk.CTkFrame(parent)

        form_frame.pack(
            pady=10,
            padx=20,
            fill="x"
        )

        # =====================================
        # ID CLIENTE
        # =====================================

        self.id_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="ID Cliente",
            width=250
        )

        self.id_entry.grid(
            row=0,
            column=0,
            padx=10,
            pady=10
        )

        # =====================================
        # NOMBRE
        # =====================================

        self.name_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Nombre",
            width=250
        )

        self.name_entry.grid(
            row=0,
            column=1,
            padx=10,
            pady=10
        )

        # =====================================
        # TELEFONO
        # =====================================

        self.phone_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Teléfono",
            width=250
        )

        self.phone_entry.grid(
            row=1,
            column=0,
            padx=10,
            pady=10
        )

        # =====================================
        # DIRECCION
        # =====================================

        self.address_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Dirección",
            width=250
        )

        self.address_entry.grid(
            row=1,
            column=1,
            padx=10,
            pady=10
        )

        # =====================================
        # BOTONES
        # =====================================

        button_frame = ctk.CTkFrame(parent)

        button_frame.pack(
            pady=10,
            padx=20,
            fill="x"
        )

        add_button = ctk.CTkButton(
            button_frame,
            text="Agregar",
            command=self.add_customer
        )

        add_button.pack(
            side="left",
            padx=10,
            pady=10
        )

        update_button = ctk.CTkButton(
            button_frame,
            text="Actualizar",
            command=self.update_customer
        )

        update_button.pack(
            side="left",
            padx=10,
            pady=10
        )

        delete_button = ctk.CTkButton(
            button_frame,
            text="Eliminar",
            fg_color="red",
            hover_color="darkred",
            command=self.delete_customer
        )

        delete_button.pack(
            side="left",
            padx=10,
            pady=10
        )

        clear_button = ctk.CTkButton(
            button_frame,
            text="Limpiar",
            fg_color="gray",
            command=self.clear_fields
        )

        clear_button.pack(
            side="left",
            padx=10,
            pady=10
        )

        export_button = ctk.CTkButton(
            button_frame,
            text="Exportar Excel",
            fg_color="green",
            hover_color="darkgreen",
            command=self.export_customers
        )

        export_button.pack(
            side="left",
            padx=10,
            pady=10
        )

        # =====================================
        # TABLA
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
            "name",
            "phone",
            "address"
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

        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Nombre")
        self.tree.heading("phone", text="Teléfono")
        self.tree.heading("address", text="Dirección")

        self.tree.pack(
            expand=True,
            fill="both"
        )

        self.tree.bind(
            "<<TreeviewSelect>>",
            self.select_customer
        )

        # =====================================
        # CARGAR CLIENTES
        # =====================================

        self.load_customers()

    # =========================================
    # CONEXION
    # =========================================

    def get_connection(self):

        return create_connection()

    # =========================================
    # AGREGAR CLIENTE
    # =========================================

    def add_customer(self):

        customer_id = self.id_entry.get()
        name = self.name_entry.get()
        phone = self.phone_entry.get()
        address = self.address_entry.get()

        if not customer_id or not name:

            messagebox.showerror(
                "Error",
                "Complete los campos obligatorios."
            )

            return

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # =====================================
            # VALIDAR ID DUPLICADO
            # =====================================

            cursor.execute(
                "SELECT id FROM customers WHERE id=?",
                (customer_id,)
            )

            existing_customer = cursor.fetchone()

            if existing_customer:

                messagebox.showerror(
                    "Error",
                    "El ID del cliente ya existe."
                )

                conn.close()

                return           

            cursor.execute(
                """
                INSERT INTO customers
                (id, name, phone, address)
                VALUES (?, ?, ?, ?)
                """,
                (
                    customer_id,
                    name,
                    phone,
                    address
                )
            )

            conn.commit()

            messagebox.showinfo(
                "Éxito",
                "Cliente agregado."
            )

            self.clear_fields()
            self.load_customers()

        except Exception as error:

            messagebox.showerror(
                "Error",
                str(error)
            )

        finally:

            conn.close()

    # =========================================
    # CARGAR CLIENTES
    # =========================================

    def load_customers(self):

        for item in self.tree.get_children():
            self.tree.delete(item)

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, name, phone, address
            FROM customers
            """
        )

        customers = cursor.fetchall()

        conn.close()

        for customer in customers:

            self.tree.insert(
                "",
                "end",
                values=customer
            )

    # =========================================
    # SELECCIONAR CLIENTE
    # =========================================

    def select_customer(self, event):

        selected = self.tree.selection()

        if not selected:
            return

        values = self.tree.item(
            selected[0],
            "values"
        )

        self.clear_fields()

        self.id_entry.insert(0, values[0])
        self.name_entry.insert(0, values[1])
        self.phone_entry.insert(0, values[2])
        self.address_entry.insert(0, values[3])

    # =========================================
    # ACTUALIZAR CLIENTE
    # =========================================

    def update_customer(self):

        customer_id = self.id_entry.get()
        name = self.name_entry.get()
        phone = self.phone_entry.get()
        address = self.address_entry.get()

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE customers
            SET name=?,
                phone=?,
                address=?
            WHERE id=?
            """,
            (
                name,
                phone,
                address,
                customer_id
            )
        )

        conn.commit()
        conn.close()

        messagebox.showinfo(
            "Éxito",
            "Cliente actualizado."
        )

        self.load_customers()
        self.clear_fields()

    # =========================================
    # ELIMINAR CLIENTE
    # =========================================

    def delete_customer(self):

        selected = self.tree.selection()

        if not selected:

            messagebox.showwarning(
                "Advertencia",
                "Seleccione un cliente."
            )

            return

        values = self.tree.item(
            selected[0],
            "values"
        )

        customer_id = values[0]

        confirm = messagebox.askyesno(
            "Confirmar",
            "¿Eliminar cliente?"
        )

        if not confirm:
            return

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM customers WHERE id=?",
            (customer_id,)
        )

        conn.commit()
        conn.close()

        messagebox.showinfo(
            "Éxito",
            "Cliente eliminado."
        )

        self.load_customers()
        self.clear_fields()

    # =========================================
    # LIMPIAR CAMPOS
    # =========================================

    def clear_fields(self):

        self.id_entry.delete(0, "end")
        self.name_entry.delete(0, "end")
        self.phone_entry.delete(0, "end")
        self.address_entry.delete(0, "end")
    
    # =========================================
    # EXPORTAR CLIENTES
    # =========================================

    def export_customers(self):

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, name, phone, address
            FROM customers
            """
        )

        customers = cursor.fetchall()

        conn.close()

        filename = export_to_excel(
            customers,
            [
                "ID",
                "Nombre",
                "Teléfono",
                "Dirección"
            ],
            "clientes.xlsx"
        )

        messagebox.showinfo(
            "Éxito",
            f"Archivo exportado:\n{filename}"
        )