import numpy as np

def VertexShader(vertex, **kwargs):
    M = kwargs["modelMatrix"]
    vt = np.array([vertex[0], vertex[1], vertex[2], 1.0])
    vt = np.array(M @ vt).flatten()
    return [vt[0] / vt[3], vt[1] / vt[3], vt[2] / vt[3]]

def FlatShader(**kw):
    A, B, C = kw["verts"]
    bar_u, bar_v, bar_w = kw["baryCoords"]
    u_tex = kw.get("u")
    v_tex = kw.get("v")
    L = np.array(kw["dirLight"])
    T = kw.get("texture", None)
    ambient = 0.3
    nA = np.array([A[3], A[4], A[5]])
    nB = np.array([B[3], B[4], B[5]])
    nC = np.array([C[3], C[4], C[5]])
    N = (nA + nB + nC) / 3
    N = N / np.linalg.norm(N)
    diff = max(0, N.dot(-L))
    I = ambient + (1 - ambient) * diff
    if T:
        r, g, b = T.getColor(u_tex, v_tex)
        r, g, b = r * 255, g * 255, b * 255
    else:
        r = g = b = 255
    return (int(r * I), int(g * I), int(b * I))

def GouraudShader(**kw):
    A, B, C = kw["verts"]
    bar_u, bar_v, bar_w = kw["baryCoords"]
    u_tex = kw.get("u")
    v_tex = kw.get("v")
    L = np.array(kw["dirLight"])
    T = kw.get("texture", None)
    ambient = 0.3
    nA = np.array([A[3], A[4], A[5]])
    nB = np.array([B[3], B[4], B[5]])
    nC = np.array([C[3], C[4], C[5]])
    N = bar_u * nA + bar_v * nB + bar_w * nC
    N = N / np.linalg.norm(N)
    diff = max(0, N.dot(-L))
    I = ambient + (1 - ambient) * diff
    if T:
        r, g, b = T.getColor(u_tex, v_tex)
        r, g, b = r * 255, g * 255, b * 255
    else:
        r = g = b = 255
    return (int(r * I), int(g * I), int(b * I))


def MetallicShader(**kw):
   
    A, B, C = kw["verts"]
    bar_u, bar_v, bar_w = kw["baryCoords"]
    u_tex = kw.get("u")
    v_tex = kw.get("v")
    L = np.array(kw["dirLight"])
    T = kw.get("texture", None)

    # Parámetros ajustables
    ambient = kw.get("ambient", 0.1)
    diffuse_weight = kw.get("diffuseWeight", 0.6)
    specular_strength = kw.get("specularStrength", 0.8)
    shininess = kw.get("shininess", 50)

    # Interpolación de la normal (igual que FlatShader)
    nA = np.array([A[3], A[4], A[5]])
    nB = np.array([B[3], B[4], B[5]])
    nC = np.array([C[3], C[4], C[5]])
    N = bar_u * nA + bar_v * nB + bar_w * nC
    norm_N = np.linalg.norm(N)
    if norm_N != 0:
        N = N / norm_N

    # Difusa (obs: FlatShader usa -L para el dot)
    diff = max(0, N.dot(-L))

    # Dirección de vista por defecto (fallback). Si quieres pasar la vista real, habría que extender el pipeline.
    V = np.array((0, 0, 1))
    # Medio vector para Blinn-Phong: dirección hacia la luz es -L
    H = -L + V
    norm_H = np.linalg.norm(H)
    if norm_H != 0:
        H = H / norm_H

    spec = 0.0
    ndotH = max(0, N.dot(H))
    spec = ndotH ** shininess

    # Base gris a partir de la textura
    if T and u_tex is not None and v_tex is not None:
        r, g, b = T.getColor(u_tex, v_tex)
        gray = 0.299 * r + 0.587 * g + 0.114 * b
    else:
        gray = 0.5  # fallback

    # Composición: gris * (ambient + diffuse_weight * diff) + especular
    base = gray * (ambient + diffuse_weight * diff)
    color_val = base + specular_strength * spec

    # Clamp a [0,1]
    color_val = min(1.0, max(0.0, color_val))

    c = int(color_val * 255)
    return (c, c, c)