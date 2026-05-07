# Proyecto MongoCrud - Merciotech

Guia rapida para ejecutar el proyecto desde un archivo RAR.

## 1) Descomprimir

Descomprime el archivo RAR y abre la carpeta del proyecto en VS Code.

## 2) Crear entorno virtual

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Si falla la activacion:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 3) Instalar dependencias

```bash
pip install pymongo bcrypt
```

## 4) Configurar MongoDB

En `conexion.py` revisa:

- `CONEXION` (tu URI de MongoDB)
- `ADMIN_CORREO` (correo del super admin)

## 5) Ejecutar el sistema

```bash
python menu_usuario.py
```

## 6) Backup

En menu admin, opcion `9`.
Los archivos se guardan en la carpeta `backups/`.

## 7) Pruebas QA

```bash
python qa_tests.py
```

## Problemas comunes

- No conecta a MongoDB: revisa `CONEXION` y la IP permitida en Atlas.
- No entra a admin: el correo debe ser igual a `ADMIN_CORREO`.
- Faltan modulos: ejecuta `pip install pymongo bcrypt`.
