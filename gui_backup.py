import datetime
import os
import tkinter as tk
from decimal import Decimal, InvalidOperation
from tkinter import messagebox, simpledialog, ttk

from ventana_cierre import VentanaCierreCaja


BG = "#141722"
PANEL = "#1c2030"
PANEL_2 = "#252a3e"
ORANGE = "#ff8c2b"
GREEN = "#2ecc71"
RED = "#ff4d4d"
TEXT = "#ffffff"
MUTED = "#a0a5b5"


def fmt_gs(monto):
    """Formatea un valor numérico como Guaraníes."""
    try:
        return f"Gs. {int(Decimal(str(monto))):,}".replace(",", ".")
    except (InvalidOperation, ValueError, TypeError):
        return f"Gs. {monto}"


def parse_gs(texto):
    """Acepta 150000, 150.000 o Gs. 150.000."""
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
    """Activa el scroll solamente cuando el mouse está encima del canvas."""

    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_enter(_event):
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def _on_leave(_event):
        canvas.unbind_all("<MouseWheel>")

    canvas.bind("<Enter>", _on_enter)
    canvas.bind("<Leave>", _on_leave)


class VentanaHistorialVentas(tk.Toplevel):
    """Ventas completadas de la sesión de caja actualmente abierta."""

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
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)

        self.frame_ventas = tk.Frame(self.canvas, bg=BG)
        self.window_id = self.canvas.create_window((0, 0), window=self.frame_ventas, anchor="nw")

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

    def cargar_datos(self):
        for widget in self.frame_ventas.winfo_children():
            widget.destroy()

        try:
            ventas = self.db.obtener_ventas_sesion_activa()
        except Exception as exc:
            messagebox.showerror(
                "Error",
                f"No se pudieron consultar las ventas del turno:\n{exc}",
                parent=self,
            )
            return

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
                lambda _e, vid=venta_id, cb=combo: self.cambiar_metodo(vid, cb.get()),
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
        try:
            self.db.actualizar_metodo_pago_venta(venta_id, nuevo_metodo)
            self.parent.actualizar_header_caja()
        except Exception as exc:
            messagebox.showerror("No se pudo modificar", str(exc), parent=self)
            self.cargar_datos()

    def anular(self, venta_id):
        if not messagebox.askyesno(
            "Anular venta",
            f"¿Desea anular el Ticket #{venta_id}?",
            parent=self,
        ):
            return

        try:
            self.db.anular_venta(venta_id)
            self.parent.actualizar_header_caja()
            self.cargar_datos()
        except Exception as exc:
            messagebox.showerror("No se pudo anular", str(exc), parent=self)


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

        txt = tk.Text(self, bg="#0f1119", fg=TEXT, font=("Courier New", 10), width=42)
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

    def _armar_texto(self, venta_id, items, total, metodo_pago, tipo_entrega, recargo_delivery):
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
        ruta = os.path.join("tickets", f"ticket_{datetime.datetime.now():%Y%m%d_%H%M%S}.txt")

        try:
            with open(ruta, "w", encoding="utf-8") as archivo:
                archivo.write(self.texto_ticket)
        except OSError as exc:
            messagebox.showerror("Error", f"No se pudo guardar el ticket:\n{exc}", parent=self)
            return

        try:
            os.startfile(ruta, "print")
            messagebox.showinfo("Ticket", f"Ticket guardado y enviado a impresión:\n{ruta}", parent=self)
        except (AttributeError, OSError):
            messagebox.showinfo("Ticket guardado", f"El ticket se guardó en:\n{ruta}", parent=self)


class VentanaPrincipal(tk.Tk):
    """Interfaz principal del POS."""

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.carrito = {}
        self.catalogo_productos = []

        self.categorias_menu = [
            "Hamburguesas",
            "Lomitos y Sándwiches",
            "Agregados",
            "Bebidas",
            "Helados y Postres",
            "Papas Fritas",
        ]
        self.title("Campo Burger & Açaí - Punto de Venta")
        self.geometry("1180x760")
        self.minsize(980, 650)
        self.configure(bg=BG)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # La apertura de caja es flujo de UI, no responsabilidad de main.py.
        self.withdraw()
        if not self._asegurar_caja_abierta():
            self.destroy()
            return
        self.cargar_catalogo()

        self.crear_interfaz()

        self.actualizar_header_caja()

        self.cargar_menu_productos("TODOS")

        self.deiconify()
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
                    f"Sesión #{sesion_id} abierta correctamente.\nFondo inicial: {fmt_gs(monto)}",
                    parent=self,
                )
                return True
            except ValueError as exc:
                messagebox.showwarning("Monto inválido", str(exc), parent=self)
            except Exception as exc:
                messagebox.showerror("No se pudo abrir la caja", str(exc), parent=self)
                return False

    def actualizar_header_caja(self):
        try:
            sesion = self.db.obtener_sesion_abierta()
            resumen = self.db.obtener_resumen_caja()
        except Exception as exc:
            self.lbl_sesion.config(text="Caja: error de conexión")
            self.lbl_resumen_header.config(text=str(exc))
            return

        if not sesion:
            self.lbl_sesion.config(text="CAJA CERRADA")
            self.lbl_resumen_header.config(text="")
            return

        self.lbl_sesion.config(text=f"SESIÓN #{sesion['id']} · ABIERTA")
        self.lbl_resumen_header.config(
            text=(
                f"Ventas: {fmt_gs(resumen['total_ventas'])}   |   "
                f"Efectivo esperado: {fmt_gs(resumen['efectivo_esperado'])}"
            )
        )

    # ================================================================
    # CONSTRUCCIÓN UI
    # ================================================================

    def crear_interfaz(self):
        self._crear_header()
        self._crear_navegacion()
        self._crear_contenido()

    def _crear_header(self):
        header = tk.Frame(self, bg="#11141d", padx=14, pady=10)
        header.pack(fill="x")

        titulo_frame = tk.Frame(header, bg="#11141d")
        titulo_frame.pack(side="left")

        tk.Label(
            titulo_frame,
            text="CAMPO BURGER & AÇAÍ",
            font=("Segoe UI", 18, "bold"),
            fg=ORANGE,
            bg="#11141d",
        ).pack(anchor="w")

        self.lbl_sesion = tk.Label(
            titulo_frame,
            text="",
            font=("Segoe UI", 9, "bold"),
            fg=GREEN,
            bg="#11141d",
        )
        self.lbl_sesion.pack(anchor="w")

        self.lbl_resumen_header = tk.Label(
            header,
            text="",
            font=("Segoe UI", 9),
            fg=MUTED,
            bg="#11141d",
        )
        self.lbl_resumen_header.pack(side="right", padx=10)

    def _crear_navegacion(self):

        self.frame_nav = tk.Frame(
            self,
            bg=PANEL,
            padx=10,
            pady=8,
        )

        self.frame_nav.pack(
            fill="x"
        )

        # --------------------------------------------------------
        # TODOS
        # --------------------------------------------------------

        tk.Button(
            self.frame_nav,
            text="TODOS",
            command=lambda: self.cargar_menu_productos(
                "TODOS"
            ),
            bg=ORANGE,
            fg=TEXT,
            relief="flat",
            font=("Helvetica", 9, "bold"),
            padx=10,
            cursor="hand2",
        ).pack(
            side="left",
            padx=3,
        )

        # --------------------------------------------------------
        # CATEGORÍAS EN ORDEN FIJO
        # --------------------------------------------------------

        for categoria in self.categorias_menu:

            tk.Button(
                self.frame_nav,
                text=categoria.upper(),
                command=lambda cat=categoria:
                    self.cargar_menu_productos(cat),
                bg=PANEL_2,
                fg=TEXT,
                relief="flat",
                font=("Helvetica", 8, "bold"),
                padx=8,
                cursor="hand2",
            ).pack(
                side="left",
                padx=2,
            )

        # --------------------------------------------------------
        # CIERRE DE CAJA
        # --------------------------------------------------------

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
        ).pack(
            side="right",
            padx=(6, 0),
        )

        # --------------------------------------------------------
        # VENTAS DEL TURNO
        # --------------------------------------------------------

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
        ).pack(
            side="right"
        )
    # ================================================================
    # MENÚ
    # ================================================================

    def cargar_menu_productos(
        self,
        categoria="TODOS",
        ):
        """
        Filtra el catálogo EN MEMORIA.

        No consulta Supabase al cambiar de pestaña.
        """

        # --------------------------------------------------------
        # FILTRAR PRIMERO
        #
        # Importante:
        # NO borramos la pantalla hasta tener los datos preparados.
        # --------------------------------------------------------

        if categoria.upper() == "TODOS":

            productos = list(
                self.catalogo_productos
            )

        else:

            productos = [
                producto
                for producto
                in self.catalogo_productos

                if str(
                    producto[3]
                    or ""
                ).strip().casefold()

                == categoria.strip().casefold()
            ]

        # --------------------------------------------------------
        # AHORA SÍ LIMPIAMOS LA UI
        # --------------------------------------------------------

        for widget in (
            self.frame_productos_container.winfo_children()
        ):
            widget.destroy()

        # Volver arriba al cambiar de categoría
        self.canvas_menu.yview_moveto(0)

        # --------------------------------------------------------
        # SIN PRODUCTOS
        # --------------------------------------------------------

        if not productos:

            tk.Label(
                self.frame_productos_container,
                text=(
                    "No hay productos "
                    "en esta categoría."
                ),
                bg=BG,
                fg=MUTED,
                font=(
                    "Helvetica",
                    11,
                ),
            ).pack(
                pady=100
            )

            return

        # --------------------------------------------------------
        # AGRUPAR POR SUBCATEGORÍA
        # --------------------------------------------------------

        productos_por_subcategoria = {}

        for producto in productos:

            subcategoria = (
                str(producto[4]).strip()
                if producto[4]
                else "VARIOS"
            )

            productos_por_subcategoria.setdefault(
                subcategoria,
                [],
            ).append(
                producto
            )

        # --------------------------------------------------------
        # CREAR UI
        # --------------------------------------------------------

        for (
            subcategoria,
            lista_productos,
        ) in productos_por_subcategoria.items():

            cabecera = tk.Frame(
                self.frame_productos_container,
                bg=PANEL,
                padx=10,
                pady=6,
            )

            cabecera.pack(
                fill="x",
                pady=(10, 4),
            )

            tk.Label(
                cabecera,
                text=subcategoria.upper(),
                font=(
                    "Helvetica",
                    10,
                    "bold",
                ),
                fg=ORANGE,
                bg=PANEL,
            ).pack(
                anchor="w"
            )

            for producto in lista_productos:

                self._crear_tarjeta_producto(
                    producto
                )    
    # ================================================================
    # CARRITO
    # ================================================================

    def agregar_al_carrito(self, producto):
        producto_id = producto[0]
        if producto_id in self.carrito:
            self.carrito[producto_id]["cantidad"] += 1
        else:
            self.carrito[producto_id] = {"producto": producto, "cantidad": 1, "obs": None}
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

            tk.Label(controles, text=str(cantidad), width=3, bg=PANEL, fg=TEXT).pack(side="left")

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
    # CONFIRMAR VENTA
    # ================================================================

    def confirmar_venta(self):
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

            categoria = str(producto[3] or "").strip().upper()
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

        try:
            venta_id = self.db.crear_venta(
                total=total,
                metodo_pago=metodo_pago,
                items=items,
                tipo_entrega=tipo_entrega,
                recargo_delivery=recargo,
            )
        except Exception as exc:
            messagebox.showerror("No se pudo registrar la venta", str(exc), parent=self)
            return

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
        self.actualizar_header_caja()

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
                recargo = parse_gs(entry_recargo.get()) if combo_entrega.get() == "Delivery" else Decimal("0")
            except ValueError as exc:
                messagebox.showwarning("Recargo inválido", str(exc), parent=dialog)
                return

            resultado["valor"] = (combo_pago.get(), combo_entrega.get(), recargo)
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

    def abrir_cierre_caja(self):
        VentanaCierreCaja(self, self.db)

    def on_caja_cerrada(self):
        """Cerrar caja termina el turno y cierra la aplicación."""
        self.vaciar_carrito()
        self.after(150, self.destroy)

    def on_close(self):
        try:
            self.db.close()
        finally:
            self.destroy()
