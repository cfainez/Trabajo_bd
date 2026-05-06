import bcrypt
import re
import json
from getpass import getpass
from conexion import ADMIN_CORREO, productos, usuarios

TAMANO_PAGINA = 10
PRIORIDAD_COLUMNAS = [
    "_id",
    "id",
    "nombre",
    "categoria",
    "descripcion",
    "precio",
    "correo",
    "cliente",
    "estado",
    "fecha",
    "total",
]


def pedir_no_vacio(mensaje):
    while True:
        valor = input(mensaje).strip()
        if valor:
            return valor
        print("El campo no puede estar vacio")


def _leer_clave_enmascarada(mensaje):
    try:
        import msvcrt
    except ImportError:
        return getpass(mensaje)

    print(mensaje, end="", flush=True)
    caracteres = []

    while True:
        tecla = msvcrt.getwch()

        if tecla in ("\r", "\n"):
            print()
            break

        if tecla == "\003":
            raise KeyboardInterrupt

        if tecla == "\b":
            if caracteres:
                caracteres.pop()
                print("\b \b", end="", flush=True)
            continue

        if tecla in ("\x00", "\xe0"):
            msvcrt.getwch()
            continue

        caracteres.append(tecla)
        print("*", end="", flush=True)

    return "".join(caracteres)


def pedir_clave(mensaje):
    while True:
        valor = _leer_clave_enmascarada(mensaje).strip()
        if valor:
            return valor
        print("La contrasena no puede estar vacia")


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
    clave = pedir_clave("Contrasena: ")

    if correo == ADMIN_CORREO:
        print("Este correo esta reservado para el administrador\n")
        return

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
    clave = pedir_clave("Contrasena: ")

    usuario = usuarios.find_one({"correo": correo}, {"nombre": 1, "clave": 1, "correo": 1})
    if not usuario:
        print("Usuario no encontrado\n")
        return None

    if validar_clave(clave, usuario["clave"]):
        print(f"\nBienvenido {usuario['nombre']}\n")
        return usuario

    print("Contrasena incorrecta\n")
    return None


def es_usuario_admin(usuario):
    return usuario.get("correo", "").lower() == ADMIN_CORREO


def obtener_documentos(coleccion):
    return list(coleccion.find({}))


def buscar_productos_por_nombre(termino):
    patron = re.escape(termino)
    return list(productos.find({"nombre": {"$regex": patron, "$options": "i"}}))


def buscar_productos_por_categoria(categoria):
    patron = re.escape(categoria)
    return list(productos.find({"categoria": {"$regex": f"^{patron}$", "$options": "i"}}))


def agregar_producto():
    print("\n=== AGREGAR PRODUCTO ===")
    nombre = pedir_no_vacio("Nombre del producto: ")
    categoria = pedir_no_vacio("Categoria: ")
    precio = pedir_no_vacio("Precio: ")

    try:
        precio = float(precio)
    except ValueError:
        print("Precio invalido. Debe ser un numero.\n")
        return

    productos.insert_one({
        "nombre": nombre,
        "categoria": categoria,
        "precio": precio
    })
    print("Producto agregado correctamente\n")


def _texto_celda(valor, max_largo=28):
    if isinstance(valor, (dict, list, tuple)):
        texto = json.dumps(valor, ensure_ascii=True)
    else:
        texto = str(valor)

    if len(texto) > max_largo:
        return texto[: max_largo - 3] + "..."
    return texto


def _ancho_columnas(columnas, filas):
    anchos = {col: len(col) for col in columnas}
    for fila in filas:
        for col in columnas:
            anchos[col] = max(anchos[col], len(fila.get(col, "")))
    return anchos


def _ordenar_columnas(documentos):
    claves = {clave for doc in documentos for clave in doc.keys()}
    primeras = [col for col in PRIORIDAD_COLUMNAS if col in claves]
    restantes = sorted(claves - set(primeras))
    return primeras + restantes


def _imprimir_tabla(documentos, columnas):
    if not columnas:
        print("No hay campos para mostrar")
        return

    filas = []
    for doc in documentos:
        fila = {}
        for col in columnas:
            fila[col] = _texto_celda(doc.get(col, ""))
        filas.append(fila)

    anchos = _ancho_columnas(columnas, filas)
    separador = "+-" + "-+-".join("-" * anchos[col] for col in columnas) + "-+"
    encabezado = "| " + " | ".join(col.ljust(anchos[col]) for col in columnas) + " |"

    print(separador)
    print(encabezado)
    print(separador)
    for fila in filas:
        linea = "| " + " | ".join(fila[col].ljust(anchos[col]) for col in columnas) + " |"
        print(linea)
    print(separador)


def mostrar_documentos(nombre_coleccion, documentos):
    print(f"\n=== {nombre_coleccion.upper()} ===")
    if not documentos:
        print("No hay datos en esta coleccion\n")
        return

    columnas = _ordenar_columnas(documentos)
    total = len(documentos)
    total_paginas = (total + TAMANO_PAGINA - 1) // TAMANO_PAGINA

    pagina = 1
    inicio = 0
    while inicio < total:
        fin = min(inicio + TAMANO_PAGINA, total)
        print(f"Pagina {pagina}/{total_paginas} - mostrando {inicio + 1} a {fin} de {total}")
        _imprimir_tabla(documentos[inicio:fin], columnas)

        if fin >= total:
            break

        continuar = input("Mostrar siguiente pagina? (s/n): ").strip().lower()
        if continuar != "s":
            break

        inicio = fin
        pagina += 1

    print()


def main():
    from menu_usuario import main as main_menu

    main_menu()


if __name__ == "__main__":
    main()