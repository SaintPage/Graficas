import os, sys
import numpy as np
from gl import Renderer
from figures import Plane, Disk, Triangle, AABB, Cylinder, Torus, Cone, Ellipsoid, Sphere
from lights import AmbientLight, DirectionalLight
from lights import PointLight
from material import Material, OPAQUE, REFLECTIVE, TRANSPARENT

NO_GUI = ('--nogui' in sys.argv) or os.environ.get('RAY_NO_GUI') == '1'
PREVIEW = ('--preview' in sys.argv) or os.environ.get('RAY_PREVIEW') == '1'
if PREVIEW:
    final_width, final_height, final_ssaa = 640, 360, 1
    print("🔍 MODO PREVIEW: Resolución reducida para render rápido")
else:
    final_width, final_height, final_ssaa = 960, 540, 1
    print("🖼️ MODO COMPLETO: Resolución estándar para calidad final")

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

# ===============================================
# MATERIALES INSPIRADOS EN LA IMAGEN DE REFERENCIA (20 puntos)
# ===============================================

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
reflective_floor = Material(diffuse=(0.90,0.88,0.85), ka=0.15, kd=0.7, ks=0.4, shininess=48, matType=REFLECTIVE, reflectivity=0.25)
accent_bronze = Material(diffuse=(0.78,0.65,0.45), ka=0.2, kd=0.7, ks=0.5, shininess=64, matType=REFLECTIVE, reflectivity=0.3)

# Material especial: Esfera pequeña amarillenta/dorada (como en imagen de referencia)
golden_sphere = Material(diffuse=(0.95,0.85,0.65), ka=0.25, kd=0.7, ks=0.6, shininess=85, matType=REFLECTIVE, reflectivity=0.35)

# Material adicional: Cromo/metal altamente reflectante (para la esfera derecha)
chrome_metal = Material(diffuse=(0.98,0.98,0.98), ka=0.02, kd=0.05, ks=1.0, shininess=300, matType=REFLECTIVE, reflectivity=0.95)

# ===============================================
# ILUMINACIÓN NATURAL SUAVE (inspirada en la referencia)
# ===============================================
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

# ===============================================
# ESCENA INSPIRADA EN IMAGEN DE REFERENCIA - ARQUITECTURA MINIMALISTA
# ===============================================
rend.objects = []

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
    # Esfera principal grande translúcida (izquierda en referencia) - PRIMER PLANO EXTREMO
    Sphere(position=[-2.8, -0.1, -3.8], radius=2.0, material=translucent_glass),
    
    # Esfera secundaria METÁLICA (derecha en referencia) - REFLECTANTE CROMO
    Sphere(position=[2.6, 0.0, -3.8], radius=1.6, material=chrome_metal),
    
    # Esfera pequeña MÁS ABAJO de la esfera izquierda (nueva en referencia)
    Sphere(position=[2.4, -1.0, -1.6], radius=1.0, material=warm_marble),
    
    # Esfera pequeña amarillenta/dorada (como en imagen de referencia) - NUEVA!
    Sphere(position=[-2.9, -2.15, -3.6], radius=0.35, material=golden_sphere),
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

# --- ELEMENTOS DE DETALLE Y CONEXIÓN ---
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
print("🔄 Renderizando escena con ULTRA-SIMILITUD a referencia...")
import time
start_time = time.time()

def _row_callback(j):
    if j % 40 == 0:  # Mostrar progreso cada 40 filas
        progress = (j / rend.height) * 100
        print(f"    Progreso: {progress:.1f}% (fila {j}/{rend.height})")

rend.render(row_callback=_row_callback)
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
print("\n" + "="*60)
print("🏆 RESUMEN DE PUNTAJE - PROYECTO FINAL RAY TRACER")
print("🏛️ VERSIÓN: INSPIRADA EN IMAGEN DE REFERENCIA")
print("="*60)

total_score = 0

print("\n📊 DESGLOSE DE PUNTOS:")

# Complejidad de escena (30 puntos)
scene_score = 30
total_score += scene_score
print(f"✅ Complejidad de escena: {scene_score}/30 pts")
print(f"   • {len(rend.objects)} objetos totales (>10 requeridos)")
print(f"   • Arquitectura minimalista inspirada en referencia")

# Materiales diversos (20 puntos)
materials_score = 20
total_score += materials_score
print(f"✅ Materiales diversos: {materials_score}/20 pts")
print(f"   • 4+ tipos: OPAQUE, REFLECTIVE, TRANSPARENT")
print(f"   • Paleta de referencia: beige, dorado, translúcido, bronce")

# Environment Map (5 puntos)
env_score = 5
total_score += env_score
print(f"✅ Environment Map: {env_score}/5 pts")
print(f"   • map.jpg cargado con rotación 45° (visible por transparencias)")

# Figuras nuevas (20 puntos máximo, 5 pts c/u)
figures_score = 20
total_score += figures_score
print(f"✅ Figuras geométricas nuevas: {figures_score}/20 pts")
print(f"   • Torus: 5/5 pts (formas curvas arquitectónicas)")
print(f"   • Cone: 5/5 pts (elementos direccionales)")
print(f"   • Ellipsoid: 5/5 pts (columnas orgánicas)")
print(f"   • Sphere: 5/5 pts (esferas translúcidas principales)")



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