import os
import numpy as np

from gl import Renderer
from figures import Sphere
from lights import AmbientLight, DirectionalLight
from material import Material, OPAQUE, REFLECTIVE, TRANSPARENT

W, H = 1280, 720
BASE = os.path.dirname(os.path.abspath(__file__))

rt = Renderer(W, H, fov=60, bg_color=(0, 0, 0))
rt.load_envmap("map.jpg", yaw_deg=0, vflip=False, mode="latlong")


# Luces
rt.add_light(AmbientLight(color=[1,1,1], intensity=0.12))
rt.add_light(DirectionalLight(color=[1,1,1], intensity=1.1, direction=[-0.7, -1.0, -0.5]))

# Materiales
red   = Material(diffuse=(1.0, 0.15, 0.15), kd=0.9, ks=0.35, ka=0.1, shininess=64,  matType=OPAQUE)
yellow= Material(diffuse=(1.0, 0.9,  0.1 ), kd=0.9, ks=0.45, ka=0.1, shininess=96,  matType=OPAQUE)

mirror= Material(diffuse=(1,1,1),  matType=REFLECTIVE, reflectivity=0.95, ks=0.0, kd=0.0, ka=0.0)
gold  = Material(diffuse=(1.0, 0.75, 0.2), matType=REFLECTIVE, reflectivity=0.75, ks=0.2, kd=0.2, ka=0.05)

glass = Material(diffuse=(0.9, 0.95, 1.0), matType=TRANSPARENT, ior=1.5, ks=0.0, kd=0.0, ka=0.0)
water = Material(diffuse=(0.8, 0.9,  1.0), matType=TRANSPARENT, ior=1.33, ks=0.0, kd=0.0, ka=0.0)

# Esferas (2 opacas, 2 reflectivas, 2 transparentes)
rt.add(Sphere(center=(-3, -1.5, -5), radius=0.9, material=yellow))  # opaca
rt.add(Sphere(center=( 3, -1.5, -5), radius=0.9, material=red))     # opaca

rt.add(Sphere(center=( 0, -1.5, -5), radius=0.9, material=mirror))  # reflectiva
rt.add(Sphere(center=(-0,  1.3, -5), radius=0.9, material=gold))    # reflectiva

rt.add(Sphere(center=( 3,  0.8, -5), radius=0.9, material=glass))   # transparente
rt.add(Sphere(center=(-3,  0.8, -5), radius=0.9, material=water))   # transparente

rt.render()
rt.saveBMP("output.bmp")
print("✓ render listo: output.bmp")
