import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter

customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("blue")

COLOR_RED = "#e74c3c"
COLOR_GREEN = "#2ecc71"
COLOR_AMBER = "#f39c12"

# Categorías a excluir de la barra superior
CATEGORIAS_EXCLUIDAS = {
    "Papas y Agregados",
    "Postres",
    "Bebidas",
    "Papas Fritas",
    "Agregados",
}


class VentanaCierreCaja(customtkinter.CTkToplevel):
    """Ventana emergente para el Resumen y Cierre de Caja / Día."""

    def __init__(self, parent, db_manager):
        super().__init__(parent)
        self.db = db_manager
        self.parent = parent

        self.title("Cierre de Caja / Resumen del Día")
        self.geometry("520x580")
        self.grab_set()

        self.crear_interfaz()

    def crear_interfaz(self):
        (
            desglose,
            total_ventas,
            cant_ventas,
            monto_inicial,
        ) = self.db.obtener_cierre_caja_activa()
        monto_total_caja = monto_inicial + total_ventas

        lbl_titulo = customtkinter.CTkLabel(
            self, text="RESUMEN DE CIERRE DE CAJA", font=("Arial", 18, "bold")
        )
        lbl_titulo.pack(pady=15)

        frame_info = customtkinter.CTkFrame(self)
        frame_info.pack(fill="x", padx=20, pady=5)

        customtkinter.CTkLabel(
            frame_info,
            text=f"Fondo Inicial de Caja: ${monto_inicial:.2f}",
            font=("Arial", 13),
        ).pack(anchor="w", padx=15, pady=3)
        customtkinter.CTkLabel(
            frame_info,
            text=f"Total de Ventas: ${total_ventas:.2f} ({cant_ventas} transacciones)",
            font=("Arial", 13),
        ).pack(anchor="w", padx=15, pady=3)
        customtkinter.CTkLabel(
            frame_info,
            text=f"TOTAL EN CAJA: ${monto_total_caja:.2f}",
            font=("Arial", 15, "bold"),
            text_color=COLOR_GREEN,
        ).pack(anchor="w", padx=15, pady=6)

        lbl_desglose = customtkinter.CTkLabel(
            self, text="Desglose por Método de Pago:", font=("Arial", 14, "bold")
        )
        lbl_desglose.pack(pady=(15, 5))

        tabla = ttk.Treeview(
            self, columns=("metodo", "monto", "cant"), show="headings", height=5
        )
        tabla.heading("metodo", text="Método de Pago")
        tabla.heading("monto", text="Monto Recaudado")
        tabla.heading("cant", text="Cant. Ventas")
        tabla.column("metodo", width=180)
        tabla.column("monto", width=140, anchor="e")
        tabla.column("cant", width=100, anchor="center")
        tabla.pack(fill="x", padx=20, pady=5)

        for met, monto, cant in desglose:
            tabla.insert("", "end", values=(met, f"${monto:.2f}", cant))

        btn_confirmar = customtkinter.CTkButton(
            self,
            text="CONFIRMAR Y CERRAR CAJA",
            fg_color=COLOR_RED,
            hover_color="#922b21",
            height=45,
            font=("Arial", 14, "bold"),
            command=self.confirmar_cierre,
        )
        btn_confirmar.pack(fill="x", padx=20, pady=20)

    def confirmar_cierre(self):
        if messagebox.askyesno(
            "Confirmar Cierre",
            "¿Está seguro de realizar el cierre de caja y finalizar el día?",
            parent=self,
        ):
            self.db.procesar_cierre_de_caja()
            messagebox.showinfo(
                "Caja Cerrada",
                "El turno ha sido cerrado con éxito.",
                parent=self,
            )
            self.parent.actualizar_estado_caja()
            self.destroy()


class VentanaHistorialVentas(customtkinter.CTkToplevel):
    """Ventana para consultar y gestionar el historial de ventas del turno."""

    def __init__(self, parent, db_manager):
        super().__init__(parent)
        self.db = db_manager
        self.parent = parent

        self.title("Historial de Ventas del Turno")
        self.geometry("750x520")
        self.grab_set()

        self.crear_interfaz()
        self.cargar_ventas()

    def crear_interfaz(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        lbl_tit = customtkinter.CTkLabel(
            self, text="VENTAS REGISTRADAS", font=("Arial", 16, "bold")
        )
        lbl_tit.grid(row=0, column=0, columnspan=2, pady=10)

        cols_v = ("id", "hora", "monto", "metodo")
        self.tabla_ventas = ttk.Treeview(
            self, columns=cols_v, show="headings", height=12
        )
        self.tabla_ventas.heading("id", text="ID")
        self.tabla_ventas.heading("hora", text="Hora")
        self.tabla_ventas.heading("monto", text="Monto")
        self.tabla_ventas.heading("metodo", text="Método")
        self.tabla_ventas.column("id", width=40, anchor="center")
        self.tabla_ventas.column("hora", width=70, anchor="center")
        self.tabla_ventas.column("monto", width=90, anchor="e")
        self.tabla_ventas.column("metodo", width=110)
        self.tabla_ventas.grid(
            row=1, column=0, padx=10, pady=5, sticky="nsew"
        )
        self.tabla_ventas.bind("<<TreeviewSelect>>", self.cargar_detalle)

        cols_d = ("prod", "cant", "precio", "subtotal", "notas")
        self.tabla_detalle = ttk.Treeview(
            self, columns=cols_d, show="headings", height=12
        )
        self.tabla_detalle.heading("prod", text="Producto")
        self.tabla_detalle.heading("cant", text="Cant.")
        self.tabla_detalle.heading("precio", text="P.Unit")
        self.tabla_detalle.heading("subtotal", text="Subtotal")
        self.tabla_detalle.heading("notas", text="Notas")
        self.tabla_detalle.column("prod", width=110)
        self.tabla_detalle.column("cant", width=40, anchor="center")
        self.tabla_detalle.column("precio", width=60, anchor="e")
        self.tabla_detalle.column("subtotal", width=60, anchor="e")
        self.tabla_detalle.column("notas", width=90)
        self.tabla_detalle.grid(
            row=1, column=1, padx=10, pady=5, sticky="nsew"
        )

        frame_acciones = customtkinter.CTkFrame(self)
        frame_acciones.grid(
            row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=10
        )

        btn_cambiar_pago = customtkinter.CTkButton(
            frame_acciones,
            text="Cambiar Método Pago",
            command=self.cambiar_pago,
        )
        btn_cambiar_pago.pack(side="left", padx=10, pady=5)

        btn_eliminar = customtkinter.CTkButton(
            frame_acciones,
            text="Anular / Eliminar Venta",
            fg_color=COLOR_RED,
            command=self.eliminar_venta,
        )
        btn_eliminar.pack(side="right", padx=10, pady=5)

    def cargar_ventas(self):
        for r in self.tabla_ventas.get_children():
            self.tabla_ventas.delete(r)

        ventas = self.db.obtener_ventas_activas()
        for v in ventas:
            self.tabla_ventas.insert(
                "", "end", values=(v[0], v[1], f"${v[2]:.2f}", v[3])
            )

    def cargar_detalle(self, event):
        for r in self.tabla_detalle.get_children():
            self.tabla_detalle.delete(r)

        sel = self.tabla_ventas.focus()
        if not sel:
            return

        venta_id = self.tabla_ventas.item(sel)["values"][0]
        detalles = self.db.obtener_detalle_venta(venta_id)
        for d in detalles:
            self.tabla_detalle.insert(
                "",
                "end",
                values=(d[0], d[1], f"${d[2]:.2f}", f"${d[3]:.2f}", d[4]),
            )

    def cambiar_pago(self):
        sel = self.tabla_ventas.focus()
        if not sel:
            return

        venta_id = self.tabla_ventas.item(sel)["values"][0]
        dialog = customtkinter.CTkInputDialog(
            text="Nuevo método de pago (EFECTIVO, TRANSFERENCIA, TARJETA):",
            title="Modificar Pago",
        )
        nuevo_m = dialog.get_input()
        if nuevo_m:
            self.db.cambiar_metodo_pago(venta_id, nuevo_m.upper().strip())
            self.cargar_ventas()
            self.parent.actualizar_estado_caja()

    def eliminar_venta(self):
        sel = self.tabla_ventas.focus()
        if not sel:
            return

        venta_id = self.tabla_ventas.item(sel)["values"][0]
        if messagebox.askyesno(
            "Anular Venta",
            f"¿Desea anular la venta #{venta_id}?",
            parent=self,
        ):
            self.db.eliminar_venta(venta_id)
            self.cargar_ventas()
            for r in self.tabla_detalle.get_children():
                self.tabla_detalle.delete(r)
            self.parent.actualizar_estado_caja()


class VentanaPrincipal(customtkinter.CTk):
    """Ventana Principal del Sistema POS."""

    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.carrito = []
        self.widgets_productos = []  # Almacena los elementos de la grilla

        self.title("Sistema POS - Hamburguesería")
        self.geometry("1180x730")

        self.aplicar_estilo_tabla_oscura()
        self.crear_interfaz()
        self.actualizar_estado_caja()
        self.cargar_categorias()
        self.cargar_productos("TODOS")

    def aplicar_estilo_tabla_oscura(self):
        """Estilo para mantener las tablas en modo oscuro."""
        style = ttk.Style()
        style.theme_use("default")

        style.configure(
            "Treeview",
            background="#2a2d2e",
            foreground="#ffffff",
            fieldbackground="#2a2d2e",
            rowheight=30,
            borderwidth=0,
        )
        style.map(
            "Treeview",
            background=[("selected", "#1f538d")],
            foreground=[("selected", "#ffffff")],
        )

        style.configure(
            "Treeview.Heading",
            background="#1f1f1f",
            foreground="#ffffff",
            relief="flat",
            font=("Arial", 10, "bold"),
        )
        style.map("Treeview.Heading", background=[("active", "#343638")])

    def crear_interfaz(self):
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(1, weight=1)

        # ---------------- Barra Superior (Estado de Caja) ----------------
        self.frame_top = customtkinter.CTkFrame(self, height=50)
        self.frame_top.grid(
            row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 0)
        )

        self.lbl_estado_caja = customtkinter.CTkLabel(
            self.frame_top,
            text="CAJA: VERIFICANDO...",
            font=("Arial", 14, "bold"),
        )
        self.lbl_estado_caja.pack(side="left", padx=15, pady=10)

        self.btn_abrir_caja = customtkinter.CTkButton(
            self.frame_top,
            text="Abrir Caja",
            fg_color=COLOR_GREEN,
            hover_color="#1f8a43",
            command=self.abrir_caja_dialog,
        )
        self.btn_abrir_caja.pack(side="left", padx=5)

        self.btn_cierre_caja = customtkinter.CTkButton(
            self.frame_top,
            text="Cierre de Caja / Día",
            fg_color=COLOR_AMBER,
            hover_color="#b9770e",
            command=self.abrir_cierre_caja_window,
        )
        self.btn_cierre_caja.pack(side="left", padx=5)

        self.btn_historial = customtkinter.CTkButton(
            self.frame_top,
            text="Historial Ventas",
            command=self.abrir_historial_window,
        )
        self.btn_historial.pack(side="right", padx=15)

        # ---------------- Panel Izquierdo (Categorías y Menú) ----------------
        self.frame_izq = customtkinter.CTkFrame(self)
        self.frame_izq.grid(
            row=1, column=0, padx=(10, 5), pady=10, sticky="nsew"
        )

        # Barra de Categorías Principales
        self.frame_categorias = customtkinter.CTkFrame(
            self.frame_izq, height=50
        )
        self.frame_categorias.pack(fill="x", padx=5, pady=5)

        # Área Scrollable de Productos
        self.frame_productos = customtkinter.CTkScrollableFrame(self.frame_izq)
        self.frame_productos.pack(fill="both", expand=True, padx=5, pady=5)

        # ---------------- Panel Derecho (Carrito de Compra) ----------------
        self.frame_der = customtkinter.CTkFrame(self)
        self.frame_der.grid(
            row=1, column=1, padx=(5, 10), pady=10, sticky="nsew"
        )

        self.lbl_carrito = customtkinter.CTkLabel(
            self.frame_der, text="ORDEN ACTUAL", font=("Arial", 16, "bold")
        )
        self.lbl_carrito.pack(pady=5)

        cols = ("nombre", "cant", "precio", "subtotal", "notas")
        self.tabla_carrito = ttk.Treeview(
            self.frame_der, columns=cols, show="headings", height=12
        )
        self.tabla_carrito.heading("nombre", text="Producto")
        self.tabla_carrito.heading("cant", text="Cant.")
        self.tabla_carrito.heading("precio", text="Precio")
        self.tabla_carrito.heading("subtotal", text="Subtotal")
        self.tabla_carrito.heading("notas", text="Notas / Detalle")

        self.tabla_carrito.column("nombre", width=120)
        self.tabla_carrito.column("cant", width=45, anchor="center")
        self.tabla_carrito.column("precio", width=65, anchor="e")
        self.tabla_carrito.column("subtotal", width=75, anchor="e")
        self.tabla_carrito.column("notas", width=120)
        self.tabla_carrito.pack(fill="both", expand=True, padx=5, pady=5)

        self.btn_nota = customtkinter.CTkButton(
            self.frame_der,
            text="✎ AGREGAR NOTA / MODIFICAR PEDIDO",
            fg_color="#34495e",
            hover_color="#2c3e50",
            command=self.agregar_observacion_item,
        )
        self.btn_nota.pack(fill="x", padx=5, pady=3)

        self.seg_metodo = customtkinter.CTkSegmentedButton(
            self.frame_der,
            values=["EFECTIVO", "TRANSFERENCIA", "TARJETA"],
        )
        self.seg_metodo.set("EFECTIVO")
        self.seg_metodo.pack(fill="x", padx=5, pady=8)

        self.lbl_total = customtkinter.CTkLabel(
            self.frame_der, text="Total: $0.00", font=("Arial", 20, "bold")
        )
        self.lbl_total.pack(pady=5)

        self.btn_cobrar = customtkinter.CTkButton(
            self.frame_der,
            text="COBRAR / REGISTRAR VENTA",
            fg_color=COLOR_GREEN,
            hover_color="#1f8a43",
            height=48,
            font=("Arial", 14, "bold"),
            command=self.procesar_venta,
        )
        self.btn_cobrar.pack(fill="x", padx=5, pady=5)

        self.btn_limpiar = customtkinter.CTkButton(
            self.frame_der,
            text="Cancelar / Limpiar Carrito",
            fg_color="transparent",
            border_color=COLOR_RED,
            border_width=1,
            text_color=COLOR_RED,
            hover_color="#2b1a1a",
            command=self.limpiar_carrito,
        )
        self.btn_limpiar.pack(fill="x", padx=5, pady=3)

    # ==========================================
    # GESTIÓN DE CAJA
    # ==========================================

    def actualizar_estado_caja(self):
        sesion = self.db.obtener_sesion_activa()
        if sesion:
            _, _, monto_inicial, _ = sesion
            self.lbl_estado_caja.configure(
                text=f"CAJA ABIERTA (Fondo: ${float(monto_inicial):.2f})",
                text_color=COLOR_GREEN,
            )
            self.btn_abrir_caja.configure(state="disabled")
            self.btn_cierre_caja.configure(state="normal")
        else:
            self.lbl_estado_caja.configure(
                text="CAJA CERRADA", text_color=COLOR_RED
            )
            self.btn_abrir_caja.configure(state="normal")
            self.btn_cierre_caja.configure(state="disabled")

    def abrir_caja_dialog(self):
        dialog = customtkinter.CTkInputDialog(
            text="Ingrese el monto inicial de la caja:", title="Apertura de Caja"
        )
        monto_str = dialog.get_input()
        if monto_str:
            try:
                monto = float(monto_str)
                self.db.abrir_caja(monto)
                self.actualizar_estado_caja()
                messagebox.showinfo(
                    "Caja Abierta", f"Caja iniciada con ${monto:.2f}"
                )
            except ValueError:
                messagebox.showerror(
                    "Error", "Ingrese un número válido.", parent=self
                )

    def abrir_cierre_caja_window(self):
        VentanaCierreCaja(self, self.db)

    def abrir_historial_window(self):
        VentanaHistorialVentas(self, self.db)

    # ==========================================
    # CARGA DE MENÚ Y SUBCATEGORÍAS
    # ==========================================

    def cargar_categorias(self):
        for widget in self.frame_categorias.winfo_children():
            widget.destroy()

        btn_todos = customtkinter.CTkButton(
            self.frame_categorias,
            text="TODOS",
            width=90,
            command=lambda: self.cargar_productos("TODOS"),
        )
        btn_todos.pack(side="left", padx=4, pady=5)

        categorias_db = self.db.obtener_categorias_principales()
        categorias_filtradas = [
            c for c in categorias_db if c not in CATEGORIAS_EXCLUIDAS
        ]

        for cat in categorias_filtradas:
            btn = customtkinter.CTkButton(
                self.frame_categorias,
                text=cat,
                width=130,
                command=lambda c=cat: self.cargar_productos(c),
            )
            btn.pack(side="left", padx=4, pady=5)

    def cargar_productos(self, categoria="TODOS"):
        """Limpia la vista de forma segura y despliega productos agrupados por subcategoría."""
        # Destruir únicamente los widgets creados para productos (sin romper el scrollbar interno)
        for widget in self.widgets_productos:
            widget.destroy()
        self.widgets_productos.clear()

        productos = self.db.obtener_productos_filtrados(categoria=categoria)

        # Agrupar productos por subcategoría
        grupos = {}
        for prod in productos:
            p_id, nombre, precio, cat, subcat = prod
            subcat_nombre = (
                subcat.strip().upper()
                if (subcat and subcat.strip())
                else "VARIOS"
            )
            if subcat_nombre not in grupos:
                grupos[subcat_nombre] = []
            grupos[subcat_nombre].append(prod)

        row_idx = 0
        for subcat_titulo, lista_prods in grupos.items():
            # Título de Subcategoría (Clásicas, Gourmet, etc.)
            lbl_subcat = customtkinter.CTkLabel(
                self.frame_productos,
                text=f"━━━  {subcat_titulo}  ━━━",
                font=("Arial", 13, "bold"),
                text_color="#3598db",
            )
            lbl_subcat.grid(
                row=row_idx,
                column=0,
                columnspan=3,
                pady=(14, 6),
                sticky="ew",
            )
            self.widgets_productos.append(lbl_subcat)
            row_idx += 1

            col_idx = 0
            for prod in lista_prods:
                p_id, nombre, precio, cat, subcat_val = prod
                btn = customtkinter.CTkButton(
                    self.frame_productos,
                    text=f"{nombre}\n${precio:.2f}",
                    width=140,
                    height=70,
                    font=("Arial", 12, "bold"),
                    command=lambda p=prod: self.agregar_al_carrito(p),
                )
                btn.grid(row=row_idx, column=col_idx, padx=6, pady=6)
                self.widgets_productos.append(btn)

                col_idx += 1
                if col_idx > 2:
                    col_idx = 0
                    row_idx += 1

            if col_idx != 0:
                row_idx += 1

    # ==========================================
    # CARRITO Y OBSERVACIONES
    # ==========================================

    def agregar_al_carrito(self, producto):
        p_id, nombre, precio, cat, subcat = producto

        for item in self.carrito:
            if item["id"] == p_id and item["notas"] == "":
                item["cantidad"] += 1
                self.actualizar_tabla_carrito()
                return

        self.carrito.append(
            {
                "id": p_id,
                "nombre": nombre,
                "precio": float(precio),
                "cantidad": 1,
                "notas": "",
            }
        )
        self.actualizar_tabla_carrito()

    def agregar_observacion_item(self):
        item_sel = self.tabla_carrito.focus()
        if not item_sel:
            messagebox.showwarning(
                "Selección Requerida",
                "Selecciona un producto del carrito para agregar observaciones.",
                parent=self,
            )
            return

        index = self.tabla_carrito.index(item_sel)
        item_actual = self.carrito[index]

        dialogo = customtkinter.CTkInputDialog(
            text=f"Notas para '{item_actual['nombre']}' (ej: Sin cebolla, Extra salsa):",
            title="Modificar Pedido",
        )
        nota = dialogo.get_input()

        if nota is not None:
            self.carrito[index]["notas"] = nota.strip()
            self.actualizar_tabla_carrito()

    def actualizar_tabla_carrito(self):
        for row in self.tabla_carrito.get_children():
            self.tabla_carrito.delete(row)

        total = 0.0
        for item in self.carrito:
            subtotal = item["precio"] * item["cantidad"]
            total += subtotal
            self.tabla_carrito.insert(
                "",
                "end",
                values=(
                    item["nombre"],
                    item["cantidad"],
                    f"${item['precio']:.2f}",
                    f"${subtotal:.2f}",
                    item["notas"],
                ),
            )

        self.lbl_total.configure(text=f"Total: ${total:.2f}")

    def limpiar_carrito(self):
        self.carrito.clear()
        self.actualizar_tabla_carrito()

    # ==========================================
    # REGISTRO DE VENTAS
    # ==========================================

    def procesar_venta(self):
        if not self.carrito:
            messagebox.showwarning(
                "Carrito Vacío",
                "No hay productos en la orden actual.",
                parent=self,
            )
            return

        sesion = self.db.obtener_sesion_activa()
        if not sesion:
            messagebox.showerror(
                "Caja Cerrada",
                "Debes abrir la caja antes de registrar ventas.",
                parent=self,
            )
            return

        total_venta = sum(
            item["precio"] * item["cantidad"] for item in self.carrito
        )
        metodo_pago = self.seg_metodo.get()

        try:
            id_venta = self.db.guardar_venta(
                total_venta, metodo_pago, self.carrito
            )
            messagebox.showinfo(
                "Venta Exitosa",
                f"Venta #{id_venta} registrada correctamente.",
                parent=self,
            )
            self.limpiar_carrito()
            self.actualizar_estado_caja()
        except Exception as e:
            messagebox.showerror(
                "Error de Venta",
                f"No se pudo completar la transacción:\n{e}",
                parent=self,
            )