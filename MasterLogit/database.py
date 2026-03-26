import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

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
        nombre TEXT NOT NULL UNIQUE,
        descripcion TEXT,
        cantidad INTEGER NOT NULL DEFAULT 0,
        precio REAL NOT NULL,
        estado TEXT DEFAULT 'Activo',
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Tabla clientes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        apellidos TEXT,
        correo TEXT,
        telefono TEXT,
        direccion TEXT,
        dni TEXT UNIQUE,
        estado TEXT DEFAULT 'Activo',
        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Añadir columnas si no existen (versiones previas)
    for col_def in [
        ('apellidos', 'TEXT'),
        ('direccion', 'TEXT'),
        ('dni', 'TEXT'),
    ]:
        col_name, col_type = col_def
        try:
            cursor.execute(f"ALTER TABLE clientes ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass  # ya existe


    # Tabla tecnicos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tecnicos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        especialidad TEXT,
        telefono TEXT,
        estado TEXT DEFAULT 'Activo',
        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Tabla servicios
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS servicios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descripcion TEXT NOT NULL,
        costo REAL NOT NULL,
        id_cliente INTEGER,
        tecnico TEXT,
        especialidad TEXT,
        fecha_solicitud DATE,
        estado TEXT DEFAULT 'Activo',
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(id_cliente) REFERENCES clientes(id)
    )
    """)

    # Añadir columnas extra si existen tablas previas sin ellas
    try:
        cursor.execute("ALTER TABLE servicios ADD COLUMN id_cliente INTEGER")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE servicios ADD COLUMN tecnico TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE servicios ADD COLUMN especialidad TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE servicios ADD COLUMN fecha_solicitud DATE")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE servicios ADD COLUMN estado TEXT DEFAULT 'Activo'")
    except sqlite3.OperationalError:
        pass

    # Tabla repuestos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS repuestos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        descripcion TEXT,
        precio REAL NOT NULL,
        cantidad INTEGER NOT NULL DEFAULT 0,
        id_cliente INTEGER,
        estado TEXT DEFAULT 'Activo',
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(id_cliente) REFERENCES clientes(id)
    )
    """)

    # Añadir columna id_cliente si no existe (versiones previas)
    try:
        cursor.execute("ALTER TABLE repuestos ADD COLUMN id_cliente INTEGER")
    except sqlite3.OperationalError:
        pass  # ya existe
    # Añadir columna cantidad si viene de esquemas antiguos
    try:
        cursor.execute("ALTER TABLE repuestos ADD COLUMN cantidad INTEGER NOT NULL DEFAULT 1")
    except sqlite3.OperationalError:
        pass  # ya existe

    # Tabla relación servicio - repuesto
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS servicio_repuesto (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_servicio INTEGER NOT NULL,
        id_repuesto INTEGER NOT NULL,
        cantidad INTEGER DEFAULT 1,
        FOREIGN KEY(id_servicio) REFERENCES servicios(id),
        FOREIGN KEY(id_repuesto) REFERENCES repuestos(id)
    )
    """)

    # Tabla facturas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS facturas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_cliente INTEGER NOT NULL,
        numero_factura TEXT UNIQUE,
        fecha DATE DEFAULT CURRENT_DATE,
        total REAL NOT NULL,
        estado TEXT DEFAULT 'Pendiente',
        FOREIGN KEY(id_cliente) REFERENCES clientes(id)
    )
    """)

    # Añadir columna descripcion a bases antiguas
    try:
        cursor.execute("ALTER TABLE productos ADD COLUMN descripcion TEXT")
    except sqlite3.OperationalError:
        pass

    # Asegurar columna estado en bases antiguas
    try:
        cursor.execute("ALTER TABLE facturas ADD COLUMN estado TEXT DEFAULT 'Pendiente'")
    except sqlite3.OperationalError:
        pass  # ya existe

    # Tabla detalles de factura
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS factura_detalle (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_factura INTEGER NOT NULL,
        concepto TEXT NOT NULL,
        cantidad REAL,
        precio_unitario REAL,
        subtotal REAL,
        FOREIGN KEY(id_factura) REFERENCES facturas(id)
    )
    """)

    # Tabla usuarios - NUEVA
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        nombre TEXT,
        estado TEXT DEFAULT 'Activo',
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Asegurar relación cliente-producto (columna opcional)
    try:
        cursor.execute("ALTER TABLE productos ADD COLUMN id_cliente INTEGER")
    except sqlite3.OperationalError:
        pass  # columna ya existe

    # Crear índices para búsqueda rápida
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_productos_nombre ON productos(nombre)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clientes_nombre ON clientes(nombre)")
    
    # Crear índice de DNI solo si la columna existe
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_clientes_dni ON clientes(dni)")
    except sqlite3.OperationalError:
        pass  # La columna no existe aún
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_repuestos_nombre ON repuestos(nombre)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tecnicos_nombre ON tecnicos(nombre)")

    conn.commit()
    conn.close()


# ============= FUNCIONES DE BÚSQUEDA =============

def buscar_productos(termino):
    """
    Busca productos por nombre o descripción
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM productos 
        WHERE nombre LIKE ? OR descripcion LIKE ?
        ORDER BY nombre
    """, (f"%{termino}%", f"%{termino}%"))
    resultados = cursor.fetchall()
    conn.close()
    return resultados


def buscar_clientes(termino):
    """
    Busca clientes por nombre, email, teléfono o DNI
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM clientes 
        WHERE nombre LIKE ? OR correo LIKE ? OR telefono LIKE ? OR dni LIKE ?
        ORDER BY nombre
    """, (f"%{termino}%", f"%{termino}%", f"%{termino}%", f"%{termino}%"))
    resultados = cursor.fetchall()
    conn.close()
    return resultados


def buscar_clientes_exacto(nombre=None, correo=None, dni=None):
    """
    Busca clientes con coincidencia exacta en nombre/email/dni.
    Campos vacíos son ignorados.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    condiciones = []
    parametros = []
    
    if nombre:
        condiciones.append("nombre LIKE ?")
        parametros.append(f"%{nombre}%")
    if correo:
        condiciones.append("correo LIKE ?")
        parametros.append(f"%{correo}%")
    if dni:
        condiciones.append("dni = ?")
        parametros.append(dni)
    
    if not condiciones:
        return []

    query = "SELECT * FROM clientes WHERE " + " AND ".join(condiciones) + " ORDER BY nombre"
    cursor.execute(query, tuple(parametros))
    resultados = cursor.fetchall()
    conn.close()
    return resultados


def buscar_repuestos(termino):
    """
    Busca repuestos por nombre o descripción
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM repuestos 
        WHERE nombre LIKE ? OR descripcion LIKE ?
        ORDER BY nombre
    """, (f"%{termino}%", f"%{termino}%"))
    resultados = cursor.fetchall()
    conn.close()
    return resultados


def buscar_tecnicos(termino):
    """
    Busca técnicos por nombre o especialidad
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM tecnicos 
        WHERE nombre LIKE ? OR especialidad LIKE ?
        ORDER BY nombre
    """, (f"%{termino}%", f"%{termino}%"))
    resultados = cursor.fetchall()
    conn.close()
    return resultados


def buscar_global(termino):
    """
    Realiza una búsqueda global en todas las tablas principales
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    resultados = {
        'productos': [],
        'clientes': [],
        'repuestos': [],
        'tecnicos': [],
        'servicios': []
    }
    
    if termino.strip():
        busqueda = f"%{termino}%"
        
        # Buscar en productos
        cursor.execute("""
            SELECT 'producto' as tipo, id, nombre, null as correo, null as precio_unitario, 
                   precio, cantidad, null as especialidad FROM productos 
            WHERE nombre LIKE ? OR descripcion LIKE ?
        """, (busqueda, busqueda))
        resultados['productos'] = cursor.fetchall()
        
        # Buscar en clientes
        cursor.execute("""
            SELECT 'cliente' as tipo, id, nombre, correo, telefono as precio_unitario,
                   null as precio, null as cantidad, null as especialidad FROM clientes 
            WHERE nombre LIKE ? OR correo LIKE ? OR telefono LIKE ? OR dni LIKE ?
        """, (busqueda, busqueda, busqueda, busqueda))
        resultados['clientes'] = cursor.fetchall()
        
        # Buscar en repuestos
        cursor.execute("""
            SELECT 'repuesto' as tipo, id, nombre, null as correo, null as precio_unitario,
                   precio, cantidad, null as especialidad FROM repuestos 
            WHERE nombre LIKE ? OR descripcion LIKE ?
        """, (busqueda, busqueda))
        resultados['repuestos'] = cursor.fetchall()
        
        # Buscar en técnicos
        cursor.execute("""
            SELECT 'tecnico' as tipo, id, nombre, null as correo, null as precio_unitario,
                   null as precio, null as cantidad, especialidad FROM tecnicos 
            WHERE nombre LIKE ? OR especialidad LIKE ?
        """, (busqueda, busqueda))
        resultados['tecnicos'] = cursor.fetchall()
        
        # Buscar en servicios
        cursor.execute("""
            SELECT 'servicio' as tipo, id, descripcion as nombre, null as correo, null as precio_unitario,
                   costo as precio, null as cantidad, null as especialidad FROM servicios 
            WHERE descripcion LIKE ?
        """, (busqueda,))
        resultados['servicios'] = cursor.fetchall()
    
    conn.close()
    return resultados


# ============= FUNCIONES DE AUTENTICACIÓN =============

def crear_usuario(usuario, email, password, nombre=None):
    """
    Crea un nuevo usuario con contraseña cifrada
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Hashear la contraseña
        password_hash = generate_password_hash(password)
        
        cursor.execute("""
            INSERT INTO usuarios(usuario, email, password, nombre)
            VALUES (?, ?, ?, ?)
        """, (usuario, email, password_hash, nombre))
        
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False  # Usuario o email ya existe


def verificar_usuario(usuario_email, password):
    """
    Verifica las credenciales del usuario (usuario o email + contraseña)
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Buscar por usuario o email
        cursor.execute("""
            SELECT id, usuario, email, password, nombre FROM usuarios 
            WHERE usuario = ? OR email = ?
        """, (usuario_email, usuario_email))
        
        usuario = cursor.fetchone()
        conn.close()
        
        if usuario and check_password_hash(usuario['password'], password):
            return {
                'id': usuario['id'],
                'usuario': usuario['usuario'],
                'email': usuario['email'],
                'nombre': usuario['nombre']
            }
        return None
    except Exception as e:
        print(f"Error al verificar usuario: {e}")
        return None


def obtener_usuario(usuario_id):
    """
    Obtiene la información del usuario por ID
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, usuario, email, nombre FROM usuarios 
            WHERE id = ?
        """, (usuario_id,))
        
        usuario = cursor.fetchone()
        conn.close()
        return usuario
    except Exception as e:
        print(f"Error al obtener usuario: {e}")
        return None
