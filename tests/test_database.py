from server.database import DBManager

def main():
    print("=== INICIANDO PRUEBA DE BASE DE DATOS ===")

    db = DBManager()

    print("\n=== 1. CONEXION ===")
    print(db.probar_conexion())

    print("\n=== 2. ESTRUCTURA ===")
    print("Estructura correcta:", db.verificar_estructura())

    print("\n=== 3. SESION ABIERTA ===")
    print(db.obtener_sesion_abierta())

    print("\n=== 4. RESUMEN DE CAJA ===")
    print(db.obtener_resumen_caja())

    print("\n=== 5. PRODUCTOS ===")
    productos = db.obtener_productos_filtrados()

    print(f"Productos encontrados: {len(productos)}")

    for producto in productos[:5]:
        print(producto)

    print("\n=== PRUEBA FINALIZADA CORRECTAMENTE ===")


if __name__ == "__main__":
    main()