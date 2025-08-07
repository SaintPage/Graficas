import struct

def GenerateBmp(filename, width, height, byteDepth, colorBuffer):
    def char(c):
        return struct.pack("<c", c.encode("ascii"))
    def word(w):
        return struct.pack("<H", w)
    def dword(d):
        return struct.pack("<L", d)
    with open(filename, "wb") as file:
        file.write(char("B"))
        file.write(char("M"))
        file.write(dword(14 + 40 + (width * height * byteDepth)))
        file.write(dword(0))
        file.write(dword(14 + 40))
        file.write(dword(40))
        file.write(dword(width))
        file.write(dword(height))
        file.write(word(1))
        file.write(word(byteDepth * 8))
        file.write(dword(0))
        file.write(dword(width * height * byteDepth))
        file.write(dword(0))
        file.write(dword(0))
        file.write(dword(0))
        file.write(dword(0))
        for y in range(height):
            for x in range(width):
                color = colorBuffer[x][y]
                b = int(color[2]) if len(color) > 2 else 0
                g = int(color[1]) if len(color) > 1 else 0
                r = int(color[0]) if len(color) > 0 else 0
                file.write(b.to_bytes(1, "little"))
                file.write(g.to_bytes(1, "little"))
                file.write(r.to_bytes(1, "little"))

class BMPTexture:
    def __init__(self, filename):
        with open(filename, "rb") as image:
            image.seek(10)
            headerSize = struct.unpack("=l", image.read(4))[0]
            image.seek(18)
            self.width = struct.unpack("=l", image.read(4))[0]
            self.height = struct.unpack("=l", image.read(4))[0]
            image.seek(headerSize)
            self.pixels = []
            for y in range(self.height):
                row = []
                for x in range(self.width):
                    b = image.read(1)[0] / 255
                    g = image.read(1)[0] / 255
                    r = image.read(1)[0] / 255
                    row.append((r, g, b))
                self.pixels.append(row)
    def getColor(self, u, v):
        if 0 <= u < 1 and 0 <= v < 1:
            i = int(u * (self.width - 1))
            j = int(v * (self.height - 1))
            return self.pixels[j][i]
        return (0, 0, 0)