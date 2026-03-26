from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response, abort, flash
import sqlite3
from pathlib import Path
from database import init_db, get_connection, buscar_productos, buscar_clientes, crear_usuario, verificar_usuario, buscar_clientes_exacto
import json
import csv
from io import StringIO
from datetime import date
from functools import wraps
from conexion.conexion import conectar, desconectar



app = Flask(__name__)
app.config['SECRET_KEY'] = 'tu-clave-secreta-aqui'  # Cambiar a una clave segura en producción
init_db()

# Decorador para proteger rutas que requieren login
def login_requerido(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

PUBLIC_ENDPOINTS = {
    "login",
    "registro",
    "about",
    "contacto",
    "index",
    "static",
}


@app.before_request
def exigir_login():
    """Redirige a login si el usuario no ha iniciado sesión y entra a rutas protegidas."""
    endpoint = request.endpoint or ""
    if "usuario_id" not in session and endpoint not in PUBLIC_ENDPOINTS:
        return redirect(url_for("login"))

DATA_DIR = Path(__file__).parent / "Inventario" / "data"
TXT_FILE = DATA_DIR / "datos.txt"
JSON_FILE = DATA_DIR / "datos.json"
CSV_FILE = DATA_DIR / "datos.csv"


def _save_product_to_files(nombre, cantidad, precio):
    """Guardar un producto en TXT, JSON y CSV."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        # TXT
        with open(TXT_FILE, "a", encoding="utf-8") as f:
            f.write(f"{nombre},{cantidad},{precio}\n")

        # JSON
        data = {"nombre": nombre, "cantidad": cantidad, "precio": precio}

        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                lista = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            lista = []

        lista.append(data)

        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(lista, f, indent=4, ensure_ascii=False)

        # CSV
        with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([nombre, cantidad, precio])
    except Exception as e:
        print(f"Error al guardar en archivos: {e}")


def _insert_producto_db(nombre, cantidad, precio, id_cliente=None, id_producto=None):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        if id_producto:
            cursor.execute(
                "INSERT OR REPLACE INTO productos(id, nombre, cantidad, precio, id_cliente) VALUES (?, ?, ?, ?, ?)",
                (id_producto, nombre, cantidad, precio, id_cliente),
            )
        else:
            cursor.execute(
                "INSERT INTO productos(nombre, cantidad, precio, id_cliente) VALUES (?, ?, ?, ?)",
                (nombre, cantidad, precio, id_cliente),
            )

        conn.commit()
    except Exception as e:
        print(f"Error al insertar producto: {e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Página de login"""
    if request.method == "POST":
        usuario_email = request.form.get("usuario_email", "").strip()
        password = request.form.get("password", "").strip()
        
        if usuario_email and password:
            usuario = verificar_usuario(usuario_email, password)
            if usuario:
                session['usuario_id'] = usuario['id']
                session['usuario'] = usuario['usuario']
                session['email'] = usuario['email']
                session['nombre'] = usuario['nombre']
                return redirect(url_for('index'))
            else:
                return render_template("login.html", error="Usuario o contraseña incorrectos")
    
    return render_template("login.html")


@app.route("/logout")
def logout():
    """Cierra la sesión"""
    session.clear()
    return redirect(url_for("login"))


@app.route("/registro", methods=["GET", "POST"])
def registro():
    """Página de registro de nuevos usuarios"""
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        confirmar_password = request.form.get("confirmar_password", "").strip()
        nombre = request.form.get("nombre", "").strip()
        
        # Validaciones
        if not all([usuario, email, password, confirmar_password]):
            return render_template("registro.html", error="Todos los campos son requeridos")
        
        if password != confirmar_password:
            return render_template("registro.html", error="Las contraseñas no coinciden")
        
        if len(password) < 6:
            return render_template("registro.html", error="La contraseña debe tener al menos 6 caracteres")
        
        if crear_usuario(usuario, email, password, nombre):
            return redirect(url_for("login"))
        else:
            return render_template("registro.html", error="El usuario o email ya existe")
    
    return render_template("registro.html")

@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contacto", methods=["GET", "POST"])
def contacto():
    """Formulario de contacto simple que guarda envíos en un archivo."""
    success = False

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip()
        mensaje = request.form.get("mensaje", "").strip()

        if nombre and email and mensaje:
            with open("contactos.txt", "a", encoding="utf-8") as f:
                f.write(f"{nombre}|{email}|{mensaje}\n")
            success = True

    # Mostrar mensajes guardados
    mensajes = []
    try:
        with open("contactos.txt", "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) == 3:
                    mensajes.append({
                        "nombre": parts[0],
                        "email": parts[1],
                        "mensaje": parts[2],
                    })
    except FileNotFoundError:
        pass

    return render_template("contactos.html", success=success, mensajes=mensajes)


# ---------------- CLIENTES ----------------

@app.route("/clientes")
def clientes():
    q = request.args.get("q", "").strip()
    page = int(request.args.get("page", 1))
    per_page = 20

    conn = get_connection()
    cursor = conn.cursor()

    if q:
        cursor.execute(
            "SELECT * FROM clientes WHERE nombre LIKE ? OR apellidos LIKE ? OR correo LIKE ? OR telefono LIKE ? OR direccion LIKE ? OR dni LIKE ? ORDER BY nombre",
            (f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%")
        )
    else:
        cursor.execute("SELECT * FROM clientes ORDER BY nombre")

    todos_clientes = [dict(row) for row in cursor.fetchall()]
    conn.close()

    total_clientes = len(todos_clientes)
    start = (page - 1) * per_page
    end = start + per_page
    clientes = todos_clientes[start:end]

    return render_template(
        "cliente.html",
        clientes=clientes,
        q=q,
        page=page,
        per_page=per_page,
        total_clientes=total_clientes
    )


@app.route("/cliente/nuevo", methods=["GET","POST"])
def cliente_form():

    if request.method == "POST":

        nombre = request.form.get("nombre", "").strip()
        apellidos = request.form.get("apellidos", "").strip()
        correo = request.form.get("correo", "").strip()
        telefono = request.form.get("telefono", "").strip()
        direccion = request.form.get("direccion", "").strip()
        dni = request.form.get("dni", "").strip()

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO clientes(nombre,apellidos,correo,telefono,direccion,dni) VALUES (?,?,?,?,?,?)",
            (nombre, apellidos, correo, telefono, direccion, dni)
        )

        conn.commit()
        conn.close()

        return redirect(url_for("clientes"))

    return render_template("cliente_forms.html", cliente=None)


@app.route("/cliente/editar/<int:id>", methods=["GET", "POST"])
def cliente_editar(id):
    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        apellidos = request.form.get("apellidos", "").strip()
        correo = request.form.get("correo", "").strip()
        telefono = request.form.get("telefono", "").strip()
        direccion = request.form.get("direccion", "").strip()
        dni = request.form.get("dni", "").strip()

        cursor.execute(
            "UPDATE clientes SET nombre = ?, apellidos = ?, correo = ?, telefono = ?, direccion = ?, dni = ? WHERE id = ?",
            (nombre, apellidos, correo, telefono, direccion, dni, id)
        )
        conn.commit()
        conn.close()

        return redirect(url_for("clientes"))

    cursor.execute("SELECT * FROM clientes WHERE id = ?", (id,))
    cliente_row = cursor.fetchone()
    cliente = dict(cliente_row) if cliente_row else None
    conn.close()

    if not cliente:
        return redirect(url_for("clientes"))

    return render_template("cliente_editar.html", cliente=cliente)


@app.route("/cliente/eliminar/<int:id>")
def cliente_eliminar(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM clientes WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("clientes"))


@app.route("/register_client", methods=["GET","POST"])
def register_client():

    if request.method == "POST":

        nombre = request.form["nombre"].strip()
        apellidos = request.form.get("apellidos", "").strip()
        correo = request.form["correo"].strip()
        telefono = request.form["telefono"].strip()
        direccion = request.form.get("direccion", "").strip()
        dni = request.form.get("dni", "").strip()

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO clientes(nombre,apellidos,correo,telefono,direccion,dni) VALUES (?,?,?,?,?,?)",
            (nombre, apellidos, correo, telefono, direccion, dni)
        )

        conn.commit()
        conn.close()

        return redirect(url_for("clientes"))

    return render_template("register_client.html")


# ---------------- PRODUCTOS ----------------

@app.route("/productos")
def productos():

    q = request.args.get("q", "").strip()
    page = int(request.args.get("page", 1))
    per_page = 20

    conn = get_connection()
    cursor = conn.cursor()

    if q:
        cursor.execute(
            "SELECT p.*, c.nombre AS cliente_nombre FROM productos p LEFT JOIN clientes c ON p.id_cliente = c.id WHERE p.nombre LIKE ? OR COALESCE(p.descripcion,'') LIKE ? ORDER BY p.nombre",
            (f"%{q}%", f"%{q}%")
        )
    else:
        cursor.execute("SELECT p.*, c.nombre AS cliente_nombre FROM productos p LEFT JOIN clientes c ON p.id_cliente = c.id ORDER BY p.nombre")

    todos_productos = cursor.fetchall()
    conn.close()

    total_productos = len(todos_productos)
    start = (page - 1) * per_page
    end = start + per_page
    productos = todos_productos[start:end]

    return render_template(
        "producto.html",
        productos=productos,
        q=q,
        page=page,
        per_page=per_page,
        total_productos=total_productos
    )


@app.route("/producto/editar/<int:id>", methods=["GET", "POST"])
def producto_editar(id):
    conn = get_connection()
    cursor = conn.cursor()

    # lista de clientes para selector
    cursor.execute("SELECT id, nombre FROM clientes ORDER BY nombre")
    clientes = [dict(row) for row in cursor.fetchall()]

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        cantidad = request.form.get("cantidad", "").strip() or "0"
        precio = request.form.get("precio", "").strip() or "0"
        id_cliente = request.form.get("id_cliente")

        cursor.execute("SELECT id FROM productos WHERE id = ?", (id,))
        if cursor.fetchone():
            cursor.execute(
                "UPDATE productos SET nombre = ?, cantidad = ?, precio = ?, id_cliente = ? WHERE id = ?",
                (nombre, cantidad, precio, id_cliente if id_cliente else None, id)
            )
            conn.commit()
            flash("Producto actualizado", "success")
        conn.close()
        return redirect(url_for("productos"))

    cursor.execute("SELECT * FROM productos WHERE id = ?", (id,))
    producto_row = cursor.fetchone()
    producto = dict(producto_row) if producto_row else None
    conn.close()

    if not producto:
        return redirect(url_for("productos"))

    return render_template("producto_forms.html", producto=producto, clientes=clientes)


@app.route("/producto/eliminar/<int:id>", methods=["POST"])
def producto_eliminar(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM productos WHERE id = ?", (id,))
    if cursor.fetchone():
        cursor.execute("DELETE FROM productos WHERE id = ?", (id,))
        conn.commit()
        flash("Producto eliminado", "info")
    conn.close()
    return redirect(url_for("productos"))


@app.route("/producto/nuevo", methods=["GET","POST"])
def producto_form():

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre FROM clientes ORDER BY nombre")
    clientes = cursor.fetchall()
    conn.close()

    error = None

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        cantidad = request.form.get("cantidad", "0").strip() or "0"
        precio = request.form.get("precio", "0").strip() or "0"
        id_cliente = request.form.get("id_cliente")

        if nombre:
            try:
                cantidad_int = int(float(cantidad))
                precio_float = float(precio)
            except ValueError:
                error = "Cantidad y precio deben ser números."
            else:
                try:
                    _save_product_to_files(nombre, cantidad_int, precio_float)
                    _insert_producto_db(nombre, cantidad_int, precio_float, id_cliente=id_cliente)
                    flash("Producto agregado exitosamente", "success")
                    return redirect(url_for("productos"))
                except sqlite3.IntegrityError:
                    error = "Ya existe un producto con ese nombre."
                except Exception as e:
                    print(f"Error al agregar producto: {e}")
                    error = "No se pudo guardar el producto."

    return render_template("producto_forms.html", clientes=clientes, error=error, producto=None)


# ---------------- SERVICIOS ----------------

@app.route("/servicios", methods=["GET", "POST"])
def servicios():
    """Listado y creación de servicios con cliente que lo solicita."""
    conn = get_connection()
    cursor = conn.cursor()

    # clientes disponibles para asignar solicitud
    cols = [c[1] for c in cursor.execute("PRAGMA table_info(clientes)").fetchall()]
    select_cols = [c for c in ['id', 'nombre', 'apellidos', 'correo', 'telefono', 'direccion', 'dni'] if c in cols]
    select_str = ', '.join(select_cols)
    if not select_str:
        select_str = 'id, nombre'
    clientes = cursor.execute(f"SELECT {select_str} FROM clientes ORDER BY nombre").fetchall()

    # campos de cliente en SELECT para servicios/repuestos
    c_aliases = {
        'nombre': 'cliente_nombre',
        'apellidos': 'cliente_apellidos',
        'correo': 'cliente_correo',
        'telefono': 'cliente_telefono',
        'direccion': 'cliente_direccion',
        'dni': 'cliente_dni'
    }
    cliente_selects = []
    for c in ['nombre', 'apellidos', 'correo', 'telefono', 'direccion', 'dni']:
        if c in cols:
            cliente_selects.append(f"c.{c} AS {c_aliases[c]}")
    cliente_select_clause = ', '.join(cliente_selects) if cliente_selects else "'' AS cliente_nombre"

    if request.method == "POST":
        descripcion = request.form.get("descripcion", "").strip()
        costo = request.form.get("costo", "0").strip() or "0"
        id_cliente = request.form.get("id_cliente")
        tecnico = request.form.get("tecnico", "").strip()
        especialidad = request.form.get("especialidad", "").strip()
        fecha_solicitud = request.form.get("fecha_solicitud", "")
        estado = request.form.get("estado", "Activo").strip()

        if descripcion:
            cursor.execute(
                "INSERT INTO servicios(descripcion, costo, id_cliente, tecnico, especialidad, fecha_solicitud, estado) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (descripcion, costo, id_cliente if id_cliente else None, tecnico, especialidad, fecha_solicitud or None, estado),
            )
            conn.commit()
            return redirect(url_for("servicios"))

    # consultar servicios con los campos de cliente:
    base_servicios_select = (
        "SELECT s.id, s.descripcion, s.costo, s.id_cliente, s.tecnico, s.especialidad, s.fecha_solicitud, s.estado, "
        f"{cliente_select_clause} "
        "FROM servicios s "
        "LEFT JOIN clientes c ON s.id_cliente = c.id "
        "ORDER BY s.id"
    )
    servicios_list = cursor.execute(base_servicios_select).fetchall()
    conn.close()

    return render_template("service_request.html", servicios=servicios_list, clientes=clientes)


# ---------------- REPUESTOS ----------------

@app.route("/repuestos", methods=["GET", "POST"])
def repuestos():
    """Listado y creación de repuestos."""

    conn = get_connection()
    cursor = conn.cursor()
    cols = [c[1] for c in cursor.execute("PRAGMA table_info(clientes)").fetchall()]
    select_cols = [c for c in ['id', 'nombre', 'apellidos', 'correo', 'telefono', 'direccion', 'dni'] if c in cols]
    select_str = ', '.join(select_cols)
    if not select_str:
        select_str = 'id, nombre'
    clientes = cursor.execute(f"SELECT {select_str} FROM clientes ORDER BY nombre").fetchall()

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        precio = request.form.get("precio", "0").strip() or "0"
        cantidad = request.form.get("cantidad", "1").strip() or "1"
        id_cliente = request.form.get("id_cliente")

        if nombre:
            try:
                cursor.execute(
                    "INSERT INTO repuestos(nombre, precio, cantidad, id_cliente) VALUES (?, ?, ?, ?)",
                    (nombre, precio, cantidad, id_cliente if id_cliente else None),
                )
                conn.commit()
            except Exception as e:
                print(f"Error al agregar repuesto: {e}")
            return redirect(url_for("repuestos"))

    try:
        cursor.execute(
            "SELECT r.id, r.nombre, r.precio, r.id_cliente, c.nombre AS cliente_nombre, c.apellidos AS cliente_apellidos, c.dni AS cliente_dni, c.correo AS cliente_correo, c.direccion AS cliente_direccion "
            "FROM repuestos r "
            "LEFT JOIN clientes c ON r.id_cliente = c.id "
            "ORDER BY r.id"
        )
        repuestos_list = cursor.fetchall()
        conn.close()
    except Exception as e:
        print(f"Error al listar repuestos: {e}")
        repuestos_list = []

    return render_template("repuestos.html", repuestos=repuestos_list, clientes=clientes)


# ---------------- FACTURAS ----------------

@app.route("/facturas", methods=["GET", "POST"])
def facturas():
    """Listado y creación de facturas."""
    if request.method == "POST":
        id_cliente = request.form.get("id_cliente")
        fecha = request.form.get("fecha") or date.today().isoformat()

        # Calcular subtotal automático con todos los registros del cliente
        subtotal = 0
        if id_cliente:
            try:
                conn_calc = get_connection()
                cur_calc = conn_calc.cursor()
                prod_total = cur_calc.execute(
                    "SELECT COALESCE(SUM(cantidad * precio),0) FROM productos WHERE id_cliente = ?",
                    (id_cliente,),
                ).fetchone()[0] or 0
                rep_total = cur_calc.execute(
                    "SELECT COALESCE(SUM(cantidad * precio),0) FROM repuestos WHERE id_cliente = ?",
                    (id_cliente,),
                ).fetchone()[0] or 0
                serv_total = cur_calc.execute(
                    "SELECT COALESCE(SUM(costo),0) FROM servicios WHERE id_cliente = ?",
                    (id_cliente,),
                ).fetchone()[0] or 0
                subtotal = float(prod_total) + float(rep_total) + float(serv_total)
            finally:
                conn_calc.close()

        if id_cliente:
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO facturas(id_cliente, fecha, total) VALUES (?, ?, ?)",
                    (id_cliente, fecha, subtotal),
                )
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"Error al crear factura: {e}")
            return redirect(url_for("facturas"))

    try:
        conn = get_connection()
        cursor = conn.cursor()
        clientes_rows = cursor.execute("SELECT id, nombre FROM clientes ORDER BY nombre").fetchall()
        clientes = [dict(r) for r in clientes_rows]

        cursor.execute(
            "SELECT f.id, f.id_cliente, f.estado, c.nombre AS cliente, f.fecha, f.total "
            "FROM facturas f "
            "LEFT JOIN clientes c ON f.id_cliente = c.id"
        )
        facturas_rows = cursor.fetchall()
        facturas_list = [dict(r) for r in facturas_rows]
        conn.close()
    except Exception as e:
        print(f"Error al listar facturas: {e}")
        clientes = []
        facturas_list = []

    return render_template("facturas.html", facturas=facturas_list, clientes=clientes)


def _obtener_historial_cliente(cliente_id):
    """Devuelve cliente + listas vinculadas de productos, servicios y facturas."""
    conn = get_connection()
    cursor = conn.cursor()
    cliente_row = cursor.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,)).fetchone()
    productos_rows = cursor.execute("SELECT * FROM productos WHERE id_cliente = ?", (cliente_id,)).fetchall()
    servicios_rows = cursor.execute("SELECT * FROM servicios WHERE id_cliente = ?", (cliente_id,)).fetchall()
    repuestos_rows = cursor.execute("SELECT * FROM repuestos WHERE id_cliente = ?", (cliente_id,)).fetchall()
    facturas_rows = cursor.execute(
        "SELECT id, fecha, total, estado FROM facturas WHERE id_cliente = ? ORDER BY fecha DESC",
        (cliente_id,),
    ).fetchall()

    # Subtotal de todas las partidas del cliente
    prod_total = cursor.execute(
        "SELECT COALESCE(SUM(cantidad * precio),0) FROM productos WHERE id_cliente = ?",
        (cliente_id,),
    ).fetchone()[0] or 0
    rep_total = cursor.execute(
        "SELECT COALESCE(SUM(cantidad * precio),0) FROM repuestos WHERE id_cliente = ?",
        (cliente_id,),
    ).fetchone()[0] or 0
    serv_total = cursor.execute(
        "SELECT COALESCE(SUM(costo),0) FROM servicios WHERE id_cliente = ?",
        (cliente_id,),
    ).fetchone()[0] or 0
    subtotal = float(prod_total) + float(rep_total) + float(serv_total)
    conn.close()
    cliente = dict(cliente_row) if cliente_row else None
    productos = [dict(r) for r in productos_rows]
    servicios = [dict(r) for r in servicios_rows]
    repuestos = [dict(r) for r in repuestos_rows]
    facturas = [dict(r) for r in facturas_rows]
    return cliente, productos, servicios, repuestos, facturas, subtotal


@app.route("/clientes/<int:cliente_id>/historial")
def cliente_historial(cliente_id):
    """Vista consolidada para imprimir historial del cliente."""
    cliente, productos, servicios, repuestos, facturas, subtotal = _obtener_historial_cliente(cliente_id)
    if not cliente:
        abort(404)
    return render_template(
        "historial_cliente.html",
        cliente=cliente,
        productos=productos,
        servicios=servicios,
        repuestos=repuestos,
        facturas=facturas,
        subtotal=subtotal,
    )


@app.route("/buscar", methods=["GET"])
@login_requerido
def buscar_producto():
    """Busca en productos y clientes solamente."""
    termino = request.args.get("q", "").strip()
    cliente_nombre = request.args.get("cliente_nombre", "").strip()
    cliente_correo = request.args.get("cliente_correo", "").strip()
    cliente_dni = request.args.get("cliente_dni", "").strip()
    page_p = int(request.args.get("page_p", 1))
    page_c = int(request.args.get("page_c", 1))
    per_page = 20

    if cliente_nombre or cliente_correo or cliente_dni:
        clientes = buscar_clientes_exacto(cliente_nombre, cliente_correo, cliente_dni)
        productos = []
    elif termino:
        productos = buscar_productos(termino)
        clientes = buscar_clientes(termino)
    else:
        productos = []
        clientes = []

    total_resultados = len(productos) + len(clientes)

    # Paginación
    productos_pag = productos[(page_p-1)*per_page: page_p*per_page]
    clientes_pag = clientes[(page_c-1)*per_page: page_c*per_page]

    if request.args.get("export") in ["csv", "xls"]:
        export_tipo = request.args.get("export")
        si = StringIO()
        writer = csv.writer(si)

        # Encabezado unificado: productos primero, luego clientes
        writer.writerow(["tipo", "id", "nombre", "cantidad", "precio", "correo", "telefono", "dni"])
        for p in productos:
            writer.writerow(["producto", p["id"], p["nombre"], p["cantidad"], p["precio"], "", "", ""])
        for c in clientes:
            writer.writerow(["cliente", c["id"], c["nombre"], "", "", c["correo"], c["telefono"], c.get("dni", "")])

        output = make_response(si.getvalue())
        si.close()

        if export_tipo == "xls":
            output.headers["Content-Type"] = "application/vnd.ms-excel"
            output.headers["Content-Disposition"] = "attachment; filename=busqueda_resultados.xls"
        else:
            output.headers["Content-Type"] = "text/csv; charset=utf-8"
            output.headers["Content-Disposition"] = "attachment; filename=busqueda_resultados.csv"

        return output

    return render_template(
        "buscar.html",
        productos=productos_pag,
        clientes=clientes_pag,
        termino=termino,
        cliente_nombre=cliente_nombre,
        cliente_correo=cliente_correo,
        cliente_dni=cliente_dni,
        total=total_resultados,
        page_p=page_p,
        page_c=page_c,
        per_page=per_page,
        total_productos=len(productos),
        total_clientes=len(clientes)
    )


@app.route("/autocomplete", methods=["GET"])
@login_requerido
def autocomplete():
    """Devuelve sugerencias de productos/clientes para autocompletar."""
    termino = request.args.get("q", "").strip()
    if not termino:
        return jsonify([])

    productos = buscar_productos(termino)
    clientes = buscar_clientes(termino)

    sugerencias = []
    for p in productos:
        sugerencias.append({"tipo": "producto", "texto": p["nombre"], "id": p["id"]})
    for c in clientes:
        sugerencias.append({"tipo": "cliente", "texto": c["nombre"], "id": c["id"]})

    # devolver como máximo 10 resultados
    return jsonify(sugerencias[:10])


# -------- Código del archivo actualizado --------

# Ruta para datos (opcional)
@app.route("/datos")
def datos():
    try:
        with open(TXT_FILE, "r", encoding="utf-8") as f:
            txt_lines = [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        txt_lines = []

    # Convertir líneas TXT (nombre,cantidad,precio) a dicts
    txt_items = []
    for line in txt_lines:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 3:
            txt_items.append({
                "nombre": parts[0],
                "cantidad": parts[1],
                "precio": parts[2],
            })

    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            json_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        json_data = []

    try:
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            csv_data = [row for row in reader if row]
    except FileNotFoundError:
        csv_data = []

    csv_items = []
    for row in csv_data:
        if len(row) >= 3:
            csv_items.append({
                "nombre": row[0],
                "cantidad": row[1],
                "precio": row[2],
            })

    # Datos de facturas y repuestos desde la base de datos
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM repuestos")
    repuestos = cursor.fetchall()

    cursor.execute(
        "SELECT f.id, c.nombre AS cliente, f.fecha, f.total "
        "FROM facturas f "
        "LEFT JOIN clientes c ON f.id_cliente = c.id"
    )
    facturas = cursor.fetchall()

    conn.close()

    return render_template(
        "datos.html",
        txt_items=txt_items,
        json=json_data,
        csv_items=csv_items,
        repuestos=repuestos,
        facturas=facturas,
    )
@app.route("/test_db")
def test_db():
    try:
        conexion = conectar()
        cursor=conexion.cursor()
        cursor.execute("SELECT 1")
        print("Conexión a MySQL exitosa")
        db=cursor.fetchone()
        print(f"Resultado de prueba: {db}")
        cursor.close()
        desconectar(conexion)

        return "Conexión a MySQL exitosa"
    except Exception as e:
        print(f"Error al conectar a MySQL: {e}")
        return f" error al conectar a MySQL: {e}"

if __name__ == "__main__":
    app.run(debug=True)
