import json

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

from funciones import (
    autenticar_usuario,
    buscar_productos_por_categoria,
    buscar_productos_por_nombre,
    clientes,
    es_error_mongo,
    inicializar_base_datos,
    mostrar_error_conexion,
    obtener_documentos,
    pedidos,
    pedir_no_vacio,
    productos,
    registrar_usuario,
)


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


def menu_colecciones():
    while True:
        print("\n=== COLECCIONES (MERCIOTECH) ===")
        print("1. Ver productos")
        print("2. Ver pedidos")
        print("3. Ver clientes")
        print("4. Volver")

        opcion = input("Seleccione coleccion: ").strip()

        if opcion == "1":
            mostrar_documentos("productos", obtener_documentos(productos))
        elif opcion == "2":
            mostrar_documentos("pedidos", obtener_documentos(pedidos))
        elif opcion == "3":
            mostrar_documentos("clientes", obtener_documentos(clientes))
        elif opcion == "4":
            return
        else:
            print("Opcion invalida\n")


def menu_usuario(usuario_actual):
    while True:
        print("===== MERCIOTECH =====")
        print(f"Sesion actual: {usuario_actual['nombre']}")
        print("1. Ver colecciones")
        print("2. Buscar producto por nombre")
        print("3. Ver productos por categoria")
        print("4. Cerrar sesion")

        opcion = input("Seleccione: ").strip()

        if opcion == "1":
            menu_colecciones()
        elif opcion == "2":
            termino = pedir_no_vacio("Ingrese nombre del producto: ")
            resultados = buscar_productos_por_nombre(termino)
            mostrar_documentos("resultados", resultados)
        elif opcion == "3":
            categoria = pedir_no_vacio("Ingrese categoria: ")
            resultados = buscar_productos_por_categoria(categoria)
            mostrar_documentos("productos por categoria", resultados)
        elif opcion == "4":
            print("Sesion cerrada\n")
            return
        else:
            print("Opcion invalida\n")


def menu_principal():
    while True:
        print("================================")
        print("Bienvenido a Merciotech")
        print("================================\n")
        print("1. Iniciar sesion")
        print("2. Registrarse")
        print("3. Salir\n")

        opcion = input("Seleccione una opcion: ").strip()

        if opcion == "1":
            usuario = autenticar_usuario()
            if usuario:
                menu_usuario(usuario)
        elif opcion == "2":
            registrar_usuario()
        elif opcion == "3":
            print("Hasta luego")
            return
        else:
            print("Opcion no valida\n")


def main():
    try:
        inicializar_base_datos()
        menu_principal()
    except Exception as error:
        if es_error_mongo(error):
            mostrar_error_conexion(error)
        else:
            raise


if __name__ == "__main__":
    main()


#productos
# ingresar productos 
# modificar productos
# eliminar productos

#reporte
# consultar historial de pedidos
# cosultar historial de clientes (verificar la modificacion de datos personales)
# generar reporte de estado de pedidos (pendiente, completado, cancelado)
#  



#cliente
# consulta de historial de clientes
# administrar usuarios (ingresar, modificar, eliminar)
# visualizar pedidos por estado (pendiente, completado, cancelado)            