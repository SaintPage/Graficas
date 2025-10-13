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

# ---------------- Cylinder ----------------
class Cylinder:
    def __init__(self, center, axis, radius, height, material):
        self.center = np.array(center, dtype=float)
        self.axis = _norm(axis)  # dirección del eje del cilindro (normalizada)
        self.radius = float(radius)
        self.height = float(height)
        self.material = material
        
        # Puntos de los extremos del cilindro
        half_height = self.height * 0.5
        self.bottom = self.center - self.axis * half_height
        self.top = self.center + self.axis * half_height

    def ray_intersect(self, orig, dir):
        # Algoritmo de intersección rayo-cilindro
        # Transformamos a un sistema donde el cilindro está alineado con el eje Y
        
        # Vector del origen al centro del cilindro
        oc = orig - self.center
        
        # Proyectamos el rayo en el plano perpendicular al eje del cilindro
        # Componentes paralelas y perpendiculares al eje
        dir_parallel = np.dot(dir, self.axis) * self.axis
        dir_perp = dir - dir_parallel
        
        oc_parallel = np.dot(oc, self.axis) * self.axis
        oc_perp = oc - oc_parallel
        
        # Resolvemos la intersección en 2D (cilindro infinito)
        a = np.dot(dir_perp, dir_perp)
        b = 2.0 * np.dot(oc_perp, dir_perp)
        c = np.dot(oc_perp, oc_perp) - self.radius * self.radius
        
        discriminant = b * b - 4 * a * c
        
        if discriminant < 0:
            return None  # No hay intersección con el cilindro infinito
        
        if abs(a) < 1e-8:
            # Rayo paralelo al eje del cilindro
            if c > 0:
                return None  # Fuera del radio
            # Intersección con las tapas
            return self._intersect_caps(orig, dir)
        
        sqrt_disc = np.sqrt(discriminant)
        t1 = (-b - sqrt_disc) / (2 * a)
        t2 = (-b + sqrt_disc) / (2 * a)
        
        candidates = []
        
        # Verificar ambas intersecciones
        for t in [t1, t2]:
            if t <= 1e-4:
                continue
                
            P = orig + dir * t
            
            # Verificar si está dentro de la altura del cilindro
            height_param = np.dot(P - self.center, self.axis)
            if abs(height_param) <= self.height * 0.5:
                # Calcular normal (perpendicular al eje, apuntando hacia afuera)
                center_to_point = P - self.center
                normal_component = center_to_point - np.dot(center_to_point, self.axis) * self.axis
                normal = _norm(normal_component)
                candidates.append((t, P, normal))
        
        # También verificar intersección con las tapas
        cap_result = self._intersect_caps(orig, dir)
        if cap_result is not None:
            candidates.append((cap_result.distance, cap_result.point, cap_result.normal))
        
        if not candidates:
            return None
        
        # Devolver la intersección más cercana
        candidates.sort(key=lambda x: x[0])
        t, P, N = candidates[0]
        return Intercept(P, N, t, dir, self)
    
    def _intersect_caps(self, orig, dir):
        """Intersección con las tapas circulares del cilindro"""
        candidates = []
        
        # Verificar intersección con cada tapa
        for cap_center, cap_normal in [(self.bottom, -self.axis), (self.top, self.axis)]:
            # Intersección rayo-plano
            denom = np.dot(dir, cap_normal)
            if abs(denom) < 1e-6:
                continue  # Paralelo al plano
            
            t = np.dot(cap_center - orig, cap_normal) / denom
            if t <= 1e-4:
                continue
            
            P = orig + dir * t
            
            # Verificar si está dentro del radio
            dist_from_center = np.linalg.norm(P - cap_center)
            if dist_from_center <= self.radius:
                candidates.append((t, P, cap_normal))
        
        if not candidates:
            return None
        
        # Devolver la intersección más cercana
        candidates.sort(key=lambda x: x[0])
        t, P, N = candidates[0]
        return Intercept(P, N, t, dir, self)

# ---------------- Torus (Dona) ----------------
class Torus:
    def __init__(self, center, axis, major_radius, minor_radius, material):
        self.center = np.array(center, dtype=float)
        self.axis = _norm(axis)  # eje principal del torus (normalizada)
        self.major_radius = float(major_radius)  # radio mayor (del centro al tubo)
        self.minor_radius = float(minor_radius)  # radio menor (grosor del tubo)
        self.material = material
        
        # Crear sistema de coordenadas local
        # Necesitamos dos vectores perpendiculares al eje
        if abs(self.axis[0]) < 0.9:
            temp = np.array([1, 0, 0])
        else:
            temp = np.array([0, 1, 0])
        
        self.u = _norm(np.cross(self.axis, temp))
        self.v = _norm(np.cross(self.axis, self.u))

    def ray_intersect(self, orig, dir):
        # Transformar el rayo al sistema de coordenadas local del torus
        # donde el eje principal está alineado con Z
        
        # Trasladar origen
        local_orig = orig - self.center
        
        # Rotar al sistema local
        ox = np.dot(local_orig, self.u)
        oy = np.dot(local_orig, self.v)
        oz = np.dot(local_orig, self.axis)
        
        dx = np.dot(dir, self.u)
        dy = np.dot(dir, self.v)
        dz = np.dot(dir, self.axis)
        
        # Parámetros del torus
        R = self.major_radius  # radio mayor
        r = self.minor_radius  # radio menor
        
        # Resolver la ecuación cuártica del torus
        # (x² + y² + z² + R² - r²)² = 4R²(x² + y²)
        
        # Coeficientes para t en la ecuación paramétrica del rayo
        # P(t) = orig + t * dir = (ox + t*dx, oy + t*dy, oz + t*dz)
        
        # Términos intermedios
        sum_d_sqr = dx*dx + dy*dy + dz*dz
        sum_o_sqr = ox*ox + oy*oy + oz*oz
        sum_od = ox*dx + oy*dy + oz*dz
        
        k = sum_o_sqr + R*R - r*r
        
        # Coeficientes de la ecuación cuártica At⁴ + Bt³ + Ct² + Dt + E = 0
        A = sum_d_sqr * sum_d_sqr
        B = 4.0 * sum_d_sqr * sum_od
        C = 2.0 * sum_d_sqr * k + 4.0 * sum_od * sum_od + 4.0 * R*R * (dx*dx + dy*dy)
        D = 4.0 * k * sum_od + 8.0 * R*R * (ox*dx + oy*dy)
        E = k*k + 4.0 * R*R * (ox*ox + oy*oy) - 4.0 * R*R * r*r
        
        # Resolver ecuación cuártica
        roots = self._solve_quartic(A, B, C, D, E)
        
        valid_intersections = []
        
        for t in roots:
            if t <= 1e-4:
                continue
            
            # Punto de intersección
            P = orig + t * dir
            
            # Calcular normal
            normal = self._compute_normal(P)
            if normal is not None:
                valid_intersections.append((t, P, normal))
        
        if not valid_intersections:
            return None
        
        # Devolver la intersección más cercana
        valid_intersections.sort(key=lambda x: x[0])
        t, P, N = valid_intersections[0]
        return Intercept(P, N, t, dir, self)
    
    def _solve_quartic(self, a, b, c, d, e):
        """Resuelve una ecuación cuártica usando método numérico simplificado"""
        if abs(a) < 1e-10:
            return self._solve_cubic(b, c, d, e)
        
        # Normalizar coeficientes
        b /= a
        c /= a 
        d /= a
        e /= a
        
        # Método más preciso usando numpy para casos complejos
        try:
            coeffs = [1, b, c, d, e]
            numpy_roots = np.roots(coeffs)
            roots = []
            
            for root in numpy_roots:
                if np.isreal(root) and np.real(root) > 1e-4:
                    t_val = float(np.real(root))
                    if not any(abs(t_val - r) < 1e-4 for r in roots):
                        roots.append(t_val)
            return roots
        except:
            return []
    
    def _solve_cubic(self, a, b, c, d):
        """Resuelve ecuación cúbica"""
        try:
            coeffs = [a, b, c, d]
            numpy_roots = np.roots(coeffs)
            roots = []
            
            for root in numpy_roots:
                if np.isreal(root) and np.real(root) > 1e-4:
                    roots.append(float(np.real(root)))
            return roots
        except:
            return []
    
    def _compute_normal(self, point):
        """Calcula la normal en un punto del torus"""
        # Transformar punto al sistema local
        local_point = point - self.center
        
        x = np.dot(local_point, self.u)
        y = np.dot(local_point, self.v)
        z = np.dot(local_point, self.axis)
        
        # Distancia del punto al eje principal en el plano XY
        rho = np.sqrt(x*x + y*y)
        
        if rho < 1e-8:
            return None  # Punto en el eje, normal indefinida
        
        # Punto en el círculo central más cercano
        circle_x = self.major_radius * x / rho
        circle_y = self.major_radius * y / rho
        circle_z = 0.0
        
        # Vector del círculo central al punto
        dx = x - circle_x
        dy = y - circle_y
        dz = z - circle_z
        
        # Normal en coordenadas locales
        local_normal = np.array([dx, dy, dz])
        local_normal = _norm(local_normal)
        
        # Transformar de vuelta al sistema global
        global_normal = (local_normal[0] * self.u + 
                        local_normal[1] * self.v + 
                        local_normal[2] * self.axis)
        
        return _norm(global_normal)

# ---------------- Cone ----------------
class Cone:
    def __init__(self, apex, base_center, radius, material):
        self.apex = np.array(apex, dtype=float)
        self.base_center = np.array(base_center, dtype=float)
        self.radius = float(radius)
        self.material = material
        
        # Calcular eje y altura del cono
        self.axis = self.base_center - self.apex
        self.height = np.linalg.norm(self.axis)
        self.axis_unit = _norm(self.axis)

    def ray_intersect(self, orig, dir):
        # Trasladar al sistema donde el apex está en el origen
        orig_local = orig - self.apex
        
        # Proyección en el eje del cono
        k = self.radius / self.height
        k_sq = k * k
        
        # Coeficientes de la ecuación cuadrática para la superficie lateral
        axis_dot_dir = np.dot(self.axis_unit, dir)
        axis_dot_orig = np.dot(self.axis_unit, orig_local)
        
        a = np.dot(dir, dir) - (1 + k_sq) * axis_dot_dir * axis_dot_dir
        b = 2 * (np.dot(orig_local, dir) - (1 + k_sq) * axis_dot_orig * axis_dot_dir)
        c = np.dot(orig_local, orig_local) - (1 + k_sq) * axis_dot_orig * axis_dot_orig
        
        discriminant = b * b - 4 * a * c
        candidates = []
        
        if discriminant >= 0 and abs(a) > 1e-8:
            sqrt_disc = np.sqrt(discriminant)
            t1 = (-b - sqrt_disc) / (2 * a)
            t2 = (-b + sqrt_disc) / (2 * a)
            
            for t in [t1, t2]:
                if t <= 1e-4:
                    continue
                    
                P = orig + t * dir
                P_local = P - self.apex
                
                # Verificar si está dentro de la altura del cono
                height_param = np.dot(P_local, self.axis_unit)
                if 0 <= height_param <= self.height:
                    # Calcular normal de la superficie lateral
                    # Normal apunta hacia afuera del cono
                    proj_on_axis = height_param * self.axis_unit
                    radial_component = P_local - proj_on_axis
                    
                    # Normal del cono en coordenadas locales
                    normal_radial = _norm(radial_component)
                    slope_factor = self.radius / self.height
                    normal = _norm(normal_radial - slope_factor * self.axis_unit)
                    
                    candidates.append((t, P, normal))
        
        # Verificar intersección con la base
        base_result = self._intersect_base(orig, dir)
        if base_result is not None:
            candidates.append((base_result.distance, base_result.point, base_result.normal))
        
        if not candidates:
            return None
        
        # Devolver la intersección más cercana
        candidates.sort(key=lambda x: x[0])
        t, P, N = candidates[0]
        return Intercept(P, N, t, dir, self)
    
    def _intersect_base(self, orig, dir):
        """Intersección con la base circular del cono"""
        # Intersección rayo-plano de la base
        denom = np.dot(dir, self.axis_unit)
        if abs(denom) < 1e-6:
            return None
        
        t = np.dot(self.base_center - orig, self.axis_unit) / denom
        if t <= 1e-4:
            return None
        
        P = orig + t * dir
        
        # Verificar si está dentro del radio de la base
        dist_from_center = np.linalg.norm(P - self.base_center)
        if dist_from_center <= self.radius:
            return Intercept(P, self.axis_unit, t, dir, self)
        
        return None

# ---------------- Ellipsoid ----------------
class Ellipsoid:
    def __init__(self, center, radii, material):
        self.center = np.array(center, dtype=float)
        self.radii = np.array(radii, dtype=float)  # (rx, ry, rz)
        self.material = material

    def ray_intersect(self, orig, dir):
        # Trasladar al sistema donde el elipsoide está centrado en el origen
        oc = orig - self.center
        
        # Normalizar por los radii para convertir a esfera unitaria
        oc_norm = oc / self.radii
        dir_norm = dir / self.radii
        
        # Resolver intersección con esfera unitaria
        a = np.dot(dir_norm, dir_norm)
        b = 2.0 * np.dot(oc_norm, dir_norm)
        c = np.dot(oc_norm, oc_norm) - 1.0
        
        discriminant = b * b - 4 * a * c
        
        if discriminant < 0:
            return None
        
        sqrt_disc = np.sqrt(discriminant)
        t1 = (-b - sqrt_disc) / (2 * a)
        t2 = (-b + sqrt_disc) / (2 * a)
        
        t = t1 if t1 > 1e-4 else t2
        if t <= 1e-4:
            return None
        
        P = orig + t * dir
        
        # Calcular normal del elipsoide
        # La normal en un elipsoide es: (2*(P-C)/radii²) normalizada
        P_local = P - self.center
        normal_unnorm = 2 * P_local / (self.radii * self.radii)
        normal = _norm(normal_unnorm)
        
        return Intercept(P, normal, t, dir, self)
