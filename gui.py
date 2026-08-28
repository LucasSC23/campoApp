import datetime
import os
import queue
import threading
import tkinter as tk
from decimal import Decimal, InvalidOperation
from tkinter import messagebox, simpledialog, ttk

from ventana_cierre import VentanaCierreCaja
from ventana_reportes import VentanaReportes


BG = "#141722"
PANEL = "#1c2030"
PANEL_2 = "#252a3e"
HEADER_BG = "#11141d"
ORANGE = "#ff8c2b"
GREEN = "#2ecc71"
RED = "#ff4d4d"
TEXT = "#ffffff"
MUTED = "#a0a5b5"


def fmt_gs(monto):
    try:
        return f"Gs. {int(Decimal(str(monto))):,}".replace(",", ".")
    except (InvalidOperation, ValueError, TypeError):
        return f"Gs. {monto}"


def parse_gs(texto):
    if texto is None:
        return None

    limpio = str(texto).strip()
    for token in ("Gs.", "GS.", "Gs", "GS", "₲"):
        limpio = limpio.replace(token, "")

    limpio = limpio.replace(".", "").replace(",", "").replace(" ", "")

    if limpio == "":
        return Decimal("0")

    try:
        monto = Decimal(limpio)
    except InvalidOperation as exc:
        raise ValueError("El monto ingresado no es válido.") from exc

    if monto < 0:
        raise ValueError("El monto no puede ser negativo.")

    return monto


def bind_mousewheel_local(canvas):
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_enter(_event):
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def _on_leave(_event):
        canvas.unbind_all("<MouseWheel>")

    canvas.bind("<Enter>", _on_enter)
    canvas.bind("<Leave>", _on_leave)


class VentanaHistorialVentas(tk.Toplevel):
    """Ventas completadas de la sesión de caja abierta."""

    def __init__(self, parent, db):
        super().__init__(parent)
        self.parent = parent
        self.db = db

        self.title("Ventas del Turno")
        self.geometry("720x540")
        self.minsize(620, 440)
        self.configure(bg=BG)
        self.transient(parent)

        tk.Label(
            self,
            text="VENTAS DEL TURNO ACTUAL",
            font=("Helvetica", 12, "bold"),
            fg=ORANGE,
            bg=BG,
        ).pack(pady=12)

        canvas_frame = tk.Frame(self, bg=BG)
        canvas_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.canvas = tk.Canvas(canvas_frame, bg=BG, highlightthickness=0)
        bind_mousewheel_local(self.canvas)

        scrollbar = ttk.Scrollbar(
            canvas_frame,
            orient="vertical",
            command=self.canvas.yview,
        )

        self.frame_ventas = tk.Frame(self.canvas, bg=BG)
        self.window_id = self.canvas.create_window(
            (0, 0),
            window=self.frame_ventas,
            anchor="nw",
        )

        self.frame_ventas.bind(
            "<Configure>",
            lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.window_id, width=e.width),
        )

        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.cargar_datos()

    def _mostrar_cargando(self, texto="Cargando ventas..."):
        for widget in self.frame_ventas.winfo_children():
            widget.destroy()
        tk.Label(
            self.frame_ventas,
            text=texto,
            font=("Helvetica", 10),
            fg=MUTED,
            bg=BG,
        ).pack(pady=150)

    def cargar_datos(self):
        self._mostrar_cargando()
        self.parent.run_async(
            self.db.obtener_ventas_sesion_activa,
            self._render_ventas,
            self._mostrar_error,
        )

    def _mostrar_error(self, mensaje):
        if not self.winfo_exists():
            return
        messagebox.showerror(
            "Error",
            f"No se pudieron consultar las ventas del turno:\n{mensaje}",
            parent=self,
        )
        self._mostrar_cargando("No se pudieron cargar las ventas.")

    def _render_ventas(self, ventas):
        if not self.winfo_exists():
            return

        for widget in self.frame_ventas.winfo_children():
            widget.destroy()

        if not ventas:
            tk.Label(
                self.frame_ventas,
                text="Todavía no hay ventas completadas en este turno.",
                font=("Helvetica", 11),
                fg=MUTED,
                bg=BG,
            ).pack(pady=150)
            return

        for venta_id, hora, monto, metodo, detalle in ventas:
            card = tk.Frame(self.frame_ventas, bg=PANEL, padx=12, pady=10)
            card.pack(fill="x", pady=4)

            top = tk.Frame(card, bg=PANEL)
            top.pack(fill="x")

            tk.Label(
                top,
                text=f"Ticket #{venta_id}  |  {hora} hs  |  {fmt_gs(monto)}",
                font=("Helvetica", 9, "bold"),
                fg=TEXT,
                bg=PANEL,
            ).pack(side="left")

            tk.Button(
                top,
                text="Anular",
                command=lambda vid=venta_id: self.anular(vid),
                bg=RED,
                fg=TEXT,
                relief="flat",
                font=("Helvetica", 8, "bold"),
                cursor="hand2",
                padx=8,
            ).pack(side="right")

            combo = ttk.Combobox(
                top,
                values=["Efectivo", "POS / Tarjeta", "Transferencia"],
                state="readonly",
                width=16,
            )
            combo.set(metodo)
            combo.pack(side="right", padx=8)
            combo.bind(
                "<<ComboboxSelected>>",
                lambda _e, vid=venta_id, cb=combo: self.cambiar_metodo(
                    vid, cb.get()
                ),
            )

            detalle_frame = tk.Frame(card, bg=BG, padx=10, pady=7)
            detalle_frame.pack(fill="x", pady=(7, 0))

            for item in detalle:
                obs = f" ({item['obs']})" if item.get("obs") else ""
                prefijo = "  + " if item.get("es_extra") else "• "
                tk.Label(
                    detalle_frame,
                    text=(
                        f"{prefijo}{item['cant']}x {item['nombre']}{obs}"
                        f"  —  {fmt_gs(item['subtotal'])}"
                    ),
                    font=("Helvetica", 8),
                    fg=TEXT,
                    bg=BG,
                    anchor="w",
                    justify="left",
                ).pack(fill="x")

    def cambiar_metodo(self, venta_id, nuevo_metodo):
        self.parent.run_async(
            lambda: self.db.actualizar_metodo_pago_venta(venta_id, nuevo_metodo),
            lambda _resultado: self._despues_de_modificar(),
            lambda mensaje: messagebox.showerror(
                "No se pudo modificar", mensaje, parent=self
            ),
        )

    def _despues_de_modificar(self):
        self.parent.actualizar_header_caja_async()
        self.cargar_datos()

    def anular(self, venta_id):
        if not messagebox.askyesno(
            "Anular venta",
            f"¿Desea anular el Ticket #{venta_id}?",
            parent=self,
        ):
            return

        self._mostrar_cargando("Anulando venta...")
        self.parent.run_async(
            lambda: self.db.anular_venta(venta_id),
            lambda _resultado: self._despues_de_modificar(),
            self._mostrar_error,
        )


class VentanaTicket(tk.Toplevel):
    """Vista previa del ticket y guardado opcional en TXT."""

    def __init__(
        self,
        parent,
        venta_id,
        items,
        total,
        metodo_pago,
        tipo_entrega,
        recargo_delivery,
    ):
        super().__init__(parent)
        self.title(f"Ticket #{venta_id}")
        self.geometry("390x520")
        self.configure(bg=BG)
        self.transient(parent)

        self.texto_ticket = self._armar_texto(
            venta_id,
            items,
            total,
            metodo_pago,
            tipo_entrega,
            recargo_delivery,
        )

        txt = tk.Text(
            self,
            bg="#0f1119",
            fg=TEXT,
            font=("Courier New", 10),
            width=42,
        )
        txt.insert("1.0", self.texto_ticket)
        txt.config(state="disabled")
        txt.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Button(
            self,
            text="Guardar / Imprimir Ticket",
            command=self.guardar_e_imprimir,
            bg=ORANGE,
            fg=TEXT,
            relief="flat",
            font=("Helvetica", 9, "bold"),
            pady=7,
            cursor="hand2",
        ).pack(fill="x", padx=10, pady=(0, 10))

    def _armar_texto(
        self,
        venta_id,
        items,
        total,
        metodo_pago,
        tipo_entrega,
        recargo_delivery,
    ):
        ahora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        lineas = [
            "======= CAMPO BURGER & ACAI =======",
            f"Ticket #{venta_id}",
            f"Fecha: {ahora}",
            f"Entrega: {tipo_entrega}",
            "-" * 35,
        ]

        for item in items:
            obs = f" ({item['obs']})" if item.get("obs") else ""
            lineas.append(f"{item['cant']}x {item['nombre']}{obs}")
            lineas.append(f"{fmt_gs(item['subtotal']):>35}")

        if Decimal(str(recargo_delivery)) > 0:
            lineas.append("-" * 35)
            lineas.append(f"Recargo delivery: {fmt_gs(recargo_delivery)}")

        lineas.extend(
            [
                "-" * 35,
                f"TOTAL: {fmt_gs(total)}",
                f"Pago: {metodo_pago}",
                "=" * 35,
            ]
        )
        return "\n".join(lineas)

    def guardar_e_imprimir(self):
        os.makedirs("tickets", exist_ok=True)
        ruta = os.path.join(
            "tickets",
            f"ticket_{datetime.datetime.now():%Y%m%d_%H%M%S}.txt",
        )

        try:
            with open(ruta, "w", encoding="utf-8") as archivo:
                archivo.write(self.texto_ticket)
        except OSError as exc:
            messagebox.showerror(
                "Error", f"No se pudo guardar el ticket:\n{exc}", parent=self
            )
            return

        try:
            os.startfile(ruta, "print")
            messagebox.showinfo(
                "Ticket",
                f"Ticket guardado y enviado a impresión:\n{ruta}",
                parent=self,
            )
        except (AttributeError, OSError):
            messagebox.showinfo(
                "Ticket guardado",
                f"El ticket se guardó en:\n{ruta}",
                parent=self,
            )


class VentanaPrincipal(tk.Tk):
    """Interfaz principal del POS."""

    CATEGORIAS_MENU = [
        "Hamburguesas",
        "Lomitos y Sándwiches",
        "Agregados",
        "Bebidas",
        "Helados y Postres",
        "Papas Fritas",
    ]

    MAPEO_CATEGORIAS_ANTIGUAS = {
        "papas y agregados": "Papas Fritas",
        "postres": "Helados y Postres",
    }

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.carrito = {}
        self.catalogo_productos = []
        self.categoria_actual = "TODOS"

        self._ui_queue = queue.Queue()
        self._cerrando = False
        self._venta_en_proceso = False
        self._catalogo_cargando = False
        self._header_en_proceso = False

        self.title("Campo Burger & Açaí - Punto de Venta")
        self.geometry("1180x760")
        self.minsize(980, 650)
        self.configure(bg=BG)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.withdraw()
        if not self._asegurar_caja_abierta():
            self.destroy()
            return

        self.crear_interfaz()
        self.deiconify()

        # Procesa callbacks provenientes de threads en el hilo de Tkinter.
        self.after(40, self._procesar_cola_ui)

        self.cargar_catalogo_async(inicial=True)
        self.actualizar_header_caja_async()

    # ================================================================
    # ASINCRONÍA SEGURA PARA TKINTER
    # ================================================================

    def run_async(self, trabajo, al_terminar, al_error=None):
        """Ejecuta trabajo de BD fuera del hilo gráfico."""

        def worker():
            try:
                resultado = trabajo()
            except Exception as exc:
                if al_error is not None:
                    self._ui_queue.put((al_error, (str(exc),), {}))
            else:
                if al_terminar is not None:
                    self._ui_queue.put((al_terminar, (resultado,), {}))

        threading.Thread(target=worker, daemon=True).start()

    def _procesar_cola_ui(self):
        if self._cerrando:
            return

        try:
            while True:
                callback, args, kwargs = self._ui_queue.get_nowait()
                try:
                    callback(*args, **kwargs)
                except tk.TclError:
                    pass
                except Exception as exc:
                    print(f"[UI] Error aplicando callback: {exc}")
        except queue.Empty:
            pass

        if not self._cerrando:
            self.after(40, self._procesar_cola_ui)

    # ================================================================
    # SESIÓN / APERTURA
    # ================================================================

    def _asegurar_caja_abierta(self):
        try:
            sesion = self.db.obtener_sesion_abierta()
        except Exception as exc:
            messagebox.showerror(
                "Error de base de datos",
                f"No se pudo consultar la sesión de caja:\n{exc}",
                parent=self,
            )
            return False

        if sesion is not None:
            return True

        while True:
            entrada = simpledialog.askstring(
                "Apertura de caja",
                (
                    "No existe una sesión de caja abierta.\n\n"
                    "Ingrese el fondo inicial en Guaraníes.\n"
                    "Ejemplo: 150000"
                ),
                parent=self,
            )

            if entrada is None:
                return False

            try:
                monto = parse_gs(entrada)
                sesion_id = self.db.abrir_caja(monto)
                messagebox.showinfo(
                    "Caja abierta",
                    (
                        f"Sesión #{sesion_id} abierta correctamente.\n"
                        f"Fondo inicial: {fmt_gs(monto)}"
                    ),
                    parent=self,
                )
                return True
            except ValueError as exc:
                messagebox.showwarning("Monto inválido", str(exc), parent=self)
            except Exception as exc:
                messagebox.showerror(
                    "No se pudo abrir la caja", str(exc), parent=self
                )
                return False

    # ================================================================
    # CATÁLOGO EN MEMORIA
    # ================================================================

    def cargar_catalogo_async(self, inicial=False):
        if self._catalogo_cargando:
            return

        self._catalogo_cargando = True
        self.btn_recargar_catalogo.config(state="disabled", text="…")
        self._mostrar_estado_catalogo("Cargando catálogo...")

        self.run_async(
            lambda: self.db.obtener_productos_filtrados("TODOS"),
            lambda productos: self._catalogo_cargado(productos, inicial),
            self._error_catalogo,
        )

    def _mostrar_estado_catalogo(self, texto):
        for widget in self.frame_productos_container.winfo_children():
            widget.destroy()
        tk.Label(
            self.frame_productos_container,
            text=texto,
            bg=BG,
            fg=MUTED,
            font=("Helvetica", 11),
        ).pack(pady=100)

    def _catalogo_cargado(self, productos, inicial=False):
        self.catalogo_productos = list(productos)
        self._catalogo_cargando = False
        self.btn_recargar_catalogo.config(state="normal", text="↻")

        print(f"[CATALOGO] {len(self.catalogo_productos)} productos cargados.")
        self.cargar_menu_productos("TODOS" if inicial else self.categoria_actual)

    def _error_catalogo(self, mensaje):
        self._catalogo_cargando = False
        self.btn_recargar_catalogo.config(state="normal", text="↻")
        self._mostrar_estado_catalogo("No se pudo cargar el catálogo.")
        messagebox.showerror(
            "Error de catálogo",
            f"No se pudieron cargar los productos desde Supabase.\n\n{mensaje}",
            parent=self,
        )

    @classmethod
    def _normalizar_categoria_catalogo(cls, categoria):
        original = str(categoria or "").strip()
        return cls.MAPEO_CATEGORIAS_ANTIGUAS.get(original.casefold(), original)

    # ================================================================
    # HEADER DE CAJA
    # ================================================================

    def actualizar_header_caja_async(self):
        if self._header_en_proceso or self._cerrando:
            return

        self._header_en_proceso = True
        self.run_async(
            self.db.obtener_resumen_caja,
            self._aplicar_header,
            self._error_header,
        )

    def _aplicar_header(self, resumen):
        self._header_en_proceso = False

        if not resumen.get("sesion_id"):
            self.lbl_sesion.config(text="CAJA CERRADA")
            self.lbl_resumen_header.config(text="")
            return

        self.lbl_sesion.config(
            text=f"SESIÓN #{resumen['sesion_id']} · ABIERTA"
        )
        self.lbl_resumen_header.config(
            text=(
                f"Ventas: {fmt_gs(resumen['total_ventas'])}   |   "
                f"Efectivo esperado: {fmt_gs(resumen['efectivo_esperado'])}"
            )
        )

    def _error_header(self, mensaje):
        self._header_en_proceso = False
        self.lbl_resumen_header.config(text=f"Error de caja: {mensaje}")

    # Compatibilidad con ventanas que llamaban el método sincrónico.
    def actualizar_header_caja(self):
        self.actualizar_header_caja_async()

    # ================================================================
    # CONSTRUCCIÓN UI
    # ================================================================

    def crear_interfaz(self):
        self._crear_header()
        self._crear_navegacion()
        self._crear_contenido()

    def _crear_header(self):
        header = tk.Frame(self, bg=HEADER_BG, padx=14, pady=10)
        header.pack(fill="x")

        titulo_frame = tk.Frame(header, bg=HEADER_BG)
        titulo_frame.pack(side="left")

        tk.Label(
            titulo_frame,
            text="CAMPO BURGER & AÇAÍ",
            font=("Segoe UI", 18, "bold"),
            fg=ORANGE,
            bg=HEADER_BG,
        ).pack(anchor="w")

        self.lbl_sesion = tk.Label(
            titulo_frame,
            text="",
            font=("Segoe UI", 9, "bold"),
            fg=GREEN,
            bg=HEADER_BG,
        )
        self.lbl_sesion.pack(anchor="w")

        self.lbl_resumen_header = tk.Label(
            header,
            text="Cargando resumen...",
            font=("Segoe UI", 9),
            fg=MUTED,
            bg=HEADER_BG,
        )
        self.lbl_resumen_header.pack(side="right", padx=10)

    def _crear_navegacion(self):
        self.frame_nav = tk.Frame(self, bg=PANEL, padx=10, pady=8)
        self.frame_nav.pack(fill="x")

        self.botones_categoria = {}

        boton_todos = tk.Button(
            self.frame_nav,
            text="TODOS",
            command=lambda: self.cargar_menu_productos("TODOS"),
            bg=ORANGE,
            fg=TEXT,
            relief="flat",
            font=("Helvetica", 9, "bold"),
            padx=10,
            cursor="hand2",
        )
        boton_todos.pack(side="left", padx=3)
        self.botones_categoria["TODOS"] = boton_todos

        for categoria in self.CATEGORIAS_MENU:
            boton = tk.Button(
                self.frame_nav,
                text=categoria.upper(),
                command=lambda cat=categoria: self.cargar_menu_productos(cat),
                bg=PANEL_2,
                fg=TEXT,
                relief="flat",
                font=("Helvetica", 8, "bold"),
                padx=8,
                cursor="hand2",
            )
            boton.pack(side="left", padx=2)
            self.botones_categoria[categoria] = boton

        tk.Button(
            self.frame_nav,
            text="Cerrar Caja",
            command=self.abrir_cierre_caja,
            bg=RED,
            fg=TEXT,
            relief="flat",
            font=("Helvetica", 9, "bold"),
            padx=10,
            cursor="hand2",
        ).pack(side="right", padx=(6, 0))

        tk.Button(
            self.frame_nav,
            text="Reportes",
            command=self.abrir_reportes,
            bg=PANEL_2,
            fg=TEXT,
            relief="flat",
            font=("Helvetica", 9, "bold"),
            padx=10,
            cursor="hand2",
        ).pack(side="right", padx=4)

        tk.Button(
            self.frame_nav,
            text="Ventas del Turno",
            command=self.abrir_historial,
            bg=PANEL_2,
            fg=ORANGE,
            relief="flat",
            font=("Helvetica", 9, "bold"),
            padx=10,
            cursor="hand2",
        ).pack(side="right")

        self.btn_recargar_catalogo = tk.Button(
            self.frame_nav,
            text="↻",
            command=lambda: self.cargar_catalogo_async(inicial=False),
            bg=PANEL_2,
            fg=MUTED,
            relief="flat",
            font=("Helvetica", 10, "bold"),
            width=3,
            cursor="hand2",
        )
        self.btn_recargar_catalogo.pack(side="right", padx=5)

    def _crear_contenido(self):
        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True, padx=10, pady=10)

        left = tk.Frame(main, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.canvas_menu = tk.Canvas(left, bg=BG, highlightthickness=0)
        scrollbar_menu = ttk.Scrollbar(
            left,
            orient="vertical",
            command=self.canvas_menu.yview,
        )
        bind_mousewheel_local(self.canvas_menu)

        self.frame_productos_container = tk.Frame(self.canvas_menu, bg=BG)
        self.menu_window_id = self.canvas_menu.create_window(
            (0, 0),
            window=self.frame_productos_container,
            anchor="nw",
        )

        self.frame_productos_container.bind(
            "<Configure>",
            lambda _e: self.canvas_menu.configure(
                scrollregion=self.canvas_menu.bbox("all")
            ),
        )
        self.canvas_menu.bind(
            "<Configure>",
            lambda e: self.canvas_menu.itemconfig(self.menu_window_id, width=e.width),
        )
        self.canvas_menu.configure(yscrollcommand=scrollbar_menu.set)
        self.canvas_menu.pack(side="left", fill="both", expand=True)
        scrollbar_menu.pack(side="right", fill="y")

        right = tk.Frame(main, bg=PANEL, width=370, padx=10, pady=10)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        tk.Label(
            right,
            text="DETALLE DE LA VENTA",
            font=("Helvetica", 11, "bold"),
            fg=ORANGE,
            bg=PANEL,
        ).pack(anchor="w", pady=(0, 8))

        cart_frame = tk.Frame(right, bg=PANEL)
        cart_frame.pack(fill="both", expand=True)

        self.canvas_carrito = tk.Canvas(
            cart_frame,
            bg=PANEL,
            highlightthickness=0,
        )
        scrollbar_carrito = ttk.Scrollbar(
            cart_frame,
            orient="vertical",
            command=self.canvas_carrito.yview,
        )
        bind_mousewheel_local(self.canvas_carrito)

        self.frame_carrito_items = tk.Frame(self.canvas_carrito, bg=PANEL)
        self.cart_window_id = self.canvas_carrito.create_window(
            (0, 0),
            window=self.frame_carrito_items,
            anchor="nw",
        )
        self.frame_carrito_items.bind(
            "<Configure>",
            lambda _e: self.canvas_carrito.configure(
                scrollregion=self.canvas_carrito.bbox("all")
            ),
        )
        self.canvas_carrito.bind(
            "<Configure>",
            lambda e: self.canvas_carrito.itemconfig(
                self.cart_window_id,
                width=e.width,
            ),
        )
        self.canvas_carrito.configure(yscrollcommand=scrollbar_carrito.set)
        self.canvas_carrito.pack(side="left", fill="both", expand=True)
        scrollbar_carrito.pack(side="right", fill="y")

        self.lbl_total = tk.Label(
            right,
            text="TOTAL: Gs. 0",
            font=("Helvetica", 13, "bold"),
            fg=TEXT,
            bg=PANEL,
        )
        self.lbl_total.pack(anchor="e", pady=(10, 6))

        self.btn_confirmar_venta = tk.Button(
            right,
            text="Confirmar Venta",
            command=self.confirmar_venta,
            bg=GREEN,
            fg=TEXT,
            activebackground=GREEN,
            activeforeground=TEXT,
            relief="flat",
            font=("Helvetica", 10, "bold"),
            pady=8,
            cursor="hand2",
        )
        self.btn_confirmar_venta.pack(fill="x", pady=(0, 6))

        tk.Button(
            right,
            text="Vaciar Carrito",
            command=self.vaciar_carrito,
            bg=PANEL_2,
            fg=MUTED,
            relief="flat",
            pady=5,
            cursor="hand2",
        ).pack(fill="x")

    # ================================================================
    # MENÚ / CATÁLOGO LOCAL
    # ================================================================

    def _actualizar_boton_categoria_activa(self, categoria):
        for nombre, boton in self.botones_categoria.items():
            boton.configure(bg=ORANGE if nombre == categoria else PANEL_2)

    def cargar_menu_productos(self, categoria="TODOS"):
        self.categoria_actual = categoria

        if self._catalogo_cargando and not self.catalogo_productos:
            self._mostrar_estado_catalogo("Cargando catálogo...")
            return

        if categoria == "TODOS":
            productos = list(self.catalogo_productos)
        else:
            buscada = categoria.strip().casefold()
            productos = [
                producto
                for producto in self.catalogo_productos
                if self._normalizar_categoria_catalogo(producto[3])
                .strip()
                .casefold()
                == buscada
            ]

        for widget in self.frame_productos_container.winfo_children():
            widget.destroy()

        self.canvas_menu.yview_moveto(0)
        self._actualizar_boton_categoria_activa(categoria)

        if not productos:
            tk.Label(
                self.frame_productos_container,
                text="No hay productos en esta categoría.",
                bg=BG,
                fg=MUTED,
                font=("Helvetica", 11),
            ).pack(pady=100)
            return

        productos_por_subcategoria = {}
        for producto in productos:
            subcategoria = str(producto[4]).strip() if producto[4] else "VARIOS"
            productos_por_subcategoria.setdefault(subcategoria, []).append(producto)

        for subcategoria, lista_productos in productos_por_subcategoria.items():
            cabecera = tk.Frame(
                self.frame_productos_container,
                bg=PANEL,
                padx=10,
                pady=6,
            )
            cabecera.pack(fill="x", pady=(10, 4))

            tk.Label(
                cabecera,
                text=subcategoria.upper(),
                font=("Helvetica", 10, "bold"),
                fg=ORANGE,
                bg=PANEL,
            ).pack(anchor="w")

            for producto in lista_productos:
                self._crear_tarjeta_producto(producto)

    def _crear_tarjeta_producto(self, producto):
        nombre = producto[1]
        precio = producto[2]
        descripcion = producto[5]

        card = tk.Frame(
            self.frame_productos_container,
            bg=PANEL,
            padx=12,
            pady=8,
        )
        card.pack(fill="x", pady=2)

        info = tk.Frame(card, bg=PANEL)
        info.pack(side="left", fill="x", expand=True)

        tk.Label(
            info,
            text=nombre,
            font=("Helvetica", 10, "bold"),
            fg=TEXT,
            bg=PANEL,
            anchor="w",
        ).pack(fill="x")

        if descripcion:
            tk.Label(
                info,
                text=descripcion,
                font=("Helvetica", 8),
                fg=MUTED,
                bg=PANEL,
                anchor="w",
                justify="left",
                wraplength=480,
            ).pack(fill="x", pady=2)

        tk.Label(
            info,
            text=fmt_gs(precio),
            font=("Helvetica", 9, "bold"),
            fg=MUTED,
            bg=PANEL,
            anchor="w",
        ).pack(fill="x")

        tk.Button(
            card,
            text="+ Agregar",
            command=lambda prod=producto: self.agregar_al_carrito(prod),
            bg=PANEL_2,
            fg=TEXT,
            relief="flat",
            font=("Helvetica", 9, "bold"),
            padx=12,
            pady=5,
            cursor="hand2",
        ).pack(side="right")

    # ================================================================
    # CARRITO
    # ================================================================

    def agregar_al_carrito(self, producto):
        producto_id = producto[0]
        if producto_id in self.carrito:
            self.carrito[producto_id]["cantidad"] += 1
        else:
            self.carrito[producto_id] = {
                "producto": producto,
                "cantidad": 1,
                "obs": None,
            }
        self.refrescar_carrito_ui()

    def cambiar_cantidad(self, producto_id, delta):
        if producto_id not in self.carrito:
            return
        self.carrito[producto_id]["cantidad"] += delta
        if self.carrito[producto_id]["cantidad"] <= 0:
            del self.carrito[producto_id]
        self.refrescar_carrito_ui()

    def editar_observacion(self, producto_id):
        if producto_id not in self.carrito:
            return

        actual = self.carrito[producto_id].get("obs") or ""
        dialog = tk.Toplevel(self)
        dialog.title("Observación")
        dialog.geometry("340x150")
        dialog.resizable(False, False)
        dialog.configure(bg=BG)
        dialog.transient(self)
        dialog.grab_set()

        tk.Label(
            dialog,
            text="Observación del producto:",
            fg=TEXT,
            bg=BG,
            font=("Helvetica", 9, "bold"),
        ).pack(pady=(15, 6))

        entry = tk.Entry(dialog, font=("Helvetica", 10), width=34)
        entry.insert(0, actual)
        entry.pack(pady=4)
        entry.focus_set()

        def guardar():
            texto = entry.get().strip()
            self.carrito[producto_id]["obs"] = texto or None
            dialog.destroy()
            self.refrescar_carrito_ui()

        botones = tk.Frame(dialog, bg=BG)
        botones.pack(pady=12)

        tk.Button(
            botones,
            text="Guardar",
            command=guardar,
            bg=GREEN,
            fg=TEXT,
            relief="flat",
            padx=12,
        ).pack(side="left", padx=4)

        tk.Button(
            botones,
            text="Cancelar",
            command=dialog.destroy,
            bg=PANEL_2,
            fg=TEXT,
            relief="flat",
            padx=12,
        ).pack(side="left", padx=4)

    def quitar_del_carrito(self, producto_id):
        self.carrito.pop(producto_id, None)
        self.refrescar_carrito_ui()

    def vaciar_carrito(self):
        self.carrito.clear()
        self.refrescar_carrito_ui()

    def refrescar_carrito_ui(self):
        for widget in self.frame_carrito_items.winfo_children():
            widget.destroy()

        total = Decimal("0")

        for producto_id, entrada in self.carrito.items():
            producto = entrada["producto"]
            cantidad = entrada["cantidad"]
            precio = Decimal(str(producto[2]))
            subtotal = precio * cantidad
            total += subtotal

            obs = entrada.get("obs")
            obs_texto = f" ({obs})" if obs else ""

            fila = tk.Frame(self.frame_carrito_items, bg=PANEL, pady=5)
            fila.pack(fill="x", pady=2)

            tk.Label(
                fila,
                text=f"{producto[1]}{obs_texto}",
                fg=ORANGE if obs else TEXT,
                bg=PANEL,
                anchor="w",
                justify="left",
                wraplength=320,
                font=("Helvetica", 9, "bold" if obs else "normal"),
            ).pack(anchor="w")

            controles = tk.Frame(fila, bg=PANEL)
            controles.pack(fill="x", pady=(3, 0))

            tk.Button(
                controles,
                text="-",
                command=lambda pid=producto_id: self.cambiar_cantidad(pid, -1),
                width=2,
                bg=PANEL_2,
                fg=TEXT,
                relief="flat",
            ).pack(side="left")

            tk.Label(
                controles,
                text=str(cantidad),
                width=3,
                bg=PANEL,
                fg=TEXT,
            ).pack(side="left")

            tk.Button(
                controles,
                text="+",
                command=lambda pid=producto_id: self.cambiar_cantidad(pid, 1),
                width=2,
                bg=PANEL_2,
                fg=TEXT,
                relief="flat",
            ).pack(side="left")

            tk.Button(
                controles,
                text="Obs",
                command=lambda pid=producto_id: self.editar_observacion(pid),
                bg=PANEL_2,
                fg=ORANGE,
                relief="flat",
                font=("Helvetica", 8, "bold"),
            ).pack(side="left", padx=4)

            tk.Label(
                controles,
                text=fmt_gs(subtotal),
                bg=PANEL,
                fg=MUTED,
                font=("Helvetica", 8),
            ).pack(side="left", padx=5)

            tk.Button(
                controles,
                text="Quitar",
                command=lambda pid=producto_id: self.quitar_del_carrito(pid),
                bg=RED,
                fg=TEXT,
                relief="flat",
                font=("Helvetica", 8),
            ).pack(side="right")

        self.lbl_total.config(text=f"TOTAL: {fmt_gs(total)}")

    # ================================================================
    # CONFIRMAR VENTA SIN CONGELAR TKINTER
    # ================================================================

    def confirmar_venta(self):
        if self._venta_en_proceso:
            return

        if not self.carrito:
            messagebox.showwarning(
                "Carrito vacío",
                "Agregá al menos un producto antes de confirmar.",
                parent=self,
            )
            return

        configuracion = self._pedir_datos_venta()
        if configuracion is None:
            return

        metodo_pago, tipo_entrega, recargo = configuracion
        items = []
        subtotal_productos = Decimal("0")

        for entrada in self.carrito.values():
            producto = entrada["producto"]
            cantidad = entrada["cantidad"]
            precio = Decimal(str(producto[2]))
            subtotal = precio * cantidad
            subtotal_productos += subtotal

            categoria = (
                self._normalizar_categoria_catalogo(producto[3]).strip().upper()
            )
            subcategoria = str(producto[4] or "").strip().upper()
            es_extra = categoria == "AGREGADOS" or subcategoria == "EXTRAS"

            items.append(
                {
                    "cant": cantidad,
                    "nombre": producto[1],
                    "precio_unitario": precio,
                    "subtotal": subtotal,
                    "obs": entrada.get("obs"),
                    "es_extra": es_extra,
                    "parent_detalle_id": None,
                }
            )

        total = subtotal_productos + recargo

        self._venta_en_proceso = True
        self.btn_confirmar_venta.config(state="disabled", text="Procesando...")
        self.config(cursor="watch")

        self.run_async(
            lambda: self.db.crear_venta(
                total=total,
                metodo_pago=metodo_pago,
                items=items,
                tipo_entrega=tipo_entrega,
                recargo_delivery=recargo,
            ),
            lambda venta_id: self._venta_registrada_ui(
                venta_id,
                items,
                total,
                metodo_pago,
                tipo_entrega,
                recargo,
            ),
            self._error_venta_ui,
        )

    def _venta_registrada_ui(
        self,
        venta_id,
        items,
        total,
        metodo_pago,
        tipo_entrega,
        recargo,
    ):
        self._venta_en_proceso = False
        self.btn_confirmar_venta.config(state="normal", text="Confirmar Venta")
        self.config(cursor="")

        VentanaTicket(
            self,
            venta_id,
            items,
            total,
            metodo_pago,
            tipo_entrega,
            recargo,
        )

        self.vaciar_carrito()
        self.actualizar_header_caja_async()

    def _error_venta_ui(self, mensaje):
        self._venta_en_proceso = False
        self.btn_confirmar_venta.config(state="normal", text="Confirmar Venta")
        self.config(cursor="")
        messagebox.showerror(
            "No se pudo registrar la venta",
            mensaje,
            parent=self,
        )

    def _pedir_datos_venta(self):
        dialog = tk.Toplevel(self)
        dialog.title("Confirmar venta")
        dialog.geometry("360x280")
        dialog.resizable(False, False)
        dialog.configure(bg=BG)
        dialog.transient(self)
        dialog.grab_set()

        resultado = {"valor": None}

        tk.Label(
            dialog,
            text="Método de pago",
            bg=BG,
            fg=TEXT,
            font=("Helvetica", 9, "bold"),
        ).pack(pady=(18, 5))

        combo_pago = ttk.Combobox(
            dialog,
            values=["Efectivo", "POS / Tarjeta", "Transferencia"],
            state="readonly",
            width=25,
        )
        combo_pago.current(0)
        combo_pago.pack()

        tk.Label(
            dialog,
            text="Tipo de entrega",
            bg=BG,
            fg=TEXT,
            font=("Helvetica", 9, "bold"),
        ).pack(pady=(14, 5))

        combo_entrega = ttk.Combobox(
            dialog,
            values=["Mostrador", "Retiro", "Delivery"],
            state="readonly",
            width=25,
        )
        combo_entrega.current(0)
        combo_entrega.pack()

        frame_delivery = tk.Frame(dialog, bg=BG)
        tk.Label(
            frame_delivery,
            text="Recargo delivery:",
            bg=BG,
            fg=MUTED,
            font=("Helvetica", 9),
        ).pack(side="left", padx=(0, 5))

        entry_recargo = tk.Entry(frame_delivery, width=15)
        entry_recargo.insert(0, "0")
        entry_recargo.pack(side="left")

        def actualizar_delivery(_event=None):
            if combo_entrega.get() == "Delivery":
                frame_delivery.pack(pady=14)
            else:
                frame_delivery.pack_forget()
                entry_recargo.delete(0, tk.END)
                entry_recargo.insert(0, "0")

        combo_entrega.bind("<<ComboboxSelected>>", actualizar_delivery)

        def confirmar():
            try:
                recargo = (
                    parse_gs(entry_recargo.get())
                    if combo_entrega.get() == "Delivery"
                    else Decimal("0")
                )
            except ValueError as exc:
                messagebox.showwarning(
                    "Recargo inválido",
                    str(exc),
                    parent=dialog,
                )
                return

            resultado["valor"] = (
                combo_pago.get(),
                combo_entrega.get(),
                recargo,
            )
            dialog.destroy()

        botones = tk.Frame(dialog, bg=BG)
        botones.pack(side="bottom", pady=18)

        tk.Button(
            botones,
            text="Confirmar",
            command=confirmar,
            bg=GREEN,
            fg=TEXT,
            relief="flat",
            padx=14,
            pady=5,
        ).pack(side="left", padx=5)

        tk.Button(
            botones,
            text="Cancelar",
            command=dialog.destroy,
            bg=PANEL_2,
            fg=TEXT,
            relief="flat",
            padx=14,
            pady=5,
        ).pack(side="left", padx=5)

        dialog.wait_window()
        return resultado["valor"]

    # ================================================================
    # OTRAS VENTANAS
    # ================================================================

    def abrir_historial(self):
        VentanaHistorialVentas(self, self.db)

    def abrir_reportes(self):
        VentanaReportes(self, self.db)

    def abrir_cierre_caja(self):
        VentanaCierreCaja(self, self.db)

    def on_caja_cerrada(self):
        self.vaciar_carrito()
        self.after(150, self.on_close)

    def on_close(self):
        if self._venta_en_proceso:
            messagebox.showwarning(
                "Venta en proceso",
                "Espere a que termine de registrarse la venta antes de cerrar.",
                parent=self,
            )
            return

        self._cerrando = True
        try:
            self.db.close()
        finally:
            self.destroy()
