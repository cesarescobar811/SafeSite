"""datos_prueba.py - Datos e imágenes de prueba (se reemplazan en la fase 2)."""
import random
from datetime import datetime, timedelta
from functools import lru_cache

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QPixmap

TIPOS_FALTA = ["Sin casco", "Sin chaleco", "Sin casco, Sin chaleco"]


def generar_infracciones(n: int = 25) -> list[dict]:
    """Infracciones falsas, de la más reciente a la más antigua.

    Cada fila: {"id", "fecha", "tipo", "ruta"}; ruta=None usa una imagen de prueba.
    """
    rng = random.Random(7)
    t = datetime.now()
    filas = []
    for i in range(n):
        t -= timedelta(minutes=rng.randint(4, 90))
        filas.append({
            "id": n - i,
            "fecha": t.strftime("%Y-%m-%d %H:%M:%S"),
            "tipo": rng.choice(TIPOS_FALTA),
            "ruta": None,
        })
    return filas


@lru_cache(maxsize=64)
def pixmap_prueba(texto: str, ancho: int = 640, alto: int = 480,
                  color: str = "#e74c3c") -> QPixmap:
    """Dibuja una 'captura' de prueba con un recuadro de alerta."""
    pix = QPixmap(ancho, alto)
    pix.fill(QColor("#2b2f3a"))
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    p.setPen(QPen(QColor("#343949"), 1))
    for x in range(0, ancho, 40):
        p.drawLine(x, 0, x, alto)
    for y in range(0, alto, 40):
        p.drawLine(0, y, ancho, y)

    p.setPen(QPen(QColor(color), max(2, ancho // 160)))
    p.drawRect(int(ancho * 0.32), int(alto * 0.15), int(ancho * 0.36), int(alto * 0.75))

    fuente = QFont()
    fuente.setBold(True)
    fuente.setPixelSize(max(10, ancho // 24))
    p.setFont(fuente)
    p.setPen(QColor("#ffffff"))
    p.drawText(pix.rect().adjusted(0, 0, 0, -int(alto * 0.1)),
               Qt.AlignmentFlag.AlignCenter, "IMAGEN DE PRUEBA")

    fuente.setPixelSize(max(9, ancho // 34))
    p.setFont(fuente)
    p.setPen(QColor(color))
    p.drawText(pix.rect().adjusted(0, int(alto * 0.1), 0, 0),
               Qt.AlignmentFlag.AlignCenter, texto)
    p.end()
    return pix
