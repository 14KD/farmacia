"""
ui/purchases_ui.py — Módulo de Compras.
Encabezado + detalle editable, con cálculo automático de subtotal/ITBIS/
descuento/total. Al guardar, registra purchases + purchase_details y crea
un lote por línea (reutilizando el mecanismo de lotes/FEFO de Lotes y
Ventas) para actualizar el inventario automáticamente — ver
database/purchases.py.
Diseño consistente con ui/invoices_ui.py y ui/lots_ui.py.
"""
import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import date, datetime

import config
from database.connection import create_connection
from database.purchases import (register_purchase, update_purchase,
                                 search_purchases, get_purchase_detail)
from ui.predictive_search import PredictiveSearch
from ui.live_search import LiveSearch
from ui.date_field import DateField
from auth import session
from utils.notifications import success_message, error_message, warning_message
from utils.logger import audit


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
PURPLE       = "#C084FC"
INPUT_BG     = "#23263A"
INPUT_BORDER = "#2E3148"

PAYMENT_METHODS = ["Efectivo", "Transferencia", "Cheque", "Crédito"]


class PurchasesUI:

    def __init__(self, parent):
        self.parent = parent
        self.items  = []   # detalle de la compra en curso
        self._editing_purchase_id = None   # None = compra nueva; int = editando esta compra
        self._editing_item_meta   = None   # pd_id/lot_id de la línea que se está reeditando

        container = ctk.CTkFrame(parent, fg_color=BG, corner_radius=0)
        container.pack(fill="both", expand=True)

        # ══════════════════════════════════════
        # ENCABEZADO
        # ══════════════════════════════════════
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 0))
        ctk.CTkLabel(header, text="🛒  Compras",
                     font=("Arial", 22, "bold"), text_color=TEXT).pack(side="left")
        ctk.CTkFrame(container, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=20, pady=(10, 12))

        # ══════════════════════════════════════
        # TABS: Registrar Compra | Consultar Facturas
        # ══════════════════════════════════════
        self.tabs = ctk.CTkTabview(
            container,
            fg_color=CARD, corner_radius=12,
            segmented_button_fg_color="#1E2130",
            segmented_button_selected_color=ACCENT,
            segmented_button_selected_hover_color="#2EBF7A",
            segmented_button_unselected_color="#1E2130",
            segmented_button_unselected_hover_color="#252836",
            text_color=TEXT, text_color_disabled=SUBTEXT
        )
        self.tabs.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        for tab in ["🧾  Registrar Compra", "🔍  Consultar Facturas"]:
            self.tabs.add(tab)

        self._build_register(self.tabs.tab("🧾  Registrar Compra"))
        self._build_query(self.tabs.tab("🔍  Consultar Facturas"))

    # ═══════════════════════════════════════════
    # TAB 1 — REGISTRAR COMPRA
    # ═══════════════════════════════════════════
    def _build_register(self, parent):
        # Aviso de modo edición — oculto por defecto, se muestra desde
        # load_purchase_for_edit() cuando se está editando una compra ya guardada.
        self.edit_banner = ctk.CTkFrame(parent, fg_color="#1A2E3A", corner_radius=8,
                                         border_width=1, border_color=CYAN)
        self.edit_banner_lbl = ctk.CTkLabel(self.edit_banner, text="", font=("Arial", 12, "bold"),
                                             text_color=CYAN)
        self.edit_banner_lbl.pack(side="left", padx=14, pady=10)
        ctk.CTkButton(self.edit_banner, text="✖  Cancelar edición", height=28, corner_radius=6,
                      fg_color="transparent", hover_color="#2E3148", text_color=SUBTEXT,
                      font=("Arial", 11), command=self.clear_form
                      ).pack(side="right", padx=14, pady=6)

        hdr_card = self.hdr_card = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=12,
                                 border_width=1, border_color=CARD_BORDER)
        hdr_card.pack(fill="x", padx=20, pady=(0, 8))
        self._card_header(hdr_card, "Datos de la Compra")

        r1 = ctk.CTkFrame(hdr_card, fg_color="transparent")
        r1.pack(fill="x", padx=16, pady=(0, 8))
        r1.columnconfigure((0, 1, 2), weight=1)

        self.invoice_entry = self._lbl_entry(r1, "N° de Factura", 0,
                                              placeholder="FAC-2024-001")
        self.date_field = self._date_col(r1, "Fecha de Compra", 1,
                                          value=date.today().isoformat())

        pay_w = ctk.CTkFrame(r1, fg_color="transparent")
        pay_w.grid(row=0, column=2, padx=(0, 0), sticky="ew")
        ctk.CTkLabel(pay_w, text="Método de Pago", font=("Arial", 11),
                     text_color=SUBTEXT).pack(anchor="w", padx=2)
        self.payment_var = ctk.StringVar(value=PAYMENT_METHODS[0])
        ctk.CTkOptionMenu(pay_w, variable=self.payment_var, values=PAYMENT_METHODS,
                          fg_color=INPUT_BG, button_color="#2A2D3A",
                          button_hover_color="#3A3D52", dropdown_fg_color="#1A1D27",
                          dropdown_hover_color="#1A2E22", text_color=TEXT,
                          font=("Arial", 12), height=38, dynamic_resizing=False,
                          command=self._on_payment_method_change
                          ).pack(fill="x", pady=(3, 0))

        # Fecha de vencimiento de pago — solo visible/obligatoria si el
        # método de pago es "Crédito" (ver _on_payment_method_change).
        self.due_date_wrap = ctk.CTkFrame(hdr_card, fg_color="transparent")
        self.due_date_field = self._date_col(self.due_date_wrap,
                                              "Fecha de Vencimiento de Pago (crédito)", 0,
                                              padx=(0, 0))
        self.due_date_wrap.columnconfigure(0, weight=1)

        r2 = self.r2 = ctk.CTkFrame(hdr_card, fg_color="transparent")
        r2.pack(fill="x", padx=16, pady=(0, 8))
        r2.columnconfigure((0, 1), weight=1)

        sup_w = ctk.CTkFrame(r2, fg_color="transparent")
        sup_w.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        ctk.CTkLabel(sup_w, text="Proveedor (buscar por nombre, teléfono o email)",
                     font=("Arial", 11), text_color=SUBTEXT).pack(anchor="w", padx=2)
        self._supplier_lookup = {}
        self._selected_supplier_id = None
        self.supplier_search = LiveSearch(
            sup_w,
            query_fn=self._suggest_suppliers,
            on_select=self._on_supplier_selected,
            on_change=lambda t: setattr(self, "_selected_supplier_id", None),
            placeholder="🔍  Escribir nombre del proveedor...",
        )
        self.supplier_search.pack(fill="x", pady=(3, 0))

        self._info_block(r2, "👤  Usuario", self._current_username(), CYAN, 1)

        r3 = ctk.CTkFrame(hdr_card, fg_color="transparent")
        r3.pack(fill="x", padx=16, pady=(0, 14))
        ctk.CTkLabel(r3, text="Observaciones", font=("Arial", 11),
                     text_color=SUBTEXT).pack(anchor="w", padx=2)
        obs_ef = ctk.CTkFrame(r3, fg_color=INPUT_BG, corner_radius=8,
                               border_width=1, border_color=INPUT_BORDER)
        obs_ef.pack(fill="x", pady=(3, 0))
        self.notes_entry = ctk.CTkEntry(obs_ef, border_width=0, fg_color="transparent",
                                         height=38, font=("Arial", 13), text_color=TEXT,
                                         placeholder_text="Observación (opcional)...")
        self.notes_entry.pack(fill="x", padx=8)

        # ══════════════════════════════════════
        # TARJETA: AGREGAR PRODUCTO
        # ══════════════════════════════════════
        prod_card = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=12,
                                  border_width=1, border_color=CARD_BORDER)
        prod_card.pack(fill="x", padx=20, pady=(0, 8))
        self._card_header(prod_card, "Agregar Producto")

        pf = ctk.CTkFrame(prod_card, fg_color="transparent")
        pf.pack(fill="x", padx=16, pady=(0, 6))
        ctk.CTkLabel(pf, text="Buscar Producto (nombre, principio activo o ID)",
                     font=("Arial", 11), text_color=SUBTEXT).pack(anchor="w", padx=2)
        self.product_search = PredictiveSearch(
            pf, on_select=self._on_product_selected,
            placeholder="🔍  Escribir nombre, principio activo o ID...",
            show_picker_btn=True
        )
        self.product_search.pack(fill="x", pady=(3, 0))
        self._selected_product = None

        cfg0 = config.load()

        rb = ctk.CTkFrame(prod_card, fg_color="transparent")
        rb.pack(fill="x", padx=16, pady=(0, 6))
        rb.columnconfigure((0, 1, 2), weight=1)
        self.qty_entry  = self._lbl_entry(rb, "Cantidad", 0)
        self.cost_entry = self._lbl_entry(rb, "Precio de Compra", 1)
        self.disc_entry = self._lbl_entry(rb, "Descuento %", 2)
        # ITBIS: ya no se captura aquí, se toma del producto (Productos > ¿Aplica ITBIS?)

        rc = ctk.CTkFrame(prod_card, fg_color="transparent")
        rc.pack(fill="x", padx=16, pady=(0, 10))
        rc.columnconfigure((0, 1), weight=1)
        self.batch_entry = self._lbl_entry(rc, "N° de Lote", 0,
                                            placeholder="LOT-2024-001")
        self.expiry_field = self._date_col(rc, "Fecha de Vencimiento *", 1)

        btn_row = ctk.CTkFrame(prod_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 14))
        self.btn_add = ctk.CTkButton(btn_row, text="➕  Agregar Producto",
                      height=40, corner_radius=8,
                      fg_color=ACCENT, hover_color="#2EBF7A",
                      text_color="#0F1117", font=("Arial", 13, "bold"),
                      command=self.add_item)
        self.btn_add.pack(side="left", padx=(0, 8))
        # "Editar Producto" solo se muestra cuando hay una fila seleccionada
        # con clic en la tabla de detalle (ver _on_tree_select).
        self.btn_edit = ctk.CTkButton(btn_row, text="✏  Editar Producto",
                      height=40, corner_radius=8,
                      fg_color="#1A2E3A", hover_color="#1E6A9A",
                      text_color=CYAN, font=("Arial", 12),
                      command=self.edit_item)
        self.btn_remove = ctk.CTkButton(btn_row, text="🗑  Eliminar Producto",
                      height=40, corner_radius=8,
                      fg_color="#2E1A1A", hover_color=DANGER_H,
                      text_color=DANGER, font=("Arial", 12),
                      command=self.remove_item)
        self.btn_remove.pack(side="left")

        # ══════════════════════════════════════
        # TABLA DE DETALLE
        # ══════════════════════════════════════
        table_card = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=12,
                                   border_width=1, border_color=CARD_BORDER)
        table_card.pack(fill="x", padx=20, pady=(0, 8))
        self._card_header(table_card, "Detalle de la Compra")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("PUR.Treeview", background="#1A1D27", foreground="#FFFFFF",
                         fieldbackground="#1A1D27", borderwidth=0,
                         font=("Arial", 11), rowheight=30)
        style.configure("PUR.Treeview.Heading", background="#1E2130",
                         foreground="#8B8FA8", font=("Arial", 10, "bold"), borderwidth=0)
        style.map("PUR.Treeview",
                  background=[("selected", "#1A2E22"), ("!selected", "#1A1D27")],
                  foreground=[("selected", "#3DD68C"), ("!selected", "#FFFFFF")])

        cols = ("Código", "Producto", "Lote", "Vence", "Cantidad",
                "Precio", "ITBIS", "Descuento", "Subtotal", "Total")
        widths  = {"Código": 60, "Producto": 190, "Lote": 100, "Vence": 90,
                   "Cantidad": 70, "Precio": 90, "ITBIS": 80,
                   "Descuento": 80, "Subtotal": 90, "Total": 100}
        anchors = {"Código": "center", "Producto": "w", "Lote": "center", "Vence": "center",
                   "Cantidad": "center", "Precio": "e", "ITBIS": "e",
                   "Descuento": "e", "Subtotal": "e", "Total": "e"}
        self.tree = ttk.Treeview(table_card, columns=cols, show="headings",
                                  height=8, style="PUR.Treeview")
        try:
            self.tree.configure(style=self.tree["style"])
            self.tree.tk.call("ttk::style", "configure", self.tree["style"], "-fieldbackground", "#1A1D27")
            self.tree.tk.call("ttk::style", "configure", self.tree["style"], "-background", "#1A1D27")
            self.tree.tk.call("ttk::style", "configure", self.tree["style"], "-foreground", "#FFFFFF")
        except Exception:
            pass
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=widths[col], anchor=anchors[col])
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.pack(fill="x", padx=14, pady=(0, 12))

        # ══════════════════════════════════════
        # TOTALES + ACCIONES
        # ══════════════════════════════════════
        bottom_card = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=12,
                                    border_width=1, border_color=CARD_BORDER)
        bottom_card.pack(fill="x", padx=20, pady=(0, 20))

        brow = ctk.CTkFrame(bottom_card, fg_color="transparent")
        brow.pack(fill="x", padx=20, pady=14)

        btn_col = ctk.CTkFrame(brow, fg_color="transparent")
        btn_col.pack(side="left")

        self.btn_save = ctk.CTkButton(btn_col, text="✔  Guardar Compra",
                      height=50, width=210, corner_radius=10,
                      fg_color=ACCENT, hover_color="#2EBF7A",
                      text_color="#0F1117", font=("Arial", 14, "bold"),
                      command=self.save_purchase)
        self.btn_save.pack(pady=(0, 8))

        ctk.CTkButton(btn_col, text="✖  Cancelar",
                      height=38, width=210, corner_radius=10,
                      fg_color=INPUT_BG, hover_color="#2E3148",
                      text_color=SUBTEXT, font=("Arial", 12),
                      command=self.cancel_purchase).pack()

        totals = ctk.CTkFrame(brow, fg_color=INPUT_BG, corner_radius=12)
        totals.pack(side="right", padx=(20, 0), ipadx=16, ipady=10)

        cy0 = cfg0["billing"].get("currency", "RD$")
        self.subtotal_lbl = self._total_row(totals, "Subtotal:",  f"{cy0} 0.00", TEXT,    0)
        self.tax_lbl      = self._total_row(totals, "ITBIS:",     f"{cy0} 0.00", TEXT,    1)
        self.disc_lbl     = self._total_row(totals, "Descuento:", f"{cy0} 0.00", SUBTEXT, 2)
        ctk.CTkFrame(totals, height=1, fg_color=CARD_BORDER).grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=6)
        self.total_lbl    = self._total_row(totals, "TOTAL:", f"{cy0} 0.00", ACCENT, 4, large=True)

    # ═══════════════════════════════════════════
    # TAB 2 — CONSULTAR FACTURAS
    # ═══════════════════════════════════════════
    def _build_query(self, parent):
        fcard = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=12,
                              border_width=1, border_color=CARD_BORDER)
        fcard.pack(fill="x", padx=4, pady=(4, 8))
        self._card_header(fcard, "🔍  Filtros")

        fr = ctk.CTkFrame(fcard, fg_color="transparent")
        fr.pack(fill="x", padx=16, pady=(0, 4))
        fr.columnconfigure((0, 1, 2, 3), weight=1)

        self.q_supplier = self._lbl_entry(fr, "Proveedor", 0)
        self.q_invoice  = self._lbl_entry(fr, "N° de Factura", 1)
        self.q_date_from = self._date_col(fr, "Desde", 2,
                                           value=date.today().replace(day=1).isoformat())
        self.q_date_to   = self._date_col(fr, "Hasta", 3, value=date.today().isoformat())

        br = ctk.CTkFrame(fcard, fg_color="transparent")
        br.pack(fill="x", padx=16, pady=(0, 14))
        ctk.CTkButton(br, text="🔍  Buscar", height=38, corner_radius=8,
                      fg_color=ACCENT, hover_color="#2EBF7A",
                      text_color="#0F1117", font=("Arial", 12, "bold"),
                      command=self.search_invoices).pack(side="left")

        tc = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=12,
                           border_width=1, border_color=CARD_BORDER)
        tc.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        ctk.CTkLabel(tc, text="💡  Doble clic sobre una factura para ver su detalle completo",
                     font=("Arial", 10), text_color="#3A3D52").pack(anchor="e", padx=16, pady=(8, 2))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("PURQ.Treeview", background="#1A1D27", foreground="#FFFFFF",
                         fieldbackground="#1A1D27", borderwidth=0,
                         font=("Arial", 11), rowheight=30)
        style.configure("PURQ.Treeview.Heading", background="#1E2130",
                         foreground="#8B8FA8", font=("Arial", 10, "bold"), borderwidth=0)
        style.map("PURQ.Treeview",
                  background=[("selected", "#1A2E22"), ("!selected", "#1A1D27")],
                  foreground=[("selected", "#3DD68C"), ("!selected", "#FFFFFF")])

        cols = ("ID", "Fecha", "Proveedor", "N° Factura", "Pago",
                "Subtotal", "ITBIS", "Descuento", "Total", "Estado")
        widths  = {"ID": 55, "Fecha": 130, "Proveedor": 170, "N° Factura": 110,
                   "Pago": 100, "Subtotal": 90, "ITBIS": 80, "Descuento": 85,
                   "Total": 100, "Estado": 90}
        anchors = {"ID": "center", "Fecha": "center", "Proveedor": "w", "N° Factura": "center",
                   "Pago": "center", "Subtotal": "e", "ITBIS": "e",
                   "Descuento": "e", "Total": "e", "Estado": "center"}
        self.q_tree = ttk.Treeview(tc, columns=cols, show="headings",
                                    height=14, style="PURQ.Treeview")
        try:
            self.q_tree.configure(style=self.q_tree["style"])
            self.q_tree.tk.call("ttk::style", "configure", self.q_tree["style"], "-fieldbackground", "#1A1D27")
            self.q_tree.tk.call("ttk::style", "configure", self.q_tree["style"], "-background", "#1A1D27")
            self.q_tree.tk.call("ttk::style", "configure", self.q_tree["style"], "-foreground", "#FFFFFF")
        except Exception:
            pass
        for col in cols:
            self.q_tree.heading(col, text=col)
            self.q_tree.column(col, width=widths[col], anchor=anchors[col])
        self.q_tree.bind("<Double-1>", self._show_purchase_detail)
        self.q_tree.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.search_invoices()

    def search_invoices(self):
        cy = self._currency()
        rows = search_purchases(
            supplier_name=self.q_supplier.get().strip(),
            invoice_number=self.q_invoice.get().strip(),
            date_from=self.q_date_from.get().strip() or None,
            date_to=self.q_date_to.get().strip() or None,
        )
        for i in self.q_tree.get_children():
            self.q_tree.delete(i)
        for r in rows:
            (pid, pdate, supplier, invoice_number, payment,
             subtotal, tax, discount, total, status) = r
            pdate_str = pdate.strftime("%d/%m/%Y %H:%M") if hasattr(pdate, "strftime") else str(pdate)
            self.q_tree.insert("", "end", values=(
                pid, pdate_str, supplier, invoice_number or "—", payment or "—",
                f"{cy} {float(subtotal or 0):,.2f}",
                f"{cy} {float(tax or 0):,.2f}",
                f"{cy} {float(discount or 0):,.2f}",
                f"{cy} {float(total or 0):,.2f}",
                (status or "").upper(),
            ))

    def _show_purchase_detail(self, event=None):
        sel = self.q_tree.selection()
        if not sel:
            return
        purchase_id = int(self.q_tree.item(sel[0], "values")[0])
        header, lines = get_purchase_detail(purchase_id)
        if not header:
            error_message("Error", "No se pudo cargar la compra."); return

        (pid, pdate, supplier_id, supplier, invoice_number, payment, due_date,
         subtotal, tax, discount, total, notes, status) = header
        cy = self._currency()
        pdate_str = pdate.strftime("%d/%m/%Y %H:%M") if hasattr(pdate, "strftime") else str(pdate)
        due_str = (due_date.strftime("%d/%m/%Y") if hasattr(due_date, "strftime")
                   else due_date) if due_date else None

        win = ctk.CTkToplevel(self.parent)
        win.title(f"Compra #{pid} — {supplier}")
        win.geometry("820x520")
        win.configure(fg_color=BG)
        win.grab_set()

        ctk.CTkLabel(win, text=f"🧾  Compra #{pid}  —  {supplier}",
                     font=("Arial", 16, "bold"), text_color=TEXT
                     ).pack(padx=20, pady=(20, 2), anchor="w")
        info_text = (f"Factura: {invoice_number or '—'}   |   Fecha: {pdate_str}   |   "
                     f"Pago: {payment or '—'}   |   Estado: {(status or '').upper()}")
        if due_str:
            info_text += f"   |   Vence pago: {due_str}"
        ctk.CTkLabel(win, text=info_text, font=("Arial", 11), text_color=SUBTEXT
                     ).pack(padx=20, anchor="w")
        ctk.CTkFrame(win, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=20, pady=(10, 10))

        mc = ctk.CTkFrame(win, fg_color=CARD, corner_radius=12,
                           border_width=1, border_color=CARD_BORDER)
        mc.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        style = ttk.Style(); style.theme_use("clam")
        style.configure("PURD.Treeview", background="#1A1D27", foreground="#FFFFFF",
                         fieldbackground="#1A1D27", borderwidth=0,
                         font=("Arial", 10), rowheight=28)
        style.configure("PURD.Treeview.Heading", background="#1E2130",
                         foreground="#8B8FA8", font=("Arial", 9, "bold"), borderwidth=0)

        dcols = ("Producto", "Lote", "Vence", "Cantidad", "Costo", "ITBIS", "Descuento", "Subtotal", "Total")
        t = ttk.Treeview(mc, columns=dcols, show="headings", style="PURD.Treeview")
        for col, w, anc in [("Producto", 190, "w"), ("Lote", 90, "center"), ("Vence", 85, "center"),
                             ("Cantidad", 70, "center"), ("Costo", 85, "e"), ("ITBIS", 75, "e"),
                             ("Descuento", 80, "e"), ("Subtotal", 85, "e"), ("Total", 90, "e")]:
            t.heading(col, text=col); t.column(col, width=w, anchor=anc)
        for line in lines:
            (_pd_id, _prod_id, prod_name, batch, expiry, qty, unit_cost,
             ltax, ldisc, lsub, ltot, _lot_id) = line
            expiry_str = expiry.strftime("%d/%m/%Y") if hasattr(expiry, "strftime") else (expiry or "—")
            t.insert("", "end", values=(
                prod_name, batch or "—", expiry_str, qty,
                f"{cy} {float(unit_cost or 0):,.2f}", f"{cy} {float(ltax or 0):,.2f}",
                f"{cy} {float(ldisc or 0):,.2f}", f"{cy} {float(lsub or 0):,.2f}",
                f"{cy} {float(ltot or 0):,.2f}",
            ))
        t.pack(fill="both", expand=True, padx=12, pady=12)

        totals_row = ctk.CTkFrame(win, fg_color="transparent")
        totals_row.pack(fill="x", padx=20, pady=(0, 6))
        ctk.CTkLabel(totals_row,
                     text=(f"Subtotal: {cy} {float(subtotal or 0):,.2f}   |   "
                           f"ITBIS: {cy} {float(tax or 0):,.2f}   |   "
                           f"Descuento: {cy} {float(discount or 0):,.2f}"),
                     font=("Arial", 12), text_color=SUBTEXT).pack(side="left")
        ctk.CTkLabel(totals_row, text=f"TOTAL: {cy} {float(total or 0):,.2f}",
                     font=("Arial", 15, "bold"), text_color=ACCENT).pack(side="right")

        if notes:
            ctk.CTkLabel(win, text=f"Observaciones: {notes}", font=("Arial", 11),
                         text_color=SUBTEXT, wraplength=760, justify="left"
                         ).pack(padx=20, anchor="w", pady=(0, 6))

        btns = ctk.CTkFrame(win, fg_color="transparent")
        btns.pack(fill="x", padx=20, pady=(0, 16))

        def _open_edit(pid=pid):
            win.destroy()
            self.load_purchase_for_edit(pid)

        ctk.CTkButton(btns, text="✏  Editar Compra", height=38, corner_radius=8,
                      fg_color="#1A2E3A", hover_color="#1E6A9A",
                      text_color=CYAN, font=("Arial", 12, "bold"),
                      command=_open_edit).pack(side="left")

        ctk.CTkButton(btns, text="Cerrar", height=38, corner_radius=8,
                      fg_color=INPUT_BG, hover_color="#2E3148",
                      text_color=TEXT, font=("Arial", 12),
                      command=win.destroy).pack(side="right")

    def load_purchase_for_edit(self, purchase_id: int):
        """Carga una compra ya guardada en la pestaña Registrar para editarla."""
        header, lines = get_purchase_detail(purchase_id)
        if not header:
            error_message("Error", f"No se pudo cargar la compra #{purchase_id}."); return

        (pid, pdate, supplier_id, supplier_name, invoice_number, payment, due_date,
         subtotal, tax, discount, total, notes, status) = header
        pdate_str = pdate.strftime("%Y-%m-%d") if hasattr(pdate, "strftime") else str(pdate)[:10]
        due_date_str = (due_date.isoformat() if hasattr(due_date, "isoformat")
                         else due_date) if due_date else ""

        self.items.clear()
        for line in lines:
            (pd_id, prod_id, prod_name, batch, expiry, qty, unit_cost,
             ltax, ldisc, lsub, ltot, lot_id) = line
            qty       = int(qty)
            unit_cost = float(unit_cost or 0)
            lsub      = float(lsub or 0)
            ltax      = float(ltax or 0)
            ldisc     = float(ldisc or 0)
            expiry_str = expiry.isoformat() if hasattr(expiry, "isoformat") else expiry
            self.items.append({
                "product_id": prod_id, "product_name": prod_name,
                "batch": batch or "", "expiration_date": expiry_str,
                "quantity": qty, "unit_cost": unit_cost,
                "disc_pct": round(ldisc / lsub * 100, 2) if lsub else 0.0,
                "tax_pct":  round(ltax  / lsub * 100, 2) if lsub else 0.0,
                "discount": ldisc, "tax": ltax, "subtotal": lsub, "total": float(ltot or 0),
                "pd_id": pd_id, "lot_id": lot_id,
            })

        self.tabs.set("🧾  Registrar Compra")

        self.invoice_entry.delete(0, "end")
        self.invoice_entry.insert(0, invoice_number or "")
        self.date_field.set(pdate_str)
        self.payment_var.set(payment or PAYMENT_METHODS[0])
        self._on_payment_method_change()   # muestra/oculta el campo según el método cargado
        self.due_date_field.set(due_date_str)
        self.supplier_search.set(supplier_name)
        self._selected_supplier_id = supplier_id
        self.notes_entry.delete(0, "end")
        self.notes_entry.insert(0, notes or "")

        self._clear_item_form()
        self._refresh_tree()

        self._editing_purchase_id = purchase_id
        self.edit_banner_lbl.configure(
            text=f"✏  Editando Compra #{purchase_id} — los cambios en cantidad/costo "
                 f"ajustarán el inventario automáticamente.")
        self.edit_banner.pack(fill="x", padx=20, pady=(0, 8), before=self.hdr_card)
        self.btn_save.configure(text="💾  Guardar Cambios")

    # ═══════════════════════════════════════════
    # HELPERS DE UI
    # ═══════════════════════════════════════════

    def _card_header(self, parent, text):
        ctk.CTkLabel(parent, text=text, font=("Arial", 12, "bold"),
                     text_color=SUBTEXT).pack(anchor="w", padx=16, pady=(12, 2))
        ctk.CTkFrame(parent, height=1, fg_color=CARD_BORDER).pack(
            fill="x", padx=16, pady=(0, 8))

    def _info_block(self, parent, label, value, color, col):
        f = ctk.CTkFrame(parent, fg_color=INPUT_BG, corner_radius=10)
        f.grid(row=0, column=col, padx=(0, 0), sticky="ew")
        ctk.CTkLabel(f, text=label, font=("Arial", 10),
                     text_color=SUBTEXT).pack(anchor="w", padx=12, pady=(8, 0))
        ctk.CTkLabel(f, text=value, font=("Arial", 15, "bold"),
                     text_color=color).pack(anchor="w", padx=12, pady=(0, 8))

    def _lbl_entry(self, parent, label, col, padx=(0, 10), placeholder=""):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=0, column=col, padx=padx, pady=(0, 10), sticky="ew")
        ctk.CTkLabel(f, text=label, font=("Arial", 11),
                     text_color=SUBTEXT).pack(anchor="w", padx=2)
        ef = ctk.CTkFrame(f, fg_color=INPUT_BG, corner_radius=8,
                           border_width=1, border_color=INPUT_BORDER)
        ef.pack(fill="x", pady=(3, 0))
        e = ctk.CTkEntry(ef, border_width=0, fg_color="transparent",
                          height=38, font=("Arial", 13), text_color=TEXT,
                          placeholder_text=placeholder)
        e.pack(fill="x", padx=8)
        return e

    def _date_col(self, parent, label, col, padx=(0, 10), value=""):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=0, column=col, padx=padx, pady=(0, 10), sticky="ew")
        field = DateField(f, label=label, value=value)
        field.pack(fill="x")
        return field

    def _total_row(self, parent, label, value, color, row, large=False):
        font_lbl = ("Arial", 12) if not large else ("Arial", 13, "bold")
        font_val = ("Arial", 14, "bold") if not large else ("Arial", 24, "bold")
        ctk.CTkLabel(parent, text=label, font=font_lbl,
                     text_color=SUBTEXT).grid(row=row, column=0, sticky="w", pady=1)
        lbl = ctk.CTkLabel(parent, text=value, font=font_val, text_color=color)
        lbl.grid(row=row, column=1, sticky="e", padx=(24, 0), pady=1)
        return lbl

    def _current_username(self):
        u = session.current_user
        return u[1] if isinstance(u, tuple) and len(u) > 1 else str(u or "sistema")

    def _current_user_id(self):
        u = session.current_user
        return u[0] if isinstance(u, tuple) and len(u) > 0 else None

    def _currency(self):
        return config.load()["billing"].get("currency", "$")

    # ═══════════════════════════════════════════
    # PROVEEDOR — BÚSQUEDA
    # ═══════════════════════════════════════════

    def _suggest_suppliers(self, text):
        conn = create_connection(); cur = conn.cursor()
        cur.execute("""SELECT id, name, IFNULL(phone,'') FROM suppliers
                       WHERE name LIKE ? ORDER BY name LIMIT 8""", (f"%{text}%",))
        rows = cur.fetchall(); conn.close()
        self._supplier_lookup = {r[1]: r[0] for r in rows}
        return [(r[1], f"N° {r[0]}" + (f" · Tel: {r[2]}" if r[2] else ""), r[0])
                for r in rows]

    def _on_supplier_selected(self, name, supplier_id=None):
        # El ID viene directo del resultado elegido (más confiable que
        # buscarlo por nombre, que puede repetirse entre proveedores).
        self._selected_supplier_id = supplier_id if supplier_id is not None \
            else self._supplier_lookup.get(name)

    # ═══════════════════════════════════════════
    # MÉTODO DE PAGO — FECHA DE VENCIMIENTO OBLIGATORIA SI ES CRÉDITO
    # ═══════════════════════════════════════════

    def _on_payment_method_change(self, choice=None):
        if self.payment_var.get() == "Crédito":
            if not self.due_date_wrap.winfo_ismapped():
                self.due_date_wrap.pack(fill="x", padx=16, pady=(0, 8), before=self.r2)
        else:
            self.due_date_wrap.pack_forget()
            self.due_date_field.clear()

    # ═══════════════════════════════════════════
    # PRODUCTO — BÚSQUEDA PREDICTIVA
    # ═══════════════════════════════════════════

    def _on_product_selected(self, prod: dict):
        self._selected_product = {
            "id":   prod["id"], "name": prod["name"],
            "manages_lots": bool(prod.get("manages_lots", True)),
            "applies_itbis": bool(prod.get("applies_itbis", True)),
        }
        self.qty_entry.focus()

    # ═══════════════════════════════════════════
    # CÁLCULO DE LÍNEA
    # ═══════════════════════════════════════════

    def _read_item_inputs(self):
        """Lee y valida los campos del formulario de línea. Retorna dict o None
        (mostrando el error correspondiente) si algo es inválido."""
        # Si la compra es a crédito, la fecha de vencimiento de pago debe
        # completarse ANTES de poder agregar productos a la tabla — no solo
        # al guardar la compra completa.
        if self.payment_var.get() == "Crédito" and not self.due_date_field.get().strip():
            error_message("Error",
                "Completa la fecha de vencimiento de pago (compra a crédito) "
                "antes de agregar productos.")
            return None
        if not self._selected_product:
            error_message("Error", "Selecciona un producto de la lista predictiva.")
            return None
        try:
            qty = int(self.qty_entry.get().strip())
            if qty <= 0: raise ValueError
        except ValueError:
            error_message("Error", "La cantidad debe ser un número entero mayor que cero.")
            return None
        try:
            cost = float(self.cost_entry.get().strip() or 0)
            if cost < 0: raise ValueError
        except ValueError:
            error_message("Error", "El precio de compra no puede ser negativo.")
            return None
        # ITBIS: se calcula solo, según lo configurado en el producto.
        if self._selected_product.get("applies_itbis", True):
            tax_pct = float(config.load()["billing"].get("tax_rate", 0))
        else:
            tax_pct = 0.0
        try:
            disc_pct = float(self.disc_entry.get().strip() or 0)
            if not (0 <= disc_pct <= 100): raise ValueError
        except ValueError:
            error_message("Error", "El descuento debe ser un porcentaje entre 0 y 100.")
            return None

        expiry = self.expiry_field.get().strip() or None
        if not expiry:
            error_message("Error",
                "La fecha de vencimiento es obligatoria. Usa el calendario 📅.")
            return None
        try:
            date.fromisoformat(expiry)
        except ValueError:
            error_message("Fecha inválida",
                f"Fecha de vencimiento '{expiry}' no es válida. Usa el calendario 📅.")
            return None

        # Subtotal = Cantidad × Precio (bruto, antes de descuento/ITBIS)
        subtotal = round(qty * cost, 2)
        discount = round(subtotal * disc_pct / 100, 2)
        tax      = round(subtotal * tax_pct / 100, 2)
        total    = round(subtotal + tax - discount, 2)

        # Las columnas de la BD son DECIMAL(10,2) — máximo 99,999,999.99.
        # Validar aquí evita el error crudo de MariaDB ("Out of range value
        # for column 'subtotal'") cuando cantidad × precio da un número
        # gigante por un error de digitación.
        DECIMAL_10_2_MAX = 99_999_999.99
        if max(abs(subtotal), abs(tax), abs(discount), abs(total)) > DECIMAL_10_2_MAX:
            error_message("Error",
                f"El monto de esta línea es demasiado grande "
                f"(subtotal {subtotal:,.2f}). Revisa la cantidad y el precio "
                f"de compra — probablemente sobra un dígito.")
            return None

        # Si se llegó aquí reeditando una línea existente (ver edit_item), se
        # conserva su pd_id/lot_id para que update_purchase() ajuste el MISMO
        # lote en vez de crear uno nuevo. Se consume una sola vez.
        meta = self._editing_item_meta or {}
        self._editing_item_meta = None

        return {
            "product_id":   self._selected_product["id"],
            "product_name": self._selected_product["name"],
            "batch":        self.batch_entry.get().strip(),
            "expiration_date": expiry,
            "quantity":     qty,
            "unit_cost":    cost,
            "disc_pct":     disc_pct,
            "tax_pct":      tax_pct,
            "discount":     discount,
            "tax":          tax,
            "subtotal":     subtotal,
            "total":        total,
            "pd_id":        meta.get("pd_id"),
            "lot_id":       meta.get("lot_id"),
        }

    # ═══════════════════════════════════════════
    # AGREGAR / EDITAR / ELIMINAR PRODUCTO
    # ═══════════════════════════════════════════

    def add_item(self):
        item = self._read_item_inputs()
        if item is None:
            return

        # Productos repetidos en la misma compra (mismo producto + lote +
        # vencimiento) deben sumarse en vez de crear una línea duplicada.
        for existing in self.items:
            if (existing["product_id"] == item["product_id"]
                    and existing["batch"] == item["batch"]
                    and existing["expiration_date"] == item["expiration_date"]):
                existing["quantity"] += item["quantity"]
                existing["subtotal"]  = round(existing["quantity"] * existing["unit_cost"], 2)
                existing["discount"]  = round(existing["subtotal"] * existing["disc_pct"] / 100, 2)
                existing["tax"]       = round(existing["subtotal"] * existing["tax_pct"] / 100, 2)
                existing["total"]     = round(existing["subtotal"] + existing["tax"] - existing["discount"], 2)
                self._refresh_tree()
                self._clear_item_form()
                return

        self.items.append(item)
        self._refresh_tree()
        self._clear_item_form()

    def edit_item(self):
        sel = self.tree.selection()
        if not sel:
            warning_message("Sin selección", "Selecciona una fila de la tabla para editar.")
            return
        idx = self.tree.index(sel[0])
        item = self.items.pop(idx)
        self._refresh_tree()

        # Conservar el enlace a la línea/lote original (si lo tiene) para que,
        # al volver a agregarla, update_purchase() ajuste el MISMO lote en vez
        # de crear uno nuevo (ver _read_item_inputs).
        self._editing_item_meta = {"pd_id": item.get("pd_id"), "lot_id": item.get("lot_id")}

        self._selected_product = {
            "id": item["product_id"], "name": item["product_name"],
            "applies_itbis": item["tax_pct"] > 0,
        }
        self.product_search.set(item["product_name"])
        self.qty_entry.delete(0, "end");   self.qty_entry.insert(0, str(item["quantity"]))
        self.cost_entry.delete(0, "end");  self.cost_entry.insert(0, str(item["unit_cost"]))
        self.disc_entry.delete(0, "end");  self.disc_entry.insert(0, str(item["disc_pct"]))
        self.batch_entry.delete(0, "end"); self.batch_entry.insert(0, item["batch"])
        self.expiry_field.set(item["expiration_date"] or "")
        self.qty_entry.focus()

    def remove_item(self):
        sel = self.tree.selection()
        if not sel:
            warning_message("Sin selección", "Selecciona una fila de la tabla para eliminar.")
            return
        idx = self.tree.index(sel[0])
        self.items.pop(idx)
        self._refresh_tree()

    def _clear_item_form(self):
        self._selected_product = None
        self.product_search.clear()
        self.qty_entry.delete(0, "end")
        self.cost_entry.delete(0, "end")
        self.disc_entry.delete(0, "end")
        self.batch_entry.delete(0, "end")
        self.expiry_field.clear()
        self.product_search.focus()

    def _refresh_tree(self):
        cy = self._currency()
        for i in self.tree.get_children():
            self.tree.delete(i)
        for item in self.items:
            expiry_disp = "—"
            if item["expiration_date"]:
                try:
                    expiry_disp = date.fromisoformat(item["expiration_date"]).strftime("%d/%m/%Y")
                except Exception:
                    expiry_disp = item["expiration_date"]
            self.tree.insert("", "end", values=(
                item["product_id"], item["product_name"],
                item["batch"] or "—", expiry_disp, item["quantity"],
                f"{cy} {item['unit_cost']:,.2f}",
                f"{cy} {item['tax']:,.2f}",
                f"{cy} {item['discount']:,.2f}",
                f"{cy} {item['subtotal']:,.2f}",
                f"{cy} {item['total']:,.2f}",
            ))
        self.update_totals()
        self._on_tree_select()  # la tabla se reconstruyó: no queda nada seleccionado

    def _on_tree_select(self, event=None):
        """Muestra 'Editar Producto' solo mientras haya una fila seleccionada con clic."""
        if self.tree.selection():
            if not self.btn_edit.winfo_ismapped():
                self.btn_edit.pack(side="left", padx=(0, 8), before=self.btn_remove)
        else:
            self.btn_edit.pack_forget()

    # ═══════════════════════════════════════════
    # TOTALES GENERALES
    # ═══════════════════════════════════════════

    def update_totals(self):
        cy = self._currency()
        subtotal = sum(i["subtotal"] for i in self.items)
        tax      = sum(i["tax"]      for i in self.items)
        discount = sum(i["discount"] for i in self.items)
        total    = subtotal + tax - discount
        self.subtotal_lbl.configure(text=f"{cy} {subtotal:,.2f}")
        self.tax_lbl.configure(text=f"{cy} {tax:,.2f}")
        self.disc_lbl.configure(text=f"{cy} {discount:,.2f}" if discount else f"{cy} 0.00",
                                 text_color=DANGER if discount else SUBTEXT)
        self.total_lbl.configure(text=f"{cy} {total:,.2f}")
        return subtotal, tax, discount, total

    # ═══════════════════════════════════════════
    # GUARDAR COMPRA
    # ═══════════════════════════════════════════

    def save_purchase(self):
        if not self.items:
            error_message("Error", "Agrega al menos un producto a la compra."); return
        if not self._selected_supplier_id:
            error_message("Error", "Selecciona un proveedor válido de la lista de sugerencias."); return

        purchase_date_str = self.date_field.get().strip() or date.today().isoformat()
        try:
            date.fromisoformat(purchase_date_str)
        except ValueError:
            error_message("Fecha inválida", "La fecha de compra no es válida."); return

        due_date_str = self.due_date_field.get().strip()
        if self.payment_var.get() == "Crédito":
            if not due_date_str:
                error_message("Error",
                    "La fecha de vencimiento de pago es obligatoria para compras a crédito.")
                return
            try:
                date.fromisoformat(due_date_str)
            except ValueError:
                error_message("Fecha inválida", "La fecha de vencimiento de pago no es válida.")
                return
        else:
            due_date_str = None

        subtotal, tax, discount, total = self.update_totals()

        editing = self._editing_purchase_id is not None
        confirm_msg = (
            f"¿Guardar los cambios de la Compra #{self._editing_purchase_id} "
            f"(total {self._currency()} {total:,.2f})?\nSe ajustará el inventario "
            f"según los cambios en cantidades/costos."
            if editing else
            f"¿Registrar esta compra por {self._currency()} {total:,.2f}?\n"
            f"Se actualizará el inventario automáticamente."
        )
        if not messagebox.askyesno("Confirmar Compra", confirm_msg):
            return

        # Indicador de carga mientras se guarda.
        saving_label = "⏳  Guardando cambios..." if editing else "⏳  Guardando..."
        self.btn_save.configure(state="disabled", text=saving_label)
        self.parent.update_idletasks()

        header = {
            "supplier_id":    self._selected_supplier_id,
            "invoice_number": self.invoice_entry.get().strip(),
            "purchase_date":  f"{purchase_date_str} {datetime.now().strftime('%H:%M:%S')}",
            "payment_method": self.payment_var.get(),
            "due_date": due_date_str,
            "subtotal": subtotal, "tax": tax, "discount": discount, "total": total,
            "notes": self.notes_entry.get().strip(),
        }
        username = self._current_username()
        if editing:
            result = update_purchase(self._editing_purchase_id, header, self.items,
                                      username, self._current_user_id())
        else:
            result = register_purchase(header, self.items, username, self._current_user_id())

        self.btn_save.configure(state="normal",
                                 text="💾  Guardar Cambios" if editing else "✔  Guardar Compra")

        if not result.get("ok"):
            error_message("Error al guardar la compra",
                          result.get("error", "Error desconocido."))
            return

        purchase_id = result["purchase_id"]
        audit("COMPRA_EDITADA" if editing else "COMPRA_REGISTRADA",
              f"Compra #{purchase_id} | Proveedor: {self.supplier_search.get()} | "
              f"Factura: {header['invoice_number'] or '—'} | Total: {total:,.2f}",
              module="compras")

        success_message(
            "Compra Actualizada" if editing else "Compra Registrada",
            f"Compra #{purchase_id} {'actualizada' if editing else 'registrada'} correctamente.\n"
            f"Proveedor: {self.supplier_search.get()}\n"
            f"Total: {self._currency()} {total:,.2f}\n\n"
            f"El inventario fue actualizado automáticamente.")
        self.clear_form()
        self.search_invoices()

    def cancel_purchase(self):
        if self.items or self.invoice_entry.get().strip():
            if not messagebox.askyesno("Cancelar Compra",
                    "¿Descartar los datos de esta compra?"):
                return
        self.clear_form()

    def clear_form(self):
        self.items.clear()
        self._refresh_tree()
        self._clear_item_form()
        self.invoice_entry.delete(0, "end")
        self.date_field.set(date.today().isoformat())
        self.payment_var.set(PAYMENT_METHODS[0])
        self._on_payment_method_change()   # oculta y limpia la fecha de vencimiento de pago
        self.supplier_search.clear()
        self._selected_supplier_id = None
        self.notes_entry.delete(0, "end")

        self._editing_purchase_id = None
        self._editing_item_meta   = None
        self.edit_banner.pack_forget()
        self.btn_save.configure(text="✔  Guardar Compra")
