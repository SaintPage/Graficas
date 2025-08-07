import numpy as np

def LookAt(eye, target, up):
    forward = (eye - target)
    forward = forward / np.linalg.norm(forward)
    right = np.cross(up, forward)
    right = right / np.linalg.norm(right)
    trueUp = np.cross(forward, right)
    M = np.eye(4)
    M[0, 0:3] = right
    M[1, 0:3] = trueUp
    M[2, 0:3] = forward
    T = np.eye(4)
    T[0, 3] = -eye[0]
    T[1, 3] = -eye[1]
    T[2, 3] = -eye[2]
    return M @ T





def Perspective(fov, aspect, near, far):
    """
    Matriz de proyección fila-mayor (row-major) que respeta el aspect ratio.
    fov en grados, aspect = width/height.
    """
    f = 1 / np.tan(np.radians(fov) / 2)
    return np.array([
        [f / aspect, 0,  0,                              0],
        [0,          f,  0,                              0],
        [0,          0, (far+near)/(near-far), (2*far*near)/(near-far)],
        [0,          0, -1,                              0]
    ], dtype=float)



def Viewport(x, y, w, h):
    M = np.eye(4)
    M[0, 0] = w / 2
    M[1, 1] = h / 2
    M[0, 3] = x + w / 2
    M[1, 3] = y + h / 2
    M[2, 2] = 0.5
    M[2, 3] = 0.5
    return M

def RotationMatrix(rx, ry, rz):
    Rx = np.array([
        [1, 0, 0, 0],
        [0, np.cos(rx), -np.sin(rx), 0],
        [0, np.sin(rx), np.cos(rx), 0],
        [0, 0, 0, 1]
    ])
    Ry = np.array([
        [np.cos(ry), 0, np.sin(ry), 0],
        [0, 1, 0, 0],
        [-np.sin(ry), 0, np.cos(ry), 0],
        [0, 0, 0, 1]
    ])
    Rz = np.array([
        [np.cos(rz), -np.sin(rz), 0, 0],
        [np.sin(rz), np.cos(rz), 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ])
    return Rx @ Ry @ Rz