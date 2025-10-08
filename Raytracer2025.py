import os, sys
import numpy as np
from gl import Renderer
from figures import Plane, Disk, Triangle, AABB, Cylinder, Torus
from lights import AmbientLight, DirectionalLight
from lights import PointLight
from material import Material, OPAQUE, REFLECTIVE, TRANSPARENT

NO_GUI = ('--nogui' in sys.argv) or os.environ.get('RAY_NO_GUI') == '1'
PREVIEW = ('--preview' in sys.argv) or os.environ.get('RAY_PREVIEW') == '1'
if PREVIEW:
    W_PREV, H_PREV = 640, 360
else:
    W_PREV, H_PREV = 960, 540

try:
    ENV_W = int(os.environ.get('RAY_WIDTH')) if os.environ.get('RAY_WIDTH') else None
    ENV_H = int(os.environ.get('RAY_HEIGHT')) if os.environ.get('RAY_HEIGHT') else None
    ENV_SSAA = int(os.environ.get('RAY_SSAA')) if os.environ.get('RAY_SSAA') else None
except Exception:
    ENV_W = ENV_H = ENV_SSAA = None

if not NO_GUI:
    import pygame
    pygame.init()
    width, height = W_PREV, H_PREV
    screen = pygame.display.set_mode((width, height), pygame.SCALED)
    clock = pygame.time.Clock()
else:
    width, height = W_PREV, H_PREV

# Resolve desired resolution / SSAA: PREVIEW takes precedence, then env overrides, then defaults
final_width = width
final_height = height
final_ssaa = 1
if not PREVIEW:
    if ENV_W and ENV_H:
        final_width, final_height = ENV_W, ENV_H
    if ENV_SSAA:
        final_ssaa = max(1, ENV_SSAA)

# Instantiate renderer with chosen params
print(f"Renderer resolution: {final_width}x{final_height}, SSAA={final_ssaa}")
rend = Renderer(final_width, final_height, fov=60, bg_color=(0.02, 0.02, 0.02), ssaa=final_ssaa)

# --- materiales/escena/luces (igual que antes) ---
# Base wall materials (different colors for a room look)
# Palette 2: softer room colors (provided as RGB floats)
back_wall  = Material(diffuse=(0.941,0.941,0.929), ka=0.10, kd=0.85, ks=0.12, shininess=12, matType=OPAQUE)
left_wall  = Material(diffuse=(0.871,0.812,0.725), ka=0.08, kd=0.9, ks=0.05, shininess=8, matType=OPAQUE)  # warm/beige
right_wall = Material(diffuse=(0.784,0.851,0.922), ka=0.08, kd=0.9, ks=0.05, shininess=8, matType=OPAQUE)  # cool/blue
ceiling    = Material(diffuse=(0.235,0.235,0.251), ka=0.06, kd=0.85, ks=0.02, shininess=4, matType=OPAQUE)  # darker ceiling
# piso con algo de reflectividad para ver reflejos
floor = Material(diffuse=(0.75,0.65,0.55), ka=0.05, kd=0.7, ks=0.2, shininess=8, matType=REFLECTIVE, reflectivity=0.45)
obj1  = Material(diffuse=(0.95,0.75,0.35), ka=0.08, kd=0.9, ks=0.25, shininess=32, matType=OPAQUE)  # warm wood
obj2  = Material(diffuse=(0.18,0.28,0.75), ka=0.04, kd=0.7, ks=0.25, shininess=48, matType=REFLECTIVE, reflectivity=0.45)  # blue reflective cube
objTri= Material(diffuse=(0.25,0.85,0.55), ka=0.08, kd=0.9, ks=0.2, shininess=24, matType=OPAQUE)  # green triangle
obj3  = Material(diffuse=(0.9,0.9,0.95), ka=0.02, kd=0.35, ks=0.28, shininess=128, matType=TRANSPARENT, ior=1.8)
obj4  = Material(diffuse=(0.5,0.35,0.2), ka=0.05, kd=0.8, ks=0.1, shininess=8, matType=OPAQUE)  # small floor disk

# Crear materiales adicionales para las nuevas figuras
cylinder_opaque = Material(diffuse=(0.8,0.4,0.2), ka=0.08, kd=0.9, ks=0.15, shininess=16, matType=OPAQUE)
cylinder_reflective = Material(diffuse=(0.7,0.7,0.9), ka=0.05, kd=0.6, ks=0.35, shininess=64, matType=REFLECTIVE, reflectivity=0.6)
cylinder_transparent = Material(diffuse=(0.9,0.95,0.9), ka=0.02, kd=0.3, ks=0.4, shininess=128, matType=TRANSPARENT, ior=1.5)

torus_opaque = Material(diffuse=(0.9,0.2,0.4), ka=0.08, kd=0.9, ks=0.2, shininess=32, matType=OPAQUE)
torus_reflective = Material(diffuse=(0.3,0.8,0.3), ka=0.05, kd=0.6, ks=0.4, shininess=80, matType=REFLECTIVE, reflectivity=0.7)
torus_transparent = Material(diffuse=(0.8,0.9,1.0), ka=0.03, kd=0.25, ks=0.45, shininess=96, matType=TRANSPARENT, ior=1.4)

# Escena de demostración LAB 8 - Solo las nuevas figuras: Cilindros y Torus
rend.objects = []
rend.objects += [
    # Cuarto básico (piso, techo, paredes)
    Plane(position=( 0.0, -2.0, -8.0), normal=( 0, 1, 0), material=floor),   # piso
    Plane(position=( 0.0,  2.0, -8.0), normal=( 0,-1, 0), material=ceiling ),   # techo
    Plane(position=( 0.0,  0.0,-15.0), normal=( 0, 0, 1), material=back_wall ),   # pared fondo
    Plane(position=(-4.0,  0.0, -8.0), normal=( 1, 0, 0), material=left_wall ),   # izquierda
    Plane(position=( 4.0,  0.0, -8.0), normal=(-1, 0, 0), material=right_wall ),   # derecha
    
    # CILINDROS - 3 instancias con diferentes materiales
    # Cilindro 1: Opaco, vertical en el lado izquierdo
    Cylinder(center=(-2.5, -0.5, -10.0), axis=(0, 1, 0), radius=0.4, height=1.8, material=cylinder_opaque),
    
    # Cilindro 2: Reflectivo, horizontal en el centro
    Cylinder(center=(0.0, 0.3, -9.0), axis=(1, 0, 0), radius=0.3, height=2.0, material=cylinder_reflective),
    
    # Cilindro 3: Transparente, inclinado en el lado derecho
    Cylinder(center=(2.2, -0.2, -11.0), axis=(0.3, 1, 0.2), radius=0.35, height=1.5, material=cylinder_transparent),
    
    # TORUS - 3 instancias con diferentes materiales
    # Torus 1: Opaco, grande en el fondo izquierdo
    Torus(center=(-1.8, 0.5, -13.0), axis=(0, 0, 1), major_radius=0.8, minor_radius=0.25, material=torus_opaque),
    
    # Torus 2: Reflectivo, mediano en el centro-derecha
    Torus(center=(1.5, -0.3, -9.5), axis=(1, 0.5, 0), major_radius=0.6, minor_radius=0.18, material=torus_reflective),
    
    # Torus 3: Transparente, pequeño flotando
    Torus(center=(0.3, 1.0, -8.5), axis=(0, 1, 0), major_radius=0.5, minor_radius=0.15, material=torus_transparent),
]

rend.lights = [
    AmbientLight(color=(1,1,1), intensity=0.18),
    # warm ceiling light
    DirectionalLight(color=(1.0,0.95,0.9), intensity=1.0, direction=(0.0,-1.0,-0.1)),
    DirectionalLight(color=(0.8,0.9,1.0), intensity=0.6, direction=(-0.6,-0.4,-0.2)),
    # Point lamp in the ceiling to create a local lamp illumination
    PointLight(color=(1.0,0.95,0.9), intensity=2.8, position=(0.0, 1.0, -7.5), range=4.0, attenuation=(1.0,0.35,0.12)),
]

if hasattr(rend, "glRender"):
    def _row_cb(j):
        if j % 20 == 0:
            print(f"Rendered row {j}/{rend.height}")
    # Mover cámara un poco hacia atrás para encuadre tipo habitación
    rend.camPos = np.array((0.0, 0.0, 1.2), dtype=float)
    rend.glRender()
else:
    def _row_cb(j):
        if j % 20 == 0:
            print(f"Rendered row {j}/{rend.height}")
    rend.camPos = np.array((0.0, 0.0, 1.2), dtype=float)
    rend.render(row_callback=_row_cb)

# Guardar resultado en BMP para inspeccionar
try:
    rend.saveBMP("output.bmp")
    print("Saved output.bmp")
except Exception as e:
    print("Failed to save output.bmp:", e)

if not NO_GUI:
    # Mostrar framebuffer en Pygame
    surf = pygame.surfarray.make_surface(np.flipud(rend.framebuffer).swapaxes(0,1))
    screen.blit(pygame.transform.scale(surf, screen.get_size()), (0,0))
    pygame.display.flip()

    running = True
    while running:
        clock.tick(60)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
    pygame.quit()
else:
    print("Headless mode: rendered and saved output.bmp")
