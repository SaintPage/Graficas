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


