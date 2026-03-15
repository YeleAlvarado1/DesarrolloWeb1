import mysql.connector

def get_connection():

    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",   # pon tu contraseña si tienes
        database="jaz_climatizacion",
        port=3307
    )

    return connection