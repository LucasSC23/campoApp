import tkinter as tk
from decimal import Decimal, InvalidOperation
from tkinter import messagebox, ttk


BG = "#141722"
PANEL = "#1c2030"
TEXT = "#ffffff"
MUTED = "#a0a5b5"
ORANGE = "#ff8c2b"


def fmt_gs(monto):
    try:
        return f"Gs. {int(Decimal(str(monto))):,}".replace(",", ".")
    except (InvalidOperation, ValueError, TypeError):
        return f"Gs. {monto}"


class VentanaReportes(tk.Toplevel):
    """Historial de sesiones y resúmenes semanal/mensual por método de pago."""

    def __init__(self, parent, db):
        super().__init__(parent)
        self.parent = parent
        self.db = db

        self.title("Reportes")
        self.geometry("1080x620")
        self.minsize(900, 520)
        self.configure(bg=BG)
        self.transient(parent)

        self._configurar_estilo()
        self._crear_interfaz()
        self.cargar_datos()

    def _configurar_estilo(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Campo.Treeview",
            background=PANEL,
            fieldbackground=PANEL,
            foreground=TEXT,
            rowheight=26,
            borderwidth=0,
        )
        style.configure(
            "Campo.Treeview.Heading",
            background="#252a3e",
            foreground=TEXT,
            relief="flat",
            font=("Helvetica", 9, "bold"),
        )
        style.map(
            "Campo.Treeview",
            background=[("selected", "#374151")],
            foreground=[("selected", TEXT)],
        )

    def _crear_interfaz(self):
        header = tk.Frame(self, bg="#11141d", padx=15, pady=12)
        header.pack(fill="x")

        tk.Label(
            header,
            text="REPORTES DE CAJA Y VENTAS",
            font=("Helvetica", 14, "bold"),
            fg=ORANGE,
            bg="#11141d",
        ).pack(side="left")

        self.lbl_estado = tk.Label(
            header,
            text="Cargando...",
            font=("Helvetica", 9),
            fg=MUTED,
            bg="#11141d",
        )
        self.lbl_estado.pack(side="right")

        acciones = tk.Frame(self, bg=BG, padx=12, pady=8)
        acciones.pack(fill="x")

        self.btn_actualizar = tk.Button(
            acciones,
            text="↻ Actualizar",
            command=self.cargar_datos,
            bg="#252a3e",
            fg=TEXT,
            relief="flat",
            padx=12,
            pady=5,
            cursor="hand2",
        )
        self.btn_actualizar.pack(side="right")

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        tab_sesiones = tk.Frame(notebook, bg=BG)
        tab_semanal = tk.Frame(notebook, bg=BG)
        tab_mensual = tk.Frame(notebook, bg=BG)

        notebook.add(tab_sesiones, text="Sesiones de caja")
        notebook.add(tab_semanal, text="Resumen semanal")
        notebook.add(tab_mensual, text="Resumen mensual")

        self._crear_tabla_sesiones(tab_sesiones)
        self._crear_tabla_semanal(tab_semanal)
        self._crear_tabla_mensual(tab_mensual)

    def _crear_tabla_sesiones(self, parent):
        columnas = (
            "sesion",
            "apertura",
            "cierre",
            "estado",
            "fondo",
            "ventas",
            "anuladas",
            "efectivo",
            "pos",
            "transferencia",
            "total",
            "esperado",
        )

        frame = tk.Frame(parent, bg=BG)
        frame.pack(fill="both", expand=True, padx=8, pady=8)

        self.tree_sesiones = ttk.Treeview(
            frame,
            columns=columnas,
            show="headings",
            style="Campo.Treeview",
        )

        encabezados = {
            "sesion": "Sesión",
            "apertura": "Apertura",
            "cierre": "Cierre",
            "estado": "Estado",
            "fondo": "Fondo inicial",
            "ventas": "Ventas",
            "anuladas": "Anuladas",
            "efectivo": "Efectivo",
            "pos": "POS",
            "transferencia": "Transferencia",
            "total": "Total ventas",
            "esperado": "Efectivo esperado",
        }

        anchos = {
            "sesion": 60,
            "apertura": 135,
            "cierre": 135,
            "estado": 80,
            "fondo": 110,
            "ventas": 65,
            "anuladas": 70,
            "efectivo": 105,
            "pos": 105,
            "transferencia": 115,
            "total": 110,
            "esperado": 125,
        }

        for col in columnas:
            self.tree_sesiones.heading(col, text=encabezados[col])
            self.tree_sesiones.column(
                col,
                width=anchos[col],
                minwidth=50,
                anchor="center",
                stretch=False,
            )

        scroll_y = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=self.tree_sesiones.yview,
        )
        scroll_x = ttk.Scrollbar(
            frame,
            orient="horizontal",
            command=self.tree_sesiones.xview,
        )
        self.tree_sesiones.configure(
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set,
        )

        self.tree_sesiones.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

    def _crear_tabla_semanal(self, parent):
        columnas = (
            "semana",
            "tickets",
            "efectivo",
            "pos",
            "transferencia",
            "total",
        )

        frame = tk.Frame(parent, bg=BG)
        frame.pack(fill="both", expand=True, padx=8, pady=8)

        self.tree_semanal = ttk.Treeview(
            frame,
            columns=columnas,
            show="headings",
            style="Campo.Treeview",
        )

        encabezados = {
            "semana": "Semana",
            "tickets": "Ventas",
            "efectivo": "Efectivo",
            "pos": "POS / Tarjeta",
            "transferencia": "Transferencia",
            "total": "Total semanal",
        }

        for col in columnas:
            self.tree_semanal.heading(col, text=encabezados[col])
            self.tree_semanal.column(
                col,
                width=185 if col == "semana" else (100 if col == "tickets" else 160),
                anchor="center",
                stretch=True,
            )

        scroll_y = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=self.tree_semanal.yview,
        )
        self.tree_semanal.configure(yscrollcommand=scroll_y.set)

        self.tree_semanal.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

    def _crear_tabla_mensual(self, parent):
        columnas = (
            "mes",
            "tickets",
            "efectivo",
            "pos",
            "transferencia",
            "total",
        )

        frame = tk.Frame(parent, bg=BG)
        frame.pack(fill="both", expand=True, padx=8, pady=8)

        self.tree_mensual = ttk.Treeview(
            frame,
            columns=columnas,
            show="headings",
            style="Campo.Treeview",
        )

        encabezados = {
            "mes": "Mes",
            "tickets": "Ventas",
            "efectivo": "Efectivo",
            "pos": "POS / Tarjeta",
            "transferencia": "Transferencia",
            "total": "Total mensual",
        }

        for col in columnas:
            self.tree_mensual.heading(col, text=encabezados[col])
            self.tree_mensual.column(
                col,
                width=160 if col != "tickets" else 100,
                anchor="center",
                stretch=True,
            )

        scroll_y = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=self.tree_mensual.yview,
        )
        self.tree_mensual.configure(yscrollcommand=scroll_y.set)

        self.tree_mensual.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

    def cargar_datos(self):
        self.btn_actualizar.config(state="disabled", text="Cargando...")
        self.lbl_estado.config(text="Consultando Supabase...")

        if hasattr(self.parent, "run_async"):
            self.parent.run_async(
                self._consultar_reportes,
                self._aplicar_reportes,
                self._mostrar_error,
            )
        else:
            try:
                self._aplicar_reportes(self._consultar_reportes())
            except Exception as exc:
                self._mostrar_error(str(exc))

    def _consultar_reportes(self):
        sesiones = self.db.obtener_resumen_sesiones(200)
        semanal = self.db.obtener_resumen_semanal(52)
        mensual = self.db.obtener_resumen_mensual(36)
        return sesiones, semanal, mensual

    def _mostrar_error(self, mensaje):
        if not self.winfo_exists():
            return
        self.btn_actualizar.config(state="normal", text="↻ Actualizar")
        self.lbl_estado.config(text="Error")
        messagebox.showerror(
            "Reportes",
            f"No se pudieron cargar los reportes:\n{mensaje}",
            parent=self,
        )

    def _aplicar_reportes(self, datos):
        if not self.winfo_exists():
            return

        sesiones, semanal, mensual = datos

        for item in self.tree_sesiones.get_children():
            self.tree_sesiones.delete(item)

        for fila in sesiones:
            apertura = (
                fila["fecha_apertura"].strftime("%d/%m/%Y %H:%M")
                if fila["fecha_apertura"]
                else ""
            )
            cierre = (
                fila["fecha_cierre"].strftime("%d/%m/%Y %H:%M")
                if fila["fecha_cierre"]
                else "—"
            )

            self.tree_sesiones.insert(
                "",
                "end",
                values=(
                    fila["sesion_id"],
                    apertura,
                    cierre,
                    fila["estado"],
                    fmt_gs(fila["monto_inicial"]),
                    fila["ventas"],
                    fila["anuladas"],
                    fmt_gs(fila["efectivo"]),
                    fmt_gs(fila["pos"]),
                    fmt_gs(fila["transferencia"]),
                    fmt_gs(fila["total_ventas"]),
                    fmt_gs(fila["efectivo_esperado"]),
                ),
            )

        for item in self.tree_semanal.get_children():
            self.tree_semanal.delete(item)

        for fila in semanal:
            inicio = (
                fila["semana_inicio"].strftime("%d/%m/%Y")
                if fila["semana_inicio"]
                else ""
            )
            fin = (
                fila["semana_fin"].strftime("%d/%m/%Y")
                if fila["semana_fin"]
                else ""
            )
            semana = f"{inicio} - {fin}" if inicio and fin else ""

            self.tree_semanal.insert(
                "",
                "end",
                values=(
                    semana,
                    fila["cantidad_ventas"],
                    fmt_gs(fila["efectivo"]),
                    fmt_gs(fila["pos"]),
                    fmt_gs(fila["transferencia"]),
                    fmt_gs(fila["total"]),
                ),
            )

        for item in self.tree_mensual.get_children():
            self.tree_mensual.delete(item)

        for fila in mensual:
            mes = fila["mes"].strftime("%m/%Y") if fila["mes"] else ""
            self.tree_mensual.insert(
                "",
                "end",
                values=(
                    mes,
                    fila["cantidad_ventas"],
                    fmt_gs(fila["efectivo"]),
                    fmt_gs(fila["pos"]),
                    fmt_gs(fila["transferencia"]),
                    fmt_gs(fila["total"]),
                ),
            )

        self.btn_actualizar.config(state="normal", text="↻ Actualizar")
        self.lbl_estado.config(
            text=(
                f"{len(sesiones)} sesiones · "
                f"{len(semanal)} semanas · "
                f"{len(mensual)} meses"
            )
        )
