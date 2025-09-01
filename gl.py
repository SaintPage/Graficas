import numpy as np

class Renderer:
    def __init__(self, width, height, fov=60, bg_color=(0, 0, 0)):
        self.width  = int(width)
        self.height = int(height)
        self.aspect = self.width / self.height
        self.fov    = np.deg2rad(fov)               # en radianes
        self.tanFov = np.tan(self.fov * 0.5)
        # framebuffer en 0..255 (uint8)
        self.framebuffer = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # cámara en el origen mirando -Z
        self.camPos    = np.array((0.0, 0.0, 0.0), dtype=float)
        self.camTarget = np.array((0.0, 0.0, -1.0), dtype=float)
        self.camUp     = np.array((0.0, 1.0,  0.0), dtype=float)

        # escena
        self.objects = []   # esferas u otras figuras
        self.lights  = []   # luces

        # color de fondo en 0..1
        self.bg_color = np.array(bg_color, dtype=float)

    @staticmethod
    def _to_u8(color01):
        return (np.clip(color01, 0.0, 1.0) * 255).astype(np.uint8)

    # ---------------- API de escena ----------------
    def add(self, obj): self.objects.append(obj)
    def add_light(self, light): self.lights.append(light)

    # ---------------- Núcleo del raytracer ----------------
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

    def cast_ray(self, origin, direction):
        """Devuelve color [0..1] para un rayo origen+tdir."""
        O = np.array(origin, dtype=float)
        D = np.array(direction, dtype=float);  D /= (np.linalg.norm(D) + 1e-8)

        hit = self.scene_intersect(O, D)
        if hit is None:
            return self.bg_color
        return hit.obj.material.GetSurfaceColor(hit, self)

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

    # alias usado por material.py para sombras
    def glCastRay(self, origin, direction, ignore_obj=None):
        return self.scene_intersect(origin, direction, ignore_obj)

    # ---------------- Guardado a BMP ----------------
    def saveBMP(self, filename: str):
        """
        Guarda el framebuffer (H,W,3) uint8 como BMP 24-bit.
        """
        h, w, _ = self.framebuffer.shape
        row_stride = w * 3
        # Cada fila del BMP debe estar alineada a múltiplos de 4 bytes
        row_padded = (row_stride + 3) & ~3
        padding = row_padded - row_stride

        filesize = 14 + 40 + row_padded * h  # FileHeader (14) + InfoHeader (40) + data

        with open(filename, "wb") as f:
            # --- BITMAPFILEHEADER (14 bytes) ---
            f.write(b"BM")                               # bfType
            f.write(filesize.to_bytes(4, "little"))      # bfSize
            f.write((0).to_bytes(2, "little"))           # bfReserved1
            f.write((0).to_bytes(2, "little"))           # bfReserved2
            f.write((14 + 40).to_bytes(4, "little"))     # bfOffBits

            # --- BITMAPINFOHEADER (40 bytes) ---
            f.write((40).to_bytes(4, "little"))          # biSize
            f.write(w.to_bytes(4, "little", signed=True))# biWidth
            f.write(h.to_bytes(4, "little", signed=True))# biHeight (positivo = bottom-up)
            f.write((1).to_bytes(2, "little"))           # biPlanes
            f.write((24).to_bytes(2, "little"))          # biBitCount
            f.write((0).to_bytes(4, "little"))           # biCompression (BI_RGB)
            f.write((row_padded*h).to_bytes(4, "little"))# biSizeImage
            f.write((2835).to_bytes(4, "little"))        # biXPelsPerMeter (~72 DPI)
            f.write((2835).to_bytes(4, "little"))        # biYPelsPerMeter
            f.write((0).to_bytes(4, "little"))           # biClrUsed
            f.write((0).to_bytes(4, "little"))           # biClrImportant

            # --- Pixel data (BGR, filas de abajo hacia arriba) ---
            pad_bytes = b"\x00" * padding
            for y in range(h-1, -1, -1):                 # bottom-up
                row = self.framebuffer[y]                # (W,3) en RGB
                bgr = row[:, [2, 1, 0]]                  # convertir a BGR
                f.write(bgr.tobytes())
                if padding:
                    f.write(pad_bytes)
