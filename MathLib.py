import numpy as np

def normalize(v):
    v = np.array(v, dtype=float)
    n = np.linalg.norm(v)
    return v if n == 0 else v / n

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

def reflectVector(normal, direction):
    """
    Refleja el vector `direction` alrededor de la normal `normal`.

    Convención:
      - `direction` es el vector de LLEGADA a la superficie (del punto hacia la luz).
      - Fórmula: R = 2*(N·L)*N - L
    """
    N = normalize(normal)
    L = normalize(direction)
    R = 2.0 * np.dot(N, L) * N - L
    return normalize(R)
