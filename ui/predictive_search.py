"""
predictive_search.py
Widget de búsqueda predictiva para productos farmacéuticos.
Reutilizable en Facturación e Inventario.

Uso:
    widget = PredictiveSearch(parent, on_select=callback, placeholder="Buscar...")
    widget.pack(fill="x")

    # callback recibe: {"id", "name", "price", "stock", "category"}
"""
import customtkinter as ctk
from tkinter import ttk
from database.connection import create_connection
import config


BG          = "#0F1117"
CARD        = "#1A1D27"
CARD_BORDER = "#252836"
ACCENT      = "#3DD68C"
CYAN        = "#22D3EE"
TEXT        = "#FFFFFF"
SUBTEXT     = "#8B8FA8"
WARNING     = "#FFA94D"
DANGER      = "#EF4444"
INPUT_BG    = "#23263A"
INPUT_BORDER= "#2E3148"
HOVER       = "#1A2E22"
SELECT_BG   = "#162B1F"


class PredictiveSearch(ctk.CTkFrame):
    """
    Campo de búsqueda con autocompletado predictivo en tiempo real.
    Busca por nombre comercial, principio activo (parte del nombre)
    o ID del producto.
    """

    DEBOUNCE_MS = 180    # ms de espera tras última tecla
    MIN_CHARS   = 1      # caracteres mínimos para activar búsqueda
    MAX_RESULTS = 8      # máximo de resultados visibles

    def __init__(self, parent, on_select=None, placeholder="🔍  Buscar medicamento...",
                 show_picker_btn=True, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self._on_select    = on_select
        self._results      = []       # lista de dicts de productos
        self._active_idx   = -1       # índice resaltado por teclado
        self._debounce_job = None
        self._popup        = None
        self._result_btns  = []

        # ── Barra de búsqueda ──
        bar = ctk.CTkFrame(self, fg_color=INPUT_BG, corner_radius=10,
                            border_width=1, border_color=INPUT_BORDER)
        bar.pack(fill="x")

        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="x", padx=8, pady=4)

        ctk.CTkLabel(inner, text="🔍", font=("Arial", 14),
                     text_color=SUBTEXT, width=24).pack(side="left")

        self._entry = ctk.CTkEntry(inner, placeholder_text=placeholder,
                                    border_width=0, fg_color="transparent",
                                    height=36, font=("Arial", 13),
                                    text_color=TEXT,
                                    placeholder_text_color="#555870")
        self._entry.pack(side="left", fill="x", expand=True, padx=(4, 0))

        # Botón limpiar
        self._clear_btn = ctk.CTkButton(inner, text="✕", width=28, height=28,
                                         corner_radius=6, fg_color="transparent",
                                         hover_color="#2E1A1A", text_color=SUBTEXT,
                                         font=("Arial", 12), command=self.clear)
        self._clear_btn.pack(side="right")
        self._clear_btn.pack_forget()   # oculto hasta que haya texto

        if show_picker_btn:
            ctk.CTkButton(inner, text="⊞", width=30, height=30,
                          corner_radius=6, fg_color="#1A2E22",
                          hover_color="#2EBF7A", text_color=ACCENT,
                          font=("Arial", 14), command=self._open_full_picker
                          ).pack(side="right", padx=(4, 0))

        # ── Popup container (se posiciona dinámicamente) ──
        self._popup_container = ctk.CTkFrame(self, fg_color=CARD, corner_radius=10,
                                              border_width=1, border_color=CARD_BORDER)

        # Bindings
        self._entry.bind("<KeyRelease>", self._on_key)
        self._entry.bind("<Down>",       self._move_down)
        self._entry.bind("<Up>",         self._move_up)
        self._entry.bind("<Return>",     self._confirm_selection)
        self._entry.bind("<Escape>",     lambda e: self._hide_popup())
        self._entry.bind("<FocusOut>",   self._on_focus_out)

    # ═══════════════════════════════════════════
    # INTERFAZ PÚBLICA
    # ═══════════════════════════════════════════

    def get(self) -> str:
        return self._entry.get()

    def set(self, text: str):
        self._entry.delete(0, "end")
        self._entry.insert(0, text)
        self._toggle_clear()

    def clear(self):
        self._entry.delete(0, "end")
        self._hide_popup()
        self._toggle_clear()

    def focus(self):
        self._entry.focus()

    def get_selected(self) -> dict | None:
        return getattr(self, "_selected", None)

    # ═══════════════════════════════════════════
    # DEBOUNCE Y BÚSQUEDA
    # ═══════════════════════════════════════════

    def _on_key(self, event=None):
        # Ver nota equivalente en live_search.py: <KeyRelease> también se
        # dispara para ↑ ↓ Enter Esc, y sin este filtro relanzaba una
        # búsqueda que reiniciaba la selección al primer resultado.
        if event is not None and event.keysym in ("Up", "Down", "Return", "Escape"):
            return
        self._toggle_clear()
        # Cancelar job anterior
        if self._debounce_job:
            self.after_cancel(self._debounce_job)
        q = self._entry.get().strip()
        if len(q) < self.MIN_CHARS:
            self._hide_popup(); return
        # Esperar DEBOUNCE_MS antes de buscar
        self._debounce_job = self.after(self.DEBOUNCE_MS, lambda: self._search(q))

    def _search(self, q: str):
        if not q: self._hide_popup(); return

        conn = create_connection(); cur = conn.cursor()
        # Busca por nombre (nombre comercial / principio activo) o ID.
        # El stock se calcula según el modo del producto: en vivo desde
        # los lotes si maneja lotes, o el valor manual si no; la fecha de
        # vencimiento siempre es propia del producto.
        cur.execute("""
            SELECT p.id, p.name, p.price,
                   COALESCE(CASE WHEN p.manages_lots=1 THEN
                       (SELECT SUM(l.quantity_available) FROM lots l
                        WHERE l.product_id=p.id AND l.status='activo')
                   ELSE p.stock END, 0) AS stock,
                   p.category, p.expiry_date, s.name as supplier,
                   p.manages_lots, p.applies_itbis
            FROM products p
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            WHERE p.active = 1
              AND (p.name    LIKE ?
                OR p.category LIKE ?
                OR CAST(p.id AS CHAR) = ?)
            ORDER BY
                CASE WHEN p.name LIKE ? THEN 0 ELSE 1 END,
                stock DESC,
                p.name
            LIMIT ?
        """, (f"%{q}%", f"%{q}%", q, f"{q}%", self.MAX_RESULTS))
        rows = cur.fetchall()
        conn.close()

        self._results = [{
            "id":       r[0], "name":     r[1], "price":    r[2],
            "stock":    r[3], "category": r[4] or "General",
            "expiry":   r[5], "supplier": r[6], "manages_lots": bool(r[7]),
            "applies_itbis": bool(r[8]),
        } for r in rows]

        if self._results:
            self._show_popup()
        else:
            self._hide_popup()
            self._show_no_results()

    # ═══════════════════════════════════════════
    # POPUP DE RESULTADOS
    # ═══════════════════════════════════════════

    def _show_popup(self):
        cfg      = config.load()
        currency = cfg["billing"].get("currency", "$")
        threshold= cfg["inventory"].get("low_stock_threshold", 10)

        # Limpiar popup anterior
        for w in self._popup_container.winfo_children():
            w.destroy()
        self._result_btns.clear()
        self._active_idx = -1

        for idx, prod in enumerate(self._results):
            btn_frame = ctk.CTkFrame(self._popup_container,
                                      fg_color="transparent", corner_radius=8)
            btn_frame.pack(fill="x", padx=6, pady=2)

            # Determinar color de stock
            stock = prod["stock"]
            if stock == 0:
                stock_color, stock_icon = DANGER,  "⛔"
            elif stock <= threshold:
                stock_color, stock_icon = WARNING, "⚠"
            else:
                stock_color, stock_icon = ACCENT,  "✔"

            # Layout de cada resultado
            row = ctk.CTkFrame(btn_frame, fg_color="transparent")
            row.pack(fill="x", padx=4, pady=4)

            # Columna izquierda: nombre + categoría
            left = ctk.CTkFrame(row, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(left, text=prod["name"],
                         font=("Arial", 12, "bold"), text_color=TEXT,
                         anchor="w").pack(fill="x")
            ctk.CTkLabel(left, text=f"🏷 {prod['category']}",
                         font=("Arial", 10), text_color=SUBTEXT,
                         anchor="w").pack(fill="x")

            # Columna derecha: precio + stock
            right = ctk.CTkFrame(row, fg_color="transparent")
            right.pack(side="right", padx=(8, 0))

            ctk.CTkLabel(right, text=f"{currency} {prod['price']:,.2f}",
                         font=("Arial", 12, "bold"), text_color=CYAN,
                         anchor="e").pack(anchor="e")
            ctk.CTkLabel(right,
                         text=f"{stock_icon} {stock} uds",
                         font=("Arial", 10), text_color=stock_color,
                         anchor="e").pack(anchor="e")

            # Overlay clickeable
            overlay = ctk.CTkButton(
                btn_frame, text="", fg_color="transparent",
                hover_color=HOVER, height=1,
                command=lambda p=prod: self._select(p)
            )
            overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
            overlay.lower()
            self._result_btns.append((btn_frame, overlay))

        # Separador de cuenta
        count_frame = ctk.CTkFrame(self._popup_container,
                                    fg_color=INPUT_BG, corner_radius=0)
        count_frame.pack(fill="x")
        n = len(self._results)
        ctk.CTkLabel(count_frame,
                     text=f"{n} resultado{'s' if n != 1 else ''} — ↑↓ navegar · Enter seleccionar · Esc cerrar",
                     font=("Arial", 9), text_color=SUBTEXT).pack(pady=4)

        self._popup_container.pack(fill="x", pady=(4, 0))
        self._highlight(0)

    def _show_no_results(self):
        for w in self._popup_container.winfo_children():
            w.destroy()
        ctk.CTkLabel(self._popup_container,
                     text="😕  Sin resultados",
                     font=("Arial", 12), text_color=SUBTEXT).pack(pady=12)
        self._popup_container.pack(fill="x", pady=(4, 0))
        self.after(1500, self._hide_popup)

    def _hide_popup(self):
        self._popup_container.pack_forget()
        self._results = []
        self._active_idx = -1

    def _on_focus_out(self, event):
        # Pequeño delay para permitir clic en resultado
        self.after(200, self._hide_popup)

    # ═══════════════════════════════════════════
    # NAVEGACIÓN POR TECLADO
    # ═══════════════════════════════════════════

    def _move_down(self, event=None):
        if not self._results: return "break"
        idx = min(self._active_idx + 1, len(self._results) - 1)
        self._highlight(idx)
        return "break"

    def _move_up(self, event=None):
        if not self._results: return "break"
        idx = max(self._active_idx - 1, 0)
        self._highlight(idx)
        return "break"

    def _highlight(self, idx: int):
        # Quitar resaltado anterior
        for i, (frame, _) in enumerate(self._result_btns):
            frame.configure(fg_color=SELECT_BG if i == idx else "transparent")
        self._active_idx = idx

    def _confirm_selection(self, event=None):
        if self._results and 0 <= self._active_idx < len(self._results):
            self._select(self._results[self._active_idx])
        return "break"

    def _select(self, prod: dict):
        self._selected = prod
        self.set(prod["name"])
        self._hide_popup()
        if self._on_select:
            self._on_select(prod)

    # ═══════════════════════════════════════════
    # PICKER COMPLETO (modal)
    # ═══════════════════════════════════════════

    def _open_full_picker(self):
        root = self.winfo_toplevel()
        win  = ctk.CTkToplevel(root)
        win.title("Buscar Producto")
        win.geometry("700x500")
        win.configure(fg_color=BG)
        win.grab_set()

        ctk.CTkLabel(win, text="🔍  Seleccionar Producto",
                     font=("Arial", 16, "bold"), text_color=TEXT
                     ).pack(padx=20, pady=(20, 8), anchor="w")

        # Mini buscador en el picker
        sf = ctk.CTkFrame(win, fg_color=INPUT_BG, corner_radius=8,
                           border_width=1, border_color=INPUT_BORDER)
        sf.pack(fill="x", padx=20, pady=(0, 10))
        search_e = ctk.CTkEntry(sf, placeholder_text="Escribir nombre o ID...",
                                 border_width=0, fg_color="transparent",
                                 height=42, font=("Arial", 13), text_color=TEXT,
                                 placeholder_text_color="#555870")
        search_e.pack(fill="x", padx=10)

        card = ctk.CTkFrame(win, fg_color=CARD, corner_radius=12,
                             border_width=1, border_color=CARD_BORDER)
        card.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("FPS.Treeview", background=CARD, foreground=TEXT,
                         fieldbackground=CARD, borderwidth=0,
                         font=("Arial", 11), rowheight=30)
        style.configure("FPS.Treeview.Heading", background="#1E2130",
                         foreground=SUBTEXT, font=("Arial", 10, "bold"), borderwidth=0)
        style.map("FPS.Treeview",
                  background=[("selected","#1A2E22")],
                  foreground=[("selected", ACCENT)])

        cfg      = config.load()
        currency = cfg["billing"].get("currency", "$")
        threshold= cfg["inventory"].get("low_stock_threshold", 10)

        cols = ("ID", "Nombre", "Categoría", "Precio", "Stock")
        tree = ttk.Treeview(card, columns=cols, show="headings", style="FPS.Treeview")
        for col, w, anc in [
            ("ID",        55,  "center"),
            ("Nombre",   250,  "w"),
            ("Categoría",120,  "w"),
            ("Precio",   100,  "e"),
            ("Stock",     70,  "center"),
        ]:
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor=anc)

        tree.tag_configure("sin_stock",  foreground=DANGER)
        tree.tag_configure("bajo_stock", foreground=WARNING)
        tree.tag_configure("ok_stock",   foreground=ACCENT)

        tree.pack(fill="both", expand=True, padx=12, pady=12)

        extra_map = {}  # {product_id: {"manages_lots":bool,"applies_itbis":bool}} — no se muestra en el Treeview

        def _load(q=""):
            for i in tree.get_children(): tree.delete(i)
            extra_map.clear()
            conn = create_connection(); cur = conn.cursor()
            cur.execute("""
                SELECT p.id, p.name, p.category, p.price,
                       COALESCE(CASE WHEN p.manages_lots=1 THEN
                           (SELECT SUM(l.quantity_available) FROM lots l
                            WHERE l.product_id=p.id AND l.status='activo')
                       ELSE p.stock END, 0) AS stock,
                       p.manages_lots, p.applies_itbis
                FROM products p
                WHERE p.active = 1
                  AND (p.name LIKE ? OR p.category LIKE ? OR CAST(p.id AS CHAR) = ?)
                ORDER BY p.name LIMIT 100
            """, (f"%{q}%", f"%{q}%", q))
            for r in cur.fetchall():
                s = r[4]
                extra_map[r[0]] = {"manages_lots": bool(r[5]), "applies_itbis": bool(r[6])}
                tag = "sin_stock" if s == 0 else ("bajo_stock" if s <= threshold else "ok_stock")
                tree.insert("", "end", tags=(tag,),
                             values=(r[0], r[1], r[2] or "General",
                                     f"{currency} {r[3]:,.2f}", s))

        search_e.bind("<KeyRelease>", lambda e: _load(search_e.get().strip()))

        def _confirm(e=None):
            sel = tree.selection()
            if not sel: return
            v = tree.item(sel[0], "values")
            extra = extra_map.get(int(v[0]), {})
            prod = {
                "id":       int(v[0]),
                "name":     v[1],
                "category": v[2],
                "price":    float(v[3].replace(currency,"").replace(",","").strip()),
                "stock":    int(v[4]),
                "manages_lots": extra.get("manages_lots", True),
                "applies_itbis": extra.get("applies_itbis", True),
            }
            self._select(prod)
            win.destroy()

        tree.bind("<Double-1>", _confirm)
        ctk.CTkButton(win, text="✔  Seleccionar",
                      height=42, corner_radius=8,
                      fg_color=ACCENT, hover_color="#2EBF7A",
                      text_color="#0F1117", font=("Arial", 13, "bold"),
                      command=_confirm).pack(padx=20, pady=(0, 16))
        _load()
        search_e.focus()

    # ═══════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════

    def _toggle_clear(self):
        if self._entry.get():
            self._clear_btn.pack(side="right")
        else:
            self._clear_btn.pack_forget()
