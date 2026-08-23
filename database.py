import os
import psycopg2
from contextlib import contextmanager
from dotenv import load_dotenv

# Carga variables de entorno (.env)
load_dotenv()


class DatabaseManager:
    def __init__(self, host=None, port=None, database=None, user=None, password=None):
        self.db_config = {
            "host": host or os.getenv("DB_HOST", "localhost"),
            "database": database or os.getenv("DB_NAME", "postgres"),
            "user": user or os.getenv("DB_USER", "postgres"),
            "password": password or os.getenv("DB_PASSWORD", ""),
            "port": port or os.getenv("DB_PORT", "5432"),
            "sslmode": "require",
            "connect_timeout": 10
        }
        self.init_db()

    @contextmanager
    def obtener_conexion(self):
        """Maneja conexiones independientes a la base de datos."""
        conn = psycopg2.connect(**self.db_config)
        try:
            yield conn
        finally:
            conn.close()

    def init_db(self):
        """Crea las tablas en PostgreSQL / Supabase si no existen."""
        try:
            with self.obtener_conexion() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS productos (
                            id SERIAL PRIMARY KEY,
                            nombre VARCHAR(100) UNIQUE NOT NULL,
                            precio NUMERIC(12, 2) NOT NULL,
                            categoria VARCHAR(50) NOT NULL,
                            subcategoria VARCHAR(50) NOT NULL,
                            descripcion TEXT
                        );
                    ''')

                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS sesiones_caja (
                            id SERIAL PRIMARY KEY,
                            monto_inicial NUMERIC(12, 2) NOT NULL,
                            monto_final NUMERIC(12, 2) DEFAULT 0,
                            fecha_apertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            fecha_cierre TIMESTAMP,
                            estado VARCHAR(20) DEFAULT 'ABIERTA'
                        );
                    ''')

                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS ventas (
                            id SERIAL PRIMARY KEY,
                            sesion_id INT REFERENCES sesiones_caja(id) ON DELETE CASCADE,
                            monto_total NUMERIC(12, 2) NOT NULL,
                            metodo_pago VARCHAR(50) NOT NULL,
                            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    ''')

                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS detalle_ventas (
                            id SERIAL PRIMARY KEY,
                            venta_id INT REFERENCES ventas(id) ON DELETE CASCADE,
                            producto_nombre VARCHAR(100) NOT NULL,
                            cantidad INT NOT NULL,
                            precio_unitario NUMERIC(12, 2) NOT NULL,
                            subtotal NUMERIC(12, 2) NOT NULL,
                            notas TEXT
                        );
                    ''')
                    conn.commit()
        except Exception as e:
            print(f"Notificación init_db: {e}")

    # ==========================================
    # GESTIÓN DE PRODUCTOS Y MENÚ
    # ==========================================

    def obtener_categorias_principales(self):
        """Devuelve las categorías priorizando el orden personalizado del menú."""
        orden_prioritario = [
            "Hamburguesas",
            "Lomitos y Sándwiches",
            "Helados y Postres",
            "Agregados",
        ]

        with self.obtener_conexion() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT DISTINCT categoria 
                    FROM productos 
                    WHERE categoria IS NOT NULL AND TRIM(categoria) != '';
                """
                )
                categorias = [r[0] for r in cursor.fetchall()]

        # Ordena según la lista prioritaria (y al final cualquier otra que exista)
        categorias.sort(
            key=lambda cat: (
                orden_prioritario.index(cat)
                if cat in orden_prioritario
                else len(orden_prioritario)
            )
        )
        return categorias

    def obtener_categorias(self):
        return self.obtener_categorias_principales()

    def obtener_productos_filtrados(self, categoria=None, busqueda=None):
        with self.obtener_conexion() as conn:
            with conn.cursor() as cursor:
                query = "SELECT id, nombre, precio, categoria, subcategoria FROM productos WHERE 1=1"
                params = []

                if categoria and str(categoria).strip().upper() != "TODOS":
                    cat_limpia = str(categoria).strip()
                    query += " AND (TRIM(LOWER(categoria)) = TRIM(LOWER(%s)) OR TRIM(LOWER(subcategoria)) = TRIM(LOWER(%s)))"
                    params.extend([cat_limpia, cat_limpia])

                if busqueda and str(busqueda).strip():
                    term = f"%{str(busqueda).strip()}%"
                    query += " AND (nombre ILIKE %s OR subcategoria ILIKE %s OR categoria ILIKE %s)"
                    params.extend([term, term, term])

                query += " ORDER BY id, categoria, subcategoria, nombre;"
                cursor.execute(query, params)
                filas = cursor.fetchall()

        return [(r[0], r[1], float(r[2]), r[3], r[4]) for r in filas]

    # ==========================================
    # GESTIÓN DE CAJA Y SESIONES
    # ==========================================

    def obtener_sesion_activa(self):
        """Devuelve tupla (id, estado, monto_inicial, fecha) según gui.py."""
        with self.obtener_conexion() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, estado, monto_inicial, fecha_apertura 
                    FROM sesiones_caja 
                    WHERE estado = 'ABIERTA' 
                    ORDER BY id DESC LIMIT 1;
                """)
                return cursor.fetchone()

    def abrir_caja(self, monto_inicial):
        with self.obtener_conexion() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO sesiones_caja (monto_inicial, estado, fecha_apertura)
                    VALUES (%s, 'ABIERTA', CURRENT_TIMESTAMP)
                    RETURNING id;
                """, (monto_inicial,))
                sesion_id = cursor.fetchone()[0]
                conn.commit()
                return sesion_id

    def actualizar_monto_inicial(self, sesion_id, nuevo_monto):
        with self.obtener_conexion() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE sesiones_caja 
                    SET monto_inicial = %s 
                    WHERE id = %s;
                """, (nuevo_monto, sesion_id))
                conn.commit()

    def obtener_cierre_caja_activa(self):
        """Retorna (desglose, total_ventas, cant_ventas, monto_inicial) requeridos por gui.py."""
        sesion = self.obtener_sesion_activa()
        if not sesion:
            return [], 0.0, 0, 0.0

        sesion_id = sesion[0]
        monto_inicial = float(sesion[2])

        with self.obtener_conexion() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT metodo_pago, COALESCE(SUM(monto_total), 0), COUNT(id)
                    FROM ventas
                    WHERE sesion_id = %s
                    GROUP BY metodo_pago;
                """, (sesion_id,))
                desglose = [(r[0], float(r[1]), r[2]) for r in cursor.fetchall()]

                cursor.execute("""
                    SELECT COALESCE(SUM(monto_total), 0), COUNT(id)
                    FROM ventas
                    WHERE sesion_id = %s;
                """, (sesion_id,))
                row = cursor.fetchone()
                total_ventas = float(row[0]) if row else 0.0
                cant_ventas = row[1] if row else 0

        return desglose, total_ventas, cant_ventas, monto_inicial

    def procesar_cierre_de_caja(self):
        sesion = self.obtener_sesion_activa()
        if not sesion:
            return

        sesion_id = sesion[0]
        _, total_ventas, _, monto_inicial = self.obtener_cierre_caja_activa()
        monto_final = monto_inicial + total_ventas

        with self.obtener_conexion() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE sesiones_caja 
                    SET monto_final = %s, fecha_cierre = CURRENT_TIMESTAMP, estado = 'CERRADA'
                    WHERE id = %s;
                """, (monto_final, sesion_id))
                conn.commit()

    # ==========================================
    # GESTIÓN Y HISTORIAL DE VENTAS
    # ==========================================

    def registrar_venta(self, sesion_id, total, metodo_pago, carrito):
        with self.obtener_conexion() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO ventas (sesion_id, monto_total, metodo_pago, fecha)
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                    RETURNING id;
                """, (sesion_id, total, metodo_pago))
                venta_id = cursor.fetchone()[0]

                for item in carrito:
                    subtotal = float(item['precio']) * int(item['cantidad'])
                    cursor.execute("""
                        INSERT INTO detalle_ventas (venta_id, producto_nombre, cantidad, precio_unitario, subtotal, notas)
                        VALUES (%s, %s, %s, %s, %s, %s);
                    """, (venta_id, item['nombre'], item['cantidad'], item['precio'], subtotal, item.get('notas', '')))

                conn.commit()
                return venta_id

    def guardar_venta(self, total, metodo_pago, carrito):
        sesion = self.obtener_sesion_activa()
        sesion_id = sesion[0] if sesion else None
        return self.registrar_venta(sesion_id, total, metodo_pago, carrito)

    def obtener_ventas_activas(self):
        """Retorna ventas del turno con hora formateada: (id, hora, monto, metodo)."""
        sesion = self.obtener_sesion_activa()
        if not sesion:
            return []

        sesion_id = sesion[0]
        with self.obtener_conexion() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, TO_CHAR(fecha, 'HH24:MI'), monto_total, metodo_pago 
                    FROM ventas 
                    WHERE sesion_id = %s 
                    ORDER BY id DESC;
                """, (sesion_id,))
                return [(r[0], r[1], float(r[2]), r[3]) for r in cursor.fetchall()]

    def obtener_detalle_venta(self, venta_id):
        """Retorna ítems del pedido: (nombre, cantidad, precio_unit, subtotal, notas)."""
        with self.obtener_conexion() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT producto_nombre, cantidad, precio_unitario, subtotal, COALESCE(notas, '') 
                    FROM detalle_ventas 
                    WHERE venta_id = %s 
                    ORDER BY id ASC;
                """, (venta_id,))
                return [(r[0], r[1], float(r[2]), float(r[3]), r[4]) for r in cursor.fetchall()]

    def cambiar_metodo_pago(self, id_venta, nuevo_metodo):
        with self.obtener_conexion() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE ventas 
                    SET metodo_pago = %s 
                    WHERE id = %s;
                """, (nuevo_metodo, id_venta))
                conn.commit()

    def eliminar_venta(self, id_venta):
        with self.obtener_conexion() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM detalle_ventas WHERE venta_id = %s;", (id_venta,))
                cursor.execute("DELETE FROM ventas WHERE id = %s;", (id_venta,))
                conn.commit()