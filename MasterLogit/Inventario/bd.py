import sqlite3

DATABASE = "masterlogic.db"

def obtener_conexion():
    conexion = sqlite3.connect(DATABASE)
    conexion.row_factory = sqlite3.Row
    return conexion