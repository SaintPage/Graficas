def load_obj(path):
    """
    Carga un OBJ y devuelve una lista plana [x0,y0,z0, x1,y1,z1, ...],
    triangulando y respetando índices negativos (relativos al final).
    """
    verts = []          # lista de vértices (x,y,z)
    model_vertices = [] # resultado final

    with open(path, "r") as f:
        for line in f:
            parts = line.strip().split()
            if not parts:
                continue

            # vértice: "v x y z"
            if parts[0] == "v":
                if len(parts) < 4:
                    print(f"Warning: vértice malformado: {line.strip()}")
                    continue
                x, y, z = map(float, parts[1:4])
                verts.append((x, y, z))

            # cara: "f v1[/vt1[/vn1]] v2[...] v3[...] ..."
            elif parts[0] == "f":
                idx = []
                for tok in parts[1:]:
                    # extraigo sólo el índice de vértice antes de cualquier "/"
                    token_v = tok.split("/")[0]
                    try:
                        raw = int(token_v)
                    except ValueError:
                        print(f"Warning: no pude parsear índice '{tok}'")
                        idx = []
                        break

                    # convierto raw a índice Python 0-based
                    if raw > 0:
                        vi = raw - 1
                    elif raw < 0:
                        vi = len(verts) + raw
                    else:
                        # en OBJ no se usa 0
                        idx = []
                        break

                    # compruebo rango
                    if vi < 0 or vi >= len(verts):
                        print(f"Warning: índice {raw} (=>{vi}) fuera de rango (0–{len(verts)-1})")
                        idx = []
                        break

                    idx.append(vi)

                # al menos 3 vértices para triangular
                if len(idx) < 3:
                    continue

                # triangulación fan: (0,i,i+1)
                for i in range(1, len(idx) - 1):
                    for j in (0, i, i + 1):
                        x, y, z = verts[idx[j]]
                        model_vertices.extend([x, y, z])

    return model_vertices
