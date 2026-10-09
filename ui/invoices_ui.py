import os
import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime, date

import config
from database.connection import create_connection
from database.fefo import sync_product_cost as _sync_product_cost
from reports.pdf_generator import generate_invoice_pdf
from reports.receipt_generator import generate_receipt
from reports.invoice_generator import generate_invoice_txt
from ui.predictive_search import PredictiveSearch
from ui.live_search import LiveSearch
from auth import session
from utils.notifications import success_message, error_message, warning_message
from utils.logger import write_log, log_sale, audit


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
PURPLE       = "#C084FC"



def _deduct_lots_peps(cur, product_id: int, qty_needed: int,
                      invoice_id: int, username: str,
                      chosen_lot_id: int = None):
    """
    Descuenta qty_needed UNIDADES BASE usando PEPS.
    - Si chosen_lot_id está definido: descuenta de ese lote específico primero,
      luego del resto si no alcanza.
    - Si es None: usa FEFO automático (vence antes = primero).
    qty_needed ya viene convertido (ej: 2 cajas x 100 = 200 unidades base).
    """
    from datetime import datetime as _dt
    ts = _dt.now().strftime("%Y-%m-%d %H:%M:%S")

    # Si se eligió un lote específico, ponerlo primero
    if chosen_lot_id:
        cur.execute("""SELECT id, quantity_available FROM lots
                       WHERE product_id=%s AND status='activo' AND quantity_available>0
                         AND (expiry_date IS NULL OR expiry_date >= CURDATE())
                       ORDER BY
                           CASE WHEN id=%s THEN 0 ELSE 1 END,
                           CASE WHEN expiry_date IS NULL THEN 1 ELSE 0 END,
                           expiry_date ASC,
                           received_date ASC,
                           id ASC""", (product_id, chosen_lot_id))
    else:
        # PEPS automático: más antiguo Y más próximo a vencer primero
        cur.execute("""SELECT id, quantity_available FROM lots
                       WHERE product_id=%s AND status='activo' AND quantity_available>0
                         AND (expiry_date IS NULL OR expiry_date >= CURDATE())
                       ORDER BY
                           CASE WHEN expiry_date IS NULL THEN 1 ELSE 0 END,
                           expiry_date ASC,
                           received_date ASC,
                           id ASC""", (product_id,))
    lots      = cur.fetchall()
    remaining = qty_needed

    for lot_id, available in lots:
        if remaining <= 0: break
        take      = min(remaining, int(available))
        new_avail = int(available) - take
        cur.execute("UPDATE lots SET quantity_available=%s, status=%s WHERE id=%s",
                    (new_avail, "agotado" if new_avail == 0 else "activo", lot_id))
        cur.execute("""INSERT INTO lot_movements
            (lot_id, type, quantity, reason, invoice_id, username, timestamp)
            VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (lot_id, "salida", -take, "Venta", invoice_id, username, ts))
        remaining -= take

    # Sincronizar stock del producto
    cur.execute("""UPDATE products
                   SET stock = (SELECT COALESCE(SUM(quantity_available),0)
                                FROM lots WHERE product_id=%s AND status='activo')
                   WHERE id=%s""", (product_id, product_id))

    # Sincronizar costo promedio ponderado (la venta puede agotar el lote
    # más barato/caro y cambiar la mezcla de costos restante)
    _sync_product_cost(cur, product_id)


class InvoicesUI:

    def __init__(self, parent):
        self.parent = parent
        self.cart   = []
        self._cfg   = config.load()

        container = ctk.CTkFrame(parent, fg_color=BG, corner_radius=0)
        container.pack(fill="both", expand=True)

        # ══════════════════════════════════════
        # ENCABEZADO CON DATOS DE FACTURA
        # ══════════════════════════════════════
        header_card = ctk.CTkFrame(container, fg_color=CARD, corner_radius=12,
                                    border_width=1, border_color=CARD_BORDER)
        header_card.pack(fill="x", padx=20, pady=(16, 8))

        hrow = ctk.CTkFrame(header_card, fg_color="transparent")
        hrow.pack(fill="x", padx=16, pady=12)
        hrow.columnconfigure((0,1,2,3), weight=1)

        # Número de factura
        self._next_num = self._get_next_number()
        self._info_block(hrow, "🧾  N° Factura",
                         f"#{self._next_num:06d}", ACCENT, 0)

        # Fecha y hora
        self._now = datetime.now()
        self._info_block(hrow, "📅  Fecha",
                         self._now.strftime("%d/%m/%Y"), TEXT, 1)
        self._info_block(hrow, "🕐  Hora",
                         self._now.strftime("%I:%M %p"), TEXT, 2)

        # Cajero activo
        user = session.current_user
        cashier = user[1] if isinstance(user, tuple) else str(user)
        self._info_block(hrow, "👤  Cajero", cashier, CYAN, 3)

        # ── Guía de atajos ──
        shortcuts_bar = ctk.CTkFrame(container, fg_color="#0D1A24", corner_radius=8)
        shortcuts_bar.pack(fill="x", padx=20, pady=(0, 6))
        srow = ctk.CTkFrame(shortcuts_bar, fg_color="transparent")
        srow.pack(padx=14, pady=6)
        for key, desc in [("Ctrl+B","Buscar"),("Ctrl+N","Cantidad"),("Ctrl+M","Agregar"),
                           ("Ctrl+G","Generar"),("Ctrl+P","Imprimir"),("Ctrl+W","Vista previa"),
                           ("Ctrl+D","Limpiar"),("Ctrl+Q","Quitar"),("Esc","Limpiar búsqueda")]:
            kb = ctk.CTkFrame(srow, fg_color="#1A2E3A", corner_radius=4)
            kb.pack(side="left", padx=3)
            ctk.CTkLabel(kb, text=key, font=("Arial",9,"bold"),
                         text_color=CYAN).pack(padx=5, pady=2)
            ctk.CTkLabel(srow, text=desc, font=("Arial",9),
                         text_color=SUBTEXT).pack(side="left", padx=(0,8))

        # ══════════════════════════════════════
        # TARJETA: DATOS DE VENTA
        # ══════════════════════════════════════
        form_card = ctk.CTkFrame(container, fg_color=CARD, corner_radius=12,
                                  border_width=1, border_color=CARD_BORDER)
        form_card.pack(fill="x", padx=20, pady=(0, 8))

        self._card_header(form_card, "Datos de la Venta")

        # Fila 1: Cliente
        r1 = ctk.CTkFrame(form_card, fg_color="transparent")
        r1.pack(fill="x", padx=16, pady=(0, 8))
        r1.columnconfigure(0, weight=1)

        cw = ctk.CTkFrame(r1, fg_color="transparent")
        cw.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(cw, text="Cliente",
                     font=("Arial", 11), text_color=SUBTEXT).pack(anchor="w", padx=2)
        self.customer_entry = LiveSearch(
            cw,
            query_fn=self._suggest_customers,
            on_select=lambda v, i=None: None,
            placeholder="🔍  Nombre del cliente o consumidor final...",
            debounce_ms=180
        )
        self.customer_entry.pack(fill="x", pady=(3, 0))

        # Fila 2: Búsqueda de producto + Cantidad + Descuento por item
        r2 = ctk.CTkFrame(form_card, fg_color="transparent")
        r2.pack(fill="x", padx=16, pady=(0, 8))
        r2.columnconfigure(0, weight=4)
        r2.columnconfigure(1, weight=1)
        r2.columnconfigure(2, weight=1)
        r2.columnconfigure(3, weight=1)

        # Búsqueda predictiva
        search_wrap = ctk.CTkFrame(r2, fg_color="transparent")
        search_wrap.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        ctk.CTkLabel(search_wrap, text="Buscar Producto (nombre o ID)",
                     font=("Arial", 11), text_color=SUBTEXT).pack(anchor="w", padx=2)

        self.product_search = PredictiveSearch(
            search_wrap,
            on_select=self._on_product_selected,
            placeholder="🔍  Escribir nombre, principio activo o ID...",
            show_picker_btn=True
        )
        self.product_search.pack(fill="x", pady=(3, 0))
        self._selected_product = None

        self.quantity_entry  = self._lbl_entry(r2, "Cantidad  ↵ Enter para agregar", 1)
        self.item_disc_entry = self._lbl_entry(r2, "Desc. %", 2)

        # Presentacion
        uw = ctk.CTkFrame(r2, fg_color="transparent")
        uw.grid(row=0, column=2, padx=(0,8), sticky="ew")
        ctk.CTkLabel(uw, text="Presentacion", font=("Arial",11), text_color=SUBTEXT).pack(anchor="w", padx=2)
        self.unit_var = ctk.StringVar(value="Unidad (x1)")
        self._unit_options = {"Unidad (x1)": (1, None)}
        self.unit_menu = ctk.CTkOptionMenu(
            uw, variable=self.unit_var, values=["Unidad (x1)"],
            fg_color=INPUT_BG, button_color="#2A2D3A",
            button_hover_color="#3A3D52", dropdown_fg_color="#1A1D27",
            dropdown_hover_color="#1A2E22", text_color=TEXT,
            font=("Arial",12), height=38, dynamic_resizing=False)
        self.unit_menu.pack(fill="x", pady=(3,0))

        # Selector de lote + botón ℹ info
        lw = ctk.CTkFrame(r2, fg_color="transparent")
        lw.grid(row=0, column=3, padx=(0,8), sticky="ew")
        ctk.CTkLabel(lw, text="Lote",
                     font=("Arial",11), text_color=SUBTEXT).pack(anchor="w", padx=2)
        self.lot_var  = ctk.StringVar(value="Auto (PEPS)")
        self._lot_options = {"Auto (PEPS)": None}
        lot_row = ctk.CTkFrame(lw, fg_color="transparent")
        lot_row.pack(fill="x", pady=(3,0))
        self.lot_menu = ctk.CTkOptionMenu(
            lot_row, variable=self.lot_var, values=["Auto (PEPS)"],
            fg_color=INPUT_BG, button_color="#2A2D3A",
            button_hover_color="#3A3D52", dropdown_fg_color="#1A1D27",
            dropdown_hover_color="#1A2E22", text_color=TEXT,
            font=("Arial",11), height=38, dynamic_resizing=False,
            command=self._on_lot_selected)
        self.lot_menu.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(
            lot_row, text="ℹ", width=38, height=38,
            corner_radius=8, fg_color="#1A2E3A",
            hover_color="#1E6A9A", text_color=CYAN,
            font=("Arial",16,"bold"),
            command=self._show_lot_info
        ).pack(side="left", padx=(4,0))

        # Botones
        btn_row = ctk.CTkFrame(form_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 14))
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
        # TABLA DEL CARRITO
        # ══════════════════════════════════════
        table_card = ctk.CTkFrame(container, fg_color=CARD, corner_radius=12,
                                   border_width=1, border_color=CARD_BORDER)
        table_card.pack(fill="x", padx=20, pady=(0, 8))
        self._card_header(table_card, "Carrito de Compras")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("INV.Treeview", background="#1A1D27", foreground="#FFFFFF",
                         fieldbackground="#1A1D27", borderwidth=0,
                         font=("Arial", 11), rowheight=32)
        style.configure("INV.Treeview.Heading", background="#1E2130",
                         foreground="#8B8FA8", font=("Arial", 10, "bold"), borderwidth=0)
        style.map("INV.Treeview",
                  background=[("selected", "#1A2E22"), ("!selected", "#1A1D27")],
                  foreground=[("selected", "#3DD68C"), ("!selected", "#FFFFFF")])

        cols = ("Producto", "Cant.", "P. Unit.", "Desc.%", "ITBIS", "Total")
        self.tree = ttk.Treeview(table_card, columns=cols, show="headings",
                                  height=7, style="INV.Treeview")
        try:
            self.tree.configure(style=self.tree["style"])
            self.tree.tk.call("ttk::style", "configure", self.tree["style"], "-fieldbackground", "#1A1D27")
            self.tree.tk.call("ttk::style", "configure", self.tree["style"], "-background", "#1A1D27")
            self.tree.tk.call("ttk::style", "configure", self.tree["style"], "-foreground", "#FFFFFF")
        except Exception:
            pass
        widths = {"Producto": 260, "Cant.": 60, "P. Unit.": 100,
                  "Desc.%": 70, "ITBIS": 90, "Total": 100}
        anchors = {"Producto": "w", "Cant.": "center", "P. Unit.": "e",
                   "Desc.%": "center", "ITBIS": "e", "Total": "e"}
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=widths[col], anchor=anchors[col])
        self.tree.pack(fill="x", padx=14, pady=(0, 12))

        # ══════════════════════════════════════
        # TOTALES + ACCIONES
        # ══════════════════════════════════════
        bottom_card = ctk.CTkFrame(container, fg_color=CARD, corner_radius=12,
                                    border_width=1, border_color=CARD_BORDER)
        bottom_card.pack(fill="x", padx=20, pady=(0, 20))

        brow = ctk.CTkFrame(bottom_card, fg_color="transparent")
        brow.pack(fill="x", padx=20, pady=14)

        # Columna izquierda: botones de acción
        btn_col = ctk.CTkFrame(brow, fg_color="transparent")
        btn_col.pack(side="left")

        ctk.CTkButton(btn_col, text="✔  Generar Factura",
                      height=50, width=210, corner_radius=10,
                      fg_color=ACCENT, hover_color="#2EBF7A",
                      text_color="#0F1117", font=("Arial", 14, "bold"),
                      command=self.generate_invoice).pack(pady=(0, 8))

        ctk.CTkButton(btn_col, text="🖨  Imprimir Comprobante",
                      height=42, width=210, corner_radius=10,
                      fg_color="#2A1A3A", hover_color="#6B21A8",
                      text_color=PURPLE, font=("Arial", 13, "bold"),
                      command=self.print_receipt).pack(pady=(0, 8))

        ctk.CTkButton(btn_col, text="👁  Previsualizar PDF",
                      height=38, width=210, corner_radius=10,
                      fg_color="#1A2E3A", hover_color="#1E6A9A",
                      text_color=CYAN, font=("Arial", 12),
                      command=self.preview_pdf).pack(pady=(0, 8))

        ctk.CTkButton(btn_col, text="↺  Limpiar",
                      height=34, width=210, corner_radius=10,
                      fg_color=INPUT_BG, hover_color="#2E3148",
                      text_color=SUBTEXT, font=("Arial", 12),
                      command=self.clear_invoice).pack()

        # Columna derecha: desglose de totales
        totals = ctk.CTkFrame(brow, fg_color=INPUT_BG, corner_radius=12)
        totals.pack(side="right", padx=(20, 0), ipadx=16, ipady=10)

        cfg0 = config.load(); cy0 = cfg0["billing"].get("currency","RD$")
        tr0  = float(cfg0["billing"].get("tax_rate",0))
        self.subtotal_lbl  = self._total_row(totals, "Subtotal:",         f"{cy0} 0.00", TEXT,   0)
        self.itbis_lbl, self.itbis_key_lbl = self._total_row_with_key(
            totals, f"ITBIS ({tr0:.0f}%):", f"{cy0} 0.00", TEXT, 1)
        self._disc_lbl_row = self._total_row(totals, "Descuento global:", f"{cy0} 0.00", SUBTEXT,2)

        # Descuento global %
        disc_frame = ctk.CTkFrame(totals, fg_color="transparent")
        disc_frame.grid(row=3, column=0, columnspan=2, sticky="w", pady=(6, 6))
        ctk.CTkLabel(disc_frame, text="Desc. global %",
                     font=("Arial", 11), text_color=SUBTEXT).pack(side="left")
        gf = ctk.CTkFrame(disc_frame, fg_color=CARD, corner_radius=6,
                           border_width=1, border_color=CARD_BORDER)
        gf.pack(side="left", padx=(8, 6))
        self.global_disc_entry = ctk.CTkEntry(gf, width=65, height=28,
                                               border_width=0, fg_color="transparent",
                                               font=("Arial", 12), text_color=TEXT)
        self.global_disc_entry.pack(padx=6)
        self.global_disc_entry.bind("<KeyRelease>", lambda e: self.update_total())

        ctk.CTkFrame(totals, height=1, fg_color=CARD_BORDER).grid(
            row=4, column=0, columnspan=2, sticky="ew", pady=6)

        self.total_lbl = self._total_row(totals, "TOTAL:", "$0.00", ACCENT, 5, large=True)

        # ══ Atajos de teclado — al final cuando TODOS los widgets existen ══
        self._register_inv_shortcuts(parent)

    def _register_inv_shortcuts(self, parent):
        """Registra atajos de teclado en la ventana raíz."""
        root = parent.winfo_toplevel()

        # Usar lambda diferidas para no evaluar self.X hasta que se pulse la tecla
        # Enter en cantidad = agregar al carrito (una sola vez, evitar doble disparo)
        self._enter_lock = False
        def _enter_add(event):
            if self._enter_lock: return "break"
            self._enter_lock = True
            self.add_to_cart()
            self.parent.after(300, lambda: setattr(self, "_enter_lock", False))
            return "break"
        self.quantity_entry.bind("<Return>", _enter_add)
        self.quantity_entry.bind("<KP_Enter>", _enter_add)

        root.bind("<Control-b>", lambda e: [self.product_search.focus(), "break"][1])
        root.bind("<Control-n>", lambda e: [self.quantity_entry.focus(),  "break"][1])
        root.bind("<Control-m>", lambda e: [self.add_to_cart(),           "break"][1])
        root.bind("<Control-g>", lambda e: [self.generate_invoice(),      "break"][1])
        root.bind("<Control-p>", lambda e: [self.print_receipt(),         "break"][1])
        root.bind("<Control-w>", lambda e: [self.preview_pdf(),           "break"][1])
        root.bind("<Control-d>", lambda e: [self.clear_invoice(),         "break"][1])
        root.bind("<Control-q>", lambda e: [self.remove_product(),        "break"][1])
        root.bind("<Escape>",    lambda e: [self.product_search.clear(),  "break"][1])

    # ═══════════════════════════════════════════
    # HELPERS DE UI
    # ═══════════════════════════════════════════

    def _suggest_customers(self, text):
        """Sugiere clientes registrados al escribir en el campo cliente."""
        conn = create_connection()
        try:
            cur = conn.cursor()
            cur.execute("""SELECT name, IFNULL(phone,''), seq FROM customers
                           WHERE name LIKE ? ORDER BY seq ASC LIMIT 8""",
                        (f"%{text}%",))
            rows = cur.fetchall()
        finally:
            conn.close()
        return [(r[0], f"Tel: {r[1]}" if r[1] else "", r[2]) for r in rows]

    def _card_header(self, parent, text):
        ctk.CTkLabel(parent, text=text,
                     font=("Arial", 12, "bold"), text_color=SUBTEXT).pack(
            anchor="w", padx=16, pady=(12, 2))
        ctk.CTkFrame(parent, height=1, fg_color=CARD_BORDER).pack(
            fill="x", padx=16, pady=(0, 8))

    def _info_block(self, parent, label, value, color, col):
        f = ctk.CTkFrame(parent, fg_color=INPUT_BG, corner_radius=10)
        f.grid(row=0, column=col, padx=6, sticky="ew")
        ctk.CTkLabel(f, text=label, font=("Arial", 10),
                     text_color=SUBTEXT).pack(anchor="w", padx=12, pady=(8, 0))
        ctk.CTkLabel(f, text=value, font=("Arial", 15, "bold"),
                     text_color=color).pack(anchor="w", padx=12, pady=(0, 8))

    def _lbl_entry(self, parent, label, col):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=0, column=col, padx=(0, 10), sticky="ew")
        ctk.CTkLabel(f, text=label, font=("Arial", 11),
                     text_color=SUBTEXT).pack(anchor="w", padx=2)
        ef = ctk.CTkFrame(f, fg_color=INPUT_BG, corner_radius=8,
                           border_width=1, border_color=INPUT_BORDER)
        ef.pack(fill="x", pady=(3, 0))
        e = ctk.CTkEntry(ef, border_width=0, fg_color="transparent",
                          height=38, font=("Arial", 13), text_color=TEXT)
        e.pack(fill="x", padx=8)
        return e

    def _total_row(self, parent, label, value, color, row, large=False):
        font_lbl = ("Arial", 12) if not large else ("Arial", 13, "bold")
        font_val = ("Arial", 14, "bold") if not large else ("Arial", 24, "bold")
        ctk.CTkLabel(parent, text=label, font=font_lbl,
                     text_color=SUBTEXT).grid(row=row, column=0, sticky="w", pady=1)
        lbl = ctk.CTkLabel(parent, text=value, font=font_val, text_color=color)
        lbl.grid(row=row, column=1, sticky="e", padx=(24, 0), pady=1)
        return lbl

    def _total_row_with_key(self, parent, label, value, color, row):
        """Como _total_row pero retorna también el label de la clave para actualizarlo."""
        key_lbl = ctk.CTkLabel(parent, text=label, font=("Arial", 12),
                                text_color=SUBTEXT)
        key_lbl.grid(row=row, column=0, sticky="w", pady=1)
        val_lbl = ctk.CTkLabel(parent, text=value, font=("Arial", 14, "bold"),
                                text_color=color)
        val_lbl.grid(row=row, column=1, sticky="e", padx=(24, 0), pady=1)
        return val_lbl, key_lbl

    # ═══════════════════════════════════════════
    # NÚMERO CORRELATIVO
    # ═══════════════════════════════════════════

    def _get_next_number(self) -> int:
        conn = create_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT IFNULL(MAX(id), 0) + 1 FROM invoices")
            return cur.fetchone()[0]
        finally:
            conn.close()

    # ═══════════════════════════════════════════
    # BÚSQUEDA PREDICTIVA — CALLBACK
    # ═══════════════════════════════════════════

    def _on_product_selected(self, prod: dict):
        self._selected_product = {
            "id":    prod["id"],
            "name":  prod["name"],
            "price": float(prod["price"]),
            "stock": int(prod["stock"]),
            "manages_lots": bool(prod.get("manages_lots", True)),
            "applies_itbis": bool(prod.get("applies_itbis", True)),
            "expiry": prod.get("expiry"),
        }
        if hasattr(self, 'unit_var'):        self._load_product_units(prod["id"])
        if hasattr(self, 'lot_var'):         self._load_product_lots(prod["id"])
        self.quantity_entry.focus()

    def _sellable_stock(self, product_id: int) -> int:
        """Stock realmente disponible para vender: excluye lotes vencidos."""
        try:
            conn = create_connection(); cur = conn.cursor()
            cur.execute("""
                SELECT COALESCE(SUM(quantity_available), 0) FROM lots
                WHERE product_id = %s AND status = 'activo'
                  AND (expiry_date IS NULL OR expiry_date >= CURDATE())
            """, (product_id,))
            row = cur.fetchone(); conn.close()
            return int(row[0] or 0)
        except Exception:
            return 0

    def _load_product_lots(self, product_id: int):
        """Carga lotes disponibles ordenados por PEPS. Excluye lotes vencidos:
        un producto vencido no debe poder venderse."""
        try:
            conn = create_connection(); cur = conn.cursor()
            cur.execute("""
                SELECT id, lot_number, quantity_available, expiry_date, received_date
                FROM lots
                WHERE product_id = %s
                  AND status = 'activo'
                  AND quantity_available > 0
                  AND (expiry_date IS NULL OR expiry_date >= CURDATE())
                ORDER BY
                    CASE WHEN expiry_date IS NULL THEN 1 ELSE 0 END,
                    expiry_date   ASC,
                    received_date ASC,
                    id            ASC
            """, (product_id,))
            rows = cur.fetchall(); conn.close()
            self._lot_options = {"Auto (PEPS)": None}
            for lot_id, lot_num, qty_avail, exp_date, recv_date in rows:
                qty = int(qty_avail or 0)
                if exp_date:
                    exp_str = (exp_date.strftime("%d/%m/%Y")
                               if hasattr(exp_date, "strftime") else str(exp_date)[:10])
                    lbl = f"{lot_num}  |  {qty} uds  |  Vence: {exp_str}"
                else:
                    lbl = f"{lot_num}  |  {qty} uds"
                self._lot_options[lbl] = lot_id
            opts = list(self._lot_options.keys())
            self.lot_var.set(opts[0])
            self.lot_menu.configure(values=opts)
        except Exception:
            self._lot_options = {"Auto (PEPS)": None}
            self.lot_var.set("Auto (PEPS)")
            self.lot_menu.configure(values=["Auto (PEPS)"])

    def _on_lot_selected(self, choice: str):
        """Actualiza stock disponible al cambiar de lote."""
        lot_id = self._lot_options.get(choice)
        if lot_id and self._selected_product:
            try:
                conn = create_connection(); cur = conn.cursor()
                cur.execute("SELECT quantity_available FROM lots WHERE id=%s", (lot_id,))
                row = cur.fetchone(); conn.close()
                if row:
                    self._selected_product["_lot_stock"] = int(row[0] or 0)
            except Exception:
                pass
        elif self._selected_product:
            self._selected_product["_lot_stock"] = int(
                self._selected_product.get("stock", 0))

    def _show_lot_info(self):
        """Popup con información completa del lote seleccionado."""
        choice = self.lot_var.get()
        lot_id = self._lot_options.get(choice)

        if lot_id is None:
            messagebox.showinfo(
                "Modo Automático",
                "El sistema usará PEPS (Primero en Entrar, Primero en Salir)\n"
                "automáticamente: primero se descuenta el lote que vence más\n"
                "pronto y, si hay empate, el más antiguo.\n\n"
                "Elige un lote específico del menú para ver su información."
            )
            return

        try:
            conn = create_connection(); cur = conn.cursor()
            cur.execute("""
                SELECT l.id, l.lot_number, p.name,
                       l.quantity_received, l.quantity_available,
                       l.cost, l.expiry_date, l.received_date,
                       l.status, l.notes,
                       IFNULL(s.name,'Sin proveedor') AS supplier,
                       DATEDIFF(l.expiry_date, CURDATE()) AS days_left
                FROM lots l
                JOIN products p ON p.id = l.product_id
                LEFT JOIN suppliers s ON s.id = l.supplier_id
                WHERE l.id = %s
            """, (lot_id,))
            lot = cur.fetchone()
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        if not lot:
            messagebox.showwarning("", "No se encontro el lote.")
            return

        (lid, lot_num, prod_name, qty_recv, qty_avail,
         cost, expiry, recv_date, status, notes, supplier, days_left) = lot

        def fmt(d):
            if d is None: return "Sin fecha"
            return d.strftime("%d/%m/%Y") if hasattr(d,"strftime") else str(d)[:10]

        if expiry is None:
            venc_str   = "Sin fecha de vencimiento"
            venc_color = SUBTEXT
        elif days_left is not None and int(days_left) < 0:
            venc_str   = f"VENCIDO hace {abs(int(days_left))} dias"
            venc_color = DANGER
        elif days_left is not None and int(days_left) <= 30:
            venc_str   = f"Vence en {int(days_left)} dias  ({fmt(expiry)})"
            venc_color = WARNING
        else:
            venc_str   = f"{fmt(expiry)}  ({int(days_left) if days_left else '?'} dias)"
            venc_color = ACCENT

        cfg = config.load()
        cy  = cfg["billing"].get("currency","RD$")

        # ── Ventana popup ──────────────────────────────────────
        win = ctk.CTkToplevel(self.parent)
        win.title(f"Lote — {lot_num}")
        win.geometry("480x430")
        win.configure(fg_color=BG)
        win.resizable(False, False)
        win.grab_set()
        win.update_idletasks()
        sx = self.parent.winfo_rootx() + self.parent.winfo_width()  // 2 - 240
        sy = self.parent.winfo_rooty() + self.parent.winfo_height() // 2 - 215
        win.geometry(f"480x430+{sx}+{sy}")

        # Encabezado
        hdr = ctk.CTkFrame(win, fg_color=CARD, corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text=f"  {lot_num}",
                     font=("Arial",18,"bold"), text_color=CYAN
                     ).pack(anchor="w", padx=20, pady=(16,2))
        ctk.CTkLabel(hdr, text=f"Producto: {prod_name}  |  ID Lote: #{lid}",
                     font=("Arial",11), text_color=SUBTEXT
                     ).pack(anchor="w", padx=20, pady=(0,12))
        ctk.CTkFrame(win, height=1, fg_color=CARD_BORDER).pack(fill="x")

        # Cuerpo
        body = ctk.CTkFrame(win, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=14)
        body.columnconfigure(1, weight=1)

        def row(lbl, val, color=TEXT, r=0):
            ctk.CTkLabel(body, text=lbl, font=("Arial",11),
                         text_color=SUBTEXT, anchor="w"
                         ).grid(row=r, column=0, sticky="w", pady=4, padx=(0,16))
            ctk.CTkLabel(body, text=str(val), font=("Arial",12,"bold"),
                         text_color=color, anchor="w"
                         ).grid(row=r, column=1, sticky="w", pady=4)

        row("N de Lote:",         lot_num,                                       CYAN,    0)
        row("Cant. Recibida:",    f"{int(qty_recv  or 0)} unidades",             TEXT,    1)
        row("Disponible:",        f"{int(qty_avail or 0)} unidades",
            ACCENT if int(qty_avail or 0) > 0 else DANGER,                                2)
        row("Costo Unitario:",    f"{cy} {float(cost or 0):,.2f}",              TEXT,    3)
        row("Vencimiento:",       venc_str,                                       venc_color, 4)
        row("Fecha Recepcion:",   fmt(recv_date),                                TEXT,    5)
        row("Proveedor:",         supplier,                                       TEXT,    6)
        row("Estado:",            (status or "").upper(),
            ACCENT if status == "activo" else DANGER,                                      7)

        if notes:
            ctk.CTkFrame(body, height=1, fg_color=CARD_BORDER
                         ).grid(row=8, column=0, columnspan=2,
                                sticky="ew", pady=(6,2))
            ctk.CTkLabel(body, text="Notas:", font=("Arial",11),
                         text_color=SUBTEXT, anchor="w"
                         ).grid(row=9, column=0, sticky="nw", pady=4, padx=(0,16))
            ctk.CTkLabel(body, text=notes, font=("Arial",11),
                         text_color=TEXT, anchor="w",
                         wraplength=280, justify="left"
                         ).grid(row=9, column=1, sticky="w", pady=4)

        ctk.CTkFrame(win, height=1, fg_color=CARD_BORDER).pack(fill="x")
        ctk.CTkButton(win, text="Cerrar", height=38, corner_radius=8,
                      fg_color=INPUT_BG, hover_color="#2E3148",
                      text_color=TEXT, font=("Arial",12),
                      command=win.destroy
                      ).pack(padx=20, pady=12, anchor="e")

    def _load_product_units(self, pid):
        try:
            conn=create_connection(); cur=conn.cursor()
            cur.execute("SELECT unit_name,factor,price FROM product_units WHERE product_id=? ORDER BY factor",(pid,))
            rows=cur.fetchall(); conn.close()
            self._unit_options={}
            for uname,factor,uprice in rows or []:
                lbl=f"{uname} (x{int(factor)})"
                self._unit_options[lbl]=(int(factor),float(uprice) if uprice else None)
            if not self._unit_options: self._unit_options={"Unidad (x1)":(1,None)}
            opts=list(self._unit_options.keys())
            self.unit_var.set(opts[0]); self.unit_menu.configure(values=opts)
        except Exception:
            self._unit_options={"Unidad (x1)":(1,None)}
            self.unit_var.set("Unidad (x1)"); self.unit_menu.configure(values=["Unidad (x1)"])

    # ═══════════════════════════════════════════
    # AGREGAR AL CARRITO
    # ═══════════════════════════════════════════

    def add_to_cart(self):
        # Intentar resolver desde el widget predictivo si no hay selección
        if not self._selected_product:
            selected = self.product_search.get_selected()
            if selected:
                self._selected_product = {
                    "id": selected["id"], "name": selected["name"],
                    "price": selected["price"], "stock": selected["stock"],
                    "manages_lots": bool(selected.get("manages_lots", True)),
                    "applies_itbis": bool(selected.get("applies_itbis", True)),
                    "expiry": selected.get("expiry"),
                }
        if not self._selected_product:
            error_message("Error", "Seleccione un producto de la lista predictiva."); return

        qty_str = self.quantity_entry.get().strip()
        if not qty_str:
            error_message("Error", "Ingrese la cantidad."); return
        try:
            quantity = int(qty_str)
            if quantity <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Cantidad debe ser número entero positivo."); return

        try:
            item_disc = float(self.item_disc_entry.get().strip() or 0)
            if not (0 <= item_disc <= 100): raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Descuento debe ser entre 0 y 100."); return

        p          = self._selected_product

        # ── Bloquear venta de producto vencido ────────────────────────
        if p.get("manages_lots", True):
            if self._sellable_stock(p["id"]) <= 0:
                error_message("Producto vencido",
                    f"'{p['name']}' no tiene lotes vigentes: todo el stock "
                    "disponible está vencido. No se puede vender.")
                return
        else:
            exp = p.get("expiry")
            if exp:
                exp_d = exp if isinstance(exp, date) else None
                if exp_d is None:
                    try:
                        exp_d = date.fromisoformat(str(exp)[:10])
                    except Exception:
                        exp_d = None
                if exp_d and exp_d < date.today():
                    error_message("Producto vencido",
                        f"'{p['name']}' está vencido (venció el "
                        f"{exp_d.strftime('%d/%m/%Y')}). No se puede vender.")
                    return

        # ── Presentación seleccionada (factor y precio) ──────────────
        unit_label          = self.unit_var.get() if hasattr(self, "unit_var") else "Unidad (x1)"
        factor, unit_price  = self._unit_options.get(unit_label, (1, None))
        if unit_price is None:
            # Precio "Auto" = precio base del producto × factor de la presentación
            unit_price = float(p["price"]) * factor

        base_qty = quantity * factor  # unidades base reales a descontar del stock

        # Verificar stock según lote elegido o stock total
        chosen_lot_id = self._lot_options.get(self.lot_var.get()) if hasattr(self,"lot_var") else None
        lot_stock = self._selected_product.get("_lot_stock", int(p["stock"]))
        stock_disp = lot_stock if chosen_lot_id else int(p["stock"])

        if base_qty > stock_disp:
            lot_info = f"lote {self.lot_var.get().split('|')[0].strip()}" if chosen_lot_id else "stock total"
            messagebox.showerror("Error",
                f"Stock insuficiente en {lot_info}.\n"
                f"Disponible: {stock_disp} uds, necesitas: {base_qty} uds.")
            return

        cfg        = config.load()
        tax_rate   = float(cfg["billing"].get("tax_rate", 0))
        currency   = cfg["billing"].get("currency", "$")

        # MariaDB retorna DECIMAL como decimal.Decimal — convertir a float
        price_disc = float(unit_price) * (1 - item_disc / 100)
        subtotal   = round(quantity * price_disc, 2)
        apply_itbis = bool(p.get("applies_itbis", True))
        itbis_amt  = round(subtotal * tax_rate / 100, 2) if apply_itbis else 0.0
        total_item = round(subtotal + itbis_amt, 2)

        # Identificar lote seleccionado
        chosen_lot_id   = self._lot_options.get(self.lot_var.get()) if hasattr(self,"lot_var") else None
        lot_display     = self.lot_var.get().split("|")[0].strip() if chosen_lot_id else "Auto"

        self.cart.append({
            "product_id":  str(p["id"]),
            "pid_int":     p["id"],
            "name":        p["name"],
            "quantity":    quantity,
            "price":       price_disc,
            "price_orig":  unit_price,
            "unit_label":  unit_label,
            "factor":      factor,
            "base_qty":    base_qty,
            "chosen_lot_id": chosen_lot_id,
            "lot_display": lot_display,
            "discount":    item_disc,
            "itbis":       itbis_amt,
            "tax_rate":    tax_rate,
            "total":       total_item,
            "subtotal":    subtotal,
            "manages_lots": p.get("manages_lots", True),
            "applies_itbis": apply_itbis,
        })

        disc_str  = f"{item_disc:.0f}%" if item_disc > 0 else "—"
        itbis_str = f"{currency} {itbis_amt:,.2f}" if (tax_rate > 0 and apply_itbis) else f"{currency} 0.00"
        iid = self.tree.insert("", "end", values=(
            f"{p['name']} — {unit_label}", quantity,
            f"{currency} {unit_price:,.2f}",
            disc_str,
            itbis_str,
            f"{currency} {total_item:,.2f}"
        ))
        self.update_total()
        self._flash_row(iid)
        self._show_toast(f"✔  {p['name']} x{quantity} agregado")
        # Limpiar cantidad y volver al buscador para el siguiente producto
        self.quantity_entry.delete(0, "end")
        self.quantity_entry.insert(0, "1")
        self.product_search.focus()

        self._selected_product = None
        self.product_search.clear()
        self.quantity_entry.delete(0, "end")
        self.item_disc_entry.delete(0, "end")

    # ═══════════════════════════════════════════
    # TOTALES
    # ═══════════════════════════════════════════

    def update_total(self):
        cfg      = config.load()
        tax_rate = float(cfg["billing"].get("tax_rate", 0))
        currency = cfg["billing"].get("currency", "$")

        subtotal  = sum(i["subtotal"] for i in self.cart)
        itbis_tot = sum(i["itbis"]    for i in self.cart)

        try:
            g_disc = float(self.global_disc_entry.get().strip() or 0)
            g_disc = max(0, min(100, g_disc))
        except ValueError:
            g_disc = 0.0

        disc_amt = (subtotal + itbis_tot) * g_disc / 100
        total    = subtotal + itbis_tot - disc_amt

        self.subtotal_lbl.configure(text=f"{currency} {subtotal:,.2f}")
        tax_label = f"ITBIS ({tax_rate:.0f}%):"
        self.itbis_key_lbl.configure(text=tax_label)
        self.itbis_lbl.configure(text=f"{currency} {itbis_tot:,.2f}")
        if disc_amt > 0:
            self._disc_lbl_row.configure(text=f"- {currency} {disc_amt:,.2f}",
                                          text_color=DANGER)
        else:
            self._disc_lbl_row.configure(text=f"{currency} 0.00",
                                          text_color=SUBTEXT)
        self.total_lbl.configure(text=f"{currency} {total:,.2f}")

    def _get_final_total(self):
        subtotal  = sum(i["subtotal"] for i in self.cart)
        itbis_tot = sum(i["itbis"]    for i in self.cart)
        try:
            g_disc = float(self.global_disc_entry.get().strip() or 0)
            g_disc = max(0, min(100, g_disc))
        except ValueError:
            g_disc = 0.0
        return round((subtotal + itbis_tot) * (1 - g_disc / 100), 2)

    # ═══════════════════════════════════════════
    # ELIMINAR DEL CARRITO
    # ═══════════════════════════════════════════

    def remove_product(self):
        selected = self.tree.selection()
        if not selected:
            warning_message("Advertencia", "Seleccione un producto."); return
        item = selected[0]
        name = self.tree.item(item, "values")[0]
        for p in self.cart:
            if p["name"] == name:
                self.cart.remove(p); break
        self.tree.delete(item)
        self.update_total()

    # ═══════════════════════════════════════════
    # PREVISUALIZAR PDF
    # ═══════════════════════════════════════════

    def print_receipt(self):
        """Genera e imprime el comprobante de venta en formato térmico."""
        if not self.cart:
            messagebox.showerror("Error", "El carrito está vacío."); return

        customer = self.customer_entry.get().strip() or "Consumidor Final"
        total    = self._get_final_total()
        payment  = "Efectivo"
        user     = session.current_user
        cashier  = user[1] if isinstance(user, tuple) else str(user)

        try:
            g_disc = float(self.global_disc_entry.get().strip() or 0)
            g_disc = max(0, min(100, g_disc))
        except ValueError:
            g_disc = 0.0

        filename = f"Comprobante_{self._next_num:06d}.pdf"

        try:
            path = generate_receipt(
                invoice_id     = self._next_num,
                customer       = customer,
                cart           = self.cart,
                total          = total,
                payment_method = payment,
                cashier        = cashier,
                invoice_date   = self._now,
                discount_pct   = g_disc,
                filename       = filename,
            )
            # Abrir con visor/impresora del sistema
            try:
                os.startfile(path)
            except AttributeError:
                import subprocess
                subprocess.run(["xdg-open", path], check=False)

            messagebox.showinfo("Comprobante listo",
                                f"Comprobante generado:\n{path}\n\n"
                                "Se abrirá el visor para imprimir.")
        except Exception as e:
            messagebox.showerror("Error al generar comprobante", str(e))

    def preview_pdf(self):
        if not self.cart:
            messagebox.showerror("Error", "El carrito está vacío."); return
        customer = self.customer_entry.get().strip() or "Previsualización"
        total    = self._get_final_total()
        temp     = f"preview_{datetime.now().strftime('%H%M%S')}.pdf"
        try:
            generate_invoice_pdf("PREVIEW", customer, self.cart, total, filename=temp)
        except TypeError:
            generate_invoice_pdf("PREVIEW", customer, self.cart, total)
            temp = "Factura_PREVIEW.pdf"
        try:
            os.startfile(temp)
        except Exception:
            import subprocess
            subprocess.run(["xdg-open", temp], check=False)

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
        payment  = "Efectivo"  # método fijo

        conn = create_connection(); cursor = conn.cursor()

        try:
            # Transacción atómica: todo o nada
            cursor.execute(
                """INSERT INTO invoices
                   (customer_name, total, purchase_date, employee, payment_method)
                   VALUES (?,?,?,?,?)""",
                (customer, float(total), self._now.strftime("%Y-%m-%d %H:%M:%S"),
                 username, payment)
            )
            invoice_id = cursor.lastrowid

            for item in self.cart:
                cursor.execute(
                    """INSERT INTO invoice_items
                       (invoice_id, product_id, product_name, quantity, price, total)
                       VALUES (?,?,?,?,?,?)""",
                    (invoice_id, item.get("pid_int"), item["name"],
                     item["quantity"], item["price"], item["total"])
                )
                base_qty = item.get("base_qty", item["quantity"])
                if item.get("manages_lots", True):
                    # El stock real vive en los lotes, no en products.stock
                    # (que es solo una copia informativa) — validar contra eso.
                    cursor.execute("""SELECT COALESCE(SUM(quantity_available),0) FROM lots
                                       WHERE product_id=? AND status='activo'""",
                                   (item["product_id"],))
                    row = cursor.fetchone()
                    stock_disp = int(row[0]) if row else 0
                    if stock_disp < base_qty:
                        raise ValueError(
                            f"Stock insuficiente para '{item["name"]}'. "
                            f"Necesitas {base_qty} uds, disponible: {stock_disp}")
                    _deduct_lots_peps(cursor, int(item["product_id"]), base_qty,
                                      invoice_id, username,
                                      chosen_lot_id=item.get("chosen_lot_id"))
                else:
                    # Producto sin lotes: el stock vive directo en
                    # products.stock, se descuenta ahí sin tocar lots.
                    cursor.execute("SELECT stock FROM products WHERE id=?",
                                   (item["product_id"],))
                    row = cursor.fetchone()
                    stock_disp = int(row[0]) if row else 0
                    if stock_disp < base_qty:
                        raise ValueError(
                            f"Stock insuficiente para '{item["name"]}'. "
                            f"Necesitas {base_qty} uds, disponible: {stock_disp}")
                    cursor.execute("UPDATE products SET stock = stock - ? WHERE id=?",
                                   (base_qty, item["product_id"]))

            conn.commit()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error de transacción",
                                 f"La factura no fue guardada:\n{e}")
            conn.close()
            return
        conn.close()

        try:
            g_disc = float(self.global_disc_entry.get().strip() or 0)
            g_disc = max(0, min(100, g_disc))
        except ValueError:
            g_disc = 0.0

        pdf_file = generate_invoice_pdf(invoice_id, customer, self.cart, total)
        txt_file = generate_invoice_txt(invoice_id, customer, self.cart, total,
                                         cashier=username, invoice_date=self._now,
                                         discount_pct=g_disc)
        success_message("Factura Generada",
                        f"Factura #{invoice_id:06d} registrada.\n"
                        f"Cliente: {customer}\n"
                        f"Pago: {payment}\n"
                        f"Total: {self._get_currency()} {total:,.2f}")
        log_sale(invoice_id, customer, total, payment, self.cart)

        # Se abre el .txt (no el PDF): en Windows, el PDF suele abrirse con
        # Word si no hay un lector de PDF configurado como predeterminado.
        try:
            os.startfile(txt_file)
        except Exception:
            pass

        self.clear_invoice()

    def _get_currency(self):
        return config.load()["billing"].get("currency", "$")

    # ═══════════════════════════════════════════
    # TOAST / FLASH
    # ═══════════════════════════════════════════

    def _flash_row(self, iid):
        self.tree.selection_set(iid)
        self.tree.see(iid)
        self.parent.after(800, lambda: self.tree.selection_remove(iid))

    def _show_toast(self, msg):
        if hasattr(self, "_toast") and self._toast.winfo_exists():
            self._toast.destroy()
        self._toast = ctk.CTkLabel(self.parent, text=msg,
                                    font=("Arial", 12, "bold"),
                                    text_color="#0F1117", fg_color=ACCENT,
                                    corner_radius=10, padx=14, pady=6)
        self._toast.place(relx=0.5, rely=0.95, anchor="center")
        self.parent.after(2200, self._hide_toast)

    def _hide_toast(self):
        if hasattr(self, "_toast") and self._toast.winfo_exists():
            self._toast.destroy()

    # ═══════════════════════════════════════════
    # LIMPIAR
    # ═══════════════════════════════════════════

    def clear_invoice(self):
        self.customer_entry.clear()
        self.product_search.clear()
        self.unit_var.set("Unidad (x1)")
        self._unit_options = {"Unidad (x1)": (1, None)}
        self.unit_menu.configure(values=["Unidad (x1)"])
        self.lot_var.set("Automatico (PEPS)")
        self._lot_options = {"Automatico (PEPS)": None}
        self.lot_menu.configure(values=["Automatico (PEPS)"])
        self.quantity_entry.delete(0, "end")
        self.item_disc_entry.delete(0, "end")
        self.global_disc_entry.delete(0, "end")
        self._selected_product = None
        self.cart.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.update_total()
        # Actualizar número correlativo
        self._next_num = self._get_next_number()

