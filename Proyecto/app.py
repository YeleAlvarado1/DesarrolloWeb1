from flask import Flask, render_template, request, redirect, url_for, session, make_response
from conexion.conexion import get_connection
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models.usuario import Usuario
from werkzeug.security import generate_password_hash, check_password_hash
from fpdf import FPDF
from flask import flash
from decimal import Decimal

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
# LOGIN
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
        return Usuario(user[0], user[1], user[2], user[3], user[4])
    return None

# ===============================
# INVENTARIO
# ===============================
inventario = Inventario()
inventario.agregar_producto(Producto(1, "Aire acondicionado LG", 5, 450))
inventario.agregar_producto(Producto(2, "Filtro de aire", 10, 25))

# ===============================
# PDF CONTACTOS 
# ===============================
@app.route("/reporte_contactos")
@login_required
def reporte_contactos():

    if session.get("rol") != "admin":
        return redirect(url_for('index'))

    fecha_inicio = request.args.get("fecha_inicio")
    fecha_fin = request.args.get("fecha_fin")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT nombre, telefono, correo, mensaje, fecha, estado, eliminado_por, fecha_eliminado
        FROM contactos
        WHERE DATE(fecha) BETWEEN %s AND %s
        ORDER BY fecha DESC
    """, (fecha_inicio, fecha_fin))

    contactos = cursor.fetchall()
    conn.close()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=8)

    pdf.cell(200, 10, txt="Reporte de Contactos - JAZ Climatización", ln=True)
    pdf.cell(200, 10, txt=f"Desde: {fecha_inicio} Hasta: {fecha_fin}", ln=True)
    pdf.ln(5)

    headers = ["Nombre", "Teléfono", "Correo", "Mensaje", "Fecha", "Estado", "Eliminado por", "Fecha eliminado"]

    ancho = 23

    # ENCABEZADOS
    for h in headers:
        pdf.cell(ancho, 8, h, border=1, align="C")
    pdf.ln()

    # DATOS
    for c in contactos:
        for dato in c:
            texto = str(dato) if dato else "-"
            pdf.cell(ancho, 8, texto[:12], border=1)
        pdf.ln()

    response = make_response(pdf.output(dest='S').encode('latin-1'))
    response.headers.set('Content-Type', 'application/pdf')
    response.headers.set('Content-Disposition', 'attachment', filename='reporte_contactos.pdf')

    return response

# ===============================
# PAGINAS
# ===============================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/servicios")
def servicios():

    productos = obtener_productos()

    return render_template("servicios.html", productos=productos)

# ===============================
#Clientes Admin
# ===============================
@app.route("/admin/clientes")
@login_required
def clientes():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT c.id_cliente, c.nombre, c.correo, c.telefono, c.direccion, c.fecha,
               v.id_venta, v.fecha
        FROM clientes c
        LEFT JOIN ventas v ON c.id_cliente = v.id_cliente
        ORDER BY c.id_cliente DESC
    """)

    datos = cursor.fetchall()
    conn.close()

    return render_template("clientes.html", datos=datos)
# ===============================
#acerca de
# ===============================


@app.route("/acerca")
def acerca():
    return render_template("about.html")

@app.route("/tienda")
def tienda():

    productos = obtener_productos() 

    return render_template("tienda.html", productos=productos) 

@app.route("/vaciar")
def vaciar():
    session.pop("carrito", None)
    return "Carrito limpiado"    
# ===============================
# CARRITO DE COMPRAS
# ===============================
@app.route("/carrito/agregar/<int:id>")
def agregar_carrito(id):

    carrito = session.get("carrito", {})

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT cantidad, nombre FROM productos WHERE id=%s", (id,))
    producto = cursor.fetchone()

    stock = producto[0]
    nombre = producto[1]

    id_str = str(id)

    # SIN STOCK
    if stock <= 0:
        flash(f" {nombre} está agotado (stock 0)")
        return redirect(url_for("servicios"))

    # 🛒 AGREGAR NORMAL
    if id_str in carrito:
        if carrito[id_str] < stock:
            carrito[id_str] += 1
        else:
            flash(f" Solo hay {stock} unidades disponibles")
            return redirect(url_for("servicios"))
    else:
        carrito[id_str] = 1

    session["carrito"] = carrito

    flash(f" {nombre} agregado al carrito")
    return redirect(url_for("servicios"))

# ===============================
# ver carrito
# ===============================    
@app.route("/carrito")
def ver_carrito():

    carrito = session.get("carrito", {})
    productos_db = obtener_productos()

    productos = []
    subtotal = 0

    for p in productos_db:
        id_str = str(p[0])
        if id_str in carrito:
            cantidad = carrito[id_str]
            total = cantidad * (p[3])

            productos.append({
                "id": p[0],
                "nombre": p[1],
                "precio": p[3],
                "cantidad": cantidad,
                "total": total
            })

            subtotal += total

    iva = subtotal * Decimal ("0.15")
    total_final = subtotal + iva

    return render_template("carrito.html",
                           productos=productos,
                           subtotal=subtotal,
                           iva=iva,
                           total=total_final)

# ===============================
# Auemtar y disminuir
# ==============================
@app.route("/carrito/aumentar/<int:id>")
def aumentar_cantidad(id):

    carrito = session.get("carrito", {})
    id_str = str(id)
  

    if id_str in carrito:
        carrito[id_str] += 1

    session["carrito"] = carrito

    return redirect(url_for("ver_carrito"))

@app.route("/carrito/disminuir/<int:id>")
def disminuir_cantidad(id):

    carrito = session.get("carrito", {})
    id_str = str(id)

    if id_str in carrito:
        carrito[id_str] -= 1

        if carrito[id_str] <= 0:
            del carrito[id_str]

    session["carrito"] = carrito

    return redirect(url_for("ver_carrito"))
                           
# ===============================
# COMPRAR
# ===============================   
@app.route("/comprar")
def comprar():

    carrito = session.get("carrito", {})

    conn = get_connection()
    cursor = conn.cursor()

    # Crear venta
    cursor.execute("INSERT INTO ventas (fecha) VALUES (NOW())")
    venta_id = cursor.lastrowid

    for id, cantidad in carrito.items():

        # Obtener precio actual
        cursor.execute("SELECT precio FROM productos WHERE id=%s", (id,))
        precio = cursor.fetchone()[0]

        # Guardar detalle de venta

        cursor.execute("SELECT nombre, precio FROM productos WHERE id=%s", (id,))
        producto_data = cursor.fetchone()

        nombre_producto = producto_data[0]
        precio = producto_data[1]

        # Insertar con más datos
        cursor.execute("""
        INSERT INTO detalle_venta (venta_id, producto_id, nombre_producto, cantidad, precio, fecha)
        VALUES (%s, %s, %s, %s, %s, NOW())
        """, (venta_id, id, nombre_producto, cantidad, precio))

        # Descontar stock
        cursor.execute("""
            UPDATE productos 
            SET cantidad = cantidad - %s
            WHERE id=%s AND cantidad >= %s
        """, (cantidad, id, cantidad))

    conn.commit()
    conn.close()

    session["carrito"] = {}

    return redirect(url_for("detalle_compra"))

#==============================
# DETALLE COMPRA
#==============================

@app.route("/detalle_compra")
def detalle_compra():

    return render_template("detalle.html")

#==============================
# finalizar la compra
# =============================    
@app.route("/finalizar_compra", methods=["POST"])
def finalizar_compra():

    carrito = session.get("carrito", {})

    nombre = request.form["nombre"]
    correo = request.form["correo"]
    telefono = request.form["telefono"]
    direccion = request.form["direccion"]

    conn = get_connection()
    cursor = conn.cursor()

    # GUARDAR CLIENTE
    cursor.execute("""
        INSERT INTO clientes (nombre, correo, telefono, direccion, fecha)
        VALUES (%s, %s, %s, %s, NOW())
    """, (nombre, correo, telefono, direccion))

    cliente_id = cursor.lastrowid

    # CREAR VENTA CON CLIENTE
    cursor.execute("""
        INSERT INTO ventas (fecha, id_cliente)
        VALUES (NOW(), %s)
    """, (cliente_id,))

    venta_id = cursor.lastrowid

    #  DETALLE DE VENTA
    for id, cantidad in carrito.items():

        cursor.execute("SELECT nombre, precio FROM productos WHERE id=%s", (id,))
        producto = cursor.fetchone()

        nombre_producto = producto[0]
        precio = producto[1]

        cursor.execute("""
            INSERT INTO detalle_venta (venta_id, producto_id, nombre_producto, cantidad, precio, fecha)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """, (venta_id, id, nombre_producto, cantidad, precio))

        # descontar stock
        cursor.execute("""
            UPDATE productos 
            SET cantidad = cantidad - %s
            WHERE id=%s
        """, (cantidad, id))

    conn.commit()
    conn.close()

    session["carrito"] = {}

    return render_template("compra_exitosa.html", nombre=nombre)
#==============================
#DESCONTAR
#==============================

@app.context_processor
def carrito_contador():

    carrito = session.get("carrito", {})

    if isinstance(carrito, list):
        total = len(carrito)
    else:
        total = sum(carrito.values())

    return dict(carrito_total=total)   

def total_carrito():
    carrito = session.get('carrito', {})
    return sum(carrito.values())     


# ===============================
# CONTACTO PUBLICO
# ===============================
@app.route("/contacto", methods=["GET", "POST"])
def contacto():

    if request.method == "POST":
        nombre = request.form["nombre"]
        correo = request.form["correo"]
        telefono = request.form["telefono"]

        if not telefono.isdigit():
            return "El teléfono solo debe contener números"

        mensaje = request.form["mensaje"]

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO contactos (nombre, telefono, correo, mensaje, fecha, estado)
            VALUES (%s, %s, %s, %s, NOW(), 'Pendiente')
        """, (nombre, telefono, correo, mensaje))

        conn.commit()
        conn.close()

        return redirect(url_for("index"))

    return render_template("contacto.html")

# ===============================
# ADMIN CONTACTOS
# ===============================
@app.route('/admin/contactos')
@login_required
def ver_contactos():

    if session.get("rol") != "admin":
        return redirect(url_for('index'))

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, nombre, telefono, correo, mensaje, fecha, estado, respuesta
        FROM contactos
        ORDER BY fecha DESC
    """)

    contactos = cursor.fetchall()
    conn.close()

    return render_template('admin_contactos.html', contactos=contactos)

@app.route('/admin')
@login_required
def admin():
    if session.get("rol") == "admin":
        return redirect(url_for('ver_contactos'))
    return "No autorizado"

# ===============================
# ACCIONES CONTACTOS
# ===============================
@app.route("/contacto/leido/<int:id>")
@login_required
def marcar_leido(id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE contactos SET estado='Leído' WHERE id=%s", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for("ver_contactos"))

@app.route("/contacto/eliminar/<int:id>")
@login_required
def eliminar_contacto(id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE contactos 
        SET estado='Eliminado',
            eliminado_por=%s,
            fecha_eliminado=NOW()
        WHERE id=%s
    """, (session.get("usuario"), id))

    conn.commit()
    conn.close()
    flash("Contacto eliminado correctamente 🗑️", "success") 

    return redirect(url_for("ver_contactos"))

@app.route("/contacto/responder/<int:id>", methods=["GET","POST"])
@login_required
def responder_contacto(id):

    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        respuesta = request.form["respuesta"]

        cursor.execute("""
            UPDATE contactos 
            SET respuesta=%s, estado='Respondido'
            WHERE id=%s
        """, (respuesta, id))

        conn.commit()
        conn.close()

        return redirect(url_for("ver_contactos"))

    cursor.execute("SELECT * FROM contactos WHERE id=%s", (id,))
    contacto = cursor.fetchone()
    conn.close()

    return render_template("responder_contacto.html", contacto=contacto)

# ===============================
# PRODUCTOS
# ===============================
@app.route("/productos")
@login_required
def productos():

    if current_user.rol != "admin":
        return redirect(url_for("index"))

    productos = obtener_productos()
    return render_template("productos_listar.html", productos=productos)

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


@app.route("/productos/eliminar/<int:id>")
@login_required
def eliminar_producto_view(id):
    eliminar_producto(id)
    return redirect(url_for("productos"))

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
    productos = obtener_productos()  # NUEVO

    return render_template("productos_editar.html", 
                           producto=producto, 
                           productos=productos)

# ===============================
# REPORTE PRODUCTOS
# ===============================

@app.route("/reporte_productos", methods=["POST"])
@login_required
def reporte_productos():

    if current_user.rol != "admin":
        return redirect(url_for("index"))

    fecha_inicio = request.form.get("fecha_inicio")
    fecha_fin = request.form.get("fecha_fin")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT nombre, cantidad, precio
        FROM productos
    """)

    productos = cursor.fetchall()
    conn.close()

    from datetime import datetime

    pdf = FPDF()
    pdf.add_page()

    #  TÍTULO
    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 12, "JAZ Climatizacion", 0, 1, "C")

    # Línea decorativa
    pdf.set_draw_color(0, 102, 204)
    pdf.set_line_width(0.8)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    # Fecha del reporte
    pdf.set_font("Arial", "", 10)
    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
    pdf.cell(0, 8, f"Fecha del reporte: {fecha_actual}", 0, 1, "R")

    #  Rango de fechas
    pdf.cell(0, 8, f"Desde: {fecha_inicio}   Hasta: {fecha_fin}", 0, 1, "L")

    pdf.ln(5)

    # ENCABEZADO
    pdf.set_fill_color(0, 102, 204)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 12)

    pdf.cell(90, 10, "Producto", 1, 0, "C", True)
    pdf.cell(30, 10, "Cantidad", 1, 0, "C", True)
    pdf.cell(40, 10, "Precio", 1, 1, "C", True)

    # TEXTO NORMAL
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 11)

    pdf.set_draw_color(200, 200, 200)  # bordes suaves
    pdf.set_line_width(0.3)

    total_general = 0

    for p in productos:
        nombre = str(p[0])
        cantidad = int(p[1])
        precio = float(p[2])

        total = cantidad * precio
        total_general += total

        # calcular altura necesaria
        start_x = pdf.get_x()
        start_y = pdf.get_y()

        # dividir texto en líneas
        lineas = pdf.multi_cell(90, 8, nombre, border=0, split_only=True)
        altura = 8 * len(lineas)

        # PRODUCTO
        pdf.multi_cell(90, 8, nombre, border=1)

        # volver arriba a la derecha
        pdf.set_xy(start_x + 90, start_y)

        # CANTIDAD y PRECIO con misma altura
        pdf.cell(30, altura, str(cantidad), border=1, align="C")
        pdf.cell(40, altura, f"${precio:.2f}", border=1, align="C")

        pdf.ln()
    # TOTAL
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"Total inventario: ${total_general:.2f}", 0, 1, "R")

    # DESCARGA
    response = make_response(pdf.output(dest='S').encode('latin-1'))
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=reporte_productos.pdf'

    return response 
# ===============================
#reporte de ventas
# =============================     
@app.route("/reporte_ventas", methods=["POST"])
@login_required
def reporte_ventas():

    if current_user.rol != "admin":
        return redirect(url_for("index"))

    fecha_inicio = request.form.get("fecha_inicio")
    fecha_fin = request.form.get("fecha_fin")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT v.id_venta, v.fecha, c.nombre, d.nombre_producto, d.cantidad, d.precio
        FROM ventas v
        JOIN clientes c ON v.id_cliente = c.id_cliente
        JOIN detalle_venta d ON v.id_venta = d.venta_id
        WHERE DATE(v.fecha) BETWEEN %s AND %s
        ORDER BY v.fecha DESC
    """, (fecha_inicio, fecha_fin))

    ventas = cursor.fetchall()
    conn.close()

    from datetime import datetime
    pdf = FPDF()
    pdf.add_page()

    # 🧾 TÍTULO
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Reporte de Ventas - JAZ Climatizacion", 0, 1, "C")

    pdf.set_font("Arial", "", 10)
    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
    pdf.cell(0, 8, f"Generado: {fecha_actual}", 0, 1, "R")
    pdf.cell(0, 8, f"Desde: {fecha_inicio} Hasta: {fecha_fin}", 0, 1, "L")

    pdf.ln(5)

    # 🔵 ENCABEZADO
    pdf.set_fill_color(0, 102, 204)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 10)

    pdf.cell(20, 8, "Venta", 1, 0, "C", True)
    pdf.cell(35, 8, "Fecha", 1, 0, "C", True)
    pdf.cell(35, 8, "Cliente", 1, 0, "C", True)
    pdf.cell(50, 8, "Producto", 1, 0, "C", True)
    pdf.cell(20, 8, "Cant.", 1, 0, "C", True)
    pdf.cell(30, 8, "Precio", 1, 1, "C", True)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 9)

    total_general = 0

    for v in ventas:
        venta_id, fecha, cliente, producto, cantidad, precio = v
        subtotal = cantidad * precio
        total_general += subtotal

        pdf.cell(20, 8, str(venta_id), 1)
        pdf.cell(35, 8, str(fecha)[:16], 1)
        pdf.cell(35, 8, cliente, 1)

        # producto adaptable
        x = pdf.get_x()
        y = pdf.get_y()
        lineas = pdf.multi_cell(50, 8, producto, border=0, split_only=True)
        altura = 8 * len(lineas)

        pdf.multi_cell(50, 8, producto, border=1)
        pdf.set_xy(x + 50, y)

        pdf.cell(20, altura, str(cantidad), 1, 0, "C")
        pdf.cell(30, altura, f"${precio:.2f}", 1, 1, "C")

    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"Total vendido: ${total_general:.2f}", 0, 1, "R")

    response = make_response(pdf.output(dest='S').encode('latin-1'))
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=reporte_ventas.pdf'

    return response
# ===============================
# REGISTRO / LOGIN 
# ===============================
@app.route("/registro", methods=["GET", "POST"])
def registro():

    if request.method == "POST":
        nombre = request.form["nombre"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

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

        if user and check_password_hash(user[3], password):

            usuario = Usuario(user[0], user[1], user[2], user[3], user[4])
            login_user(usuario)

            session["usuario"] = user[1]
            session["rol"] = user[4]

            if user[4] == "admin":
                return redirect(url_for("admin"))
            else:
                return redirect(url_for("index"))

        return render_template("login.html", error="Credenciales incorrectas")

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for("login"))

# ===============================
# RUN
# ===============================
if __name__ == "__main__":
    app.run(debug=True)