import os, pygame, numpy as np
from collections import defaultdict

from GraphicLibrary import Renderer
from OBJ_Loader import LoadObj
from Model import Model
from MathLibrary import LookAt, RotationMatrix
from Shaders import VertexShader, GouraudShader        # VertexShader base
from Texture import Texture
from BMP_Writer import GenerateBmp


from custom_shaders import (
    RetroPlasmaShader,   # ← nuevo shader #1
    HalftoneToonShader,
    HologramShader,
    WaveVertexShader,    # el vertex que ondula
    GlowEdgeShader       # el fragment para WaveGlow
)



# Configuración de ventana

width, height = 720, 480
pygame.init()
screen = pygame.display.set_mode((width, height), pygame.SCALED)
clock = pygame.time.Clock()
renderer = Renderer(screen)
renderer.primitiveType = 2                # TRIANGLES 


# Carga del modelo y texturas

obj_path = "mayor/mayorhamm.obj"          # ← NUEVO
vertices, uvs, normals, faces, mtl_map = LoadObj(obj_path)

obj_dir = os.path.dirname(obj_path)       # ← NUEVO
textures = {mat: Texture(fname) for mat, fname in mtl_map.items()}


# Agrupamos caras por material (solo usaremos el primero)
faces_by_mat = defaultdict(list)
for tri, mat in faces:
    faces_by_mat[mat].append(tri)

all_xyz = np.array(
    [vertices[vi] for tris in faces_by_mat.values()
                   for tri in tris for (vi, _, _) in tri])
centroid = all_xyz.mean(axis=0)

shader_dict = {
    "RetroPlasma"  : (VertexShader,   RetroPlasmaShader),   # shader #1
    "HalftoneToon" : (VertexShader,   HalftoneToonShader),  # shader #2
    "Hologram"     : (VertexShader,   HologramShader),      # shader #3
    "WaveGlow"     : (WaveVertexShader, GlowEdgeShader)     # shader #4
}

# Usaremos TODAS las caras y la primera textura
all_tris      = [tri for tris in faces_by_mat.values() for tri in tris]
base_texture  = next(iter(textures.values())) if textures else None



def build_model(v_sh, f_sh):
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
    model.translation     = [0, 0, -2.2]   # ↙ Más lejos
    model.scale           = [3, 3, 3]    # ↗ Más grande
    import numpy as np
    model.rotation    = [np.deg2rad(20), np.deg2rad(25), 0]

    return model



if not os.path.exists("shoots"):
    os.makedirs("shoots")

for name, (v_sh, f_sh) in shader_dict.items():          # ← línea 1
    # 4 espacios a partir de aquí  ↓↓↓↓
    renderer.models = [build_model(v_sh, f_sh)]

    # cámara tres-cuartos + ligero picado
    renderer.viewMatrix = LookAt(
        np.array((3, 2, 3.0)),   # posición de la cámara
        np.array((0.0, 0.0, 0.0)),   # mira al origen
        np.array((0.0, 1.0, 0.0))
    )
    renderer.glClear()
    angle_x = np.deg2rad(30)          # 10° picado
    renderer.viewMatrix = LookAt(
        np.array((0,  0, 3)),     # ojo
        np.array((0, -0.5, 0)),   # mira ligeramente abajo
        np.array((0,  1, 0))
)
    renderer.glRender()
    pygame.display.flip()           # para ver el resultado en la ventana

    # guarda el framebuffer en /shoots/
    fname = os.path.join("shoots", f"{name}.bmp")
    GenerateBmp(fname, width, height, 3, renderer.frameBuffer)
    print(f"✓ guardado {fname}")


pygame.time.wait(1500)   
pygame.quit()

