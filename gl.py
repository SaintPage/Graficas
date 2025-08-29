# gl.py
import math, struct
import numpy as np

# ---------------- utils ----------------
def normalize(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    return v / n if n > 1e-8 else v

def clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)

# ---------------- BMP writer (24-bit, sin compresión) ----------------
def savebmp(filename: str, width: int, height: int, framebuffer_u8: np.ndarray):
    """
    framebuffer_u8: np.uint8 [H, W, 3] en RGB (origen arriba-izquierda).
    """
    pad = (4 - (width * 3) % 4) % 4
    image_size = (3 * width + pad) * height
    file_size = 14 + 40 + image_size

    with open(filename, "wb") as f:
        # File header
        f.write(b"BM")
        f.write(struct.pack("<I", file_size))
        f.write(b"\x00\x00\x00\x00")         # reserved
        f.write(struct.pack("<I", 14 + 40))  # offset to pixel data

        # DIB header (BITMAPINFOHEADER)
        f.write(struct.pack("<I", 40))       # header size
        f.write(struct.pack("<i", width))
        f.write(struct.pack("<i", height))   # positivo = bottom-up
        f.write(struct.pack("<H", 1))        # planes
        f.write(struct.pack("<H", 24))       # bpp
        f.write(struct.pack("<I", 0))        # BI_RGB
        f.write(struct.pack("<I", image_size))
        f.write(struct.pack("<I", 0))        # x ppm
        f.write(struct.pack("<I", 0))        # y ppm
        f.write(struct.pack("<I", 0))        # colors
        f.write(struct.pack("<I", 0))        # important colors

        # Pixel data (bottom-up), BGR + padding por fila
        for y in range(height - 1, -1, -1):
            row_rgb = framebuffer_u8[y]                 # [W,3]
            row_bgr = row_rgb[:, ::-1].tobytes()        # RGB -> BGR
            f.write(row_bgr)
            if pad:
                f.write(b"\x00" * pad)

# ---------------- Raytracer ----------------
class Raytracer:
    def __init__(self, width=800, height=450):
        self.width  = width
        self.height = height
        self.fb = np.zeros((height, width, 3), dtype=np.float32)

        # cámara (se calcula con set_camera)
        self.eye = np.array((0.0, 0.0, 0.0), dtype=float)
        self.forward = np.array((0.0, 0.0, -1.0), dtype=float)
        self.right   = np.array((1.0, 0.0,  0.0), dtype=float)
        self.up      = np.array((0.0, 1.0,  0.0), dtype=float)
        self.half_w = 1.0
        self.half_h = 1.0

        self.scene  = []   # lista de Sphere (figures.Sphere)
        self.lights = []   # lista de luces (PointLight / DirectionalLight)
        self.clear_color = np.array((0.7, 0.8, 1.0), dtype=float)

    # ---------- cámara ----------
    def set_camera(self, eye, target, up=(0,1,0), fov_deg=60.0):
        eye    = np.array(eye,    dtype=float)
        target = np.array(target, dtype=float)
        up     = np.array(up,     dtype=float)

        forward = normalize(target - eye)
        right   = normalize(np.cross(forward, up))
        new_up  = normalize(np.cross(right, forward))

        aspect = self.width / float(self.height)
        fov = math.radians(fov_deg)
        half_h = math.tan(fov * 0.5)
        half_w = half_h * aspect

        self.eye = eye
        self.forward = forward
        self.right = right
        self.up = new_up
        self.half_w = half_w
        self.half_h = half_h

    def set_scene(self, figures):
        self.scene = figures

    def set_lights(self, lights):
        self.lights = lights

    # ---------- intersección rayo-esfera ----------
    def _ray_sphere_intersect(self, ro, rd, sphere):
        oc = ro - sphere.center
        b = 2.0 * np.dot(rd, oc)
        c = np.dot(oc, oc) - sphere.radius * sphere.radius
        disc = b*b - 4.0*c
        if disc < 0.0:
            return None
        sdisc = math.sqrt(disc)
        t0 = (-b - sdisc) * 0.5
        t1 = (-b + sdisc) * 0.5
        t  = t0 if t0 > 1e-4 else (t1 if t1 > 1e-4 else None)
        if t is None:
            return None
        hit = ro + t * rd
        nrm = (hit - sphere.center)
        nrm = nrm / (np.linalg.norm(nrm) + 1e-8)
        return t, hit, nrm

    def _shade(self, hit, nrm, view_dir, material, spheres):
        def clamp01(x: float) -> float:
            return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)

        col = np.array(material.color, dtype=float) * material.ka

        for L in self.lights:
            ldir, Ldist, Lcol = L.sample(hit)

            # ---- sombras (rayito hacia la luz) ----
            shadow = False
            ro = hit + nrm * 1e-3
            rd = ldir
            max_t = (Ldist - 1e-3) if np.isfinite(Ldist) else None
            for s in spheres:
                isec = self._ray_sphere_intersect(ro, rd, s)
                if isec is None:
                    continue
                if max_t is None or isec[0] < max_t:
                    shadow = True
                    break
            if shadow:
                continue

            # ---- Phong (Blinn) ----
            ndl  = clamp01(float(np.dot(nrm, ldir)))
            diff = material.kd * ndl
            h = ldir + view_dir
            h = h / (np.linalg.norm(h) + 1e-8)
            spec = material.ks * (clamp01(float(np.dot(nrm, h))) ** material.shininess)

            col += np.array(material.color) * diff * Lcol
            col += spec * Lcol

        return np.clip(col, 0.0, 1.0)

    # ---------- render ----------
    def render(self):
        H, W = self.height, self.width
        eye, fwd, right, up = self.eye, self.forward, self.right, self.up
        half_w, half_h = self.half_w, self.half_h
        bg = self.clear_color

        for j in range(H):
            v = (1 - 2 * ((j + 0.5) / H)) * half_h
            for i in range(W):
                u = (2 * ((i + 0.5) / W) - 1) * half_w
                rd = normalize(fwd + u * right + v * up)
                ro = eye

                nearest_t = 1e9
                rec = None
                for s in self.scene:
                    hit = self._ray_sphere_intersect(ro, rd, s)
                    if hit is not None and hit[0] < nearest_t:
                        nearest_t = hit[0]
                        rec = (s, hit[1], hit[2])  # sphere, point, normal

                if rec is None:
                    # cielo simple
                    t = 0.5 * (rd[1] + 1.0)
                    self.fb[j, i] = (1.0 - t) * np.array((1, 1, 1)) + t * np.array((0.6, 0.8, 1.0))
                else:
                    s, hit, nrm = rec
                    view_dir = normalize(-rd)
                    self.fb[j, i] = self._shade(hit, nrm, view_dir, s.material, self.scene)

    # ---------- guardar ----------
    def save(self, filename="output.bmp"):
        # gamma 2.2
        img = (np.clip(self.fb, 0, 1) ** (1/2.2) * 255).astype(np.uint8)
        savebmp(filename, self.width, self.height, img)
