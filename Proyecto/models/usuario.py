from flask_login import UserMixin

class Usuario(UserMixin):
    def __init__(self, id, nombre, email, password):
        self.id = id
        self.nombre = nombre
        self.email = email
        self.password = password