import pygame
import sys
from gl import Renderer
from BMP_Writer import GenerateBMP


class ScanlineRenderer(Renderer):
    def glFillPolygon(self, poly, color=None):

        ys = [p[1] for p in poly]
        y_min, y_max = min(ys), max(ys)

        for y in range(y_min, y_max + 1):
            intersecciones = []
            n = len(poly)
            for i in range(n):
                x0, y0 = poly[i]
                x1, y1 = poly[(i+1) % n]
                # ignorar aristas horizontales
                if y0 == y1:
                    continue
                # asegurar y0 < y1
                if y0 > y1:
                    x0, y0, x1, y1 = x1, y1, x0, y0
                # si la scanline cruza la arista
                if y0 <= y < y1:
                    t = (y - y0) / (y1 - y0)
                    xi = x0 + t * (x1 - x0)
                    intersecciones.append(xi)

            if len(intersecciones) >= 2:
                intersecciones.sort()
                # conectar pares de intersección
                for i in range(0, len(intersecciones), 2):
                    x_start = int(intersecciones[i])
                    x_end   = int(intersecciones[i+1])
                    self.glLine((x_start, y), (x_end, y), color)


pygame.init()
width, height = 960, 540
screen = pygame.display.set_mode((width, height), pygame.SCALED)
pygame.display.set_caption("Scanline: figuras blancas y estrella amarilla")
clock = pygame.time.Clock()

poly1 = [(165,380),(185,360),(180,330),(207,345),(233,330),
         (230,360),(250,380),(220,385),(205,410),(193,383)]
poly2 = [(321,335),(288,286),(339,251),(374,302)]
poly3 = [(377,249),(411,197),(436,249)]
poly4 = [(413,177),(448,159),(502, 88),(553, 53),(535, 36),(676, 37),
         (660, 52),(750,145),(761,179),(672,192),(659,214),(615,214),
         (632,230),(580,230),(597,215),(552,214),(517,144),(466,180)]
poly5 = [(682,175),(708,120),(735,148),(739,170)]  # hueco dentro de poly4


fill_colors = {
    1: (1, 1, 0),   
    2: (1, 1, 1),   
}
line_color = (0, 0, 0)  # negro para todos los bordes
hole_color = (1, 1, 1)  


def main():
    rend = ScanlineRenderer(screen)

    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

        rend.glClear()

        # Polígono 1
        rend.glFillPolygon(poly1, fill_colors[1])
        rend.glColor(*line_color)
        for i in range(len(poly1)):
            rend.glLine(poly1[i], poly1[(i+1) % len(poly1)])

        #Polígono 2
        rend.glFillPolygon(poly2, fill_colors[2])
        rend.glColor(*line_color)
        for i in range(len(poly2)):
            rend.glLine(poly2[i], poly2[(i+1) % len(poly2)])

        #Pologino 3
        rend.glFillPolygon(poly3, fill_colors[2])
        rend.glColor(*line_color)
        for i in range(len(poly3)):
            rend.glLine(poly3[i], poly3[(i+1) % len(poly3)])

        #Poligono 4
        rend.glFillPolygon(poly4, fill_colors[2])
        rend.glColor(*line_color)
        for i in range(len(poly4)):
            rend.glLine(poly4[i], poly4[(i+1) % len(poly4)])

        #Poligono5
        rend.glFillPolygon(poly5, line_color)
        rend.glColor(*line_color)
        for i in range(len(poly5)):
            rend.glLine(poly5[i], poly5[(i+1) % len(poly5)])

        pygame.display.flip()
        clock.tick(60)

  
    GenerateBMP("output.bmp", width, height, 3, rend.frameBuffer)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
