"""ventana_principal.py - Ventana principal: sidebar, header y navegación."""
from datetime import datetime

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QApplication, QButtonGroup, QFrame, QHBoxLayout, QLabel, QMainWindow,
    QStackedWidget, QStatusBar, QVBoxLayout, QWidget,
)

from safesite.config import AZUL, GRIS, NOMBRE_APP, SUBTITULO, VERDE, VERSION
from safesite.datos.datos_prueba import generar_infracciones, pixmap_prueba
from safesite.ui.componentes import BotonNav, Insignia
from safesite.ui.estilos import generar_qss
from safesite.ui.vistas.ajustes import VistaAjustes
from safesite.ui.vistas.historial import VistaHistorial
from safesite.ui.vistas.monitoreo import VistaMonitoreo


class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{NOMBRE_APP} - {SUBTITULO}")
        self.resize(1280, 780)
        self.setMinimumSize(1020, 640)

        # ---- Vistas ----
        self.vista_monitoreo = VistaMonitoreo()
        self.vista_historial = VistaHistorial()
        self.vista_ajustes = VistaAjustes()

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
        self._aplicar_tema(self.vista_ajustes.valores()["tema"])
        self.vista_historial.set_datos(generar_infracciones())  # TODO fase 2: leer de SQLite
        self._ir_a(0)
        self.statusBar().showMessage("Listo · fase 1: interfaz sin lógica de visión", 6000)

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
        # Fase 2: aquí se conectará el hilo de video y la base de datos real.
        self.vista_monitoreo.iniciar_solicitado.connect(self._iniciar_demo)
        self.vista_monitoreo.detener_solicitado.connect(self._detener_demo)
        self.vista_ajustes.ajustes_guardados.connect(self._al_guardar_ajustes)
        for vista in (self.vista_historial, self.vista_ajustes):
            vista.mensaje.connect(lambda t: self.statusBar().showMessage(t, 6000))
        self.vista_historial.refrescar_solicitado.connect(
            lambda: self.vista_historial.set_datos(generar_infracciones()))

    # ------------------------- Navegación y tema -------------------------
    def _ir_a(self, indice: int) -> None:
        self.paginas.setCurrentIndex(indice)
        self.lbl_titulo.setText(self._paginas[indice][1])
        self.grupo_nav.button(indice).setChecked(True)

    def _aplicar_tema(self, tema: str) -> None:
        QApplication.instance().setStyleSheet(generar_qss(tema))

    def _al_guardar_ajustes(self, valores: dict) -> None:
        self._aplicar_tema(valores["tema"])
        # TODO fase 2: reconfigurar detector/cámara/alarma con 'valores'

    def _actualizar_reloj(self) -> None:
        self.lbl_reloj.setText(datetime.now().strftime("%d/%m/%Y  %H:%M:%S"))

    # ------------------------- Demo (se reemplaza en la fase 2) -------------------------
    def _iniciar_demo(self) -> None:
        m = self.vista_monitoreo
        m.establecer_ejecucion(True)
        m.mostrar_frame(pixmap_prueba("VISTA PREVIA", color="#2ecc71").toImage())
        m.actualizar_estado({"camara": True, "personas": 2, "cumplen": 2, "incumplen": 0,
                             "fps": 14.8, "infraccion": False, "alarma": "APAGADA"})
        m.agregar_evento("Monitoreo iniciado (demo)", VERDE)
        self.insignia_sistema.set_estado("●  ACTIVO", VERDE)

    def _detener_demo(self) -> None:
        m = self.vista_monitoreo
        m.establecer_ejecucion(False)
        m.agregar_evento("Monitoreo detenido", AZUL)
        self.insignia_sistema.set_estado("●  DETENIDO", GRIS)
