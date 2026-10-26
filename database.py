import sqlite3

DB_NAME = "sistema_pos.db"

def conectar_db():
    return sqlite3.connect(DB_NAME)

def inicializar_db():
    conn = conectar_db()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS Usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        rol TEXT NOT NULL,
        estado TEXT DEFAULT 'ACTIVO')""")

    c.execute("""CREATE TABLE IF NOT EXISTS Clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        documento TEXT UNIQUE NOT NULL,
        nombre TEXT NOT NULL,
        telefono TEXT,
        direccion TEXT,
        tipo TEXT DEFAULT 'REGULAR')""")

    c.execute("""CREATE TABLE IF NOT EXISTS Productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_barras TEXT UNIQUE NOT NULL,
        nombre TEXT NOT NULL,
        categoria TEXT,
        unidad_medida TEXT,
        costo_usd REAL NOT NULL DEFAULT 0,
        precio_venta_usd REAL NOT NULL,
        precio_mayor_usd REAL,
        stock_actual REAL NOT NULL DEFAULT 0,
        imagen_path TEXT)""")

    c.execute("""CREATE TABLE IF NOT EXISTS Ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
        cliente_id INTEGER,
        usuario_id INTEGER,
        caja_sesion_id INTEGER DEFAULT 0,
        total_usd REAL NOT NULL,
        total_bs REAL NOT NULL,
        tasa_aplicada REAL NOT NULL,
        metodo_pago TEXT,
        estado TEXT DEFAULT 'COMPLETADA',
        FOREIGN KEY(cliente_id) REFERENCES Clientes(id),
        FOREIGN KEY(usuario_id) REFERENCES Usuarios(id))""")

    c.execute("""CREATE TABLE IF NOT EXISTS Detalle_Ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venta_id INTEGER,
        producto_id INTEGER,
        cantidad REAL NOT NULL,
        precio_unitario_usd REAL NOT NULL,
        costo_unitario_usd REAL NOT NULL DEFAULT 0,
        subtotal_usd REAL NOT NULL,
        FOREIGN KEY(venta_id) REFERENCES Ventas(id),
        FOREIGN KEY(producto_id) REFERENCES Productos(id))""")

    c.execute("""CREATE TABLE IF NOT EXISTS Movimientos_Stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        producto_id INTEGER,
        tipo_movimiento TEXT NOT NULL,
        cantidad REAL NOT NULL,
        fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
        referencia TEXT,
        FOREIGN KEY(producto_id) REFERENCES Productos(id))""")

    c.execute("""CREATE TABLE IF NOT EXISTS Configuracion (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        empresa_nombre TEXT DEFAULT 'MAXI POS',
        empresa_rif TEXT DEFAULT 'J-0000000-0',
        empresa_direccion TEXT DEFAULT 'Ciudad Guayana, Bolívar',
        tasa_manual REAL DEFAULT 1.0,
        usar_tasa_manual INTEGER DEFAULT 0)""")

    c.execute("""CREATE TABLE IF NOT EXISTS Proveedores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rif TEXT,
        nombre TEXT NOT NULL,
        telefono TEXT,
        empresa TEXT)""")

    c.execute("""CREATE TABLE IF NOT EXISTS Cuentas_Pagar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        proveedor_id INTEGER,
        descripcion TEXT,
        monto_total_usd REAL NOT NULL,
        abonado_usd REAL DEFAULT 0,
        fecha_emision DATE,
        fecha_vencimiento DATE,
        imagen_path TEXT,
        estado TEXT DEFAULT 'PENDIENTE',
        FOREIGN KEY(proveedor_id) REFERENCES Proveedores(id))""")

    c.execute("""CREATE TABLE IF NOT EXISTS Cortes_Z (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha_corte DATETIME,
        total_ventas INTEGER,
        total_usd REAL,
        total_bs REAL,
        ganancia_usd REAL,
        tasa_bcv REAL,
        desglose_pagos TEXT)""")

    # Migraciones automáticas sin afectar datos existentes
    for col_sql in [
        "ALTER TABLE Configuracion ADD COLUMN telegram_token TEXT DEFAULT ''",
        "ALTER TABLE Configuracion ADD COLUMN telegram_chat_id TEXT DEFAULT ''",
        "ALTER TABLE Configuracion ADD COLUMN mostrar_datos_fiscales INTEGER DEFAULT 1"
    ]:
        try:
            c.execute(col_sql)
        except Exception:
            pass

    c.execute("UPDATE Ventas SET caja_sesion_id = 0 WHERE caja_sesion_id IS NULL")

    c.execute("SELECT COUNT(*) FROM Usuarios")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO Usuarios (usuario, password, rol, estado) VALUES ('admin', 'admin123', 'Administrador', 'ACTIVO')")

    c.execute("SELECT COUNT(*) FROM Clientes")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO Clientes (documento, nombre, telefono, direccion, tipo) VALUES ('V-00000000', 'CONSUMIDOR FINAL', '', '', 'REGULAR')")

    c.execute("SELECT COUNT(*) FROM Configuracion")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO Configuracion (id, empresa_nombre, empresa_rif, empresa_direccion, tasa_manual, usar_tasa_manual) VALUES (1, 'MAXI POS', 'J-0000000-0', 'Ciudad Guayana, Bolívar', 1.0, 0)")

    conn.commit()
    conn.close()

inicializar_db()