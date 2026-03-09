from flask import Flask, render_template, request, redirect, url_for
from forms import ProductoForm
from flask_sqlalchemy import SQLAlchemy
from database import init_db, get_connection
import json
import csv
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tu-clave-secreta-aqui'  # Cambiar a una clave segura en producción
init_db()

TXT_FILE = "inventario/data/datos.txt"
JSON_FILE = "inventario/data/datos.json"
CSV_FILE = "inventario/data/datos.csv"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contacto")
def contacto():
    return render_template("contactos.html")


# ---------------- CLIENTES ----------------

@app.route("/clientes")
def clientes():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clientes")
    clientes = cursor.fetchall()
    conn.close()
    return render_template("cliente.html", clientes=clientes)


@app.route("/cliente/nuevo", methods=["GET","POST"])
def cliente_form():

    if request.method == "POST":

        nombre = request.form["nombre"]
        correo = request.form["correo"]
        telefono = request.form["telefono"]

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
        "INSERT INTO clientes(nombre,correo,telefono) VALUES (?,?,?)",
        (nombre,correo,telefono)
        )

        conn.commit()
        conn.close()

        return redirect(url_for("clientes"))

    return render_template("cliente_form.html")


@app.route("/register_client", methods=["GET","POST"])
def register_client():

    if request.method == "POST":

        nombre = request.form["nombre"]
        correo = request.form["correo"]
        telefono = request.form["telefono"]
        direccion = request.form.get("direccion", "")
        dni = request.form.get("dni", "")

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
        "INSERT INTO clientes(nombre,correo,telefono) VALUES (?,?,?)",
        (nombre,correo,telefono)
        )

        conn.commit()
        conn.close()

        return redirect(url_for("clientes"))

    return render_template("register_client.html")


# ---------------- PRODUCTOS ----------------

@app.route("/productos")
def productos():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM productos")

    productos = cursor.fetchall()

    conn.close()

    return render_template("producto.html", productos=productos)


@app.route("/producto/nuevo", methods=["GET","POST"])
def producto_form():

    if request.method == "POST":

        nombre = request.form["nombre"]
        cantidad = request.form["cantidad"]
        precio = request.form["precio"]

        # TXT
        with open(TXT_FILE,"a") as f:
            f.write(f"{nombre},{cantidad},{precio}\n")

        # JSON
        data = {"nombre":nombre,"cantidad":cantidad,"precio":precio}

        try:
            with open(JSON_FILE,"r") as f:
                lista = json.load(f)
        except:
            lista = []

        lista.append(data)

        with open(JSON_FILE,"w") as f:
            json.dump(lista,f,indent=4)

        # CSV
        with open(CSV_FILE,"a",newline="") as f:
            writer = csv.writer(f)
            writer.writerow([nombre,cantidad,precio])

        # BASE DE DATOS
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
        "INSERT INTO productos(nombre,cantidad,precio) VALUES (?,?,?)",
        (nombre,cantidad,precio)
        )

        conn.commit()
        conn.close()

        return redirect(url_for("productos"))

    return render_template("producto.forms.html")


# ---------------- INVENTARIO ----------------

@app.route("/inventario")
def inventario():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM productos")

    inventario = cursor.fetchall()

    conn.close()

    return render_template("inventario.html", inventario=inventario)


# -------- Código del archivo actualizado --------

# Ruta para datos (opcional)
@app.route("/datos")
def datos():
    try:
        with open(TXT_FILE,"r") as f:
            txt = f.readlines()
    except FileNotFoundError:
        txt = []

    try:
        with open(JSON_FILE,"r") as f:
            json_data = json.load(f)
    except FileNotFoundError:
        json_data = []

    try:
        with open(CSV_FILE,"r") as f:
            reader = csv.reader(f)
            csv_data = list(reader)
    except FileNotFoundError:
        csv_data = []

    return render_template("datos.html",txt=txt,json=json_data,csv=csv_data)

if __name__ == "__main__":
    app.run(debug=True)
