import base64
import hashlib
import secrets
import tkinter as tk
from tkinter import simpledialog


ITERACIONES = 260_000


def b64(valor):
    return base64.urlsafe_b64encode(valor).decode("ascii").rstrip("=")


def solicitar_pin():
    ventana = tk.Tk()
    ventana.withdraw()
    ventana.attributes("-topmost", True)

    try:
        pin = simpledialog.askstring(
            "Campo POS - PIN administrativo",
            "Elegí un PIN de 6 a 12 dígitos (recomendado: 8):",
            show="*",
            parent=ventana,
        )
        if pin is None:
            raise SystemExit("Operación cancelada.")

        pin = pin.strip()
        if not pin.isascii() or not pin.isdigit() or not 6 <= len(pin) <= 12:
            raise SystemExit("El PIN debe contener entre 6 y 12 dígitos.")

        confirmar = simpledialog.askstring(
            "Campo POS - Confirmar PIN",
            "Volvé a escribir el mismo PIN:",
            show="*",
            parent=ventana,
        )
        if confirmar is None:
            raise SystemExit("Operación cancelada.")

        if confirmar.strip() != pin:
            raise SystemExit("Los PIN no coinciden.")

        return pin
    finally:
        ventana.destroy()


def main():
    pin = solicitar_pin()

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
