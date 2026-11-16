"""Pruebas del punto de entrada (app.py): manejo de errores y dependencias faltantes.

Ejecutar desde la raíz del proyecto:
    python -m unittest discover -s tests -v
"""
import contextlib
import io
import logging
import os
import sys
import tempfile
import threading
import unittest
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")   # GUI sin pantalla
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")        # pygame sin tarjeta de audio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication, QMessageBox  # noqa: E402

import app as punto_entrada  # noqa: E402


class RegistroEnMemoria(logging.Handler):
    """Captura los mensajes del registro para poder comprobarlos sin escribir archivos."""

    def __init__(self):
        super().__init__()
        self.mensajes = []

    def emit(self, record):
        self.mensajes.append(record.getMessage())


def error_de_ejemplo():
    """Devuelve la información de una excepción real (tipo, valor, traza)."""
    try:
        1 / 0
    except ZeroDivisionError:
        return sys.exc_info()


class PruebasManejoDeErrores(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qapp = QApplication.instance() or QApplication([])

    def setUp(self):
        self.registro = RegistroEnMemoria()
        punto_entrada._registro.addHandler(self.registro)
        punto_entrada._registro.setLevel(logging.INFO)
        self.addCleanup(punto_entrada._registro.removeHandler, self.registro)
        punto_entrada._mostrando_error = False

        # Los cuadros de diálogo no se muestran: solo se anota su contenido.
        self.dialogos = []

        def falso_exec(caja):
            self.dialogos.append(caja.informativeText() + "\n" + caja.detailedText())
            return 0

        parche = mock.patch.object(QMessageBox, "exec", falso_exec)
        parche.start()
        self.addCleanup(parche.stop)

    def _manejar(self, info_error):
        with contextlib.redirect_stderr(io.StringIO()):  # evita ensuciar la salida de pruebas
            punto_entrada._manejar_excepcion(*info_error)

    def test_error_se_registra_y_muestra_dialogo(self):
        self._manejar(error_de_ejemplo())
        self.assertEqual(len(self.dialogos), 1)
        self.assertIn("ZeroDivisionError", self.dialogos[0])
        self.assertTrue(any("Excepción no controlada" in m for m in self.registro.mensajes))

    def test_error_en_otro_hilo_solo_se_registra(self):
        info = error_de_ejemplo()
        hilo = threading.Thread(target=self._manejar, args=(info,))
        hilo.start()
        hilo.join()
        self.assertEqual(self.dialogos, [])  # un diálogo desde otro hilo congelaría la interfaz
        self.assertTrue(any("Excepción no controlada" in m for m in self.registro.mensajes))

    def test_no_hay_dialogos_en_cascada(self):
        punto_entrada._mostrando_error = True
        self._manejar(error_de_ejemplo())
        self.assertEqual(self.dialogos, [])
        self.assertTrue(any("Excepción no controlada" in m for m in self.registro.mensajes))

    def test_ctrl_c_no_muestra_dialogo(self):
        with contextlib.redirect_stderr(io.StringIO()):
            punto_entrada._manejar_excepcion(KeyboardInterrupt, KeyboardInterrupt(), None)
        self.assertEqual(self.dialogos, [])


class PruebasRegistroEnArchivo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qapp = QApplication.instance() or QApplication([])

    def test_configurar_registro_crea_el_archivo(self):
        antes = list(punto_entrada._registro.handlers)
        with tempfile.TemporaryDirectory() as carpeta:
            try:
                with mock.patch.object(punto_entrada.QStandardPaths, "writableLocation",
                                       return_value=carpeta):
                    ruta = punto_entrada._configurar_registro()
                punto_entrada._registro.info("mensaje de prueba")
                self.assertEqual(os.path.dirname(ruta), carpeta)
                self.assertTrue(ruta.endswith("safesite.log"))
                with open(ruta, encoding="utf-8") as f:
                    self.assertIn("mensaje de prueba", f.read())
            finally:  # cerrar el archivo antes de borrar la carpeta temporal (Windows)
                for manejador in list(punto_entrada._registro.handlers):
                    if manejador not in antes:
                        punto_entrada._registro.removeHandler(manejador)
                        manejador.close()


class PruebasDependencias(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qapp = QApplication.instance() or QApplication([])

    def test_traduce_modulo_a_paquete_de_pip(self):
        self.assertEqual(punto_entrada.PAQUETES["cv2"], "opencv-python")
        self.assertEqual(punto_entrada.PAQUETES["pygame"], "pygame-ce")

    def test_importar_ventana_devuelve_la_clase(self):
        self.assertEqual(punto_entrada._importar_ventana().__name__, "VentanaPrincipal")

    def test_dependencia_faltante_avisa_y_termina(self):
        mensajes = []
        with mock.patch.dict(sys.modules):  # restaura sys.modules al salir del bloque
            for nombre in [n for n in sys.modules
                           if n.startswith(("safesite.ui", "safesite.nucleo"))]:
                del sys.modules[nombre]       # fuerza a importar de nuevo la ventana
            sys.modules["cv2"] = None         # simula que OpenCV no está instalado
            with mock.patch.object(
                    QMessageBox, "critical",
                    staticmethod(lambda padre, titulo, texto: mensajes.append(texto))):
                with self.assertRaises(SystemExit) as ctx:
                    punto_entrada._importar_ventana()
        self.assertEqual(ctx.exception.code, 1)
        self.assertEqual(len(mensajes), 1)
        self.assertIn("opencv-python", mensajes[0])
        self.assertIn("pip install -r requirements.txt", mensajes[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
