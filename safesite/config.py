"""config.py - Constantes globales de SafeSite."""
import os

NOMBRE_APP = "SafeSite"
SUBTITULO = "Monitoreo de EPP"
VERSION = "v0.2.0 · prototipo"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # .../SafeSite/safesite
RAIZ_PROYECTO = os.path.dirname(BASE_DIR)                # .../SafeSite
CARPETA_CAPTURAS = os.path.join(RAIZ_PROYECTO, "capturas")
DB_PATH = os.path.join(RAIZ_PROYECTO, "infracciones.db")

# Colores de estado (iguales en tema claro y oscuro)
VERDE = "#2ecc71"
ROJO = "#e74c3c"
AMARILLO = "#f1c40f"
AZUL = "#3d7eff"
GRIS = "#7f8c8d"

# Reglas del monitoreo
CONFIRMACION = 2          # detecciones consecutivas con falta para confirmar la infracción
COOLDOWN_REGISTRO = 5     # segundos mínimos entre registros (evita saturar la BD)

# Valores por defecto de la pantalla de Ajustes.
# El tipo de cada valor se usa para leerlo correctamente desde QSettings.
AJUSTES_POR_DEFECTO = {
    "camara_indice": 0,
    "resolucion": "640x480",
    "modelo": "yolov8n.pt",
    "imgsz": "320",
    "confianza": 40,          # porcentaje
    "salto_frames": 3,
    "alarma_activa": True,
    "volumen": 70,            # porcentaje
    "carpeta_capturas": CARPETA_CAPTURAS,
    "tema": "Oscuro",
}
