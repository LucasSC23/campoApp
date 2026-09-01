import tkinter as tk
from decimal import Decimal, InvalidOperation
from tkinter import messagebox, ttk


BG = "#141722"
PANEL = "#1c2030"
MUTED = "#a0a5b5"
TEXT = "#ffffff"
GREEN = "#10b981"
RED = "#ef4444"
BLUE = "#60a5fa"


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

        self.title("Cierre de Caja")
        self.geometry("590x760")
        self.minsize(540, 620)
        self.resizable(True, True) 
        self.configure(bg=BG)
        self.transient(parent)
        self.grab_set()

        self._crear_interfaz()
        self.cargar_datos()

    def _crear_interfaz(self):
        # HEADER
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

        # FOOTER FIJO
        btn_frame = tk.Frame(
            self,
            bg=BG,
            pady=12,
            padx=20,
        )
        btn_frame.pack(
            side="bottom",
            fill="x",
        )

        self.btn_cancelar = tk.Button(
            btn_frame,
            text="Cancelar",
            command=self.destroy,
            bg="#374151",
            fg=TEXT,
            relief="flat",
            font=("Helvetica", 10, "bold"),
            padx=15,
            pady=8,
            cursor="hand2",
        )
        self.btn_cancelar.pack(side="left")

        self.btn_cerrar = tk.Button(
            btn_frame,
            text="Guardar y Cerrar Caja",
            command=self.cerrar_caja,
            bg=RED,
            fg=TEXT,
            relief="flat",
            font=("Helvetica", 10, "bold"),
            padx=18,
            pady=8,
            cursor="hand2",
        )
        self.btn_cerrar.pack(side="right")

        # CONTENIDO
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

        self.lbl_efectivo_ventas = self._label_resumen(container)
        self.lbl_efectivo_ventas.pack(fill="x", pady=2)

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
        self.lbl_cantidades.pack(fill="x", pady=(0, 8))

        tk.Label(
            container,
            text="Ventas por método de pago",
            fg=TEXT,
            bg=BG,
            font=("Helvetica", 10, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(5, 3))

        self.frame_pagos = tk.Frame(
            container,
            bg=PANEL,
            padx=12,
            pady=8,
        )
        self.frame_pagos.pack(fill="x", pady=(0, 10))

        tk.Label(
            container,
            text="Ventas por categoría y subcategoría",
            fg=TEXT,
            bg=BG,
            font=("Helvetica", 10, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(5, 3))

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
        label = tk.Label(
            parent,
            text="Cargando...",
            fg=MUTED,
            bg=BG,
            font=("Helvetica", 10),
            anchor="w",
        )
        label.pack(fill="x", pady=2)
        return label

    def cargar_datos(self):
        self.btn_cerrar.config(state="disabled", text="Cargando...")

        if hasattr(self.parent, "run_async"):
            self.parent.run_async(
                self.db.obtener_resumen_caja,
                self._aplicar_resumen,
                self._error_carga,
            )
        else:
            try:
                self._aplicar_resumen(self.db.obtener_resumen_caja())
            except Exception as exc:
                self._error_carga(str(exc))

    def _error_carga(self, mensaje):
        if not self.winfo_exists():
            return
        self.btn_cerrar.config(state="disabled", text="Cerrar Caja")
        messagebox.showerror(
            "Error",
            f"No se pudo cargar el cierre de caja:\n{mensaje}",
            parent=self,
        )

    def _aplicar_resumen(self, resumen):
        if not self.winfo_exists():
            return

        if not resumen.get("sesion_id"):
            self.lbl_sesion.config(text="NO HAY SESIÓN ABIERTA")
            self.btn_cerrar.config(state="disabled", text="Cerrar Caja")
            return

        fecha = resumen.get("fecha_apertura")
        fecha_txt = fecha.strftime("%d/%m/%Y %H:%M") if fecha else ""

        self.lbl_sesion.config(
            text=f"Sesión #{resumen['sesion_id']} · abierta {fecha_txt}"
        )
        self.lbl_monto_inicial.config(
            text=f"Fondo inicial: {fmt_gs(resumen['monto_inicial'])}"
        )
        self.lbl_total_ventas.config(
            text=f"Total procesado en ventas: {fmt_gs(resumen['total_ventas'])}"
        )

        efectivo = resumen.get("desglose_pagos", {}).get("Efectivo", Decimal("0"))
        self.lbl_efectivo_recibido.config(
            text=f"Efectivo recibido por ventas: {fmt_gs(efectivo)}"
        )
        self.lbl_efectivo_esperado.config(
            text=f"EFECTIVO ESPERADO: {fmt_gs(resumen['efectivo_esperado'])}"
        )
        self.lbl_cantidades.config(
            text=(
                f"Ventas completadas: {resumen['ventas_completadas']}   |   "
                f"Ventas anuladas: {resumen['ventas_anuladas']}"
            )
        )

        for widget in self.frame_pagos.winfo_children():
            widget.destroy()

        pagos = resumen.get("desglose_pagos", {})
        if pagos:
            for metodo in ("Efectivo", "POS / Tarjeta", "Transferencia"):
                monto = pagos.get(metodo, Decimal("0"))
                tk.Label(
                    self.frame_pagos,
                    text=f"• {metodo}: {fmt_gs(monto)}",
                    fg=MUTED,
                    bg=PANEL,
                    font=("Helvetica", 9),
                    anchor="w",
                ).pack(fill="x", pady=1)
        else:
            tk.Label(
                self.frame_pagos,
                text="Sin ventas registradas.",
                fg=MUTED,
                bg=PANEL,
                font=("Helvetica", 9, "italic"),
            ).pack(anchor="w")

        for widget in self.frame_categorias.winfo_children():
            widget.destroy()

        categorias = resumen.get("desglose_categorias", {})
        if categorias:
            for categoria, subcategorias in categorias.items():
                tk.Label(
                    self.frame_categorias,
                    text=f"▸ {categoria.upper()}",
                    fg=BLUE,
                    bg=PANEL,
                    font=("Helvetica", 9, "bold"),
                    anchor="w",
                ).pack(fill="x", pady=(5, 1))

                for subcategoria, monto in subcategorias.items():
                    tk.Label(
                        self.frame_categorias,
                        text=f"    • {subcategoria}: {fmt_gs(monto)}",
                        fg="#d1d5db",
                        bg=PANEL,
                        font=("Helvetica", 9),
                        anchor="w",
                    ).pack(fill="x", pady=1)
        else:
            tk.Label(
                self.frame_categorias,
                text="Sin ventas por categoría.",
                fg=MUTED,
                bg=PANEL,
                font=("Helvetica", 9, "italic"),
            ).pack(anchor="w")

        self.btn_cerrar.config(state="normal", text="Confirmar Cierre de Caja")

    def cerrar_caja(self):
        confirmar = messagebox.askyesno(
            "Confirmar cierre",
            (
                "¿Está seguro de cerrar la caja y finalizar el turno?\n\n"
                "Las ventas permanecerán registradas como COMPLETADA o ANULADA."
            ),
            parent=self,
        )
        if not confirmar:
            return

        self.btn_cerrar.config(state="disabled", text="Cerrando...")
        self.config(cursor="watch")

        if hasattr(self.parent, "run_async"):
            self.parent.run_async(
                self.db.cerrar_caja,
                self._cierre_correcto,
                self._error_cierre,
            )
        else:
            try:
                self._cierre_correcto(self.db.cerrar_caja())
            except Exception as exc:
                self._error_cierre(str(exc))

    def _error_cierre(self, mensaje):
        if not self.winfo_exists():
            return
        self.config(cursor="")
        self.btn_cerrar.config(state="normal", text="Confirmar Cierre de Caja")
        messagebox.showerror(
            "No se pudo cerrar la caja",
            mensaje,
            parent=self,
        )

    def _cierre_correcto(self, sesion_id):
        if not self.winfo_exists():
            return
        self.config(cursor="")
        messagebox.showinfo(
            "Caja cerrada",
            f"La sesión #{sesion_id} fue cerrada correctamente.",
            parent=self,
        )
        self.destroy()

        if hasattr(self.parent, "on_caja_cerrada"):
            self.parent.on_caja_cerrada()
