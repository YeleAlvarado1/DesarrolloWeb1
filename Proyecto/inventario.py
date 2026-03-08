# Clase Producto (POO)

class Producto:

    def __init__(self, id, nombre, cantidad, precio):
        self.id = id
        self.nombre = nombre
        self.cantidad = cantidad
        self.precio = precio



# Clase Inventario

class Inventario:

    def __init__(self):

        # colección tipo diccionario
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