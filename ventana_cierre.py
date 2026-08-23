import customtkinter as ctk
from tkinter import messagebox

class VentanaCierreCaja(ctk.CTkToplevel):
    """
    Ventana modal estilizada para el Cierre y Arqueo de Caja.
    Muestra el desglose por métodos de pago (Efectivo, Tarjeta, Transferencia),
    el total recaudado y el total esperado en caja (monto inicial + ventas).
    """
    def __init__(self, parent, db, al_cerrar_caja_exitoso=None):
        super().__init__(parent)

        self.db = db
        self.al_cerrar_caja_exitoso = al_cerrar_caja_exitoso

        self.title("Cierre de Caja - Resumen de Turno")
        self.geometry("500x650")
        self.resizable(False, False)

        # Hace que la ventana sea modal (se mantiene al frente y bloquea la principal)
        self.transient(parent)
        self.grab_set()

        self.crear_interfaz()
        self.cargar_datos_cierre()

    def crear_interfaz(self):
        # Título Principal
        self.lbl_titulo = ctk.CTkLabel(
            self, 
            text="🔒 Cierre y Arqueo de Caja", 
            font=("Arial", 20, "bold")
        )
        self.lbl_titulo.pack(pady=(20, 10))

        # Frame Contenedor Principal
        self.frame_contenido = ctk.CTkFrame(self)
        self.frame_contenido.pack(padx=20, pady=10, fill="both", expand=True)

        # 1. Saldo Inicial
        self.frame_inicial = ctk.CTkFrame(self.frame_contenido, fg_color="transparent")
        self.frame_inicial.pack(fill="x", padx=15, pady=(15, 5))

        ctk.CTkLabel(
            self.frame_inicial, 
            text="Fondo Inicial de Caja:", 
            font=("Arial", 13, "bold")
        ).pack(side="left")

        self.lbl_monto_inicial = ctk.CTkLabel(
            self.frame_inicial, 
            text="Gs. 0", 
            font=("Arial", 13)
        )
        self.lbl_monto_inicial.pack(side="right")

        # Separador visual
        ctk.CTkFrame(self.frame_contenido, height=2, fg_color="gray30").pack(fill="x", padx=15, pady=10)

        # 2. Desglose por Método de Pago
        ctk.CTkLabel(
            self.frame_contenido, 
            text="Desglose por Métodos de Pago", 
            font=("Arial", 14, "bold"),
            anchor="w"
        ).pack(fill="x", padx=15, pady=(5, 5))

        self.frame_desglose = ctk.CTkScrollableFrame(self.frame_contenido, height=180)
        self.frame_desglose.pack(fill="x", padx=15, pady=5)

        # Separador visual
        ctk.CTkFrame(self.frame_contenido, height=2, fg_color="gray30").pack(fill="x", padx=15, pady=10)

        # 3. Totales
        self.frame_totales = ctk.CTkFrame(self.frame_contenido, fg_color="transparent")
        self.frame_totales.pack(fill="x", padx=15, pady=5)

        # Cantidad de Transacciones
        frame_cant = ctk.CTkFrame(self.frame_totales, fg_color="transparent")
        frame_cant.pack(fill="x", pady=2)
        ctk.CTkLabel(frame_cant, text="Total de Pedidos Realizados:", font=("Arial", 12)).pack(side="left")
        self.lbl_cant_ventas = ctk.CTkLabel(frame_cant, text="0 pedidos", font=("Arial", 12, "bold"))
        self.lbl_cant_ventas.pack(side="right")

        # Total Recaudado en Turno
        frame_recaudado = ctk.CTkFrame(self.frame_totales, fg_color="transparent")
        frame_recaudado.pack(fill="x", pady=2)
        ctk.CTkLabel(frame_recaudado, text="Total Recaudado (Ventas):", font=("Arial", 13, "bold")).pack(side="left")
        self.lbl_total_ventas = ctk.CTkLabel(frame_recaudado, text="Gs. 0", font=("Arial", 13, "bold"), text_color="#2CC985")
        self.lbl_total_ventas.pack(side="right")

        # Total General Esperado en Caja (Inicial + Recaudado)
        frame_gran_total = ctk.CTkFrame(self.frame_totales, fg_color="transparent")
        frame_gran_total.pack(fill="x", pady=(8, 2))
        ctk.CTkLabel(frame_gran_total, text="TOTAL ESPERADO EN CAJA:", font=("Arial", 14, "bold")).pack(side="left")
        self.lbl_total_general = ctk.CTkLabel(frame_gran_total, text="Gs. 0", font=("Arial", 16, "bold"), text_color="#1E90FF")
        self.lbl_total_general.pack(side="right")

        # Botones de Acción
        self.frame_botones = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_botones.pack(fill="x", padx=20, pady=(10, 20))

        self.btn_cerrar = ctk.CTkButton(
            self.frame_botones, 
            text="PROCESAR CIERRE DE CAJA", 
            fg_color="#D32F2F", 
            hover_color="#9A0007",
            font=("Arial", 13, "bold"),
            height=40,
            command=self.confirmar_cierre
        )
        self.btn_cerrar.pack(fill="x", pady=(0, 5))

        self.btn_cancelar = ctk.CTkButton(
            self.frame_botones, 
            text="Volver / Cancelar", 
            fg_color="gray30", 
            hover_color="gray40",
            height=32,
            command=self.destroy
        )
        self.btn_cancelar.pack(fill="x")

    def cargar_datos_cierre(self):
        """Consulta la base de datos en segundo plano y completa los datos de la interfaz."""
        parent_app = self.master

        def al_obtener_datos(resultado, error):
            if error:
                messagebox.showerror("Error", f"No se pudieron obtener los datos del cierre:\n{error}", parent=self)
                return

            desglose, total_ventas, cant_ventas, monto_inicial = resultado

            # 1. Monto Inicial
            self.lbl_monto_inicial.configure(text=f"Gs. {monto_inicial:,.0f}".replace(",", "."))

            # 2. Desglose por Método de Pago
            for widget in self.frame_desglose.winfo_children():
                widget.destroy()

            if not desglose:
                ctk.CTkLabel(
                    self.frame_desglose, 
                    text="No hay ventas registradas en esta sesión.", 
                    font=("Arial", 11, "italic")
                ).pack(pady=10)
            else:
                for metodo, suma, cantidad in desglose:
                    frame_fila = ctk.CTkFrame(self.frame_desglose, fg_color="gray20")
                    frame_fila.pack(fill="x", pady=3, padx=5)

                    lbl_metodo = ctk.CTkLabel(
                        frame_fila, 
                        text=f"• {metodo} ({cantidad} pedidos)", 
                        font=("Arial", 12)
                    )
                    lbl_metodo.pack(side="left", padx=10, pady=5)

                    lbl_monto = ctk.CTkLabel(
                        frame_fila, 
                        text=f"Gs. {suma:,.0f}".replace(",", "."), 
                        font=("Arial", 12, "bold")
                    )
                    lbl_monto.pack(side="right", padx=10, pady=5)

            # 3. Totales
            self.lbl_cant_ventas.configure(text=f"{cant_ventas} pedido(s)")
            self.lbl_total_ventas.configure(text=f"Gs. {total_ventas:,.0f}".replace(",", "."))

            total_esperado = monto_inicial + total_ventas
            self.lbl_total_general.configure(text=f"Gs. {total_esperado:,.0f}".replace(",", "."))

        # Usar el ejecutor en segundo plano si la app principal lo tiene
        if hasattr(parent_app, 'ejecutar_en_segundo_plano'):
            parent_app.ejecutar_en_segundo_plano(
                funcion_db=self.db.obtener_cierre_caja_activa,
                al_finalizar=al_obtener_datos
            )
        else:
            try:
                res = self.db.obtener_cierre_caja_activa()
                al_obtener_datos(res, None)
            except Exception as e:
                al_obtener_datos(None, e)

    def confirmar_cierre(self):
        respuesta = messagebox.askyesno(
            "Confirmación de Cierre",
            "¿Estás seguro de que deseas procesar el cierre de caja?\n\n"
            "Esto finalizará la sesión actual y cambiará el estado de todas las ventas a 'CERRADO'.",
            icon="warning",
            parent=self
        )

        if not respuesta:
            return

        self.btn_cerrar.configure(state="disabled", text="Cerrando caja...")

        parent_app = self.master

        def al_finalizar_cierre(resultado, error):
            self.btn_cerrar.configure(state="normal", text="PROCESAR CIERRE DE CAJA")

            if error:
                messagebox.showerror("Error", f"Error al cerrar la caja:\n{error}", parent=self)
                return

            messagebox.showinfo("Caja Cerrada", "La sesión de caja ha sido cerrada correctamente.", parent=self)
            
            if self.al_cerrar_caja_exitoso:
                self.al_cerrar_caja_exitoso()

            self.destroy()

        if hasattr(parent_app, 'ejecutar_en_segundo_plano'):
            parent_app.ejecutar_en_segundo_plano(
                funcion_db=self.db.procesar_cierre_de_caja,
                al_finalizar=al_finalizar_cierre
            )
        else:
            try:
                self.db.procesar_cierre_de_caja()
                al_finalizar_cierre(None, None)
            except Exception as e:
                al_finalizar_cierre(None, e)