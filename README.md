# Campo POS

Sistema de punto de venta para negocios gastronómicos.

Campo POS comenzó como un sistema para Campo Burger y está evolucionando hacia una arquitectura comercial reutilizable para hamburgueserías, pizzerías, cafeterías y otros negocios gastronómicos de tamaño pequeño o mediano.

---

## Arquitectura

El sistema está dividido en varias capas:

```text
Usuario / Cajero
      ↓
GUI - Tkinter
      ↓
api_client.py
      ↓ HTTP / HTTPS
FastAPI
      ↓
database.py / DBManager
      ↓
PostgreSQL / Supabase
```

### Flujo de una venta

```text
gui.py
    ↓
api_client.py
    ↓
POST /ventas
    ↓
API/api.py
    ↓
CrearVentaRequest
    ↓
DBManager.crear_venta()
    ↓
PostgreSQL / Supabase
```

La respuesta vuelve en sentido contrario:

```text
PostgreSQL
    ↓
DBManager
    ↓
FastAPI
    ↓
api_client.py
    ↓
GUI
```

---

## Tecnologías

### Cliente de escritorio

- Python 3.11
- Tkinter
- Requests
- PyWin32
- PyInstaller

### Backend

- Python
- FastAPI
- Uvicorn
- Pydantic

### Base de datos

- PostgreSQL
- Supabase
- Psycopg2

### Instalación Windows

- PyInstaller
- Inno Setup

---

## Estructura actual del proyecto

```text
POS_Hamburgueseria/
│
├── API/
│   ├── __init__.py
│   └── api.py
│
├── installer/
│   └── CampoBurgerPOS.iss
│
├── scripts/
│   ├── build_campoburger.ps1
│   └── crear_instalador.ps1
│
├── sql/
│   └── reportes.sql
│
├── api_client.py
├── database.py
├── gui.py
├── impresora_termica.py
├── main.py
├── ui_dialogos.py
├── ventana_cierre.py
├── ventana_reportes.py
│
├── CampoBurgerPOS.spec
├── campo_burger.ico
│
├── requirements.txt
├── requirements-dev.txt
├── .env.example
└── .gitignore
```

---

## Responsabilidad de los módulos principales

### `main.py`

Punto de entrada de la aplicación de escritorio.

Crea `APIClient` e inicia la interfaz principal.

---

### `gui.py`

Interfaz principal del POS.

Gestiona:

- catálogo
- carrito
- cobros
- tickets
- historial de ventas
- configuración de impresora

---

### `api_client.py`

Cliente HTTP del POS.

Su responsabilidad es comunicarse con FastAPI.

No accede directamente a PostgreSQL.

---

### `API/api.py`

Backend HTTP del sistema.

Define los endpoints de la API, valida los datos y coordina las operaciones.

Ejemplos:

```text
GET  /productos
POST /ventas
GET  /caja
POST /caja/abrir
POST /caja/cerrar
GET  /reportes/semanal
```

---

### `database.py`

Capa de acceso a datos.

Contiene `DBManager`, que administra las conexiones con PostgreSQL y ejecuta las operaciones SQL.

---

### `impresora_termica.py`

Gestiona la impresión de tickets mediante las impresoras instaladas en Windows.

---

## Configuración

Crear un archivo:

```text
.env
```

a partir de:

```text
.env.example
```

Las credenciales de base de datos son utilizadas únicamente por el backend.

El archivo `.env` no debe versionarse ni incluirse dentro del cliente compilado.

---

## Instalación de dependencias

Dependencias de ejecución:

```powershell
python -m pip install -r requirements.txt
```

Dependencias de desarrollo:

```powershell
python -m pip install -r requirements-dev.txt
```

---

## Ejecutar la API localmente

Desde la raíz del proyecto:

```powershell
python -m uvicorn API.api:app --reload
```

La API estará disponible en:

```text
http://127.0.0.1:8000
```

Documentación automática:

```text
http://127.0.0.1:8000/docs
```

---

## Ejecutar el cliente

Con la API activa:

```powershell
python main.py
```

---

## Generar el ejecutable Windows

Ejecutar:

```powershell
.\scripts\build_campoburger.ps1
```

El resultado queda en:

```text
dist\CampoBurgerPOS\CampoBurgerPOS.exe
```

El proceso verifica que el archivo `.env` no sea incluido dentro del cliente.

---

## Crear el instalador

Después del build:

```powershell
.\scripts\crear_instalador.ps1
```

El instalador generado queda en:

```text
installer\CampoBurgerPOS_Setup.exe
```

---

## Seguridad

El objetivo de la arquitectura es que la computadora del cliente no tenga acceso directo a PostgreSQL.

Arquitectura objetivo:

```text
PC DEL CLIENTE
CampoBurgerPOS.exe
        ↓ HTTPS
API FastAPI
        ↓
PostgreSQL / Supabase
```

El cliente no debe contener:

```text
DB_HOST
DB_USER
DB_PASSWORD
```

Las credenciales privadas deben existir únicamente en el servidor backend.

---

## Estado actual

Actualmente la API se ejecuta localmente durante el desarrollo mediante:

```text
http://127.0.0.1:8000
```

El próximo objetivo es desplegar FastAPI en un servidor remoto utilizando HTTPS.

---

## Evolución prevista

Entre las siguientes mejoras previstas se encuentran:

- autenticación
- usuarios
- roles y permisos
- soporte multiempresa
- soporte multisucursal
- auditoría
- arqueo de caja
- logs
- backups
- actualización automática
- despliegue de FastAPI en producción

---

## Desarrollo

El proyecto utiliza Git para control de versiones.

El desarrollo de la reorganización comercial se realiza actualmente en:

```text
refactor/estructura-comercial
```

La rama `main` se mantiene como versión estable hasta completar y probar la reorganización.