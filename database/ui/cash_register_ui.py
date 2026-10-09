"""
cash_register_ui.py  —  Cuadre Diario de Caja
Reporte de cierre de jornada con ingresos brutos, netos,
desglose por método de pago y exportación a PDF/Excel.
"""
import os
from datetime import datetime, date, timedelta
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

import config
from database.connection import create_connection
from exports.excel_exporter import _open_file


BG          = "#0F1117"
CARD        = "#1A1D27"
CARD_BORDER = "#252836"
ACCENT      = "#3DD68C"
CYAN        = "#22D3EE"
TEXT        = "#FFFFFF"
SUBTEXT     = "#8B8FA8"
DANGER      = "#EF4444"
WARNING     = "#FFA94D"
PURPLE      = "#C084FC"
INPUT_BG    = "#23263A"
INPUT_BORDER= "#2E3148"



def _fmt_date(v):
    """Convierte fecha MySQL (datetime/date obj o string) a YYYY-MM-DD."""
    if v is None: return "—"
    if hasattr(v, "strftime"): return v.strftime("%Y-%m-%d")
    s = str(v); return s[:10] if len(s) >= 10 else s

def _fmt_time(v):
    """Extrae HH:MM de fecha MySQL (datetime obj o string)."""
    if v is None: return "—"
    if hasattr(v, "strftime"): return v.strftime("%H:%M")
    s = str(v); return s[11:16] if len(s) >= 16 else "—"


class CashRegisterUI:

    def __init__(self, parent):
        self.parent   = parent
        self._date    = date.today()
        self._canvas  = None

        container = ctk.CTkFrame(parent, fg_color=BG, corner_radius=0)
        container.pack(fill="both", expand=True)

        # ══════════════════════════════════════
        # ENCABEZADO + SELECTOR DE FECHA
        # ══════════════════════════════════════
        header = ctk.CTkFrame(container, fg_color=CARD, corner_radius=12,
                               border_width=1, border_color=CARD_BORDER)
        header.pack(fill="x", padx=20, pady=(16, 10))

        hrow = ctk.CTkFrame(header, fg_color="transparent")
        hrow.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(hrow, text="🏦  Cuadre Diario de Caja",
                     font=("Arial", 20, "bold"), text_color=TEXT).pack(side="left")

        # Controles de fecha
        date_ctrl = ctk.CTkFrame(hrow, fg_color="transparent")
        date_ctrl.pack(side="right")

        ctk.CTkButton(date_ctrl, text="◀", width=32, height=32, corner_radius=6,
                      fg_color=INPUT_BG, hover_color="#2E3148", text_color=SUBTEXT,
                      command=self._prev_day).pack(side="left", padx=2)

        self._date_lbl = ctk.CTkLabel(date_ctrl, text="",
                                       font=("Arial", 13, "bold"), text_color=CYAN,
                                       width=160)
        self._date_lbl.pack(side="left", padx=4)

        ctk.CTkButton(date_ctrl, text="▶", width=32, height=32, corner_radius=6,
                      fg_color=INPUT_BG, hover_color="#2E3148", text_color=SUBTEXT,
                      command=self._next_day).pack(side="left", padx=2)

        ctk.CTkButton(date_ctrl, text="📅 Hoy", width=70, height=32, corner_radius=6,
                      fg_color="#1A2E22", hover_color="#2EBF7A", text_color=ACCENT,
                      font=("Arial", 11), command=self._today).pack(side="left", padx=(8,0))

        # ══════════════════════════════════════
        # CUERPO DEL REPORTE
        # ══════════════════════════════════════
        self._scroll = ctk.CTkFrame(container, fg_color=BG, corner_radius=0)
        self._scroll.pack(fill="both", expand=True, padx=0, pady=0)

        self._load()

    # ═══════════════════════════════════════════
    # NAVEGACIÓN DE FECHA
    # ═══════════════════════════════════════════

    def _prev_day(self):
        self._date -= timedelta(days=1); self._load()

    def _next_day(self):
        if self._date < date.today():
            self._date += timedelta(days=1); self._load()

    def _today(self):
        self._date = date.today(); self._load()

    # ═══════════════════════════════════════════
    # CARGA DE DATOS
    # ═══════════════════════════════════════════

    def _load(self):
        """Consulta la BD y redibuja el reporte."""
        d = self._date
        self._date_lbl.configure(
            text=d.strftime("%A %d / %B / %Y").title()
        )
        self._data = self._query(d)
        self._build_report()

    def _query(self, d: date) -> dict:
        conn = create_connection()
        try:
            cur = conn.cursor()
            ds  = d.isoformat()

            # Facturas del día
            cur.execute("""
                SELECT id, customer_name, total, purchase_date,
                       IFNULL(employee,'—'), IFNULL(payment_method,'Efectivo')
                FROM invoices
                WHERE purchase_date LIKE ?
                ORDER BY id
            """, (f"{ds}%",))
            invoices = cur.fetchall()

            # Totales de items (subtotales antes de ITBIS)
            cur.execute("""
                SELECT IFNULL(SUM(ii.price * ii.quantity), 0)
                FROM invoice_items ii
                JOIN invoices i ON ii.invoice_id = i.id
                WHERE i.purchase_date LIKE ?
            """, (f"{ds}%",))
            subtotal_items = cur.fetchone()[0]

            # Total bruto (suma de totales de facturas)
            gross = sum(inv[2] for inv in invoices)

            # Desglose por método de pago
            cur.execute("""
                SELECT IFNULL(payment_method,'Efectivo'), COUNT(*), SUM(total)
                FROM invoices
                WHERE purchase_date LIKE ?
                GROUP BY payment_method
                ORDER BY SUM(total) DESC
            """, (f"{ds}%",))
            by_payment = cur.fetchall()

            # Productos más vendidos hoy
            cur.execute("""
                SELECT ii.product_name, SUM(ii.quantity) q, SUM(ii.total) t
                FROM invoice_items ii
                JOIN invoices i ON ii.invoice_id = i.id
                WHERE i.purchase_date LIKE ?
                GROUP BY ii.product_name
                ORDER BY q DESC
                LIMIT 10
            """, (f"{ds}%",))
            top_products = cur.fetchall()

            # Desglose por hora
            cur.execute("""
                SELECT DATE_FORMAT(purchase_date, '%H') hr, COUNT(*), SUM(total)
                FROM invoices
                WHERE purchase_date LIKE ?
                GROUP BY hr ORDER BY hr
            """, (f"{ds}%",))
            by_hour = cur.fetchall()

            # Config ITBIS
            cfg      = config.load()
            tax_rate = float(cfg["billing"].get("tax_rate", 0))
            currency = cfg["billing"].get("currency", "$")

            subtotal_items  = float(subtotal_items or 0)
            gross           = float(gross)
            itbis_collected = round(subtotal_items * tax_rate / 100, 2) if tax_rate > 0 else 0
            net_income      = round(gross - itbis_collected, 2)

        finally:
            conn.close()

        return {
            "invoices":       invoices,
            "gross":          gross,
            "subtotal_items": subtotal_items,
            "itbis":          itbis_collected,
            "net":            net_income,
            "tax_rate":       tax_rate,
            "currency":       currency,
            "by_payment":     by_payment,
            "top_products":   top_products,
            "by_hour":        by_hour,
            "count":          len(invoices),
        }

    # ═══════════════════════════════════════════
    # CONSTRUCCIÓN DEL REPORTE
    # ═══════════════════════════════════════════

    def _build_report(self):
        for w in self._scroll.winfo_children():
            w.destroy()
        if self._canvas:
            plt.close("all")
            self._canvas = None

        d  = self._data
        cy = d["currency"]

        # ── TARJETAS KPI ───────────────────────
        kpi_row = ctk.CTkFrame(self._scroll, fg_color="transparent")
        kpi_row.pack(fill="x", padx=20, pady=(12, 8))
        kpi_row.columnconfigure((0,1,2,3), weight=1)

        kpis = [
            ("🧾  Facturas",      str(d["count"]),              TEXT,   0),
            ("💰  Ingreso Bruto", f"{cy} {d['gross']:,.2f}",    ACCENT, 1),
            ("🏛  ITBIS Cobrado", f"{cy} {d['itbis']:,.2f}",    WARNING,2),
            ("✅  Ingreso Neto",  f"{cy} {d['net']:,.2f}",      CYAN,   3),
        ]
        for label, value, color, col in kpis:
            self._kpi_card(kpi_row, label, value, color, col)

        if d["count"] == 0:
            empty = ctk.CTkFrame(self._scroll, fg_color=CARD, corner_radius=12,
                                  border_width=1, border_color=CARD_BORDER)
            empty.pack(fill="x", padx=20, pady=20)
            ctk.CTkLabel(empty,
                         text="📭  Sin ventas registradas en esta fecha",
                         font=("Arial", 14), text_color=SUBTEXT).pack(pady=40)
            self._build_export_buttons()
            return

        # ── FILA: Gráfico por hora + Métodos de pago ──
        mid = ctk.CTkFrame(self._scroll, fg_color="transparent")
        mid.pack(fill="x", padx=20, pady=(0, 8))
        mid.columnconfigure(0, weight=3)
        mid.columnconfigure(1, weight=2)

        # Gráfico por hora
        chart_card = ctk.CTkFrame(mid, fg_color=CARD, corner_radius=12,
                                   border_width=1, border_color=CARD_BORDER)
        chart_card.grid(row=0, column=0, padx=(0,8), sticky="nsew")
        self._section_title(chart_card, "📈  Ventas por Hora")
        self._hourly_chart(chart_card, d["by_hour"], cy)

        # Métodos de pago
        pay_card = ctk.CTkFrame(mid, fg_color=CARD, corner_radius=12,
                                 border_width=1, border_color=CARD_BORDER)
        pay_card.grid(row=0, column=1, sticky="nsew")
        self._section_title(pay_card, "💳  Por Método de Pago")
        self._payment_table(pay_card, d["by_payment"], cy, d["gross"])

        # ── PRODUCTOS MÁS VENDIDOS ─────────────
        prod_card = ctk.CTkFrame(self._scroll, fg_color=CARD, corner_radius=12,
                                  border_width=1, border_color=CARD_BORDER)
        prod_card.pack(fill="x", padx=20, pady=(0, 8))
        self._section_title(prod_card, "🏆  Productos Más Vendidos Hoy")
        self._products_table(prod_card, d["top_products"], cy)

        # ── DETALLE DE FACTURAS ─────────────────
        inv_card = ctk.CTkFrame(self._scroll, fg_color=CARD, corner_radius=12,
                                 border_width=1, border_color=CARD_BORDER)
        inv_card.pack(fill="x", padx=20, pady=(0, 20))
        self._section_title(inv_card, "🧾  Detalle de Facturas del Día")
        self._invoices_table(inv_card, d["invoices"], cy)

        # ── RESUMEN DE CIERRE ──────────────────
        self._closure_summary()
        self._build_export_buttons()

    # ═══════════════════════════════════════════
    # COMPONENTES
    # ═══════════════════════════════════════════

    def _kpi_card(self, parent, label, value, color, col):
        f = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=12,
                         border_width=1, border_color=CARD_BORDER)
        f.grid(row=0, column=col, padx=(0 if col==0 else 6, 0), sticky="ew")
        ctk.CTkLabel(f, text=label, font=("Arial", 11),
                     text_color=SUBTEXT).pack(anchor="w", padx=14, pady=(12,0))
        ctk.CTkLabel(f, text=value, font=("Arial", 20, "bold"),
                     text_color=color).pack(anchor="w", padx=14, pady=(2,14))

    def _section_title(self, parent, text):
        ctk.CTkLabel(parent, text=text, font=("Arial", 12, "bold"),
                     text_color=SUBTEXT).pack(anchor="w", padx=14, pady=(12,2))
        ctk.CTkFrame(parent, height=1, fg_color=CARD_BORDER).pack(
            fill="x", padx=14, pady=(0,8))

    def _hourly_chart(self, parent, by_hour, currency):
        if not by_hour:
            ctk.CTkLabel(parent, text="Sin datos", text_color=SUBTEXT,
                         font=("Arial", 12)).pack(pady=20)
            return
        fig, ax = plt.subplots(figsize=(4.2, 2.2))
        fig.patch.set_facecolor(CARD)
        ax.set_facecolor(CARD)
        hrs  = [f"{h[0]}h" for h in by_hour]
        vals = [h[2] for h in by_hour]
        bars = ax.bar(hrs, vals, color=ACCENT, width=0.5)
        ax.tick_params(colors=SUBTEXT, labelsize=7)
        ax.spines[:].set_visible(False)
        ax.yaxis.set_visible(False)
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width()/2,
                    bar.get_height() + max(vals)*0.02,
                    f"{currency}{val:,.0f}",
                    ha="center", color=SUBTEXT, fontsize=6)
        fig.tight_layout(pad=0.4)
        cv = FigureCanvasTkAgg(fig, parent)
        cv.get_tk_widget().pack(padx=10, pady=(0,12), fill="x")
        cv.draw()
        plt.close(fig)

    def _payment_table(self, parent, by_payment, currency, gross):
        style = ttk.Style(); style.theme_use("clam")
        style.configure("CR.Treeview", background="#1A1D27", foreground="#FFFFFF",
                         fieldbackground="#1A1D27", borderwidth=0,
                         font=("Arial", 11), rowheight=30)
        style.configure("CR.Treeview.Heading", background="#1E2130",
                         foreground="#8B8FA8", font=("Arial", 10, "bold"), borderwidth=0)
        style.map("CR.Treeview", background=[("selected", "#1A2E22"), ("!selected", "#1A1D27")],
                  foreground=[("selected", "#3DD68C"), ("!selected", "#FFFFFF")])

        cols = ("Método", "Facturas", "Total", "%")
        tree = ttk.Treeview(parent, columns=cols, show="headings",
                             height=min(len(by_payment)+1, 6), style="CR.Treeview")
        try:
            tree.tk.call("ttk::style", "configure", tree["style"], "-fieldbackground", "#1A1D27")
            tree.tk.call("ttk::style", "configure", tree["style"], "-background", "#1A1D27")
            tree.tk.call("ttk::style", "configure", tree["style"], "-foreground", "#FFFFFF")
        except Exception:
            pass
        for col, w, anc in [("Método",150,"w"),("Facturas",65,"center"),
                              ("Total",100,"e"),("%",55,"center")]:
            tree.heading(col, text=col); tree.column(col, width=w, anchor=anc)

        for row in by_payment:
            row2 = float(row[2] or 0)
            pct = (row2 / gross * 100) if gross > 0 else 0
            tree.insert("", "end", values=(
                row[0], row[1], f"{currency} {row2:,.2f}", f"{pct:.1f}%"
            ))
        tree.pack(padx=10, pady=(0,12), fill="x")

    def _products_table(self, parent, products, currency):
        style = ttk.Style()
        style.configure("PRD2.Treeview", background="#1A1D27", foreground="#FFFFFF",
                         fieldbackground="#1A1D27", borderwidth=0,
                         font=("Arial", 11), rowheight=28)
        style.configure("PRD2.Treeview.Heading", background="#1E2130",
                         foreground="#8B8FA8", font=("Arial", 10, "bold"), borderwidth=0)
        style.map("PRD2.Treeview", background=[("selected", "#1A2E22"), ("!selected", "#1A1D27")],
                  foreground=[("selected", "#3DD68C"), ("!selected", "#FFFFFF")])

        cols = ("#", "Producto", "Cant.", "Total")
        tree = ttk.Treeview(parent, columns=cols, show="headings",
                             height=min(len(products), 8), style="PRD2.Treeview")
        try:
            tree.tk.call("ttk::style", "configure", tree["style"], "-fieldbackground", "#1A1D27")
            tree.tk.call("ttk::style", "configure", tree["style"], "-background", "#1A1D27")
            tree.tk.call("ttk::style", "configure", tree["style"], "-foreground", "#FFFFFF")
        except Exception:
            pass
        for col, w, anc in [("#",40,"center"),("Producto",280,"w"),
                              ("Cant.",70,"center"),("Total",110,"e")]:
            tree.heading(col, text=col); tree.column(col, width=w, anchor=anc)
        for i, row in enumerate(products, 1):
            tree.insert("", "end", values=(
                i, row[0], row[1], f"{currency} {float(row[2] or 0):,.2f}"
            ))
        tree.pack(padx=10, pady=(0,12), fill="x")

    def _invoices_table(self, parent, invoices, currency):
        style = ttk.Style()
        style.configure("INV2.Treeview", background="#1A1D27", foreground="#FFFFFF",
                         fieldbackground="#1A1D27", borderwidth=0,
                         font=("Arial", 11), rowheight=28)
        style.configure("INV2.Treeview.Heading", background="#1E2130",
                         foreground="#8B8FA8", font=("Arial", 10, "bold"), borderwidth=0)
        style.map("INV2.Treeview", background=[("selected", "#1A2E22"), ("!selected", "#1A1D27")],
                  foreground=[("selected", "#3DD68C"), ("!selected", "#FFFFFF")])

        cols = ("N°", "Cliente", "Hora", "Cajero", "Método", "Total")
        tree = ttk.Treeview(parent, columns=cols, show="headings",
                             height=min(len(invoices), 10), style="INV2.Treeview")
        try:
            tree.tk.call("ttk::style", "configure", tree["style"], "-fieldbackground", "#1A1D27")
            tree.tk.call("ttk::style", "configure", tree["style"], "-background", "#1A1D27")
            tree.tk.call("ttk::style", "configure", tree["style"], "-foreground", "#FFFFFF")
        except Exception:
            pass
        for col, w, anc in [("N°",60,"center"),("Cliente",180,"w"),
                              ("Hora",70,"center"),("Cajero",100,"w"),
                              ("Método",130,"w"),("Total",100,"e")]:
            tree.heading(col, text=col); tree.column(col, width=w, anchor=anc)

        for inv in invoices:
            hora = _fmt_time(inv[3])
            tree.insert("", "end", values=(
                f"#{inv[0]:06d}", inv[1], hora, inv[4], inv[5],
                f"{currency} {float(inv[2] or 0):,.2f}"
            ))
        tree.pack(padx=10, pady=(0,12), fill="x")

    def _closure_summary(self):
        """Tarjeta de resumen para el cierre de caja."""
        d  = self._data
        cy = d["currency"]

        box = ctk.CTkFrame(self._scroll, fg_color="#0D1F14", corner_radius=12,
                            border_width=2, border_color=ACCENT)
        box.pack(fill="x", padx=20, pady=(0, 24))

        ctk.CTkLabel(box, text="✅  RESUMEN DE CIERRE DE CAJA",
                     font=("Arial", 13, "bold"), text_color=ACCENT
                     ).pack(anchor="w", padx=16, pady=(14,2))
        ctk.CTkFrame(box, height=1, fg_color=ACCENT).pack(
            fill="x", padx=16, pady=(0,10))

        rows = [
            ("Fecha de cierre",        self._date.strftime("%d/%m/%Y")),
            ("Hora de generación",     datetime.now().strftime("%I:%M %p")),
            ("Total de transacciones", str(d["count"])),
            ("Ingreso bruto del día",  f"{cy} {d['gross']:,.2f}"),
        ]
        if d["tax_rate"] > 0:
            rows.append((f"ITBIS ({d['tax_rate']:.0f}%) cobrado",
                         f"{cy} {d['itbis']:,.2f}"))
        rows.append(("Ingreso neto del día", f"{cy} {d['net']:,.2f}"))

        # Método de pago dominante
        if d["by_payment"]:
            top_pay = d["by_payment"][0]
            rows.append(("Método de pago principal",
                         f"{top_pay[0]} ({top_pay[1]} facturas)"))

        grid = ctk.CTkFrame(box, fg_color="transparent")
        grid.pack(fill="x", padx=16, pady=(0,14))
        grid.columnconfigure((0,1), weight=1)

        for i, (lbl, val) in enumerate(rows):
            r, c = divmod(i, 2)
            ctk.CTkLabel(grid, text=f"{lbl}:",
                         font=("Arial", 11), text_color=SUBTEXT,
                         anchor="w").grid(row=r*2, column=c, sticky="w", padx=10, pady=(8,0))
            color = ACCENT if "neto" in lbl.lower() else TEXT
            ctk.CTkLabel(grid, text=val,
                         font=("Arial", 12, "bold"), text_color=color,
                         anchor="w").grid(row=r*2+1, column=c, sticky="w", padx=10, pady=(0,4))

    # ═══════════════════════════════════════════
    # EXPORTACIÓN
    # ═══════════════════════════════════════════

    def _build_export_buttons(self):
        """Botones de exportación al final del reporte."""
        act = ctk.CTkFrame(self._scroll, fg_color=CARD, corner_radius=12,
                            border_width=1, border_color=CARD_BORDER)
        act.pack(fill="x", padx=20, pady=(0, 24))
        ctk.CTkLabel(act, text="Exportar Reporte",
                     font=("Arial", 12, "bold"), text_color=SUBTEXT
                     ).pack(anchor="w", padx=16, pady=(12, 2))
        ctk.CTkFrame(act, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=16, pady=(0, 10))
        arow = ctk.CTkFrame(act, fg_color="transparent")
        arow.pack(padx=16, pady=(0, 14))
        for text, fg, hov, tc, cmd in [
            ("📄  Exportar PDF",   "#1A2E3A", "#1E6A9A", CYAN,   self._export_pdf),
            ("📊  Exportar Excel", "#1A3A2A", "#2EBF7A", ACCENT, self._export_excel),
            ("🖨  Imprimir",       "#2A1A3A", "#6B21A8", PURPLE, self._print_report),
        ]:
            ctk.CTkButton(arow, text=text, height=40, corner_radius=8,
                          fg_color=fg, hover_color=hov, text_color=tc,
                          font=("Arial", 12, "bold"), command=cmd
                          ).pack(side="left", padx=(0, 8))

    def _export_pdf(self):
        d      = self._data
        cy     = d["currency"]
        ds     = self._date.strftime("%Y-%m-%d")
        fname  = f"Cuadre_Caja_{ds}.pdf"
        cfg    = config.load()
        ph     = cfg["pharmacy"]

        doc = SimpleDocTemplate(fname, pagesize=letter,
                                 leftMargin=2*cm, rightMargin=2*cm,
                                 topMargin=2*cm, bottomMargin=2*cm)

        def P(text, fs=10, bold=False, align=TA_LEFT, color=colors.black):
            fn = "Helvetica-Bold" if bold else "Helvetica"
            return Paragraph(text, ParagraphStyle("p", fontSize=fs,
                             fontName=fn, alignment=align,
                             textColor=color, leading=fs+4))

        def HR():
            return HRFlowable(width="100%", thickness=0.5,
                               color=colors.HexColor("#CCCCCC"),
                               spaceBefore=6, spaceAfter=6)

        elems = []

        # Encabezado
        elems += [
            P(ph.get("name") or "FarmaFactura Pro", 16, True, TA_CENTER),
            P(ph.get("address") or "", 9, align=TA_CENTER,
              color=colors.HexColor("#666666")),
            P(f"RNC: {ph.get('rnc') or '—'}", 9, align=TA_CENTER,
              color=colors.HexColor("#666666")),
            Spacer(1, 8),
            P("CUADRE DIARIO DE CAJA", 14, True, TA_CENTER),
            P(f"Fecha: {self._date.strftime('%d/%m/%Y')}  |  "
              f"Generado: {datetime.now().strftime('%d/%m/%Y %I:%M %p')}",
              9, align=TA_CENTER, color=colors.HexColor("#666666")),
            HR(),
        ]

        # KPIs
        kpi_data = [
            ["Facturas emitidas", "Ingreso Bruto", "ITBIS Cobrado", "Ingreso Neto"],
            [str(d["count"]),
             f"{cy} {d['gross']:,.2f}",
             f"{cy} {d['itbis']:,.2f}",
             f"{cy} {d['net']:,.2f}"],
        ]
        kpi_t = Table(kpi_data, colWidths=[4*cm]*4)
        kpi_t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,0), colors.HexColor("#1A1D27")),
            ("TEXTCOLOR",     (0,0),(-1,0), colors.HexColor("#3DD68C")),
            ("FONTNAME",      (0,0),(-1,0), "Helvetica-Bold"),
            ("FONTSIZE",      (0,0),(-1,-1), 10),
            ("BACKGROUND",    (3,1),(3,1), colors.HexColor("#E8F5EE")),
            ("FONTNAME",      (3,1),(3,1), "Helvetica-Bold"),
            ("ALIGN",         (0,0),(-1,-1), "CENTER"),
            ("TOPPADDING",    (0,0),(-1,-1), 8),
            ("BOTTOMPADDING", (0,0),(-1,-1), 8),
            ("GRID",          (0,0),(-1,-1), 0.5, colors.HexColor("#DDDDDD")),
        ]))
        elems += [kpi_t, Spacer(1, 12)]

        # Por método de pago
        elems.append(P("Desglose por Método de Pago", 11, True))
        elems.append(HR())
        pay_data = [["Método", "Facturas", "Total", "%"]]
        for row in d["by_payment"]:
            pct = (row[2]/d["gross"]*100) if d["gross"] > 0 else 0
            pay_data.append([row[0], str(row[1]),
                             f"{cy} {row[2]:,.2f}", f"{pct:.1f}%"])
        pay_t = Table(pay_data, colWidths=[6*cm, 3*cm, 4*cm, 3*cm])
        pay_t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,0), colors.HexColor("#1E2130")),
            ("TEXTCOLOR",     (0,0),(-1,0), colors.HexColor("#8B8FA8")),
            ("FONTNAME",      (0,0),(-1,0), "Helvetica-Bold"),
            ("FONTSIZE",      (0,0),(-1,-1), 10),
            ("ALIGN",         (1,0),(-1,-1), "RIGHT"),
            ("ALIGN",         (0,0),(0,-1), "LEFT"),
            ("TOPPADDING",    (0,0),(-1,-1), 6),
            ("BOTTOMPADDING", (0,0),(-1,-1), 6),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),
             [colors.HexColor("#F8F8F8"), colors.white]),
            ("GRID",          (0,0),(-1,-1), 0.5, colors.HexColor("#DDDDDD")),
        ]))
        elems += [pay_t, Spacer(1, 12)]

        # Productos más vendidos
        elems.append(P("Productos Más Vendidos", 11, True))
        elems.append(HR())
        prod_data = [["#", "Producto", "Cant.", "Total"]]
        for i, row in enumerate(d["top_products"], 1):
            prod_data.append([str(i), row[0], str(row[1]),
                              f"{cy} {float(row[2] or 0):,.2f}"])
        prod_t = Table(prod_data, colWidths=[1*cm, 9*cm, 2*cm, 4*cm])
        prod_t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,0), colors.HexColor("#1E2130")),
            ("TEXTCOLOR",     (0,0),(-1,0), colors.HexColor("#8B8FA8")),
            ("FONTNAME",      (0,0),(-1,0), "Helvetica-Bold"),
            ("FONTSIZE",      (0,0),(-1,-1), 9),
            ("ALIGN",         (2,0),(-1,-1), "RIGHT"),
            ("ALIGN",         (0,0),(1,-1), "LEFT"),
            ("TOPPADDING",    (0,0),(-1,-1), 5),
            ("BOTTOMPADDING", (0,0),(-1,-1), 5),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),
             [colors.HexColor("#F8F8F8"), colors.white]),
            ("GRID",          (0,0),(-1,-1), 0.5, colors.HexColor("#DDDDDD")),
        ]))
        elems += [prod_t, Spacer(1, 12)]

        # Detalle facturas
        elems.append(P("Detalle de Facturas", 11, True))
        elems.append(HR())
        inv_data = [["N°", "Cliente", "Hora", "Cajero", "Método", "Total"]]
        for inv in d["invoices"]:
            hora = _fmt_time(inv[3])
            inv_data.append([f"#{inv[0]:06d}", inv[1], hora,
                              inv[4], inv[5], f"{cy} {float(inv[2] or 0):,.2f}"])
        inv_t = Table(inv_data, colWidths=[2*cm, 4*cm, 1.5*cm, 2.5*cm, 3*cm, 3*cm])
        inv_t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,0), colors.HexColor("#1E2130")),
            ("TEXTCOLOR",     (0,0),(-1,0), colors.HexColor("#8B8FA8")),
            ("FONTNAME",      (0,0),(-1,0), "Helvetica-Bold"),
            ("FONTSIZE",      (0,0),(-1,-1), 8),
            ("ALIGN",         (5,0),(-1,-1), "RIGHT"),
            ("TOPPADDING",    (0,0),(-1,-1), 4),
            ("BOTTOMPADDING", (0,0),(-1,-1), 4),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),
             [colors.HexColor("#F8F8F8"), colors.white]),
            ("GRID",          (0,0),(-1,-1), 0.3, colors.HexColor("#DDDDDD")),
        ]))
        elems.append(inv_t)

        doc.build(elems)
        _open_file(fname)
        messagebox.showinfo("PDF generado", f"Reporte guardado:\n{os.path.abspath(fname)}")

    def _export_excel(self):
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

        d   = self._data
        cy  = d["currency"]
        ds  = self._date.strftime("%Y-%m-%d")
        fname = f"Cuadre_Caja_{ds}.xlsx"

        wb = openpyxl.Workbook()

        # ── Hoja Resumen ──
        ws = wb.active; ws.title = "Resumen"
        h_fill = PatternFill("solid", fgColor="1A1D27")
        h_font = Font(bold=True, color="3DD68C", size=11)
        bold14 = Font(bold=True, size=14, color="0F1117")
        accent_fill = PatternFill("solid", fgColor="3DD68C")

        ws["A1"] = "CUADRE DIARIO DE CAJA"
        ws["A1"].font = Font(bold=True, size=14)
        ws["A2"] = f"Fecha: {ds}"
        ws["A3"] = f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}"

        ws.append([])
        headers = ["Métrica", "Valor"]
        ws.append(headers)
        for cell in ws[ws.max_row]:
            cell.fill = h_fill; cell.font = h_font

        resumen = [
            ("Facturas emitidas",  d["count"]),
            ("Ingreso bruto",      f"{cy} {d['gross']:,.2f}"),
            (f"ITBIS ({d['tax_rate']:.0f}%)", f"{cy} {d['itbis']:,.2f}"),
            ("Ingreso neto",       f"{cy} {d['net']:,.2f}"),
        ]
        for row in resumen:
            ws.append(list(row))

        ws.column_dimensions["A"].width = 25
        ws.column_dimensions["B"].width = 20

        # ── Hoja Métodos de Pago ──
        ws2 = wb.create_sheet("Métodos de Pago")
        ws2.append(["Método", "Facturas", "Total", "Porcentaje"])
        for cell in ws2[1]: cell.fill = h_fill; cell.font = h_font
        for row in d["by_payment"]:
            pct = (row[2]/d["gross"]*100) if d["gross"] > 0 else 0
            ws2.append([row[0], row[1], f"{cy} {row[2]:,.2f}", f"{pct:.1f}%"])

        # ── Hoja Productos ──
        ws3 = wb.create_sheet("Productos")
        ws3.append(["#", "Producto", "Cantidad", "Total"])
        for cell in ws3[1]: cell.fill = h_fill; cell.font = h_font
        for i, row in enumerate(d["top_products"], 1):
            ws3.append([i, row[0], row[1], f"{cy} {float(row[2] or 0):,.2f}"])

        # ── Hoja Facturas ──
        ws4 = wb.create_sheet("Facturas")
        ws4.append(["N° Factura", "Cliente", "Hora", "Cajero", "Método", "Total"])
        for cell in ws4[1]: cell.fill = h_fill; cell.font = h_font
        for inv in d["invoices"]:
            hora = _fmt_time(inv[3])
            ws4.append([f"#{inv[0]:06d}", inv[1], hora, inv[4], inv[5],
                        f"{cy} {float(inv[2] or 0):,.2f}"])

        wb.save(fname)
        _open_file(fname)
        messagebox.showinfo("Excel generado", f"Reporte guardado:\n{os.path.abspath(fname)}")

    def _print_report(self):
        """Genera el PDF y lo envía directamente al diálogo de impresión."""
        self._export_pdf()
