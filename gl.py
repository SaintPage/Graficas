# gl.py
import numpy as np
from PIL import Image

class Renderer:
    def __init__(self, width, height, fov=60, bg_color=(0, 0, 0)):
        self.width  = int(width)
        self.height = int(height)
        self.aspect = self.width / self.height
        self.fov    = np.deg2rad(fov)
        self.tanFov = np.tan(self.fov * 0.5)
        self.lights  = []
        self.max_depth = 3
        self.env_mode = "latlong" 

        self.framebuffer = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # cámara sencilla en el origen mirando -Z
        self.camPos = np.array((0.0, 0.0, 0.0), dtype=float)

        # color de fondo (si no hay envmap)
        self.bg_color = np.array(bg_color, dtype=float)


        self.env = None            # ndarray float (H,W,3) en 0..1
        self.env_yaw = 0.0         # grados de giro horizontal
        self.env_vflip = False     # invertir V si viene “al revés”

        self.objects = []          # esferas u otras figuras
        self.lights  = []          # luces

    @staticmethod
    def _to_u8(color01):
        return (np.clip(color01, 0.0, 1.0) * 255).astype(np.uint8)

    # API cómoda para armar la escena
    def add(self, obj):
        self.objects.append(obj)

    def add_light(self, light):
        self.lights.append(light)

    # rotación sobre Y (para alinear el envmap)
    def _rot_y(self, v, yaw_rad):
        cy, sy = np.cos(yaw_rad), np.sin(yaw_rad)
        x, y, z = v
        return np.array([cy*x + sy*z, y, -sy*x + cy*z], dtype=float)

    def load_envmap(self, path, yaw_deg=0.0, vflip=False, mode="latlong"):
        img = Image.open(path).convert("RGB")
        w, h = img.size
        if abs((w / h) - 2.0) > 0.2:
            print(f"[WARN] {path} no tiene relación de aspecto ~2:1 (es {w}:{h}). "
                "Podría verse distorsionada; idealmente usa un panorama lat-long 2:1.")
        self.env = np.asarray(img).astype(np.float32) / 255.0
        self.env_yaw   = float(yaw_deg)
        self.env_vflip = bool(vflip)
        self.env_mode  = mode



    def _sample_env_bilinear(self, u, v):
        """Muestreo bilineal en env lat-long (u,v en [0,1])."""
        H, W, _ = self.env.shape
        u = (u % 1.0) * W
        v = np.clip(v, 0.0, 0.999999) * H

        x0 = int(np.floor(u)) % W
        y0 = int(np.floor(v)) % H
        x1 = (x0 + 1) % W
        y1 = min(y0 + 1, H - 1)

        sx = u - np.floor(u)
        sy = v - np.floor(v)

        c00 = self.env[y0, x0]
        c10 = self.env[y0, x1]
        c01 = self.env[y1, x0]
        c11 = self.env[y1, x1]

        c0 = c00 * (1 - sx) + c10 * sx
        c1 = c01 * (1 - sx) + c11 * sx
        return c0 * (1 - sy) + c1 * sy

    def glEnvMapColor(self, point, direction):
        if self.env is None:
            return tuple(self.bg_color)

        d = np.array(direction, dtype=float)
        d /= (np.linalg.norm(d) + 1e-8)

        # Ajuste de yaw para alinear la imagen
        if self.env_yaw != 0.0:
            d = self._rot_y(d, np.deg2rad(self.env_yaw))

        if self.env_mode == "cyl":
            # Mapeo cilíndrico: U = atan2, V = lineal con Y (menos estiramiento si la imagen no es 360°)
            u = 0.5 + np.arctan2(-d[2], d[0]) / (2 * np.pi)
            v = 0.5 - 0.5 * d[1]                     # Y en [-1,1] → V en [0,1]
            v = np.clip(v, 0.0, 1.0)
        else:
            # Equirectangular (lat-long) 360x180
            u = 0.5 + np.arctan2(-d[2], d[0]) / (2 * np.pi)
            v = 0.5 - np.arcsin(np.clip(d[1], -1, 1)) / np.pi

        if self.env_vflip:
            v = 1.0 - v

        col = self._sample_env_bilinear(u, v)
        return tuple(col)

    def render(self):
        """Traza un rayo por pixel desde camPos hacia el plano de imagen."""
        for j in range(self.height):
            y = (1 - 2 * ((j + 0.5) / self.height)) * self.tanFov
            for i in range(self.width):
                x = (2 * ((i + 0.5) / self.width) - 1) * self.tanFov * self.aspect
                dir_cam = np.array((x, y, -1.0), dtype=float)
                dir_cam /= (np.linalg.norm(dir_cam) + 1e-8)

                color = self.cast_ray(self.camPos, dir_cam)
                self.framebuffer[j, i] = self._to_u8(color)

    def cast_ray(self, origin, direction, recursion=0):
        """Devuelve color [0..1] para un rayo origen+tdir."""
        O = np.array(origin, dtype=float)
        D = np.array(direction, dtype=float);  D /= (np.linalg.norm(D) + 1e-8)

        hit = self.scene_intersect(O, D)
        if hit is None:
            # Fondo: env map si existe, sino el bg fijo
            return self.glEnvMapColor(O, D) if self.env is not None else self.bg_color

        # El material (Phong/reflect/refract) calcula el color
        return hit.obj.material.GetSurfaceColor(hit, self, recursion)

    def scene_intersect(self, origin, direction, ignore_obj=None):
        """Encuentra el primer objeto intersectado por el rayo."""
        O = np.array(origin, dtype=float)
        D = np.array(direction, dtype=float);  D /= (np.linalg.norm(D) + 1e-8)

        nearest_hit, nearest_t = None, float("inf")
        for obj in self.objects:
            if obj is ignore_obj:
                continue
            h = obj.ray_intersect(O, D)
            if h and 1e-4 < h.distance < nearest_t:
                nearest_hit, nearest_t = h, h.distance
        return nearest_hit

    # Alias que usa material.py para sombras/recursión
    def glCastRay(self, origin, direction, ignore_obj=None, recursion=0):
        return self.scene_intersect(origin, direction, ignore_obj)

    def saveBMP(self, filename: str):
        """Guarda el framebuffer (H,W,3) uint8 como BMP 24-bit."""
        h, w, _ = self.framebuffer.shape
        row_stride = w * 3
        row_padded = (row_stride + 3) & ~3
        padding = row_padded - row_stride
        filesize = 14 + 40 + row_padded * h

        with open(filename, "wb") as f:
            # BITMAPFILEHEADER
            f.write(b"BM")
            f.write(filesize.to_bytes(4, "little"))
            f.write((0).to_bytes(2, "little"))
            f.write((0).to_bytes(2, "little"))
            f.write((14 + 40).to_bytes(4, "little"))

            # BITMAPINFOHEADER
            f.write((40).to_bytes(4, "little"))
            f.write(w.to_bytes(4, "little", signed=True))
            f.write(h.to_bytes(4, "little", signed=True))   # positivo => bottom-up
            f.write((1).to_bytes(2, "little"))
            f.write((24).to_bytes(2, "little"))
            f.write((0).to_bytes(4, "little"))              # BI_RGB
            f.write((row_padded*h).to_bytes(4, "little"))
            f.write((2835).to_bytes(4, "little"))           # ~72 DPI
            f.write((2835).to_bytes(4, "little"))
            f.write((0).to_bytes(4, "little"))
            f.write((0).to_bytes(4, "little"))

            # pixel data (BGR, bottom-up)
            pad = b"\x00" * padding
            for y in range(h-1, -1, -1):
                row = self.framebuffer[y]          # RGB
                bgr = row[:, [2, 1, 0]]
                f.write(bgr.tobytes())
                if padding:
                    f.write(pad)
