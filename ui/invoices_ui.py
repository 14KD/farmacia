import os
import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime

from database.connection import create_connection
from reports.pdf_generator import generate_invoice_pdf
from auth import session
from utils.notifications import success_message, error_message, warning_message
from utils.logger import write_log


BG           = "#0F1117"
CARD         = "#1A1D27"
CARD_BORDER  = "#252836"
ACCENT       = "#3DD68C"
CYAN         = "#22D3EE"
TEXT         = "#FFFFFF"
SUBTEXT      = "#8B8FA8"
DANGER       = "#EF4444"
DANGER_H     = "#DC2626"
WARNING      = "#FFA94D"
INPUT_BG     = "#23263A"
INPUT_BORDER = "#2E3148"


class InvoicesUI:

    def __init__(self, parent):
        self.parent  = parent
        self.cart    = []
        self._discount_global = 0.0   # % descuento global

        container = ctk.CTkFrame(parent, fg_color=BG, corner_radius=0)
        container.pack(fill="both", expand=True)

        # ── Encabezado ──
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 0))
        ctk.CTkLabel(header, text="🧾  Nueva Factura",
                     font=("Arial", 22, "bold"), text_color=TEXT).pack(side="left")
        ctk.CTkLabel(header, text=f"📅  {datetime.now().strftime('%d/%m/%Y')}",
                     font=("Arial", 13), text_color=SUBTEXT).pack(side="right")
        ctk.CTkFrame(container, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=20, pady=(10, 16))

        # ══════════════════════════════════════
        # TARJETA: FORMULARIO
        # ══════════════════════════════════════
        form_card = ctk.CTkFrame(container, fg_color=CARD, corner_radius=12,
                                  border_width=1, border_color=CARD_BORDER)
        form_card.pack(fill="x", padx=20, pady=(0, 12))

        ctk.CTkLabel(form_card, text="Datos de la Venta",
                     font=("Arial", 12, "bold"), text_color=SUBTEXT).pack(anchor="w", padx=16, pady=(14, 2))
        ctk.CTkFrame(form_card, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=16, pady=(0, 12))

        # Fila 1: Cliente + búsqueda de producto
        row1 = ctk.CTkFrame(form_card, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=(0, 8))
        row1.columnconfigure(0, weight=2)
        row1.columnconfigure(1, weight=3)

        self.customer_entry = self._field(row1, "👤  Nombre del Cliente", 0)

        # Buscador de producto por nombre o ID
        search_frame = ctk.CTkFrame(row1, fg_color=INPUT_BG, corner_radius=8,
                                     border_width=1, border_color=INPUT_BORDER)
        search_frame.grid(row=0, column=1, padx=(0, 0), sticky="ew", ipady=2)
        search_inner = ctk.CTkFrame(search_frame, fg_color="transparent")
        search_inner.pack(fill="x", padx=8, pady=4)

        self.product_search = ctk.CTkEntry(
            search_inner, placeholder_text="🔍  Buscar producto por nombre o ID...",
            border_width=0, fg_color="transparent", height=38,
            font=("Arial", 13), text_color=TEXT, placeholder_text_color="#555870"
        )
        self.product_search.pack(side="left", fill="x", expand=True)
        self.product_search.bind("<KeyRelease>", self._on_search_key)
        self.product_search.bind("<Return>", lambda e: self._confirm_first_result())

        ctk.CTkButton(search_inner, text="🔍", width=36, height=34, corner_radius=6,
                      fg_color="#1A2E22", hover_color="#2EBF7A", text_color=ACCENT,
                      font=("Arial", 13), command=self._open_product_picker).pack(side="right")

        # Dropdown de resultados
        self._picker_frame = ctk.CTkFrame(form_card, fg_color="#1E2130", corner_radius=8,
                                           border_width=1, border_color=CARD_BORDER)
        self._result_btns = []
        self._selected_product = None   # dict con id, name, price, stock

        # Fila 2: Cantidad | Descuento por producto | Botones
        row2 = ctk.CTkFrame(form_card, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=(0, 10))
        row2.columnconfigure((0, 1), weight=1)

        self.quantity_entry  = self._field(row2, "🔢  Cantidad",           0)
        self.item_disc_entry = self._field(row2, "🏷  Descuento producto %", 1)

        # Botones de acción del formulario
        btn_row = ctk.CTkFrame(form_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 16))

        ctk.CTkButton(btn_row, text="＋  Agregar al Carrito",
                      height=40, corner_radius=8,
                      fg_color=ACCENT, hover_color="#2EBF7A",
                      text_color="#0F1117", font=("Arial", 13, "bold"),
                      command=self.add_to_cart).pack(side="left", padx=(0, 8))

        ctk.CTkButton(btn_row, text="🗑  Quitar Seleccionado",
                      height=40, corner_radius=8,
                      fg_color="#2E1A1A", hover_color=DANGER_H,
                      text_color=DANGER, font=("Arial", 13),
                      command=self.remove_product).pack(side="left")

        # ══════════════════════════════════════
        # TARJETA: TABLA DEL CARRITO
        # ══════════════════════════════════════
        table_card = ctk.CTkFrame(container, fg_color=CARD, corner_radius=12,
                                   border_width=1, border_color=CARD_BORDER)
        table_card.pack(fill="x", padx=20, pady=(0, 12))

        ctk.CTkLabel(table_card, text="Carrito de Compras",
                     font=("Arial", 12, "bold"), text_color=SUBTEXT).pack(anchor="w", padx=16, pady=(14, 2))
        ctk.CTkFrame(table_card, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=16, pady=(0, 8))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("INV.Treeview", background=CARD, foreground=TEXT,
                         fieldbackground=CARD, borderwidth=0, font=("Arial", 12), rowheight=34)
        style.configure("INV.Treeview.Heading", background="#1E2130", foreground=SUBTEXT,
                         font=("Arial", 11, "bold"), borderwidth=0)
        style.map("INV.Treeview",
                  background=[("selected", "#1A2E22")],
                  foreground=[("selected", ACCENT)])

        cols = ("Producto", "Cant.", "Precio", "Desc.%", "Total")
        self.tree = ttk.Treeview(table_card, columns=cols, show="headings",
                                  height=8, style="INV.Treeview")
        for col, w, anc in [
            ("Producto", 280, "w"),
            ("Cant.",     70, "center"),
            ("Precio",   120, "e"),
            ("Desc.%",    70, "center"),
            ("Total",    130, "e"),
        ]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor=anc)
        self.tree.pack(fill="x", padx=16, pady=(0, 14))

        # ══════════════════════════════════════
        # TARJETA: TOTALES + DESCUENTO GLOBAL
        # ══════════════════════════════════════
        bottom_card = ctk.CTkFrame(container, fg_color=CARD, corner_radius=12,
                                    border_width=1, border_color=CARD_BORDER)
        bottom_card.pack(fill="x", padx=20, pady=(0, 24))

        brow = ctk.CTkFrame(bottom_card, fg_color="transparent")
        brow.pack(fill="x", padx=20, pady=16)

        # Columna izquierda: subtotal, descuento global, total
        totals_col = ctk.CTkFrame(brow, fg_color="transparent")
        totals_col.pack(side="left")

        ctk.CTkLabel(totals_col, text="SUBTOTAL", font=("Arial", 11), text_color=SUBTEXT).grid(row=0, column=0, sticky="w")
        self.subtotal_lbl = ctk.CTkLabel(totals_col, text="$0.00", font=("Arial", 14), text_color=TEXT)
        self.subtotal_lbl.grid(row=0, column=1, padx=(16, 0), sticky="e")

        # Descuento global
        disc_row = ctk.CTkFrame(totals_col, fg_color="transparent")
        disc_row.grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 6))
        ctk.CTkLabel(disc_row, text="Descuento global %", font=("Arial", 11), text_color=SUBTEXT).pack(side="left")
        disc_frame = ctk.CTkFrame(disc_row, fg_color=INPUT_BG, corner_radius=6,
                                   border_width=1, border_color=INPUT_BORDER)
        disc_frame.pack(side="left", padx=(10, 6))
        self.global_disc_entry = ctk.CTkEntry(disc_frame, width=70, height=30, border_width=0,
                                               fg_color="transparent", font=("Arial", 12),
                                               text_color=TEXT, placeholder_text="0")
        self.global_disc_entry.pack(padx=6)
        self.global_disc_entry.bind("<KeyRelease>", lambda e: self.update_total())
        ctk.CTkButton(disc_row, text="Aplicar", height=30, width=70, corner_radius=6,
                      fg_color="#1A3A2A", hover_color="#2EBF7A", text_color=ACCENT,
                      font=("Arial", 11), command=self.update_total).pack(side="left")

        ctk.CTkLabel(totals_col, text="TOTAL A PAGAR", font=("Arial", 11, "bold"), text_color=SUBTEXT).grid(row=2, column=0, sticky="w")
        self.total_label = ctk.CTkLabel(totals_col, text="$0.00", font=("Arial", 28, "bold"), text_color=ACCENT)
        self.total_label.grid(row=2, column=1, padx=(16, 0), sticky="e")

        self.discount_lbl = ctk.CTkLabel(totals_col, text="", font=("Arial", 11), text_color=WARNING)
        self.discount_lbl.grid(row=3, column=0, columnspan=2, sticky="w")

        # Botones derecha
        btns_col = ctk.CTkFrame(brow, fg_color="transparent")
        btns_col.pack(side="right")

        ctk.CTkButton(btns_col, text="✔  Generar Factura",
                      height=50, width=200, corner_radius=10,
                      fg_color=ACCENT, hover_color="#2EBF7A",
                      text_color="#0F1117", font=("Arial", 14, "bold"),
                      command=self.generate_invoice).pack(pady=(0, 8))

        ctk.CTkButton(btns_col, text="👁  Previsualizar PDF",
                      height=40, width=200, corner_radius=10,
                      fg_color="#1A2E3A", hover_color="#1E6A9A",
                      text_color=CYAN, font=("Arial", 13),
                      command=self.preview_pdf).pack(pady=(0, 8))

        ctk.CTkButton(btns_col, text="↺  Limpiar",
                      height=36, width=200, corner_radius=10,
                      fg_color=INPUT_BG, hover_color="#2E3148",
                      text_color=SUBTEXT, font=("Arial", 12),
                      command=self.clear_invoice).pack()

    # ═══════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════

    def _field(self, parent, placeholder, col):
        frame = ctk.CTkFrame(parent, fg_color=INPUT_BG, corner_radius=8,
                              border_width=1, border_color=INPUT_BORDER)
        frame.grid(row=0, column=col, padx=(0, 10), sticky="ew", ipady=2)
        entry = ctk.CTkEntry(frame, placeholder_text=placeholder, border_width=0,
                              fg_color="transparent", height=42, font=("Arial", 13),
                              text_color=TEXT, placeholder_text_color="#555870")
        entry.pack(fill="x", padx=8)
        return entry

    def _flash_row(self, iid):
        self.tree.selection_set(iid)
        self.tree.see(iid)
        self.parent.after(800, lambda: self.tree.selection_remove(iid))

    def _show_toast(self, msg):
        if hasattr(self, "_toast") and self._toast.winfo_exists():
            self._toast.destroy()
        self._toast = ctk.CTkLabel(self.parent, text=msg,
                                    font=("Arial", 13, "bold"), text_color="#0F1117",
                                    fg_color="#3DD68C", corner_radius=10, padx=16, pady=8)
        self._toast.place(relx=0.5, rely=0.95, anchor="center")
        self.parent.after(2200, self._hide_toast)

    def _hide_toast(self):
        if hasattr(self, "_toast") and self._toast.winfo_exists():
            self._toast.destroy()

    # ═══════════════════════════════════════════
    # BÚSQUEDA DE PRODUCTO POR NOMBRE O ID
    # ═══════════════════════════════════════════

    def _on_search_key(self, event=None):
        q = self.product_search.get().strip()
        for btn in self._result_btns:
            btn.destroy()
        self._result_btns.clear()

        if not q:
            self._picker_frame.pack_forget()
            return

        conn = create_connection(); cur = conn.cursor()
        cur.execute("""SELECT id, name, price, stock FROM products
                       WHERE (name LIKE ? OR CAST(id AS TEXT) LIKE ?) AND stock > 0
                       ORDER BY name LIMIT 6""", (f"%{q}%", f"%{q}%"))
        results = cur.fetchall()
        conn.close()

        if not results:
            self._picker_frame.pack_forget()
            return

        self._picker_frame.pack(fill="x", padx=16, pady=(0, 8))
        for pid, name, price, stock in results:
            label = f"[ID:{pid}]  {name}  —  ${price:,.2f}  (Stock: {stock})"
            btn = ctk.CTkButton(self._picker_frame, text=label, anchor="w",
                                height=34, corner_radius=0, fg_color="transparent",
                                hover_color="#1A2E22", text_color=TEXT, font=("Arial", 12),
                                command=lambda p=(pid, name, price, stock): self._select_product(p))
            btn.pack(fill="x", padx=4, pady=1)
            self._result_btns.append(btn)

    def _select_product(self, product):
        pid, name, price, stock = product
        self._selected_product = {"id": pid, "name": name, "price": price, "stock": stock}
        self.product_search.delete(0, "end")
        self.product_search.insert(0, f"[{pid}] {name}")
        for btn in self._result_btns:
            btn.destroy()
        self._result_btns.clear()
        self._picker_frame.pack_forget()
        self.quantity_entry.focus()

    def _confirm_first_result(self):
        if self._result_btns:
            self._result_btns[0].invoke()

    def _open_product_picker(self):
        """Ventana modal completa para buscar producto."""
        win = ctk.CTkToplevel(self.parent)
        win.title("Buscar Producto")
        win.geometry("600x420")
        win.configure(fg_color=BG)
        win.grab_set()

        ctk.CTkLabel(win, text="🔍  Seleccionar Producto",
                     font=("Arial", 16, "bold"), text_color=TEXT).pack(padx=20, pady=(20, 8), anchor="w")

        sf = ctk.CTkFrame(win, fg_color=INPUT_BG, corner_radius=8,
                           border_width=1, border_color=INPUT_BORDER)
        sf.pack(fill="x", padx=20, pady=(0, 12))
        search_e = ctk.CTkEntry(sf, placeholder_text="Buscar por nombre o ID...",
                                 border_width=0, fg_color="transparent", height=42,
                                 font=("Arial", 13), text_color=TEXT)
        search_e.pack(fill="x", padx=8)

        card = ctk.CTkFrame(win, fg_color=CARD, corner_radius=12,
                             border_width=1, border_color=CARD_BORDER)
        card.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        style2 = ttk.Style()
        style2.configure("PKR.Treeview", background=CARD, foreground=TEXT,
                          fieldbackground=CARD, borderwidth=0, font=("Arial", 12), rowheight=32)
        style2.configure("PKR.Treeview.Heading", background="#1E2130", foreground=SUBTEXT,
                          font=("Arial", 11, "bold"), borderwidth=0)
        style2.map("PKR.Treeview", background=[("selected","#1A2E22")], foreground=[("selected",ACCENT)])

        cols = ("ID", "Nombre", "Precio", "Stock")
        tree2 = ttk.Treeview(card, columns=cols, show="headings", style="PKR.Treeview")
        for col, w in zip(cols, [60, 280, 110, 80]):
            tree2.heading(col, text=col)
            tree2.column(col, width=w, anchor="center" if col in ("ID","Stock") else "w")
        tree2.column("Precio", anchor="e")
        tree2.pack(fill="both", expand=True, padx=12, pady=12)

        def _load(q=""):
            for i in tree2.get_children(): tree2.delete(i)
            conn = create_connection(); cur = conn.cursor()
            cur.execute("""SELECT id, name, price, stock FROM products
                           WHERE (name LIKE ? OR CAST(id AS TEXT) LIKE ?) AND stock > 0
                           ORDER BY name""", (f"%{q}%", f"%{q}%"))
            for row in cur.fetchall():
                tree2.insert("", "end", values=(row[0], row[1], f"${row[2]:,.2f}", row[3]))
            conn.close()

        def _on_key(e=None): _load(search_e.get().strip())
        search_e.bind("<KeyRelease>", _on_key)

        def _confirm(e=None):
            sel = tree2.selection()
            if not sel: return
            v = tree2.item(sel[0], "values")
            self._select_product((int(v[0]), v[1],
                                   float(v[2].replace("$","").replace(",","")),
                                   int(v[3])))
            win.destroy()

        tree2.bind("<Double-1>", _confirm)
        ctk.CTkButton(win, text="✔  Seleccionar", height=40, corner_radius=8,
                      fg_color=ACCENT, hover_color="#2EBF7A", text_color="#0F1117",
                      font=("Arial", 13, "bold"), command=_confirm).pack(padx=20, pady=(0, 16))
        _load()

    # ═══════════════════════════════════════════
    # AGREGAR AL CARRITO
    # ═══════════════════════════════════════════

    def add_to_cart(self):
        if not self._selected_product:
            # Intentar buscar por lo que hay en el campo
            q = self.product_search.get().strip()
            if q.isdigit():
                conn = create_connection(); cur = conn.cursor()
                cur.execute("SELECT id, name, price, stock FROM products WHERE id=?", (q,))
                row = cur.fetchone(); conn.close()
                if row:
                    self._selected_product = {"id": row[0], "name": row[1],
                                               "price": row[2], "stock": row[3]}
            if not self._selected_product:
                error_message("Error", "Seleccione un producto de la lista de búsqueda."); return

        qty_str = self.quantity_entry.get().strip()
        if not qty_str:
            error_message("Error", "Ingrese la cantidad."); return

        try:
            quantity = int(qty_str)
            if quantity <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Error", "La cantidad debe ser un número entero positivo."); return

        # Descuento por producto
        try:
            item_disc = float(self.item_disc_entry.get().strip() or 0)
            if not (0 <= item_disc <= 100): raise ValueError
        except ValueError:
            messagebox.showerror("Error", "El descuento debe ser un número entre 0 y 100."); return

        p     = self._selected_product
        stock = p["stock"]
        if quantity > stock:
            messagebox.showerror("Error", f"Stock insuficiente.\nDisponible: {stock} unidades."); return

        price_orig   = p["price"]
        price_disc   = price_orig * (1 - item_disc / 100)
        total        = round(quantity * price_disc, 2)

        self.cart.append({
            "product_id": str(p["id"]),
            "pid_int":    p["id"],
            "name":       p["name"],
            "quantity":   quantity,
            "price":      price_disc,
            "price_orig": price_orig,
            "discount":   item_disc,
            "total":      total
        })

        disc_str = f"{item_disc:.0f}%" if item_disc > 0 else "—"
        iid = self.tree.insert("", "end", values=(
            p["name"], quantity, f"${price_orig:,.2f}", disc_str, f"${total:,.2f}"
        ))
        self.update_total()
        self._flash_row(iid)
        self._show_toast(f"✔  {p['name']} x{quantity} agregado al carrito")

        # Limpiar
        self._selected_product = None
        self.product_search.delete(0, "end")
        self.quantity_entry.delete(0, "end")
        self.item_disc_entry.delete(0, "end")

    # ═══════════════════════════════════════════
    # TOTALES CON DESCUENTO GLOBAL
    # ═══════════════════════════════════════════

    def update_total(self):
        subtotal = sum(i["total"] for i in self.cart)
        try:
            g_disc = float(self.global_disc_entry.get().strip() or 0)
            g_disc = max(0, min(100, g_disc))
        except ValueError:
            g_disc = 0.0

        descuento = subtotal * g_disc / 100
        total     = subtotal - descuento

        self.subtotal_lbl.configure(text=f"${subtotal:,.2f}")
        self.total_label.configure(text=f"${total:,.2f}")

        if g_disc > 0:
            self.discount_lbl.configure(text=f"Descuento global: -${descuento:,.2f}  ({g_disc:.0f}%)")
        else:
            self.discount_lbl.configure(text="")

    def _get_final_total(self):
        subtotal = sum(i["total"] for i in self.cart)
        try:
            g_disc = float(self.global_disc_entry.get().strip() or 0)
            g_disc = max(0, min(100, g_disc))
        except ValueError:
            g_disc = 0.0
        return round(subtotal * (1 - g_disc / 100), 2)

    # ═══════════════════════════════════════════
    # ELIMINAR DEL CARRITO
    # ═══════════════════════════════════════════

    def remove_product(self):
        selected = self.tree.selection()
        if not selected:
            warning_message("Advertencia", "Seleccione un producto de la tabla."); return
        item = selected[0]
        name = self.tree.item(item, "values")[0]
        for p in self.cart:
            if p["name"] == name:
                self.cart.remove(p); break
        self.tree.delete(item)
        self.update_total()

    # ═══════════════════════════════════════════
    # PREVISUALIZAR PDF (sin guardar en BD)
    # ═══════════════════════════════════════════

    def preview_pdf(self):
        if not self.cart:
            messagebox.showerror("Error", "El carrito está vacío."); return

        customer = self.customer_entry.get().strip() or "Previsualización"
        total    = self._get_final_total()

        # Generar PDF temporal
        temp_name = f"preview_temp_{datetime.now().strftime('%H%M%S')}.pdf"
        try:
            generate_invoice_pdf("PREVIEW", customer, self.cart, total,
                                  filename=temp_name)
        except TypeError:
            # Si el pdf_generator no acepta filename, usar el default
            generate_invoice_pdf("PREVIEW", customer, self.cart, total)
            temp_name = "Factura_PREVIEW.pdf"

        # Abrir con el visor del sistema
        try:
            os.startfile(temp_name)
        except AttributeError:
            import subprocess
            subprocess.run(["xdg-open", temp_name])
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el PDF:\n{e}")

    # ═══════════════════════════════════════════
    # GENERAR FACTURA
    # ═══════════════════════════════════════════

    def generate_invoice(self):
        customer = self.customer_entry.get().strip()
        if not customer:
            messagebox.showerror("Error", "Ingrese el nombre del cliente."); return
        if not self.cart:
            messagebox.showerror("Error", "El carrito está vacío."); return

        total    = self._get_final_total()
        user     = session.current_user
        username = user[1] if isinstance(user, tuple) else str(user)

        conn = create_connection(); cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO invoices (customer_name, total, purchase_date, employee) VALUES (?,?,?,?)",
            (customer, total, datetime.now().strftime("%Y-%m-%d"), username)
        )
        invoice_id = cursor.lastrowid

        for item in self.cart:
            cursor.execute(
                "INSERT INTO invoice_items (invoice_id, product_id, product_name, quantity, price, total) VALUES (?,?,?,?,?,?)",
                (invoice_id, item.get("pid_int"), item["name"],
                 item["quantity"], item["price"], item["total"])
            )
            cursor.execute("UPDATE products SET stock = stock - ? WHERE id=?",
                           (item["quantity"], item["product_id"]))

        conn.commit(); conn.close()

        pdf_file = generate_invoice_pdf(invoice_id, customer, self.cart, total)
        success_message("Factura Generada",
                        f"Factura #{invoice_id} creada exitosamente.\n\nPDF guardado en:\n{pdf_file}")
        write_log(f"Factura #{invoice_id} | Cliente: {customer} | Total: ${total:.2f}")

        # Abrir PDF automáticamente
        try:
            os.startfile(pdf_file)
        except Exception:
            pass

        self.clear_invoice()

    # ═══════════════════════════════════════════
    # LIMPIAR
    # ═══════════════════════════════════════════

    def clear_invoice(self):
        self.customer_entry.delete(0, "end")
        self.product_search.delete(0, "end")
        self.quantity_entry.delete(0, "end")
        self.item_disc_entry.delete(0, "end")
        self.global_disc_entry.delete(0, "end")
        self._selected_product = None
        self.cart.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.update_total()