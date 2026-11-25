import json
from pathlib import Path

from client.config import APP_DIR


CATALOGO_CACHE_PATH = APP_DIR / "catalogo.json"


def cargar_catalogo_cache():
    try:
        datos = json.loads(
            CATALOGO_CACHE_PATH.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError):
        return []

    if not isinstance(datos, dict) or datos.get("version") != 1:
        return []

    productos = datos.get("productos")
    if not isinstance(productos, list):
        return []

    resultado = []
    for producto in productos:
        if isinstance(producto, list) and len(producto) >= 7:
            resultado.append(tuple(producto[:7]))
    return resultado


def guardar_catalogo_cache(productos):
    APP_DIR.mkdir(parents=True, exist_ok=True)

    temporal = Path(str(CATALOGO_CACHE_PATH) + ".tmp")
    datos = {
        "version": 1,
        "productos": [list(producto[:7]) for producto in productos],
    }

    try:
        temporal.write_text(
            json.dumps(
                datos,
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )
        temporal.replace(CATALOGO_CACHE_PATH)
    except OSError:
        try:
            temporal.unlink(missing_ok=True)
        except OSError:
            pass
