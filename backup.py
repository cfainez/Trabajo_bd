"""
Script de copia de seguridad para la base de datos merciotech.
Exporta todas las colecciones a archivos JSON con fecha y hora.
"""

import json
import os
from datetime import datetime
from bson import ObjectId
from conexion import clientes, es_error_mongo, pedidos, productos, usuarios


COLECCIONES = {
    "usuarios": usuarios,
    "productos": productos,
    "pedidos": pedidos,
    "clientes": clientes,
}


def _serializar(obj):
    """Convierte tipos de MongoDB (ObjectId, datetime) a string para JSON."""
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Tipo no serializable: {type(obj)}")


def exportar_coleccion(nombre, coleccion, carpeta):
    """Exporta una coleccion a un archivo JSON."""
    documentos = list(coleccion.find())
    ruta = os.path.join(carpeta, f"{nombre}.json")

    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(documentos, f, ensure_ascii=False, indent=2, default=_serializar)

    return len(documentos)


def realizar_backup():
    """Realiza el backup completo de la base de datos."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    carpeta = os.path.join("backups", timestamp)
    os.makedirs(carpeta, exist_ok=True)

    print(f"\n=== COPIA DE SEGURIDAD ===")
    print(f"Destino: {carpeta}")
    print()

    total_docs = 0
    errores = []

    for nombre, coleccion in COLECCIONES.items():
        try:
            cantidad = exportar_coleccion(nombre, coleccion, carpeta)
            print(f"  ✓ {nombre}: {cantidad} documentos exportados")
            total_docs += cantidad
        except Exception as e:
            print(f"  ✗ {nombre}: error al exportar ({e})")
            errores.append(nombre)

    print()
    print(f"Backup completado: {total_docs} documentos en {len(COLECCIONES) - len(errores)}/{len(COLECCIONES)} colecciones")
    if errores:
        print(f"Colecciones con error: {', '.join(errores)}")
    print(f"Carpeta: {os.path.abspath(carpeta)}\n")


def listar_backups():
    """Muestra los backups disponibles."""
    if not os.path.exists("backups"):
        print("No hay backups disponibles\n")
        return

    carpetas = sorted(os.listdir("backups"), reverse=True)
    if not carpetas:
        print("No hay backups disponibles\n")
        return

    print("\n=== BACKUPS DISPONIBLES ===")
    for i, nombre in enumerate(carpetas, 1):
        ruta = os.path.join("backups", nombre)
        archivos = [f for f in os.listdir(ruta) if f.endswith(".json")]
        print(f"{i}. {nombre} ({len(archivos)} colecciones)")
    print()


def menu_backup():
    while True:
        print("===== COPIA DE SEGURIDAD =====")
        print("1. Realizar backup ahora")
        print("2. Ver backups disponibles")
        print("3. Salir")

        opcion = input("Seleccione: ").strip()

        if opcion == "1":
            try:
                realizar_backup()
            except Exception as e:
                if es_error_mongo(e):
                    print(f"\nError de conexion a MongoDB: {e}\n")
                else:
                    print(f"\nError inesperado: {e}\n")
        elif opcion == "2":
            listar_backups()
        elif opcion == "3":
            return
        else:
            print("Opcion invalida\n")


def main():
    from conexion import inicializar_base_datos, mostrar_error_conexion, es_error_mongo

    try:
        inicializar_base_datos()
    except Exception as e:
        mostrar_error_conexion(e)
        return

    menu_backup()


if __name__ == "__main__":
    main()
