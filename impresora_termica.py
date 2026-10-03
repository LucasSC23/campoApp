import json
import os
from pathlib import Path


APP_DIR = Path(
    os.environ.get(
        "APPDATA",
        str(Path.home()),
    )
) / "CampoBurgerPOS"

CONFIG_PATH = APP_DIR / "printer_config.json"

CONFIG_DEFAULT = {
    "nombre_impresora": "",
    "ancho_caracteres": 42,
    "cortar_papel": True,
    "copias": 1,
}


class ErrorImpresora(RuntimeError):
    pass


def _importar_win32print():
    try:
        import win32print
        return win32print
    except ImportError as exc:
        raise ErrorImpresora(
            "Falta el componente de impresión de Windows (pywin32). "
            "Instalá la dependencia con: pip install pywin32"
        ) from exc


def cargar_configuracion():
    config = dict(CONFIG_DEFAULT)

    try:
        if CONFIG_PATH.exists():
            datos = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(datos, dict):
                config.update(datos)
    except (OSError, json.JSONDecodeError):
        pass

    try:
        config["ancho_caracteres"] = int(config.get("ancho_caracteres", 42))
    except (TypeError, ValueError):
        config["ancho_caracteres"] = 42

    try:
        config["copias"] = max(1, min(int(config.get("copias", 1)), 5))
    except (TypeError, ValueError):
        config["copias"] = 1

    config["cortar_papel"] = bool(config.get("cortar_papel", True))
    config["nombre_impresora"] = str(
        config.get("nombre_impresora", "")
    ).strip()

    return config


def guardar_configuracion(
    nombre_impresora,
    ancho_caracteres=42,
    cortar_papel=True,
    copias=1,
):
    APP_DIR.mkdir(parents=True, exist_ok=True)

    config = {
        "nombre_impresora": str(nombre_impresora or "").strip(),
        "ancho_caracteres": max(32, min(int(ancho_caracteres), 64)),
        "cortar_papel": bool(cortar_papel),
        "copias": max(1, min(int(copias), 5)),
    }

    CONFIG_PATH.write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return config


def listar_impresoras():
    win32print = _importar_win32print()

    flags = (
        win32print.PRINTER_ENUM_LOCAL
        | win32print.PRINTER_ENUM_CONNECTIONS
    )

    impresoras = win32print.EnumPrinters(flags, None, 1)

    nombres = []
    for info in impresoras:
        nombre = info.get("pPrinterName")
        if nombre:
            nombres.append(str(nombre))

    return sorted(set(nombres), key=str.casefold)


def obtener_impresora_predeterminada():
    win32print = _importar_win32print()

    try:
        return win32print.GetDefaultPrinter()
    except Exception:
        return ""


def obtener_impresora_activa():
    config = cargar_configuracion()
    configurada = config.get("nombre_impresora", "").strip()

    if configurada:
        return configurada

    predeterminada = obtener_impresora_predeterminada()
    if predeterminada:
        return predeterminada

    raise ErrorImpresora(
        "No hay ninguna impresora configurada ni una impresora "
        "predeterminada en Windows."
    )


def _normalizar_texto_escpos(texto):
    # CP850 permite los caracteres españoles habituales y es común en
    # impresoras ESC/POS. Los caracteres no disponibles se reemplazan.
    return str(texto).replace("\r\n", "\n").replace("\r", "\n")


def _datos_escpos(texto, cortar_papel=True):
    texto = _normalizar_texto_escpos(texto)

    datos = bytearray()

    # Inicializar impresora.
    datos.extend(b"\x1b\x40")

    # Seleccionar tabla de caracteres PC850 en equipos ESC/POS compatibles.
    datos.extend(b"\x1b\x74\x02")

    # Alineación izquierda.
    datos.extend(b"\x1b\x61\x00")

    for linea in texto.split("\n"):
        es_cabecera = "CAMPO BURGER" in linea.upper()
        es_total = linea.strip().upper().startswith("TOTAL:")

        if es_cabecera:
            datos.extend(b"\x1b\x61\x01")  # centrar
            datos.extend(b"\x1b\x45\x01")  # negrita
        elif es_total:
            datos.extend(b"\x1b\x61\x00")
            datos.extend(b"\x1b\x45\x01")
            datos.extend(b"\x1d\x21\x01")  # doble alto
        else:
            datos.extend(b"\x1b\x61\x00")
            datos.extend(b"\x1b\x45\x00")
            datos.extend(b"\x1d\x21\x00")

        datos.extend(linea.encode("cp850", errors="replace"))
        datos.extend(b"\n")

    # Restablecer tamaño y negrita.
    datos.extend(b"\x1d\x21\x00")
    datos.extend(b"\x1b\x45\x00")
    datos.extend(b"\x1b\x61\x00")

    # Avanzar unas líneas antes de cortar.
    datos.extend(b"\n\n\n")

    if cortar_papel:
        # Corte completo ESC/POS.
        datos.extend(b"\x1d\x56\x00")

    return bytes(datos)


def imprimir_ticket(texto, nombre_impresora=None):
    """
    Envía el ticket directamente a la cola de Windows en modo RAW ESC/POS.

    La impresora debe estar instalada en Windows y ser compatible con
    comandos ESC/POS para aprovechar el corte automático.
    """
    win32print = _importar_win32print()
    config = cargar_configuracion()

    impresora = (
        str(nombre_impresora or "").strip()
        or obtener_impresora_activa()
    )

    cortar = bool(config.get("cortar_papel", True))
    copias = max(1, int(config.get("copias", 1)))

    datos = _datos_escpos(
        texto,
        cortar_papel=cortar,
    )

    handle = None

    try:
        handle = win32print.OpenPrinter(impresora)

        for numero_copia in range(1, copias + 1):
            doc_name = (
                "Campo Burger - Ticket"
                if copias == 1
                else f"Campo Burger - Ticket copia {numero_copia}"
            )

            job = win32print.StartDocPrinter(
                handle,
                1,
                (doc_name, None, "RAW"),
            )

            try:
                win32print.StartPagePrinter(handle)
                win32print.WritePrinter(handle, datos)
                win32print.EndPagePrinter(handle)
            finally:
                win32print.EndDocPrinter(handle)

        return impresora

    except Exception as exc:
        raise ErrorImpresora(
            f"No se pudo imprimir en '{impresora}'. "
            f"Verificá que esté encendida, conectada e instalada en Windows.\n\n"
            f"Detalle: {exc}"
        ) from exc

    finally:
        if handle is not None:
            try:
                win32print.ClosePrinter(handle)
            except Exception:
                pass


def imprimir_prueba(nombre_impresora=None):
    impresora = (
        str(nombre_impresora or "").strip()
        or obtener_impresora_activa()
    )

    texto = "\n".join(
        [
            "CAMPO BURGER & ACAI".center(42),
            "PRUEBA DE IMPRESION 80 MM".center(42),
            "-" * 42,
            f"Impresora: {impresora}",
            "",
            "Si puede leer este ticket,",
            "la impresora esta lista para el POS.",
            "-" * 42,
            "TOTAL: Gs. 10.000",
        ]
    )

    return imprimir_ticket(
        texto,
        nombre_impresora=impresora,
    )
