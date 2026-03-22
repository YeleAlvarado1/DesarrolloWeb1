from flask import Flask, render_template, request, redirect, url_for
from conexion.conexion import get_connection
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import Usuario
from werkzeug.security import generate_password_hash, check_password_hash

# importar inventario
from inventario import Producto, Inventario
from inventario import guardar_txt, guardar_json, guardar_csv, leer_txt

app = Flask(__name__)
app.secret_key = "clave_secreta"

# ===============================
# CONFIGURAR FLASK LOGIN
# ===============================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM usuarios WHERE id_usuario=%s", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if user:
        return Usuario(user[0], user[1], user[2], user[3])
    return None

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
# PRODUCTOS (PROTEGIDO)
# ===============================
@app.route("/productos")
@login_required
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
@login_required
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
@login_required
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
@login_required
def eliminar_producto(id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM productos WHERE id=%s", (id,))
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
# REGISTRO DE USUARIOS
# ===============================
@app.route("/registro", methods=["GET", "POST"])
def registro():

    if request.method == "POST":
        nombre = request.form["nombre"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])  # 🔐 cifrado

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO usuarios(nombre,email,password) VALUES (%s,%s,%s)",
            (nombre, email, password)
        )

        conn.commit()
        conn.close()

        return redirect(url_for("login"))

    return render_template("registro.html")

# ===============================
# LOGIN USUARIOS
# ===============================
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM usuarios WHERE email=%s", (email,))
        user = cursor.fetchone()

        conn.close()

        if user and check_password_hash(user[3], password):
            usuario = Usuario(user[0], user[1], user[2], user[3])
            login_user(usuario)
            return redirect(url_for("productos"))
        else:
            return render_template("login.html", error="Credenciales incorrectas")

    return render_template("login.html")

# ===============================
# LOGOUT
# ===============================
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# ===============================
# RUN
# ===============================
if __name__ == "__main__":
    app.run(debug=True)