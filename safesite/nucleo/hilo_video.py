"""hilo_video.py - Hilo de monitoreo: cámara -> detección -> alarma -> registro.

Se ejecuta en un QThread para no bloquear la interfaz. Se comunica con la GUI
únicamente mediante señales.
"""
import os
import time
from datetime import datetime

import cv2
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage

from safesite import config
from safesite.datos import base_datos
from safesite.nucleo.alarma import Alarma
from safesite.nucleo.detector import DetectorEPP
from safesite.nucleo.dibujo import dibujar


def _parsear_resolucion(texto: str) -> tuple[int, int]:
    try:
        ancho, alto = texto.lower().split("x")
        return int(ancho), int(alto)
    except ValueError:
        return 640, 480


class HiloVideo(QThread):
    """
    Señales:
      frame_listo(QImage)        fotograma anotado
      estado(dict)               claves: camara, personas, cumplen, incumplen, fps,
                                 infraccion, alarma ("SONANDO"|"SILENCIADA"|"APAGADA")
      nueva_infraccion(int)      id registrado en SQLite
      evento(str, str)           texto y color para la actividad reciente
      cargando()                 se está cargando el modelo (primera vez)
      error(str)                 fallo de cámara u otro problema
    """

    frame_listo = pyqtSignal(QImage)
    estado = pyqtSignal(dict)
    nueva_infraccion = pyqtSignal(int)
    evento = pyqtSignal(str, str)
    cargando = pyqtSignal()
    error = pyqtSignal(str)

    _cache_detectores: dict[str, DetectorEPP] = {}  # el modelo se carga una sola vez

    def __init__(self, ajustes: dict, silenciar: bool = False, detector=None,
                 fuente=None, db_path: str | None = None):
        """
        ajustes : diccionario con las claves de config.AJUSTES_POR_DEFECTO
        detector: objeto con .analizar(frame) y .nombre_modo (útil para pruebas)
        fuente  : índice de cámara o ruta de video; por defecto, la cámara de los ajustes
        """
        super().__init__()
        self.ajustes = dict(ajustes)
        self.silenciar = silenciar
        self._detector_inyectado = detector
        self._fuente = fuente
        self._db_path = db_path
        self._activo = False

    def detener(self) -> None:
        self._activo = False

    # ------------------------------------------------------------------
    def _obtener_detector(self):
        if self._detector_inyectado is not None:
            return self._detector_inyectado
        ruta = self.ajustes["modelo"]
        if ruta not in HiloVideo._cache_detectores:
            self.cargando.emit()
            HiloVideo._cache_detectores[ruta] = DetectorEPP(ruta)
        detector = HiloVideo._cache_detectores[ruta]
        detector.imgsz = int(self.ajustes["imgsz"])
        detector.confianza = int(self.ajustes["confianza"]) / 100
        return detector

    def _registrar(self, imagen, personas) -> tuple[int, str]:
        carpeta = self.ajustes.get("carpeta_capturas") or config.CARPETA_CAPTURAS
        os.makedirs(carpeta, exist_ok=True)
        marca = datetime.now().strftime("%Y%m%d_%H%M%S")
        ruta = os.path.join(carpeta, f"infraccion_{marca}.jpg")
        cv2.imwrite(ruta, imagen)

        faltas = sorted({f for p in personas for f in p["faltas"]})
        tipo = ", ".join(faltas) if faltas else "Falta de EPP"
        id_reg = base_datos.insertar_infraccion(tipo, ruta, db_path=self._db_path)
        print(f"[ALERTA] #{id_reg} {tipo} -> {ruta}")
        return id_reg, tipo

    # ------------------------------------------------------------------
    def run(self) -> None:
        self._activo = True
        cap = None
        alarma = None
        try:
            detector = self._obtener_detector()
            alarma = Alarma(int(self.ajustes["volumen"]))

            es_camara = self._fuente is None or isinstance(self._fuente, int)
            fuente = self.ajustes["camara_indice"] if self._fuente is None else self._fuente
            cap = cv2.VideoCapture(fuente)
            if es_camara:
                ancho, alto = _parsear_resolucion(self.ajustes["resolucion"])
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, ancho)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, alto)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # menor latencia
            if not cap.isOpened():
                self.error.emit("No se pudo abrir la cámara. Revisa el índice en Ajustes "
                                "y que ninguna otra aplicación la esté usando.")
                return

            self.evento.emit("Cámara conectada", config.VERDE)
            self.evento.emit(f"Detección: {detector.nombre_modo}", config.AZUL)

            salto = max(1, int(self.ajustes["salto_frames"]))
            alarma_activa = bool(self.ajustes["alarma_activa"])
            contador, personas, consecutivas = 0, [], 0
            infraccion_previa = False
            ultimo_registro = 0.0
            fps, t_prev = 0.0, time.time()

            while self._activo:
                ok, frame = cap.read()
                if not ok:
                    if es_camara:
                        self.error.emit("Se perdió la señal de la cámara.")
                    else:
                        self.evento.emit("Fin del video", config.GRIS)
                    break
                contador += 1

                # Salto de fotogramas: inferencia solo cada N frames
                if contador == 1 or contador % salto == 0:
                    personas = detector.analizar(frame)
                    hay_falta = any(p["faltas"] for p in personas)
                    consecutivas = consecutivas + 1 if hay_falta else 0

                infraccion = consecutivas >= config.CONFIRMACION

                ahora = time.time()
                fps = 0.9 * fps + 0.1 * (1.0 / max(ahora - t_prev, 1e-6))
                t_prev = ahora

                salida = dibujar(frame, personas, infraccion, fps)

                # Alarma continua: suena mientras haya infracción (si no está silenciada)
                debe_sonar = infraccion and alarma_activa and not self.silenciar
                if debe_sonar:
                    alarma.iniciar()
                else:
                    alarma.detener()

                # Registro en BD + captura (con enfriamiento)
                if infraccion and (ahora - ultimo_registro) >= config.COOLDOWN_REGISTRO:
                    id_reg, tipo = self._registrar(salida, personas)
                    ultimo_registro = ahora
                    self.nueva_infraccion.emit(id_reg)
                    self.evento.emit(f"Infracción #{id_reg}: {tipo}", config.ROJO)
                if infraccion_previa and not infraccion:
                    self.evento.emit("EPP regularizado: alarma detenida", config.VERDE)
                infraccion_previa = infraccion

                # Enviar imagen y estado a la interfaz
                rgb = cv2.cvtColor(salida, cv2.COLOR_BGR2RGB)
                h, w, _ = rgb.shape
                self.frame_listo.emit(
                    QImage(rgb.data, w, h, 3 * w, QImage.Format.Format_RGB888).copy())

                incumplen = sum(1 for p in personas if p["faltas"])
                if debe_sonar:
                    estado_alarma = "SONANDO"
                elif infraccion:
                    estado_alarma = "SILENCIADA"
                else:
                    estado_alarma = "APAGADA"
                self.estado.emit({
                    "camara": True,
                    "personas": len(personas),
                    "cumplen": len(personas) - incumplen,
                    "incumplen": incumplen,
                    "fps": fps,
                    "infraccion": infraccion,
                    "alarma": estado_alarma,
                })
        except Exception as exc:  # noqa: BLE001 - mostrar cualquier fallo en la interfaz
            self.error.emit(f"Error en el monitoreo: {exc}")
        finally:
            if cap is not None:
                cap.release()
            if alarma is not None:
                alarma.cerrar()
