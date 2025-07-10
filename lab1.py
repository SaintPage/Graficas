import pygame
import sys
from gl import Renderer
from BMP_Writer import GenerateBMP


class ScanlineRenderer(Renderer):
    def glFillPolygon(self, poly, color=None):
        #Fijar el color de relleno en el renderer
        if color is not None:
            self.glColor(*color)

        
        ys = [p[1] for p in poly]
        y_min, y_max = min(ys), max(ys)

        for y in range(y_min, y_max + 1):
            inters = []
            n = len(poly)
            yf = y + 0.5  # muestreo medio-píxel

            for i in range(n):
                x0, y0 = poly[i]
                x1, y1 = poly[(i + 1) % n]

                if y0 == y1:
                    continue
                if y0 > y1:
                    x0, y0, x1, y1 = x1, y1, x0, y0

                if y0 <= yf < y1:
                    t = (yf - y0) / (y1 - y0)
                    xi = x0 + t * (x1 - x0)
                    inters.append(xi)

            if len(inters) >= 2:
                inters.sort()
                for i in range(0, len(inters), 2):
                    x_start = int(inters[i])
                    x_end   = int(inters[i + 1])
                    for x in range(x_start, x_end + 1):
                        # aquí sólo puntos, usa el color fijado arriba
                        self.glLine((x, y), (x, y))


pygame.init()
width, height = 960, 540
screen = pygame.display.set_mode((width, height), pygame.SCALED)
pygame.display.set_caption("Scanline: estrella amarilla y agarre negro")
clock = pygame.time.Clock()

# polígonos
poly1 = [(165,380),(185,360),(180,330),(207,345),(233,330),
         (230,360),(250,380),(220,385),(205,410),(193,383)]  # estrella
poly2 = [(321,335),(288,286),(339,251),(374,302)]
poly3 = [(377,249),(411,197),(436,249)]
poly4 = [(413,177),(448,159),(502, 88),(553, 53),(535, 36),(676, 37),
         (660, 52),(750,145),(761,179),(672,192),(659,214),(615,214),
         (632,230),(580,230),(597,215),(552,214),(517,144),(466,180)]  # tetera
poly5 = [(682,175),(708,120),(735,148),(739,170)]  #hueco

# colores
YELLOW = (1.0, 1.0, 0.0)
WHITE  = (1.0, 1.0, 1.0)
BLACK  = (0.0, 0.0, 0.0)


def main():
    rend = ScanlineRenderer(screen)
    running = True

    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

        rend.glClear()

        #Poligono1
        rend.glFillPolygon(poly1, YELLOW)

        #Poligono2
        rend.glFillPolygon(poly2, WHITE)

        #Poligono3
        rend.glFillPolygon(poly3, WHITE)
        
        #Poligono4
        rend.glFillPolygon(poly4, WHITE)
        
        #Poligono5
        rend.glFillPolygon(poly5, BLACK)

        pygame.display.flip()
        clock.tick(60)

    GenerateBMP("output.bmp", width, height, 3, rend.frameBuffer)
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
