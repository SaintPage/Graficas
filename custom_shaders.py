import numpy as np


# 1. RetroPlasmaShader (Fragment) — NUEVO, reemplaza ChromeRainbow


"""Un shader inspirado en las demoscene plasma‑effects de los 90:
   combina dos ondas seno desplazadas para generar franjas de color en
   tiempo real.  El resultado recuerda al metal líquido arcoíris, pero
   con animación propia que no depende de la normal.
   Parámetros:
      * speed   : velocidad de la animación (1.0 ≈ 1 ciclo/seg)
      * scale   : frecuencia espacial; menor = franjas más anchas
      * palette : 'rainbow' (default) o 'sunset' (gradiente rojo‑amarillo)
"""

def RetroPlasmaShader(**kw):
    """Plasma arcoíris animado usando dos senos 2‑D."""
    x_pix = kw.get("x", 0)
    y_pix = kw.get("y", 0)
    time  = kw.get("time", 0.0)
    speed = kw.get("speed", 1.0)
    scale = kw.get("scale", 60.0)

    v = (
        np.sin((x_pix + time*speed*40) / scale) +
        np.sin((x_pix + y_pix + time*speed*30) / scale)
    ) * 0.5 + 0.5

    palette = kw.get("palette", "rainbow")
    if palette == "sunset":
        r = v
        g = v*0.5
        b = (1-v)*0.2
    else:
        r, g, b = hsv_to_rgb(v, 1, 1)

    if "verts" in kw:
        A, B, C = kw["verts"]
        u_b, v_b, w_b = kw["baryCoords"]
        N = u_b*np.array(A[3:6]) + v_b*np.array(B[3:6]) + w_b*np.array(C[3:6])
        N /= np.linalg.norm(N)+1e-8
        diff = max(0, N.dot(-np.array(kw["dirLight"])))
        r, g, b = np.array((r, g, b)) * (0.3 + 0.7*diff)

    return tuple((np.clip([r, g, b], 0, 1)*255).astype(int))

# helper HSV→RGB (re‑insertado)

# helper HSV→RGB
def hsv_to_rgb(h, s, v):
    i = int(h * 6)
    f = h * 6 - i
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)
    i %= 6
    if i == 0:  return v, t, p
    if i == 1:  return q, v, p
    if i == 2:  return p, v, t
    if i == 3:  return p, q, v
    if i == 4:  return t, p, v
    return v, p, q



# 2. HalftoneToonShader (Fragment)

def HalftoneToonShader(**kw):
    """Posterizado + patrón de puntos (halftone) en zonas medias."""
    A, B, C = kw["verts"]
    bu, bv, bw = kw["baryCoords"]
    L = np.array(kw["dirLight"], dtype=float)

    # Normal + difusa
    NA, NB, NC = np.array(A[3:6]), np.array(B[3:6]), np.array(C[3:6])
    N = bu*NA + bv*NB + bw*NC;  N /= np.linalg.norm(N)+1e-8
    diff = max(0, N.dot(-L))

    # Posterización de la intensidad
    levels = kw.get("levels", 4)
    diff_q = np.floor(diff * levels) / (levels-1)

    # Color base (desde textura o constante)
    if (T:=kw.get("texture")) is not None:
        r, g, b = T.getColor(kw.get("u"), kw.get("v"))
    else:
        r, g, b = kw.get("baseColor", (1,1,1))

    color = np.array((r, g, b)) * (kw.get("ambient",0.2) + diff_q*(1-kw.get("ambient",0.2)))

    # Halftone pattern — usa coords de pantalla si están en kw
    x_pix = kw.get("x", 0); y_pix = kw.get("y", 0)
    dot_size = kw.get("dotSize", 4)
    mask = ((x_pix//dot_size)+(y_pix//dot_size))%2  # tablero
    mid_band = diff_q > 0.3 and diff_q < 0.7
    if mid_band and mask:
        color *= 0.5  # oscurece puntos alternos

    return tuple((color*255).astype(int))


# 3. HologramShader (Fragment)

def HologramShader(**kw):
    """Efecto holograma con bordes brillantes, scanlines y flicker animado."""
    A, B, C = kw["verts"]
    bu, bv, bw = kw["baryCoords"]
    time = kw.get("time", 0)

    # Normal + Rim light
    NA, NB, NC = np.array(A[3:6]), np.array(B[3:6]), np.array(C[3:6])
    N = bu*NA + bv*NB + bw*NC;  N /= np.linalg.norm(N)+1e-8
    V = np.array((0,0,1))
    rim = (1 - max(0, N.dot(V))) ** 2

    # Color base (azul‑cyan)
    base_color = np.array((0.0, 0.8, 1.0))

    # Scanlines: alterna brillo según y‑pixel
    y_pix = kw.get("y",0); scan_strength = 0.15
    scan_factor = 1 - scan_strength*((y_pix+ int(time*120))%2)

    # Flicker global (ruido seno)
    flicker = 0.85 + 0.15*np.sin(time*50)

    color = base_color * flicker * scan_factor + rim*kw.get("rimIntensity",1)
    color = np.clip(color, 0, 1)
    return tuple((color*255).astype(int))


# 4. WaveVertexShader (Vertex)  — reemplaza Twist


def WaveVertexShader(vertex, **kw):
    """Ondea la malla como si viajara una ola senoidal a lo largo del eje X.
    Ideal para darle "latido" o vibración suave a un personaje sin romper
    su silueta.  Se puede animar con *time* y controlar la amplitud/longitud.
    """
    time       = kw.get("time", 0.0)  # segundos
    amplitude  = kw.get("amplitude", 0.15)  # desplazamiento máximo
    wavelength = kw.get("wavelength", 2.5)  # número de ondas a lo largo de X
    speed      = kw.get("speed", 1.0)       # Hz de avance de la ola

    x, y, z = vertex[:3]

    # Desplazamiento vertical en Y basado en sinusoide
    disp = amplitude * np.sin(2*np.pi*(x/wavelength + time*speed))
    y += disp

    M = kw["modelMatrix"]
    vt = M @ np.array([x, y, z, 1.0])
    return [vt[0]/vt[3], vt[1]/vt[3], vt[2]/vt[3]]

# 5. GlowEdgeShader (Fragment)

def GlowEdgeShader(**kw):
    """Iluminación tipo *Tron*: interior oscuro, bordes con halo brillante
    y color que cicla en el arcoíris según el tiempo.
    Ideal para combinar con TwistVertexShader (TwistGlow).
    """
    A, B, C     = kw["verts"]
    u_bar, v_bar, w_bar = kw["baryCoords"]
    time        = kw.get("time", 0)

    # Normal interpolada y rim‑light
    NA, NB, NC = np.array(A[3:6]), np.array(B[3:6]), np.array(C[3:6])
    N   = u_bar*NA + v_bar*NB + w_bar*NC
    N  /= np.linalg.norm(N)+1e-8
    V   = np.array((0,0,1))
    rim = (1 - max(0, N.dot(V))) ** 3            # halo fino

    # Color que recorre el espectro cada 6 s
    hue = (time*60) % 360
    r, g, b = hsv_to_rgb(hue/360, 1, 1)

    glow  = np.array((r, g, b)) * rim * kw.get("intensity", 1.2)
    base  = np.array((0.05, 0.05, 0.05))         # cuerpo casi negro
    color = np.clip(base + glow, 0, 1)
    return tuple((color*255).astype(int))


def NormalMappedPhongShader(**kw):
    """
    Phong con normal mapping (o bump si se pasa height map).
    Usa:
        - texture: albedo (opcional)
        - normalTex: normal map en espacio tangente (RGB en [0,1])
        - heightTex: height map (grises) si no hay normalTex → bump
    Parámetros opcionales:
        ambient=0.15, kd=1.0, ks=0.35, shininess=64, bumpScale=1.0
    """
    A, B, C = kw["verts"]
    u_b, v_b, w_b = kw["baryCoords"]
    u, v = kw.get("u", 0), kw.get("v", 0)
    L = np.array(kw["dirLight"], dtype=float)

    # Normal geométrica interpolada
    NA, NB, NC = np.array(A[3:6]), np.array(B[3:6]), np.array(C[3:6])
    N = u_b*NA + v_b*NB + w_b*NC
    N = N / (np.linalg.norm(N) + 1e-8)

    # Base de color (albedo)
    if (T := kw.get("texture")) is not None:
        r, g, b = T.getColor(u, v)
        albedo = np.array((r, g, b))
    else:
        albedo = np.array((1.0, 1.0, 1.0))

    # --- Tangent space (simple, sin tangentes de malla) ---
    # Construimos T y B ortogonales a N con un "up" estable
    up = np.array((0.0, 1.0, 0.0)) if abs(N[1]) < 0.9 else np.array((1.0, 0.0, 0.0))
    T = np.cross(up, N);  T /= np.linalg.norm(T) + 1e-8
    B = np.cross(N, T)

    # --- Normal map o Bump map ---
    normalTex = kw.get("normalTex", None)
    heightTex = kw.get("heightTex", None)
    if normalTex is not None:
        rn, gn, bn = normalTex.getColor(u, v)          # [0,1]
        n_t = np.array((rn*2-1, gn*2-1, bn*2-1))       # [-1,1]
    elif heightTex is not None:
        # Bump: gradiente numérico en UV
        eps = 1.0 / 1024.0
        def grayAt(uu, vv):
            rr, gg, bb = heightTex.getColor(uu, vv)
            return 0.299*rr + 0.587*gg + 0.114*bb
        h  = grayAt(u, v)
        hx = grayAt(u+eps, v) - h
        hy = grayAt(u, v+eps) - h
        scale = kw.get("bumpScale", 1.0)
        n_t = np.array((-scale*hx, -scale*hy, 1.0))
        n_t /= np.linalg.norm(n_t) + 1e-8
    else:
        n_t = np.array((0.0, 0.0, 1.0))                # sin mapa → normal original

    # Tangent → espacio "mundo/vista"
    N = T*n_t[0] + B*n_t[1] + N*n_t[2]
    N /= np.linalg.norm(N) + 1e-8

    # Iluminación Phong (Blinn)
    diff = max(0.0, N.dot(-L))
    V = np.array((0, 0, 1), dtype=float)
    H = (-L + V); H /= np.linalg.norm(H) + 1e-8
    spec = max(0.0, N.dot(H)) ** kw.get("shininess", 64)

    ambient = kw.get("ambient", 0.15)
    kd = kw.get("kd", 1.0)
    ks = kw.get("ks", 0.35)
    color = albedo * (ambient + kd*diff) + ks*spec
    color = np.clip(color, 0, 1)
    return tuple((color*255).astype(int))

def NeonFresnelShader(**kw):
    """
    Toon + borde neón:
      - Interior: difusa cuantizada (toon).
      - Borde: rim/fresnel con color neón y contorno por baricéntricas.
    Params:
      levels=5, ambient=0.12,
      neonColor=(0.2,0.9,1.0), neonIntensity=1.5,
      pulseSpeed=4.0, fresnelPow=3.0,
      outlineIntensity=1.0, edgeWidth=0.08
    """
    A, B, C = kw["verts"]
    u_b, v_b, w_b = kw["baryCoords"]
    L = np.array(kw["dirLight"], dtype=float)
    time = kw.get("time", 0.0)

    # Normal interpolada
    NA, NB, NC = np.array(A[3:6]), np.array(B[3:6]), np.array(C[3:6])
    N = u_b*NA + v_b*NB + w_b*NC
    N /= np.linalg.norm(N) + 1e-8

    # Luz difusa → cuantizada (toon)
    diff = max(0.0, N.dot(-L))
    levels = kw.get("levels", 5)
    diff_q = np.floor(diff * levels) / max(1, (levels - 1))

    # Color base: textura si existe, si no baseColor
    if (T := kw.get("texture")) is not None:
        r, g, b = T.getColor(kw.get("u"), kw.get("v"))
        base = np.array((r, g, b))
    else:
        base = np.array(kw.get("baseColor", (1.0, 1.0, 1.0)))

    ambient = kw.get("ambient", 0.12)
    body = base * (ambient + diff_q * (1 - ambient))

    # Fresnel / rim
    V = np.array((0, 0, 1), dtype=float)
    fres = (1.0 - max(0.0, N.dot(V))) ** kw.get("fresnelPow", 3.0)
    neonColor = np.array(kw.get("neonColor", (0.2, 0.9, 1.0)))
    pulse = 0.6 + 0.4 * np.sin(time * kw.get("pulseSpeed", 4.0))
    rim = neonColor * fres * kw.get("neonIntensity", 1.5) * pulse

    # Contorno por baricéntricas (bordes del triángulo)
    edgeWidth = kw.get("edgeWidth", 0.08)
    edge = np.clip(np.minimum.reduce([u_b, v_b, w_b]) / edgeWidth, 0.0, 1.0)
    outlineMask = 1.0 - edge
    outline = neonColor * outlineMask * kw.get("outlineIntensity", 1.0)

    color = np.clip(body + rim + outline, 0, 1)
    return tuple((color * 255).astype(int))
