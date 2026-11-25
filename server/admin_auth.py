import base64
import hashlib
import hmac
import os
import secrets
import threading
import time

from fastapi import Header, HTTPException, Request


_TOKEN_TTL = max(300, int(os.getenv("CAMPO_ADMIN_TOKEN_TTL", "1200")))
_FAIL_WINDOW = 300
_FAIL_LIMIT = 5

_lock = threading.Lock()
_tokens = {}
_fallos = {}


def _b64decode(valor):
    texto = str(valor)
    texto += "=" * (-len(texto) % 4)
    return base64.urlsafe_b64decode(texto.encode("ascii"))


def _configuracion_pin():
    valor = str(os.getenv("CAMPO_ADMIN_PIN_HASH") or "").strip()
    if not valor:
        raise HTTPException(
            status_code=503,
            detail="La administración de menú todavía no está configurada.",
        )

    try:
        esquema, iteraciones, sal, esperado = valor.split("$", 3)
        if esquema != "pbkdf2_sha256":
            raise ValueError
        iteraciones = int(iteraciones)
        sal = _b64decode(sal)
        esperado = _b64decode(esperado)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=503,
            detail="La configuración administrativa del servidor es inválida.",
        )

    return iteraciones, sal, esperado


def _verificar_pin(pin):
    pin = str(pin or "").strip()
    if not pin.isdigit() or not 6 <= len(pin) <= 12:
        return False

    iteraciones, sal, esperado = _configuracion_pin()
    calculado = hashlib.pbkdf2_hmac(
        "sha256",
        pin.encode("utf-8"),
        sal,
        iteraciones,
    )
    return hmac.compare_digest(calculado, esperado)


def _clave_cliente(request):
    reenviado = str(request.headers.get("x-forwarded-for") or "").strip()
    if reenviado:
        return reenviado.split(",", 1)[0].strip()
    if request.client:
        return request.client.host
    return "desconocido"


def _limpiar_tokens(ahora):
    vencidos = [
        token
        for token, expira in _tokens.items()
        if expira <= ahora
    ]
    for token in vencidos:
        _tokens.pop(token, None)


def autenticar_admin(pin, request: Request):
    ahora = time.monotonic()
    cliente = _clave_cliente(request)

    with _lock:
        recientes = [
            instante
            for instante in _fallos.get(cliente, [])
            if ahora - instante < _FAIL_WINDOW
        ]
        _fallos[cliente] = recientes

        if len(recientes) >= _FAIL_LIMIT:
            raise HTTPException(
                status_code=429,
                detail="Demasiados intentos. Espere unos minutos.",
            )

    if not _verificar_pin(pin):
        with _lock:
            _fallos.setdefault(cliente, []).append(ahora)
        time.sleep(0.35)
        raise HTTPException(
            status_code=401,
            detail="PIN administrativo incorrecto.",
        )

    token = secrets.token_urlsafe(32)

    with _lock:
        _fallos.pop(cliente, None)
        _limpiar_tokens(ahora)
        _tokens[token] = ahora + _TOKEN_TTL

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": _TOKEN_TTL,
    }


def requerir_admin(
    authorization: str | None = Header(default=None),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Se requiere una sesión administrativa.",
        )

    token = authorization[7:].strip()
    ahora = time.monotonic()

    with _lock:
        _limpiar_tokens(ahora)
        expira = _tokens.get(token)

        if expira is None or expira <= ahora:
            _tokens.pop(token, None)
            raise HTTPException(
                status_code=401,
                detail="La sesión administrativa expiró.",
            )

        _tokens[token] = ahora + _TOKEN_TTL

    return token


def operaciones_sensibles_protegidas():
    valor = str(
        os.getenv("CAMPO_PROTEGER_OPERACIONES_SENSIBLES", "false")
    ).strip().lower()
    return valor in {"1", "true", "yes", "si", "sí", "on"}


def requerir_admin_sensible(
    authorization: str | None = Header(default=None),
):
    """
    Protege operaciones sensibles sin romper clientes antiguos durante
    el despliegue. Se activa con CAMPO_PROTEGER_OPERACIONES_SENSIBLES=true.
    """
    if not operaciones_sensibles_protegidas():
        return None

    return requerir_admin(authorization)
