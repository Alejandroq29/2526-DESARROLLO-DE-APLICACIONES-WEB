from .bd import obtener_conexion


def obtener_productos():
    conexion = obtener_conexion()
    productos = conexion.execute(
        "SELECT * FROM productos"
    ).fetchall()
    conexion.close()
    return productos


def agregar_producto(nombre, cantidad, precio):
    conexion = obtener_conexion()
    conexion.execute(
        "INSERT INTO productos (nombre, cantidad, precio) VALUES (?, ?, ?)",
        (nombre, cantidad, precio)
    )
    conexion.commit()
    conexion.close()