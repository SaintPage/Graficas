import numpy as np
from MathLib import reflectVector
from refractionFunctions import refractVector, totalInternalReflection, fresnel  # :contentReference[oaicite:1]{index=1}

# Tipos de material
OPAQUE      = "OPAQUE"
REFLECTIVE  = "REFLECTIVE"
TRANSPARENT = "TRANSPARENT"


class Material(object):
    def __init__(
        self,
        diffuse=(1, 1, 1),
        ka=0.1, kd=0.9, ks=0.35, shininess=64,
        matType=OPAQUE,
        ior=1.5,                 # índice de refracción (vidrio ~1.5)
        reflectivity=0.9         # mezcla para REFLECTIVE
    ):
        self.diffuse     = np.array(diffuse, dtype=float)
        self.ka, self.kd = float(ka), float(kd)
        self.ks          = float(ks)
        self.shininess   = float(shininess)
        self.matType     = matType
        self.ior         = float(ior)
        self.reflectivity = float(reflectivity)

    
    # Phong + Sombras + (Reflexión / Refracción / Fresnel)

    def GetSurfaceColor(self, intercept, renderer, recursion=0):
        N = intercept.normal / (np.linalg.norm(intercept.normal) + 1e-8)
        V = (-intercept.rayDirection)
        V /= (np.linalg.norm(V) + 1e-8)

        # Luz ambiente (si hay)
        ambient = np.zeros(3, dtype=float)
        for L in renderer.lights:
            if getattr(L, "lightType", "") == "Ambient":
                ambient += np.array(L.GetLightColor(), dtype=float)

        # Difusa + especular (con sombras)
        diff = np.zeros(3, dtype=float)
        spec = np.zeros(3, dtype=float)

        for L in renderer.lights:
            if getattr(L, "lightType", "") != "Directional":
                continue

            Ldir = -np.array(L.direction, dtype=float)
            Ldir /= (np.linalg.norm(Ldir) + 1e-8)

            # Sombra: lanzar rayo desde el punto hacia la luz
            biasP = intercept.point + N * 1e-3
            shadow = renderer.glCastRay(biasP, Ldir, intercept.obj)
            if shadow is not None:
                continue  # en sombra: no suma difusa/especular

            # Difusa
            ndotl = max(0.0, float(np.dot(N, Ldir)))
            diff += np.array(L.color, dtype=float) * L.intensity * ndotl

            # Especular (Phong: R·V)^shininess
            R = reflectVector(N, -Ldir)
            rdotv = max(0.0, float(np.dot(R, V)))
            spec += np.array(L.color, dtype=float) * (rdotv ** self.shininess) * L.intensity

        base = self.diffuse * (self.ka * ambient + self.kd * diff) + self.ks * spec
        base = np.clip(base, 0, 1)

        # Materiales especiales
        if self.matType == REFLECTIVE:
            if recursion >= renderer.max_depth:
                return tuple(base)

            # Reflexión
            R = reflectVector(N, V)
            ro = intercept.point + N * 1e-3
            hit = renderer.glCastRay(ro, R, intercept.obj)
            if hit is not None:
                Rcol = hit.obj.material.GetSurfaceColor(hit, renderer, recursion + 1)
            else:
                Rcol = renderer.glEnvMapColor(ro, R)

            color = (1.0 - self.reflectivity) * base + self.reflectivity * np.array(Rcol)
            return tuple(np.clip(color, 0, 1))

        if self.matType == TRANSPARENT:
            if recursion >= renderer.max_depth:
                return tuple(base)

            # ¿el rayo viene de fuera?
            outside = float(np.dot(N, intercept.rayDirection)) < 0.0
            Nuse = N if outside else -N
            bias = Nuse * 1e-3

            # Fresnel
            Kr, Kt = fresnel(Nuse, -V, 1.0, self.ior)  # :contentReference[oaicite:2]{index=2}

            # Reflexión
            R = reflectVector(Nuse, V)
            Rorig = intercept.point + bias
            Rhit = renderer.glCastRay(Rorig, R, None)
            if Rhit is not None:
                Rcol = Rhit.obj.material.GetSurfaceColor(Rhit, renderer, recursion + 1)
            else:
                Rcol = renderer.glEnvMapColor(Rorig, R)

            # Refracción (si no hay TIR)
            if not totalInternalReflection(Nuse, -V, 1.0, self.ior):  # :contentReference[oaicite:3]{index=3}
                T = refractVector(Nuse, -V, 1.0, self.ior)            # :contentReference[oaicite:4]{index=4}
                Torig = intercept.point - bias
                Thit = renderer.glCastRay(Torig, T, None)
                if Thit is not None:
                    Tcol = Thit.obj.material.GetSurfaceColor(Thit, renderer, recursion + 1)
                else:
                    Tcol = renderer.glEnvMapColor(Torig, T)
            else:
                Kt = 0.0
                Tcol = np.zeros(3)

            # Mezcla Fresnel
            color = Kr * np.array(Rcol) + Kt * np.array(Tcol)
            return tuple(np.clip(color, 0, 1))

        # OPAQUE (por defecto)
        return tuple(base)
