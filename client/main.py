from client.api_client import APIClient
from client.gui import VentanaPrincipal


def main():
    api = APIClient()

    app = VentanaPrincipal(api)
    app.mainloop()


if __name__ == "__main__":
    main()