"""componentes.py - Widgets reutilizables."""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QImage, QPixmap
from PyQt6.QtWidgets import QFrame, QLabel, QPushButton, QSizePolicy, QVBoxLayout

from safesite.config import GRIS


def con_alfa(color_hex: str, alfa: int = 40) -> str:
    c = QColor(color_hex)
    return f"rgba({c.red()}, {c.green()}, {c.blue()}, {alfa})"


def refrescar_estilo(widget) -> None:
    """Reaplica el QSS tras cambiar objectName en tiempo de ejecución."""
    widget.style().unpolish(widget)
    widget.style().polish(widget)


class BotonNav(QPushButton):
    """Botón de la barra lateral (checkable)."""

    def __init__(self, texto: str):
        super().__init__(texto)
        self.setObjectName("nav")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class TarjetaEstado(QFrame):
    """Tarjeta con título pequeño y valor grande de color."""

    def __init__(self, titulo: str, valor: str = "—", color: str = GRIS):
        super().__init__()
        self.setObjectName("tarjeta")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(2)
        self._titulo = QLabel(titulo)
        self._titulo.setObjectName("tarjeta_titulo")
        self._valor = QLabel()
        self._valor.setObjectName("tarjeta_valor")
        lay.addWidget(self._titulo)
        lay.addWidget(self._valor)
        self.set_valor(valor, color)

    def set_valor(self, texto: str, color: str | None = None) -> None:
        self._valor.setText(texto)
        if color:
            self._valor.setStyleSheet(f"color: {color};")


class Insignia(QLabel):
    """Etiqueta tipo 'pill' con color translúcido."""

    def __init__(self, texto: str = "", color: str = GRIS):
        super().__init__()
        self.set_estado(texto, color)

    def set_estado(self, texto: str, color: str) -> None:
        self.setText(texto)
        self.setStyleSheet(
            f"color: {color}; background: {con_alfa(color)}; border: 1px solid {color};"
            "border-radius: 12px; padding: 4px 12px; font-weight: 600;"
        )


class BannerEstado(QLabel):
    """Banner grande de estado con fondo sólido."""

    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def set_estado(self, texto: str, color: str) -> None:
        self.setText(texto)
        self.setStyleSheet(
            f"background: {color}; color: white; font-size: 18px; font-weight: 700;"
            "border-radius: 10px; padding: 16px;"
        )


class VisorVideo(QLabel):
    """Área de video: muestra un placeholder o los frames que reciba."""

    def __init__(self, texto: str = "SIN SEÑAL\nCámara detenida"):
        super().__init__(texto)
        self._texto = texto
        self._pix: QPixmap | None = None
        self.setObjectName("video")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(480, 360)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def mostrar_frame(self, imagen: QImage) -> None:
        self._pix = QPixmap.fromImage(imagen)
        self._reescalar()

    def limpiar(self) -> None:
        self._pix = None
        self.setPixmap(QPixmap())
        self.setText(self._texto)

    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        self._reescalar()

    def _reescalar(self) -> None:
        if self._pix is None:
            return
        self.setPixmap(self._pix.scaled(
            self.size(), Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation))
