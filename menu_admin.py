from conexion import ADMIN_CORREO, clientes, pedidos, productos, usuarios
from funciones import (
    agregar_producto,
    buscar_productos_por_nombre,
    encriptar_clave,
    mostrar_documentos,
    obtener_documentos,
    pedir_clave,
    pedir_no_vacio,
)


def _seleccionar_por_indice(documentos, mensaje):
    if not documentos:
        return None

    for i, doc in enumerate(documentos, start=1):
        nombre = doc.get("nombre", doc.get("correo", "sin nombre"))
        print(f"{i}. {nombre}")

    seleccion = pedir_no_vacio(mensaje)
    try:
        indice = int(seleccion) - 1
        if indice < 0 or indice >= len(documentos):
            raise ValueError
    except ValueError:
        print("Seleccion invalida\n")
        return None

    return documentos[indice]


def _modificar_producto():
    print("\n=== MODIFICAR PRODUCTO ===")
    termino = pedir_no_vacio("Nombre del producto a modificar: ")
    candidatos = buscar_productos_por_nombre(termino)

    if not candidatos:
        print("No se encontraron productos\n")
        return

    producto = _seleccionar_por_indice(candidatos, "Seleccione producto: ")
    if not producto:
        return

    nuevo_nombre = input("Nuevo nombre (enter para mantener): ").strip()
    nueva_categoria = input("Nueva categoria (enter para mantener): ").strip()
    nuevo_precio = input("Nuevo precio (enter para mantener): ").strip()

    cambios = {}
    if nuevo_nombre:
        cambios["nombre"] = nuevo_nombre
    if nueva_categoria:
        cambios["categoria"] = nueva_categoria
    if nuevo_precio:
        try:
            cambios["precio"] = float(nuevo_precio)
        except ValueError:
            print("Precio invalido\n")
            return

    if not cambios:
        print("No se realizaron cambios\n")
        return

    productos.update_one({"_id": producto["_id"]}, {"$set": cambios})
    print("Producto actualizado correctamente\n")


def _eliminar_producto():
    print("\n=== ELIMINAR PRODUCTO ===")
    termino = pedir_no_vacio("Nombre del producto a eliminar: ")
    candidatos = buscar_productos_por_nombre(termino)

    if not candidatos:
        print("No se encontraron productos\n")
        return

    producto = _seleccionar_por_indice(candidatos, "Seleccione producto: ")
    if not producto:
        return

    confirmar = input("Escriba ELIMINAR para confirmar: ").strip()
    if confirmar != "ELIMINAR":
        print("Operacion cancelada\n")
        return

    productos.delete_one({"_id": producto["_id"]})
    print("Producto eliminado correctamente\n")


def _ingresar_cliente():
    print("\n=== INGRESAR CLIENTE ===")
    nombre = pedir_no_vacio("Nombre: ")
    correo = pedir_no_vacio("Correo: ").lower()
    telefono = input("Telefono: ").strip()

    if clientes.find_one({"correo": correo}):
        print("Ya existe un cliente con ese correo\n")
        return

    clientes.insert_one({"nombre": nombre, "correo": correo, "telefono": telefono})
    print("Cliente ingresado correctamente\n")


def _modificar_cliente():
    print("\n=== MODIFICAR CLIENTE ===")
    correo = pedir_no_vacio("Correo del cliente: ").lower()
    cliente = clientes.find_one({"correo": correo})

    if not cliente:
        print("Cliente no encontrado\n")
        return

    nuevo_nombre = input("Nuevo nombre (enter para mantener): ").strip()
    nuevo_telefono = input("Nuevo telefono (enter para mantener): ").strip()

    cambios = {}
    if nuevo_nombre:
        cambios["nombre"] = nuevo_nombre
    if nuevo_telefono:
        cambios["telefono"] = nuevo_telefono

    if not cambios:
        print("No se realizaron cambios\n")
        return

    clientes.update_one({"_id": cliente["_id"]}, {"$set": cambios})
    print("Cliente actualizado correctamente\n")


def _eliminar_cliente():
    print("\n=== ELIMINAR CLIENTE ===")
    correo = pedir_no_vacio("Correo del cliente: ").lower()
    cliente = clientes.find_one({"correo": correo})

    if not cliente:
        print("Cliente no encontrado\n")
        return

    confirmar = input("Escriba ELIMINAR para confirmar: ").strip()
    if confirmar != "ELIMINAR":
        print("Operacion cancelada\n")
        return

    clientes.delete_one({"_id": cliente["_id"]})
    print("Cliente eliminado correctamente\n")


def _ingresar_usuario_admin():
    print("\n=== INGRESAR USUARIO ===")
    nombre = pedir_no_vacio("Nombre: ")
    correo = pedir_no_vacio("Correo: ").lower()
    clave = pedir_clave("Contrasena: ")

    if correo == ADMIN_CORREO:
        print("Este correo esta reservado para el super admin\n")
        return

    if usuarios.find_one({"correo": correo}):
        print("El usuario ya existe\n")
        return

    usuarios.insert_one({"nombre": nombre, "correo": correo, "clave": encriptar_clave(clave)})
    print("Usuario creado correctamente\n")


def _modificar_usuario_admin():
    print("\n=== MODIFICAR USUARIO ===")
    correo = pedir_no_vacio("Correo del usuario: ").lower()
    usuario = usuarios.find_one({"correo": correo})

    if not usuario:
        print("Usuario no encontrado\n")
        return

    nuevo_nombre = input("Nuevo nombre (enter para mantener): ").strip()
    cambiar_clave = input("Cambiar contrasena? (s/n): ").strip().lower()

    cambios = {}
    if nuevo_nombre:
        cambios["nombre"] = nuevo_nombre
    if cambiar_clave == "s":
        cambios["clave"] = encriptar_clave(pedir_clave("Nueva contrasena: "))

    if not cambios:
        print("No se realizaron cambios\n")
        return

    usuarios.update_one({"_id": usuario["_id"]}, {"$set": cambios})
    print("Usuario actualizado correctamente\n")


def _eliminar_usuario_admin():
    print("\n=== ELIMINAR USUARIO ===")
    correo = pedir_no_vacio("Correo del usuario: ").lower()

    if correo == ADMIN_CORREO:
        print("No se puede eliminar al super admin\n")
        return

    usuario = usuarios.find_one({"correo": correo})
    if not usuario:
        print("Usuario no encontrado\n")
        return

    confirmar = input("Escriba ELIMINAR para confirmar: ").strip()
    if confirmar != "ELIMINAR":
        print("Operacion cancelada\n")
        return

    usuarios.delete_one({"_id": usuario["_id"]})
    print("Usuario eliminado correctamente\n")


def _reporte_estado_pedidos():
    print("\n=== REPORTE DE ESTADO DE PEDIDOS ===")
    reporte = list(pedidos.aggregate([{"$group": {"_id": "$estado", "cantidad": {"$sum": 1}}}]))

    if not reporte:
        print("No hay pedidos para reportar\n")
        return

    for item in reporte:
        estado = item.get("_id", "sin estado")
        cantidad = item.get("cantidad", 0)
        print(f"Estado: {estado} | Cantidad: {cantidad}")
    print()


def _visualizar_pedidos_por_estado():
    print("\n=== PEDIDOS POR ESTADO ===")
    estado = pedir_no_vacio("Ingrese estado (pendiente/completado/cancelado): ").lower()
    documentos = list(pedidos.find({"estado": estado}))
    mostrar_documentos(f"pedidos {estado}", documentos)


def menu_super_admin(usuario_actual):
    while True:
        print("===== MENU SUPER ADMIN =====")
        print(f"Sesion actual: {usuario_actual['nombre']} ({usuario_actual['correo']})")
        print("1. Productos")
        print("2. Clientes")
        print("3. Historial de pedidos")
        print("4. Historial de clientes")
        print("5. Reporte de estado de pedidos")
        print("6. Administrar usuarios")
        print("7. Visualizar pedidos por estado")
        print("8. Cerrar sesion")

        opcion = input("Seleccione: ").strip()

        if opcion == "1":
            while True:
                print("\n--- PRODUCTOS ---")
                print("1. Ingresar productos")
                print("2. Modificar productos")
                print("3. Eliminar productos")
                print("4. Volver")
                sub = input("Seleccione: ").strip()
                if sub == "1":
                    agregar_producto()
                elif sub == "2":
                    _modificar_producto()
                elif sub == "3":
                    _eliminar_producto()
                elif sub == "4":
                    break
                else:
                    print("Opcion invalida\n")
        elif opcion == "2":
            while True:
                print("\n--- CLIENTES ---")
                print("1. Ingresar cliente")
                print("2. Modificar cliente")
                print("3. Eliminar cliente")
                print("4. Volver")
                sub = input("Seleccione: ").strip()
                if sub == "1":
                    _ingresar_cliente()
                elif sub == "2":
                    _modificar_cliente()
                elif sub == "3":
                    _eliminar_cliente()
                elif sub == "4":
                    break
                else:
                    print("Opcion invalida\n")
        elif opcion == "3":
            mostrar_documentos("historial de pedidos", obtener_documentos(pedidos))
        elif opcion == "4":
            mostrar_documentos("historial de clientes", obtener_documentos(clientes))
        elif opcion == "5":
            _reporte_estado_pedidos()
        elif opcion == "6":
            while True:
                print("\n--- ADMINISTRAR USUARIOS ---")
                print("1. Ingresar usuario")
                print("2. Modificar usuario")
                print("3. Eliminar usuario")
                print("4. Volver")
                sub = input("Seleccione: ").strip()
                if sub == "1":
                    _ingresar_usuario_admin()
                elif sub == "2":
                    _modificar_usuario_admin()
                elif sub == "3":
                    _eliminar_usuario_admin()
                elif sub == "4":
                    break
                else:
                    print("Opcion invalida\n")
        elif opcion == "7":
            _visualizar_pedidos_por_estado()
        elif opcion == "8":
            print("Sesion de super admin cerrada\n")
            return
        else:
            print("Opcion invalida\n")


def main():
    from menu_usuario import main as main_menu

    main_menu()


if __name__ == "__main__":
    main()
