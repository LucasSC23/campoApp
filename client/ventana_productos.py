import tkinter as tk
from decimal import Decimal, InvalidOperation
from tkinter import ttk

from client.ui_dialogos import (
    confirmar,
    mostrar_advertencia,
    mostrar_error,
    mostrar_exito,
)


BG = "#141722"
PANEL = "#1c2030"
PANEL_2 = "#252a3e"
ORANGE = "#ff8c2b"
GREEN = "#2ecc71"
RED = "#ff4d4d"
TEXT = "#ffffff"
MUTED = "#a0a5b5"

CATEGORIAS = (
    "Hamburguesas",
    "Lomitos y Sándwiches",
    "Agregados",
    "Bebidas",
    "Helados y Postres",
    "Papas Fritas",
    "Milanesas",
)


def _precio_desde_texto(texto):
    limpio = str(texto or "").strip()
    for token in ("Gs.", "GS.", "Gs", "GS", "₲"):
        limpio = limpio.replace(token, "")
    limpio = limpio.replace(".", "").replace(",", "").replace(" ", "")
    try:
        precio = Decimal(limpio)
    except (InvalidOperation, ValueError):
        raise ValueError("El precio no es válido.")
    if not precio.is_finite() or precio < 0:
        raise ValueError("El precio debe ser mayor o igual a cero.")
    return precio


class VentanaAdministrarMenu(tk.Toplevel):
    def __init__(self, parent, api, on_catalogo_actualizado=None):
        super().__init__(parent)
        self.parent = parent
        self.api = api
        self.on_catalogo_actualizado = on_catalogo_actualizado
        self.productos = {}

        self.title("Administrar menú")
        self.geometry("880x620")
        self.minsize(760, 520)
        self.configure(bg=BG)
        self.transient(parent)

        self.contenido = tk.Frame(self, bg=BG, padx=18, pady=18)
        self.contenido.pack(fill="both", expand=True)
        self._mostrar_login()

    def _limpiar(self):
        for widget in self.contenido.winfo_children():
            widget.destroy()

    def _mostrar_login(self):
        self._limpiar()

        frame = tk.Frame(self.contenido, bg=PANEL, padx=26, pady=24)
        frame.pack(expand=True)

        tk.Label(
            frame,
            text="ADMINISTRAR MENÚ",
            bg=PANEL,
            fg=ORANGE,
            font=("Segoe UI", 14, "bold"),
        ).pack(pady=(0, 8))

        tk.Label(
            frame,
            text=(
                "Ingrese el PIN administrativo. "
                "El PIN se valida en el servidor y no se guarda en esta PC."
            ),
            bg=PANEL,
            fg=MUTED,
            font=("Segoe UI", 9),
            wraplength=390,
            justify="center",
        ).pack(pady=(0, 14))

        self.pin_var = tk.StringVar()
        entry = tk.Entry(
            frame,
            textvariable=self.pin_var,
            show="•",
            justify="center",
            font=("Segoe UI", 15),
            bg=PANEL_2,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            width=20,
        )
        entry.pack(ipady=8, pady=(0, 12))
        entry.focus_set()

        self.lbl_login = tk.Label(
            frame,
            text="",
            bg=PANEL,
            fg=MUTED,
            font=("Segoe UI", 8),
        )
        self.lbl_login.pack(pady=(0, 8))

        self.btn_login = tk.Button(
            frame,
            text="Ingresar",
            command=self._autenticar,
            bg=GREEN,
            fg=TEXT,
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            padx=22,
            pady=7,
            cursor="hand2",
        )
        self.btn_login.pack()

        entry.bind("<Return>", lambda _e: self._autenticar())

    def _autenticar(self):
        pin = self.pin_var.get().strip()
        if not pin:
            self.lbl_login.config(text="Ingrese el PIN.")
            return

        self.btn_login.config(state="disabled", text="Verificando...")
        self.lbl_login.config(text="Conectando con el servidor...")

        self.parent.run_async(
            lambda: self.api.autenticar_admin(pin),
            lambda _resultado: self._mostrar_panel(),
            self._error_login,
        )

    def _error_login(self, mensaje):
        if not self.winfo_exists():
            return
        self.btn_login.config(state="normal", text="Ingresar")
        self.lbl_login.config(text=mensaje)

    def _mostrar_panel(self):
        if not self.winfo_exists():
            return
        self._limpiar()

        encabezado = tk.Frame(self.contenido, bg=BG)
        encabezado.pack(fill="x", pady=(0, 12))

        tk.Label(
            encabezado,
            text="ADMINISTRAR MENÚ",
            bg=BG,
            fg=ORANGE,
            font=("Segoe UI", 14, "bold"),
        ).pack(side="left")

        self.lbl_estado = tk.Label(
            encabezado,
            text="",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9),
        )
        self.lbl_estado.pack(side="right")

        tabla_frame = tk.Frame(self.contenido, bg=BG)
        tabla_frame.pack(fill="both", expand=True)

        columnas = ("nombre", "precio", "categoria", "subcategoria", "estado")
        self.tree = ttk.Treeview(
            tabla_frame,
            columns=columnas,
            show="headings",
            selectmode="browse",
        )

        titulos = {
            "nombre": "Producto",
            "precio": "Precio",
            "categoria": "Categoría",
            "subcategoria": "Subcategoría",
            "estado": "Estado",
        }
        anchos = {
            "nombre": 230,
            "precio": 100,
            "categoria": 170,
            "subcategoria": 150,
            "estado": 85,
        }

        for col in columnas:
            self.tree.heading(col, text=titulos[col])
            self.tree.column(col, width=anchos[col], anchor="w")

        scroll = ttk.Scrollbar(
            tabla_frame,
            orient="vertical",
            command=self.tree.yview,
        )
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        botones = tk.Frame(self.contenido, bg=BG)
        botones.pack(fill="x", pady=(12, 0))

        tk.Button(
            botones,
            text="+ Nuevo producto",
            command=self._nuevo_producto,
            bg=GREEN,
            fg=TEXT,
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
        ).pack(side="left")

        tk.Button(
            botones,
            text="Editar",
            command=self._editar_producto,
            bg=PANEL_2,
            fg=TEXT,
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
        ).pack(side="left", padx=6)

        tk.Button(
            botones,
            text="Activar / Desactivar",
            command=self._alternar_estado,
            bg=PANEL_2,
            fg=ORANGE,
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
        ).pack(side="left")

        tk.Button(
            botones,
            text="↻ Actualizar",
            command=self.cargar_productos,
            bg=PANEL_2,
            fg=MUTED,
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
        ).pack(side="right")

        self.cargar_productos()

    def cargar_productos(self):
        self.lbl_estado.config(text="Cargando...")
        self.parent.run_async(
            self.api.obtener_productos_admin,
            self._aplicar_productos,
            self._error_productos,
        )

    def _aplicar_productos(self, productos):
        if not self.winfo_exists():
            return

        self.productos = {
            int(producto["id"]): producto
            for producto in productos
        }

        for item in self.tree.get_children():
            self.tree.delete(item)

        for producto in productos:
            precio = int(Decimal(str(producto["precio"])))
            self.tree.insert(
                "",
                "end",
                iid=str(producto["id"]),
                values=(
                    producto["nombre"],
                    f"{precio:,}".replace(",", "."),
                    producto["categoria"],
                    producto.get("subcategoria") or "",
                    "Activo" if producto.get("activo") else "Inactivo",
                ),
            )

        self.lbl_estado.config(text=f"{len(productos)} productos")

    def _error_productos(self, mensaje):
        if not self.winfo_exists():
            return
        self.lbl_estado.config(text="Error")
        mostrar_error(self, "Administrar menú", mensaje)

    def _seleccionado(self):
        seleccion = self.tree.selection()
        if not seleccion:
            mostrar_advertencia(
                self,
                "Administrar menú",
                "Seleccione un producto.",
            )
            return None
        return self.productos.get(int(seleccion[0]))

    def _nuevo_producto(self):
        datos = _pedir_producto(self)
        if datos is not None:
            self._guardar_producto(datos)

    def _editar_producto(self):
        producto = self._seleccionado()
        if not producto:
            return
        datos = _pedir_producto(self, producto)
        if datos is not None:
            self._guardar_producto(datos, producto_id=producto["id"])

    def _guardar_producto(self, datos, producto_id=None):
        if producto_id is None:
            trabajo = lambda: self.api.agregar_producto_admin(datos)
            mensaje = "Producto agregado correctamente."
        else:
            trabajo = lambda: self.api.actualizar_producto_admin(
                producto_id,
                datos,
            )
            mensaje = "Producto actualizado correctamente."

        self.lbl_estado.config(text="Guardando...")
        self.parent.run_async(
            trabajo,
            lambda _resultado: self._cambio_exitoso(mensaje),
            lambda error: mostrar_error(
                self,
                "No se pudo guardar",
                error,
            ),
        )

    def _alternar_estado(self):
        producto = self._seleccionado()
        if not producto:
            return

        nuevo_estado = not bool(producto.get("activo"))
        accion = "activar" if nuevo_estado else "desactivar"

        if not confirmar(
            self,
            "Cambiar estado",
            f"¿Desea {accion} {producto['nombre']}?",
            texto_confirmar="Sí",
            texto_cancelar="Cancelar",
        ):
            return

        self.lbl_estado.config(text="Guardando...")
        self.parent.run_async(
            lambda: self.api.cambiar_estado_producto_admin(
                producto["id"],
                nuevo_estado,
            ),
            lambda _resultado: self._cambio_exitoso(
                "Estado actualizado correctamente."
            ),
            lambda error: mostrar_error(
                self,
                "No se pudo cambiar el estado",
                error,
            ),
        )

    def _cambio_exitoso(self, mensaje):
        if not self.winfo_exists():
            return
        mostrar_exito(self, "Administrar menú", mensaje)
        self.cargar_productos()
        if self.on_catalogo_actualizado is not None:
            self.on_catalogo_actualizado()


def _pedir_producto(parent, producto=None):
    dialog = tk.Toplevel(parent)
    dialog.title("Nuevo producto" if producto is None else "Editar producto")
    dialog.geometry("520x540")
    dialog.resizable(False, False)
    dialog.configure(bg=BG)
    dialog.transient(parent)
    dialog.grab_set()

    resultado = {"datos": None}

    nombre_var = tk.StringVar(value=(producto or {}).get("nombre", ""))
    precio_var = tk.StringVar(value=str((producto or {}).get("precio", "")))
    categoria_var = tk.StringVar(
        value=(producto or {}).get("categoria", CATEGORIAS[0])
    )
    subcategoria_var = tk.StringVar(
        value=(producto or {}).get("subcategoria") or ""
    )
    tipo_var = tk.StringVar(
        value=(producto or {}).get("tipo_venta", "unidad")
    )

    def label(texto):
        tk.Label(
            dialog,
            text=texto,
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        ).pack(fill="x", padx=22, pady=(10, 4))

    def entry(variable):
        control = tk.Entry(
            dialog,
            textvariable=variable,
            bg=PANEL_2,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=("Segoe UI", 10),
        )
        control.pack(fill="x", padx=22, ipady=7)
        return control

    label("Nombre")
    nombre_entry = entry(nombre_var)

    label("Precio")
    entry(precio_var)

    label("Categoría")
    ttk.Combobox(
        dialog,
        textvariable=categoria_var,
        values=CATEGORIAS,
        state="readonly",
    ).pack(fill="x", padx=22)

    label("Subcategoría")
    entry(subcategoria_var)

    label("Tipo de venta")
    ttk.Combobox(
        dialog,
        textvariable=tipo_var,
        values=("unidad", "peso"),
        state="readonly",
    ).pack(fill="x", padx=22)

    label("Descripción")
    descripcion = tk.Text(
        dialog,
        height=4,
        bg=PANEL_2,
        fg=TEXT,
        insertbackground=TEXT,
        relief="flat",
        font=("Segoe UI", 9),
    )
    descripcion.pack(fill="x", padx=22)
    descripcion.insert("1.0", (producto or {}).get("descripcion") or "")

    lbl_error = tk.Label(
        dialog,
        text="",
        bg=BG,
        fg=RED,
        font=("Segoe UI", 8),
    )
    lbl_error.pack(fill="x", padx=22, pady=(8, 0))

    def guardar():
        try:
            nombre = nombre_var.get().strip()
            if not nombre:
                raise ValueError("El nombre es obligatorio.")

            precio = _precio_desde_texto(precio_var.get())
            categoria = categoria_var.get().strip()
            if categoria not in CATEGORIAS:
                raise ValueError("Seleccione una categoría válida.")

            tipo = tipo_var.get().strip().lower()
            if tipo not in ("unidad", "peso"):
                raise ValueError("Seleccione un tipo de venta válido.")

            resultado["datos"] = {
                "nombre": nombre,
                "precio": str(precio),
                "categoria": categoria,
                "subcategoria": subcategoria_var.get().strip(),
                "descripcion": descripcion.get("1.0", "end").strip(),
                "tipo_venta": tipo,
            }
        except ValueError as exc:
            lbl_error.config(text=str(exc))
            return

        dialog.destroy()

    botones = tk.Frame(dialog, bg=BG)
    botones.pack(fill="x", padx=22, pady=16)

    tk.Button(
        botones,
        text="Guardar",
        command=guardar,
        bg=GREEN,
        fg=TEXT,
        relief="flat",
        padx=18,
        pady=7,
        cursor="hand2",
    ).pack(side="right")

    tk.Button(
        botones,
        text="Cancelar",
        command=dialog.destroy,
        bg=PANEL_2,
        fg=TEXT,
        relief="flat",
        padx=18,
        pady=7,
        cursor="hand2",
    ).pack(side="right", padx=(0, 8))

    nombre_entry.focus_set()
    parent.wait_window(dialog)
    return resultado["datos"]
