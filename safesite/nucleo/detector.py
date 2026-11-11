"""detector.py - Detección de personas y verificación de EPP (casco y chaleco).

Dos modos, elegidos automáticamente según las clases del modelo cargado:
  * Reglas por color: modelo COCO (yolov8n.pt) detecta personas y el color de la
    zona de la cabeza y del torso indica si hay casco y chaleco.
  * Modelo EPP: si el modelo trae clases de casco y chaleco (p. ej. un
    modelo entrenado con un dataset de EPP), se usan directamente.
"""
import os

import cv2
import numpy as np

from safesite import config

# --- Reglas por color (HSV) ---
UMBRAL_CASCO = 0.30     # fracción de píxeles "color casco" en la zona de la cabeza
UMBRAL_CHALECO = 0.15   # fracción de píxeles "color alta visibilidad" en el torso

RANGOS_CASCO = [  # amarillo, naranja, rojo, azul, blanco
    ((20, 100, 100), (35, 255, 255)),
    ((5, 120, 120), (20, 255, 255)),
    ((0, 120, 100), (5, 255, 255)),
    ((170, 120, 100), (180, 255, 255)),
    ((100, 120, 60), (130, 255, 255)),
    ((0, 0, 200), (180, 40, 255)),
]
RANGOS_CHALECO = [  # amarillo-verde fluorescente y naranja
    ((25, 100, 100), (50, 255, 255)),
    ((5, 150, 120), (25, 255, 255)),
]

# --- Nombres de clases para el modo con modelo EPP (en minúsculas) ---
CLASES_PERSONA = {"person", "worker"}
CLASES_CASCO = {"hardhat", "helmet", "hard-hat", "hard hat"}
CLASES_CHALECO = {"safety vest", "safety-vest", "vest"}


def proporcion_color(roi: np.ndarray, rangos) -> float:
    """Fracción de píxeles de la ROI que caen dentro de los rangos HSV."""
    if roi.size == 0:
        return 0.0
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    mascara = np.zeros(hsv.shape[:2], dtype=np.uint8)
    for bajo, alto in rangos:
        mascara |= cv2.inRange(hsv, np.array(bajo), np.array(alto))
    return cv2.countNonZero(mascara) / mascara.size


def faltas_por_color(frame: np.ndarray, bbox: tuple[int, int, int, int]) -> list[str]:
    """Evalúa una persona (caja x1,y1,x2,y2) y devuelve la lista de EPP faltante."""
    x1, y1, x2, y2 = bbox
    h_img, w_img = frame.shape[:2]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w_img, x2), min(h_img, y2)
    w, h = x2 - x1, y2 - y1

    cabeza = frame[y1:y1 + int(h * 0.20), x1 + int(w * 0.25):x1 + int(w * 0.75)]
    torso = frame[y1 + int(h * 0.25):y1 + int(h * 0.60),
                  x1 + int(w * 0.20):x1 + int(w * 0.80)]

    faltas = []
    if proporcion_color(cabeza, RANGOS_CASCO) < UMBRAL_CASCO:
        faltas.append("Sin casco")
    if proporcion_color(torso, RANGOS_CHALECO) < UMBRAL_CHALECO:
        faltas.append("Sin chaleco")
    return faltas


def centro_dentro(caja_interna, caja_externa) -> bool:
    x1, y1, x2, y2 = caja_interna
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    ex1, ey1, ex2, ey2 = caja_externa
    return ex1 <= cx <= ex2 and ey1 <= cy <= ey2


class DetectorEPP:
    """Detecta personas y determina qué EPP les falta.

    analizar(frame) devuelve [{"bbox": (x1,y1,x2,y2), "faltas": [str, ...]}, ...]
    """

    def __init__(self, ruta_modelo: str = "yolov8n.pt", imgsz: int = 320,
                 confianza: float = 0.40):
        from ultralytics import YOLO  # import diferido: es la dependencia más pesada

        self.imgsz = imgsz
        self.confianza = confianza
        if not os.path.isabs(ruta_modelo):
            local = os.path.join(config.RAIZ_PROYECTO, ruta_modelo)
            ruta_modelo = local if os.path.exists(local) else ruta_modelo
        self.ruta_modelo = ruta_modelo
        self.modelo = YOLO(ruta_modelo)

        nombres = {str(n).lower() for n in self.modelo.names.values()}
        self.modo_modelo = bool(nombres & (CLASES_CASCO | CLASES_CHALECO))

        # Calentamiento: la primera inferencia es lenta
        self.modelo.predict(np.zeros((480, 640, 3), np.uint8), imgsz=self.imgsz,
                            device="cpu", verbose=False)

    @property
    def nombre_modo(self) -> str:
        return "Modelo EPP" if self.modo_modelo else "Reglas por color"

    def analizar(self, frame: np.ndarray) -> list[dict]:
        if self.modo_modelo:
            return self._analizar_con_modelo(frame)
        return self._analizar_con_reglas(frame)

    def _analizar_con_reglas(self, frame):
        res = self.modelo.predict(frame, imgsz=self.imgsz, conf=self.confianza,
                                  classes=[0], device="cpu", verbose=False)[0]
        personas = []
        for b in res.boxes:
            x1, y1, x2, y2 = (int(v) for v in b.xyxy[0].tolist())
            if (x2 - x1) < 20 or (y2 - y1) < 40:
                continue
            personas.append({"bbox": (x1, y1, x2, y2),
                             "faltas": faltas_por_color(frame, (x1, y1, x2, y2))})
        return personas

    def _analizar_con_modelo(self, frame):
        res = self.modelo.predict(frame, imgsz=self.imgsz, conf=self.confianza,
                                  device="cpu", verbose=False)[0]
        personas, cascos, chalecos = [], [], []
        for b in res.boxes:
            nombre = str(res.names[int(b.cls[0])]).lower()
            if nombre.startswith(("no-", "no_", "no ")):
                continue  # clases negativas (p. ej. NO-Hardhat) se ignoran
            caja = tuple(int(v) for v in b.xyxy[0].tolist())
            if nombre in CLASES_PERSONA:
                personas.append(caja)
            elif nombre in CLASES_CASCO:
                cascos.append(caja)
            elif nombre in CLASES_CHALECO:
                chalecos.append(caja)

        resultado = []
        for p in personas:
            x1, y1, x2, y2 = p
            mitad_superior = (x1, y1, x2, y1 + (y2 - y1) // 2)
            faltas = []
            if not any(centro_dentro(c, mitad_superior) for c in cascos):
                faltas.append("Sin casco")
            if not any(centro_dentro(v, p) for v in chalecos):
                faltas.append("Sin chaleco")
            resultado.append({"bbox": p, "faltas": faltas})
        return resultado
