"""G6: scena Blendera (4.4) z wynikiem pipeline/g6_bake.py. Ciemny motyw.
GUI:   blender --python blender/g6_load.py -- --data output/g6_blender
Render: blender -b --python blender/g6_load.py -- --data output/g6_blender --stills 1200,1500 --out reports/etap2/g6_blender
        ... --anim 1200 1320 --out reports/etap2/g6_blender   (klatki animacji = indeksy .npz)
1 jednostka = 1 m; srodek sceny = (524805, 485023) EPSG:2180."""
import sys, argparse, math
from pathlib import Path
import bpy, numpy as np

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--data", default="output/g6_blender")
ap.add_argument("--out", default="reports/etap2/g6_blender")
ap.add_argument("--stills", default="")          # lista klatek npz, np. 1200,1500
ap.add_argument("--anim", nargs=2, type=int)     # start end (indeksy klatek npz)
ap.add_argument("--fps", type=int, default=24)
ap.add_argument("--res", nargs=2, type=int, default=[960, 540])
ap.add_argument("--car-scale", type=float, default=8)   # powiekszenie auta (4.5 m jest niewidoczne z 7 km)
ap.add_argument("--view", type=float, default=7000)     # szerokosc widoku ortho w m
ap.add_argument("--net-radius", type=float, default=9000)
ap.add_argument("--net-width", type=float, default=12)
ap.add_argument("--vmax", type=float, default=14)       # m/s, gorna granica skali koloru
a, _ = ap.parse_known_args(argv)   # nieznane (np. z g6_story.py) ignorujemy
data = Path(a.data)

V = np.load(data / "vehicles.npz"); POS, VIS, HEAD, SPD = V["pos"], V["visible"], V["heading"], V["speed"]
NF, N = VIS.shape; STEP = float(V["step"])
E = np.load(data / "network.npz")["edges"].astype(np.float64)

# --- czysta scena
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 0, NF - 1
sc.render.fps = a.fps

# --- swiat: prawie czarny
w = bpy.data.worlds.new("dark"); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.004, 0.005, 0.008, 1); bg.inputs[1].default_value = 1.0

# --- siec: pasy (quady), kolor i szerokosc wg klasy drogi (paleta OSM, przyciemniona pod ciemny motyw)
HW = np.load(data / "network.npz")["hw"] if "hw" in np.load(data / "network.npz").files else np.array(["residential"] * len(E))
CLS = {  # klasa: (kolor OSM * jasnosc, mnoznik szerokosci, kolejnosc rysowania)
    "motorway": ((0.91, 0.57, 0.64), 2.4, 6), "trunk": ((0.98, 0.70, 0.61), 2.2, 5), "primary": ((0.99, 0.84, 0.64), 2.0, 4),
    "secondary": ((0.97, 0.98, 0.75), 1.6, 3), "tertiary": ((0.80, 0.80, 0.80), 1.25, 2)}
MINOR = ((0.055, 0.085, 0.14), 1.0, 0)
def cls_of(h):
    h = str(h).replace("_link", ""); c = CLS.get(h, MINOR)
    return (tuple(x * (1.0 if h in ("motorway", "trunk", "primary") else 0.75) for x in c[0]), c[1] * (0.7 if "_link" in str(h) else 1), c[2]) if c is not MINOR else MINOR
_cl = [cls_of(h) for h in HW]
ECOL = np.array([c[0] for c in _cl], np.float32); WF = np.array([c[1] for c in _cl], np.float32); ZR = np.array([c[2] for c in _cl], np.float32)
keep = (np.hypot(E[:, 0], E[:, 1]) < a.net_radius) | (np.hypot(E[:, 2], E[:, 3]) < a.net_radius)
E, ECOL, WF, ZR = E[keep], ECOL[keep], WF[keep], ZR[keep]
M = len(E); idx = np.arange(M)
def net_verts(w):   # w = szerokosc bazowa; wyzsze klasy szersze i wyzej (z) => rysowane na wierzchu
    d = E[:, 2:] - E[:, :2]; L = np.maximum(np.hypot(d[:, 0], d[:, 1]), 1e-6)[:, None]
    n = np.stack([-d[:, 1], d[:, 0]], 1) / L * (w * WF)[:, None] / 2
    A, B = E[:, :2], E[:, 2:]; z = np.tile(ZR * 0.2, 4)
    return np.c_[np.concatenate([A + n, A - n, B - n, B + n], 0), z].astype(np.float32)
faces = np.stack([idx, idx + M, idx + 2 * M, idx + 3 * M], 1)
me = bpy.data.meshes.new("network")
me.from_pydata(net_verts(a.net_width).tolist(), [], faces.tolist()); me.update()
ca = me.attributes.new("col", "FLOAT_COLOR", "POINT"); ca.data.foreach_set("color", np.c_[np.tile(ECOL, (4, 1)), np.ones(4 * M)].astype(np.float32).ravel())
net = bpy.data.objects.new("network", me); sc.collection.objects.link(net)
m = bpy.data.materials.new("road"); m.use_nodes = True; tn = m.node_tree; tn.nodes.clear()
_at = tn.nodes.new("ShaderNodeAttribute"); _at.attribute_name = "col"; _at.attribute_type = "GEOMETRY"
_em = tn.nodes.new("ShaderNodeEmission"); _em.inputs["Strength"].default_value = 0.9; _ot = tn.nodes.new("ShaderNodeOutputMaterial")
tn.links.new(_at.outputs["Color"], _em.inputs["Color"]); tn.links.new(_em.outputs[0], _ot.inputs[0])
net.data.materials.append(m)

# --- granica powiatu (fioletowa, jak granice administracyjne w OSM); wstega o szerokosci zaleznej od zoomu
import json
_pg = json.load(open(Path(__file__).resolve().parents[1] / "scenarios/kutno/area/powiat.geojson"))["features"][0]["geometry"]["coordinates"]
_segs = []
for ring in _pg:
    r_ = np.array(ring, np.float64)[:, :2] - np.array((524805.0, 485023.0)); _segs.append(np.c_[r_[:-1], r_[1:]])
BS = np.concatenate(_segs); BM = len(BS)
def border_verts(w):
    d = BS[:, 2:] - BS[:, :2]; L = np.maximum(np.hypot(d[:, 0], d[:, 1]), 1e-6)[:, None]; n = np.stack([-d[:, 1], d[:, 0]], 1) / L * w / 2
    return np.c_[np.concatenate([BS[:, :2] + n, BS[:, :2] - n, BS[:, 2:] - n, BS[:, 2:] + n], 0), np.full(4 * BM, 1.5)].astype(np.float32)
bi = np.arange(BM); bme = bpy.data.meshes.new("border")
bme.from_pydata(border_verts(30).tolist(), [], np.stack([bi, bi + BM, bi + 2 * BM, bi + 3 * BM], 1).tolist()); bme.update()
border = bpy.data.objects.new("border", bme); sc.collection.objects.link(border)
bm_ = bpy.data.materials.new("border"); bm_.use_nodes = True; bt = bm_.node_tree; bt.nodes.clear()
_be = bt.nodes.new("ShaderNodeEmission"); _be.inputs["Color"].default_value = (0.75, 0.35, 0.9, 1); _be.inputs["Strength"].default_value = 2.0
_bo = bt.nodes.new("ShaderNodeOutputMaterial"); bt.links.new(_be.outputs[0], _bo.inputs[0]); bme.materials.append(bm_)

# --- punkty pojazdow (N wierzcholkow; niewidoczne parkujemy pod kamera, z=-1e4)
pm = bpy.data.meshes.new("veh_pts")
pm.from_pydata([(0, 0, -1e4)] * N, [], []); pm.attributes.new("heading", "FLOAT", "POINT"); pm.attributes.new("speed", "FLOAT", "POINT")
veh = bpy.data.objects.new("vehicles", pm); sc.collection.objects.link(veh)

def update(frame):
    f = min(max(int(frame), 0), NF - 1)
    co = np.zeros((N, 3), np.float32); co[:, :2] = POS[f]; co[:, 2] = 3.0
    co[~VIS[f]] = (1e7, 1e7, -1e4)   # poza kadrem (ortho ignoruje glebie: pod droga byloby widac w lukach na wezlach)
    pm.vertices.foreach_set("co", co.ravel())
    pm.attributes["heading"].data.foreach_set("value", HEAD[f])
    pm.attributes["speed"].data.foreach_set("value", SPD[f])
    pm.update()

def on_frame(scene, *_): update(scene.frame_current)
bpy.app.handlers.frame_change_pre[:] = [h for h in bpy.app.handlers.frame_change_pre if h.__name__ != "on_frame"]
bpy.app.handlers.frame_change_pre.append(on_frame)

# --- Geometry Nodes: kostka na punkcie, obrot z atrybutu heading, realize (atrybut speed do materialu)
ng = bpy.data.node_groups.new("cars", "GeometryNodeTree")
ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
nd = ng.nodes; ln = ng.links.new
gi, go = nd.new("NodeGroupInput"), nd.new("NodeGroupOutput")
cube = nd.new("GeometryNodeMeshCube"); cube.inputs["Size"].default_value = (4.5 * a.car_scale, 1.8 * a.car_scale, 1.5 * a.car_scale)
na = nd.new("GeometryNodeInputNamedAttribute"); na.data_type = "FLOAT"; na.inputs["Name"].default_value = "heading"
cx = nd.new("ShaderNodeCombineXYZ"); eu = nd.new("FunctionNodeEulerToRotation")
iop = nd.new("GeometryNodeInstanceOnPoints"); rl = nd.new("GeometryNodeRealizeInstances")
ln(na.outputs["Attribute"], cx.inputs["Z"]); ln(cx.outputs[0], eu.inputs[0]); ln(eu.outputs[0], iop.inputs["Rotation"])
ln(gi.outputs[0], iop.inputs["Points"]); ln(cube.outputs[0], iop.inputs["Instance"])
ln(iop.outputs[0], rl.inputs[0]); ln(rl.outputs[0], go.inputs[0])
mod = veh.modifiers.new("cars", "NODES"); mod.node_group = ng

cm = bpy.data.materials.new("car"); cm.use_nodes = True; t = cm.node_tree; t.nodes.clear()
at = t.nodes.new("ShaderNodeAttribute"); at.attribute_name = "speed"; at.attribute_type = "GEOMETRY"
mr = t.nodes.new("ShaderNodeMapRange"); mr.inputs["From Max"].default_value = a.vmax
cr = t.nodes.new("ShaderNodeValToRGB")   # wolno = czerwony -> szybko = turkus
cr.color_ramp.elements[0].color = (1.0, 0.12, 0.05, 1); cr.color_ramp.elements[1].color = (0.1, 0.9, 1.0, 1)
cr.color_ramp.elements.new(0.4).color = (1.0, 0.7, 0.1, 1)
ems = t.nodes.new("ShaderNodeEmission"); ems.inputs["Strength"].default_value = 4.0
out = t.nodes.new("ShaderNodeOutputMaterial")
t.links.new(at.outputs["Fac"], mr.inputs["Value"]); t.links.new(mr.outputs[0], cr.inputs[0])
t.links.new(cr.outputs[0], ems.inputs["Color"]); t.links.new(ems.outputs[0], out.inputs[0])
rl_mat = nd.new("GeometryNodeSetMaterial"); rl_mat.inputs["Material"].default_value = cm
ng.links.remove(rl.outputs[0].links[0]); ln(rl.outputs[0], rl_mat.inputs[0]); ln(rl_mat.outputs[0], go.inputs[0])

# --- kamera: ortho z gory, nad centrum Kutna
cd = bpy.data.cameras.new("cam"); cd.type = "ORTHO"; cd.ortho_scale = a.view; cd.clip_end = 1e5
cam = bpy.data.objects.new("cam", cd); cam.location = (0, 0, 5000); sc.collection.objects.link(cam); sc.camera = cam

# --- render
sc.render.engine = "BLENDER_EEVEE_NEXT"
sc.render.resolution_x, sc.render.resolution_y = a.res; sc.render.resolution_percentage = 100
sc.view_settings.view_transform = "Standard"
update(0)

if a.stills or a.anim:
    out_dir = Path(a.out).resolve(); out_dir.mkdir(parents=True, exist_ok=True)
    for s in filter(None, a.stills.split(",")):
        sc.frame_set(int(s)); sc.render.filepath = str(out_dir / f"frame_{int(s):04d}.png")
        bpy.ops.render.render(write_still=True)
    if a.anim:
        sc.frame_start, sc.frame_end = a.anim
        try:
            sc.render.image_settings.file_format = "FFMPEG"; sc.render.ffmpeg.format = "MPEG4"
            sc.render.ffmpeg.codec = "H264"; sc.render.ffmpeg.constant_rate_factor = "MEDIUM"
            sc.render.filepath = str(out_dir / "anim.mp4")
        except TypeError as e:
            print("ffmpeg niedostepny:", e); sc.render.image_settings.file_format = "PNG"; sc.render.filepath = str(out_dir / "anim_")
        bpy.ops.render.render(animation=True)
else:
    sc.frame_set(1200)
