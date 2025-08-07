import numpy as np

class Model:
    def __init__(self):
        self.vertices = []
        self.translation = [0, 0, 0]
        self.scale = [1, 1, 1]
        self.rotation = [0, 0, 0]
        self.vertexShader = None
        self.fragmentShader = None
        self.texture = None

    def GetModelMatrix(self):
        T = np.eye(4)
        T[0, 3] = self.translation[0]
        T[1, 3] = self.translation[1]
        T[2, 3] = self.translation[2]
        S = np.diag([self.scale[0], self.scale[1], self.scale[2], 1])
        Rx = np.array([
            [1, 0, 0, 0],
            [0, np.cos(self.rotation[0]), -np.sin(self.rotation[0]), 0],
            [0, np.sin(self.rotation[0]), np.cos(self.rotation[0]), 0],
            [0, 0, 0, 1]
        ])
        Ry = np.array([
            [np.cos(self.rotation[1]), 0, np.sin(self.rotation[1]), 0],
            [0, 1, 0, 0],
            [-np.sin(self.rotation[1]), 0, np.cos(self.rotation[1]), 0],
            [0, 0, 0, 1]
        ])
        Rz = np.array([
            [np.cos(self.rotation[2]), -np.sin(self.rotation[2]), 0, 0],
            [np.sin(self.rotation[2]), np.cos(self.rotation[2]), 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])
        R = Rx @ Ry @ Rz
        return T @ R @ S