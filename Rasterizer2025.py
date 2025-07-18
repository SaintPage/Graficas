import pygame
from gl import *
from BMP_Writer import GenerateBMP
from model import Model
from shaders import *
from objloader import load_obj
from MathLib import auto_fit_model
from shaders import vertexShader

width = 720
height = 480

screen = pygame.display.set_mode((width, height), pygame.SCALED)
clock = pygame.time.Clock()

rend = Renderer(screen)


triangleModel = Model()
triangleModel.vertices = load_obj("models/skull.obj")
auto_fit_model(triangleModel, width, height)
rend.models.append(triangleModel)

triangleModel.vertexShader = vertexShader



isRunning = True
while isRunning:

	deltaTime = clock.tick(60) / 1000.0


	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			isRunning = False

		elif event.type == pygame.KEYDOWN:
			if event.key == pygame.K_1:
				rend.primitiveType = POINTS

			elif event.key == pygame.K_2:
				rend.primitiveType = LINES

			elif event.key == pygame.K_3:
				rend.primitiveType = TRIANGLES



	keys = pygame.key.get_pressed()

	if keys[pygame.K_RIGHT]:
		triangleModel.translation[0] += 10 * deltaTime
	if keys[pygame.K_LEFT]:
		triangleModel.translation[0] -= 10 * deltaTime
	if keys[pygame.K_UP]:
		triangleModel.translation[1] += 10 * deltaTime
	if keys[pygame.K_DOWN]:
		triangleModel.translation[1] -= 10 * deltaTime


	if keys[pygame.K_d]:
		triangleModel.rotation[2] += 20 * deltaTime
	if keys[pygame.K_a]:
		triangleModel.rotation[2] -= 20 * deltaTime

	if keys[pygame.K_w]:
		triangleModel.scale =  [(i + deltaTime) for i in triangleModel.scale]
	if keys[pygame.K_s]:
		triangleModel.scale = [(i - deltaTime) for i in triangleModel.scale ]










	rend.glClear()

	# Escribir lo que se va a dibujar aqui

	rend.glRender()

	#########################################

	pygame.display.flip()


GenerateBMP("output.bmp", width, height, 3, rend.frameBuffer)
# Definimos (modo, nombre_de_archivo)
capturas = [
    (POINTS,    "output_points.bmp"),
    (LINES,     "output_lines.bmp"),
    (TRIANGLES, "output_wireframe.bmp"),
    (TRIANGLES, "output_filled.bmp"),  # si quisieras un 4º distinto, p. ej. con otro shader
]

for modo, fname in capturas:
    rend.primitiveType = modo
    rend.glClear()           # limpiar framebuffer con clearColor
    rend.glRender()          # vuelve a dibujar todo en el modo actual
    GenerateBMP(fname, width, height, 3, rend.frameBuffer)


pygame.quit()