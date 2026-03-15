from flask import Flask, render_template, request, redirect, url_for
from conexion.conexion import get_connection

# importar clases y funciones
from inventario import Producto, Inventario
from inventario import guardar_txt, guardar_json, guardar_csv
from inventario import leer_txt

app = Flask(__name__)

# ===============================
# INVENTARIO EN MEMORIA
# ===============================

inventario = Inventario()

p1 = Producto(1, "Aire acondicionado LG", 5, 450)
p2 = Producto(2, "Filtro de aire", 10, 25)

inventario.agregar_producto(p1)
inventario.agregar_producto(p2)

# ===============================
# PAGINAS PRINCIPALES
# ===============================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/servicios")
def servicios():
    return render_template("servicios.html")


@app.route("/clientes")
def clientes():
    return render_template("clientes.html")


@app.route("/acerca")
def acerca():
    return render_template("about.html")


# ===============================
# LISTAR PRODUCTOS
# ===============================

@app.route("/productos")
def productos():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM productos")
    productos = cursor.fetchall()

    conn.close()

    return render_template("productos_listar.html", productos=productos)


# ===============================
# CREAR PRODUCTO
# ===============================

@app.route("/productos/crear", methods=["GET", "POST"])
def crear_producto():

    if request.method == "POST":

        nombre = request.form["nombre"]
        cantidad = int(request.form["cantidad"])
        precio = float(request.form["precio"])

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO productos(nombre,cantidad,precio) VALUES (%s,%s,%s)",
            (nombre, cantidad, precio)
        )

        conn.commit()
        conn.close()

        guardar_txt(nombre, precio)
        guardar_json(nombre, precio)
        guardar_csv(nombre, precio)

        return redirect(url_for("productos"))

    return render_template("productos_crear.html")


# ===============================
# EDITAR PRODUCTO
# ===============================

@app.route("/productos/editar/<int:id>", methods=["GET", "POST"])
def editar_producto(id):

    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":

        nombre = request.form["nombre"]
        cantidad = int(request.form["cantidad"])
        precio = float(request.form["precio"])

        cursor.execute(
            "UPDATE productos SET nombre=%s, cantidad=%s, precio=%s WHERE id=%s",
            (nombre, cantidad, precio, id)
        )

        conn.commit()
        conn.close()

        return redirect(url_for("productos"))

    cursor.execute("SELECT * FROM productos WHERE id=%s", (id,))
    producto = cursor.fetchone()

    conn.close()

    return render_template("productos_editar.html", producto=producto)


# ===============================
# ELIMINAR PRODUCTO
# ===============================

@app.route("/productos/eliminar/<int:id>")
def eliminar_producto(id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM productos WHERE id=%s",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("productos"))


# ===============================
# DATOS TXT
# ===============================

@app.route("/datos")
def ver_datos():

    datos = leer_txt()

    return render_template("datos.html", datos=datos)


# ===============================
# RUN
# ===============================

if __name__ == "__main__":
    app.run(debug=True)

