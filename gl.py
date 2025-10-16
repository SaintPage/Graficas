import numpy as np
from PIL import Image
import math
import os
import contextlib
import sys
try:
    # pygame prints introductory lines to stdout/stderr; suppress them during import
    with open(os.devnull, 'w') as devnull:
        with contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
            import pygame
    _HAS_PYGAME = True
except Exception:
    _HAS_PYGAME = False

class Renderer:
    def __init__(self, width, height, fov=60, bg_color=(0, 0, 0), ssaa=1):
        self.width  = int(width)
        self.height = int(height)
        self.aspect = self.width / self.height
        self.fov    = np.deg2rad(fov)
        self.tanFov = np.tan(self.fov * 0.5)

        # final framebuffer (uint8) and HDR working buffer handled in render
        self.framebuffer = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        self.ssaa = int(ssaa) if ssaa >= 1 else 1
        self.camPos      = np.array((0.0, 0.0, 0.0), dtype=float)

        self.bg_color  = np.array(bg_color, dtype=float)
        self.objects   = []
        self.lights    = []
        self.max_depth = 3

        # (Envmap opcional; no lo usamos en el cuarto, pero lo dejo)
        self.env       = None
        self.env_yaw   = 0.0
        self.env_vflip = False

    @staticmethod
    def _to_u8(color01):
        return (np.clip(color01, 0.0, 1.0) * 255).astype(np.uint8)

    def add(self, obj):        self.objects.append(obj)
    def add_light(self, light): self.lights.append(light)

    # -------- envmap (opcional)
    def _rot_y(self, v, yaw_rad):
        cy, sy = np.cos(yaw_rad), np.sin(yaw_rad)
        x, y, z = v
        return np.array([cy*x + sy*z, y, -sy*x + cy*z], dtype=float)

    def load_envmap(self, path, yaw_deg=0.0, vflip=False, mode="latlong"):
        img = Image.open(path).convert("RGB")
        w, h = img.size
        if abs((w / h) - 2.0) > 0.2:
            print(f"[WARN] {path} no es ~2:1 ({w}:{h}); puede distorsionar.")
        self.env = np.asarray(img).astype(np.float32) / 255.0
        self.env_yaw   = float(yaw_deg)
        self.env_vflip = bool(vflip)

    def _sample_env_bilinear(self, u, v):
        H, W, _ = self.env.shape
        u = (u % 1.0) * W
        v = np.clip(v, 0.0, 0.999999) * H
        x0 = int(np.floor(u)) % W
        y0 = int(np.floor(v)) % H
        x1 = (x0 + 1) % W
        y1 = min(y0 + 1, H - 1)
        sx = u - np.floor(u)
        sy = v - np.floor(v)
        c00 = self.env[y0, x0]; c10 = self.env[y0, x1]
        c01 = self.env[y1, x0]; c11 = self.env[y1, x1]
        c0 = c00 * (1 - sx) + c10 * sx
        c1 = c01 * (1 - sx) + c11 * sx
        return c0 * (1 - sy) + c1 * sy

    def glEnvMapColor(self, point, direction):
        if self.env is None:
            return tuple(self.bg_color)
        d = np.array(direction, dtype=float)
        d /= (np.linalg.norm(d) + 1e-8)
        if self.env_yaw != 0.0:
            d = self._rot_y(d, np.deg2rad(self.env_yaw))
        u = 0.5 + np.arctan2(-d[2], d[0]) / (2*np.pi)
        v = 0.5 - np.arcsin(np.clip(d[1], -1, 1)) / np.pi
        if self.env_vflip: v = 1.0 - v
        return tuple(self._sample_env_bilinear(u, v))

    # -------- RT core
    def render(self, row_callback=None):
        # If no SSAA requested, keep existing fast path
        if self.ssaa == 1:
            for j in range(self.height):
                y = (1 - 2 * ((j + 0.5) / self.height)) * self.tanFov
                for i in range(self.width):
                    x = (2 * ((i + 0.5) / self.width) - 1) * self.tanFov * self.aspect
                    dir_cam = np.array((x, y, -1.0), dtype=float)
                    dir_cam /= (np.linalg.norm(dir_cam) + 1e-8)
                    color = self.cast_ray(self.camPos, dir_cam)
                    self.framebuffer[j, i] = self._to_u8(color)
                if row_callback:
                    row_callback(j)  # para refrescar pygame por filas
            return

        # SSAA path: render at higher resolution and downsample
        H_hr = self.height * self.ssaa
        W_hr = self.width * self.ssaa
        hr_buf = np.zeros((H_hr, W_hr, 3), dtype=np.float32)

        for j in range(H_hr):
            y = (1 - 2 * ((j + 0.5) / H_hr)) * self.tanFov
            for i in range(W_hr):
                x = (2 * ((i + 0.5) / W_hr) - 1) * self.tanFov * self.aspect
                dir_cam = np.array((x, y, -1.0), dtype=float)
                dir_cam /= (np.linalg.norm(dir_cam) + 1e-8)
                hr_buf[j, i] = np.array(self.cast_ray(self.camPos, dir_cam), dtype=np.float32)
            # coarse progress callback based on low-res rows
            if row_callback and (j % self.ssaa) == 0:
                row_callback(j // self.ssaa)

            # If we've completed a full low-res row (ssaa HR rows), downsample that row
            # into the final framebuffer so partial results are available.
            if (j % self.ssaa) == (self.ssaa - 1):
                y_low = j // self.ssaa
                y0 = y_low * self.ssaa
                y1 = y0 + self.ssaa
                # downsample each column block for this row
                for x_low in range(self.width):
                    x0 = x_low * self.ssaa
                    x1 = x0 + self.ssaa
                    block = hr_buf[y0:y1, x0:x1]
                    avg = block.mean(axis=(0, 1))
                    self.framebuffer[y_low, x_low] = self._to_u8(avg)

        # NOTE: after the loop the framebuffer is already filled progressively, so nothing
        # else is required here. Keep compatibility with previous behavior.

    def cast_ray(self, origin, direction, recursion=0):
        O = np.array(origin, dtype=float)
        D = np.array(direction, dtype=float);  D /= (np.linalg.norm(D) + 1e-8)
        hit = self.scene_intersect(O, D)
        if hit is None:
            return self.glEnvMapColor(O, D) if self.env is not None else self.bg_color
        return hit.obj.material.GetSurfaceColor(hit, self, recursion)

    def scene_intersect(self, origin, direction, ignore_obj=None):
        O = np.array(origin, dtype=float)
        D = np.array(direction, dtype=float);  D /= (np.linalg.norm(D) + 1e-8)
        nearest_hit, nearest_t = None, float("inf")
        for obj in self.objects:
            if obj is ignore_obj:  # para sombras/recursión
                continue
            h = obj.ray_intersect(O, D)
            if h and 1e-4 < h.distance < nearest_t:
                nearest_hit, nearest_t = h, h.distance
        return nearest_hit

    # alias para materiales
    def glCastRay(self, origin, direction, ignore_obj=None, recursion=0):
        return self.scene_intersect(origin, direction, ignore_obj)

    # BMP (por si quieres exportar)
    def saveBMP(self, filename: str):
        import os

        # optionally autoscale if values are very low (useful for low-light renders)
        NO_AUTOSCALE = os.environ.get('RAY_NO_AUTOSCALE') == '1'

        # Work on a copy so we don't mutate the in-memory framebuffer
        fb = self.framebuffer.copy().astype(np.uint8)
        h, w, _ = fb.shape

        # Compute max per channel
        maxvals = fb.max(axis=(0,1)).astype(int)
        if not NO_AUTOSCALE:
            max_overall = int(maxvals.max())
            if max_overall > 0 and max_overall < 48:
                # scale up so the max becomes near 230 (leave some headroom)
                scale = min(230.0 / max_overall, 255.0)
                if not getattr(self, 'quiet', False):
                    print(f"[saveBMP] autoscaling framebuffer by {scale:.2f} (max before {max_overall})")
                fb = np.clip((fb.astype(np.float32) * scale), 0, 255).astype(np.uint8)
            else:
                if not getattr(self, 'quiet', False):
                    print(f"[saveBMP] no autoscale needed (max per channel {tuple(maxvals)})")
        else:
            if not getattr(self, 'quiet', False):
                print("[saveBMP] autoscale disabled via RAY_NO_AUTOSCALE=1")
        row_stride = w * 3
        row_padded = (row_stride + 3) & ~3
        padding = row_padded - row_stride
        filesize = 14 + 40 + row_padded * h
        with open(filename, "wb") as f:
            f.write(b"BM")
            f.write(filesize.to_bytes(4, "little"))
            f.write((0).to_bytes(2, "little"))
            f.write((0).to_bytes(2, "little"))
            f.write((14 + 40).to_bytes(4, "little"))
            f.write((40).to_bytes(4, "little"))
            f.write(w.to_bytes(4, "little", signed=True))
            f.write(h.to_bytes(4, "little", signed=True))
            f.write((1).to_bytes(2, "little"))
            f.write((24).to_bytes(2, "little"))
            f.write((0).to_bytes(4, "little"))
            f.write((row_padded*h).to_bytes(4, "little"))
            f.write((2835).to_bytes(4, "little"))
            f.write((2835).to_bytes(4, "little"))
            f.write((0).to_bytes(4, "little"))
            f.write((0).to_bytes(4, "little"))
            pad = b"\x00" * padding
            for y in range(h-1, -1, -1):
                row = fb[y]
                bgr = row[:, [2, 1, 0]]
                f.write(bgr.tobytes())
                if padding: f.write(pad)

    # Progressive real-time render that updates a pygame surface row-by-row.
    # screen can be a pygame.Surface provided by the caller, or None to create
    # a new window sized (WINDOW_W, WINDOW_H). The method returns the final
    # framebuffer as uint8 array (H x W x 3).
    def render_progressive(self, screen=None, window_size=None):
        if not _HAS_PYGAME:
            raise RuntimeError('pygame is required for render_progressive')

        W, H = int(self.width), int(self.height)
        aspect = self.aspect
        # helper to convert linear color to sRGB-like for display
        def to_srgb(img):
            # simple gamma correction (approx sRGB)
            return np.clip(img, 0.0, 1.0) ** (1.0 / 2.2)

        # create screen if not provided
        if screen is None:
            if window_size is None:
                window_size = (self.width, self.height)
            pygame.init()
            screen = pygame.display.set_mode(window_size)
            pygame.display.set_caption('Progressive Render')

        # working float image
        img = np.zeros((H, W, 3), dtype=np.float32)
        scale = math.tan(self.fov * 0.5)

        for y in range(H):
            # handle quit events so window stays responsive
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit()
                    return (np.clip(img,0,1) * 255).astype(np.uint8)

            py = (1 - 2 * ((y + 0.5) / H)) * scale
            for x in range(W):
                px = (2 * ((x + 0.5) / W) - 1) * scale * aspect
                # note: in this renderer the camera looks towards -Z, so dir z = -1
                dir_cam = np.array((px, py, -1.0), dtype=float)
                dir_cam /= (np.linalg.norm(dir_cam) + 1e-8)
                img[y, x] = np.array(self.cast_ray(self.camPos, dir_cam), dtype=np.float32)

            # draw current image to surface and scale to window
            surf_arr = (to_srgb(img) * 255).astype(np.uint8)
            # pygame expects (w,h,3) with axes swapped from numpy default
            surf = pygame.surfarray.make_surface(surf_arr.swapaxes(0, 1))
            if window_size is not None and window_size != (W, H):
                surf = pygame.transform.smoothscale(surf, window_size)
            screen.blit(surf, (0, 0))

            # Print coarse progress to console so users running without --quiet
            # still see render progress (prints will be suppressed if stdout is
            # redirected or if builtins.print was overridden by quiet mode).
            try:
                progress_step = max(1, H // 40)
                if (y % progress_step) == 0:
                    pct = int((y + 1) * 100 / H)
                    if not getattr(self, 'quiet', False):
                        print(f"Progress: {pct}% (row {y+1}/{H})")
            except Exception:
                # never let progress printing break the render
                pass

            # draw percentage overlay (if fonts available)
            try:
                if not pygame.font.get_init():
                    pygame.font.init()
                font = pygame.font.SysFont('Arial', max(12, window_size[1] // 24))
                pct = int((y+1) * 100 / H)
                txt = font.render(f"{pct}%", True, (255,255,255))
                # draw subtle background for legibility
                rect = txt.get_rect(topleft=(8,8))
                bg = pygame.Surface((rect.width+6, rect.height+4), pygame.SRCALPHA)
                bg.fill((0,0,0,120))
                screen.blit(bg, (6,6))
                screen.blit(txt, (9,8))
            except Exception:
                # if fonts fail, silently continue
                pass
            pygame.display.flip()

        return (np.clip(img, 0, 1) * 255).astype(np.uint8)
