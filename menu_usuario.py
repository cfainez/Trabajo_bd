from conexion import ADMIN_CORREO, es_error_mongo, inicializar_base_datos, mostrar_error_conexion, pedidos, usuarios
from funciones import (
    autenticar_usuario,
    buscar_productos_por_categoria,
    buscar_productos_por_nombre,
    encriptar_clave,
    es_usuario_admin,
    mostrar_documentos,
    obtener_documentos,
    pedir_clave,
    pedir_no_vacio,
    productos,
    registrar_usuario,
)
from menu_admin import menu_super_admin


def _mostrar_carrito(carrito):
    print("\n=== CARRITO ===")
    if not carrito:
        print("El carrito esta vacio\n")
        return

    total = 0
    for i, item in enumerate(carrito, start=1):
        subtotal = item["precio"] * item["cantidad"]
        total += subtotal
        print(
            f"{i}. {item['nombre']} | precio: {item['precio']:.2f} | "
            f"cantidad: {item['cantidad']} | subtotal: {subtotal:.2f}"
        )

    print(f"Total: {total:.2f}\n")


def _modificar_perfil(usuario_actual):
    print("\n=== MODIFICAR PERFIL ===")
    nuevo_nombre = input("Nuevo nombre (enter para mantener): ").strip()
    cambiar_clave = input("Desea cambiar la contrasena? (s/n): ").strip().lower()

    cambios = {}
    if nuevo_nombre:
        cambios["nombre"] = nuevo_nombre

    if cambiar_clave == "s":
        nueva_clave = pedir_clave("Nueva contrasena: ")
        cambios["clave"] = encriptar_clave(nueva_clave)

    if not cambios:
        print("No se realizaron cambios\n")
        return

    usuarios.update_one({"correo": usuario_actual["correo"]}, {"$set": cambios})
    usuario_actual.update({k: v for k, v in cambios.items() if k != "clave"})
    print("Perfil actualizado correctamente\n")


def _eliminar_cuenta(usuario_actual):
    print("\n=== ELIMINAR CUENTA ===")
    confirmacion = input("Escriba ELIMINAR para confirmar: ").strip()
    if confirmacion != "ELIMINAR":
        print("Operacion cancelada\n")
        return False

    usuarios.delete_one({"correo": usuario_actual["correo"]})
    print("Cuenta eliminada correctamente\n")
    return True


def _consultar_producto():
    print("\n=== CONSULTAR PRODUCTO ===")
    print("1. Ver todos los productos")
    print("2. Buscar por nombre")
    print("3. Buscar por categoria")

    opcion = input("Seleccione: ").strip()
    if opcion == "1":
        mostrar_documentos("productos", obtener_documentos(productos))
    elif opcion == "2":
        termino = pedir_no_vacio("Ingrese nombre del producto: ")
        mostrar_documentos("resultados", buscar_productos_por_nombre(termino))
    elif opcion == "3":
        categoria = pedir_no_vacio("Ingrese categoria: ")
        mostrar_documentos("productos por categoria", buscar_productos_por_categoria(categoria))
    else:
        print("Opcion invalida\n")


def _agregar_producto_carrito(carrito):
    print("\n=== AGREGAR AL CARRITO ===")
    termino = pedir_no_vacio("Nombre del producto: ")
    resultados = buscar_productos_por_nombre(termino)

    if not resultados:
        print("No se encontraron productos con ese nombre\n")
        return

    mostrar_documentos("coincidencias", resultados)
    seleccion = pedir_no_vacio("Ingrese el numero del producto a agregar: ")

    try:
        indice = int(seleccion) - 1
        if indice < 0 or indice >= len(resultados):
            raise ValueError
    except ValueError:
        print("Seleccion invalida\n")
        return

    cantidad_texto = pedir_no_vacio("Cantidad: ")
    try:
        cantidad = int(cantidad_texto)
        if cantidad <= 0:
            raise ValueError
    except ValueError:
        print("Cantidad invalida\n")
        return

    producto = resultados[indice]
    nombre = producto.get("nombre", "producto")
    precio = float(producto.get("precio", 0))

    for item in carrito:
        if item["nombre"] == nombre:
            item["cantidad"] += cantidad
            print("Cantidad actualizada en el carrito\n")
            return

    carrito.append({"nombre": nombre, "precio": precio, "cantidad": cantidad})
    print("Producto agregado al carrito\n")


def _eliminar_producto_carrito(carrito):
    print("\n=== ELIMINAR DEL CARRITO ===")
    if not carrito:
        print("El carrito esta vacio\n")
        return

    _mostrar_carrito(carrito)
    seleccion = pedir_no_vacio("Ingrese el numero del producto a eliminar: ")

    try:
        indice = int(seleccion) - 1
        if indice < 0 or indice >= len(carrito):
            raise ValueError
    except ValueError:
        print("Seleccion invalida\n")
        return

    eliminado = carrito.pop(indice)
    print(f"Se elimino {eliminado['nombre']} del carrito\n")


def _mis_pedidos(usuario_actual):
    documentos = list(pedidos.find({"cliente": usuario_actual["correo"]}))
    mostrar_documentos("mis pedidos", documentos)


def menu_usuario_basico(usuario_actual):
    carrito = []

    while True:
        print("===== MENU USUARIO =====")
        print(f"Sesion actual: {usuario_actual['nombre']}")
        print("1. Modificar perfil")
        print("2. Eliminar cuenta")
        print("3. Consultar producto")
        print("4. Agregar producto al carrito")
        print("5. Eliminar producto del carrito")
        print("6. Visualizar carrito")
        print("7. Mis pedidos")
        print("8. Cerrar sesion")

        opcion = input("Seleccione: ").strip()

        if opcion == "1":
            _modificar_perfil(usuario_actual)
        elif opcion == "2":
            if _eliminar_cuenta(usuario_actual):
                return
        elif opcion == "3":
            _consultar_producto()
        elif opcion == "4":
            _agregar_producto_carrito(carrito)
        elif opcion == "5":
            _eliminar_producto_carrito(carrito)
        elif opcion == "6":
            _mostrar_carrito(carrito)
        elif opcion == "7":
            _mis_pedidos(usuario_actual)
        elif opcion == "8":
            print("Sesion cerrada\n")
            return
        else:
            print("Opcion invalida\n")


def menu_usuario(usuario_actual):
    if es_usuario_admin(usuario_actual):
        menu_super_admin(usuario_actual)
    else:
        menu_usuario_basico(usuario_actual)


def menu_principal():
    while True:
        print("================================")
        print("Bienvenido a Merciotech")
        print("================================\n")
        print("1. Iniciar sesion")
        print("2. Registrarse")
        print("3. Salir\n")
        print(f"Admin habilitado para: {ADMIN_CORREO}\n")

        opcion = input("Seleccione una opcion: ").strip()

        if opcion == "1":
            usuario = autenticar_usuario()
            if usuario:
                menu_usuario(usuario)
        elif opcion == "2":
            registrar_usuario()
        elif opcion == "3":
            print("Hasta luego\n")
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
