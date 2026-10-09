import customtkinter as ctk
from tkinter import ttk, messagebox
from database.connection import create_connection
from exports.excel_exporter import export_to_excel
from ui.predictive_search import PredictiveSearch
from auth import session
import config
from utils.logger import audit, log_price_change

BG="#0F1117"; CARD="#1A1D27"; CARD_BORDER="#252836"
ACCENT="#3DD68C"; CYAN="#22D3EE"; TEXT="#FFFFFF"; SUBTEXT="#8B8FA8"
DANGER="#EF4444"; DANGER_H="#DC2626"; WARNING="#FFA94D"
INPUT_BG="#23263A"; INPUT_BORDER="#2E3148"

CATEGORIES=["General","Analgésicos","Antibióticos","Antiinflamatorios",
            "Vitaminas","Antihistamínicos","Cardiovascular","Diabetes",
            "Dermatología","Oftalmología","Otros"]

PRESENTATIONS=["Tabletas","Cápsulas","Jarabe","Suspensión","Inyectable",
               "Crema","Ungüento","Gotas","Parche","Supositorio","Otro"]


class ProductsUI:
    def __init__(self, parent):
        self.parent=parent; self._selected_id=None
        self._page=0; self._page_size=20; self._search_q=""
        self.is_admin=session.current_role in ("admin","Administrador")

        container=ctk.CTkFrame(parent,fg_color=BG,corner_radius=0)
        container.pack(fill="both",expand=True)

        # ── Encabezado ──
        hdr=ctk.CTkFrame(container,fg_color="transparent")
        hdr.pack(fill="x",padx=20,pady=(20,0))
        ctk.CTkLabel(hdr,text="📦  Inventario de Productos",
                     font=("Arial",22,"bold"),text_color=TEXT).pack(side="left")
        ctk.CTkFrame(container,height=1,fg_color=CARD_BORDER).pack(fill="x",padx=20,pady=(10,16))

        # ── Formulario con Tabs ──
        form_tabs = ctk.CTkTabview(
            container,
            fg_color=CARD, corner_radius=12,
            segmented_button_fg_color="#1E2130",
            segmented_button_selected_color=ACCENT,
            segmented_button_selected_hover_color="#2EBF7A",
            segmented_button_unselected_color="#1E2130",
            segmented_button_unselected_hover_color="#252836",
            text_color=TEXT, text_color_disabled=SUBTEXT,
            border_width=1, border_color=CARD_BORDER,
        )
        form_tabs.pack(fill="x", padx=20, pady=(0,8))
        form_tabs.add("📋  Ficha")
        form_tabs.add("📦  Presentaciones")
        form   = form_tabs.tab("📋  Ficha")
        tab_pu = form_tabs.tab("📦  Presentaciones")

        # Fila 1: Nombre comercial, Principio activo, Laboratorio
        r1=ctk.CTkFrame(form,fg_color="transparent"); r1.pack(fill="x",padx=16,pady=(0,8))
        r1.columnconfigure((0,1,2),weight=1)
        self.name_entry  =self._lf(r1,"Nombre Comercial",0)
        self.actv_entry  =self._lf(r1,"Principio Activo",1)
        self.lab_entry   =self._lf(r1,"Laboratorio Fabricante",2)

        # Fila 2: Presentación, Categoría, Precio, Costo, Stock, Stock Mín
        r2=ctk.CTkFrame(form,fg_color="transparent"); r2.pack(fill="x",padx=16,pady=(0,8))
        r2.columnconfigure((0,1,2,3,4,5),weight=1)

        # Presentación
        pw=ctk.CTkFrame(r2,fg_color="transparent")
        pw.grid(row=0,column=0,padx=(0,8),sticky="ew")
        ctk.CTkLabel(pw,text="Presentación",font=("Arial",11),text_color=SUBTEXT).pack(anchor="w")
        self.pres_var=ctk.StringVar(value="Tabletas")
        ctk.CTkOptionMenu(pw,values=PRESENTATIONS,variable=self.pres_var,
                          fg_color=INPUT_BG,button_color="#2A2D3A",
                          button_hover_color="#3A3D52",dropdown_fg_color="#1A1D27",
                          dropdown_hover_color="#1A2E22",text_color=TEXT,
                          font=("Arial",12),height=38,
                          dynamic_resizing=False
                          ).pack(fill="x",pady=(3,0))

        # Categoría
        cw=ctk.CTkFrame(r2,fg_color="transparent")
        cw.grid(row=0,column=1,padx=(0,8),sticky="ew")
        ctk.CTkLabel(cw,text="Categoría",font=("Arial",11),text_color=SUBTEXT).pack(anchor="w")
        self.category_var=ctk.StringVar(value="General")
        ctk.CTkOptionMenu(cw,values=CATEGORIES,variable=self.category_var,
                          fg_color=INPUT_BG,button_color="#2A2D3A",
                          button_hover_color="#3A3D52",dropdown_fg_color="#1A1D27",
                          dropdown_hover_color="#1A2E22",text_color=TEXT,
                          font=("Arial",12),height=38,
                          dynamic_resizing=False
                          ).pack(fill="x",pady=(3,0))

        self.price_entry =self._lf(r2,"Precio Venta",2)
        self.cost_entry  =self._lf(r2,"Costo",3)
        self.stock_entry =self._lf(r2,"Stock (informativo)",4)
        self._make_readonly(self.stock_entry)
        self.minstk_entry=self._lf(r2,"Stock Mínimo",5)

        # Fila 2b: ¿Aplica ITBIS?
        r2b=ctk.CTkFrame(form,fg_color="transparent"); r2b.pack(fill="x",padx=16,pady=(0,8))
        self.applies_itbis_var=ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(r2b,text="¿Aplica ITBIS?",
            variable=self.applies_itbis_var,fg_color=ACCENT,hover_color="#2EBF7A",
            checkmark_color="#0F1117",font=("Arial",12),text_color=TEXT
            ).pack(side="left")

        # Fila 3: Proveedor
        r3=ctk.CTkFrame(form,fg_color="transparent"); r3.pack(fill="x",padx=16,pady=(0,8))
        r3.columnconfigure((0,1),weight=1)

        sw=ctk.CTkFrame(r3,fg_color="transparent")
        sw.grid(row=0,column=0,padx=(0,8),sticky="ew")
        ctk.CTkLabel(sw,text="Proveedor",font=("Arial",11),text_color=SUBTEXT).pack(anchor="w")
        self.supplier_var=ctk.StringVar(value="Sin proveedor")
        self.supplier_menu=ctk.CTkOptionMenu(sw,values=["Sin proveedor"],
                            variable=self.supplier_var,
                            fg_color=INPUT_BG,button_color="#2A2D3A",
                            button_hover_color="#3A3D52",dropdown_fg_color="#1A1D27",
                            dropdown_hover_color="#1A2E22",text_color=TEXT,
                            font=("Arial",12),height=38,dynamic_resizing=False)
        self.supplier_menu.pack(fill="x",pady=(3,0))
        self._load_suppliers()

        # Búsqueda predictiva
        sr=ctk.CTkFrame(form,fg_color="transparent"); sr.pack(fill="x",padx=16,pady=(0,8))
        self.search_entry=PredictiveSearch(sr,on_select=self._on_inv_search_select,
                                           placeholder="🔍  Buscar por nombre, principio activo o ID...",
                                           show_picker_btn=False)
        self.search_entry.pack(fill="x")
        self.search_entry._entry.bind("<KeyRelease>",
                                      lambda e: self.after_search())

        # Botones
        br=ctk.CTkFrame(form,fg_color="transparent"); br.pack(fill="x",padx=16,pady=(0,16))
        if self.is_admin:
            self.btn_agregar=ctk.CTkButton(br,text="＋ Agregar",height=38,corner_radius=8,
                              fg_color=ACCENT,hover_color="#2EBF7A",text_color="#0F1117",
                              font=("Arial",12,"bold"),command=self.add_product)
            self.btn_agregar.pack(side="left",padx=(0,8))

            self.btn_actualizar=ctk.CTkButton(br,text="✎ Actualizar",height=38,corner_radius=8,
                              fg_color="#1A3A4A",hover_color="#1E6A9A",text_color=CYAN,
                              font=("Arial",12,"bold"),command=self.update_product)
            self.btn_actualizar.pack(side="left",padx=(0,8))
            self.btn_actualizar.pack_forget()  # Oculto por defecto

            ctk.CTkButton(br,text="🗑 Eliminar",height=38,corner_radius=8,
                              fg_color="#2E1A1A",hover_color=DANGER_H,text_color=DANGER,
                              font=("Arial",12,"bold"),command=self.delete_product).pack(side="left",padx=(0,8))
            ctk.CTkButton(br,text="↺ Limpiar",height=38,corner_radius=8,
                              fg_color=INPUT_BG,hover_color="#2E3148",text_color=SUBTEXT,
                              font=("Arial",12,"bold"),command=self.clear_fields).pack(side="left",padx=(0,8))
            ctk.CTkButton(br,text="📊 Exportar",height=38,corner_radius=8,
                              fg_color="#1A3A2A",hover_color="#2EBF7A",text_color=ACCENT,
                              font=("Arial",12,"bold"),command=self.export_products).pack(side="left",padx=(0,8))
        else:
            ctk.CTkLabel(br,text="🔒  Solo lectura",font=("Arial",12),text_color=WARNING).pack(side="left")

        # ── Pestaña: Presentaciones de Venta ──
        ctk.CTkFrame(tab_pu, height=4, fg_color="transparent").pack()

        ur = ctk.CTkFrame(tab_pu, fg_color="transparent")
        ur.pack(fill="x", padx=16, pady=(0,4))
        ur.columnconfigure((0,1,2,3), weight=1)

        def _uf(parent, ph, col, lbl, pad=(0,8)):
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.grid(row=0, column=col, padx=pad, sticky="ew")
            ctk.CTkLabel(f, text=lbl, font=("Arial",10), text_color=SUBTEXT).pack(anchor="w")
            ef = ctk.CTkFrame(f, fg_color=INPUT_BG, corner_radius=8,
                               border_width=1, border_color=INPUT_BORDER)
            ef.pack(fill="x", pady=(2,0))
            e = ctk.CTkEntry(ef, border_width=0, fg_color="transparent",
                              height=34, font=("Arial",12), text_color=TEXT,
                              placeholder_text=ph)
            e.pack(fill="x", padx=8)
            return e

        self.unit_name_entry   = _uf(ur, "Ej: Caja, Blíster, Sobre",    0, "Presentación")
        self.unit_factor_entry = _uf(ur, "Ej: 100  (caja=100 unidades)", 1, "Factor (unidades base)")
        self.unit_price_entry  = _uf(ur, "Vacío = precio base × factor", 2, "Precio (opcional)")

        uf3 = ctk.CTkFrame(ur, fg_color="transparent")
        uf3.grid(row=0, column=3, padx=(0,0), sticky="ew")
        ctk.CTkLabel(uf3, text=" ", font=("Arial",10), text_color=SUBTEXT).pack(anchor="w")
        ctk.CTkButton(uf3, text="➕ Agregar Presentación", height=34, corner_radius=8,
                      fg_color=ACCENT, hover_color="#2EBF7A", text_color="#0F1117",
                      font=("Arial",11,"bold"), command=self._add_unit
                      ).pack(fill="x", pady=(2,0))

        ul = ctk.CTkFrame(tab_pu, fg_color="#1A1D27", corner_radius=8)
        ul.pack(fill="x", padx=16, pady=(6,4))
        sty_u = ttk.Style(); sty_u.theme_use("clam")
        sty_u.configure("UN.Treeview", background="#1A1D27", foreground="#FFFFFF",
                         fieldbackground="#1A1D27", borderwidth=0, font=("Arial",11), rowheight=26)
        sty_u.configure("UN.Treeview.Heading", background="#1E2130", foreground="#8B8FA8",
                         font=("Arial",10,"bold"), borderwidth=0)
        sty_u.map("UN.Treeview",
                  background=[("selected","#1A2E22"),("!selected","#1A1D27")],
                  foreground=[("selected","#3DD68C"),("!selected","#FFFFFF")])
        self.units_tree = ttk.Treeview(ul,
            columns=("uid","Presentación","Factor","Precio","Base","Default"),
            show="headings", height=3, style="UN.Treeview")
        for col2,w2,anc2 in [("uid",0,"w"),("Presentación",150,"w"),
                               ("Factor",80,"center"),("Precio",110,"e"),
                               ("Base",60,"center"),("Default",70,"center")]:
            self.units_tree.heading(col2, text=col2)
            self.units_tree.column(col2, width=w2, anchor=anc2, stretch=(col2=="Presentación"))
        self.units_tree.column("uid", width=0, stretch=False)
        self.units_tree.pack(fill="x", padx=8, pady=6)

        ub = ctk.CTkFrame(tab_pu, fg_color="transparent")
        ub.pack(anchor="w", padx=16, pady=(0,10))
        ctk.CTkButton(ub, text="🗑 Eliminar", height=30, corner_radius=6,
                      fg_color="#2E1A1A", hover_color="#DC2626", text_color="#EF4444",
                      font=("Arial",11), command=self._delete_unit).pack(side="left")
        ctk.CTkButton(ub, text="⭐ Marcar Default", height=30, corner_radius=6,
                      fg_color="#1A2E3A", hover_color="#1E6A9A", text_color=CYAN,
                      font=("Arial",11), command=self._set_default_unit).pack(side="left", padx=(6,0))
        self._units_hint = ctk.CTkLabel(ub,
                     text="   ← Selecciona un producto en la tabla para gestionar sus presentaciones",
                     font=("Arial",10), text_color="#3A3D52")
        self._units_hint.pack(side="left", padx=8)

        # Leyenda
        leg=ctk.CTkFrame(container,fg_color="transparent"); leg.pack(fill="x",padx=20,pady=(0,6))
        for color,lbl in [(ACCENT,"Stock normal"),(WARNING,"Stock bajo"),(DANGER,"Sin stock")]:
            ctk.CTkFrame(leg,width=10,height=10,corner_radius=5,fg_color=color).pack(side="left",padx=(0,4))
            ctk.CTkLabel(leg,text=lbl,font=("Arial",11),text_color=SUBTEXT).pack(side="left",padx=(0,16))

        # Tabla
        tc=ctk.CTkFrame(container,fg_color=CARD,corner_radius=12,
                        border_width=1,border_color=CARD_BORDER)
        tc.pack(fill="both",expand=True,padx=20,pady=(0,20))
        ctk.CTkLabel(tc,text="Lista de Medicamentos",font=("Arial",12,"bold"),
                     text_color=SUBTEXT).pack(anchor="w",padx=16,pady=(14,2))
        ctk.CTkFrame(tc,height=1,fg_color=CARD_BORDER).pack(fill="x",padx=16,pady=(0,8))

        style=ttk.Style(); style.theme_use("clam")
        style.configure("PRD.Treeview",background="#1A1D27",foreground="#FFFFFF",
                        fieldbackground="#1A1D27",borderwidth=0,font=("Arial",11),rowheight=30)
        style.configure("PRD.Treeview.Heading",background="#1E2130",foreground="#8B8FA8",
                        font=("Arial",10,"bold"),borderwidth=0)
        style.map("PRD.Treeview",background=[("selected", "#1A2E22"), ("!selected", "#1A1D27")],foreground=[("selected", "#3DD68C"), ("!selected", "#FFFFFF")])

        cols=("ID","Nombre","Principio Activo","Presentación","Lab.","Cat.","Precio","Costo","Stock","Mín","Modo","Estado")
        self.tree=ttk.Treeview(tc,columns=cols,show="headings",height=14,style="PRD.Treeview")
        try:
            self.tree.configure(style=self.tree["style"])
            self.tree.tk.call("ttk::style", "configure", self.tree["style"], "-fieldbackground", "#1A1D27")
            self.tree.tk.call("ttk::style", "configure", self.tree["style"], "-background", "#1A1D27")
            self.tree.tk.call("ttk::style", "configure", self.tree["style"], "-foreground", "#FFFFFF")
        except Exception:
            pass
        for col,w,anc in [
            ("ID",45,"center"),("Nombre",180,"w"),("Principio Activo",130,"w"),
            ("Presentación",90,"w"),("Lab.",90,"w"),("Cat.",90,"w"),
            ("Precio",90,"e"),("Costo",90,"e"),("Stock",60,"center"),
            ("Mín",60,"center"),("Modo",70,"center"),("Estado",100,"center"),
        ]:
            self.tree.heading(col,text=col); self.tree.column(col,width=w,anchor=anc)

        self.tree.tag_configure("sin_stock",foreground=DANGER)
        self.tree.tag_configure("vencido",  foreground=DANGER)
        self.tree.tag_configure("bajo_stock",foreground=WARNING)
        self.tree.tag_configure("ok_stock", foreground=ACCENT)
        self.tree.pack(fill="both",expand=True,padx=16,pady=(0,8))
        if self.is_admin: self.tree.bind("<<TreeviewSelect>>", lambda e: [self.select_product(e), self._load_units_for_product()])

        # Paginación
        pr=ctk.CTkFrame(tc,fg_color="transparent"); pr.pack(fill="x",padx=16,pady=(0,12))
        self.prev_btn=ctk.CTkButton(pr,text="◀ Anterior",width=110,height=32,corner_radius=8,
                                    fg_color=INPUT_BG,hover_color="#2E3148",text_color=SUBTEXT,
                                    font=("Arial",12),command=self._prev_page)
        self.prev_btn.pack(side="left")
        self.page_lbl=ctk.CTkLabel(pr,text="",font=("Arial",12),text_color=SUBTEXT)
        self.page_lbl.pack(side="left",expand=True)
        self.next_btn=ctk.CTkButton(pr,text="Siguiente ▶",width=110,height=32,corner_radius=8,
                                    fg_color=INPUT_BG,hover_color="#2E3148",text_color=SUBTEXT,
                                    font=("Arial",12),command=self._next_page)
        self.next_btn.pack(side="right")
        self.load_products()
        if self.is_admin:
            self._register_shortcuts()

    def _register_shortcuts(self):
        """Enter guarda (Agregar o Actualizar, según el modo activo);
        Escape limpia el formulario. Así no depende únicamente del mouse."""
        def _submit(event=None):
            if hasattr(self, "btn_actualizar") and self.btn_actualizar.winfo_ismapped():
                self.update_product()
            else:
                self.add_product()
            return "break"

        for entry in (self.name_entry, self.actv_entry, self.lab_entry,
                      self.price_entry, self.cost_entry, self.minstk_entry):
            entry.bind("<Return>", _submit)
            entry.bind("<Escape>", lambda e: self.clear_fields())
    # ─── Gestión de Presentaciones ───────────────────────────────────
    def _load_units_for_product(self):
        for i in self.units_tree.get_children(): self.units_tree.delete(i)
        if not self._selected_id: return
        try:
            conn = create_connection(); cur = conn.cursor()
            cur.execute("""SELECT id,unit_name,factor,price,is_base,is_default
                           FROM product_units WHERE product_id=?
                           ORDER BY factor ASC""", (self._selected_id,))
            cfg = config.load(); cy = cfg["billing"].get("currency","RD$")
            for r in cur.fetchall():
                ps = f"{cy} {float(r[3]):,.2f}" if r[3] is not None else "Auto"
                self.units_tree.insert("","end", values=(
                    r[0], r[1], f"x {r[2]}", ps,
                    "Si" if r[4] else "No",
                    "Si" if r[5] else "No"
                ))
            conn.close()
            self._units_hint.configure(
                text=f"   Presentaciones de: {self.name_entry.get().strip()}")
        except Exception: pass

    def _add_unit(self):
        if not self._selected_id:
            messagebox.showwarning("Sin producto",
                "Selecciona un producto de la tabla primero.")
            return
        name   = self.unit_name_entry.get().strip()
        factor = self.unit_factor_entry.get().strip()
        price  = self.unit_price_entry.get().strip()
        if not name:
            messagebox.showerror("Error","Ingresa el nombre (Ej: Caja)."); return
        try:
            factor = int(factor)
            if factor < 1: raise ValueError
        except ValueError:
            messagebox.showerror("Error","El factor debe ser entero >= 1."); return
        price_val = float(price) if price else None
        try:
            conn = create_connection(); cur = conn.cursor()
            cur.execute("""INSERT INTO product_units
                           (product_id,unit_name,factor,price,is_base,is_default)
                           VALUES (?,?,?,?,0,0)""",
                        (self._selected_id, name, factor, price_val))
            conn.commit(); conn.close()
            self.unit_name_entry.delete(0,"end")
            self.unit_factor_entry.delete(0,"end")
            self.unit_price_entry.delete(0,"end")
            self._load_units_for_product()
        except Exception as e:
            messagebox.showerror("Error",str(e))

    def _delete_unit(self):
        sel = self.units_tree.selection()
        if not sel: messagebox.showwarning("","Selecciona una presentacion."); return
        vals = self.units_tree.item(sel[0],"values")
        uid, name, _, _, is_base, _ = vals
        if is_base == "Si":
            messagebox.showwarning("No permitido","No puedes eliminar la unidad base."); return
        if not messagebox.askyesno("Confirmar",f"Eliminar presentacion '{name}'?"): return
        try:
            conn = create_connection(); cur = conn.cursor()
            cur.execute("DELETE FROM product_units WHERE id=?",(uid,))
            conn.commit(); conn.close()
            self._load_units_for_product()
        except Exception as e:
            messagebox.showerror("Error",str(e))

    def _set_default_unit(self):
        sel = self.units_tree.selection()
        if not sel: messagebox.showwarning("","Selecciona una presentacion."); return
        uid = self.units_tree.item(sel[0],"values")[0]
        try:
            conn = create_connection(); cur = conn.cursor()
            cur.execute("UPDATE product_units SET is_default=0 WHERE product_id=?",
                        (self._selected_id,))
            cur.execute("UPDATE product_units SET is_default=1 WHERE id=?",(uid,))
            conn.commit(); conn.close()
            self._load_units_for_product()
        except Exception as e:
            messagebox.showerror("Error",str(e))

    def _load_units_for_product(self):
        for i in self.units_tree.get_children(): self.units_tree.delete(i)
        if not self._selected_id: return
        try:
            conn=create_connection(); cur=conn.cursor()
            cur.execute("SELECT id,unit_name,factor,price,is_base,is_default FROM product_units WHERE product_id=? ORDER BY factor",(self._selected_id,))
            cfg=config.load(); cy=cfg["billing"].get("currency","RD$")
            for r in cur.fetchall():
                ps=f"{cy} {float(r[3]):,.2f}" if r[3] is not None else "Auto"
                self.units_tree.insert("","end",values=(r[0],r[1],f"x{r[2]}",ps,"Si" if r[4] else "No","Si" if r[5] else "No"))
            conn.close()
            self._units_hint.configure(text=f"  Presentaciones de: {self.name_entry.get().strip()}")
        except Exception: pass

    def _add_unit(self):
        if not self._selected_id:
            messagebox.showwarning("","Selecciona un producto en la tabla primero."); return
        name=self.unit_name_entry.get().strip()
        factor=self.unit_factor_entry.get().strip()
        price=self.unit_price_entry.get().strip()
        if not name: messagebox.showerror("Error","Ingresa el nombre."); return
        try:
            factor=int(factor)
            if factor<1: raise ValueError
        except ValueError:
            messagebox.showerror("Error","Factor debe ser entero >= 1."); return
        price_val=float(price) if price else None
        try:
            conn=create_connection(); cur=conn.cursor()
            cur.execute("INSERT INTO product_units (product_id,unit_name,factor,price,is_base,is_default) VALUES (?,?,?,?,0,0)",(self._selected_id,name,factor,price_val))
            conn.commit(); conn.close()
            self.unit_name_entry.delete(0,"end"); self.unit_factor_entry.delete(0,"end"); self.unit_price_entry.delete(0,"end")
            self._load_units_for_product()
        except Exception as e: messagebox.showerror("Error",str(e))

    def _delete_unit(self):
        sel=self.units_tree.selection()
        if not sel: messagebox.showwarning("","Selecciona una presentacion."); return
        vals=self.units_tree.item(sel[0],"values"); uid,name,_,_,is_base,_=vals
        if is_base=="Si": messagebox.showwarning("","No puedes eliminar la unidad base."); return
        if not messagebox.askyesno("Confirmar",f"Eliminar '{name}'?"): return
        try:
            conn=create_connection(); cur=conn.cursor()
            cur.execute("DELETE FROM product_units WHERE id=?",(uid,))
            conn.commit(); conn.close(); self._load_units_for_product()
        except Exception as e: messagebox.showerror("Error",str(e))

    def _set_default_unit(self):
        sel=self.units_tree.selection()
        if not sel: messagebox.showwarning("","Selecciona una presentacion."); return
        uid=self.units_tree.item(sel[0],"values")[0]
        try:
            conn=create_connection(); cur=conn.cursor()
            cur.execute("UPDATE product_units SET is_default=0 WHERE product_id=?",(self._selected_id,))
            cur.execute("UPDATE product_units SET is_default=1 WHERE id=?",(uid,))
            conn.commit(); conn.close(); self._load_units_for_product()
        except Exception as e: messagebox.showerror("Error",str(e))

    def _lf(self,parent,label,col,span=None,label_out=None):
        f=ctk.CTkFrame(parent,fg_color="transparent")
        kw=dict(row=0,column=col,sticky="ew",pady=(0,8))
        if span: kw["columnspan"]=span; kw["padx"]=(0,0)
        else: kw["padx"]=(0,8)
        f.grid(**kw)
        lbl=ctk.CTkLabel(f,text=label,font=("Arial",11),text_color=SUBTEXT)
        lbl.pack(anchor="w")
        if label_out: setattr(self,label_out,lbl)
        ef=ctk.CTkFrame(f,fg_color=INPUT_BG,corner_radius=8,border_width=1,border_color=INPUT_BORDER)
        ef.pack(fill="x",pady=(3,0))
        e=ctk.CTkEntry(ef,border_width=0,fg_color="transparent",height=38,
                       font=("Arial",13),text_color=TEXT)
        e.pack(fill="x",padx=8); return e

    def _load_suppliers(self):
        conn=create_connection()
        try:
            cur=conn.cursor()
            cur.execute("SELECT id,name FROM suppliers ORDER BY name")
            self._suppliers={r[1]:r[0] for r in cur.fetchall()}
        finally:
            conn.close()
        opts=["Sin proveedor"]+list(self._suppliers.keys())
        self.supplier_menu.configure(values=opts)

    def get_connection(self): return create_connection()

    def _get_status(self,stock,min_stock,expiry=None):
        if stock==0: return "sin_stock","⛔ Sin stock"
        if stock<=min_stock: return "bajo_stock","⚠ Stock bajo"
        return "ok_stock","✔ Normal"

    def after_search(self):
        self._search_q=self.search_entry.get().strip()
        self._page=0; self._render_page()

    # Consulta reutilizada para traer la ficha de un producto. El stock se
    # calcula según el modo del producto (fijado desde el módulo de
    # Lotes): en vivo desde los lotes si los maneja, o el valor directo
    # guardado en products.stock si no. Nunca se edita a mano en Productos.
    # La fecha de vencimiento siempre es un campo propio del producto.
    _PRODUCT_DETAIL_SQL = """
        SELECT p.name, p.active_ingredient, p.presentation, p.laboratory,
               p.category, p.price, p.cost,
               CASE WHEN p.manages_lots=1 THEN
                   COALESCE((SELECT SUM(l.quantity_available) FROM lots l
                             WHERE l.product_id=p.id AND l.status='activo'),0)
               ELSE p.stock END AS stock,
               p.min_stock, p.expiry_date, p.supplier_id, p.applies_itbis
        FROM products p WHERE p.id=?"""

    def _fetch_product_detail(self,pid):
        conn=create_connection(); cur=conn.cursor()
        cur.execute(self._PRODUCT_DETAIL_SQL,(pid,))
        r=cur.fetchone(); conn.close()
        return r

    def _make_readonly(self,entry):
        """Deja el campo con apariencia de campo normal (no gris/disabled).
        Permite escribir dígitos y usar las teclas de edición/navegación,
        pero bloquea letras y símbolos."""
        def _filter(e):
            if e.keysym in ("BackSpace","Delete","Left","Right","Home","End","Tab"):
                return None
            if e.char.isdigit():
                return None
            return "break"
        entry.bind("<Key>", _filter)

    def _set_disabled(self,entry,value):
        """Escribe un valor en un campo informativo (de solo lectura)."""
        entry.delete(0,"end")
        entry.insert(0,str(value if value is not None else ""))

    def _populate_fields_from_row(self,pid,r):
        """Llena el formulario con los datos de un producto.
        r = (name,active_ingredient,presentation,laboratory,category,
             price,cost,stock,min_stock,expiry_date,supplier_id,applies_itbis)
        stock viene calculado según el modo del producto (ver
        _PRODUCT_DETAIL_SQL). La fecha de vencimiento ya no se edita desde
        Productos — se gestiona por lote desde el módulo de Compra.
        Usado tanto al hacer clic en la tabla como al seleccionar
        desde el buscador predictivo, para que ambos caminos se
        comporten igual (ver también Stock Mínimo del producto 123)."""
        self._selected_id=pid
        for e,v in [(self.name_entry,r[0] or ""),(self.actv_entry,r[1] or ""),
                    (self.lab_entry,r[3] or ""),
                    (self.price_entry,str(r[5])),(self.cost_entry,str(r[6])),
                    (self.minstk_entry,str(r[8] if r[8] is not None else 10))]:
            e.delete(0,"end"); e.insert(0,v)
        self._set_disabled(self.stock_entry,r[7])
        self.applies_itbis_var.set(bool(r[11]) if len(r)>11 else True)
        if r[2]: self.pres_var.set(r[2])
        if r[4]: self.category_var.set(r[4])
        if len(r)>10 and hasattr(self,"_suppliers"):
            sup_name=next((n for n,i in self._suppliers.items() if i==r[10]),"Sin proveedor")
            self.supplier_var.set(sup_name)
        # Mostrar Actualizar, ocultar Agregar mientras se edita
        if hasattr(self,"btn_agregar"):
            self.btn_agregar.pack_forget()
            self.btn_actualizar.pack(side="left",padx=(0,8))

    def _on_inv_search_select(self,prod):
        self.clear_fields(keep_id=True)
        r=self._fetch_product_detail(prod["id"])
        if not r: return
        self._populate_fields_from_row(prod["id"],r)

    def _count_products(self,q=""):
        conn=create_connection()
        try:
            cur=conn.cursor()
            if q:
                cur.execute("""SELECT COUNT(*) FROM products
                               WHERE active=1 AND (name LIKE ? OR active_ingredient LIKE ?
                               OR category LIKE ? OR CAST(id AS CHAR) LIKE ?)""",
                            (f"%{q}%",f"%{q}%",f"%{q}%",f"%{q}%"))
            else:
                cur.execute("SELECT COUNT(*) FROM products WHERE active=1")
            return cur.fetchone()[0]
        finally:
            conn.close()

    def _fetch_page(self,q=""):
        off=self._page*self._page_size
        conn=create_connection()
        try:
            cur=conn.cursor()
            base="""SELECT p.id,p.name,p.active_ingredient,p.presentation,
                           p.laboratory,p.category,p.price,p.cost,
                           CASE WHEN p.manages_lots=1 THEN
                               COALESCE((SELECT SUM(l.quantity_available) FROM lots l
                                         WHERE l.product_id=p.id AND l.status='activo'),0)
                           ELSE p.stock END AS stock,
                           p.min_stock,s.name,p.manages_lots
                    FROM products p LEFT JOIN suppliers s ON p.supplier_id=s.id
                    WHERE p.active=1"""
            if q:
                cur.execute(base+""" AND (p.name LIKE ? OR p.active_ingredient LIKE ?
                               OR p.category LIKE ? OR CAST(p.id AS CHAR) LIKE ?)
                               ORDER BY p.name LIMIT ? OFFSET ?""",
                            (f"%{q}%",f"%{q}%",f"%{q}%",f"%{q}%",self._page_size,off))
            else:
                cur.execute(base+" ORDER BY p.name LIMIT ? OFFSET ?",(self._page_size,off))
            return cur.fetchall()
        finally:
            conn.close()

    def load_products(self): self._page=0; self._search_q=""; self._render_page()

    def _render_page(self):
        q=self._search_q; total=self._count_products(q)
        pages=max(1,-(-total//self._page_size)); rows=self._fetch_page(q)
        for i in self.tree.get_children(): self.tree.delete(i)
        cfg=config.load(); cy=cfg["billing"].get("currency","$")
        for p in rows:
            min_s = p[9] if p[9] is not None else 10
            modo = "Lotes" if p[11] else "Directo"
            tag,estado=self._get_status(p[8],min_s,None)
            self.tree.insert("","end",tags=(tag,),
                values=(p[0],p[1],p[2] or "—",p[3] or "—",p[4] or "—",
                        p[5] or "General",f"{cy}{float(p[6] or 0):,.2f}",f"{cy}{float(p[7] or 0):,.2f}",
                        p[8],p[9] or 10,modo,estado))
        if hasattr(self,"page_lbl"):
            self.page_lbl.configure(text=f"Página {self._page+1} de {pages}  ({total} productos)")
            self.prev_btn.configure(state="normal" if self._page>0 else "disabled")
            self.next_btn.configure(state="normal" if self._page<pages-1 else "disabled")

    def _prev_page(self):
        if self._page>0: self._page-=1; self._render_page()
    def _next_page(self):
        pages=max(1,-(-self._count_products(self._search_q)//self._page_size))
        if self._page<pages-1: self._page+=1; self._render_page()

    def select_product(self,event):
        sel=self.tree.selection()
        if not sel: return
        v=self.tree.item(sel[0],"values")
        self.clear_fields(keep_id=True)
        r=self._fetch_product_detail(v[0])
        if not r: return
        self._populate_fields_from_row(v[0],r)

    def _get_form(self):
        name=self.name_entry.get().strip()
        if not name: messagebox.showerror("Error","El nombre es obligatorio."); return None
        try:
            price=float(self.price_entry.get() or 0)
            cost =float(self.cost_entry.get()  or 0)
            minstk=int(self.minstk_entry.get() or 10)
            if price<0 or cost<0: raise ValueError
        except ValueError:
            messagebox.showerror("Error","Precio, costo y stock mínimo deben ser números positivos."); return None
        return dict(name=name,actv=self.actv_entry.get().strip(),
                    pres=self.pres_var.get(),lab=self.lab_entry.get().strip(),
                    cat=self.category_var.get(),price=price,cost=cost,
                    minstk=minstk,
                    applies_itbis=self.applies_itbis_var.get(),
                    sup_id=self._suppliers.get(self.supplier_var.get()))

    def add_product(self):
        d=self._get_form()
        if not d: return
        conn=create_connection(); cur=conn.cursor()
        # Evitar duplicados por nombre: si ya existe un producto activo con
        # el mismo nombre, las compras de "otro" producto igual quedarían
        # separadas en dos fichas distintas y el stock NO se sumaría al
        # vender (ni directo ni por lote). Mejor reutilizar el existente.
        cur.execute("SELECT id FROM products WHERE active=1 AND LOWER(name)=LOWER(?)",
                    (d["name"],))
        dup = cur.fetchone()
        if dup:
            conn.close()
            messagebox.showwarning(
                "Producto ya existe",
                f"Ya existe un producto llamado '{d['name']}' (ID {dup[0]}).\n\n"
                "Para que el stock se sume correctamente, ve a Compras y "
                "agrégale un lote (o compra directa) a ese producto existente "
                "en vez de crear uno nuevo con el mismo nombre."
            )
            return
        # El producto es ficha/catálogo: el stock lo gestiona el módulo de
        # Compra (por lotes o directo), nunca se edita a mano aquí.
        cur.execute("""INSERT INTO products
            (name,active_ingredient,presentation,laboratory,category,
             min_stock,price,cost,supplier_id,applies_itbis)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (d["name"],d["actv"],d["pres"],d["lab"],d["cat"],
             d["minstk"],d["price"],d["cost"],d["sup_id"],
             1 if d["applies_itbis"] else 0))
        pid = cur.lastrowid

        # Crear unidad base automáticamente
        cur.execute("SELECT COUNT(*) FROM product_units WHERE product_id=?",(pid,))
        if cur.fetchone()[0] == 0:
            cur.execute("""INSERT INTO product_units
                           (product_id,unit_name,factor,price,is_base,is_default)
                           VALUES (?,'Unidad',1,NULL,1,1)""",(pid,))
        conn.commit(); conn.close()
        audit("PRODUCTO_AGREGADO", f"#{pid} '{d['name']}' | Precio:${d['price']}", module="inventario")
        messagebox.showinfo("Éxito",f"'{d['name']}' agregado correctamente.\nAgrega un lote (o stock directo) desde el módulo de Compra para registrar existencias.")
        self.clear_fields(); self.load_products()

    def update_product(self):
        if not self._selected_id: messagebox.showerror("Error","Seleccione un producto."); return
        d=self._get_form()
        if not d: return
        conn=create_connection(); cur=conn.cursor()
        cur.execute("SELECT id FROM products WHERE active=1 AND LOWER(name)=LOWER(?) AND id<>?",
                    (d["name"], self._selected_id))
        dup = cur.fetchone()
        if dup:
            conn.close()
            messagebox.showwarning(
                "Producto ya existe",
                f"Ya existe otro producto llamado '{d['name']}' (ID {dup[0]}).\n\n"
                "Usa un nombre distinto, o si son el mismo producto, agrega "
                "la compra desde ese producto existente en vez de duplicarlo."
            )
            return
        # Leer valores anteriores para auditoría (el stock no se toca aquí:
        # lo gestiona el módulo de Compra, no el de Productos)
        cur.execute("SELECT name,price FROM products WHERE id=?", (self._selected_id,))
        old = cur.fetchone()
        cur.execute("""UPDATE products SET name=?,active_ingredient=?,presentation=?,
            laboratory=?,category=?,price=?,cost=?,min_stock=?,
            supplier_id=?,applies_itbis=? WHERE id=?""",
            (d["name"],d["actv"],d["pres"],d["lab"],d["cat"],
             d["price"],d["cost"],d["minstk"],
             d["sup_id"],1 if d["applies_itbis"] else 0,self._selected_id))
        conn.commit()
        if old and old[1] != d["price"]:
            log_price_change(self._selected_id, d["name"], old[1], d["price"])
        conn.close()
        messagebox.showinfo("Éxito","Producto actualizado.")
        self.clear_fields(); self.load_products()

    def delete_product(self):
        sel=self.tree.selection()
        if not sel: messagebox.showwarning("Advertencia","Seleccione un producto."); return
        pid=self.tree.item(sel[0],"values")[0]
        name=self.tree.item(sel[0],"values")[1]

        # No se puede borrar (ni desactivar) un producto con stock vigente:
        # primero hay que retirar sus lotes activos desde el módulo Lotes.
        conn0 = create_connection(); cur0 = conn0.cursor()
        try:
            cur0.execute("""SELECT COALESCE(SUM(quantity_available),0) FROM lots
                             WHERE product_id=? AND status='activo'""", (pid,))
            active_stock = int(cur0.fetchone()[0] or 0)
        finally:
            conn0.close()
        if active_stock > 0:
            messagebox.showwarning(
                "No se puede eliminar",
                f"'{name}' todavía tiene {active_stock} unidades en lotes activos.\n\n"
                "Retira primero sus lotes desde el módulo Lotes y luego "
                "podrás eliminar el producto."
            )
            return

        if not messagebox.askyesno("Confirmar",f"¿Eliminar '{name}'?"): return
        conn=create_connection(); cur=conn.cursor()
        try:
            cur.execute("DELETE FROM products WHERE id=?",(pid,))
            conn.commit()
            hard_deleted = True
        except Exception as e:
            conn.rollback()
            msg = str(e)
            if "foreign key" in msg.lower() or "1451" in msg or "restrict" in msg.lower():
                # Ya no tiene stock activo (los lotes fueron retirados), pero
                # conserva historial de compras: no se puede borrar sin perder
                # ese historial, así que se desactiva (desaparece de las
                # listas/búsquedas, igual que si se hubiera borrado).
                try:
                    cur.execute("UPDATE products SET active=0 WHERE id=?", (pid,))
                    conn.commit()
                    hard_deleted = False
                except Exception as e2:
                    conn.rollback()
                    messagebox.showerror("Error", f"No se pudo eliminar el producto:\n{e2}")
                    return
            elif "1205" in msg or "lock wait timeout" in msg.lower():
                messagebox.showerror(
                    "Base de datos ocupada",
                    "El sistema está tardando en responder porque otra operación "
                    "sigue en curso sobre este producto.\n\n"
                    "Espera unos segundos e inténtalo de nuevo. Si el problema "
                    "persiste, cierra y vuelve a abrir el programa (o reinicia "
                    "MariaDB/XAMPP) para liberar la conexión trabada."
                )
                return
            else:
                messagebox.showerror("Error", f"No se pudo eliminar el producto:\n{msg}")
                return
        finally:
            conn.close()

        if hard_deleted:
            messagebox.showinfo("Éxito","Producto eliminado.")
        else:
            messagebox.showinfo(
                "Producto eliminado",
                f"'{name}' se eliminó de las listas. Como tiene compras "
                "registradas, se conservó ese historial internamente, pero "
                "ya no aparecerá para venderlo ni comprarlo."
            )
        self.clear_fields(); self.load_products()

    def clear_fields(self,keep_id=False):
        if not keep_id: self._selected_id=None
        for e in [self.name_entry,self.actv_entry,self.lab_entry,
                  self.price_entry,self.cost_entry,self.minstk_entry]:
            e.delete(0,"end")
        self._set_disabled(self.stock_entry,"")
        self.applies_itbis_var.set(True)
        self.category_var.set("General"); self.pres_var.set("Tabletas")
        self.supplier_var.set("Sin proveedor")
        # Restaurar botones: mostrar Agregar, ocultar Actualizar
        if hasattr(self,"btn_agregar"):
            self.btn_actualizar.pack_forget()
            self.btn_agregar.pack(side="left",padx=(0,8))

    def export_products(self):
        conn=create_connection()
        try:
            cur=conn.cursor()
            cur.execute("""SELECT p.id,p.name,p.active_ingredient,p.presentation,
                                  p.laboratory,p.category,p.price,p.cost,
                                  CASE WHEN p.manages_lots=1 THEN
                                      COALESCE((SELECT SUM(l.quantity_available) FROM lots l
                                                WHERE l.product_id=p.id AND l.status='activo'),0)
                                  ELSE p.stock END AS stock,
                                  p.min_stock,s.name,p.manages_lots
                           FROM products p LEFT JOIN suppliers s ON p.supplier_id=s.id
                           ORDER BY p.name""")
            raw=cur.fetchall()
        finally:
            conn.close()
        rows=[]
        for r in raw:
            modo="Lotes" if r[11] else "Directo"
            rows.append(r[:11]+(modo,))
        export_to_excel(rows,["ID","Nombre","Principio Activo","Presentación",
                               "Laboratorio","Categoría","Precio","Costo",
                               "Stock","Stock Mín","Proveedor","Modo"],"productos.xlsx")
