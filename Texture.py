from PIL import Image
import numpy as np

class Texture:
    def __init__(self, filename):
        img = Image.open(filename).convert("RGB")
        self.width, self.height = img.size
        data = np.array(img, dtype=np.float32) / 255.0
        self.pixels = [
            [tuple(data[y, x]) for x in range(self.width)]
            for y in range(self.height)
        ]

    def getColor(self, u, v):
        u = min(max(u, 0.001), 0.999)
        v = min(max(v, 0.001), 0.999)
        i = int(u * (self.width - 1))
        j = int((1 - v) * (self.height - 1))
        return self.pixels[j][i]