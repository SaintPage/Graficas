# Raytracer2025.py
import os
import numpy as np
from lights import PointLight, DirectionalLight  
from figures import Material, Sphere
from gl import Raytracer

def main():
    width, height = 800, 450
    rt = Raytracer(width, height)

    # -------- materiales --------
    matte_red    = Material((0.90, 0.20, 0.25), ka=0.12, kd=1.0, ks=0.10, shininess=16)
    matte_green  = Material((0.25, 0.90, 0.35), ka=0.12, kd=1.0, ks=0.10, shininess=16)
    plastic_blue = Material((0.20, 0.45, 1.00), ka=0.10, kd=1.0, ks=0.35, shininess=64)
    gold         = Material((1.00, 0.85, 0.35), ka=0.12, kd=0.9, ks=0.6,  shininess=96)
    ivory        = Material((0.95, 0.92, 0.85), ka=0.15, kd=1.0, ks=0.25, shininess=32)

    # -------- escena (esferas) --------
    spheres = [
        Sphere(np.array((-1.6, -0.2, -4.5)), 0.8, matte_red),
        Sphere(np.array(( 0.3, -0.5, -3.2)), 0.5, gold),
        Sphere(np.array(( 1.7,  0.1, -5.0)), 0.9, plastic_blue),
        Sphere(np.array((-0.2,  0.9, -6.0)), 1.1, ivory),
        # "piso" como esfera enorme
        Sphere(np.array((0.0, -5001.0, 0.0)), 5000.0, matte_green),
    ]
    rt.set_scene(spheres)

    # -------- luces --------
    lights = [
        PointLight(np.array(( 2.5, 3.5,  1.5)), color=(1.0, 0.95, 0.95), intensity=2.0, att_a=0.02, att_b=0.01),
        DirectionalLight(direction=np.array((0.7, -1.2, 0.6)), color=(0.6, 0.7, 1.0), intensity=0.5),
    ]
    rt.set_lights(lights)

    # -------- cámara --------
    rt.set_camera(
        eye=(0.0, 0.8, 1.8),
        target=(0.0, 0.2, -4.0),
        up=(0.0, 1.0, 0.0),
        fov_deg=60
    )

    # -------- render --------
    rt.render()

    out = os.path.join(os.path.dirname(__file__), "output.bmp")
    rt.save(out)
    print(f"✓ Imagen guardada en {out}")

if __name__ == "__main__":
    main()
