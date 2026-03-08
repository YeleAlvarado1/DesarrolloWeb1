import sqlite3

conexion = sqlite3.connect("inventario.db")

cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    cantidad INTEGER,
    precio REAL
)
""")

conexion.commit()
conexion.close()

print("Tabla productos creada correctamente")