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

# Rutas 
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
BG_PATH    = os.path.join(BASE_DIR, "background.jpg")
SHOOTS_DIR = os.path.join(BASE_DIR, "shoots")

# Ventana / renderer
width, height = 1280, 720
pygame.init()
screen   = pygame.display.set_mode((width, height), pygame.SCALED)
clock    = pygame.time.Clock()
renderer = Renderer(screen)
renderer.primitiveType = 2
renderer.dirLight = np.array((0.5, 0.7, -1.0))

# Background 
bg_surf = None
if os.path.exists(BG_PATH):
    bg_surf = pygame.image.load(BG_PATH).convert()
    bg_surf = pygame.transform.smoothscale(bg_surf, (width, height))

def paint_background():
    if bg_surf is None:
        return
    screen.blit(bg_surf, (0, 0))
    arr = pygame.surfarray.array3d(bg_surf)  # (W,H,3)
    for x in range(width):
        col = arr[x]
        for y_scr in range(height):
            y_fb = height - 1 - y_scr
            r, g, b = map(int, col[y_scr])
            renderer.frameBuffer[x][y_fb] = [r, g, b]

#  Helper: crea Model() desde un .obj (respeta .mtl) 
def build_models_from_obj(obj_path, v_sh, f_sh,
                          translation=(0,0,-6), rotation_deg=(0,0,0), scale=(1,1,1),
                          frag_params=None, vert_params=None,
                          normalize=True, target_radius=1.2):
    """Crea 1+ Model() (uno por material) respetando texturas del .mtl.
       Si normalize=True, ajusta cada modelo a un radio world común."""
    models = []
    vertices, uvs, normals, faces, mtl_map = LoadObj(obj_path)
    textures = {mat: Texture(tex_path) for mat, tex_path in mtl_map.items()}

    faces_by_mat = defaultdict(list)
    for tri, mat in faces:
        faces_by_mat[mat].append(tri)

    # centroide + radio para normalizar tamaños 
    all_xyz = np.array([vertices[vi]
                        for tris in faces_by_mat.values()
                        for tri in tris
                        for (vi, _, _) in tri], dtype=float)
    if len(all_xyz) == 0:
        return models

    centroid = all_xyz.mean(axis=0)
    radius   = np.max(np.linalg.norm(all_xyz - centroid, axis=1))
    unit_mul = (target_radius / max(radius, 1e-6)) if normalize else 1.0
    scale_mul = np.array(scale, dtype=float) * unit_mul

    for mat, tris in faces_by_mat.items():
        buf = []
        for tri in tris:
            for vi, ti, ni in tri:
                x, y, z = vertices[vi] - centroid      # center
                x, y, z = x*scale_mul[0], y*scale_mul[1], z*scale_mul[2]
                nx, ny, nz = normals[ni] if ni is not None else (0, 0, 1)
                u, v = uvs[ti] if ti is not None else (0, 0)
                buf += [x, y, z, nx, ny, nz, u, v]

        m = Model()
        m.vertices        = buf
        m.vertexShader    = v_sh
        m.fragmentShader  = f_sh
        m.texture         = textures.get(mat)

        m.translation     = list(translation)
        rx, ry, rz        = rotation_deg
        m.rotation        = [np.deg2rad(rx), np.deg2rad(ry), np.deg2rad(rz)]

        if frag_params: m.fragmentParams = frag_params.copy()
        if vert_params: m.vertexParams   = vert_params.copy()
        models.append(m)
    return models

SCENE = [
    # 1) Hamm 
    (os.path.join(BASE_DIR,"mayor","mayorhamm.obj"),
     (3.5,3.5,3.5), (-10.8, -0.50, -7.2), (-8,  25, 0),
     (VertexShader, RetroPlasmaShader),
     {"frag":{"speed":0.8,"scale":60,"palette":"rainbow"}}),

    # 2) Sonic 
    (os.path.join(BASE_DIR,"mayor","Sonic.obj"),
     (3.3,3.3,3.3), ( 0.2, -0.45, 2.4), (0, -18, 0),
     (VertexShader, HologramShader),
     {"frag":{"rimIntensity":1.2}}),
    
    # 3) Dragón
    (os.path.join(BASE_DIR,"mayor","Model.obj"),
     (8,8,8), (-0.3,  6.30, -6.8), (10, 12, 0),
     (VertexShader, HalftoneToonShader),
     {"frag":{"levels":4,"ambient":0.18,"dotSize":4}}),

    # 4) Humano — MÁS DERECHA y MÁS LEJOS
    (os.path.join(BASE_DIR,"mayor","zfull.obj"),
     (2.5,2.5,2.5), ( 10.6, -0.50, -7.5), (0, -90, 0),
     (WaveVertexShader, GlowEdgeShader),
     {"frag":{"intensity":1.15},
      "vert":{"amplitude":0.12,"wavelength":2.8,"speed":0.7}}),
]



# Construir y añadir modelos
renderer.models = []
for (obj_path, scale, trans, rot, (v_sh, f_sh), params) in SCENE:
    models = build_models_from_obj(
        obj_path, v_sh, f_sh,
        translation=trans, rotation_deg=rot, scale=scale,
        frag_params=params.get("frag", {}), vert_params=params.get("vert", {})
    )
    renderer.models.extend(models)

# Cámara 
renderer.viewMatrix = LookAt(
    np.array((0.0, 1.15, 6.1)),   # ojo más cerca (antes ~9.2)
    np.array((0.0,-0.05,-8.0)),   # mira un poco hacia abajo
    np.array((0.0, 1.0,  0.0))
)
# Luz lateral-alta agradable
renderer.dirLight = np.array((-0.25, 0.9, -0.35))

#  Render + captura 
os.makedirs(SHOOTS_DIR, exist_ok=True)
saved = False
running = True
while running:
    _ = clock.tick(60)
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

    renderer.glClear()
    paint_background()
    renderer.glRender()
    pygame.display.flip()

    if not saved:
        out = os.path.join(SHOOTS_DIR, "Scene.bmp")
        GenerateBmp(out, width, height, 3, renderer.frameBuffer)
        print(f"✓ guardado {out}")
        saved = True

pygame.quit()
