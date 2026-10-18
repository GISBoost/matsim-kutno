"""G6: scena Blendera (4.4) z wynikiem pipeline/g6_bake.py. Ciemny motyw.
GUI:   blender --python blender/g6_load.py -- --data output/g6_blender
Render: blender -b --python blender/g6_load.py -- --data output/g6_blender --stills 1200,1500 --out reports/g6_blender
        ... --anim 1200 1320 --out reports/g6_blender   (klatki animacji = indeksy .npz)
1 jednostka = 1 m; srodek sceny = (524805, 485023) EPSG:2180."""
import sys, argparse, math
from pathlib import Path
import bpy, numpy as np

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--data", default="output/g6_blender")
ap.add_argument("--out", default="reports/g6_blender")
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

# --- siec: pasy (quady) o szerokosci net-width
keep = (np.hypot(E[:, 0], E[:, 1]) < a.net_radius) | (np.hypot(E[:, 2], E[:, 3]) < a.net_radius)
E = E[keep]
d = E[:, 2:] - E[:, :2]; L = np.maximum(np.hypot(d[:, 0], d[:, 1]), 1e-6)[:, None]
n = np.stack([-d[:, 1], d[:, 0]], 1) / L * a.net_width / 2
A, B = E[:, :2], E[:, 2:]
verts = np.concatenate([A + n, A - n, B - n, B + n], 0)           # (4M,2), blok po M
M = len(E); idx = np.arange(M)
faces = np.stack([idx, idx + M, idx + 2 * M, idx + 3 * M], 1)
me = bpy.data.meshes.new("network")
me.from_pydata(np.c_[verts, np.zeros(4 * M)].tolist(), [], faces.tolist()); me.update()
net = bpy.data.objects.new("network", me); sc.collection.objects.link(net)
m = bpy.data.materials.new("road"); m.use_nodes = True
em = m.node_tree.nodes["Principled BSDF"]; em.inputs["Base Color"].default_value = (0.02, 0.03, 0.05, 1)
em.inputs["Emission Color"].default_value = (0.10, 0.16, 0.26, 1); em.inputs["Emission Strength"].default_value = 0.5
net.data.materials.append(m)

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
