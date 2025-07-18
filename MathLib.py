import numpy as np
from math import pi, sin, cos, isclose

def auto_fit_model(model, screen_w, screen_h, margin=0.8):
    verts = np.array(model.vertices).reshape(-1, 3)
    minv = verts.min(axis=0)
    maxv = verts.max(axis=0)
    size = maxv - minv                        # dimensión del bbox

    # FACTOR DE ESCALA:  usa el eje más grande
    # (margin <1 deja un poco de borde)
    if size.max() == 0:
        s = 1
    else:
        s = margin * min(screen_w, screen_h) / size.max()

    model.scale = [s, s, s]

    # centro geométrico → (0,0) pantalla-centro
    cx, cy, cz = (minv + size / 2)
    model.translation = [
        screen_w / 2 - cx * s,
        screen_h / 2 - cy * s,
        -cz * s  # no afecta en proyección ortográfica pero lo dejamos
    ]

def TranslationMatrix(x, y, z):
	
	return np.matrix([[1, 0, 0, x],
					  [0, 1, 0, y],
					  [0, 0, 1, z],
					  [0, 0, 0, 1]])



def ScaleMatrix(x, y, z):
	
	return np.matrix([[x, 0, 0, 0],
					  [0, y, 0, 0],
					  [0, 0, z, 0],
					  [0, 0, 0, 1]])



def RotationMatrix(pitch, yaw, roll):
	
	# Convertir a radianes
	pitch *= pi/180
	yaw *= pi/180
	roll *= pi/180
	
	# Creamos la matriz de rotaci�n para cada eje.
	pitchMat = np.matrix([[1,0,0,0],
						  [0,cos(pitch),-sin(pitch),0],
						  [0,sin(pitch),cos(pitch),0],
						  [0,0,0,1]])
	
	yawMat = np.matrix([[cos(yaw),0,sin(yaw),0],
						[0,1,0,0],
						[-sin(yaw),0,cos(yaw),0],
						[0,0,0,1]])
	
	rollMat = np.matrix([[cos(roll),-sin(roll),0,0],
						 [sin(roll),cos(roll),0,0],
						 [0,0,1,0],
						 [0,0,0,1]])
	
	return pitchMat * yawMat * rollMat