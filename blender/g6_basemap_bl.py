"""G6 v7: podklad mapowy w Blenderze (Workbench, ciemny motyw) z basemap.npz (pipeline/g6_basemap.py). Uzycie: add_basemap(bpy, sc, npz_path) -> update(orth)."""
import numpy as np

def srgb(c):   # kolory podane jak w palecie 8-bit, Workbench bierze diffuse_color liniowo
    c = np.array(c, float) / 255; return tuple(np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4))

# kategoria: (kolor sRGB, z); od dolu: pola, zabudowa, zielen, las, woda, budynki, cieki, kolej
POLY = {"farmland": ((14, 20, 17), -9.0), "residential": ((29, 32, 44), -8.0), "industrial": ((31, 29, 38), -7.5), "green": ((22, 50, 30), -7.0),
        "forest": ((13, 43, 22), -6.5), "water": ((16, 42, 88), -6.0), "building": ((40, 42, 56), -5.0)}
LINE = {"stream": ((20, 54, 108), -4.5, lambda o: max(3.0, o / 1500)), "river": ((26, 66, 130), -4.0, lambda o: max(8.0, o / 600)), "rail": ((88, 88, 104), -3.0, lambda o: max(2.5, o / 1200))}

def add_basemap(bpy, sc, path):
    D = np.load(path); lines = {}
    for cat, (rgb, z) in POLY.items():
        v, f = D[f"{cat}_v"], D[f"{cat}_f"]
        if not len(f): continue
        me = bpy.data.meshes.new(cat); me.from_pydata(np.c_[v, np.full(len(v), z)].astype(np.float32).tolist(), [], f.tolist()); me.update()
        mm = bpy.data.materials.new("bm_" + cat); mm.diffuse_color = (*srgb(rgb), 1); me.materials.append(mm)
        sc.collection.objects.link(bpy.data.objects.new(cat, me))
    def ribbon(S, w, z):
        d = S[:, 2:] - S[:, :2]; L = np.maximum(np.hypot(d[:, 0], d[:, 1]), 1e-6)[:, None]; n = np.stack([-d[:, 1], d[:, 0]], 1) / L * w / 2
        return np.c_[np.concatenate([S[:, :2] + n, S[:, :2] - n, S[:, 2:] - n, S[:, 2:] + n], 0), np.full(4 * len(S), z)].astype(np.float32)
    for cat, (rgb, z, wf) in LINE.items():
        S = D[f"{cat}_s"]; m = len(S)
        if not m: continue
        i = np.arange(m); me = bpy.data.meshes.new(cat + "_l"); me.from_pydata(ribbon(S, 5, z).tolist(), [], np.stack([i, i + m, i + 2 * m, i + 3 * m], 1).tolist()); me.update()
        mm = bpy.data.materials.new("bl_" + cat); mm.diffuse_color = (*srgb(rgb), 1); me.materials.append(mm)
        sc.collection.objects.link(bpy.data.objects.new(cat + "_l", me)); lines[cat] = (me, S, z, wf)
    def update(orth):
        for cat, (me, S, z, wf) in lines.items():
            me.vertices.foreach_set("co", ribbon(S, wf(orth), z).ravel()); me.update()
    return update
