"""historial.py - Vista de historial de infracciones (datos de prueba)."""
import csv
import os

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QAbstractItemView, QComboBox, QFileDialog, QFrame, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget,
)

from safesite.datos.datos_prueba import TIPOS_FALTA, pixmap_prueba


class VistaHistorial(QWidget):
    """
    Contrato para la fase 2:
      set_datos(list[dict])  con claves: id, fecha, tipo, ruta (ruta puede ser None)
      Señales: refrescar_solicitado (pedir datos a la BD), mensaje(str)
    """

    refrescar_solicitado = pyqtSignal()
    mensaje = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._datos: list[dict] = []
        self._visibles: list[dict] = []

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(24, 20, 24, 20)
        raiz.setSpacing(14)

        # ---- Barra de filtros ----
        barra = QHBoxLayout()
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar por ID o fecha…")
        self.txt_buscar.setMinimumWidth(240)
        self.txt_buscar.textChanged.connect(self._aplicar_filtro)
        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItem("Todos los tipos")
        self.cmb_tipo.addItems(TIPOS_FALTA)
        self.cmb_tipo.currentIndexChanged.connect(self._aplicar_filtro)
        self.lbl_total = QLabel()
        btn_refrescar = QPushButton("⟳  Refrescar")
        btn_refrescar.clicked.connect(self.refrescar_solicitado)
        btn_exportar = QPushButton("⭳  Exportar CSV")
        btn_exportar.clicked.connect(self._exportar_csv)
        barra.addWidget(self.txt_buscar)
        barra.addWidget(self.cmb_tipo)
        barra.addStretch()
        barra.addWidget(self.lbl_total)
        barra.addWidget(btn_refrescar)
        barra.addWidget(btn_exportar)
        raiz.addLayout(barra)

        # ---- Cuerpo: tabla + vista previa ----
        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(16)

        self.tabla = QTableWidget(0, 4)
        self.tabla.setHorizontalHeaderLabels(["ID", "Fecha y hora", "Tipo de falta", "Foto"])
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setShowGrid(False)
        self.tabla.setIconSize(QSize(96, 72))
        self.tabla.verticalHeader().setVisible(False)
        cab = self.tabla.horizontalHeader()
        cab.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        cab.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        cab.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        cab.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.tabla.setColumnWidth(3, 120)
        self.tabla.currentCellChanged.connect(self._mostrar_preview)
        cuerpo.addWidget(self.tabla, 3)

        panel = QFrame()
        panel.setObjectName("tarjeta")
        panel.setMinimumWidth(380)
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(16, 14, 16, 14)
        titulo = QLabel("Vista previa")
        titulo.setObjectName("seccion")
        self.lbl_preview = QLabel("Selecciona una infracción\npara ver la captura")
        self.lbl_preview.setObjectName("video")
        self.lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_preview.setMinimumSize(340, 255)
        self.lbl_caption = QLabel("")
        self.lbl_caption.setWordWrap(True)
        lay.addWidget(titulo)
        lay.addWidget(self.lbl_preview)
        lay.addWidget(self.lbl_caption)
        lay.addStretch()
        cuerpo.addWidget(panel, 2)
        raiz.addLayout(cuerpo, 1)

    # ------------------------- API pública -------------------------
    def set_datos(self, filas: list[dict]) -> None:
        self._datos = list(filas)
        self._aplicar_filtro()

    # ------------------------- Internos -------------------------
    @staticmethod
    def _pixmap_de(fila: dict) -> QPixmap:
        ruta = fila.get("ruta")
        if ruta and os.path.exists(ruta):
            pix = QPixmap(ruta)
            if not pix.isNull():
                return pix
        return pixmap_prueba(fila["tipo"])

    def _aplicar_filtro(self) -> None:
        texto = self.txt_buscar.text().strip().lower()
        tipo = self.cmb_tipo.currentText()
        self._visibles = [
            f for f in self._datos
            if (self.cmb_tipo.currentIndex() == 0 or f["tipo"] == tipo)
            and (not texto or texto in str(f["id"]) or texto in f["fecha"].lower())
        ]
        self._poblar()

    def _poblar(self) -> None:
        self.tabla.setRowCount(0)
        self.tabla.setRowCount(len(self._visibles))
        for r, fila in enumerate(self._visibles):
            self.tabla.setItem(r, 0, QTableWidgetItem(str(fila["id"])))
            self.tabla.setItem(r, 1, QTableWidgetItem(fila["fecha"]))
            self.tabla.setItem(r, 2, QTableWidgetItem(fila["tipo"]))
            foto = QTableWidgetItem()
            foto.setIcon(QIcon(self._pixmap_de(fila).scaled(
                96, 72, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation)))
            self.tabla.setItem(r, 3, foto)
            self.tabla.setRowHeight(r, 80)
        self.lbl_total.setText(f"{len(self._visibles)} de {len(self._datos)} infracciones")
        self.lbl_preview.setPixmap(QPixmap())
        self.lbl_preview.setText("Selecciona una infracción\npara ver la captura")
        self.lbl_caption.setText("")

    def _mostrar_preview(self, fila: int, _c: int, _fa: int, _ca: int) -> None:
        if fila < 0 or fila >= len(self._visibles):
            return
        datos = self._visibles[fila]
        pix = self._pixmap_de(datos)
        self.lbl_preview.setPixmap(pix.scaled(
            self.lbl_preview.size(), Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation))
        self.lbl_caption.setText(
            f"Infracción #{datos['id']}\n{datos['fecha']}\n{datos['tipo']}")

    def _exportar_csv(self) -> None:
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Exportar historial", "infracciones.csv", "CSV (*.csv)")
        if not ruta:
            return
        with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["id", "fecha_hora", "tipo_falta", "ruta_captura"])
            for fila in self._visibles:
                w.writerow([fila["id"], fila["fecha"], fila["tipo"], fila.get("ruta") or ""])
        self.mensaje.emit(f"Exportadas {len(self._visibles)} filas a {ruta}")
