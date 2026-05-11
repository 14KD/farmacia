import customtkinter as ctk
from tkinter import ttk
from tkinter import messagebox

from database.connection import create_connection

from exports.excel_exporter import export_to_excel


class ProductsUI:

    def __init__(self, parent):

        self.parent = parent

        # =====================================
        # TITULO
        # =====================================

        title = ctk.CTkLabel(
            parent,
            text="Gestión de Productos",
            font=("Arial", 28, "bold")
        )

        title.pack(pady=20)

 # =====================================
# BUSCADOR
# =====================================

        self.search_entry = ctk.CTkEntry(
             parent,
             placeholder_text="Buscar producto...",
             width=400
        )

        self.search_entry.pack(pady=10)

        self.search_entry.bind(
            "<KeyRelease>",
             self.search_products
        )

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
        # ID PRODUCTO
        # =====================================

        self.id_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="ID Producto",
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
            placeholder_text="Nombre Producto",
            width=250
        )

        self.name_entry.grid(
            row=0,
            column=1,
            padx=10,
            pady=10
        )

        # =====================================
        # PRECIO
        # =====================================

        self.price_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Precio",
            width=250
        )

        self.price_entry.grid(
            row=1,
            column=0,
            padx=10,
            pady=10
        )
        # =====================================
        # COSTO
        # =====================================

        self.cost_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Costo",
            width=250
        )

        self.cost_entry.grid(
            row=2,
            column=0,
            padx=10,
            pady=10
        )


        # =====================================
        # STOCK
        # =====================================

        self.stock_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Stock",
            width=250
        )

        self.stock_entry.grid(
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
            command=self.add_product
        )

        add_button.pack(
            side="left",
            padx=10,
            pady=10
        )

        update_button = ctk.CTkButton(
            button_frame,
            text="Actualizar",
            command=self.update_product
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
            command=self.delete_product
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
            command=self.export_products
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
            "price",
            "cost",
            "stock"
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

# =====================================
# COLORES INVENTARIO
# =====================================

        self.tree.tag_configure(
            "out_stock",
            background="#ffb3b3"
        )

        self.tree.tag_configure(
            "low_stock",
            background="#fff0b3"
        )

        self.tree.tag_configure(
            "good_stock",
            background="#b7ffb3"
        )

        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Nombre")
        self.tree.heading("price", text="Precio")
        self.tree.heading("stock", text="Stock")
        self.tree.heading("cost", text="Costo")

        self.tree.column("id", width=60)
        self.tree.column("name", width=220)
        self.tree.column("price", width=100)
        self.tree.column("cost", width=100)
        self.tree.column("stock", width=100)

        self.tree.pack(
            pady=20,
            padx=20,
            fill="both",
            expand=True
        )

        self.tree.bind(
            "<<TreeviewSelect>>",
            self.select_product
        )

        # =====================================
        # CARGAR PRODUCTOS
        # =====================================

        self.load_products()

    # =========================================
    # CONEXION
    # =========================================

    def get_connection(self):

        return create_connection()

    # =========================================
    # AGREGAR PRODUCTO
    # =========================================

    def add_product(self):

        product_id = self.id_entry.get()
        name = self.name_entry.get()
        price = self.price_entry.get()
        cost = self.cost_entry.get()
        stock = self.stock_entry.get()

        if not product_id or not name:

            messagebox.showerror(
                "Error",
                "Complete todos los campos."
            )

            return

        try:

            price = float(price)
            stock = int(stock)
            
            if price < 0:
                messagebox.showerror(
                    "Error",
                    "El precio no puede ser negativo."
                )

                return

            if stock < 0:

                messagebox.showerror(
                    "Error",
                    "El stock no puede ser negativo."
                )

                return


        except:

            messagebox.showerror(
                "Error",
                "Precio o stock inválido."
            )

            return

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # =====================================
            # VALIDAR ID DUPLICADO
            # =====================================

            cursor.execute(
                "SELECT id FROM products WHERE id=?",
                (product_id,)
            )

            existing_product = cursor.fetchone()

            if existing_product:

                messagebox.showerror(
                    "Error",
                    "El ID del producto ya existe."
                )

                conn.close()

                return
            
            cursor.execute(
                """
                INSERT INTO products (
                    name,
                    stock,
                    price,
                    cost
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    name,
                    stock,
                    price,
                    cost
                )
            )

            conn.commit()

            messagebox.showinfo(
                "Éxito",
                "Producto agregado."
            )

            self.clear_fields()
            self.load_products()

        except Exception as error:

            messagebox.showerror(
                "Error",
                str(error)
            )

        finally:

            conn.close()

    # =========================================
    # CARGAR PRODUCTOS
    # =========================================

    def load_products(self):

        for item in self.tree.get_children():
            self.tree.delete(item)

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, name, price, cost, stock FROM products"
        )

        products = cursor.fetchall()

        conn.close()

        for product in products:
            stock = product[3]

            # =====================================
            # STOCK AGOTADO
            # =====================================

            if stock == 0:
                tag = "out_stock"

            # =====================================
            # STOCK BAJO
            # =====================================

            elif stock <= 5:
                tag = "low_stock"
            # =====================================
            # STOCK NORMAL
            # =====================================

            else:

                tag = "good_stock"

            self.tree.insert(
                "",
                "end",
                values=product,
                tags=(tag,)
            )

     # =========================================
# BUSCAR PRODUCTOS
# =========================================

    def search_products(self, event=None):

        search = self.search_entry.get()

        for item in self.tree.get_children():
            self.tree.delete(item)

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, name, price, stock
            FROM products
            WHERE name LIKE ?
                OR id LIKE ?
            """,
            (
                 f"%{search}%",
                 f"%{search}%",
                 f"%{search}%"
            )
        )   

        products = cursor.fetchall()

        conn.close()

        for product in products:

            self.tree.insert(
                "",
                "end",
                values=product
            )   

    # =========================================
    # SELECCIONAR PRODUCTO
    # =========================================

    def select_product(self, event):

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
        self.price_entry.insert(0, values[2])
        self.stock_entry.insert(0, values[3])

    # =========================================
    # ACTUALIZAR PRODUCTO
    # =========================================

    def update_product(self):

        product_id = self.id_entry.get()
        name = self.name_entry.get()
        price = self.price_entry.get()
        stock = self.stock_entry.get()

        try:

            price = float(price)
            stock = int(stock)
            if price < 0:

                messagebox.showerror(
                    "Error",
                    "El precio no puede ser negativo."
                )

                return

            if stock < 0:

                messagebox.showerror(
                    "Error",
                    "El stock no puede ser negativo."
                )

                return  

        except:

            messagebox.showerror(
                "Error",
                "Datos inválidos."
            )

            return

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE products
            SET name=?,
                price=?,
                stock=?
            WHERE id=?
            """,
            (
                name,
                price,
                stock,
                product_id
            )
        )

        conn.commit()
        conn.close()

        messagebox.showinfo(
            "Éxito",
            "Producto actualizado."
        )

        self.load_products()
        self.clear_fields()

    # =========================================
    # ELIMINAR PRODUCTO
    # =========================================

    def delete_product(self):

        selected = self.tree.selection()

        if not selected:

            messagebox.showwarning(
                "Advertencia",
                "Seleccione un producto."
            )

            return

        values = self.tree.item(
            selected[0],
            "values"
        )

        product_id = values[0]

        confirm = messagebox.askyesno(
            "Confirmar",
            "¿Eliminar producto?"
        )

        if not confirm:
            return

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM products WHERE id=?",
            (product_id,)
        )

        conn.commit()
        conn.close()

        messagebox.showinfo(
            "Éxito",
            "Producto eliminado."
        )

        self.load_products()
        self.clear_fields()

    # =========================================
    # LIMPIAR CAMPOS
    # =========================================

    def clear_fields(self):

        self.id_entry.delete(0, "end")
        self.name_entry.delete(0, "end")
        self.price_entry.delete(0, "end")
        self.stock_entry.delete(0, "end")
    # =========================================
    # EXPORTAR PRODUCTOS
    # =========================================

    def export_products(self):

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, name, price, stock
            FROM products
            """
        )

        products = cursor.fetchall()

        conn.close()

        filename = export_to_excel(
            products,
            [
                "ID",
                "Nombre",
                "Precio",
                "Stock"
            ],
            "productos.xlsx"
        )

        messagebox.showinfo(
            "Éxito",
            f"Archivo exportado:\n{filename}"
        )

