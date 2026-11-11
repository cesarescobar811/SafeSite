"""estilos.py - Temas (QSS) oscuro y claro."""
from string import Template

PALETAS = {
    "Oscuro": {
        "fondo": "#14161c", "panel": "#1c1f27", "panel2": "#242834",
        "borde": "#2f3442", "texto": "#e8eaf0", "texto_suave": "#9aa3b5",
        "acento": "#3d7eff", "acento_hover": "#5a93ff", "sel": "#2a3550",
    },
    "Claro": {
        "fondo": "#f2f4f8", "panel": "#ffffff", "panel2": "#eef1f6",
        "borde": "#d5dae3", "texto": "#1d2330", "texto_suave": "#5d6779",
        "acento": "#2563eb", "acento_hover": "#1d4fd0", "sel": "#dbe6fd",
    },
}

_PLANTILLA = Template("""
* { font-family: "Segoe UI", "Inter", sans-serif; font-size: 13px; }
QMainWindow, QWidget#raiz, QWidget#paginas { background: $fondo; }
QWidget { color: $texto; }
QLabel { background: transparent; }
QToolTip { background: $panel; color: $texto; border: 1px solid $borde; padding: 4px; }

/* Sidebar */
QFrame#sidebar { background: $panel; border-right: 1px solid $borde; }
QLabel#logo { font-size: 24px; font-weight: 700; }
QLabel#subtitulo { color: $texto_suave; font-size: 12px; }
QLabel#version { color: $texto_suave; font-size: 11px; }
QPushButton#nav {
    background: transparent; border: none; border-radius: 8px;
    padding: 12px 14px; text-align: left; color: $texto_suave; font-size: 14px;
}
QPushButton#nav:hover { background: $panel2; color: $texto; }
QPushButton#nav:checked { background: $sel; color: $acento; font-weight: 600; }

/* Header */
QFrame#header { background: $panel; border-bottom: 1px solid $borde; }
QLabel#titulo_pagina { font-size: 18px; font-weight: 600; }
QLabel#reloj { color: $texto_suave; }

/* Tarjetas */
QFrame#tarjeta { background: $panel; border: 1px solid $borde; border-radius: 10px; }
QLabel#tarjeta_titulo { color: $texto_suave; font-size: 12px; }
QLabel#tarjeta_valor { font-size: 20px; font-weight: 700; }
QLabel#seccion { font-size: 14px; font-weight: 600; }
QLabel#video { background: #000000; border-radius: 10px; color: #6b7385; font-size: 16px; }

/* Botones */
QPushButton { background: $panel2; border: 1px solid $borde; border-radius: 6px; padding: 8px 16px; }
QPushButton:hover { border-color: $acento; }
QPushButton:disabled { color: $texto_suave; }
QPushButton#primario { background: $acento; border: none; color: #ffffff; font-weight: 600; }
QPushButton#primario:hover { background: $acento_hover; }
QPushButton#peligro { background: #e74c3c; border: none; color: #ffffff; font-weight: 600; }
QPushButton#peligro:hover { background: #ff6352; }

/* Campos de formulario */
QLineEdit, QComboBox, QSpinBox {
    background: $panel2; border: 1px solid $borde; border-radius: 6px; padding: 6px 10px;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border-color: $acento; }
QComboBox QAbstractItemView {
    background: $panel; border: 1px solid $borde;
    selection-background-color: $sel; selection-color: $texto;
}
QCheckBox { spacing: 8px; }
QSlider::groove:horizontal { height: 6px; background: $borde; border-radius: 3px; }
QSlider::sub-page:horizontal { background: $acento; border-radius: 3px; }
QSlider::handle:horizontal {
    background: $acento; width: 16px; height: 16px; margin: -5px 0; border-radius: 8px;
}
QGroupBox {
    background: $panel; border: 1px solid $borde; border-radius: 10px;
    margin-top: 18px; padding: 18px 12px 12px 12px; font-weight: 600;
}
QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 6px; color: $texto_suave; }

/* Tablas y listas */
QTableWidget {
    background: $panel; alternate-background-color: $panel2;
    border: 1px solid $borde; border-radius: 8px; gridline-color: transparent;
    selection-background-color: $sel; selection-color: $texto;
}
QTableWidget::item { padding: 4px; }
QHeaderView::section {
    background: $panel2; color: $texto_suave; border: none;
    border-bottom: 1px solid $borde; padding: 8px; font-weight: 600;
}
QListWidget { background: $panel; border: 1px solid $borde; border-radius: 8px; padding: 4px; }
QListWidget::item { padding: 6px; }

/* Scroll */
QScrollArea { background: transparent; border: none; }
QScrollArea > QWidget > QWidget { background: transparent; }
QScrollBar:vertical { background: transparent; width: 10px; }
QScrollBar::handle:vertical { background: $borde; border-radius: 5px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QStatusBar { background: $panel; color: $texto_suave; border-top: 1px solid $borde; }
""")


def generar_qss(tema: str) -> str:
    """Devuelve la hoja de estilos del tema indicado ('Oscuro' o 'Claro')."""
    return _PLANTILLA.substitute(PALETAS.get(tema, PALETAS["Oscuro"]))
