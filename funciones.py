from pymongo import MongoClient
from pymongo.errors import PyMongoError
import bcrypt
import re

CONEXION = "mongodb://localhost:27017/"
cliente_mongo = MongoClient(CONEXION, serverSelectionTimeoutMS=5000)
db_merciotech = cliente_mongo["merciotech"]

usuarios = db_merciotech["usuarios"]
productos = db_merciotech["productos"]
pedidos = db_merciotech["pedidos"]
clientes = db_merciotech["clientes"]

# funciones para autenticacion, gestion de usuarios, busqueda de productos y manejo de errores relacionados con la conexion a MongoDB.
# Estas funciones se utilizan en los menus para permitir al usuario interactuar con la base de datos de manera segura y eficiente,
# mostrando los datos de forma legible y manejando posibles errores de conexion.
def inicializar_base_datos():
    """Valida conexion y configura indice unico para correos."""
    cliente_mongo.admin.command("ping")
    usuarios.create_index("correo", unique=True)


def pedir_no_vacio(mensaje):
    while True:
        valor = input(mensaje).strip()
        if valor:
            return valor
        print("El campo no puede estar vacio")


def encriptar_clave(clave):
    return bcrypt.hashpw(clave.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def validar_clave(clave_ingresada, clave_guardada):
    if isinstance(clave_guardada, str):
        hash_bytes = clave_guardada.encode("utf-8")
    else:
        hash_bytes = bytes(clave_guardada)
    return bcrypt.checkpw(clave_ingresada.encode("utf-8"), hash_bytes)


def registrar_usuario():
    print("\n=== REGISTRO ===")

    nombre = pedir_no_vacio("Nombre: ")
    correo = pedir_no_vacio("Correo: ").lower()
    clave = pedir_no_vacio("Contrasena: ")

    if usuarios.find_one({"correo": correo}):
        print("El correo ya esta registrado\n")
        return

    usuarios.insert_one(
        {
            "nombre": nombre,
            "correo": correo,
            "clave": encriptar_clave(clave),
        }
    )
    print("Usuario registrado correctamente\n")


def autenticar_usuario():
    print("\n=== INICIAR SESION ===")

    correo = pedir_no_vacio("Correo: ").lower()
    clave = pedir_no_vacio("Contrasena: ")

    usuario = usuarios.find_one({"correo": correo}, {"nombre": 1, "clave": 1})
    if not usuario:
        print("Usuario no encontrado\n")
        return None

    if validar_clave(clave, usuario["clave"]):
        print(f"\nBienvenido {usuario['nombre']}\n")
        return usuario

    print("Contrasena incorrecta\n")
    return None


def obtener_documentos(coleccion):
    return list(coleccion.find({}))


def buscar_productos_por_nombre(termino):
    patron = re.escape(termino)
    return list(productos.find({"nombre": {"$regex": patron, "$options": "i"}}))


def buscar_productos_por_categoria(categoria):
    patron = re.escape(categoria)
    return list(productos.find({"categoria": {"$regex": f"^{patron}$", "$options": "i"}}))


def mostrar_error_conexion(error):
    print("\nNo se pudo conectar a MongoDB (Compass).")
    print(f"Detalle: {error}\n")
    print("Verifica que MongoDB este iniciado y que la conexion sea:")
    print(f"{CONEXION}\n")


def es_error_mongo(error):
    return isinstance(error, PyMongoError)
