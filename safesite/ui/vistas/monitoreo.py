"""monitoreo.py - Vista de monitoreo en vivo (solo interfaz)."""
from datetime import datetime

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QColor, QImage
from PyQt6.QtWidgets import (
    QCheckBox, QGridLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QVBoxLayout, QWidget,
)

from safesite.config import AMARILLO, AZUL, GRIS, ROJO, VERDE
from safesite.ui.componentes import (
    BannerEstado, TarjetaEstado, VisorVideo, refrescar_estilo,
)


class VistaMonitoreo(QWidget):
    """
    Contrato para la fase 2:
      Señales (la vista las emite):
        iniciar_solicitado, detener_solicitado, silenciar_cambiado(bool)
      Métodos (la lógica los llama):
        mostrar_frame(QImage)
        actualizar_estado(dict) con claves:
            camara(bool), personas(int), cumplen(int), incumplen(int),
            fps(float), infraccion(bool), alarma("SONANDO"|"SILENCIADA"|"APAGADA")
        establecer_ejecucion(bool)
        agregar_evento(texto, color)
    """

    iniciar_solicitado = pyqtSignal()
    detener_solicitado = pyqtSignal()
    silenciar_cambiado = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self._activo = False

        raiz = QHBoxLayout(self)
        raiz.setContentsMargins(24, 20, 24, 20)
        raiz.setSpacing(18)

        # ---- Columna izquierda: video + controles ----
        izquierda = QVBoxLayout()
        izquierda.setSpacing(12)
        self.visor = VisorVideo()
        izquierda.addWidget(self.visor, 1)

        controles = QHBoxLayout()
        self.btn_toggle = QPushButton("▶  Iniciar monitoreo")
        self.btn_toggle.setObjectName("primario")
        self.btn_toggle.setMinimumHeight(40)
        self.btn_toggle.clicked.connect(self._al_click_toggle)
        self.chk_silenciar = QCheckBox("Silenciar alarma sonora")
        self.chk_silenciar.toggled.connect(self.silenciar_cambiado)
        controles.addWidget(self.btn_toggle)
        controles.addSpacing(12)
        controles.addWidget(self.chk_silenciar)
        controles.addStretch()
        izquierda.addLayout(controles)
        raiz.addLayout(izquierda, 1)

        # ---- Columna derecha: estado ----
        derecha_w = QWidget()
        derecha_w.setFixedWidth(340)
        derecha = QVBoxLayout(derecha_w)
        derecha.setContentsMargins(0, 0, 0, 0)
        derecha.setSpacing(12)

        self.banner = BannerEstado()
        derecha.addWidget(self.banner)

        cuadricula = QGridLayout()
        cuadricula.setSpacing(10)
        self.t_camara = TarjetaEstado("Cámara")
        self.t_personas = TarjetaEstado("Personas")
        self.t_cumplen = TarjetaEstado("Con EPP completo")
        self.t_incumplen = TarjetaEstado("Sin EPP")
        self.t_fps = TarjetaEstado("FPS")
        self.t_alarma = TarjetaEstado("Alarma")
        tarjetas = (self.t_camara, self.t_personas, self.t_cumplen,
                    self.t_incumplen, self.t_fps, self.t_alarma)
        for i, t in enumerate(tarjetas):
            cuadricula.addWidget(t, i // 2, i % 2)
        derecha.addLayout(cuadricula)

        lbl_eventos = QLabel("Actividad reciente")
        lbl_eventos.setObjectName("seccion")
        derecha.addWidget(lbl_eventos)
        self.lista_eventos = QListWidget()
        self.lista_eventos.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        derecha.addWidget(self.lista_eventos, 1)
        raiz.addWidget(derecha_w)

        self.establecer_ejecucion(False)
        self.agregar_evento("Aplicación iniciada", GRIS)

    # ------------------------- API pública -------------------------
    def mostrar_frame(self, imagen: QImage) -> None:
        self.visor.mostrar_frame(imagen)

    def establecer_ejecucion(self, activo: bool) -> None:
        self._activo = activo
        if activo:
            self.btn_toggle.setText("■  Detener monitoreo")
            self.btn_toggle.setObjectName("peligro")
            self.banner.set_estado("SISTEMA ACTIVO", AZUL)
            self.t_camara.set_valor("Activa", VERDE)
        else:
            self.btn_toggle.setText("▶  Iniciar monitoreo")
            self.btn_toggle.setObjectName("primario")
            self.banner.set_estado("SISTEMA DETENIDO", GRIS)
            self.visor.limpiar()
            self.t_camara.set_valor("Inactiva", GRIS)
            for t in (self.t_personas, self.t_cumplen, self.t_incumplen, self.t_fps):
                t.set_valor("—", GRIS)
            self.t_alarma.set_valor("Apagada", GRIS)
        refrescar_estilo(self.btn_toggle)

    def actualizar_estado(self, e: dict) -> None:
        camara_ok = e.get("camara", True)
        self.t_camara.set_valor("Activa" if camara_ok else "Inactiva",
                                VERDE if camara_ok else GRIS)
        self.t_personas.set_valor(str(e["personas"]), AZUL)
        self.t_cumplen.set_valor(str(e["cumplen"]), VERDE if e["cumplen"] else GRIS)
        self.t_incumplen.set_valor(str(e["incumplen"]), ROJO if e["incumplen"] else GRIS)
        self.t_fps.set_valor(f"{e['fps']:.1f}", VERDE if e["fps"] >= 8 else AMARILLO)

        alarma = e.get("alarma", "APAGADA")
        colores = {"SONANDO": ROJO, "SILENCIADA": AMARILLO, "APAGADA": VERDE}
        self.t_alarma.set_valor(alarma.capitalize(), colores.get(alarma, GRIS))

        if e["personas"] == 0:
            self.banner.set_estado("SIN PERSONAS", GRIS)
        elif e["infraccion"]:
            self.banner.set_estado("ALERTA: FALTA EPP", ROJO)
        else:
            self.banner.set_estado("EPP COMPLETO", VERDE)

    def agregar_evento(self, texto: str, color: str = GRIS) -> None:
        hora = datetime.now().strftime("%H:%M:%S")
        item = QListWidgetItem(f"{hora}  ·  {texto}")
        item.setForeground(QColor(color))
        self.lista_eventos.insertItem(0, item)
        while self.lista_eventos.count() > 50:
            self.lista_eventos.takeItem(self.lista_eventos.count() - 1)

    # ------------------------- Internos -------------------------
    def _al_click_toggle(self) -> None:
        if self._activo:
            self.detener_solicitado.emit()
        else:
            self.iniciar_solicitado.emit()
