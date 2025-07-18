import numpy as np

def vertexShader(vertex, **kwargs):
    # Se lleva a cabo por vertice

	# Recibimos las matrices
    modelMatrix = kwargs["modelMatrix"]

	# Agregamos un componente W al vertice
    vt = [vertex[0],
          vertex[1],
          vertex[2],
          1]

	# Transformamos el vertices por todas las matrices en el orden correcto
    vt = modelMatrix @ vt

    vt = vt.tolist()[0]

	# Dividimos x,y,z por w para regresar el vertices a un tamaño de 3
    vt = [vt[0] / vt[3],
          vt[1] / vt[3],
          vt[2] / vt[3]]

    return vt