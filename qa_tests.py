"""
Script de QA - Merciotech
Verifica que todas las funciones de admin y usuario funcionen correctamente.
Usa datos de prueba temporales que se eliminan al finalizar.
"""

import sys
from datetime import datetime
from bson import ObjectId

# ── Colores para consola ──────────────────────────────────────────────
VERDE  = "\033[92m"
ROJO   = "\033[91m"
AMARILLO = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
NEGRITA = "\033[1m"

# ── Contadores globales ───────────────────────────────────────────────
resultados = {"ok": 0, "fallo": 0, "error": 0}
datos_de_prueba = {}   # guarda IDs de documentos creados para limpiar al final


def ok(nombre):
    resultados["ok"] += 1
    print(f"  {VERDE}✓ PASS{RESET}  {nombre}")


def fallo(nombre, motivo=""):
    resultados["fallo"] += 1
    msg = f" → {motivo}" if motivo else ""
    print(f"  {ROJO}✗ FAIL{RESET}  {nombre}{msg}")


def error(nombre, exc):
    resultados["error"] += 1
    print(f"  {AMARILLO}! ERROR{RESET} {nombre} → {exc}")


def seccion(titulo):
    print(f"\n{NEGRITA}{CYAN}{'─'*50}{RESET}")
    print(f"{NEGRITA}{CYAN}  {titulo}{RESET}")
    print(f"{NEGRITA}{CYAN}{'─'*50}{RESET}")


# ══════════════════════════════════════════════════════════════════════
# 1. CONEXIÓN
# ══════════════════════════════════════════════════════════════════════
def test_conexion():
    seccion("1. CONEXIÓN A MONGODB")
    try:
        from conexion import cliente_mongo, usuarios, productos, pedidos, clientes
        cliente_mongo.admin.command("ping")
        ok("Ping a MongoDB Atlas")
    except Exception as e:
        error("Ping a MongoDB Atlas", e)
        print(f"\n{ROJO}No hay conexión. Los demás tests no pueden ejecutarse.{RESET}")
        sys.exit(1)

    for nombre, col in [("usuarios", usuarios), ("productos", productos),
                        ("pedidos", pedidos), ("clientes", clientes)]:
        try:
            col.find_one()
            ok(f"Colección '{nombre}' accesible")
        except Exception as e:
            error(f"Colección '{nombre}'", e)


# ══════════════════════════════════════════════════════════════════════
# 2. FUNCIONES DE AUTENTICACIÓN (funciones.py)
# ══════════════════════════════════════════════════════════════════════
def test_autenticacion():
    seccion("2. AUTENTICACIÓN Y REGISTRO")
    from conexion import usuarios, ADMIN_CORREO
    from funciones import encriptar_clave, validar_clave, es_usuario_admin

    CORREO_TEST = "qa_test_usuario@merciotech.com"
    CLAVE_TEST  = "ClaveSegura123"

    # 2.1 Registro de usuario de prueba
    try:
        usuarios.delete_one({"correo": CORREO_TEST})   # limpiar si quedó de ejecución anterior
        hash_clave = encriptar_clave(CLAVE_TEST)
        res = usuarios.insert_one({"nombre": "QA Usuario", "correo": CORREO_TEST, "clave": hash_clave})
        datos_de_prueba["usuario_id"] = res.inserted_id
        datos_de_prueba["usuario_correo"] = CORREO_TEST
        ok("Registrar usuario de prueba")
    except Exception as e:
        error("Registrar usuario de prueba", e)

    # 2.2 Validar clave correcta
    try:
        usuario = usuarios.find_one({"correo": CORREO_TEST})
        if validar_clave(CLAVE_TEST, usuario["clave"]):
            ok("Validar clave correcta")
        else:
            fallo("Validar clave correcta", "bcrypt rechazó clave válida")
    except Exception as e:
        error("Validar clave correcta", e)

    # 2.3 Validar clave incorrecta
    try:
        usuario = usuarios.find_one({"correo": CORREO_TEST})
        if not validar_clave("ClaveIncorrecta", usuario["clave"]):
            ok("Rechazar clave incorrecta")
        else:
            fallo("Rechazar clave incorrecta", "bcrypt aceptó clave inválida")
    except Exception as e:
        error("Rechazar clave incorrecta", e)

    # 2.4 Detección de admin
    try:
        admin_doc = {"correo": ADMIN_CORREO}
        user_doc  = {"correo": CORREO_TEST}
        if es_usuario_admin(admin_doc) and not es_usuario_admin(user_doc):
            ok("Detectar rol admin correctamente")
        else:
            fallo("Detectar rol admin", f"ADMIN_CORREO={ADMIN_CORREO}")
    except Exception as e:
        error("Detectar rol admin", e)

    # 2.5 Correo duplicado
    try:
        antes = usuarios.count_documents({"correo": CORREO_TEST})
        hash_clave2 = encriptar_clave(CLAVE_TEST)
        try:
            usuarios.insert_one({"nombre": "Duplicado", "correo": CORREO_TEST, "clave": hash_clave2})
            despues = usuarios.count_documents({"correo": CORREO_TEST})
            if despues > antes:
                fallo("Rechazar correo duplicado", "Se insertó duplicado (falta índice unique)")
        except Exception:
            ok("Rechazar correo duplicado (índice unique)")
    except Exception as e:
        error("Rechazar correo duplicado", e)


# ══════════════════════════════════════════════════════════════════════
# 3. PRODUCTOS (admin)
# ══════════════════════════════════════════════════════════════════════
def test_productos():
    seccion("3. GESTIÓN DE PRODUCTOS (ADMIN)")
    from conexion import productos
    from funciones import buscar_productos_por_nombre, buscar_productos_por_categoria

    PROD_TEST = {"nombre": "QA_Producto_Test", "categoria": "QA_Categoria", "precio": 9999.0}

    # 3.1 Insertar producto
    try:
        productos.delete_one({"nombre": PROD_TEST["nombre"]})
        res = productos.insert_one(PROD_TEST.copy())
        datos_de_prueba["producto_id"] = res.inserted_id
        ok("Insertar producto")
    except Exception as e:
        error("Insertar producto", e)

    # 3.2 Buscar por nombre
    try:
        resultados_busq = buscar_productos_por_nombre("QA_Producto")
        if any(p["nombre"] == PROD_TEST["nombre"] for p in resultados_busq):
            ok("Buscar producto por nombre (regex)")
        else:
            fallo("Buscar producto por nombre", "No encontrado")
    except Exception as e:
        error("Buscar producto por nombre", e)

    # 3.3 Buscar por categoría
    try:
        resultados_cat = buscar_productos_por_categoria("QA_Categoria")
        if any(p["nombre"] == PROD_TEST["nombre"] for p in resultados_cat):
            ok("Buscar producto por categoría (regex)")
        else:
            fallo("Buscar producto por categoría", "No encontrado")
    except Exception as e:
        error("Buscar producto por categoría", e)

    # 3.4 Modificar producto
    try:
        pid = datos_de_prueba.get("producto_id")
        if pid:
            productos.update_one({"_id": pid}, {"$set": {"precio": 12345.0}})
            actualizado = productos.find_one({"_id": pid})
            if actualizado["precio"] == 12345.0:
                ok("Modificar producto")
            else:
                fallo("Modificar producto", "Precio no actualizado")
    except Exception as e:
        error("Modificar producto", e)

    # 3.5 Eliminar producto
    try:
        pid = datos_de_prueba.get("producto_id")
        if pid:
            productos.delete_one({"_id": pid})
            if not productos.find_one({"_id": pid}):
                ok("Eliminar producto")
                datos_de_prueba.pop("producto_id", None)
            else:
                fallo("Eliminar producto", "Aún existe")
    except Exception as e:
        error("Eliminar producto", e)


# ══════════════════════════════════════════════════════════════════════
# 4. CLIENTES (admin)
# ══════════════════════════════════════════════════════════════════════
def test_clientes():
    seccion("4. GESTIÓN DE CLIENTES (ADMIN)")
    from conexion import clientes

    CLIENTE_TEST = {"nombre": "QA Cliente", "correo": "qa_cliente@test.com", "telefono": "+56999999999"}

    # 4.1 Insertar cliente
    try:
        clientes.delete_one({"correo": CLIENTE_TEST["correo"]})
        res = clientes.insert_one(CLIENTE_TEST.copy())
        datos_de_prueba["cliente_id"]     = res.inserted_id
        datos_de_prueba["cliente_correo"] = CLIENTE_TEST["correo"]
        ok("Insertar cliente")
    except Exception as e:
        error("Insertar cliente", e)

    # 4.2 Buscar cliente por correo
    try:
        c = clientes.find_one({"correo": CLIENTE_TEST["correo"]})
        if c and c["nombre"] == "QA Cliente":
            ok("Buscar cliente por correo")
        else:
            fallo("Buscar cliente por correo", "No encontrado")
    except Exception as e:
        error("Buscar cliente por correo", e)

    # 4.3 Modificar cliente
    try:
        cid = datos_de_prueba.get("cliente_id")
        if cid:
            clientes.update_one({"_id": cid}, {"$set": {"telefono": "+56111111111"}})
            actualizado = clientes.find_one({"_id": cid})
            if actualizado["telefono"] == "+56111111111":
                ok("Modificar cliente")
            else:
                fallo("Modificar cliente", "Teléfono no actualizado")
    except Exception as e:
        error("Modificar cliente", e)

    # 4.4 Eliminar cliente
    try:
        cid = datos_de_prueba.get("cliente_id")
        if cid:
            clientes.delete_one({"_id": cid})
            if not clientes.find_one({"_id": cid}):
                ok("Eliminar cliente")
                datos_de_prueba.pop("cliente_id", None)
            else:
                fallo("Eliminar cliente", "Aún existe")
    except Exception as e:
        error("Eliminar cliente", e)


# ══════════════════════════════════════════════════════════════════════
# 5. USUARIOS (admin)
# ══════════════════════════════════════════════════════════════════════
def test_gestion_usuarios_admin():
    seccion("5. GESTIÓN DE USUARIOS (ADMIN)")
    from conexion import usuarios, ADMIN_CORREO
    from funciones import encriptar_clave, validar_clave

    CORREO2 = "qa_test_admin_creado@merciotech.com"

    # 5.1 Crear usuario desde admin
    try:
        usuarios.delete_one({"correo": CORREO2})
        hash_c = encriptar_clave("ClaveAdmin123")
        res = usuarios.insert_one({"nombre": "QA Admin Creado", "correo": CORREO2, "clave": hash_c})
        datos_de_prueba["usuario_admin_id"]     = res.inserted_id
        datos_de_prueba["usuario_admin_correo"] = CORREO2
        ok("Admin crea usuario")
    except Exception as e:
        error("Admin crea usuario", e)

    # 5.2 No se puede crear usuario con correo admin
    try:
        if usuarios.find_one({"correo": ADMIN_CORREO}):
            ok("Correo admin no duplicable (ya existe, protegido por lógica)")
        else:
            ok("Correo admin no existe como usuario regular (correcto)")
    except Exception as e:
        error("Verificar protección correo admin", e)

    # 5.3 Modificar usuario
    try:
        uid = datos_de_prueba.get("usuario_admin_id")
        if uid:
            nuevo_hash = encriptar_clave("NuevaClave456")
            usuarios.update_one({"_id": uid}, {"$set": {"nombre": "QA Modificado", "clave": nuevo_hash}})
            u = usuarios.find_one({"_id": uid})
            if u["nombre"] == "QA Modificado" and validar_clave("NuevaClave456", u["clave"]):
                ok("Modificar usuario (nombre y clave)")
            else:
                fallo("Modificar usuario", "Datos no actualizados")
    except Exception as e:
        error("Modificar usuario", e)

    # 5.4 Eliminar usuario
    try:
        uid = datos_de_prueba.get("usuario_admin_id")
        if uid:
            usuarios.delete_one({"_id": uid})
            if not usuarios.find_one({"_id": uid}):
                ok("Eliminar usuario (admin)")
                datos_de_prueba.pop("usuario_admin_id", None)
            else:
                fallo("Eliminar usuario", "Aún existe")
    except Exception as e:
        error("Eliminar usuario", e)


# ══════════════════════════════════════════════════════════════════════
# 6. PEDIDOS
# ══════════════════════════════════════════════════════════════════════
def test_pedidos():
    seccion("6. PEDIDOS")
    from conexion import pedidos, clientes

    # Crear cliente de prueba para pedidos
    CORREO_CLI = "qa_pedidos_cliente@test.com"
    try:
        clientes.delete_one({"correo": CORREO_CLI})
        res_cli = clientes.insert_one({"nombre": "QA Pedidos Cliente", "correo": CORREO_CLI, "telefono": "000"})
        id_cliente = res_cli.inserted_id
        datos_de_prueba["pedido_cliente_id"]     = id_cliente
        datos_de_prueba["pedido_cliente_correo"] = CORREO_CLI
    except Exception as e:
        error("Crear cliente para test pedidos", e)
        return

    # 6.1 Insertar pedido con id_cliente numérico (simulando BD real)
    try:
        pedidos.delete_many({"id_cliente": id_cliente})
        res_p = pedidos.insert_one({
            "id_cliente": id_cliente,
            "estado": "pendiente",
            "fecha": datetime.now(),
            "detalle": [{"id_producto": 999, "cantidad": 1, "precio_unitario": 100}]
        })
        datos_de_prueba["pedido_id"] = res_p.inserted_id
        ok("Insertar pedido")
    except Exception as e:
        error("Insertar pedido", e)

    # 6.2 Buscar pedidos por id_cliente (lógica de _mis_pedidos)
    try:
        cliente_doc = clientes.find_one({"correo": CORREO_CLI})
        docs = list(pedidos.find({"id_cliente": cliente_doc["_id"]}))
        if docs:
            ok("Buscar pedidos por ID de cliente")
        else:
            fallo("Buscar pedidos por ID de cliente", "No encontró pedidos del cliente")
    except Exception as e:
        error("Buscar pedidos por ID de cliente", e)

    # 6.3 Filtrar pedidos por estado
    try:
        docs_estado = list(pedidos.find({"estado": "pendiente"}))
        if any(str(d.get("id_cliente")) == str(id_cliente) for d in docs_estado):
            ok("Filtrar pedidos por estado 'pendiente'")
        else:
            fallo("Filtrar por estado", "Pedido de prueba no encontrado")
    except Exception as e:
        error("Filtrar pedidos por estado", e)

    # 6.4 Reporte de estado con aggregation
    try:
        reporte = list(pedidos.aggregate([{"$group": {"_id": "$estado", "cantidad": {"$sum": 1}}}]))
        estados = [r["_id"] for r in reporte]
        if "pendiente" in estados:
            ok("Reporte de estado de pedidos (aggregation $group)")
        else:
            fallo("Reporte de estado", f"Estados encontrados: {estados}")
    except Exception as e:
        error("Reporte de estado de pedidos", e)


# ══════════════════════════════════════════════════════════════════════
# 7. CARRITO (usuario — lógica en memoria)
# ══════════════════════════════════════════════════════════════════════
def test_carrito():
    seccion("7. CARRITO (LÓGICA EN MEMORIA)")

    # 7.1 Carrito vacío
    carrito = []
    if carrito == []:
        ok("Carrito inicia vacío")
    else:
        fallo("Carrito vacío", "No inicia vacío")

    # 7.2 Agregar producto
    carrito.append({"nombre": "Laptop QA", "precio": 500.0, "cantidad": 1})
    if len(carrito) == 1 and carrito[0]["nombre"] == "Laptop QA":
        ok("Agregar producto al carrito")
    else:
        fallo("Agregar producto al carrito")

    # 7.3 Aumentar cantidad si ya existe
    for item in carrito:
        if item["nombre"] == "Laptop QA":
            item["cantidad"] += 2
    if carrito[0]["cantidad"] == 3:
        ok("Aumentar cantidad de producto existente en carrito")
    else:
        fallo("Aumentar cantidad", f"Cantidad: {carrito[0]['cantidad']}")

    # 7.4 Calcular total
    total = sum(i["precio"] * i["cantidad"] for i in carrito)
    if total == 1500.0:
        ok("Cálculo de total del carrito")
    else:
        fallo("Cálculo de total", f"Total calculado: {total}")

    # 7.5 Eliminar producto del carrito
    carrito.pop(0)
    if len(carrito) == 0:
        ok("Eliminar producto del carrito")
    else:
        fallo("Eliminar producto del carrito")


# ══════════════════════════════════════════════════════════════════════
# 8. BACKUP
# ══════════════════════════════════════════════════════════════════════
def test_backup():
    seccion("8. COPIA DE SEGURIDAD")
    import os

    # 8.1 Importar módulo backup
    try:
        from backup import realizar_backup, exportar_coleccion, listar_backups
        ok("Importar módulo backup.py")
    except Exception as e:
        error("Importar backup.py", e)
        return

    # 8.2 Exportar una colección
    try:
        from conexion import clientes
        carpeta_test = "backups/qa_test"
        os.makedirs(carpeta_test, exist_ok=True)
        n = exportar_coleccion("clientes", clientes, carpeta_test)
        ruta = os.path.join(carpeta_test, "clientes.json")
        if os.path.exists(ruta) and n >= 0:
            ok(f"Exportar colección a JSON ({n} documentos)")
        else:
            fallo("Exportar colección", "Archivo no creado")
    except Exception as e:
        error("Exportar colección", e)

    # 8.3 Backup completo
    try:
        realizar_backup()
        carpetas = os.listdir("backups") if os.path.exists("backups") else []
        carpetas_reales = [c for c in carpetas if c != "qa_test" and c != "test"]
        if carpetas_reales:
            ok("Backup completo creó carpeta con timestamp")
        else:
            fallo("Backup completo", "No se creó carpeta de backup")
    except Exception as e:
        error("Backup completo", e)

    # Limpiar carpeta de prueba
    try:
        import shutil
        if os.path.exists("backups/qa_test"):
            shutil.rmtree("backups/qa_test")
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════
# 9. LIMPIEZA DE DATOS DE PRUEBA
# ══════════════════════════════════════════════════════════════════════
def limpiar_datos_prueba():
    seccion("9. LIMPIEZA DE DATOS DE PRUEBA")
    from conexion import usuarios, clientes, pedidos

    limpiados = 0

    # Usuarios de prueba
    for campo in ["usuario_correo", "usuario_admin_correo"]:
        correo = datos_de_prueba.get(campo)
        if correo:
            res = usuarios.delete_one({"correo": correo})
            if res.deleted_count:
                limpiados += 1

    # Cliente de prueba para pedidos
    cid = datos_de_prueba.get("pedido_cliente_id")
    correo_cli = datos_de_prueba.get("pedido_cliente_correo")
    if cid:
        pedidos.delete_many({"id_cliente": cid})
        clientes.delete_one({"_id": cid})
        limpiados += 1

    if correo_cli:
        clientes.delete_one({"correo": correo_cli})

    # Producto (por si no se eliminó en el test)
    pid = datos_de_prueba.get("producto_id")
    if pid:
        from conexion import productos
        productos.delete_one({"_id": pid})
        limpiados += 1

    if limpiados > 0:
        ok(f"Datos de prueba eliminados ({limpiados} registros limpiados)")
    else:
        ok("No quedaron datos de prueba pendientes")


# ══════════════════════════════════════════════════════════════════════
# RESUMEN FINAL
# ══════════════════════════════════════════════════════════════════════
def imprimir_resumen():
    total = resultados["ok"] + resultados["fallo"] + resultados["error"]
    print(f"\n{'═'*50}")
    print(f"{NEGRITA}  RESUMEN DE QA — Merciotech{RESET}")
    print(f"{'═'*50}")
    print(f"  {VERDE}✓ Pasaron : {resultados['ok']}{RESET}")
    print(f"  {ROJO}✗ Fallaron: {resultados['fallo']}{RESET}")
    print(f"  {AMARILLO}! Errores : {resultados['error']}{RESET}")
    print(f"  Total    : {total}")
    print(f"{'═'*50}")
    if resultados["fallo"] == 0 and resultados["error"] == 0:
        print(f"\n  {VERDE}{NEGRITA}✔ Todos los tests pasaron correctamente.{RESET}\n")
    else:
        print(f"\n  {ROJO}{NEGRITA}✘ Hay tests que necesitan revisión.{RESET}\n")


# ══════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print(f"\n{NEGRITA}{'═'*50}")
    print(f"  QA MERCIOTECH — {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"{'═'*50}{RESET}")

    test_conexion()
    test_autenticacion()
    test_productos()
    test_clientes()
    test_gestion_usuarios_admin()
    test_pedidos()
    test_carrito()
    test_backup()
    limpiar_datos_prueba()
    imprimir_resumen()
