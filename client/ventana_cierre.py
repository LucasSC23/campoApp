import sys
import ctypes
import threading
import tkinter as tk
from decimal import Decimal, InvalidOperation
from tkinter import ttk

from client.ui_dialogos import (
    confirmar,
    mostrar_error,
    mostrar_exito,
)
BG = "#141722"
HEADER_BG = "#11141d"
PANEL = "#1c2030"
PANEL_2 = "#252a3e"
TEXT = "#ffffff"
MUTED = "#a0a5b5"
GREEN = "#10b981"
RED = "#ef4444"
BLUE = "#60a5fa"
ORANGE = "#ff8c2b"



def _colorref(hex_color):
    """Convierte #RRGGBB al COLORREF que usa Windows (0x00BBGGRR)."""
    valor = hex_color.lstrip("#")
    r = int(valor[0:2], 16)
    g = int(valor[2:4], 16)
    b = int(valor[4:6], 16)
    return r | (g << 8) | (b << 16)


def aplicar_barra_titulo_campo_burger(ventana):
    """
    Colorea la barra nativa de Windows para integrarla con Campo Burger POS.

    Mantiene minimizar, maximizar, mover, redimensionar y cerrar nativos.
    En versiones de Windows que no soportan color exacto, intenta al menos
    activar el modo oscuro de la barra de título.
    """
    if sys.platform != "win32":
        return

    try:
        ventana.update_idletasks()

        hwnd_cliente = ventana.winfo_id()
        hwnd = ctypes.windll.user32.GetParent(hwnd_cliente)
        if not hwnd:
            hwnd = hwnd_cliente

        dwm = ctypes.windll.dwmapi

        # Modo oscuro de la barra. El atributo cambió entre builds de Windows.
        oscuro = ctypes.c_int(1)
        resultado = dwm.DwmSetWindowAttribute(
            hwnd,
            20,  # DWMWA_USE_IMMERSIVE_DARK_MODE (Windows 10/11 recientes)
            ctypes.byref(oscuro),
            ctypes.sizeof(oscuro),
        )
        if resultado != 0:
            dwm.DwmSetWindowAttribute(
                hwnd,
                19,  # fallback para algunas builds anteriores
                ctypes.byref(oscuro),
                ctypes.sizeof(oscuro),
            )

        # Windows 11 permite además definir los colores exactos.
        atributos_colores = (
            (35, HEADER_BG),  # DWMWA_CAPTION_COLOR
            (36, TEXT),       # DWMWA_TEXT_COLOR
            (34, HEADER_BG),  # DWMWA_BORDER_COLOR
        )

        for atributo, color_hex in atributos_colores:
            color = ctypes.c_int(_colorref(color_hex))
            dwm.DwmSetWindowAttribute(
                hwnd,
                atributo,
                ctypes.byref(color),
                ctypes.sizeof(color),
            )

    except Exception:
        # La estética nunca debe impedir que el POS funcione.
        pass


def configurar_barra_titulo_campo_burger(ventana):
    """Aplica/reaplica el estilo cuando Windows muestra o restaura la ventana."""
    ventana.after(
        25,
        lambda: aplicar_barra_titulo_campo_burger(ventana),
    )

    ventana.bind(
        "<Map>",
        lambda _event: ventana.after(
            25,
            lambda: aplicar_barra_titulo_campo_burger(ventana),
        ),
        add="+",
    )



def configurar_estilo_scrollbars(style):
    """Aplica el estilo Campo Burger a las barras de desplazamiento."""

    style.configure(
        "Campo.Vertical.TScrollbar",
        troughcolor=PANEL,
        background="#374151",
        darkcolor="#374151",
        lightcolor="#374151",
        bordercolor=PANEL,
        arrowcolor=TEXT,
        relief="flat",
        gripcount=0,
        arrowsize=12,
    )

    style.map(
        "Campo.Vertical.TScrollbar",
        background=[
            ("active", "#4b5563"),
            ("pressed", ORANGE),
        ],
        arrowcolor=[
            ("active", TEXT),
            ("pressed", TEXT),
        ],
    )

    style.configure(
        "Campo.Horizontal.TScrollbar",
        troughcolor=PANEL,
        background="#374151",
        darkcolor="#374151",
        lightcolor="#374151",
        bordercolor=PANEL,
        arrowcolor=TEXT,
        relief="flat",
        gripcount=0,
        arrowsize=12,
    )

    style.map(
        "Campo.Horizontal.TScrollbar",
        background=[
            ("active", "#4b5563"),
            ("pressed", ORANGE),
        ],
        arrowcolor=[
            ("active", TEXT),
            ("pressed", TEXT),
        ],
    )


def activar_estilo_campo_burger(ventana):
    """Configura el tema ttk y las scrollbars del POS."""
    style = ttk.Style(ventana)

    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    configurar_estilo_scrollbars(style)
    return style



def fmt_gs(monto):
    try:
        return f"Gs. {int(Decimal(str(monto))):,}".replace(",", ".")
    except (InvalidOperation, ValueError, TypeError):
        return f"Gs. {monto}"


class VentanaCierreCaja(tk.Toplevel):
    """Resumen de la sesión abierta y cierre del turno."""

    def __init__(self, parent, db):
        super().__init__(parent)

        self.parent = parent
        self.db = db
        self._cerrando = False

        self.title("Cierre de Caja")

        # 680 px para que el footer no quede debajo de la barra de tareas
        self.geometry("590x680")
        self.minsize(540, 560)
        self.resizable(True, True)

        self.configure(bg=BG)
        self.transient(parent)
        self.grab_set()
        configurar_barra_titulo_campo_burger(self)

        # Estilo ttk de esta ventana.
        self._ttk_style = activar_estilo_campo_burger(self)

        self._crear_interfaz()
        self.cargar_datos()

    # ==================================================================
    # INTERFAZ
    # ==================================================================

    def _crear_interfaz(self):
        # --------------------------------------------------------------
        # HEADER
        # --------------------------------------------------------------
        header = tk.Frame(
            self,
            bg=PANEL,
            padx=16,
            pady=14,
        )
        header.pack(fill="x")

        tk.Label(
            header,
            text="RESUMEN Y CIERRE DE CAJA",
            font=("Helvetica", 14, "bold"),
            fg=TEXT,
            bg=PANEL,
        ).pack()

        self.lbl_sesion = tk.Label(
            header,
            text="",
            font=("Helvetica", 9, "bold"),
            fg=BLUE,
            bg=PANEL,
        )
        self.lbl_sesion.pack(pady=(4, 0))

        # --------------------------------------------------------------
        # FOOTER FIJO
        # IMPORTANTE: se crea antes del contenido expandible.
        # --------------------------------------------------------------
        footer = tk.Frame(
            self,
            bg=BG,
            padx=20,
            pady=12,
        )
        footer.pack(
            side="bottom",
            fill="x",
        )

        self.btn_cancelar = tk.Button(
            footer,
            text="Cancelar",
            command=self.destroy,
            bg="#374151",
            fg=TEXT,
            activebackground="#4b5563",
            activeforeground=TEXT,
            relief="flat",
            font=("Helvetica", 10, "bold"),
            padx=16,
            pady=8,
            cursor="hand2",
        )
        self.btn_cancelar.pack(side="left")

        self.btn_cerrar = tk.Button(
            footer,
            text="Guardar y Cerrar Caja",
            command=self.cerrar_caja,
            bg=RED,
            fg=TEXT,
            activebackground="#dc2626",
            activeforeground=TEXT,
            relief="flat",
            font=("Helvetica", 10, "bold"),
            padx=18,
            pady=8,
            cursor="hand2",
        )
        self.btn_cerrar.pack(side="right")

        # --------------------------------------------------------------
        # CONTENIDO
        # --------------------------------------------------------------
        container = tk.Frame(
            self,
            bg=BG,
            padx=20,
            pady=10,
        )
        container.pack(
            fill="both",
            expand=True,
        )

        self.lbl_monto_inicial = self._label_resumen(container)
        self.lbl_monto_inicial.pack(fill="x", pady=2)

        self.lbl_total_ventas = self._label_resumen(container)
        self.lbl_total_ventas.pack(fill="x", pady=2)

        # Nombre único y consistente en todo el archivo:
        self.lbl_efectivo_recibido = self._label_resumen(container)
        self.lbl_efectivo_recibido.pack(fill="x", pady=2)

        self.lbl_efectivo_esperado = tk.Label(
            container,
            text="EFECTIVO ESPERADO: Gs. 0",
            fg=GREEN,
            bg=PANEL,
            font=("Helvetica", 12, "bold"),
            pady=11,
            relief="groove",
        )
        self.lbl_efectivo_esperado.pack(
            fill="x",
            pady=10,
        )

        self.lbl_cantidades = tk.Label(
            container,
            text="",
            fg=MUTED,
            bg=BG,
            font=("Helvetica", 9),
            anchor="w",
        )
        self.lbl_cantidades.pack(
            fill="x",
            pady=(0, 8),
        )

        tk.Label(
            container,
            text="Ventas por método de pago",
            fg=TEXT,
            bg=BG,
            font=("Helvetica", 10, "bold"),
            anchor="w",
        ).pack(
            fill="x",
            pady=(5, 3),
        )

        self.frame_pagos = tk.Frame(
            container,
            bg=PANEL,
            padx=12,
            pady=8,
        )
        self.frame_pagos.pack(
            fill="x",
            pady=(0, 10),
        )

        tk.Label(
            container,
            text="Ventas por categoría y subcategoría",
            fg=TEXT,
            bg=BG,
            font=("Helvetica", 10, "bold"),
            anchor="w",
        ).pack(
            fill="x",
            pady=(5, 3),
        )

        # --------------------------------------------------------------
        # ÚNICAMENTE ESTA PARTE TIENE SCROLL
        # --------------------------------------------------------------
        scroll_container = tk.Frame(
            container,
            bg=PANEL,
        )
        scroll_container.pack(
            fill="both",
            expand=True,
        )

        self.canvas = tk.Canvas(
            scroll_container,
            bg=PANEL,
            highlightthickness=0,
        )

        scrollbar = ttk.Scrollbar(
            scroll_container,
            orient="vertical",
            command=self.canvas.yview,
            style="Campo.Vertical.TScrollbar",
        )

        self.frame_categorias = tk.Frame(
            self.canvas,
            bg=PANEL,
            padx=10,
            pady=8,
        )

        self.cat_window_id = self.canvas.create_window(
            (0, 0),
            window=self.frame_categorias,
            anchor="nw",
        )

        self.frame_categorias.bind(
            "<Configure>",
            lambda _e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            ),
        )

        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(
                self.cat_window_id,
                width=e.width,
            ),
        )

        self.canvas.configure(
            yscrollcommand=scrollbar.set
        )

        self.canvas.pack(
            side="left",
            fill="both",
            expand=True,
        )

        scrollbar.pack(
            side="right",
            fill="y",
        )

    def _label_resumen(self, parent):
        return tk.Label(
            parent,
            text="",
            fg=MUTED,
            bg=BG,
            font=("Helvetica", 10),
            anchor="w",
        )

    # ==================================================================
    # DATOS
    # ==================================================================

    def cargar_datos(self):
        """
        Carga el resumen. La consulta se hace en un thread para no bloquear
        la ventana mientras Supabase responde.
        """
        self.lbl_efectivo_recibido.config(text="Cargando...")
        self.btn_cerrar.config(state="disabled")

        threading.Thread(
            target=self._cargar_datos_bd,
            daemon=True,
        ).start()

    def _cargar_datos_bd(self):
        try:
            sesion = self.db.obtener_sesion_abierta()
            resumen = self.db.obtener_resumen_caja()

            self.after(
                0,
                lambda: self._aplicar_datos(
                    sesion,
                    resumen,
                ),
            )

        except Exception as exc:
            mensaje = str(exc)

            self.after(
                0,
                lambda msg=mensaje: self._error_carga(msg),
            )

    def _aplicar_datos(self, sesion, resumen):
        if not sesion:
            self.lbl_sesion.config(
                text="NO HAY SESIÓN ABIERTA"
            )
            self.lbl_efectivo_recibido.config(text="")
            self.btn_cerrar.config(state="disabled")
            return

        self.lbl_sesion.config(
            text=(
                f"Sesión #{sesion['id']} · "
                f"abierta {sesion['fecha_apertura']:%d/%m/%Y %H:%M}"
            )
        )

        monto_inicial = resumen.get(
            "monto_inicial",
            Decimal("0"),
        )

        total_ventas = resumen.get(
            "total_ventas",
            Decimal("0"),
        )

        desglose_pagos = resumen.get(
            "desglose_pagos",
            {},
        )

        efectivo_recibido = desglose_pagos.get(
            "Efectivo",
            Decimal("0"),
        )

        efectivo_esperado = resumen.get(
            "efectivo_esperado",
            monto_inicial + efectivo_recibido,
        )

        self.lbl_monto_inicial.config(
            text=f"Fondo inicial: {fmt_gs(monto_inicial)}"
        )

        self.lbl_total_ventas.config(
            text=f"Total procesado en ventas: {fmt_gs(total_ventas)}"
        )

        self.lbl_efectivo_recibido.config(
            text=(
                "Efectivo recibido por ventas: "
                f"{fmt_gs(efectivo_recibido)}"
            )
        )

        self.lbl_efectivo_esperado.config(
            text=(
                "EFECTIVO ESPERADO: "
                f"{fmt_gs(efectivo_esperado)}"
            )
        )

        self.lbl_cantidades.config(
            text=(
                f"Ventas completadas: "
                f"{resumen.get('ventas_completadas', 0)}"
                "   |   "
                f"Ventas anuladas: "
                f"{resumen.get('ventas_anuladas', 0)}"
            )
        )

        # --------------------------------------------------------------
        # MÉTODOS DE PAGO
        # --------------------------------------------------------------
        for widget in self.frame_pagos.winfo_children():
            widget.destroy()

        if desglose_pagos:
            for metodo, monto in desglose_pagos.items():
                tk.Label(
                    self.frame_pagos,
                    text=f"• {metodo}: {fmt_gs(monto)}",
                    fg=MUTED,
                    bg=PANEL,
                    font=("Helvetica", 9),
                    anchor="w",
                ).pack(
                    fill="x",
                    pady=2,
                )
        else:
            tk.Label(
                self.frame_pagos,
                text="Sin ventas registradas.",
                fg=MUTED,
                bg=PANEL,
                font=("Helvetica", 9, "italic"),
            ).pack(anchor="w")

        # --------------------------------------------------------------
        # CATEGORÍAS
        # --------------------------------------------------------------
        for widget in self.frame_categorias.winfo_children():
            widget.destroy()

        categorias = resumen.get(
            "desglose_categorias",
            {},
        )

        if categorias:
            for categoria, subcategorias in categorias.items():
                tk.Label(
                    self.frame_categorias,
                    text=f"▸ {categoria.upper()}",
                    fg=BLUE,
                    bg=PANEL,
                    font=("Helvetica", 9, "bold"),
                    anchor="w",
                ).pack(
                    fill="x",
                    pady=(5, 1),
                )

                for subcategoria, monto in subcategorias.items():
                    tk.Label(
                        self.frame_categorias,
                        text=(
                            f"    • {subcategoria}: "
                            f"{fmt_gs(monto)}"
                        ),
                        fg="#d1d5db",
                        bg=PANEL,
                        font=("Helvetica", 9),
                        anchor="w",
                    ).pack(
                        fill="x",
                        pady=1,
                    )
        else:
            tk.Label(
                self.frame_categorias,
                text="Sin ventas por categoría.",
                fg=MUTED,
                bg=PANEL,
                font=("Helvetica", 9, "italic"),
            ).pack(anchor="w")

        self.btn_cerrar.config(
            state="normal"
        )

    def _error_carga(self, mensaje):
        self.lbl_efectivo_recibido.config(
            text="Error al cargar datos."
        )

        mostrar_error(
            self,
            "Error de caja",
            (
                "No se pudo cargar el cierre de caja.\n\n"
                f"{mensaje}"
            ),
        )

        self.btn_cerrar.config(
            state="disabled"
        )

    # ==================================================================
    # CIERRE
    # ==================================================================

    def cerrar_caja(self):
        if self._cerrando:
            return

        confirmado = confirmar(
            self,
            "Confirmar cierre",
            (
                "¿Está seguro de guardar el cierre "
                "y finalizar el turno?\n\n"
                "Las ventas permanecerán registradas "
                "como COMPLETADA o ANULADA."
            ),
            texto_confirmar="Sí, cerrar caja",
            texto_cancelar="Cancelar",
            peligro=True,
        )

        if not confirmado:
            return

        self._cerrando = True

        self.btn_cerrar.config(
            state="disabled",
            text="Guardando cierre...",
        )

        self.btn_cancelar.config(
            state="disabled"
        )

        self.config(
            cursor="watch"
        )

        threading.Thread(
            target=self._cerrar_caja_bd,
            daemon=True,
        ).start()

    def _cerrar_caja_bd(self):
        try:
            sesion_id = self.db.cerrar_caja()

            self.after(
                0,
                lambda: self._cierre_exitoso(
                    sesion_id
                ),
            )

        except Exception as exc:
            mensaje = str(exc)

            self.after(
                0,
                lambda msg=mensaje: self._cierre_error(msg),
            )

    def _cierre_exitoso(self, sesion_id):
        self.config(
            cursor=""
        )

        mostrar_exito(
            self,
            "Caja cerrada",
            (
                f"La sesión #{sesion_id} "
                "fue guardada y cerrada correctamente."
            ),
        )

        self.destroy()

        if hasattr(
            self.parent,
            "on_caja_cerrada",
        ):
            self.parent.on_caja_cerrada()

    def _cierre_error(self, mensaje):
        self._cerrando = False

        self.config(
            cursor=""
        )

        self.btn_cerrar.config(
            state="normal",
            text="Guardar y Cerrar Caja",
        )

        self.btn_cancelar.config(
            state="normal"
        )

        mostrar_error(
            self,
            "No se pudo cerrar la caja",
            mensaje,
        )
