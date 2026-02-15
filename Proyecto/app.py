from flask import Flask 
app = Flask(__name__)
@app.route('/')
def hello_world():
    return 'Bienvenido a JAZ Climatización Instalación y mantenimiento de aire acondicionado'
# Ruta usuarios
@app.route("/usuarios")
def usuarios():
    return "Área de usuarios Consulta tu servicio de climatización."

# Ruta contacto
@app.route("/contacto")
def contacto():
    return "Contacto JAZ Climatización | Correo: jazclimatizacion@gmail.com | WhatsApp: +593 99 456 7890"

# Ruta dinámica para clientes
@app.route("/cliente/<nombre>")
def cliente(nombre):
    return f"Hola {nombre}, tu solicitud de servicio en JAZ Climatización está en proceso."
 
if __name__ == "__main__":
    app.run(debug=True)
