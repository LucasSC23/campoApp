import tkinter as tk
from decimal import Decimal, InvalidOperation


# ================================================================
# ESTILO CAMPO BURGER POS
# ================================================================

BG = "#141722"
PANEL = "#1c2030"
PANEL_2 = "#252a3e"
HEADER_BG = "#11141d"

ORANGE = "#ff8c2b"
GREEN = "#2ecc71"
RED = "#ff4d4d"
BLUE = "#3498db"

TEXT = "#ffffff"
MUTED = "#a0a5b5"


# ================================================================
# UTILIDAD: CENTRAR DIÁLOGOS
# ================================================================

def _centrar(dialog, parent, ancho, alto):
    """
    Centra el diálogo sobre su ventana padre.

    Si la ventana padre no está disponible o visible,
    centra el diálogo en la pantalla.
    """

    dialog.update_idletasks()

    try:
        parent_visible = (
            parent is not None
            and parent.winfo_exists()
            and parent.winfo_viewable()
        )

    except tk.TclError:
        parent_visible = False

    if parent_visible:
        x = parent.winfo_rootx() + max(
            0,
            (parent.winfo_width() - ancho) // 2,
        )

        y = parent.winfo_rooty() + max(
            0,
            (parent.winfo_height() - alto) // 2,
        )

    else:
        x = max(
            0,
            (dialog.winfo_screenwidth() - ancho) // 2,
        )

        y = max(
            0,
            (dialog.winfo_screenheight() - alto) // 2,
        )

    dialog.geometry(
        f"{ancho}x{alto}+{x}+{y}"
    )


# ================================================================
# UTILIDAD: COLOR E ÍCONO SEGÚN TIPO DE MENSAJE
# ================================================================

def _color_y_simbolo(tipo):
    """
    Devuelve el color e ícono correspondiente
    al tipo de diálogo.
    """

    mapa = {
        "success": (GREEN, "✓"),
        "info": (BLUE, "i"),
        "warning": (ORANGE, "!"),
        "error": (RED, "×"),
        "question": (ORANGE, "?"),
    }

    return mapa.get(
        tipo,
        mapa["info"],
    )


# ================================================================
# UTILIDAD: CIERRE SEGURO DE DIÁLOGOS
# ================================================================

def _cerrar_dialogo_seguro(dialog):
    """
    Libera el grab modal antes de destruir el diálogo.

    Esto evita que Tkinter deje bloqueada la ventana principal
    después de cerrar un mensaje, error o confirmación.
    """

    try:
        actual = dialog.grab_current()

        if actual == dialog:
            dialog.grab_release()

    except tk.TclError:
        pass

    try:
        if dialog.winfo_exists():
            dialog.destroy()

    except tk.TclError:
        pass


# ================================================================
# BASE VISUAL DE TODOS LOS DIÁLOGOS
# ================================================================

def _crear_base(
    parent,
    titulo,
    tipo="info",
    ancho=440,
    alto=235,
):
    """
    Construye la ventana base utilizada por todos los diálogos
    personalizados de Campo Burger POS.
    """

    color, simbolo = _color_y_simbolo(tipo)

    dialog = tk.Toplevel(parent)

    dialog.title(titulo)
    dialog.configure(bg=PANEL_2)
    dialog.resizable(False, False)

    # ------------------------------------------------------------
    # QUITAR BARRA NATIVA DE WINDOWS
    # ------------------------------------------------------------

    dialog.overrideredirect(True)

    try:
        if (
            parent is not None
            and parent.winfo_exists()
            and parent.winfo_viewable()
        ):
            dialog.transient(parent)

    except tk.TclError:
        pass

    # ------------------------------------------------------------
    # MARCO PRINCIPAL
    # ------------------------------------------------------------

    marco = tk.Frame(
        dialog,
        bg=PANEL_2,
        highlightbackground=PANEL_2,
        highlightthickness=1,
        bd=0,
    )

    marco.pack(
        fill="both",
        expand=True,
    )

    # ------------------------------------------------------------
    # HEADER
    # ------------------------------------------------------------

    header = tk.Frame(
        marco,
        bg=HEADER_BG,
        height=54,
        cursor="fleur",
    )

    header.pack(fill="x")
    header.pack_propagate(False)

    titulo_label = tk.Label(
        header,
        text=titulo.upper(),
        font=("Segoe UI", 12, "bold"),
        fg=color,
        bg=HEADER_BG,
        cursor="fleur",
    )

    titulo_label.pack(
        side="left",
        padx=18,
        pady=15,
    )

    # ------------------------------------------------------------
    # BOTÓN X
    # ------------------------------------------------------------

    btn_cerrar = tk.Button(
        header,
        text="×",
        command=lambda: _cerrar_dialogo_seguro(dialog),
        bg=HEADER_BG,
        fg=MUTED,
        activebackground=RED,
        activeforeground=TEXT,
        relief="flat",
        bd=0,
        font=("Segoe UI", 14, "bold"),
        width=3,
        cursor="hand2",
    )

    btn_cerrar.pack(
        side="right",
        fill="y",
    )

    # ------------------------------------------------------------
    # ARRASTRAR VENTANA
    # ------------------------------------------------------------

    drag = {
        "x": 0,
        "y": 0,
    }

    def iniciar_arrastre(event):
        drag["x"] = (
            event.x_root - dialog.winfo_x()
        )

        drag["y"] = (
            event.y_root - dialog.winfo_y()
        )

    def mover_ventana(event):
        x = event.x_root - drag["x"]
        y = event.y_root - drag["y"]

        dialog.geometry(
            f"+{x}+{y}"
        )

    for widget in (
        header,
        titulo_label,
    ):
        widget.bind(
            "<ButtonPress-1>",
            iniciar_arrastre,
        )

        widget.bind(
            "<B1-Motion>",
            mover_ventana,
        )

    # ------------------------------------------------------------
    # CUERPO
    # ------------------------------------------------------------

    cuerpo = tk.Frame(
        marco,
        bg=BG,
        padx=22,
        pady=22,
    )

    cuerpo.pack(
        fill="both",
        expand=True,
    )

    # ------------------------------------------------------------
    # ÍCONO
    # ------------------------------------------------------------

    icono = tk.Canvas(
        cuerpo,
        width=58,
        height=58,
        bg=BG,
        highlightthickness=0,
    )

    icono.pack(
        side="left",
        padx=(0, 18),
        anchor="n",
    )

    icono.create_oval(
        5,
        5,
        53,
        53,
        fill=color,
        outline="",
    )

    icono.create_text(
        29,
        29,
        text=simbolo,
        fill=TEXT,
        font=("Segoe UI", 20, "bold"),
    )

    # ------------------------------------------------------------
    # CONTENIDO
    # ------------------------------------------------------------

    contenido = tk.Frame(
        cuerpo,
        bg=BG,
    )

    contenido.pack(
        side="left",
        fill="both",
        expand=True,
    )

    # ------------------------------------------------------------
    # FOOTER
    # ------------------------------------------------------------

    footer = tk.Frame(
        marco,
        bg=PANEL,
        padx=14,
        pady=12,
    )

    footer.pack(
        fill="x",
        side="bottom",
    )

    # ------------------------------------------------------------
    # CENTRAR
    # ------------------------------------------------------------

    _centrar(
        dialog,
        parent,
        ancho,
        alto,
    )

    # ------------------------------------------------------------
    # MOSTRAR Y HACER MODAL
    # ------------------------------------------------------------

    dialog.update_idletasks()
    dialog.lift()

    try:
        dialog.focus_force()

    except tk.TclError:
        pass

    try:
        dialog.grab_set()

    except tk.TclError:
        pass

    return (
        dialog,
        contenido,
        footer,
        color,
    )


# ================================================================
# MENSAJE DE SALIDA
# Ejemplo:
# mostrar_mensaje(self, "Información", "Operación realizada.")
# ================================================================

def mostrar_mensaje(
    parent,
    titulo,
    mensaje,
    tipo="info",
    texto_boton="Aceptar",
):
    """
    Muestra un mensaje modal personalizado.

    Tipos disponibles:
    - success
    - info
    - warning
    - error
    """

    dialog, contenido, footer, color = _crear_base(
        parent,
        titulo,
        tipo=tipo,
        ancho=450,
        alto=245,
    )

    tk.Label(
        contenido,
        text=mensaje,
        font=("Segoe UI", 10),
        fg=TEXT,
        bg=BG,
        justify="left",
        anchor="nw",
        wraplength=310,
    ).pack(
        fill="both",
        expand=True,
    )

    boton = tk.Button(
        footer,
        text=texto_boton,
        command=lambda: _cerrar_dialogo_seguro(dialog),
        bg=color,
        fg=TEXT,
        activebackground=color,
        activeforeground=TEXT,
        relief="flat",
        font=("Segoe UI", 9, "bold"),
        padx=22,
        pady=7,
        cursor="hand2",
    )

    boton.pack(
        side="right",
    )

    dialog.bind(
        "<Return>",
        lambda _e: _cerrar_dialogo_seguro(dialog),
    )

    dialog.bind(
        "<Escape>",
        lambda _e: _cerrar_dialogo_seguro(dialog),
    )

    dialog.protocol(
        "WM_DELETE_WINDOW",
        lambda: _cerrar_dialogo_seguro(dialog),
    )

    boton.focus_set()

    dialog.wait_window()


# ================================================================
# MENSAJE DE ÉXITO
# Ejemplo:
# mostrar_exito(self, "Venta registrada", "La venta fue guardada.")
# ================================================================

def mostrar_exito(
    parent,
    titulo,
    mensaje,
    texto_boton="Aceptar",
):
    return mostrar_mensaje(
        parent,
        titulo,
        mensaje,
        "success",
        texto_boton,
    )


# ================================================================
# MENSAJE INFORMATIVO
# Ejemplo:
# mostrar_info(self, "Información", "Caja abierta.")
# ================================================================

def mostrar_info(
    parent,
    titulo,
    mensaje,
    texto_boton="Aceptar",
):
    return mostrar_mensaje(
        parent,
        titulo,
        mensaje,
        "info",
        texto_boton,
    )


# ================================================================
# MENSAJE DE ADVERTENCIA
# Ejemplo:
# mostrar_advertencia(self, "Atención", "El carrito está vacío.")
# ================================================================

def mostrar_advertencia(
    parent,
    titulo,
    mensaje,
    texto_boton="Aceptar",
):
    return mostrar_mensaje(
        parent,
        titulo,
        mensaje,
        "warning",
        texto_boton,
    )


# ================================================================
# MENSAJE DE ERROR
# Ejemplo:
# mostrar_error(self, "Error", "No se pudo conectar.")
# ================================================================

def mostrar_error(
    parent,
    titulo,
    mensaje,
    texto_boton="Aceptar",
):
    return mostrar_mensaje(
        parent,
        titulo,
        mensaje,
        "error",
        texto_boton,
    )


# ================================================================
# MENSAJE DE CONFIRMACIÓN
# Ejemplo:
#
# if confirmar(self, "Confirmar", "¿Desea continuar?"):
#     ...
# ================================================================

def confirmar(
    parent,
    titulo,
    mensaje,
    texto_confirmar="Confirmar",
    texto_cancelar="Cancelar",
    tipo="question",
    peligro=False,
):
    """
    Muestra una confirmación personalizada.

    Retorna:
        True  -> usuario confirma
        False -> usuario cancela
    """

    dialog, contenido, footer, color = _crear_base(
        parent,
        titulo,
        tipo=tipo,
        ancho=470,
        alto=255,
    )

    if peligro:
        color_confirmar = RED
    else:
        color_confirmar = color

    tk.Label(
        contenido,
        text=mensaje,
        font=("Segoe UI", 10),
        fg=TEXT,
        bg=BG,
        justify="left",
        anchor="nw",
        wraplength=325,
    ).pack(
        fill="both",
        expand=True,
    )

    resultado = {
        "valor": False,
    }

    def aceptar():
        resultado["valor"] = True
        _cerrar_dialogo_seguro(dialog)

    def cancelar():
        resultado["valor"] = False
        _cerrar_dialogo_seguro(dialog)

    tk.Button(
        footer,
        text=texto_confirmar,
        command=aceptar,
        bg=color_confirmar,
        fg=TEXT,
        activebackground=color_confirmar,
        activeforeground=TEXT,
        relief="flat",
        font=("Segoe UI", 9, "bold"),
        padx=18,
        pady=7,
        cursor="hand2",
    ).pack(
        side="right",
        padx=(8, 0),
    )

    btn_cancelar = tk.Button(
        footer,
        text=texto_cancelar,
        command=cancelar,
        bg=PANEL_2,
        fg=TEXT,
        activebackground=PANEL_2,
        activeforeground=TEXT,
        relief="flat",
        font=("Segoe UI", 9, "bold"),
        padx=18,
        pady=7,
        cursor="hand2",
    )

    btn_cancelar.pack(
        side="right",
    )

    dialog.bind(
        "<Return>",
        lambda _e: aceptar(),
    )

    dialog.bind(
        "<Escape>",
        lambda _e: cancelar(),
    )

    dialog.protocol(
        "WM_DELETE_WINDOW",
        cancelar,
    )

    btn_cancelar.focus_set()

    dialog.wait_window()

    return resultado["valor"]


# ================================================================
# PEDIR TEXTO
# Ejemplo:
#
# nombre = pedir_texto(
#     self,
#     "Nombre",
#     "Ingrese el nombre:",
# )
# ================================================================

def pedir_texto(
    parent,
    titulo,
    mensaje,
    etiqueta="Valor:",
    valor_inicial="",
    texto_confirmar="Aceptar",
    permitir_vacio=False,
    solo_digitos=False,
):
    """
    Solicita texto al usuario.

    Retorna:
        str  -> valor ingresado
        None -> usuario cancela
    """

    dialog, contenido, footer, _color = _crear_base(
        parent,
        titulo,
        tipo="info",
        ancho=480,
        alto=315,
    )

    tk.Label(
        contenido,
        text=mensaje,
        font=("Segoe UI", 10),
        fg=TEXT,
        bg=BG,
        justify="left",
        anchor="w",
        wraplength=330,
    ).pack(
        fill="x",
        pady=(0, 14),
    )

    tk.Label(
        contenido,
        text=etiqueta,
        font=("Segoe UI", 9, "bold"),
        fg=MUTED,
        bg=BG,
        anchor="w",
    ).pack(
        fill="x",
        pady=(0, 5),
    )

    variable = tk.StringVar(
        value=str(valor_inicial)
    )

    kwargs_entry = {}

    if solo_digitos:

        def validar(nuevo):
            return (
                nuevo == ""
                or nuevo.isdigit()
            )

        vcmd = (
            dialog.register(validar),
            "%P",
        )

        kwargs_entry.update(
            validate="key",
            validatecommand=vcmd,
        )

    entry = tk.Entry(
        contenido,
        textvariable=variable,
        font=("Segoe UI", 13),
        justify="center",
        bg=PANEL_2,
        fg=TEXT,
        insertbackground=TEXT,
        relief="flat",
        bd=0,
        **kwargs_entry,
    )

    entry.pack(
        fill="x",
        ipady=9,
    )

    lbl_error = tk.Label(
        contenido,
        text="",
        font=("Segoe UI", 8),
        fg=RED,
        bg=BG,
        anchor="w",
    )

    lbl_error.pack(
        fill="x",
        pady=(5, 0),
    )

    resultado = {
        "valor": None,
    }

    def aceptar():
        valor = variable.get().strip()

        if (
            not permitir_vacio
            and not valor
        ):
            lbl_error.config(
                text="Este campo es obligatorio."
            )

            entry.focus_set()
            return

        resultado["valor"] = valor

        _cerrar_dialogo_seguro(dialog)

    def cancelar():
        resultado["valor"] = None

        _cerrar_dialogo_seguro(dialog)

    tk.Button(
        footer,
        text=texto_confirmar,
        command=aceptar,
        bg=GREEN,
        fg=TEXT,
        activebackground=GREEN,
        activeforeground=TEXT,
        relief="flat",
        font=("Segoe UI", 9, "bold"),
        padx=18,
        pady=7,
        cursor="hand2",
    ).pack(
        side="right",
        padx=(8, 0),
    )

    tk.Button(
        footer,
        text="Cancelar",
        command=cancelar,
        bg=PANEL_2,
        fg=TEXT,
        activebackground=PANEL_2,
        activeforeground=TEXT,
        relief="flat",
        font=("Segoe UI", 9, "bold"),
        padx=18,
        pady=7,
        cursor="hand2",
    ).pack(
        side="right",
    )

    dialog.bind(
        "<Return>",
        lambda _e: aceptar(),
    )

    dialog.bind(
        "<Escape>",
        lambda _e: cancelar(),
    )

    dialog.protocol(
        "WM_DELETE_WINDOW",
        cancelar,
    )

    entry.focus_set()
    entry.selection_range(
        0,
        tk.END,
    )

    dialog.wait_window()

    return resultado["valor"]


# ================================================================
# PEDIR MONTO EN GUARANÍES
# Ejemplo:
#
# monto = pedir_monto(
#     self,
#     "Apertura de caja",
#     "Ingrese el fondo inicial:",
# )
# ================================================================

def pedir_monto(
    parent,
    titulo,
    mensaje,
    etiqueta="Monto en Guaraníes:",
    valor_inicial="0",
    texto_confirmar="Aceptar",
):
    """
    Solicita un monto en Guaraníes.

    Acepta:
        100000
        100.000
        100,000

    Retorna:
        Decimal -> monto válido
        None    -> usuario cancela
    """

    dialog, contenido, footer, _color = _crear_base(
        parent,
        titulo,
        tipo="info",
        ancho=490,
        alto=325,
    )

    tk.Label(
        contenido,
        text=mensaje,
        font=("Segoe UI", 10),
        fg=TEXT,
        bg=BG,
        justify="left",
        anchor="w",
        wraplength=335,
    ).pack(
        fill="x",
        pady=(0, 14),
    )

    tk.Label(
        contenido,
        text=etiqueta,
        font=("Segoe UI", 9, "bold"),
        fg=MUTED,
        bg=BG,
        anchor="w",
    ).pack(
        fill="x",
        pady=(0, 5),
    )

    variable = tk.StringVar(
        value=str(valor_inicial)
    )

    def validar_tecla(nuevo):
        if nuevo == "":
            return True

        return all(
            c.isdigit()
            or c in "., "
            for c in nuevo
        )

    vcmd = (
        dialog.register(validar_tecla),
        "%P",
    )

    entry = tk.Entry(
        contenido,
        textvariable=variable,
        font=("Segoe UI", 14, "bold"),
        justify="center",
        bg=PANEL_2,
        fg=TEXT,
        insertbackground=TEXT,
        relief="flat",
        bd=0,
        validate="key",
        validatecommand=vcmd,
    )

    entry.pack(
        fill="x",
        ipady=9,
    )

    lbl_error = tk.Label(
        contenido,
        text="",
        font=("Segoe UI", 8),
        fg=RED,
        bg=BG,
        anchor="w",
    )

    lbl_error.pack(
        fill="x",
        pady=(5, 0),
    )

    resultado = {
        "valor": None,
    }

    # ------------------------------------------------------------
    # CONVERTIR TEXTO A DECIMAL
    # ------------------------------------------------------------

    def convertir():
        limpio = variable.get().strip()

        for token in (
            "Gs.",
            "GS.",
            "Gs",
            "GS",
            "₲",
        ):
            limpio = limpio.replace(
                token,
                "",
            )

        limpio = (
            limpio
            .replace(".", "")
            .replace(",", "")
            .replace(" ", "")
        )

        if limpio == "":
            return Decimal("0")

        try:
            monto = Decimal(limpio)

        except (
            InvalidOperation,
            ValueError,
        ):
            raise ValueError(
                "El monto ingresado no es válido."
            )

        if (
            not monto.is_finite()
            or monto < 0
        ):
            raise ValueError(
                "El monto debe ser un número mayor o igual a cero."
            )

        return monto

    # ------------------------------------------------------------
    # ACEPTAR
    # ------------------------------------------------------------

    def aceptar():
        try:
            resultado["valor"] = convertir()

        except ValueError as exc:
            lbl_error.config(
                text=str(exc)
            )

            entry.focus_set()
            return

        _cerrar_dialogo_seguro(dialog)

    # ------------------------------------------------------------
    # CANCELAR
    # ------------------------------------------------------------

    def cancelar():
        resultado["valor"] = None

        _cerrar_dialogo_seguro(dialog)

    # ------------------------------------------------------------
    # BOTONES
    # ------------------------------------------------------------

    tk.Button(
        footer,
        text=texto_confirmar,
        command=aceptar,
        bg=GREEN,
        fg=TEXT,
        activebackground=GREEN,
        activeforeground=TEXT,
        relief="flat",
        font=("Segoe UI", 9, "bold"),
        padx=18,
        pady=7,
        cursor="hand2",
    ).pack(
        side="right",
        padx=(8, 0),
    )

    tk.Button(
        footer,
        text="Cancelar",
        command=cancelar,
        bg=PANEL_2,
        fg=TEXT,
        activebackground=PANEL_2,
        activeforeground=TEXT,
        relief="flat",
        font=("Segoe UI", 9, "bold"),
        padx=18,
        pady=7,
        cursor="hand2",
    ).pack(
        side="right",
    )

    # ------------------------------------------------------------
    # ATAJOS
    # ------------------------------------------------------------

    dialog.bind(
        "<Return>",
        lambda _e: aceptar(),
    )

    dialog.bind(
        "<Escape>",
        lambda _e: cancelar(),
    )

    dialog.protocol(
        "WM_DELETE_WINDOW",
        cancelar,
    )

    entry.focus_set()

    entry.selection_range(
        0,
        tk.END,
    )

    dialog.wait_window()

    return resultado["valor"]