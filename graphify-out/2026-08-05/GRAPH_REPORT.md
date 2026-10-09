# Graph Report - 3.0 - copia  (2026-08-05)

## Corpus Check
- 79 files · ~79,770 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1095 nodes · 2431 edges · 54 communities (45 shown, 9 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 87 edges (avg confidence: 0.62)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- FEFO Stock Logic
- Customer/Supplier Field Widgets
- MySQL Backup & Restore
- Lots UI (Inventory)
- Lots UI (Inventory, duplicate copy)
- Login & Password Recovery
- Invoices UI (Cart & Generation)
- Dashboard Navigation
- Dashboard Navigation (duplicate copy)
- Invoices UI (Cart & Generation, duplicate copy)
- Date Field Widget
- Cash Register Closure & Export
- Cash Register Closure & Export (duplicate copy)
- Inventory Overview & Exports
- Invoice PEPS Cost Sync
- Compatibility DB Connection Wrapper
- Customers UI (CRUD)
- Live Search Widget
- Customers UI (CRUD, duplicate copy)
- Date Picker Widget
- Date Picker Widget (duplicate copy)
- Suppliers UI Validation
- Inventory UI Tabs & Adjustments
- Predictive Search Widget
- Reports UI (Financial & Alerts)
- Inventory UI Tabs & Adjustments (duplicate copy)
- Predictive Search Widget (duplicate copy)
- Reports UI (Financial & Alerts, duplicate copy)
- Reports UI (Lots & Movements Export)
- Audit Logger
- Sales History UI
- MySQL Connection Pool & Cash Register
- Sales History UI Export
- App Configuration (config.json)
- Users UI (CRUD)
- Graphify Docs & Sample Invoice
- App Configuration (config.json, duplicate copy)
- Phone/Address Validators
- Receipt Generator (Thermal Print)
- Splash Screen
- Excel Exporter
- CLAUDE.md
- productos_b1b01680.md
- ventas_por_fecha_85250860.md
- ventas_por_fecha_be880d31.md
- SalesHistoryUI
- invoice_generator.py
- historial_ventas_2026-08-05_5baffc16.md

## God Nodes (most connected - your core abstractions)
1. `create_connection()` - 164 edges
2. `Dashboard` - 53 edges
3. `Dashboard` - 46 edges
4. `export_to_excel()` - 39 edges
5. `LiveSearch` - 38 edges
6. `PurchasesUI` - 36 edges
7. `LotsUI` - 35 edges
8. `ProductsUI` - 35 edges
9. `InvoicesUI` - 34 edges
10. `InvoicesUI` - 32 edges

## Surprising Connections (you probably didn't know these)
- `Graphify Knowledge Graph` --semantically_similar_to--> `Graphify Knowledge Graph`  [INFERRED] [semantically similar]
  CLAUDE.md → database/CLAUDE.md
- `Query-First Workflow Rationale (root)` --semantically_similar_to--> `Query-First Workflow Rationale (database)`  [INFERRED] [semantically similar]
  CLAUDE.md → database/CLAUDE.md
- `LoginWindow` --uses--> `Dashboard`  [INFERRED]
  auth/login_window.py → database/ui/dashboard.py
- `Dashboard` --uses--> `CashRegisterUI`  [INFERRED]
  ui/dashboard.py → database/ui/cash_register_ui.py
- `Dashboard` --uses--> `CustomersUI`  [INFERRED]
  ui/dashboard.py → database/ui/customers_ui.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Invoice Generation Flow (FarmaFactura Pro Factura #7)** — database_factura_7_farmafacturapro, database_factura_7_factura_no_7, database_factura_7_cliente_reterytr, database_factura_7_producto_medicamento_de_prueba [INFERRED 0.75]

## Communities (54 total, 9 thin omitted)

### Community 0 - "FEFO Stock Logic"
Cohesion: 0.06
Nodes (21): create_connection(), descontar_stock_fefo(), get_proxima_vencimiento(), get_stock_total(), Revierte una salida FEFO (por cancelación de venta, por ejemplo).     Si se da l, Retorna el stock total disponible de un producto sumando todos sus lotes activos, Retorna la fecha de vencimiento más próxima entre los lotes activos de un produc, Descuenta 'cantidad' unidades del producto usando FEFO:     el lote que vence an (+13 more)

### Community 1 - "Customer/Supplier Field Widgets"
Cohesion: 0.05
Nodes (26): CustomersUI, Enter guarda (Agregar o Actualizar, según el modo activo);         Escape limpia, Campo con etiqueta arriba del input., Limita el campo de teléfono a un máximo de 10 caracteres., Retorna sugerencias para el LiveSearch., Al seleccionar sugerencia, busca ese cliente., LiveSearch, live_search.py — Barra de búsqueda con sugerencias en tiempo real. Reutilizable (+18 more)

### Community 2 - "MySQL Backup & Restore"
Cohesion: 0.08
Nodes (13): create_backup(), _load_config(), database/backup.py — Backup MariaDB via mysqldump. Para MariaDB en XAMPP, el bac, Intenta hacer backup con mysqldump (incluido en XAMPP).     Retorna (ruta_absolu, Restaurar backup MariaDB desde archivo .sql, restore_backup(), Valida el teléfono al salir del campo y muestra ayuda visual., Valida número de teléfono de República Dominicana.     Formatos aceptados: (+5 more)

### Community 3 - "Lots UI (Inventory)"
Cohesion: 0.12
Nodes (6): LotsUI, Campo solo lectura (para número de lote auto), Popup de calendario — pone la fecha elegida en entry_widget., Valida formato YYYY-MM-DD y que el vencimiento no sea anterior         a la fech, Abre popup para editar todos los campos de un lote seleccionado., _tree_style()

### Community 4 - "Lots UI (Inventory, duplicate copy)"
Cohesion: 0.08
Nodes (14): LotsUI, Abre popup para editar todos los campos de un lote seleccionado., Campo solo lectura (para número de lote auto), Popup de calendario — pone la fecha elegida en entry_widget., Valida formato YYYY-MM-DD y que el vencimiento no sea anterior         a la fech, Campo de fecha con botón 📅 que abre el calendario popup., Recalcula products.cost como el costo promedio ponderado de los lotes     activo, Agrega el producto actual a la lista de la factura. (+6 more)

### Community 5 - "Login & Password Recovery"
Cohesion: 0.07
Nodes (15): LoginWindow, RecoverPasswordWindow, RegisterWindow, hash_password(), verify_password(), main(), _run_splash(), create_tables() (+7 more)

### Community 6 - "Invoices UI (Cart & Generation)"
Cohesion: 0.09
Nodes (13): _deduct_lots_peps(), InvoicesUI, Recalcula products.cost como el costo promedio ponderado de los lotes     activo, Registra atajos de teclado en la ventana raíz., Sugiere clientes registrados al escribir en el campo cliente., Como _total_row pero retorna también el label de la clave para actualizarlo., Descuenta qty_needed UNIDADES BASE usando PEPS.     - Si chosen_lot_id está defi, Carga lotes disponibles ordenados por PEPS. (+5 more)

### Community 7 - "Dashboard Navigation"
Cohesion: 0.14
Nodes (3): Dashboard, _get_ui(), Cerrar sesión — main.py sobreescribe este método con confirmación.

### Community 8 - "Dashboard Navigation (duplicate copy)"
Cohesion: 0.14
Nodes (3): Dashboard, _get_ui(), Cerrar sesión — main.py sobreescribe este método con confirmación.

### Community 9 - "Invoices UI (Cart & Generation, duplicate copy)"
Cohesion: 0.10
Nodes (9): InvoicesUI, Registra atajos de teclado en la ventana raíz., Sugiere clientes registrados al escribir en el campo cliente., Como _total_row pero retorna también el label de la clave para actualizarlo., Stock realmente disponible para vender: excluye lotes vencidos., Carga lotes disponibles ordenados por PEPS. Excluye lotes vencidos:         un p, Actualiza stock disponible al cambiar de lote., Popup con información completa del lote seleccionado. (+1 more)

### Community 10 - "Date Field Widget"
Cohesion: 0.10
Nodes (11): DateField, ui/date_field.py — Campo de fecha reutilizable con calendario popup. Uso:     fr, Widget de fecha con entry + botón 📅 que abre un calendario popup.     Compatible, Compatibilidad con CTkEntry., Compatibilidad con CTkEntry., _fmt_date(), _fmt_time(), Convierte fecha MySQL (datetime/date obj o string) a YYYY-MM-DD. (+3 more)

### Community 11 - "Cash Register Closure & Export"
Cohesion: 0.13
Nodes (8): CashRegisterUI, _fmt_time(), date, Consulta la BD y redibuja el reporte., Tarjeta de resumen para el cierre de caja., Extrae HH:MM de fecha MySQL (datetime obj o string)., Botones de exportación al final del reporte., Genera el PDF y lo envía directamente al diálogo de impresión.

### Community 12 - "Cash Register Closure & Export (duplicate copy)"
Cohesion: 0.17
Nodes (8): Enter guarda (Agregar o Actualizar, según el modo activo);         Escape limpia, Campo con etiqueta arriba del input., Limita el campo de teléfono a un máximo de 10 caracteres., Sugerencias predictivas por nombre, teléfono o email., Al seleccionar sugerencia, filtra la tabla., Filtra la tabla según el texto en el buscador., Valida que el correo contenga @ y un dominio., SuppliersUI

### Community 13 - "Inventory Overview & Exports"
Cohesion: 0.16
Nodes (17): ui/inventory_ui.py — Inventario General (visión gerencial y control). Responsabi, ui/inventory_ui.py — Inventario General (visión gerencial y control). Responsabi, audit(), _get_user(), log_login(), log_price_change(), log_sale(), log_stock_change() (+9 more)

### Community 14 - "Invoice PEPS Cost Sync"
Cohesion: 0.13
Nodes (8): CashRegisterUI, _fmt_time(), date, Consulta la BD y redibuja el reporte., Tarjeta de resumen para el cierre de caja., Extrae HH:MM de fecha MariaDB (datetime obj o string)., Botones de exportación al final del reporte., Genera el PDF y lo envía directamente al diálogo de impresión.

### Community 15 - "Compatibility DB Connection Wrapper"
Cohesion: 0.12
Nodes (4): _CompatConnection, _CompatCursor, _convert_query(), test_connection()

### Community 16 - "Customers UI (CRUD)"
Cohesion: 0.20
Nodes (6): _fmt_date(), _fmt_time(), Convierte fecha MariaDB (datetime/date obj o string) a YYYY-MM-DD., Sugiere todos los usuarios registrados en el sistema., Extrae HH:MM de fecha MariaDB (datetime obj o string)., SalesHistoryUI

### Community 17 - "Live Search Widget"
Cohesion: 0.16
Nodes (5): LiveSearch, live_search.py — Barra de búsqueda con sugerencias en tiempo real. Reutilizable, Solo oculta si no estamos en proceso de selección., Enter: selecciona el item activo o el primero si ninguno está activo., Selecciona un valor y cierra el popup sin reabrirlo.

### Community 18 - "Customers UI (CRUD, duplicate copy)"
Cohesion: 0.14
Nodes (7): _currency_symbol(), _find_currency_option(), Fuerza el refresco visual de la ventana raíz., Valida el teléfono al salir del campo y muestra ayuda visual., Valida número de teléfono de República Dominicana.     Formatos aceptados:, SettingsUI, _validate_rd_phone()

### Community 19 - "Date Picker Widget"
Cohesion: 0.14
Nodes (7): DatePickerWidget, date_picker.py — Widget de selección de fecha para customtkinter. Muestra un bot, Compatibilidad con la interfaz CTkEntry., Cierra el popup si el foco sale completamente de él., Verifica después de un breve delay si el popup debe cerrarse., Frame que contiene un botón con la fecha seleccionada.     Al hacer clic abre un, Compatibilidad con la interfaz CTkEntry.

### Community 20 - "Date Picker Widget (duplicate copy)"
Cohesion: 0.14
Nodes (7): DatePickerWidget, date_picker.py — Widget de selección de fecha para customtkinter. Muestra un bot, Compatibilidad con la interfaz CTkEntry., Cierra el popup si el foco sale completamente de él., Verifica después de un breve delay si el popup debe cerrarse., Frame que contiene un botón con la fecha seleccionada.     Al hacer clic abre un, Compatibilidad con la interfaz CTkEntry.

### Community 21 - "Suppliers UI Validation"
Cohesion: 0.12
Nodes (7): get_purchase_detail(), Retorna (header, lines):       header: (id, purchase_date, supplier_id, supplier, PurchasesUI, Carga una compra ya guardada en la pestaña Registrar para editarla., Lee y valida los campos del formulario de línea. Retorna dict o None         (mo, Muestra 'Editar Producto' solo mientras haya una fila seleccionada con clic., error_message()

### Community 22 - "Inventory UI Tabs & Adjustments"
Cohesion: 0.16
Nodes (3): _fmt_date(), InventoryUI, _tree_style()

### Community 24 - "Reports UI (Financial & Alerts)"
Cohesion: 0.19
Nodes (5): _fmt_date(), Campo de fecha con calendario popup., Mantenido por compatibilidad — DateField lo maneja internamente., Convierte fecha MySQL (datetime/date obj o string) a YYYY-MM-DD., ReportsUI

### Community 26 - "Inventory UI Tabs & Adjustments (duplicate copy)"
Cohesion: 0.16
Nodes (3): _fmt_date(), InventoryUI, _tree_style()

### Community 28 - "Reports UI (Financial & Alerts, duplicate copy)"
Cohesion: 0.19
Nodes (5): _fmt_date(), Campo de fecha con calendario popup., Mantenido por compatibilidad — DateField lo maneja internamente., Convierte fecha MariaDB (datetime/date obj o string) a YYYY-MM-DD., ReportsUI

### Community 29 - "Reports UI (Lots & Movements Export)"
Cohesion: 0.11
Nodes (20): config.py — Gestión centralizada de configuración del sistema. Lee y escribe en, Guarda la configuración en config.json., save(), _fmt_date(), cash_register_ui.py  —  Cuadre Diario de Caja Reporte de cierre de jornada con i, Convierte fecha MySQL (datetime/date obj o string) a YYYY-MM-DD., _fmt_time(), Extrae HH:MM de fecha MySQL (datetime obj o string). (+12 more)

### Community 30 - "Audit Logger"
Cohesion: 0.14
Nodes (19): audit(), _ensure_audit_table(), _get_user(), log_login(), log_price_change(), log_sale(), log_stock_change(), log_user_action() (+11 more)

### Community 31 - "Sales History UI"
Cohesion: 0.13
Nodes (17): get(), load(), Carga la configuración. Si no existe el archivo, devuelve los valores por defect, Atajo para leer un valor específico., Recalcula products.cost como el costo promedio ponderado de los lotes     activo, sync_product_cost(), _invoice_already_registered(), database/purchases.py — Lógica de negocio del módulo de Compras. Registra encabe (+9 more)

### Community 32 - "MySQL Connection Pool & Cash Register"
Cohesion: 0.22
Nodes (11): generate_invoice_pdf(), generate_receipt(), _hr(), receipt_generator.py Genera comprobantes de venta en formato térmico (80mm) y ca, Estilos de párrafo del comprobante., Genera el comprobante de venta en PDF.      Parámetros:         invoice_id     :, _styles(), predictive_search.py Widget de búsqueda predictiva para productos farmacéuticos. (+3 more)

### Community 33 - "Sales History UI Export"
Cohesion: 0.26
Nodes (4): DateField, Widget de fecha con entry + botón 📅 que abre un calendario popup.     Compatible, Compatibilidad con CTkEntry., Compatibilidad con CTkEntry.

### Community 34 - "App Configuration (config.json)"
Cohesion: 0.16
Nodes (6): CustomersUI, Enter guarda (Agregar o Actualizar, según el modo activo);         Escape limpia, Campo con etiqueta arriba del input., Limita el campo de teléfono a un máximo de 10 caracteres., Retorna sugerencias para el LiveSearch., Al seleccionar sugerencia, busca ese cliente.

### Community 36 - "Graphify Docs & Sample Invoice"
Cohesion: 0.29
Nodes (8): Graphify Knowledge Graph, Query-First Workflow Rationale (root), Graphify Knowledge Graph, Query-First Workflow Rationale (database), Cliente: reterytr, Factura N° 7 (Invoice #7, 09/07/2026), FarmaFactura Pro, Producto: Medicamento de prueba

### Community 37 - "App Configuration (config.json, duplicate copy)"
Cohesion: 0.29
Nodes (7): get(), load(), config.py — Gestión centralizada de configuración del sistema. Lee y escribe en, Carga la configuración. Si no existe el archivo, devuelve los valores por defect, Guarda la configuración en config.json., Atajo para leer un valor específico., save()

### Community 38 - "Phone/Address Validators"
Cohesion: 0.29
Nodes (7): clean_phone_digits(), utils/validators.py — Validaciones reutilizables de teléfono y dirección.  Pensa, Devuelve solo los dígitos del teléfono, sin el 1 de código de país si aplica., Valida un teléfono dominicano.     Retorna (ok: bool, mensaje_error: str | None), Valida una dirección. Retorna (ok: bool, mensaje_error: str | None).     Por def, validate_address(), validate_phone()

### Community 39 - "Receipt Generator (Thermal Print)"
Cohesion: 0.38
Nodes (6): generate_receipt(), _hr(), receipt_generator.py Genera comprobantes de venta en formato térmico (80mm) y ca, Estilos de párrafo del comprobante., Genera el comprobante de venta en PDF.      Parámetros:         invoice_id     :, _styles()

### Community 41 - "Excel Exporter"
Cohesion: 0.50
Nodes (4): export_to_excel(), _open_file(), Abre el archivo con la aplicación predeterminada del sistema., Genera un archivo Excel con los datos proporcionados,     lo guarda y lo abre au

### Community 52 - "SalesHistoryUI"
Cohesion: 0.25
Nodes (5): _create_pool(), _load_db_config(), database/connection.py — Conexión a MariaDB (XAMPP) Pool aumentado a 20 conexion, database/fefo.py — Lógica FEFO (First Expired, First Out) para FarmaFactura Pro., predictive_search.py Widget de búsqueda predictiva para productos farmacéuticos.

### Community 53 - "invoice_generator.py"
Cohesion: 0.38
Nodes (6): _cashier_from_session(), generate_invoice_txt(), _lookup_customer(), reports/invoice_generator.py — Factura de venta en texto plano (.txt), formato p, Busca teléfono/dirección del cliente por nombre exacto. Solo lectura;     si no, Genera la factura de venta en formato de texto plano (.txt).      Firma original

## Knowledge Gaps
- **8 isolated node(s):** `graphify`, `graphify`, `Sheet: Sheet`, `Sheet: Sheet`, `Sheet: Sheet1` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `create_connection()` connect `FEFO Stock Logic` to `Customer/Supplier Field Widgets`, `MySQL Backup & Restore`, `Lots UI (Inventory)`, `Lots UI (Inventory, duplicate copy)`, `Login & Password Recovery`, `Invoices UI (Cart & Generation)`, `Dashboard Navigation`, `Dashboard Navigation (duplicate copy)`, `Invoices UI (Cart & Generation, duplicate copy)`, `Date Field Widget`, `Cash Register Closure & Export`, `Cash Register Closure & Export (duplicate copy)`, `Inventory Overview & Exports`, `Invoice PEPS Cost Sync`, `Compatibility DB Connection Wrapper`, `Customers UI (CRUD)`, `Suppliers UI Validation`, `Inventory UI Tabs & Adjustments`, `Predictive Search Widget`, `Reports UI (Financial & Alerts)`, `Inventory UI Tabs & Adjustments (duplicate copy)`, `Predictive Search Widget (duplicate copy)`, `Reports UI (Financial & Alerts, duplicate copy)`, `Reports UI (Lots & Movements Export)`, `Audit Logger`, `Sales History UI`, `MySQL Connection Pool & Cash Register`, `App Configuration (config.json)`, `SalesHistoryUI`, `invoice_generator.py`?**
  _High betweenness centrality (0.305) - this node is a cross-community bridge._
- **Why does `Dashboard` connect `Dashboard Navigation (duplicate copy)` to `FEFO Stock Logic`, `MySQL Backup & Restore`, `App Configuration (config.json)`, `Lots UI (Inventory, duplicate copy)`, `Login & Password Recovery`, `Invoices UI (Cart & Generation)`, `Date Field Widget`, `Cash Register Closure & Export`, `Cash Register Closure & Export (duplicate copy)`, `Customers UI (CRUD, duplicate copy)`, `Suppliers UI Validation`, `Inventory UI Tabs & Adjustments`, `Reports UI (Financial & Alerts)`?**
  _High betweenness centrality (0.162) - this node is a cross-community bridge._
- **Why does `Dashboard` connect `Dashboard Navigation` to `FEFO Stock Logic`, `MySQL Backup & Restore`, `App Configuration (config.json)`, `Lots UI (Inventory, duplicate copy)`, `Login & Password Recovery`, `Invoices UI (Cart & Generation)`, `Date Field Widget`, `Cash Register Closure & Export`, `Cash Register Closure & Export (duplicate copy)`, `Customers UI (CRUD, duplicate copy)`, `Inventory UI Tabs & Adjustments`, `Reports UI (Financial & Alerts)`?**
  _High betweenness centrality (0.139) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `Dashboard` (e.g. with `CashRegisterUI` and `CustomersUI`) actually correct?**
  _`Dashboard` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `Dashboard` (e.g. with `LoginWindow` and `CashRegisterUI`) actually correct?**
  _`Dashboard` has 12 INFERRED edges - model-reasoned connections that need verification._
- **What connects `graphify`, `graphify`, `Sheet: Sheet` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `FEFO Stock Logic` be split into smaller, more focused modules?**
  _Cohesion score 0.05727605727605728 - nodes in this community are weakly interconnected._