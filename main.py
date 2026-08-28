from database import DBManager
from gui import VentanaPrincipal


def main():
    db = DBManager()
    db.init_db()

    app = VentanaPrincipal(db)
    app.mainloop()


if __name__ == "__main__":
    main()