from pymongo import MongoClient
from pymongo.errors import PyMongoError

CONEXION = "mongodb+srv://administrador:admin12345@micluster.ckfwull.mongodb.net/?appName=micluster"
ADMIN_CORREO = "test@gmail.com"

cliente_mongo = MongoClient(CONEXION, serverSelectionTimeoutMS=5000)
db_merciotech = cliente_mongo["merciotech"]

usuarios = db_merciotech["usuarios"]
productos = db_merciotech["productos"]
pedidos = db_merciotech["pedidos"]
clientes = db_merciotech["clientes"]


def inicializar_base_datos():
    """Valida conexion y configura indice unico para correos."""
    cliente_mongo.admin.command("ping")
    usuarios.create_index("correo", unique=True)


def mostrar_error_conexion(error):
    print("\nNo se pudo conectar a MongoDB.")
    print(f"Detalle: {error}\n")
    print("Verifica que la conexion sea:")
    print(f"{CONEXION}\n")


def es_error_mongo(error):
    return isinstance(error, PyMongoError)


def main():
    from menu_usuario import main as main_menu

    main_menu()


if __name__ == "__main__":
    main()
