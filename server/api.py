from contextlib import asynccontextmanager
from decimal import Decimal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from server.database import DBManager

db = None


# ============================================================
# MODELOS
# ============================================================

class AbrirCajaRequest(BaseModel):
    monto_inicial: Decimal = Decimal("0")


class CambiarMetodoPagoRequest(BaseModel):
    metodo_pago: str


class VentaItem(BaseModel):
    cant: int
    nombre: str
    subtotal: Decimal

    precio_unitario: Decimal | None = None

    # La GUI actual utiliza "obs".
    obs: str | None = None

    # Se mantiene también por compatibilidad futura.
    notas: str | None = None

    es_extra: bool = False
    parent_detalle_id: int | None = None
    peso_gramos: Decimal | None = None
    precio_kg: Decimal | None = None


class CrearVentaRequest(BaseModel):
    total: Decimal
    metodo_pago: str
    items: list[VentaItem]
    tipo_entrega: str = "Mostrador"
    recargo_delivery: Decimal = Decimal("0")


# ============================================================
# CICLO DE VIDA
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db

    db = DBManager()
    db.init_db()

    yield

    db.close()


app = FastAPI(
    title="Campo POS API",
    version="2.0.0",
    lifespan=lifespan,
)


# ============================================================
# SISTEMA
# ============================================================

@app.get("/")
def inicio():
    return {
        "app": "Campo POS API",
        "version": "2.0.0",
        "status": "online",
    }


@app.get("/health")
def health():
    try:
        resultado = db.probar_conexion()

        return {
            "status": "ok",
            "database": resultado["database"],
        }

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="No se pudo conectar con la base de datos.",
        ) from exc


# ============================================================
# PRODUCTOS
# ============================================================

@app.get("/productos")
def obtener_productos(
    categoria: str = "TODOS",
    subcategoria: str = "TODOS",
):
    try:
        productos = db.obtener_productos_filtrados(
            categoria,
            subcategoria,
        )

        return [
            {
                "id": p[0],
                "nombre": p[1],
                "precio": p[2],
                "categoria": p[3],
                "subcategoria": p[4],
                "descripcion": p[5],
                "tipo_venta": p[6],
            }
            for p in productos
        ]

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="No se pudieron obtener los productos.",
        ) from exc


# ============================================================
# CAJA
# ============================================================

@app.get("/caja")
def obtener_caja():
    try:
        return db.obtener_sesion_abierta()

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="No se pudo consultar la caja.",
        ) from exc


@app.get("/caja/resumen")
def obtener_resumen_caja():
    try:
        return db.obtener_resumen_caja()

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="No se pudo obtener el resumen de caja.",
        ) from exc


@app.post("/caja/abrir")
def abrir_caja(datos: AbrirCajaRequest):
    try:
        sesion_id = db.abrir_caja(
            datos.monto_inicial
        )

        return {
            "ok": True,
            "sesion_id": sesion_id,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@app.post("/caja/cerrar")
def cerrar_caja():
    try:
        sesion_id = db.cerrar_caja()

        return {
            "ok": True,
            "sesion_id": sesion_id,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


# ============================================================
# VENTAS
# ============================================================

# IMPORTANTE:
# Esta ruta debe declararse ANTES de /ventas/{venta_id}.
@app.get("/ventas/sesion-activa")
def obtener_ventas_sesion_activa():
    try:
        return db.obtener_ventas_sesion_activa()

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="No se pudieron obtener las ventas del turno.",
        ) from exc


@app.post("/ventas")
def crear_venta(datos: CrearVentaRequest):
    try:
        items = [
            item.model_dump(exclude_none=True)
            for item in datos.items
        ]

        venta_id = db.crear_venta(
            total=datos.total,
            metodo_pago=datos.metodo_pago,
            items=items,
            tipo_entrega=datos.tipo_entrega,
            recargo_delivery=datos.recargo_delivery,
        )

        return {
            "ok": True,
            "venta_id": venta_id,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="No se pudo registrar la venta.",
        ) from exc


@app.patch("/ventas/{venta_id}/metodo-pago")
def actualizar_metodo_pago(
    venta_id: int,
    datos: CambiarMetodoPagoRequest,
):
    try:
        db.actualizar_metodo_pago_venta(
            venta_id,
            datos.metodo_pago,
        )

        return {
            "ok": True,
            "venta_id": venta_id,
            "metodo_pago": datos.metodo_pago,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@app.post("/ventas/{venta_id}/anular")
def anular_venta(venta_id: int):
    try:
        db.anular_venta(
            venta_id
        )

        return {
            "ok": True,
            "venta_id": venta_id,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@app.get("/ventas/{venta_id}")
def obtener_venta(venta_id: int):
    try:
        detalle = db.obtener_detalle_venta(
            venta_id
        )

        if not detalle:
            raise HTTPException(
                status_code=404,
                detail="Venta no encontrada.",
            )

        return {
            "venta_id": venta_id,
            "detalle": detalle,
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="No se pudo obtener la venta.",
        ) from exc


# ============================================================
# REPORTES
# ============================================================

@app.get("/reportes/sesiones")
def obtener_resumen_sesiones(
    limite: int = 100,
):
    try:
        return db.obtener_resumen_sesiones(
            limite
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="No se pudo obtener el historial de sesiones.",
        ) from exc


@app.get("/reportes/semanal")
def obtener_resumen_semanal(
    limite_semanas: int = 52,
):
    try:
        return db.obtener_resumen_semanal(
            limite_semanas
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="No se pudo obtener el resumen semanal.",
        ) from exc


@app.get("/reportes/mensual")
def obtener_resumen_mensual(
    limite_meses: int = 24,
):
    try:
        return db.obtener_resumen_mensual(
            limite_meses
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="No se pudo obtener el resumen mensual.",
        ) from exc