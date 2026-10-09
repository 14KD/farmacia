# Graph Report - 3.0 - copia  (2026-08-05)

## Corpus Check
- 78 files · ~79,760 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1096 nodes · 2435 edges · 54 communities (46 shown, 8 thin omitted)
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
- create_connection
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

## Communities (54 total, 8 thin omitted)

### Community 0 - "FEFO Stock Logic"
Cohesion: 0.12
Nodes (5): ProductsUI, Enter guarda (Agregar o Actualizar, según el modo activo);         Escape limpia, Deja el campo con apariencia de campo normal (no gris/disabled).         Permite, Escribe un valor en un campo informativo (de solo lectura)., Llena el formulario con los datos de un producto.         r = (name,active_ingre

### Community 1 - "Customer/Supplier Field Widgets"
Cohesion: 0.05
Nodes (28): Enter guarda (Agregar o Actualizar, según el modo activo);         Escape limpia, Campo con etiqueta arriba del input., Limita el campo de teléfono a un máximo de 10 caracteres., Sugerencias predictivas por nombre, teléfono o email., Al seleccionar sugerencia, filtra la tabla., Filtra la tabla según el texto en el buscador., Valida que el correo contenga @ y un dominio., SuppliersUI (+20 more)

### Community 2 - "MySQL Backup & Restore"
Cohesion: 0.19
Nodes (4): Valida el teléfono al salir del campo y muestra ayuda visual., Valida número de teléfono de República Dominicana.     Formatos aceptados:, SettingsUI, _validate_rd_phone()

### Community 3 - "Lots UI (Inventory)"
Cohesion: 0.14
Nodes (6): LotsUI, Campo solo lectura (para número de lote auto), Popup de calendario — pone la fecha elegida en entry_widget., Valida formato YYYY-MM-DD y que el vencimiento no sea anterior         a la fech, Abre popup para editar todos los campos de un lote seleccionado., _tree_style()

### Community 4 - "Lots UI (Inventory, duplicate copy)"
Cohesion: 0.08
Nodes (14): LotsUI, Abre popup para editar todos los campos de un lote seleccionado., Campo solo lectura (para número de lote auto), Popup de calendario — pone la fecha elegida en entry_widget., Valida formato YYYY-MM-DD y que el vencimiento no sea anterior         a la fech, Campo de fecha con botón 📅 que abre el calendario popup., Recalcula products.cost como el costo promedio ponderado de los lotes     activo, Agrega el producto actual a la lista de la factura. (+6 more)

### Community 5 - "Login & Password Recovery"
Cohesion: 0.06
Nodes (15): LoginWindow, RegisterWindow, hash_password(), verify_password(), main(), _run_splash(), create_tables(), database/schema.py — Inicialización de tablas MariaDB + Triggers FEFO. Versión a (+7 more)

### Community 6 - "Invoices UI (Cart & Generation)"
Cohesion: 0.09
Nodes (13): _deduct_lots_peps(), InvoicesUI, Recalcula products.cost como el costo promedio ponderado de los lotes     activo, Registra atajos de teclado en la ventana raíz., Sugiere clientes registrados al escribir en el campo cliente., Como _total_row pero retorna también el label de la clave para actualizarlo., Descuenta qty_needed UNIDADES BASE usando PEPS.     - Si chosen_lot_id está defi, Carga lotes disponibles ordenados por PEPS. (+5 more)

### Community 7 - "Dashboard Navigation"
Cohesion: 0.09
Nodes (9): create_backup(), _load_config(), database/backup.py — Backup MariaDB via mysqldump. Para MariaDB en XAMPP, el bac, Intenta hacer backup con mysqldump (incluido en XAMPP).     Retorna (ruta_absolu, Restaurar backup MariaDB desde archivo .sql, restore_backup(), Dashboard, _get_ui() (+1 more)

### Community 8 - "Dashboard Navigation (duplicate copy)"
Cohesion: 0.14
Nodes (3): Dashboard, _get_ui(), Cerrar sesión — main.py sobreescribe este método con confirmación.

### Community 9 - "Invoices UI (Cart & Generation, duplicate copy)"
Cohesion: 0.10
Nodes (9): InvoicesUI, Registra atajos de teclado en la ventana raíz., Sugiere clientes registrados al escribir en el campo cliente., Como _total_row pero retorna también el label de la clave para actualizarlo., Stock realmente disponible para vender: excluye lotes vencidos., Carga lotes disponibles ordenados por PEPS. Excluye lotes vencidos:         un p, Actualiza stock disponible al cambiar de lote., Popup con información completa del lote seleccionado. (+1 more)

### Community 10 - "Date Field Widget"
Cohesion: 0.10
Nodes (11): DateField, ui/date_field.py — Campo de fecha reutilizable con calendario popup. Uso:     fr, Widget de fecha con entry + botón 📅 que abre un calendario popup.     Compatible, Compatibilidad con CTkEntry., Compatibilidad con CTkEntry., _fmt_date(), _fmt_time(), Convierte fecha MariaDB (datetime/date obj o string) a YYYY-MM-DD. (+3 more)

### Community 11 - "Cash Register Closure & Export"
Cohesion: 0.13
Nodes (8): CashRegisterUI, _fmt_time(), date, Consulta la BD y redibuja el reporte., Tarjeta de resumen para el cierre de caja., Extrae HH:MM de fecha MySQL (datetime obj o string)., Botones de exportación al final del reporte., Genera el PDF y lo envía directamente al diálogo de impresión.

### Community 12 - "Cash Register Closure & Export (duplicate copy)"
Cohesion: 0.14
Nodes (4): ProductsUI, Enter guarda (Agregar o Actualizar, según el modo activo);         Escape limpia, Escribe el valor de stock en el campo informativo, sin importar         que esté, Llena el formulario con los datos de un producto.         r = (name,active_ingre

### Community 13 - "Inventory Overview & Exports"
Cohesion: 0.15
Nodes (20): generate_invoice_pdf(), predictive_search.py Widget de búsqueda predictiva para productos farmacéuticos., ui/purchases_ui.py — Módulo de Compras. Encabezado + detalle editable, con cálcu, audit(), _get_user(), log_price_change(), log_sale(), log_stock_change() (+12 more)

### Community 14 - "Invoice PEPS Cost Sync"
Cohesion: 0.13
Nodes (8): CashRegisterUI, _fmt_time(), date, Consulta la BD y redibuja el reporte., Tarjeta de resumen para el cierre de caja., Extrae HH:MM de fecha MariaDB (datetime obj o string)., Botones de exportación al final del reporte., Genera el PDF y lo envía directamente al diálogo de impresión.

### Community 15 - "Compatibility DB Connection Wrapper"
Cohesion: 0.12
Nodes (4): _CompatConnection, _CompatCursor, _convert_query(), test_connection()

### Community 16 - "Customers UI (CRUD)"
Cohesion: 0.16
Nodes (6): CustomersUI, Enter guarda (Agregar o Actualizar, según el modo activo);         Escape limpia, Campo con etiqueta arriba del input., Limita el campo de teléfono a un máximo de 10 caracteres., Retorna sugerencias para el LiveSearch., Al seleccionar sugerencia, busca ese cliente.

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
Nodes (7): get_purchase_detail(), Retorna (header, lines):       header: (id, purchase_date, supplier_id, supplie, PurchasesUI, Carga una compra ya guardada en la pestaña Registrar para editarla., Lee y valida los campos del formulario de línea. Retorna dict o None         (mo, Muestra 'Editar Producto' solo mientras haya una fila seleccionada con clic., error_message()

### Community 22 - "Inventory UI Tabs & Adjustments"
Cohesion: 0.20
Nodes (3): _fmt_date(), InventoryUI, _tree_style()

### Community 24 - "Reports UI (Financial & Alerts)"
Cohesion: 0.19
Nodes (5): _fmt_date(), Campo de fecha con calendario popup., Mantenido por compatibilidad — DateField lo maneja internamente., Convierte fecha MySQL (datetime/date obj o string) a YYYY-MM-DD., ReportsUI

### Community 25 - "create_connection"
Cohesion: 0.15
Nodes (11): RecoverPasswordWindow, create_connection(), get_proxima_vencimiento(), Retorna la fecha de vencimiento más próxima entre los lotes activos de un produc, Busca compras registradas con filtros opcionales. Retorna filas:     (id, purch, search_purchases(), get_user_by_username(), _ensure_audit_table() (+3 more)

### Community 26 - "Inventory UI Tabs & Adjustments (duplicate copy)"
Cohesion: 0.20
Nodes (3): _fmt_date(), InventoryUI, _tree_style()

### Community 28 - "Reports UI (Financial & Alerts, duplicate copy)"
Cohesion: 0.19
Nodes (5): _fmt_date(), Campo de fecha con calendario popup., Mantenido por compatibilidad — DateField lo maneja internamente., Convierte fecha MariaDB (datetime/date obj o string) a YYYY-MM-DD., ReportsUI

### Community 29 - "Reports UI (Lots & Movements Export)"
Cohesion: 0.09
Nodes (22): config.py — Gestión centralizada de configuración del sistema. Lee y escribe en, Guarda la configuración en config.json., save(), _create_pool(), _load_db_config(), database/connection.py — Conexión a MariaDB (XAMPP) Pool aumentado a 20 conexion, _fmt_date(), cash_register_ui.py  —  Cuadre Diario de Caja Reporte de cierre de jornada con i (+14 more)

### Community 30 - "Audit Logger"
Cohesion: 0.14
Nodes (19): audit(), _ensure_audit_table(), _get_user(), log_login(), log_price_change(), log_sale(), log_stock_change(), log_user_action() (+11 more)

### Community 31 - "Sales History UI"
Cohesion: 0.09
Nodes (25): get(), load(), Carga la configuración. Si no existe el archivo, devuelve los valores por defect, Atajo para leer un valor específico., descontar_stock_fefo(), get_stock_total(), database/fefo.py — Lógica FEFO (First Expired, First Out) para FarmaFactura Pro., Recalcula products.cost como el costo promedio ponderado de los lotes     activo (+17 more)

### Community 32 - "MySQL Connection Pool & Cash Register"
Cohesion: 0.38
Nodes (6): generate_receipt(), _hr(), receipt_generator.py Genera comprobantes de venta en formato térmico (80mm) y ca, Estilos de párrafo del comprobante., Genera el comprobante de venta en PDF.      Parámetros:         invoice_id     :, _styles()

### Community 33 - "Sales History UI Export"
Cohesion: 0.11
Nodes (11): _fmt_date(), _fmt_time(), sales_history_ui.py — Historial y auditoría de ventas. Busca y filtra facturas e, Convierte fecha MySQL (datetime/date obj o string) a YYYY-MM-DD., Sugiere todos los usuarios registrados en el sistema., Extrae HH:MM de fecha MySQL (datetime obj o string)., SalesHistoryUI, DateField (+3 more)

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
Cohesion: 0.13
Nodes (3): ui/inventory_ui.py — Inventario General (visión gerencial y control). Responsabi, export_to_excel(), Genera un archivo Excel con los datos proporcionados,     lo guarda y lo abre au

### Community 53 - "invoice_generator.py"
Cohesion: 0.38
Nodes (6): _cashier_from_session(), generate_invoice_txt(), _lookup_customer(), reports/invoice_generator.py — Factura de venta en texto plano (.txt), formato p, Busca teléfono/dirección del cliente por nombre exacto. Solo lectura;     si no, Genera la factura de venta en formato de texto plano (.txt).      Firma original

## Knowledge Gaps
- **7 isolated node(s):** `graphify`, `graphify`, `Sheet: Sheet`, `Sheet: Sheet1`, `Sheet: Sheet1` (+2 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `create_connection()` connect `create_connection` to `FEFO Stock Logic`, `Customer/Supplier Field Widgets`, `Lots UI (Inventory)`, `Lots UI (Inventory, duplicate copy)`, `Login & Password Recovery`, `Invoices UI (Cart & Generation)`, `Dashboard Navigation`, `Dashboard Navigation (duplicate copy)`, `Invoices UI (Cart & Generation, duplicate copy)`, `Date Field Widget`, `Cash Register Closure & Export`, `Cash Register Closure & Export (duplicate copy)`, `Inventory Overview & Exports`, `Invoice PEPS Cost Sync`, `Compatibility DB Connection Wrapper`, `Customers UI (CRUD)`, `Suppliers UI Validation`, `Inventory UI Tabs & Adjustments`, `Predictive Search Widget`, `Reports UI (Financial & Alerts)`, `Inventory UI Tabs & Adjustments (duplicate copy)`, `Predictive Search Widget (duplicate copy)`, `Reports UI (Financial & Alerts, duplicate copy)`, `Reports UI (Lots & Movements Export)`, `Audit Logger`, `Sales History UI`, `Sales History UI Export`, `App Configuration (config.json)`, `SalesHistoryUI`, `invoice_generator.py`?**
  _High betweenness centrality (0.289) - this node is a cross-community bridge._
- **Why does `Dashboard` connect `Dashboard Navigation (duplicate copy)` to `Sales History UI Export`, `App Configuration (config.json)`, `Customer/Supplier Field Widgets`, `Lots UI (Inventory, duplicate copy)`, `Login & Password Recovery`, `Invoices UI (Cart & Generation)`, `Dashboard Navigation`, `Cash Register Closure & Export`, `Cash Register Closure & Export (duplicate copy)`, `Customers UI (CRUD, duplicate copy)`, `Suppliers UI Validation`, `Inventory UI Tabs & Adjustments`, `Reports UI (Financial & Alerts)`, `create_connection`?**
  _High betweenness centrality (0.173) - this node is a cross-community bridge._
- **Why does `Dashboard` connect `Dashboard Navigation` to `Sales History UI Export`, `App Configuration (config.json)`, `Customer/Supplier Field Widgets`, `Lots UI (Inventory, duplicate copy)`, `Login & Password Recovery`, `Invoices UI (Cart & Generation)`, `Cash Register Closure & Export`, `Cash Register Closure & Export (duplicate copy)`, `Customers UI (CRUD, duplicate copy)`, `Inventory UI Tabs & Adjustments`, `Reports UI (Financial & Alerts)`?**
  _High betweenness centrality (0.136) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `Dashboard` (e.g. with `CashRegisterUI` and `CustomersUI`) actually correct?**
  _`Dashboard` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `Dashboard` (e.g. with `LoginWindow` and `CashRegisterUI`) actually correct?**
  _`Dashboard` has 12 INFERRED edges - model-reasoned connections that need verification._
- **What connects `graphify`, `graphify`, `Sheet: Sheet` to the rest of the system?**
  _7 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `FEFO Stock Logic` be split into smaller, more focused modules?**
  _Cohesion score 0.12299465240641712 - nodes in this community are weakly interconnected._