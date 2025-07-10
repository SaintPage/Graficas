

class Renderer:
    def __init__(self, screen):
        self.screen = screen
        _, _, self.width, self.height = screen.get_rect()

        self.glClearColor(0, 0, 0)
        self.glColor(1, 1, 1)
        self.glClear()

    def glClearColor(self, r, g, b):

        r = min(1, max(0,r))
        g = min(1, max(0,g))
        b = min(1, max(0,b))

        self.clearColor = [r, g, b]

    def glColor(self, r, g, b):
        r = min(1, max(0,r))
        g = min(1, max(0,g))
        b = min(1, max(0,b))

        self.currColor = [r, g, b]

    def glClear(self):
        #Pasa por cada valor de RGB y le aplica i por 2555 
        color = [int(i* 255) for i in self.clearColor]
        self.screen.fill(color)

        self.frameBuffer = [[self.clearColor for y in range(self.height)]
            for x in range(self.width)]
    
    def glPoint(self, x, y, color = None):

        x = round(x)
        y = round(y)

        if (0 <= x < self.width) and (0 <= y < self.height):
            color = [int(i* 255) for i in (color or self.currColor)]
            self.screen.set_at((x,self.height -1 -y), color)

            self.frameBuffer[x][y]= color

    def glLine(self, p0, p1, color= None):
        # Algoritmo de Lineas de Bresenham

        # y = mx + b

        x0 = p0[0]
        x1 = p1[0]
        y0 = p0[1]
        y1 = p1[1]

        # Si el punto 0 es igual que el punto 1, solamente dibujar un punto
        if x0 == x1 and y0 == y1:
            self.glPoint(x0, y0)
            return
        
        dy = abs(y1 - y0)
        dx = abs(x1 - x0)

        steep = dy > dx

        if steep:
            x0, y0 = y0, x0
            x1, y1 = y1, x1
        
        if x0 > x1: 
            x0, x1 = x1,x0
            y0, y1 = y1, y0
        
        dy = abs(y1 - y0)
        dx = abs(x1 - x0)

        #Cuanto he subido en la linea
        offset = 0
        limit = 0.75
        m = dy / dx
        y = y0

        for x in range(round(x0), round(x1)+ 1):
            if steep:
                self.glPoint(y, x, color or self.currColor)
            else:
                self.glPoint(x, y, color or self.currColor) 
            offset += m

            if offset >= limit:
                if y0 < y1:
                    y += 1
                else:
                    y -= 1
                limit += 1
            