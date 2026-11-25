import base64
import getpass
import hashlib
import secrets


ITERACIONES = 260_000


def b64(valor):
    return base64.urlsafe_b64encode(valor).decode("ascii").rstrip("=")


def main():
    pin = getpass.getpass(
        "PIN administrativo (recomendado: 8 dígitos): "
    ).strip()

    if not pin.isdigit() or not 6 <= len(pin) <= 12:
        raise SystemExit(
            "El PIN debe contener entre 6 y 12 dígitos."
        )

    confirmar = getpass.getpass("Repita el PIN: ").strip()
    if confirmar != pin:
        raise SystemExit("Los PIN no coinciden.")

    sal = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        pin.encode("utf-8"),
        sal,
        ITERACIONES,
    )

    print()
    print("Copie este valor en CAMPO_ADMIN_PIN_HASH del servidor:")
    print(
        "pbkdf2_sha256$"
        + str(ITERACIONES)
        + "$"
        + b64(sal)
        + "$"
        + b64(digest)
    )


if __name__ == "__main__":
    main()
