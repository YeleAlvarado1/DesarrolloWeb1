# ==============================
# CLASE PRODUCTO (POO)
# ==============================

class Producto:

    def __init__(self, id, nombre, cantidad, precio):
        self.id = id
        self.nombre = nombre
        self.cantidad = cantidad
        self.precio = precio


# ==============================
# CLASE INVENTARIO
# ==============================

class Inventario:

    def __init__(self):
        self.productos = {}

    def agregar_producto(self, producto):
        self.productos[producto.id] = producto

    def eliminar_producto(self, id):
        if id in self.productos:
            del self.productos[id]

    def buscar_producto(self, nombre):

        resultado = []

        for producto in self.productos.values():
            if nombre.lower() in producto.nombre.lower():
                resultado.append(producto)

        return resultado

    def mostrar_productos(self):
        return list(self.productos.values())


# ==============================
# PERSISTENCIA DE DATOS
# ==============================

import os
import json
import csv

# ruta base del proyecto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# carpeta data
DATA_DIR = os.path.join(BASE_DIR, "data")

# crear carpeta data si no existe
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# rutas de archivos
RUTA_TXT = os.path.join(DATA_DIR, "datos.txt")
RUTA_JSON = os.path.join(DATA_DIR, "datos.json")
RUTA_CSV = os.path.join(DATA_DIR, "datos.csv")


# ==============================
# GUARDAR EN TXT
# ==============================

def guardar_txt(nombre, precio):

    with open(RUTA_TXT, "a+", encoding="utf-8") as archivo:

        archivo.write(f"{nombre},{precio}\n")


# ==============================
# GUARDAR EN JSON
# ==============================

def guardar_json(nombre, precio):

    datos = {
        "nombre": nombre,
        "precio": precio
    }

    with open(RUTA_JSON, "a+", encoding="utf-8") as archivo:

        json.dump(datos, archivo)
        archivo.write("\n")


# ==============================
# GUARDAR EN CSV
# ==============================

def guardar_csv(nombre, precio):

    with open(RUTA_CSV, "a+", newline="", encoding="utf-8") as archivo:

        writer = csv.writer(archivo)

        writer.writerow([nombre, precio])


# ==============================
# LEER DATOS DESDE TXT
# ==============================

def leer_txt():

    datos = []

    if not os.path.exists(RUTA_TXT):
        return datos

    with open(RUTA_TXT, "r", encoding="utf-8") as archivo:

        for linea in archivo:

            if linea.strip() != "":

                partes = linea.strip().split(",")

                if len(partes) >= 2:

                    nombre = partes[0]
                    precio = partes[1]

                    datos.append({
                        "nombre": nombre,
                        "precio": precio
                    })

    return datos