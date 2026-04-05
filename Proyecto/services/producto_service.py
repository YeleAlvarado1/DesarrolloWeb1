from conexion.conexion import get_connection

# ===============================
# OBTENER TODOS LOS PRODUCTOS
# ===============================
def obtener_productos():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, cantidad, precio, estado FROM productos")
    productos = cursor.fetchall()
    conn.close()
    return productos


# ===============================
# INSERTAR PRODUCTO
# ===============================
def insertar_producto(nombre, cantidad, precio):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO productos(nombre,cantidad,precio) VALUES (%s,%s,%s)",
        (nombre, cantidad, precio)
    )

    conn.commit()
    conn.close()


# ===============================
# ELIMINAR PRODUCTO
# ===============================
def eliminar_producto(id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM productos WHERE id=%s", (id,))

    conn.commit()
    conn.close()


# ===============================
# OBTENER PRODUCTO POR ID
# ===============================
def obtener_producto_por_id(id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM productos WHERE id=%s", (id,))
    producto = cursor.fetchone()

    conn.close()
    return producto


# ===============================
# ACTUALIZAR PRODUCTO
# ===============================
def actualizar_producto(id, nombre, cantidad, precio):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE productos SET nombre=%s, cantidad=%s, precio=%s WHERE id=%s",
        (nombre, cantidad, precio, id)
    )

    conn.commit()
    conn.close()
    