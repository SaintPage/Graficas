import numpy as np
from gl import Renderer
from figures import Sphere
from material import Material
from lights import AmbientLight, DirectionalLight

if __name__ == "__main__":
    W, H = 800, 600
    rt = Renderer(W, H, fov=60)

    # Luces
    rt.lights = [
        AmbientLight(color=(1,1,1), intensity=0.15),
        DirectionalLight(color=(1,1,1), intensity=0.9, direction=(-1,-1,-1)),
        DirectionalLight(color=(1,0.95,0.9), intensity=0.6, direction=(0,-1,-0.3)),
    ]

    # Materiales (difusos distintos)
    gold     = Material(diffuse=(1.0, 0.85, 0.2),  kd=0.9, ks=0.8, ka=0.1, shininess=96)
    plastic  = Material(diffuse=(0.15, 0.4, 1.0),  kd=0.9, ks=0.3, ka=0.05, shininess=32)
    rubber   = Material(diffuse=(0.2, 0.2, 0.2),   kd=0.8, ks=0.1, ka=0.1, shininess=8)
    marble   = Material(diffuse=(0.9, 0.9, 0.95),  kd=0.85,ks=0.5, ka=0.1, shininess=64)

    # Escena (elige tu figura a base de esferas)
    rt.objects = [
        Sphere(center=(-1.2,  0.0, -4.0), radius=0.9, material=gold),
        Sphere(center=( 1.2,  0.2, -3.0), radius=0.7, material=plastic),
        Sphere(center=( 0.0, -0.9, -3.5), radius=0.6, material=rubber),
        Sphere(center=( 0.3,  1.0, -5.0), radius=1.2, material=marble),
    ]

    rt.render()
    rt.saveBMP("output.bmp")
    print("Render listo")
