"""Pruebas automáticas de SafeSite (sin cámara ni modelo YOLO).

Ejecutar desde la raíz del proyecto:
    python -m unittest discover -s tests -v
"""
import os
import sys
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")   # GUI sin pantalla
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")        # pygame sin tarjeta de audio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2  # noqa: E402
import numpy as np  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

from safesite import config  # noqa: E402
from safesite.datos import base_datos  # noqa: E402
from safesite.nucleo.alarma import Alarma  # noqa: E402
from safesite.nucleo.detector import faltas_por_color  # noqa: E402
from safesite.nucleo.dibujo import dibujar  # noqa: E402
from safesite.nucleo.hilo_video import HiloVideo  # noqa: E402

BBOX = (200, 50, 440, 450)  # persona de prueba dentro de un fotograma 640x480


def fotograma_gris() -> np.ndarray:
    return np.full((480, 640, 3), 128, np.uint8)


def pintar_casco(frame):
    x1, y1, x2, y2 = BBOX
    h = y2 - y1
    frame[y1:y1 + int(h * 0.22), x1:x2] = (0, 255, 255)      # amarillo (BGR)


def pintar_chaleco(frame):
    x1, y1, x2, y2 = BBOX
    h = y2 - y1
    frame[y1 + int(h * 0.24):y1 + int(h * 0.62), x1:x2] = (0, 255, 160)  # verde-amarillo


class DetectorFalso:
    """Reemplaza a YOLO: siempre ve a una persona con las faltas indicadas."""

    nombre_modo = "Detector de prueba"

    def __init__(self, faltas):
        self.faltas = faltas

    def analizar(self, frame):
        return [{"bbox": BBOX, "faltas": list(self.faltas)}]


class PruebasBaseDatos(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "prueba.db")
        base_datos.init_db(self.db)

    def tearDown(self):
        self.tmp.cleanup()

    def test_insertar_y_listar(self):
        id1 = base_datos.insertar_infraccion("Sin casco", "capturas/a.jpg", self.db)
        id2 = base_datos.insertar_infraccion("Sin chaleco", "capturas/b.jpg", self.db)
        self.assertEqual((id1, id2), (1, 2))
        filas = base_datos.listar_infracciones(10, self.db)
        self.assertEqual([f["id"] for f in filas], [2, 1])  # más reciente primero
        self.assertEqual(filas[0]["tipo"], "Sin chaleco")
        self.assertTrue(os.path.isabs(filas[0]["ruta"]))
        self.assertEqual(base_datos.contar_infracciones(self.db), 2)

    def test_tabla_tiene_las_columnas_pedidas(self):
        import sqlite3
        con = sqlite3.connect(self.db)
        columnas = [c[1] for c in con.execute("PRAGMA table_info(infracciones)")]
        con.close()
        self.assertEqual(columnas, ["id", "fecha_hora", "tipo_falta", "ruta_captura"])


class PruebasReglasColor(unittest.TestCase):
    def test_sin_epp(self):
        self.assertEqual(faltas_por_color(fotograma_gris(), BBOX),
                         ["Sin casco", "Sin chaleco"])

    def test_solo_casco(self):
        f = fotograma_gris()
        pintar_casco(f)
        self.assertEqual(faltas_por_color(f, BBOX), ["Sin chaleco"])

    def test_epp_completo(self):
        f = fotograma_gris()
        pintar_casco(f)
        pintar_chaleco(f)
        self.assertEqual(faltas_por_color(f, BBOX), [])


class PruebasDibujoYAlarma(unittest.TestCase):
    def test_dibujo_rojo_y_verde(self):
        base = fotograma_gris()
        rojo = dibujar(base, [{"bbox": BBOX, "faltas": ["Sin casco"]}], True, 10.0)
        verde = dibujar(base, [{"bbox": BBOX, "faltas": []}], False, 10.0)
        self.assertEqual(tuple(rojo[250, BBOX[0]]), (0, 0, 255))    # borde rojo (BGR)
        self.assertEqual(tuple(verde[250, BBOX[0]]), (0, 200, 0))   # borde verde
        self.assertFalse(np.array_equal(base, rojo))                # no modifica el original

    def test_alarma_inicia_y_se_detiene(self):
        alarma = Alarma(volumen=10)
        self.assertTrue(alarma.disponible)
        alarma.iniciar()
        self.assertTrue(alarma.sonando)
        alarma.detener()
        self.assertFalse(alarma.sonando)
        alarma.cerrar()


class PruebasHiloVideo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "prueba.db")
        base_datos.init_db(self.db)
        self.video = os.path.join(self.tmp.name, "video.avi")
        escritor = cv2.VideoWriter(self.video, cv2.VideoWriter_fourcc(*"MJPG"), 15, (640, 480))
        for _ in range(30):
            escritor.write(fotograma_gris())
        escritor.release()
        self.ajustes = dict(config.AJUSTES_POR_DEFECTO)
        self.ajustes.update(carpeta_capturas=os.path.join(self.tmp.name, "capturas"),
                            salto_frames=1, volumen=10)

    def tearDown(self):
        self.tmp.cleanup()

    def _ejecutar(self, faltas):
        hilo = HiloVideo(self.ajustes, detector=DetectorFalso(faltas),
                         fuente=self.video, db_path=self.db)
        estados, infracciones, errores, frames = [], [], [], []
        hilo.estado.connect(estados.append)
        hilo.nueva_infraccion.connect(infracciones.append)
        hilo.error.connect(errores.append)
        hilo.frame_listo.connect(frames.append)
        hilo.run()  # síncrono: ejecuta el bucle completo en este hilo
        return estados, infracciones, errores, frames

    def test_infraccion_dispara_alarma_captura_y_registro(self):
        estados, infracciones, errores, frames = self._ejecutar(["Sin casco"])
        self.assertEqual(errores, [])
        self.assertGreater(len(frames), 0)
        self.assertTrue(any(e["infraccion"] and e["alarma"] == "SONANDO" for e in estados))
        self.assertEqual(len(infracciones), 1)  # el enfriamiento evita registros repetidos
        filas = base_datos.listar_infracciones(10, self.db)
        self.assertEqual(filas[0]["tipo"], "Sin casco")
        self.assertTrue(os.path.exists(filas[0]["ruta"]))
        self.assertTrue(filas[0]["ruta"].endswith(".jpg"))

    def test_epp_completo_no_genera_infraccion(self):
        estados, infracciones, errores, _ = self._ejecutar([])
        self.assertEqual((errores, infracciones), ([], []))
        self.assertTrue(all(not e["infraccion"] and e["alarma"] == "APAGADA" for e in estados))
        self.assertEqual(base_datos.contar_infracciones(self.db), 0)

    def test_alarma_silenciada(self):
        self.ajustes["alarma_activa"] = False
        estados, _, _, _ = self._ejecutar(["Sin chaleco"])
        self.assertTrue(any(e["alarma"] == "SILENCIADA" for e in estados))
        self.assertFalse(any(e["alarma"] == "SONANDO" for e in estados))

    def test_fuente_inexistente_emite_error(self):
        hilo = HiloVideo(self.ajustes, detector=DetectorFalso([]),
                         fuente=os.path.join(self.tmp.name, "no_existe.avi"), db_path=self.db)
        errores = []
        hilo.error.connect(errores.append)
        hilo.run()
        self.assertEqual(len(errores), 1)


class PruebasVentana(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_ventana_navega_y_carga_historial(self):
        tmp = tempfile.TemporaryDirectory()
        original = config.DB_PATH
        config.DB_PATH = os.path.join(tmp.name, "ventana.db")
        try:
            base_datos.init_db()
            base_datos.insertar_infraccion("Sin casco", "capturas/no_existe.jpg")
            from safesite.ui.ventana_principal import VentanaPrincipal
            v = VentanaPrincipal()
            v.show()
            self.app.processEvents()
            for i in range(3):
                v._ir_a(i)
                self.assertEqual(v.paginas.currentIndex(), i)
            self.assertEqual(v.vista_historial.tabla.rowCount(), 1)
            v.vista_monitoreo.actualizar_estado(
                {"camara": True, "personas": 1, "cumplen": 0, "incumplen": 1,
                 "fps": 12.0, "infraccion": True, "alarma": "SONANDO"})
            self.assertEqual(v.vista_monitoreo.banner.text(), "ALERTA: FALTA EPP")
            v.close()
        finally:
            config.DB_PATH = original
            tmp.cleanup()


if __name__ == "__main__":
    unittest.main(verbosity=2)
