"""alarma.py - Alarma sonora continua con pygame (sirena generada por código)."""
import math
from array import array


class Alarma:
    """Sirena de dos tonos. Si pygame no está disponible, funciona en silencio."""

    def __init__(self, volumen: int = 70):
        self.disponible = False
        self.sonando = False
        self._sonido = None
        self._pygame = None
        try:
            import pygame

            pygame.mixer.init(frequency=44100, size=-16, channels=1)
            sr = 44100
            muestras = array("h")
            for i in range(sr):  # 1 segundo, se reproduce en bucle
                t = i / sr
                freq = 880 if int(t * 4) % 2 == 0 else 660
                muestras.append(int(12000 * math.sin(2 * math.pi * freq * t)))
            self._sonido = pygame.mixer.Sound(buffer=muestras.tobytes())
            self._pygame = pygame
            self.disponible = True
            self.set_volumen(volumen)
        except Exception as exc:  # noqa: BLE001 - sin audio no debe romper el monitoreo
            print(f"[AVISO] Alarma sonora no disponible: {exc}")

    def set_volumen(self, porcentaje: int) -> None:
        if self._sonido is not None:
            self._sonido.set_volume(max(0, min(100, porcentaje)) / 100)

    def iniciar(self) -> None:
        if self.disponible and not self.sonando:
            self._sonido.play(loops=-1)
            self.sonando = True

    def detener(self) -> None:
        if self.disponible and self.sonando:
            self._sonido.stop()
            self.sonando = False

    def cerrar(self) -> None:
        self.detener()
        if self.disponible:
            self._pygame.mixer.quit()
            self.disponible = False
