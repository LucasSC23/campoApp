from api_client import APIClient
from gui import VentanaPrincipal


def main():
    api = APIClient()

    app = VentanaPrincipal(api)
    app.mainloop()


if __name__ == "__main__":
    main()