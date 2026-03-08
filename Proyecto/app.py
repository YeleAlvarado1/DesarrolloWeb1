from flask import Flask, render_template, request, redirect, url_for
from database import get_connection
from inventario import Producto, Inventario
app = Flask(__name__)
inventario = Inventario()

p1 = Producto(1, "Aire acondicionado LG", 5, 450)
p2 = Producto(2, "Filtro de aire", 10, 25)

inventario.agregar_producto(p1)
inventario.agregar_producto(p2)



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


@app.route("/productos")
def productos():

    conn = get_connection()
    productos = conn.execute("SELECT * FROM productos").fetchall()
    conn.close()

    return render_template("productos_listar.html", productos=productos)


@app.route("/productos/crear", methods=["GET","POST"])
def crear_producto():

    if request.method == "POST":

        nombre = request.form["nombre"]
        cantidad = request.form["cantidad"]
        precio = request.form["precio"]

        conn = get_connection()
        conn.execute(
            "INSERT INTO productos(nombre,cantidad,precio) VALUES (?,?,?)",
            (nombre,cantidad,precio)
        )
        conn.commit()
        conn.close()

        return redirect(url_for("productos"))

    return render_template("productos_crear.html")


@app.route("/productos/editar/<int:id>", methods=["GET","POST"])
def editar_producto(id):

    conn = get_connection()

    if request.method == "POST":

        nombre = request.form["nombre"]
        cantidad = request.form["cantidad"]
        precio = request.form["precio"]

        conn.execute(
            "UPDATE productos SET nombre=?, cantidad=?, precio=? WHERE id=?",
            (nombre,cantidad,precio,id)
        )
        conn.commit()
        conn.close()

        return redirect(url_for("productos"))

    producto = conn.execute(
        "SELECT * FROM productos WHERE id=?",(id,)
    ).fetchone()

    conn.close()

    return render_template("productos_editar.html", producto=producto)


@app.route("/productos/eliminar/<int:id>")
def eliminar_producto(id):

    conn = get_connection()
    conn.execute("DELETE FROM productos WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for("productos"))


if __name__ == "__main__":
    app.run(debug=True)