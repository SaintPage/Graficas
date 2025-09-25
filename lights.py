import numpy as np
from MathLib import normalize, clamp01, reflectVector

class Light(object):
    def __init__(self, color=(1, 1, 1), intensity=1.0, lightType="None"):
        self.color = np.array(color, dtype=float)
        self.intensity = float(intensity)
        self.lightType = lightType

    def GetLightColor(self, intercept=None):
        # luz base, sin atenuar
        return (self.color * self.intensity).tolist()

    # por defecto sin especular
    def GetSpecularColor(self, intercept, viewPos, shininess=32, ks=0.5):
        return [0.0, 0.0, 0.0]


class AmbientLight(Light):
    def __init__(self, color=(1, 1, 1), intensity=0.12):
        super().__init__(color, intensity, "Ambient")

    # ambiente no depende de la normal
    def GetLightColor(self, intercept=None):
        return super().GetLightColor()


class DirectionalLight(Light):
    def __init__(self, color=(1, 1, 1), intensity=1.0, direction=(0, -1, 0)):
        super().__init__(color, intensity, "Directional")
        self.direction = normalize(direction)  # hacia dónde APUNTA la luz

    def GetLightColor(self, intercept=None):
        base = super().GetLightColor()
        if intercept is None:
            return base

        # Vector de luz incidente en la superficie (del punto hacia la luz)
        L = -self.direction
        N = normalize(intercept.normal)
        ndotl = clamp01(np.dot(N, L))
        return (np.array(base) * ndotl).tolist()

    def GetSpecularColor(self, intercept, viewPos, shininess=64, ks=0.35):
        # V: del punto hacia la cámara
        P = np.array(intercept.point, dtype=float)
        V = normalize(np.array(viewPos, dtype=float) - P)

        # L: del punto hacia la luz
        L = -self.direction

        # R: reflexión de L alrededor de N
        R = reflectVector(intercept.normal, L)

        spec = clamp01(np.dot(V, R)) ** shininess
        return (self.color * self.intensity * ks * spec).tolist()


class PointLight(Light):
    def __init__(self, color=(1,1,1), intensity=1.0, position=(0,0,0), range=10.0, attenuation=(1.0,0.09,0.032)):
        super().__init__(color, intensity, "Point")
        self.position = np.array(position, dtype=float)
        # range is advisory; attenuation is (constant, linear, quadratic)
        self.range = float(range)
        self.attenuation = tuple(attenuation)

    def GetLightColor(self, intercept=None):
        base = super().GetLightColor()
        if intercept is None:
            return base
        # distancia y atenuación
        P = np.array(intercept.point, dtype=float)
        d = np.linalg.norm(self.position - P)
        c, l, q = self.attenuation
        att = 1.0 / max(1e-6, c + l * d + q * (d * d))
        att *= 0.0 if d > self.range else 1.0
        return (np.array(base) * att).tolist()

    def direction_from_point(self, point):
        # devuelve el vector dirigido desde el punto hacia la luz (normalizado)
        p = np.array(point, dtype=float)
        v = self.position - p
        n = np.linalg.norm(v)
        if n == 0:
            return np.array((0.0, 1.0, 0.0))
        return v / n

    def distance_to(self, point):
        return float(np.linalg.norm(self.position - np.array(point, dtype=float)))
