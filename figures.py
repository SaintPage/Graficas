import numpy as np
from intercept import Intercept

def _norm(v): 
    v = np.array(v, dtype=float); n = np.linalg.norm(v); 
    return v if n == 0 else v / n

# ---------------- Sphere ----------------
class Sphere:
    def __init__(self, position, radius, material):
        self.center = np.array(position, dtype=float)
        self.radius = float(radius)
        self.material = material

    def ray_intersect(self, orig, dir):
        L = self.center - orig
        tca = np.dot(L, dir)
        d2 = np.dot(L, L) - tca*tca
        r2 = self.radius * self.radius
        if d2 > r2:
            return None
        thc = np.sqrt(r2 - d2)
        t0 = tca - thc
        t1 = tca + thc
        t = t0 if t0 > 1e-4 else t1
        if t <= 1e-4:
            return None
        P = orig + dir * t
        N = _norm(P - self.center)
        return Intercept(P, N, t, dir, self)

# ---------------- Plane ----------------
class Plane:
    def __init__(self, position, normal, material):
        self.P0 = np.array(position, dtype=float)  # punto del plano
        self.N  = _norm(normal)                    # ¡normal unit!

        self.material = material

    def ray_intersect(self, orig, dir):
        den = np.dot(dir, self.N)
        if abs(den) < 1e-6:
            return None
        t = np.dot(self.P0 - orig, self.N) / den
        if t <= 1e-4:
            return None
        P = orig + dir * t
        return Intercept(P, self.N, t, dir, self)

# ---------------- Disk (plano + radio) ----------------
class Disk(Plane):
    def __init__(self, position, normal, radius, material):
        super().__init__(position, normal, material)
        self.center = np.array(position, dtype=float)
        self.radius = float(radius)

    def ray_intersect(self, orig, dir):
        hit = super().ray_intersect(orig, dir)
        if hit is None:
            return None
        if np.linalg.norm(hit.point - self.center) <= self.radius + 1e-6:
            return hit
        return None

# ---------------- Triangle ----------------
class Triangle:
    def __init__(self, A, B, C, material):
        self.A = np.array(A, dtype=float)
        self.B = np.array(B, dtype=float)
        self.C = np.array(C, dtype=float)
        self.material = material
        self.N = _norm(np.cross(self.B - self.A, self.C - self.A))

    def ray_intersect(self, orig, dir):
        # Plano
        den = np.dot(dir, self.N)
        if abs(den) < 1e-6:
            return None
        t = np.dot(self.A - orig, self.N) / den
        if t <= 1e-4:
            return None
        P = orig + dir * t

        # Test dentro del triángulo (método de aristas)
        def edge(p0, p1):
            return np.cross(p1 - p0, P - p0)
        if (np.dot(self.N, edge(self.A, self.B)) >= -1e-6 and
            np.dot(self.N, edge(self.B, self.C)) >= -1e-6 and
            np.dot(self.N, edge(self.C, self.A)) >= -1e-6):
            return Intercept(P, self.N, t, dir, self)
        return None

# ---------------- AABB (cubo alineado a ejes) ----------------
class AABB:
    def __init__(self, position, sizes, material):
        self.center = np.array(position, dtype=float)
        self.half   = np.array(sizes, dtype=float) * 0.5
        self.material = material

    def ray_intersect(self, orig, dir):
        # slab method (robust normals for near/far faces)
        tmin = -np.inf
        tmax = np.inf
        normal_min = None
        normal_max = None

        for axis in range(3):
            min_plane = self.center[axis] - self.half[axis]
            max_plane = self.center[axis] + self.half[axis]

            if abs(dir[axis]) < 1e-8:
                # rayo paralelo: fuera de los límites → no intersecta
                if orig[axis] < min_plane or orig[axis] > max_plane:
                    return None
                # si está dentro en este eje, no actualizamos t's
                continue

            invD = 1.0 / dir[axis]
            t0 = (min_plane - orig[axis]) * invD
            t1 = (max_plane - orig[axis]) * invD

            # normales para los planos (orientadas hacia fuera)
            if invD >= 0:
                n0 = np.zeros(3); n0[axis] = -1
                n1 = np.zeros(3); n1[axis] = 1
            else:
                n0 = np.zeros(3); n0[axis] = 1
                n1 = np.zeros(3); n1[axis] = -1

            # asegurar t0 <= t1 y correspondencia de normales
            if t0 > t1:
                t0, t1 = t1, t0
                n0, n1 = n1, n0

            if t0 > tmin:
                tmin = t0
                normal_min = n0

            if t1 < tmax:
                tmax = t1
                normal_max = n1

            if tmin > tmax:
                return None

        # seleccionar la intersección válida (si estamos dentro del cubo, tmin puede ser negativo)
        t = tmin if tmin > 1e-4 else tmax
        if t <= 1e-4:
            return None

        P = orig + dir * t
        # elegir normal correspondiente al t elegido
        normal = normal_min if t == tmin else normal_max
        return Intercept(P, normal, t, dir, self)
