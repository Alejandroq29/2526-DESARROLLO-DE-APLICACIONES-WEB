from .bd import obtener_conexion


def obtener_clientes():
    conexion = obtener_conexion()
    clientes = conexion.execute(
        "SELECT * FROM clientes"
    ).fetchall()
    conexion.close()
    return clientes


def agregar_cliente(nombre, correo, telefono):
    conexion = obtener_conexion()

    conexion.execute(
        "INSERT INTO clientes (nombre, correo, telefono) VALUES (?, ?, ?)",
        (nombre, correo, telefono)
    )

    conexion.commit()
    conexion.close()