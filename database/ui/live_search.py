"""
live_search.py — Barra de búsqueda con sugerencias en tiempo real.
Reutilizable en cualquier módulo del sistema.
"""
import customtkinter as ctk

BG          = "#0F1117"
CARD        = "#1A1D27"
CARD_BORDER = "#252836"
ACCENT      = "#3DD68C"
CYAN        = "#22D3EE"
TEXT        = "#FFFFFF"
SUBTEXT     = "#8B8FA8"
INPUT_BG    = "#23263A"
INPUT_BORDER= "#2E3148"
HOVER       = "#1A2E22"


class LiveSearch(ctk.CTkFrame):

    def __init__(self, parent, query_fn=None, on_select=None, on_change=None,
                 placeholder="🔍  Escribir para buscar...",
                 max_results=8, debounce_ms=160, min_chars=1, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self._query_fn   = query_fn
        self._on_select  = on_select
        self._on_change  = on_change
        self._max        = max_results
        self._debounce   = debounce_ms
        self._min_chars  = min_chars
        self._job        = None
        self._results    = []
        self._active_idx = -1
        self._btns       = []
        self._selecting  = False   # ← flag anti-reopen

        # Campo de entrada
        bar = ctk.CTkFrame(self, fg_color=INPUT_BG, corner_radius=10,
                            border_width=1, border_color=INPUT_BORDER)
        bar.pack(fill="x")
        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="x", padx=8, pady=4)

        ctk.CTkLabel(inner, text="🔍", font=("Arial", 13),
                     text_color=SUBTEXT, width=22).pack(side="left")

        self._entry = ctk.CTkEntry(inner, placeholder_text=placeholder,
                                    border_width=0, fg_color="transparent",
                                    height=34, font=("Arial", 13),
                                    text_color=TEXT,
                                    placeholder_text_color="#555870")
        self._entry.pack(side="left", fill="x", expand=True, padx=(4, 0))

        self._clr = ctk.CTkButton(inner, text="✕", width=26, height=26,
                                   corner_radius=5, fg_color="transparent",
                                   hover_color="#2E1A1A", text_color=SUBTEXT,
                                   font=("Arial", 12), command=self.clear)
        self._clr.pack(side="right")
        self._clr.pack_forget()

        # Popup
        self._popup = ctk.CTkFrame(self, fg_color=CARD, corner_radius=10,
                                    border_width=1, border_color=CARD_BORDER)

        # Bindings
        self._entry.bind("<KeyRelease>", self._on_key)
        self._entry.bind("<Down>",       self._move_down)
        self._entry.bind("<Up>",         self._move_up)
        self._entry.bind("<Return>",     self._confirm)
        self._entry.bind("<Escape>",     lambda e: self._hide())
        self._entry.bind("<FocusOut>",   lambda e: self.after(200, self._maybe_hide))

    # ── Interfaz pública ──────────────────────────────────────────
    def get(self) -> str:
        return self._entry.get()

    def set(self, text: str):
        self._entry.delete(0, "end")
        self._entry.insert(0, text)
        self._toggle_clear()

    def clear(self):
        self._selecting = False
        self._entry.delete(0, "end")
        self._hide()
        self._toggle_clear()
        if self._on_change:
            self._on_change("")

    def focus(self):
        self._entry.focus()

    # ── Debounce y búsqueda ───────────────────────────────────────
    def _on_key(self, event=None):
        # Ignorar eventos de teclado durante la selección
        if self._selecting:
            return
        self._toggle_clear()
        if self._job:
            self.after_cancel(self._job)
        text = self._entry.get().strip()
        if self._on_change:
            self._on_change(text)
        if len(text) >= self._min_chars and self._query_fn:
            self._job = self.after(self._debounce, lambda: self._search(text))
        else:
            self._hide()

    def _maybe_hide(self):
        """Solo oculta si no estamos en proceso de selección."""
        if not self._selecting:
            self._hide()

    def _search(self, text: str):
        if self._selecting:
            return
        try:
            results = self._query_fn(text)[:self._max]
        except Exception:
            results = []
        self._results = results
        if results:
            self._show_popup()
        else:
            self._hide()

    # ── Popup ─────────────────────────────────────────────────────
    def _show_popup(self):
        # Destruir botones anteriores
        for item in self._btns:
            if isinstance(item, tuple):
                for w in item:
                    try: w.destroy()
                    except Exception: pass
            else:
                try: item.destroy()
                except Exception: pass
        self._btns.clear()
        self._active_idx = -1

        for idx, item in enumerate(self._results):
            primary  = item[0] if isinstance(item, (list, tuple)) else item
            subtitle = item[1] if isinstance(item, (list, tuple)) and len(item) > 1 else ""

            row = ctk.CTkFrame(self._popup, fg_color="transparent", corner_radius=6)
            row.pack(fill="x", padx=6, pady=2)

            left = ctk.CTkFrame(row, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True, padx=4, pady=4)
            ctk.CTkLabel(left, text=primary, font=("Arial", 12, "bold"),
                         text_color=TEXT, anchor="w").pack(fill="x")
            if subtitle:
                ctk.CTkLabel(left, text=subtitle, font=("Arial", 10),
                             text_color=SUBTEXT, anchor="w").pack(fill="x")

            overlay = ctk.CTkButton(row, text="", fg_color="transparent",
                                     hover_color=HOVER, height=1,
                                     command=lambda p=primary: self._select(p))
            overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
            overlay.lower()
            self._btns.append((row, overlay))

        n = len(self._results)
        ctk.CTkFrame(self._popup, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=8)
        ctk.CTkLabel(self._popup,
                     text=f"{n} resultado{'s' if n != 1 else ''} — ↑↓ navegar · Enter seleccionar",
                     font=("Arial", 9), text_color=SUBTEXT).pack(pady=4)

        self._popup.pack(fill="x", pady=(4, 0))
        self._highlight(0)

    def _hide(self):
        self._popup.pack_forget()
        for item in self._btns:
            if isinstance(item, tuple):
                for w in item:
                    try: w.destroy()
                    except Exception: pass
            else:
                try: item.destroy()
                except Exception: pass
        self._btns.clear()
        self._results    = []
        self._active_idx = -1

    # ── Navegación ────────────────────────────────────────────────
    def _move_down(self, event=None):
        if self._results:
            self._highlight(min(self._active_idx + 1, len(self._results) - 1))
        return "break"

    def _move_up(self, event=None):
        if self._results:
            self._highlight(max(self._active_idx - 1, 0))
        return "break"

    def _highlight(self, idx: int):
        for i, (frame, _) in enumerate(self._btns):
            frame.configure(fg_color="#162B1F" if i == idx else "transparent")
        self._active_idx = idx

    def _confirm(self, event=None):
        """Enter: selecciona el item activo o el primero si ninguno está activo."""
        if self._results:
            idx = self._active_idx if 0 <= self._active_idx < len(self._results) else 0
            item = self._results[idx]
            self._select(item[0] if isinstance(item, (list, tuple)) else item)
        else:
            self._hide()
        return "break"

    def _select(self, value: str):
        """Selecciona un valor y cierra el popup sin reabrirlo."""
        self._selecting = True          # ← bloquear _on_key
        self._hide()                    # ← cerrar popup primero
        # Escribir el valor en el entry SIN disparar búsqueda
        self._entry.delete(0, "end")
        self._entry.insert(0, value)
        self._toggle_clear()
        if self._on_select:
            self._on_select(value)
        # Desbloquear después de 150ms (tiempo suficiente para que pasen los eventos)
        self.after(150, self._release_selecting)

    def _release_selecting(self):
        self._selecting = False

    def _toggle_clear(self):
        if self._entry.get():
            self._clr.pack(side="right")
        else:
            self._clr.pack_forget()
