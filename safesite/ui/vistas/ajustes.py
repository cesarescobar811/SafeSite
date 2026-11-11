"""ajustes.py - Vista de ajustes del sistema (persisten con QSettings)."""
from PyQt6.QtCore import QSettings, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QScrollArea, QSlider, QSpinBox, QVBoxLayout, QWidget,
)

from safesite.config import AJUSTES_POR_DEFECTO, NOMBRE_APP


class VistaAjustes(QWidget):
    """
    Contrato para la fase 2:
      Señal ajustes_guardados(dict) con las mismas claves de AJUSTES_POR_DEFECTO.
      valores() devuelve el estado actual de los controles.
    """

    ajustes_guardados = pyqtSignal(dict)
    mensaje = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._settings = QSettings(NOMBRE_APP, NOMBRE_APP)

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(24, 20, 24, 20)
        raiz.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.viewport().setAutoFillBackground(False)
        contenido = QWidget()
        col = QVBoxLayout(contenido)
        col.setContentsMargins(0, 0, 12, 0)
        col.setSpacing(8)

        # ---- Cámara ----
        g, f = self._grupo("Cámara")
        self.spn_camara = QSpinBox()
        self.spn_camara.setRange(0, 10)
        self.cmb_resolucion = QComboBox()
        self.cmb_resolucion.addItems(["640x480", "800x600", "1280x720"])
        f.addRow("Índice de cámara", self.spn_camara)
        f.addRow("Resolución", self.cmb_resolucion)
        col.addWidget(g)

        # ---- Detección ----
        g, f = self._grupo("Detección (rendimiento en CPU)")
        self.cmb_modelo = QComboBox()
        self.cmb_modelo.setEditable(True)
        self.cmb_modelo.addItems(["yolov8n.pt", "models/epp.pt"])
        self.cmb_imgsz = QComboBox()
        self.cmb_imgsz.addItems(["320", "416", "640"])
        self.sld_confianza, _, fila_conf = self._fila_slider(10, 90, "%")
        self.spn_salto = QSpinBox()
        self.spn_salto.setRange(1, 10)
        f.addRow("Modelo", self.cmb_modelo)
        f.addRow("Tamaño de imagen (imgsz)", self.cmb_imgsz)
        f.addRow("Confianza mínima", fila_conf)
        f.addRow("Procesar 1 de cada N fotogramas", self.spn_salto)
        col.addWidget(g)

        # ---- Alarma ----
        g, f = self._grupo("Alarma")
        self.chk_alarma = QCheckBox("Activar alarma sonora")
        self.sld_volumen, _, fila_vol = self._fila_slider(0, 100, "%")
        f.addRow(self.chk_alarma)
        f.addRow("Volumen", fila_vol)
        col.addWidget(g)

        # ---- Almacenamiento ----
        g, f = self._grupo("Almacenamiento")
        self.txt_carpeta = QLineEdit()
        btn_examinar = QPushButton("Examinar…")
        btn_examinar.clicked.connect(self._elegir_carpeta)
        fila = QWidget()
        h = QHBoxLayout(fila)
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(self.txt_carpeta, 1)
        h.addWidget(btn_examinar)
        f.addRow("Carpeta de capturas", fila)
        col.addWidget(g)

        # ---- Apariencia ----
        g, f = self._grupo("Apariencia")
        self.cmb_tema = QComboBox()
        self.cmb_tema.addItems(["Oscuro", "Claro"])
        f.addRow("Tema", self.cmb_tema)
        col.addWidget(g)

        col.addStretch()
        scroll.setWidget(contenido)
        contenido.setAutoFillBackground(False)  # QScrollArea lo activa al asignar el widget
        raiz.addWidget(scroll, 1)

        # ---- Botones ----
        botones = QHBoxLayout()
        botones.addStretch()
        btn_restaurar = QPushButton("Restaurar valores")
        btn_restaurar.clicked.connect(self.restaurar)
        btn_guardar = QPushButton("Guardar ajustes")
        btn_guardar.setObjectName("primario")
        btn_guardar.clicked.connect(self.guardar)
        botones.addWidget(btn_restaurar)
        botones.addWidget(btn_guardar)
        raiz.addLayout(botones)

        self.cargar_desde_disco()

    # ------------------------- API pública -------------------------
    def valores(self) -> dict:
        return {
            "camara_indice": self.spn_camara.value(),
            "resolucion": self.cmb_resolucion.currentText(),
            "modelo": self.cmb_modelo.currentText().strip(),
            "imgsz": self.cmb_imgsz.currentText(),
            "confianza": self.sld_confianza.value(),
            "salto_frames": self.spn_salto.value(),
            "alarma_activa": self.chk_alarma.isChecked(),
            "volumen": self.sld_volumen.value(),
            "carpeta_capturas": self.txt_carpeta.text().strip(),
            "tema": self.cmb_tema.currentText(),
        }

    def aplicar(self, v: dict) -> None:
        self.spn_camara.setValue(v["camara_indice"])
        self.cmb_resolucion.setCurrentText(v["resolucion"])
        self.cmb_modelo.setCurrentText(v["modelo"])
        self.cmb_imgsz.setCurrentText(v["imgsz"])
        self.sld_confianza.setValue(v["confianza"])
        self.spn_salto.setValue(v["salto_frames"])
        self.chk_alarma.setChecked(v["alarma_activa"])
        self.sld_volumen.setValue(v["volumen"])
        self.txt_carpeta.setText(v["carpeta_capturas"])
        self.cmb_tema.setCurrentText(v["tema"])

    def cargar_desde_disco(self) -> dict:
        vals = {
            clave: self._settings.value(clave, defecto, type=type(defecto))
            for clave, defecto in AJUSTES_POR_DEFECTO.items()
        }
        self.aplicar(vals)
        return vals

    def guardar(self) -> None:
        vals = self.valores()
        for clave, valor in vals.items():
            self._settings.setValue(clave, valor)
        self._settings.sync()
        self.ajustes_guardados.emit(vals)
        self.mensaje.emit("Ajustes guardados")

    def restaurar(self) -> None:
        self.aplicar(AJUSTES_POR_DEFECTO)
        self.mensaje.emit(
            "Valores por defecto cargados (pulsa «Guardar ajustes» para aplicarlos)")

    # ------------------------- Internos -------------------------
    @staticmethod
    def _grupo(titulo: str) -> tuple[QGroupBox, QFormLayout]:
        g = QGroupBox(titulo)
        f = QFormLayout(g)
        f.setHorizontalSpacing(20)
        f.setVerticalSpacing(12)
        f.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        return g, f

    @staticmethod
    def _fila_slider(minimo: int, maximo: int, sufijo: str = ""):
        s = QSlider(Qt.Orientation.Horizontal)
        s.setRange(minimo, maximo)
        lbl = QLabel()
        lbl.setMinimumWidth(48)
        lbl.setText(f"{s.value()}{sufijo}")
        s.valueChanged.connect(lambda v: lbl.setText(f"{v}{sufijo}"))
        cont = QWidget()
        h = QHBoxLayout(cont)
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(s, 1)
        h.addWidget(lbl)
        return s, lbl, cont

    def _elegir_carpeta(self) -> None:
        carpeta = QFileDialog.getExistingDirectory(
            self, "Carpeta de capturas", self.txt_carpeta.text())
        if carpeta:
            self.txt_carpeta.setText(carpeta)
