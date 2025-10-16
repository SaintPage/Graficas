import os, sys
import builtins


def _silent_print(*args, **kwargs):
    return None

# Only suppress print output when user requests it via --quiet or env RAY_QUIET=1
QUIET = ('--quiet' in sys.argv) or os.environ.get('RAY_QUIET') == '1'
if QUIET:
    builtins.print = _silent_print
    # also hide pygame support prompt when quiet
    os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import numpy as np
from gl import Renderer
from figures import Plane, Disk, Triangle, AABB, Cylinder, Torus, Cone, Ellipsoid, Sphere
from lights import AmbientLight, DirectionalLight
from lights import PointLight
from material import Material, OPAQUE, REFLECTIVE, TRANSPARENT

NO_GUI = ('--nogui' in sys.argv) or os.environ.get('RAY_NO_GUI') == '1'
PREVIEW = ('--preview' in sys.argv) or os.environ.get('RAY_PREVIEW') == '1'
LIVE = ('--live' in sys.argv) or os.environ.get('RAY_LIVE') == '1'
TINY = ('--tiny' in sys.argv) or os.environ.get('RAY_TINY') == '1'
PROGRESSIVE = ('--progressive' in sys.argv) or os.environ.get('RAY_PROGRESSIVE') == '1'
# window scale for pygame progressive preview: --scale N or RAY_SCALE env var
SCALE_ARG = None
for a in sys.argv:
    if a.startswith('--scale='):
        try:
            SCALE_ARG = int(a.split('=', 1)[1])
        except Exception:
            SCALE_ARG = None
# environment override
if os.environ.get('RAY_SCALE'):
    try:
        SCALE_ARG = int(os.environ.get('RAY_SCALE'))
    except Exception:
        pass
if PREVIEW:
    final_width, final_height, final_ssaa = 640, 360, 1
    print("")
else:
    final_width, final_height, final_ssaa = 960, 540, 1
    print(" ")

# tiny override for very fast smoke tests
if TINY:
    final_width, final_height, final_ssaa = 160, 90, 1
    print("⚡ MODO TINY: resolución mínima para pruebas rápidas")

# custom resolution override: --res=WIDTHxHEIGHT or env RAY_RES
RES_ARG = None
for a in sys.argv:
    if a.startswith('--res='):
        RES_ARG = a.split('=', 1)[1]
        break
if os.environ.get('RAY_RES'):
    RES_ARG = os.environ.get('RAY_RES')
if RES_ARG:
    try:
        w,h = RES_ARG.lower().split('x')
        w = int(w); h = int(h)
        # clamp to reasonable maximum to avoid accidental extremely long renders
        max_w, max_h = 1920, 1080
        w = max(16, min(max_w, w))
        h = max(16, min(max_h, h))
        final_width, final_height = w, h
        print(f"📐 Resolución personalizada activada: {final_width}x{final_height}")
    except Exception:
        print(f"[WARN] formato de --res inválido: {RES_ARG}; se ignora")

# Instantiate renderer with chosen params
print(f"Renderer resolution: {final_width}x{final_height}, SSAA={final_ssaa}")
rend = Renderer(final_width, final_height, fov=50, bg_color=(0.02, 0.02, 0.02), ssaa=final_ssaa)

# ENVIRONMENT MAP (5 puntos)
try:
    rend.load_envmap("map.jpg", yaw_deg=45.0, vflip=False)
    print(" Environment map loaded successfully")
except Exception as e:
    print(f" Environment map failed to load: {e}")
    print("Continuing without environment map...")


# Material 1: Mármol beige cálido (arquitectura) - Color base de la referencia
warm_marble = Material(diffuse=(0.92,0.89,0.82), ka=0.25, kd=0.8, ks=0.3, shininess=64, matType=REFLECTIVE, reflectivity=0.15)

# Material 2: Cristal translúcido con tinte cálido (esferas de la referencia)
translucent_glass = Material(diffuse=(0.95,0.92,0.88), ka=0.1, kd=0.2, ks=0.9, shininess=128, matType=TRANSPARENT, ior=1.4)

# Material 2b: Vidrio cristalino ultra-realista (para esfera derecha como en referencia)
realistic_glass = Material(diffuse=(0.98,0.97,0.95), ka=0.05, kd=0.1, ks=0.95, shininess=180, matType=TRANSPARENT, ior=1.52)

# Material 3: Metal dorado satinado (elementos curvos de la referencia)  
satin_gold = Material(diffuse=(0.85,0.75,0.55), ka=0.2, kd=0.6, ks=0.7, shininess=96, matType=REFLECTIVE, reflectivity=0.4)

# Material 4: Superficie mate beige (paredes y elementos sólidos)
matte_beige = Material(diffuse=(0.88,0.84,0.76), ka=0.3, kd=0.9, ks=0.1, shininess=8, matType=OPAQUE)

# Materiales adicionales para variedad y detalle
warm_white = Material(diffuse=(0.95,0.93,0.90), ka=0.3, kd=0.8, ks=0.2, shininess=32, matType=OPAQUE)
reflective_floor = Material(diffuse=(0.90,0.88,0.85), ka=0.12, kd=0.65, ks=0.45, shininess=56, matType=REFLECTIVE, reflectivity=0.30)
accent_bronze = Material(diffuse=(0.78,0.65,0.45), ka=0.2, kd=0.7, ks=0.5, shininess=64, matType=REFLECTIVE, reflectivity=0.3)

golden_sphere = Material(diffuse=(0.98,0.82,0.34), ka=0.04, kd=0.32, ks=0.95, shininess=220, matType=REFLECTIVE, reflectivity=0.85)

white_gloss = Material(diffuse=(1.0, 1.0, 1.0), ka=0.02, kd=0.12, ks=0.9, shininess=220, matType=REFLECTIVE, reflectivity=0.12)

chrome_metal = Material(diffuse=(0.98,0.98,0.98), ka=0.02, kd=0.05, ks=1.0, shininess=300, matType=REFLECTIVE, reflectivity=0.95)


# ILUMINACIÓN NATURAL SUAVE 
# Luz ambiente cálida como en la imagen de referencia
rend.lights.append(AmbientLight(intensity=0.35))

# Luz direccional suave simulando luz natural de ventana
rend.lights.append(DirectionalLight(direction=[0.3, -1, -0.5], intensity=0.8, color=[1.0, 0.98, 0.9]))

# Luces puntuales suaves para iluminación arquitectónica natural
rend.lights.append(PointLight(position=[0.6, 3.5, -3.2], intensity=1.4, color=[1.0, 0.98, 0.9]))   # Luz principal cálida, posicionada para highlights
rend.lights.append(PointLight(position=[-6, 3, -8], intensity=0.8, color=[0.95, 0.93, 0.88])) # Luz lateral suave
rend.lights.append(PointLight(position=[6, 2.6, -6], intensity=0.9, color=[0.95, 0.93, 0.88])) # Luz lateral para reflejos

# Luz de relleno frontal muy suave
rend.lights.append(PointLight(position=[0, 2, 8], intensity=0.6, color=[1.0, 0.98, 0.95]))

print(" Iluminación NATURAL configurada (6 luces) - Estilo arquitectónico minimalista")



# --- ARQUITECTURA BASE (inspirada en la referencia) ---
rend.objects += [
    # Suelo reflectante beige (como en la referencia)
    Plane(position=(0.0, -2.2, -10.0), normal=(0, 1, 0), material=reflective_floor),
    
    # Techo alto con iluminación suave
    Plane(position=(0.0, 6.0, -10.0), normal=(0, -1, 0), material=warm_marble),
    
    # Pared de fondo con "ventana" conceptual (environment map visible)
    Plane(position=(0.0, 0.0, -18.0), normal=(0, 0, 1), material=warm_white),
]

# --- ELEMENTOS ARQUITECTÓNICOS CURVOS (como las formas doradas en referencia) ---
# Grupo 1: Formas curvas orgánicas usando Torus
rend.objects += [
    # Toro principal grande horizontal (forma curva central de la referencia)
    Torus(center=[0, 0.5, -10], axis=[0, 0, 1], major_radius=2.8, minor_radius=0.6, material=satin_gold),
    
    # Toros secundarios como elementos arquitectónicos curvos
    Torus(center=[-5, 1.2, -12], axis=[0.3, 1, 0], major_radius=1.5, minor_radius=0.4, material=satin_gold),
    Torus(center=[5, 1.2, -12], axis=[-0.3, 1, 0], major_radius=1.5, minor_radius=0.4, material=satin_gold),
]

# --- ESFERAS TRANSLÚCIDAS (elemento principal de la referencia) ---
# Grupo 2: Esferas translúcidas EN PRIMER PLANO EXTREMO como en la nueva imagen de referencia
rend.objects += [
    # Esfera blanca brillante a la izquierda (similar a la referencia)
    Sphere(position=[-2.8, -0.3, -3.2], radius=1.9, material=white_gloss),

    # Esfera metálica cromada a la derecha (reflejos fuertes)
    Sphere(position=[2.6, 0.0, -3.2], radius=1.6, material=chrome_metal),

    # Esfera pequeña dorada en primer plano — color sol / highlight (más pequeña)
    # Nudge: x +0.15, y +0.05, z +0.20
    Sphere(position=[-0.25, -0.60, -1.50], radius=0.36, material=golden_sphere),

    # Opcional: elemento decorativo pequeño para equilibrio (tono mármol)
    # Moverlo hacia adelante para que sea visible en la composición
    Sphere(position=[2.0, 0.35, -3.0], radius=0.9, material=warm_marble),

    # Cylinders to simulate white curved wall behind the two large spheres
    # Place them further back (higher negative Z) and aligned with each large sphere's X
    # moved to corners so they don't occlude central figures
    Cylinder(center=[-8.0, 0.0, -7.0], axis=[0,1,0], radius=2.8, height=8.0, material=warm_white),
    Cylinder(center=[8.0, 0.0, -7.0], axis=[0,1,0], radius=2.8, height=8.0, material=warm_white),
]

# --- ELEMENTOS ARQUITECTÓNICOS VERTICALES ---
# Grupo 3: Columnas y elementos verticales usando Elipsoides
rend.objects += [
    # Elipsoide vertical como columna orgánica (inspirado en arquitectura de referencia)
    Ellipsoid(center=[-7, 1, -14], radii=[0.6, 2.8, 0.6], material=warm_marble),
    
    # Elipsoide horizontal como banca/elemento funcional
    Ellipsoid(center=[6, -0.5, -14], radii=[2.0, 0.8, 1.2], material=matte_beige),
    
    # Elipsoide decorativo suspendido
    Ellipsoid(center=[2, 3.2, -16], radii=[1.2, 0.6, 0.8], material=satin_gold),
]

# --- ELEMENTOS CÓNICOS COMO ACENTOS ARQUITECTÓNICOS ---
# Grupo 4: Conos como elementos direccionales y de transición
rend.objects += [
    # Cono en la plataforma CENTRAL circular (base circular central)
    Cone(apex=[0, 0.5, -10], base_center=[0, -1.6, -10], radius=1.0, material=accent_bronze),
    
    # Conos laterales como pilares cónicos
    Cone(apex=[-8, 3, -16], base_center=[-8, -1, -16], radius=0.8, material=matte_beige),
    Cone(apex=[8, 2.5, -16], base_center=[8, -1, -16], radius=0.9, material=matte_beige),
]

# Grupo 5: Discos como elementos de transición y marcos
rend.objects += [
    # Discos como marcos conceptuales en paredes
    Disk(position=[-9, 2.5, -17.5], normal=[0.2, 0, 1], radius=1.8, material=warm_marble),
    Disk(position=[9, 2.8, -17.5], normal=[-0.2, 0, 1], radius=1.6, material=warm_marble),
    
    # Base circular central como elemento unificador
    Disk(position=[0, -1.8, -10], normal=[0, 1, 0], radius=3.5, material=accent_bronze),
    
    # Disco elevado como mesa/plataforma
    Disk(position=[4, 0.2, -8], normal=[0, 1, 0.1], radius=1.2, material=reflective_floor),
]



# Configurar cámara para vista óptima con esferas en PRIMER PLANO (como en nueva imagen de referencia)
rend.camPos = np.array([0.4, 0.25, 2.6], dtype=float)  # Ajustada: ligeramente a la derecha y más cerca

# Execute render
print("")
import time
start_time = time.time()

def _row_callback(j):
    if j % 40 == 0:  # Mostrar progreso cada 40 filas
        progress = (j / rend.height) * 100
        print(f"    Progreso: {progress:.1f}% (fila {j}/{rend.height})")

# If live preview requested and GUI allowed, create a small Tk window and update it
# periodically from the row callback. We avoid blocking mainloop by calling root.update()
root = None
label = None
if not NO_GUI and LIVE:
    try:
        import tkinter as tk
        from PIL import Image, ImageTk

        root = tk.Tk()
        root.title(f"Live Preview - {final_width}x{final_height}")
        # initial image from (empty) framebuffer
        pil_image = Image.fromarray(rend.framebuffer)
        photo = ImageTk.PhotoImage(pil_image)
        label = tk.Label(root, image=photo)
        label.image = photo
        label.pack()
        print("🔴 Live preview enabled: ventana creada y se irá actualizando durante el render")
    except Exception as e:
        print(f"[WARN] No se pudo habilitar live preview: {e}")
        root = None

# choose how often to refresh the preview (in rows)
_preview_update_every = max(1, final_height // 40)

def _row_callback_live(j):
    # original progress logging
    if j % 40 == 0:
        progress = (j / rend.height) * 100
        print(f"    Progreso: {progress:.1f}% (fila {j}/{rend.height})")

    # update GUI preview occasionally
    if root is not None and label is not None and (j % _preview_update_every) == 0:
        try:
            from PIL import Image, ImageTk
            pil_image = Image.fromarray(rend.framebuffer)
            photo = ImageTk.PhotoImage(pil_image)
            label.configure(image=photo)
            label.image = photo
            # process pending GUI events so window stays responsive
            root.update()
        except Exception:
            # silently ignore GUI update errors during render
            pass

# pick callback depending on whether live preview is active
cb = _row_callback_live if (not NO_GUI and LIVE and root is not None) else _row_callback

if PROGRESSIVE:
    try:
        
        max_vis_width = 1200
        max_scale_allowed = 8
        if SCALE_ARG and SCALE_ARG >= 1:
            scale = max(1, min(max_scale_allowed, int(SCALE_ARG)))
        else:
            # auto scale: try to fit to max_vis_width but clamp to [1, max_scale_allowed]
            auto = max(1, min(max_scale_allowed, max_vis_width // max(1, rend.width)))
            scale = auto
        WINDOW_W = int(rend.width * scale)
        WINDOW_H = int(rend.height * scale)
        print(f"🔳 Progressive window: {WINDOW_W}x{WINDOW_H} (scale={scale})")
        final_img = rend.render_progressive(screen=None, window_size=(WINDOW_W, WINDOW_H))
        # copy into framebuffer for saving
        rend.framebuffer = final_img.astype(np.uint8)
    except Exception as e:
        print(f"[WARN] render_progressive failed: {e}; falling back to standard render")
        rend.render(row_callback=cb)
else:
    rend.render(row_callback=cb)
render_time = time.time() - start_time

# Save the image 
output_path = "Proyecto_Final.bmp"
rend.saveBMP(output_path)

print(f"\n✅ RENDER ARQUITECTÓNICO COMPLETADO")
print(f"📁 Imagen guardada: {output_path}")
print(f"🖼️  Resolución final: {rend.width}x{rend.height}")
print(f"⏱️  Tiempo de render: {render_time:.2f} segundos")
if hasattr(rend, 'ssaa') and rend.ssaa > 1:
    print(f"🔍 Anti-aliasing: {rend.ssaa}x SSAA")

# RESUMEN DE PUNTAJE PROYECTO FINAL - VERSIÓN REFERENCIA





# GUI opcional para mostrar resultado
if not NO_GUI:
    import tkinter as tk
    from PIL import Image, ImageTk
    
    # Create display window
    root = tk.Tk()
    root.title(f"Proyecto Final - Arquitectura Referencia - {rend.width}x{rend.height}")
    
    # Convert framebuffer to PIL Image
    img_array = (rend.framebuffer * 255).astype(np.uint8)
    pil_image = Image.fromarray(img_array)
    photo = ImageTk.PhotoImage(pil_image)
    
    # Display image
    label = tk.Label(root, image=photo)
    label.pack()
    
    print("🖼️  Imagen mostrada en ventana GUI")
    print("   Cierra la ventana para terminar el programa")
    root.mainloop()
else:
    print("🚫 GUI deshabilitado (modo nogui activo)")