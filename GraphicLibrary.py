import pygame            
import numpy as np
from MathLibrary import LookAt, Perspective, Viewport

POINTS, LINES, TRIANGLES = 0, 1, 2

class Renderer:
    def __init__(self, screen):
        self.activeFragmentParams = {}
        self.screen = screen
        _, _, self.width, self.height = screen.get_rect()
        self.glClearColor(0, 0, 0)
        self.glColor(1, 1, 1)
        self.glClear()
        self.primitiveType = TRIANGLES
        self.models = []
        self.activeModelMatrix = None
        self.activeVertexShader = None
        self.activeFragmentShader = None
        self.activeTexture = None
        self.dirLight = np.array((0, 0, -1))
                

        # 1. Vista (cámara)
        self.viewMatrix = LookAt(
            np.array((0, 0, 3)),   # posición cámara
            np.array((0, 0, 0)),   # a dónde mira
            np.array((0, 1, 0))    # up vector
        )

        # 2. Proyección en perspectiva
        fov   = 60       # grados
        near  = 0.1
        far   = 1000
        aspect = self.width / self.height
        self.projectionMatrix = Perspective(fov, aspect, near, far)

        # 3. Viewport (mapea NDC a pixeles)
        self.viewportMatrix = Viewport(0, 0, self.width, self.height)


        fov   = 60                    
        near  = 0.1
        far   = 1000
        aspect = self.width / self.height


    def glClearColor(self, r, g, b):
        self.clearColor = [min(1, max(0, r)), min(1, max(0, g)), min(1, max(0, b))]

    def glColor(self, r, g, b):
        self.currColor = [min(1, max(0, r)), min(1, max(0, g)), min(1, max(0, b))]

    def glClear(self):
        c = [int(ch * 255) for ch in self.clearColor]
        self.screen.fill(c)
        self.frameBuffer = [[c[:] for _ in range(self.height)] for __ in range(self.width)]
        self.zBuffer = [[float('inf') for _ in range(self.height)] for __ in range(self.width)]

    def glPoint(self, x, y, color=None):
        x, y = round(x), round(y)
        if 0 <= x < self.width and 0 <= y < self.height:
            if color is None:
                c = [int(ch * 255) for ch in self.currColor]
            else:
                c = [max(0, min(255, int(ch))) for ch in color]
            self.screen.set_at((x, self.height - 1 - y), c)
            self.frameBuffer[x][y] = c

    def barycentric(self, A, B, C, P):
        px, py = P
        x0, y0 = A
        x1, y1 = B
        x2, y2 = C
        denom = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if denom == 0:
            return -1, -1, -1
        u = ((y1 - y2) * (px - x2) + (x2 - x1) * (py - y2)) / denom
        v = ((y2 - y0) * (px - x2) + (x0 - x2) * (py - y2)) / denom
        return u, v, 1 - u - v

    def glTriangle(self, A, B, C):
        xs = [A[0], B[0], C[0]]
        ys = [A[1], B[1], C[1]]
        minx, maxx = max(0, int(min(xs))), min(self.width - 1, int(max(xs)))
        miny, maxy = max(0, int(min(ys))), min(self.height - 1, int(max(ys)))
        for x in range(minx, maxx + 1):
            for y in range(miny, maxy + 1):
                px, py = x, y
                u, v, w = self.barycentric((A[0], A[1]), (B[0], B[1]), (C[0], C[1]), (x, y))
                if u < 0 or v < 0 or w < 0:
                    continue
                z = u * A[2] + v * B[2] + w * C[2]
                if z < self.zBuffer[x][y]:
                    self.zBuffer[x][y] = z
                    invw_A, invw_B, invw_C = A[8], B[8], C[8]
                    U_A, U_B, U_C = A[6], B[6], C[6]
                    V_A, V_B, V_C = A[7], B[7], C[7]
                    interpolated_invw = u * invw_A + v * invw_B + w * invw_C
                    if interpolated_invw == 0:
                        continue
                    tu = (u * U_A * invw_A + v * U_B * invw_B + w * U_C * invw_C) / interpolated_invw
                    tv = (u * V_A * invw_A + v * V_B * invw_B + w * V_C * invw_C) / interpolated_invw


                    color = self.activeFragmentShader(
                        verts=(A, B, C),
                        baryCoords=(u, v, w),
                        dirLight=self.dirLight,
                        texture=self.activeTexture,
                        u=tu, v=tv,
                        x=px, y=py,
                        **self.activeFragmentParams         
                    )


                    self.glPoint(x, y, color)

    def glDrawPrimitives(self, buf, ofs):
        if self.primitiveType == POINTS:
            for i in range(0, len(buf), ofs):
                self.glPoint(buf[i], buf[i + 1])
        elif self.primitiveType == LINES:
            for i in range(0, len(buf), ofs * 3):
                for j in range(3):
                    x0 = buf[i + ofs * j]
                    y0 = buf[i + ofs * j + 1]
                    x1 = buf[i + ofs * ((j + 1) % 3)]
                    y1 = buf[i + ofs * ((j + 1) % 3) + 1]
                    self.glLine((x0, y0), (x1, y1))
        else:
            for i in range(0, len(buf), ofs * 3):
                A = buf[i:i + ofs]
                B = buf[i + ofs:i + 2 * ofs]
                C = buf[i + 2 * ofs:i + 3 * ofs]
                self.glTriangle(A, B, C)

    def glRender(self):
        M = self.viewportMatrix @ self.projectionMatrix @ self.viewMatrix
        for model in self.models:
            self.activeModelMatrix = model.GetModelMatrix()
            self.activeVertexShader = model.vertexShader
            self.activeTexture = getattr(model, "texture", self.activeTexture)
            self.activeFragmentShader = getattr(model, "fragmentShader", self.activeFragmentShader)
            self.activeFragmentParams = getattr(model, "fragmentParams", {})  
            vertexBuffer = []
            time_val = pygame.time.get_ticks() / 1000
            self.activeFragmentParams = {
                **getattr(model, "fragmentParams", {}),
                "time": time_val
            }
            for i in range(0, len(model.vertices), 8):
                x, y, z, nx, ny, nz, u, v = model.vertices[i:i + 8]
                vx, vy, vz = self.activeVertexShader((x, y, z), modelMatrix=self.activeModelMatrix)
                vt = np.array(M @ np.array((vx, vy, vz, 1.0))).flatten()
                w = vt[3]
                vertexBuffer += [
                    vt[0] / w,
                    vt[1] / w,
                    vt[2] / w,
                    nx, ny, nz,
                    u, v,
                    1 / w
                ]
            self.glDrawPrimitives(vertexBuffer, 9)