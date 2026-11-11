"""ventana_principal.py - Ventana principal: sidebar, header, navegación y monitoreo."""
from datetime import datetime

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QApplication, QButtonGroup, QFrame, QHBoxLayout, QLabel, QMainWindow,
    QMessageBox, QStackedWidget, QStatusBar, QVBoxLayout, QWidget,
)

from safesite.config import (
    AMARILLO, GRIS, NOMBRE_APP, ROJO, SUBTITULO, VERDE, VERSION,
)
from safesite.datos import base_datos
from safesite.nucleo.hilo_video import HiloVideo
from safesite.ui.componentes import BotonNav, Insignia
from safesite.ui.estilos import generar_qss
from safesite.ui.vistas.ajustes import VistaAjustes
from safesite.ui.vistas.historial import VistaHistorial
from safesite.ui.vistas.monitoreo import VistaMonitoreo

LIMITE_HISTORIAL = 200


class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{NOMBRE_APP} - {SUBTITULO}")
        self.resize(1280, 780)
        self.setMinimumSize(1020, 640)

        base_datos.init_db()
        self.hilo: HiloVideo | None = None

        # ---- Vistas ----
        self.vista_monitoreo = VistaMonitoreo()
        self.vista_historial = VistaHistorial()
        self.vista_ajustes = VistaAjustes()
        self._ajustes = self.vista_ajustes.valores()  # ajustes guardados en disco

        # (texto del botón, título del header, vista)
        self._paginas = [
            ("◉   Monitoreo en vivo", "Monitoreo en vivo", self.vista_monitoreo),
            ("☰   Historial", "Historial de infracciones", self.vista_historial),
            ("⚙   Ajustes", "Ajustes del sistema", self.vista_ajustes),
        ]

        # ---- Layout general ----
        central = QWidget()
        central.setObjectName("raiz")
        raiz = QHBoxLayout(central)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(0)
        raiz.addWidget(self._crear_sidebar())

        columna = QVBoxLayout()
        columna.setContentsMargins(0, 0, 0, 0)
        columna.setSpacing(0)
        columna.addWidget(self._crear_header())
        self.paginas = QStackedWidget()
        self.paginas.setObjectName("paginas")
        for _, _, vista in self._paginas:
            self.paginas.addWidget(vista)
        columna.addWidget(self.paginas, 1)
        raiz.addLayout(columna, 1)
        self.setCentralWidget(central)

        self.setStatusBar(QStatusBar())

        self._conectar_senales()
        self._aplicar_tema(self._ajustes["tema"])
        self._cargar_historial()
        self._ir_a(0)
        self.statusBar().showMessage("Listo · pulsa «Iniciar monitoreo» para comenzar", 8000)

        # Reloj del header
        self._timer_reloj = QTimer(self)
        self._timer_reloj.timeout.connect(self._actualizar_reloj)
        self._timer_reloj.start(1000)
        self._actualizar_reloj()

    # ------------------------- Construcción -------------------------
    def _crear_sidebar(self) -> QFrame:
        sb = QFrame()
        sb.setObjectName("sidebar")
        sb.setFixedWidth(240)
        lay = QVBoxLayout(sb)
        lay.setContentsMargins(14, 20, 14, 14)
        lay.setSpacing(6)

        logo = QLabel(NOMBRE_APP)
        logo.setObjectName("logo")
        sub = QLabel(SUBTITULO)
        sub.setObjectName("subtitulo")
        lay.addWidget(logo)
        lay.addWidget(sub)
        lay.addSpacing(22)

        self.grupo_nav = QButtonGroup(self)
        for i, (texto, _, _) in enumerate(self._paginas):
            boton = BotonNav(texto)
            self.grupo_nav.addButton(boton, i)
            lay.addWidget(boton)
        self.grupo_nav.idClicked.connect(self._ir_a)

        lay.addStretch()
        version = QLabel(VERSION)
        version.setObjectName("version")
        lay.addWidget(version)
        return sb

    def _crear_header(self) -> QFrame:
        h = QFrame()
        h.setObjectName("header")
        h.setFixedHeight(64)
        lay = QHBoxLayout(h)
        lay.setContentsMargins(24, 0, 24, 0)
        self.lbl_titulo = QLabel()
        self.lbl_titulo.setObjectName("titulo_pagina")
        self.lbl_reloj = QLabel()
        self.lbl_reloj.setObjectName("reloj")
        self.insignia_sistema = Insignia("●  DETENIDO", GRIS)
        centrado = Qt.AlignmentFlag.AlignVCenter
        lay.addWidget(self.lbl_titulo)
        lay.addStretch()
        lay.addWidget(self.lbl_reloj, 0, centrado)
        lay.addSpacing(16)
        lay.addWidget(self.insignia_sistema, 0, centrado)
        return h

    def _conectar_senales(self) -> None:
        m = self.vista_monitoreo
        m.iniciar_solicitado.connect(self._iniciar_monitoreo)
        m.detener_solicitado.connect(self._detener_monitoreo)
        m.silenciar_cambiado.connect(self._al_silenciar)
        self.vista_ajustes.ajustes_guardados.connect(self._al_guardar_ajustes)
        for vista in (self.vista_historial, self.vista_ajustes):
            vista.mensaje.connect(lambda t: self.statusBar().showMessage(t, 8000))
        self.vista_historial.refrescar_solicitado.connect(self._cargar_historial)

    # ------------------------- Navegación y tema -------------------------
    def _ir_a(self, indice: int) -> None:
        self.paginas.setCurrentIndex(indice)
        self.lbl_titulo.setText(self._paginas[indice][1])
        self.grupo_nav.button(indice).setChecked(True)

    def _aplicar_tema(self, tema: str) -> None:
        QApplication.instance().setStyleSheet(generar_qss(tema))

    def _al_guardar_ajustes(self, valores: dict) -> None:
        self._ajustes = valores
        self._aplicar_tema(valores["tema"])

    def _actualizar_reloj(self) -> None:
        self.lbl_reloj.setText(datetime.now().strftime("%d/%m/%Y  %H:%M:%S"))

    # ------------------------- Historial -------------------------
    def _cargar_historial(self) -> None:
        self.vista_historial.set_datos(base_datos.listar_infracciones(LIMITE_HISTORIAL))

    # ------------------------- Monitoreo real -------------------------
    def _iniciar_monitoreo(self) -> None:
        m = self.vista_monitoreo
        m.establecer_ejecucion(True)
        self.insignia_sistema.set_estado("●  INICIANDO", AMARILLO)

        self.hilo = HiloVideo(self._ajustes, silenciar=m.chk_silenciar.isChecked())
        self.hilo.cargando.connect(m.mostrar_cargando)
        self.hilo.frame_listo.connect(m.mostrar_frame)
        self.hilo.estado.connect(self._al_estado)
        self.hilo.evento.connect(m.agregar_evento)
        self.hilo.nueva_infraccion.connect(self._cargar_historial_sin_args)
        self.hilo.error.connect(self._al_error)
        self.hilo.finished.connect(self._al_finalizar)
        self.hilo.start()

    def _detener_monitoreo(self) -> None:
        if self.hilo is not None and self.hilo.isRunning():
            self.hilo.detener()
            self.vista_monitoreo.establecer_deteniendo()

    def _al_silenciar(self, silenciar: bool) -> None:
        if self.hilo is not None:
            self.hilo.silenciar = silenciar

    def _al_estado(self, e: dict) -> None:
        self.vista_monitoreo.actualizar_estado(e)
        if e["infraccion"]:
            self.insignia_sistema.set_estado("●  ALERTA", ROJO)
        else:
            self.insignia_sistema.set_estado("●  ACTIVO", VERDE)

    def _cargar_historial_sin_args(self, _id_registro: int) -> None:
        self._cargar_historial()

    def _al_error(self, mensaje: str) -> None:
        QMessageBox.warning(self, NOMBRE_APP, mensaje)

    def _al_finalizar(self) -> None:
        self.vista_monitoreo.establecer_ejecucion(False)
        self.vista_monitoreo.agregar_evento("Monitoreo detenido", GRIS)
        self.insignia_sistema.set_estado("●  DETENIDO", GRIS)

    # ------------------------- Cierre -------------------------
    def closeEvent(self, evento) -> None:
        if self.hilo is not None and self.hilo.isRunning():
            self.hilo.detener()
            self.hilo.wait(5000)
        evento.accept()
