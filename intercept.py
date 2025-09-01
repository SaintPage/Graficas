class Intercept(object):
    def __init__(self, point, normal, distance, rayDirection, obj):
        self.point        = point
        self.normal       = normal
        self.distance     = distance
        self.rayDirection = rayDirection
        self.obj          = obj
