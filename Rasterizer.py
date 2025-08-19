import os, pygame, numpy as np
from collections import defaultdict

from GraphicLibrary import Renderer
from OBJ_Loader import LoadObj
from Model import Model
from MathLibrary import LookAt
from Shaders import VertexShader
from Texture import Texture
from BMP_Writer import GenerateBmp

from custom_shaders import (
    RetroPlasmaShader, HalftoneToonShader, HologramShader,
    WaveVertexShader, GlowEdgeShader,
)

# ---------- Rutas base del proyecto ----------
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
OBJ_PATH   = os.path.join(BASE_DIR, "mayor", "mayorhamm.obj")
SHOOTS_DIR = os.path.join(BASE_DIR, "shoots")
BG_PATH    = os.path.join(BASE_DIR, "background.jpg")   

# ---------- Ventana / renderer ----------
width, height = 720, 480
pygame.init()
screen   = pygame.display.set_mode((width, height), pygame.SCALED)
clock    = pygame.time.Clock()
renderer = Renderer(screen)
renderer.primitiveType = 2
renderer.dirLight = np.array((0.5, 0.7, -1.0))

# ---------- Carga del background (opcional) ----------
bg_surf = None
if os.path.exists(BG_PATH):
    bg_surf = pygame.image.load(BG_PATH).convert()
    bg_surf = pygame.transform.smoothscale(bg_surf, (width, height))

# ---------- Carga de modelo y texturas ----------
vertices, uvs, normals, faces, mtl_map = LoadObj(OBJ_PATH)
textures = {mat: Texture(tex_path) for mat, tex_path in mtl_map.items()}

faces_by_mat = defaultdict(list)
for tri, mat in faces:
    faces_by_mat[mat].append(tri)

all_xyz = np.array([vertices[vi] for tris in faces_by_mat.values()
                                  for tri in tris for (vi, _, _) in tri])
centroid = all_xyz.mean(axis=0)

all_tris     = [tri for tris in faces_by_mat.values() for tri in tris]
base_texture = next(iter(textures.values())) if textures else None

shader_dict = {
    "RetroPlasma":  (VertexShader,     RetroPlasmaShader),
    "HalftoneToon": (VertexShader,     HalftoneToonShader),
    "Hologram":     (VertexShader,     HologramShader),
    "WaveGlow":     (WaveVertexShader, GlowEdgeShader),
}

def build_model(v_sh, f_sh, frag_params=None, vert_params=None):
    model = Model()
    buf = []
    for tri in all_tris:
        for vi, ti, ni in tri:
            x, y, z = vertices[vi] - centroid
            nx, ny, nz = normals[ni] if ni is not None else (0, 0, 1)
            u, v = uvs[ti] if ti is not None else (0, 0)
            buf += [x, y, z, nx, ny, nz, u, v]

    model.vertices        = buf
    model.vertexShader    = v_sh
    model.fragmentShader  = f_sh
    model.texture         = base_texture

    # encuadre agradable
    model.translation     = [0.0, -0.1, -3.2]
    model.scale           = [3.2, 3.2, 3.2]
    model.rotation        = [np.deg2rad(-12), np.deg2rad(28), 0.0]

    if frag_params: model.fragmentParams = frag_params
    if vert_params: model.vertexParams   = vert_params
    return model

# Cámara 3/4 con ligero picado
renderer.viewMatrix = LookAt(
    np.array((2.4, 1.4, 3.0)),
    np.array((0.0, 0.0, 0.0)),
    np.array((0.0, 1.0, 0.0))
)

os.makedirs(SHOOTS_DIR, exist_ok=True)

# ---- Utilidad: pinta el background en pantalla y en frameBuffer ----
def paint_background():
    if bg_surf is None:
        return
    # 1) pantalla (orientación de pygame)
    screen.blit(bg_surf, (0, 0))

    # 2) frameBuffer del renderer (orientación y, invertida)
    arr = pygame.surfarray.array3d(bg_surf)  # shape: (W, H, 3), uint8
    # frameBuffer es [x][y] con y "al revés" (glPoint usa height-1-y)
    for x in range(width):
        col = arr[x]  # (H, 3)
        for y_screen in range(height):
            y_fb = height - 1 - y_screen
            r, g, b = col[y_screen]
            renderer.frameBuffer[x][y_fb] = [int(r), int(g), int(b)]
    # zBuffer ya está en +inf por glClear(), así que tus modelos se dibujan encima

# Renderiza un shader a la vez y guarda BMP en /shoots
for name, (v_sh, f_sh) in shader_dict.items():
    frag_params, vert_params = {}, {}

    if f_sh is RetroPlasmaShader:
        frag_params.update(dict(speed=0.8, scale=60, palette="rainbow"))
    elif f_sh is HalftoneToonShader:
        frag_params.update(dict(levels=4, ambient=0.18, dotSize=4))
    elif f_sh is HologramShader:
        frag_params.update(dict(rimIntensity=1.2))
    elif f_sh is GlowEdgeShader:
        frag_params.update(dict(intensity=1.3))

    if v_sh is WaveVertexShader:
        vert_params.update(dict(amplitude=0.18, wavelength=2.6, speed=0.8))

    renderer.models = [build_model(v_sh, f_sh, frag_params, vert_params)]

    renderer.glClear()
    paint_background()          # ← pinta el fondo antes de renderizar el modelo
    renderer.glRender()
    pygame.display.flip()

    out_path = os.path.join(SHOOTS_DIR, f"{name}.bmp")
    GenerateBmp(out_path, width, height, 3, renderer.frameBuffer)
    print(f"✓ guardado {out_path}")

pygame.time.wait(600)
pygame.quit()
