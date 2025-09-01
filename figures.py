# figures.py
from dataclasses import dataclass
import numpy as np

@dataclass
class Material:
    color: tuple               # (r,g,b) en [0..1]
    ka: float = 0.1            # ambient
    kd: float = 1.0            # diffuse
    ks: float = 0.25           # specular
    shininess: float = 32.0    # exponente

@dataclass
class Sphere:
    center: np.ndarray
    radius: float
    material: Material
