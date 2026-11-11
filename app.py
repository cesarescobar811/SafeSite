"""app.py - Punto de entrada de SafeSite."""
import sys

from PyQt6.QtWidgets import QApplication

from safesite.config import NOMBRE_APP
from safesite.ui.ventana_principal import VentanaPrincipal


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(NOMBRE_APP)
    app.setOrganizationName(NOMBRE_APP)
    ventana = VentanaPrincipal()
    ventana.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
