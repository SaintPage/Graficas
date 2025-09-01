import numpy as np
from intercept import Intercept

class Sphere(object):
    def __init__(self, center=(0,0,0), radius=1.0, material=None):
        self.center   = np.array(center, dtype=float)
        self.radius   = float(radius)
        self.material = material

    def ray_intersect(self, origin, direction):
        # Asegurar tipos correctos
        O = np.array(origin, dtype=float)
        D = np.array(direction, dtype=float)
        D /= (np.linalg.norm(D) + 1e-8)          # unitario

        L   = self.center - O
        tca = np.dot(L, D)
        d2  = np.dot(L, L) - tca*tca
        r2  = self.radius*self.radius
        if d2 > r2:
            return None

        thc = np.sqrt(max(0.0, r2 - d2))
        t0  = tca - thc
        t1  = tca + thc
        t   = t0 if t0 > 1e-4 else t1
        if t < 1e-4:
            return None

        P = O + D*t
        N = P - self.center
        N /= (np.linalg.norm(N) + 1e-8)

        return Intercept(point=P, normal=N, distance=float(t),
                         rayDirection=D, obj=self)
