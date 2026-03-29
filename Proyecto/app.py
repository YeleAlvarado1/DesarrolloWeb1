from flask import Flask, render_template, request, redirect, url_for
from conexion.conexion import get_connection
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models.usuario import Usuario
from werkzeug.security import generate_password_hash, check_password_hash
from fpdf import FPDF
from flask import make_response

# SERVICES PRODUCTOS
from services.producto_service import (
    obtener_productos,
    insertar_producto,
    eliminar_producto,
    actualizar_producto,
    obtener_producto_por_id
)

# inventario
from inventario import Producto, Inventario
from inventario import guardar_txt, guardar_json, guardar_csv, leer_txt

app = Flask(__name__)
app.secret_key = "clave_secreta"

# ===============================
# FLASK LOGIN
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
# INVENTARIO
# ===============================
inventario = Inventario()

p1 = Producto(1, "Aire acondicionado LG", 5, 450)
p2 = Producto(2, "Filtro de aire", 10, 25)

inventario.agregar_producto(p1)
inventario.agregar_producto(p2)


# ===============================
# PDF reporte
# ===============================
@app.route("/reporte")
@login_required
def reporte_pdf():

    productos = obtener_productos()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Reporte JAZ Climatización", ln=True)

    for p in productos:
        pdf.cell(200, 10, txt=f"{p[1]} - ${p[3]}", ln=True)

    response = make_response(pdf.output(dest='S').encode('latin-1'))
    response.headers.set('Content-Type', 'application/pdf')
    response.headers.set('Content-Disposition', 'attachment', filename='reporte.pdf')

    return response
# ===============================
# PAGINAS
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
# PRODUCTOS
# ===============================
@app.route("/productos")
@login_required
def productos():
    productos = obtener_productos()
    return render_template("productos_listar.html", productos=productos)

# ===============================
# CREAR
# ===============================
@app.route("/productos/crear", methods=["GET", "POST"])
@login_required
def crear_producto():

    if request.method == "POST":
        nombre = request.form["nombre"]
        cantidad = int(request.form["cantidad"])
        precio = float(request.form["precio"])

        insertar_producto(nombre, cantidad, precio)

        guardar_txt(nombre, precio)
        guardar_json(nombre, precio)
        guardar_csv(nombre, precio)

        return redirect(url_for("productos"))

    return render_template("productos_crear.html")

# ===============================
# EDITAR
# ===============================
@app.route("/productos/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_producto(id):

    if request.method == "POST":
        nombre = request.form["nombre"]
        cantidad = int(request.form["cantidad"])
        precio = float(request.form["precio"])

        actualizar_producto(id, nombre, cantidad, precio)

        return redirect(url_for("productos"))

    producto = obtener_producto_por_id(id)

    return render_template("productos_editar.html", producto=producto)

# ===============================
# ELIMINAR
# ===============================
@app.route("/productos/eliminar/<int:id>")
@login_required
def eliminar_producto_view(id):
    eliminar_producto(id)
    return redirect(url_for("productos"))

# ===============================
# DATOS TXT
# ===============================
@app.route("/datos")
def ver_datos():
    datos = leer_txt()
    return render_template("datos.html", datos=datos)

# ===============================
# REGISTRO
# ===============================
@app.route("/registro", methods=["GET", "POST"])
def registro():

    if request.method == "POST":
        nombre = request.form["nombre"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"], method='pbkdf2:sha256')

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
# LOGIN
# ===============================
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"].strip()
        password = request.form["password"].strip()

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM usuarios WHERE email=%s", (email,))
        user = cursor.fetchone()

        conn.close()

        print("USER:", user)

        if user:
            password_bd = user[-1]

            if isinstance(password_bd, bytes):
                password_bd = password_bd.decode('utf-8')

            password_bd = password_bd.strip()

            print("COMPARANDO...")
            print(password_bd)
            print(password)

            resultado = check_password_hash(password_bd, password)

            print("RESULTADO:", resultado)

            if resultado:
                usuario = Usuario(user[0], user[1], user[2], user[3])
                login_user(usuario)

                print("LOGIN EXITOSO")

                return redirect(url_for("productos"))
            else:
                print("ERROR PASSWORD")
                return render_template("login.html", error="Credenciales incorrectas")

        else:
            print("ERROR USER")
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