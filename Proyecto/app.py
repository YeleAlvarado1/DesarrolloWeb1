from flask import Flask, render_template, request, redirect, url_for
from database import get_connection

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
# PAGINA PRINCIPAL
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


@app.route("/about")
def about():
    return render_template("about.html")


# ===============================
# LISTAR PRODUCTOS
# ===============================

@app.route("/productos")
def productos():

    conn = get_connection()

    productos = conn.execute(
        "SELECT * FROM productos"
    ).fetchall()

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

        conn.execute(
            "INSERT INTO productos(nombre,cantidad,precio) VALUES (?,?,?)",
            (nombre, cantidad, precio)
        )

        conn.commit()
        conn.close()

        # guardar también en archivos
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

    if request.method == "POST":

        nombre = request.form["nombre"]
        cantidad = int(request.form["cantidad"])
        precio = float(request.form["precio"])

        conn.execute(
            "UPDATE productos SET nombre=?, cantidad=?, precio=? WHERE id=?",
            (nombre, cantidad, precio, id)
        )

        conn.commit()
        conn.close()

        return redirect(url_for("productos"))

    producto = conn.execute(
        "SELECT * FROM productos WHERE id=?", (id,)
    ).fetchone()

    conn.close()

    return render_template("productos_editar.html", producto=producto)


# ===============================
# ELIMINAR PRODUCTO
# ===============================

@app.route("/productos/eliminar/<int:id>")
def eliminar_producto(id):

    conn = get_connection()

    conn.execute(
        "DELETE FROM productos WHERE id=?", (id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("productos"))


# ===============================
# MOSTRAR DATOS DESDE TXT
# ===============================

@app.route("/datos")
def ver_datos():

    datos = leer_txt()

    return render_template("datos.html", datos=datos)


# ===============================
# EJECUTAR APLICACIÓN
# ===============================

if __name__ == "__main__":
    app.run(debug=True)