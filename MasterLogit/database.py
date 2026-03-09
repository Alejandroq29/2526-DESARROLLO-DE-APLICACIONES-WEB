import sqlite3

DATABASE = "masterlogic.db"

def get_connection():
    """
    Crea y retorna una conexión a la base de datos SQLite
    """
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Crea las tablas necesarias para el sistema MasterLogic
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Tabla productos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        cantidad INTEGER NOT NULL,
        precio REAL NOT NULL
    )
    """)

    # Tabla clientes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        correo TEXT,
        telefono TEXT
    )
    """)

    # Tabla tecnicos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tecnicos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        especialidad TEXT
    )
    """)

    # Tabla servicios
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS servicios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descripcion TEXT NOT NULL,
        costo REAL NOT NULL
    )
    """)

    # Tabla repuestos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS repuestos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        precio REAL NOT NULL
    )
    """)

    # Tabla relación servicio - repuesto
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS servicio_repuesto (
        id_servicio INTEGER,
        id_repuesto INTEGER,
        FOREIGN KEY(id_servicio) REFERENCES servicios(id),
        FOREIGN KEY(id_repuesto) REFERENCES repuestos(id)
    )
    """)

    # Tabla facturas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS facturas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_cliente INTEGER,
        fecha TEXT,
        total REAL,
        FOREIGN KEY(id_cliente) REFERENCES clientes(id)
    )
    """)

    conn.commit()
    conn.close()