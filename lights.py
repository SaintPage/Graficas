import numpy as np

_EPS = 1e-8

class Light:
    def __init__(self, color=(1, 1, 1), intensity=1.0, kind="generic"):
        self.color = np.array(color, dtype=float)
        self.intensity = float(intensity)
        self.kind = kind

    def get_light_color(self) -> np.ndarray:
        """Color * intensidad (en [0..1])."""
        return self.color * self.intensity

    # Interfaz unificada para el motor:
    #  - devuelve (ldir, dist, Lcol)
    #  - ldir: dirección NORMALIZADA desde el punto hacia la luz
    #  - dist: distancia hasta la luz; np.inf para direccional
    #  - Lcol: color de la luz (ya con intensidad/atenuación aplicadas)
    def sample(self, point: np.ndarray):
        raise NotImplementedError


class DirectionalLight(Light):
    def __init__(self, direction=(0, -1, 0), color=(1, 1, 1), intensity=1.0):
        super().__init__(color=color, intensity=intensity, kind="dir")
        d = np.array(direction, dtype=float)
        n = np.linalg.norm(d)
        self.dir = d / (n if n > _EPS else 1.0)  # dirección *desde la luz hacia la escena*

    def sample(self, point):
        ldir = -self.dir               # hacia la luz
        dist = np.inf                  # luz “en el infinito”
        Lcol = self.get_light_color()  # sin atenuación por distancia
        return ldir, dist, Lcol


class PointLight(Light):
    def __init__(self, position, color=(1, 1, 1), intensity=1.0, att_a=0.04, att_b=0.01):
        super().__init__(color=color, intensity=intensity, kind="point")
        self.pos  = np.array(position, dtype=float)
        self.att_a = float(att_a)     # 1 / (1 + a*r + b*r^2)
        self.att_b = float(att_b)

    def sample(self, point):
        toL  = self.pos - point
        dist = float(np.linalg.norm(toL))
        ldir = toL / (dist if dist > _EPS else 1.0)
        att  = 1.0 / (1.0 + self.att_a * dist + self.att_b * dist * dist)
        Lcol = self.get_light_color() * att
        return ldir, dist, Lcol
