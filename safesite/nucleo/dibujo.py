"""dibujo.py - Anotaciones sobre el fotograma (recuadros verde/rojo y textos)."""
import cv2
import numpy as np

VERDE = (0, 200, 0)    # BGR
ROJO = (0, 0, 255)
BLANCO = (255, 255, 255)


def texto_con_fondo(img, texto, origen, color_fondo, escala=0.55):
    (tw, th), base = cv2.getTextSize(texto, cv2.FONT_HERSHEY_SIMPLEX, escala, 2)
    x, y = origen
    y = max(y, th + base + 2)
    cv2.rectangle(img, (x, y - th - base - 2), (x + tw + 4, y + 2), color_fondo, -1)
    cv2.putText(img, texto, (x + 2, y - base // 2), cv2.FONT_HERSHEY_SIMPLEX,
                escala, BLANCO, 2, cv2.LINE_AA)


def dibujar(frame: np.ndarray, personas: list[dict], infraccion_confirmada: bool,
            fps: float) -> np.ndarray:
    """Devuelve una copia del fotograma con las detecciones dibujadas.

    Rojo con "ALERTA: FALTA EPP" cuando la infracción está confirmada;
    verde con "EPP COMPLETO" en caso contrario.
    """
    salida = frame.copy()
    for p in personas:
        x1, y1, x2, y2 = p["bbox"]
        if p["faltas"] and infraccion_confirmada:
            cv2.rectangle(salida, (x1, y1), (x2, y2), ROJO, 3)
            texto_con_fondo(salida, "ALERTA: FALTA EPP", (x1, y1 - 6), ROJO)
            texto_con_fondo(salida, ", ".join(p["faltas"]), (x1, y2 + 20), ROJO, 0.5)
        else:  # EPP completo (o posible falta aún sin confirmar)
            cv2.rectangle(salida, (x1, y1), (x2, y2), VERDE, 3)
            texto_con_fondo(salida, "EPP COMPLETO", (x1, y1 - 6), VERDE)

    if infraccion_confirmada:
        cv2.rectangle(salida, (0, 0), (salida.shape[1] - 1, salida.shape[0] - 1), ROJO, 6)
    cv2.putText(salida, f"FPS: {fps:.1f}", (10, salida.shape[0] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2, cv2.LINE_AA)
    return salida
