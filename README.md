# Campo POS

Sistema de punto de venta de escritorio para Campo Burger & Açaí, orientado a negocios gastronómicos pequeños y medianos.

La versión actual utiliza una arquitectura cliente-servidor: la aplicación Windows no se conecta directamente a PostgreSQL. El cliente consume una API FastAPI desplegada en Render, y el backend accede a PostgreSQL en Supabase.

---

## Arquitectura actual

```text
Cajero
  ↓
Campo POS Desktop
Python + Tkinter
  ↓ HTTPS / JSON
APIClient
  ↓
FastAPI en Render
  ↓
DBManager / psycopg2
  ↓
Supabase PostgreSQL
```

### Flujo de una venta

```text
client/gui.py
  ↓
client/api_client.py
  ↓
POST /ventas
  ↓
server/api.py
  ↓
CrearVentaRequest
  ↓
server/database.py
  ↓
PostgreSQL / Supabase
```

El cliente genera un `operacion_id` para las ventas. El backend utiliza ese identificador junto con un hash de la operación para evitar ventas duplicadas ante reintentos o respuestas ambiguas.

---

## Tecnologías

### Cliente de escritorio

- Python 3.11
- Tkinter
- Requests
- PyWin32
- PyInstaller

### Backend

- FastAPI
- Uvicorn
- Pydantic
- Psycopg2

### Infraestructura

- Render — hosting de FastAPI
- Supabase — PostgreSQL
- HTTPS entre el cliente y la API

### Instalación Windows

- PyInstaller
- Inno Setup

---

## Estructura del proyecto

```text
POS_Hamburgueseria/
├── client/
│   ├── __init__.py
│   ├── main.py
│   ├── api_client.py
│   ├── config.py
│   ├── gui.py
│   ├── impresora_termica.py
│   ├── ui_dialogos.py
│   ├── ventana_cierre.py
│   └── ventana_reportes.py
├── server/
│   ├── __init__.py
│   ├── api.py
│   └── database.py
├── tests/
│   ├── __init__.py
│   └── test_database.py
├── installer/
│   └── CampoBurgerPOS.iss
├── scripts/
│   ├── build_campoburger.ps1
│   └── crear_instalador.ps1
├── sql/
│   ├── add_ventas_idempotencia.sql
│   └── reportes.sql
├── CampoBurgerPOS.spec
├── campo_burger.ico
├── requirements.txt
├── requirements-dev.txt
├── .env.example
└── README.md
```

---

## Módulos principales

### `client/main.py`

Punto de entrada del cliente de escritorio. Crea `APIClient` e inicia `VentanaPrincipal`.

### `client/gui.py`

Interfaz principal del POS. Gestiona catálogo, carrito, ventas, tickets, historial, caja e interacción con la impresora.

### `client/api_client.py`

Capa HTTP del cliente. Se comunica con FastAPI y mantiene una interfaz similar al antiguo acceso directo a base de datos.

#### Resiliencia de red

La consulta y la apertura de caja al arrancar, el catálogo, el cierre de caja, los reportes y el historial se ejecutan en segundo plano. Tkinter sigue respondiendo mientras espera la API y muestra el estado de la caja al iniciar.

- Cada intento tiene un timeout de conexión de 5 segundos y uno de lectura de 90 segundos por defecto.
- Ante fallos transitorios de red o respuestas HTTP 408, 502, 503 o 504, se reintentan las consultas `GET` y el `POST /ventas` si incluye un `operacion_id` válido. Hay hasta dos reintentos, con pausas de 0,5 y 1 segundo. Los intentos de venta reutilizan el mismo identificador y el mismo cuerpo.
- La apertura y el cierre de caja, la anulación de venta y el cambio de método de pago se envían una sola vez por acción.
- En Windows, `%LOCALAPPDATA%\CampoBurgerPOS\logs\api.log` guarda el método, la ruta sin identificadores, el número de intento, el resultado y la duración. El archivo rota al alcanzar 1 MiB y conserva hasta tres copias. Los registros excluyen credenciales, URL completas, parámetros y cuerpos.
- El último catálogo válido se guarda en `%LOCALAPPDATA%\CampoBurgerPOS\catalogo.json`. Al abrir el POS se muestra esa copia inmediatamente y luego se actualiza desde la API en segundo plano.


### `client/config.py`

Gestiona la URL de la API. La URL de producción por defecto es:

```text
https://campo-pos-api.onrender.com
```

La configuración local puede almacenarse en:

```text
%LOCALAPPDATA%\CampoBurgerPOS\config.json
```

### `server/api.py`

Backend FastAPI. Expone endpoints para productos, caja, ventas y reportes.

Ejemplos:

```text
GET   /health
GET   /productos
POST  /admin/login
GET   /admin/productos
POST  /admin/productos
PATCH /admin/productos/{producto_id}
PATCH /admin/productos/{producto_id}/estado
GET   /caja
GET   /caja/resumen
POST  /caja/abrir
POST  /caja/cerrar
GET   /ventas/sesion-activa
POST  /ventas
PATCH /ventas/{venta_id}/metodo-pago
POST  /ventas/{venta_id}/anular
GET   /reportes/semanal
GET   /reportes/mensual
```

### `server/database.py`

Capa de acceso a PostgreSQL. Usa un `ThreadedConnectionPool`, transacciones y validaciones antes de persistir los datos.

### `client/impresora_termica.py`

Integración con impresoras instaladas en Windows mediante PyWin32.

---

## Configuración

### Backend

Crear un archivo `.env` a partir de `.env.example`.

Las credenciales PostgreSQL son utilizadas únicamente por el backend y no deben incluirse en el ejecutable Windows.

Variables principales:

```text
DB_HOST
DB_PORT
DB_NAME
DB_USER
DB_PASSWORD
DB_SSLMODE
DB_CONNECT_TIMEOUT
DB_POOL_MIN
DB_POOL_MAX
DB_TIMEZONE
```

Nunca versionar el archivo `.env`.

### Cliente

El cliente no necesita credenciales PostgreSQL.

Solo necesita conocer la URL HTTPS de Campo POS API.

---

## Desarrollo local

Instalar dependencias:

```powershell
python -m pip install -r requirements-dev.txt
```

Ejecutar la API:

```powershell
python -m uvicorn server.api:app --reload
```

Ejecutar el cliente:

```powershell
python -m client.main
```

Para apuntar temporalmente el cliente a otra API se puede utilizar `CAMPO_API_URL` o actualizar `config.json`.

---

## Build del cliente Windows

```powershell
.\scripts\build_campoburger.ps1
```

Resultado:

```text
dist\CampoBurgerPOS\CampoBurgerPOS.exe
```

El proceso de build verifica que archivos `.env` y componentes del servidor no se distribuyan con el cliente.

---

## Instalador Windows

Después del build:

```powershell
.\scripts\crear_instalador.ps1
```

Resultado:

```text
installer\CampoBurgerPOS_Setup.exe
```

---

## Seguridad y confiabilidad

La arquitectura actual evita distribuir credenciales PostgreSQL en las PCs del negocio.

Además se implementó idempotencia para `POST /ventas`:

```text
operacion_id UUID
+
operacion_hash
+
índice UNIQUE
```

Esto permite reconocer una misma operación y evita duplicar una venta si existe un reintento.

La administración del menú utiliza un PIN validado exclusivamente por FastAPI. El PIN no se guarda en el cliente: el servidor almacena solamente un hash PBKDF2 configurado mediante `CAMPO_ADMIN_PIN_HASH` y entrega un token temporal después de autenticar. Los productos se activan o desactivan en lugar de eliminarse, preservando el historial de ventas.

El mismo PIN protege en el cliente las operaciones sensibles de **cerrar caja**, **anular una venta** y **cambiar el método de pago**. El backend puede exigir también ese token en esas rutas. Para evitar romper instalaciones antiguas durante una actualización, esa exigencia se activa de forma explícita con `CAMPO_PROTEGER_OPERACIONES_SENSIBLES=true`.

Orden recomendado de despliegue:

1. generar y configurar `CAMPO_ADMIN_PIN_HASH` en el servidor;
2. desplegar el backend manteniendo `CAMPO_PROTEGER_OPERACIONES_SENSIBLES=false`;
3. instalar el nuevo cliente en la PC del negocio y probar el PIN;
4. recién entonces cambiar `CAMPO_PROTEGER_OPERACIONES_SENSIBLES=true` en Render.

Para generar el hash:

```powershell
python scripts/generar_admin_pin_hash.py
```

### Pendientes importantes

El proyecto todavía tiene mejoras previstas antes de considerarlo completamente endurecido para múltiples clientes o exposición pública a mayor escala:

- autenticación y autorización de usuarios
- roles y permisos
- auditoría de operaciones
- backend como autoridad completa de precios y totales
- persistencia local de operaciones pendientes
- tests automáticos aislados
- migraciones formales de base de datos
- actualización automática del cliente
- firma digital del instalador
- monitoreo y alertas
- soporte multiempresa / multisucursal

---

## Despliegue actual

Backend:

```text
Render
https://campo-pos-api.onrender.com
```

Base de datos:

```text
Supabase PostgreSQL
```

Cliente:

```text
CampoBurgerPOS.exe
  ↓ HTTPS
FastAPI / Render
  ↓
Supabase PostgreSQL
```

---

## Rama de desarrollo actual

La arquitectura cliente-servidor y los cambios recientes se encuentran en:

```text
refactor/estructura-comercial
```

Actualmente esta rama contiene la versión más avanzada del proyecto y está por delante de `main`.

Antes de utilizar `main` como referencia para revisión técnica, conviene integrar esta rama cuando se considere estable.

---

## Objetivo

Convertir Campo POS en una solución reutilizable y mantenible para negocios gastronómicos, manteniendo una aplicación de caja rápida en Windows y centralizando lógica, datos y futuras funciones administrativas en el backend.
