from database import DatabaseManager
from gui import VentanaPrincipal

if __name__ == "__main__":
    # Instancia el gestor de base de datos (lee automáticamente las credenciales de Supabase del .env)
    db_manager = DatabaseManager()

    # Inicia la interfaz gráfica
    app = VentanaPrincipal(db_manager)
    app.mainloop()