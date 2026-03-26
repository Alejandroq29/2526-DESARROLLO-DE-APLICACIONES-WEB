# conexión a SQLite - masterlogic.db
import sqlite3

def conectar():
    """Conecta a la base de datos SQLite masterlogic.db"""
    conexion = sqlite3.connect("masterlogic.db")
    conexion.row_factory = sqlite3.Row
    return conexion

def desconectar(conexion):
    """Cierra la conexión a la base de datos"""
    conexion.close()
