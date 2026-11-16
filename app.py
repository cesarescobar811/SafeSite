
import logging
import os
import sys
import threading
import traceback
from logging.handlers import RotatingFileHandler

try:
    from PyQt6.QtCore import QStandardPaths, QThread
    from PyQt6.QtWidgets import QApplication, QMessageBox
except ModuleNotFoundError:
    print("Falta instalar las dependencias. Ejecuta:  pip install -r requirements.txt")
    sys.exit(1)

from safesite.config import NOMBRE_APP

# Nombre del módulo que no se pudo importar -> nombre del paquete que se instala con pip
PAQUETES = {"cv2": "opencv-python", "pygame": "pygame-ce", "PyQt6": "PyQt6",
            "numpy": "numpy", "ultralytics": "ultralytics"}

_registro = logging.getLogger("safesite")
_ruta_log = ""
_mostrando_error = False  # evita diálogos en cascada si el propio diálogo falla


def _configurar_registro() -> str:
    """Crea el archivo de registro en la carpeta de datos del usuario (fuera del repositorio)."""
    carpeta = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    carpeta = carpeta or os.path.join(os.path.expanduser("~"), ".safesite")
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, "safesite.log")
    manejador = RotatingFileHandler(ruta, maxBytes=500_000, backupCount=2, encoding="utf-8")
    manejador.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    _registro.setLevel(logging.INFO)
    _registro.addHandler(manejador)
    return ruta


def _manejar_excepcion(tipo, valor, tb) -> None:
    """Registra la excepción y, si ocurre en la interfaz, avisa al usuario sin cerrar la app."""
    global _mostrando_error
    if issubclass(tipo, KeyboardInterrupt):
        sys.__excepthook__(tipo, valor, tb)
        return
    detalle = "".join(traceback.format_exception(tipo, valor, tb))
    _registro.error("Excepción no controlada:\n%s", detalle)
    print(detalle, file=sys.stderr)

    app = QApplication.instance()
    en_hilo_grafico = app is not None and QThread.currentThread() is app.thread()
    if not en_hilo_grafico or _mostrando_error:
        return  # fuera del hilo de la interfaz solo se registra
    _mostrando_error = True
    try:
        caja = QMessageBox(QMessageBox.Icon.Critical, NOMBRE_APP,
                           "Ocurrió un error inesperado. La aplicación sigue abierta, pero "
                           "conviene guardar lo que estés haciendo y reiniciarla.")
        caja.setInformativeText(f"{tipo.__name__}: {valor}\n\nRegistro: {_ruta_log}")
        caja.setDetailedText(detalle)
        caja.exec()
    except Exception:  # noqa: BLE001 - nunca fallar dentro del manejador de errores
        pass
    finally:
        _mostrando_error = False


def _excepcion_en_hilo(args) -> None:
    _manejar_excepcion(args.exc_type, args.exc_value, args.exc_traceback)


def _importar_ventana():
    """Importa la ventana principal. Si falta una dependencia, avisa con claridad y termina."""
    try:
        from safesite.ui.ventana_principal import VentanaPrincipal
    except ModuleNotFoundError as exc:
        modulo = (exc.name or "").split(".")[0]
        faltante = PAQUETES.get(modulo, modulo or "una dependencia")
        _registro.error("Dependencia faltante: %s (módulo %s)", faltante, modulo)
        QMessageBox.critical(
            None, NOMBRE_APP,
            f"Falta instalar «{faltante}».\n\nActiva el entorno virtual y ejecuta:\n"
            "pip install -r requirements.txt")
        sys.exit(1)
    return VentanaPrincipal


def main() -> None:
    global _ruta_log
    app = QApplication(sys.argv)
    app.setApplicationName(NOMBRE_APP)
    app.setOrganizationName(NOMBRE_APP)

    _ruta_log = _configurar_registro()
    sys.excepthook = _manejar_excepcion
    threading.excepthook = _excepcion_en_hilo
    _registro.info("SafeSite iniciado. Registro en %s", _ruta_log)

    VentanaPrincipal = _importar_ventana()
    ventana = VentanaPrincipal()
    ventana.show()
    codigo = app.exec()
    _registro.info("SafeSite cerrado (código %s)", codigo)
    sys.exit(codigo)


if __name__ == "__main__":
    main()
