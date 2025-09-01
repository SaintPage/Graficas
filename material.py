import numpy as np

class Material(object):
    def __init__(self,
                 diffuse=(1, 1, 1),
                 ka=0.10,          # ambient
                 kd=1.00,          # diffuse
                 ks=0.35,          # specular
                 shininess=64):
        self.diffuse   = np.array(diffuse, dtype=float)
        self.ka        = float(ka)
        self.kd        = float(kd)
        self.ks        = float(ks)
        self.shininess = int(shininess)

    def GetSurfaceColor(self, intercept, renderer):
        """
        Phong:  final = diffuse * (ka*Ambient + kd*Diffuse) + ks*Specular
        Con sombras por shadow ray.
        """
        ambient_acc = np.array((0.0, 0.0, 0.0), dtype=float)
        diffuse_acc = np.array((0.0, 0.0, 0.0), dtype=float)
        spec_acc    = np.array((0.0, 0.0, 0.0), dtype=float)

        for light in renderer.lights:
            shadowIntercept = None

            # sombra sólo para luces direccionales (o puntuales si tuvieras)
            if getattr(light, "lightType", "") == "Directional":
                lightDir = tuple(-i for i in light.direction)
                # pequeño bias para evitar acne
                biasP = (np.array(intercept.point) +
                         np.array(intercept.normal) * 1e-4).tolist()
                shadowIntercept = renderer.glCastRay(biasP, lightDir, intercept.obj)

            # APORTES
            if getattr(light, "lightType", "") == "Ambient":
                ambient_acc += np.array(light.GetLightColor(), dtype=float)

            elif getattr(light, "lightType", "") == "Directional":
                lightDir = -np.array(light.direction, dtype=float)
                biasP    = np.array(intercept.point, dtype=float) + 1e-4*np.array(intercept.normal, dtype=float)
                shadowIntercept = renderer.glCastRay(biasP, lightDir, intercept.obj)
                if shadowIntercept is None:
                    # difuso
                    diffuse_acc += np.array(light.GetLightColor(intercept), dtype=float)

                    # especular (tomando posición de cámara robustamente)
                    eye_pos = getattr(renderer, "camPos",
                                      getattr(getattr(renderer, "camera", None), "translation", (0,0,0)))

                    spec_acc += np.array(
                        light.GetSpecularColor(
                            intercept,
                            eye_pos,
                            shininess=self.shininess,
                            ks=self.ks
                        ),
                        dtype=float
                    )

        final = self.diffuse * (self.ka * ambient_acc + self.kd * diffuse_acc) + spec_acc
        final = np.clip(final, 0, 1)
        return final.tolist()
