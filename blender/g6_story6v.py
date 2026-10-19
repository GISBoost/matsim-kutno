"""G6: film v6 = v5 w silniku WORKBENCH (flat, kolory z materialow): cienkie szare drogi wg klasy, auta czerwony->zolty->zielony wg predkosci (0-80 km/h); dane z runu g5r3 (output/g6_blender_r3).
Dane: output/g6_blender_r3 (bake --t1 72000 --step 10). Reuzywa sceny z g6_load.py (runpy). Render:
 blender -b --factory-startup --python blender/g6_story6.py -- --data output/g6_blender_r3 --res 1280 720 --net-radius 1e9 --story
 ... --story-stills 100,500,900   | --story-range 0 120"""
import sys, argparse, runpy
from pathlib import Path
import bpy, bmesh, numpy as np

G = runpy.run_path(str(Path(__file__).with_name("g6_load.py")), run_name="g6")   # buduje scene, nic nie renderuje
sc, a, ng, cube, ems, cam, cd = (G[k] for k in ("sc", "a", "ng", "cube", "ems", "cam", "cd"))
POS, VIS, HEAD, SPD, NF, N, STEP, pm, mod = (G[k] for k in ("POS", "VIS", "HEAD", "SPD", "NF", "N", "STEP", "pm", "mod"))
ids, frames, E = G["V"]["ids"], G["V"]["frames"], G["E"]
ap = argparse.ArgumentParser(); ap.add_argument("--story", action="store_true"); ap.add_argument("--story-stills", default="")
ap.add_argument("--story-range", nargs=2, type=int); ap.add_argument("--fps", type=int, default=30)
sa, _ = ap.parse_known_args(sys.argv[sys.argv.index("--") + 1:])
sc.render.fps = sa.fps; cd.sensor_fit = "HORIZONTAL"   # pion: ortho_scale = szerokosc kadru
sc.render.engine = "BLENDER_WORKBENCH"; dsp = sc.display; dsp.shading.light = "FLAT"; dsp.shading.color_type = "MATERIAL"; dsp.render_aa = "8"
dsp.shading.show_cavity = dsp.shading.show_shadows = dsp.shading.show_object_outline = False; sc.view_settings.view_transform = "Standard"; sc.view_settings.look = "None"
sc.world.color = (0.002, 0.003, 0.005); cd.clip_start, cd.clip_end = 3000, 6000   # precyzja z-bufora dla nakladek przy duzej skali
# --- siec: klasy wg rangi (0 mniejsze, 2 tertiary, 3 secondary, 4 primary, 5 trunk, 6 motorway), cienkie szare
ZR_, WFc = G["ZR"], G["WF"]; WFR = {0: 1.0, 2: 1.2, 3: 1.45, 4: 1.7, 5: 1.9, 6: 2.0}; WFc[:] = np.array([WFR[int(r)] for r in ZR_], np.float32)
RC = {0: (0.17, 0.18, 0.22), 2: (0.30, 0.31, 0.35), 3: (0.42, 0.42, 0.45), 4: (0.60, 0.58, 0.55), 5: (0.72, 0.70, 0.66), 6: (0.85, 0.82, 0.78)}
nm = G["net"].data; nm.materials.clear()
for r_ in sorted(RC):
    mm = bpy.data.materials.new(f"rc{r_}"); mm.diffuse_color = (*RC[r_], 1); nm.materials.append(mm)
RI = {r_: i for i, r_ in enumerate(sorted(RC))}; nm.polygons.foreach_set("material_index", np.array([RI[int(r)] for r in ZR_], np.int32))
G["bm_"].diffuse_color = (0.7, 0.35, 0.9, 1)
# --- rampa predkosci jak w referencji: czerwony -> zolty -> zielony; GN: material wg przedzialu predkosci (K=16)
rp = G["cr"].color_ramp; rp.elements[0].color = (0.95, 0.1, 0.05, 1); rp.elements[1].color = (1.0, 0.78, 0.1, 1); rp.elements[1].position = 0.45; rp.elements[2].color = (0.15, 0.85, 0.25, 1)
def chain(grp, src, bin_out, mats, dst):   # lancuch Set Material z selekcja bin == i (Workbench bierze kolor z materialow geometrii)
    prev = src
    for i_, mm in enumerate(mats):
        cmp_ = grp.nodes.new("FunctionNodeCompare"); cmp_.data_type = "INT"; cmp_.operation = "EQUAL"; cmp_.inputs[3].default_value = i_
        sm_ = grp.nodes.new("GeometryNodeSetMaterial"); sm_.inputs["Material"].default_value = mm
        grp.links.new(bin_out, cmp_.inputs[2]); grp.links.new(cmp_.outputs[0], sm_.inputs["Selection"]); grp.links.new(prev, sm_.inputs[0]); prev = sm_.outputs[0]
    grp.links.new(prev, dst)
K = 16; VK = a.vmax * 3.6
VM = []
for i_ in range(K):
    mm = bpy.data.materials.new(f"v{i_}"); mm.diffuse_color = tuple(rp.evaluate(i_ / (K - 1))); VM.append(mm)
rlm = G["rl_mat"]; rl_src = rlm.inputs[0].links[0].from_socket; ng.links.remove(rlm.outputs[0].links[0]); ng.links.remove(rlm.inputs[0].links[0])
na_ = ng.nodes.new("GeometryNodeInputNamedAttribute"); na_.data_type = "FLOAT"; na_.inputs["Name"].default_value = "speed"
mr_ = ng.nodes.new("ShaderNodeMapRange"); mr_.inputs["From Max"].default_value = a.vmax; mr_.inputs["To Max"].default_value = K - 1; mr_.clamp = True
fi_ = ng.nodes.new("FunctionNodeFloatToInt"); fi_.rounding_mode = "ROUND"
ng.links.new(na_.outputs["Attribute"], mr_.inputs["Value"]); ng.links.new(mr_.outputs[0], fi_.inputs[0])
chain(ng, rl_src, fi_.outputs[0], VM, [n for n in ng.nodes if n.bl_idname == "NodeGroupOutput"][0].inputs[0])
smooth = lambda x: x * x * (3 - 2 * x)
lerp = lambda p, q, t: p + (q - p) * t

# ---------- skala auta jako wejscie GN (zmienna w czasie)
ng.interface.new_socket("Scale", in_out="INPUT", socket_type="NodeSocketFloat")
sid = [i.identifier for i in ng.interface.items_tree if i.name == "Scale"][0]
vs = ng.nodes.new("ShaderNodeVectorMath"); vs.operation = "SCALE"; vs.inputs[0].default_value = (4.5, 1.8, 1.5)
gi = [n for n in ng.nodes if n.bl_idname == "NodeGroupInput"][0]
ng.links.new(gi.outputs["Scale"], vs.inputs["Scale"]); ng.links.new(vs.outputs[0], cube.inputs["Size"])

# ---------- flashe aktywnosci: start/koniec przejazdu (r: dom->praca, c: wjazd->praca)
d = np.diff(VIS.astype(np.int8), axis=0)
HOME, WORK, ENTRY = (0.25, 0.55, 1.0), (1.0, 1.0, 1.0), (0.85, 0.35, 1.0)
ev = []   # (t, x, y, rgb)
for j in range(N):
    for f in np.where(d[:, j] == 1)[0]: ev.append((frames[f + 1], *POS[f + 1, j], HOME if ids[j][0] == "r" else ENTRY))
    for f in np.where(d[:, j] == -1)[0]: ev.append((frames[f], *POS[f, j], WORK))
ev.sort(key=lambda e: e[0]); EVT = np.array([e[0] for e in ev]); EXY = np.array([e[1:3] for e in ev], np.float32)
ECOL = np.array([(*e[3], 1) for e in ev], np.float32); NE = len(ev); FADE = 90.0   # s symulacji
fm = bpy.data.meshes.new("flash"); fm.from_pydata([(0, 0, -1e4)] * NE, [], [])
fm.attributes.new("age", "FLOAT", "POINT"); fm.attributes.new("col", "FLOAT_COLOR", "POINT")
fo = bpy.data.objects.new("flash", fm); sc.collection.objects.link(fo)
fg = bpy.data.node_groups.new("flash", "GeometryNodeTree")
fg.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
fg.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
fg.interface.new_socket("Size", in_out="INPUT", socket_type="NodeSocketFloat")
fid = [i.identifier for i in fg.interface.items_tree if i.name == "Size"][0]
n_, l_ = fg.nodes, fg.links.new
fi, fgo = n_.new("NodeGroupInput"), n_.new("NodeGroupOutput")
sp = n_.new("GeometryNodeMeshIcoSphere"); sp.inputs["Radius"].default_value = 1.0; sp.inputs["Subdivisions"].default_value = 2
age = n_.new("GeometryNodeInputNamedAttribute"); age.data_type = "FLOAT"; age.inputs["Name"].default_value = "age"
mu = n_.new("ShaderNodeMath"); mu.operation = "MULTIPLY_ADD"; mu.inputs[1].default_value = 2.0; mu.inputs[2].default_value = 1.0   # 1+2*age
sz = n_.new("ShaderNodeMath"); sz.operation = "MULTIPLY"
cs = n_.new("ShaderNodeCombineXYZ"); fi2 = n_.new("GeometryNodeInstanceOnPoints"); fre = n_.new("GeometryNodeRealizeInstances"); fsm = n_.new("GeometryNodeSetMaterial")
l_(age.outputs["Attribute"], mu.inputs[0]); l_(mu.outputs[0], sz.inputs[0]); l_(fi.outputs["Size"], sz.inputs[1])
for k in "XYZ": l_(sz.outputs[0], cs.inputs[k])
l_(fi.outputs[0], fi2.inputs["Points"]); l_(sp.outputs[0], fi2.inputs["Instance"]); l_(cs.outputs[0], fi2.inputs["Scale"])
l_(fi2.outputs[0], fre.inputs[0]); l_(fre.outputs[0], fsm.inputs[0]); l_(fsm.outputs[0], fgo.inputs[0])
fmod = fo.modifiers.new("flash", "NODES"); fmod.node_group = fg
FM = []
for i_, c_ in enumerate((HOME, WORK, ENTRY)):
    mm = bpy.data.materials.new(f"f{i_}"); mm.diffuse_color = (*c_, 1); FM.append(mm)
CAT = np.array([0 if e_[3] == HOME else 1 if e_[3] == WORK else 2 for e_ in ev], np.float32); fm.attributes.new("cat", "FLOAT", "POINT")
mu.inputs[1].default_value = -1.7; mu.inputs[2].default_value = 2.0   # rozmiar maleje z wiekiem: 2 - 1.7*age (bez przezroczystosci)
fg.nodes.remove(fsm)
ca_ = fg.nodes.new("GeometryNodeInputNamedAttribute"); ca_.data_type = "FLOAT"; ca_.inputs["Name"].default_value = "cat"
fi3 = fg.nodes.new("FunctionNodeFloatToInt"); fg.links.new(ca_.outputs["Attribute"], fi3.inputs[0])
chain(fg, fre.outputs[0], fi3.outputs[0], FM, fgo.inputs[0])


# ---------- agent r6509026_1: dom -> praca (2 przejazdy tego samego pojazdu: rano i po pracy)
FPS = sa.fps; T0 = float(frames[0]); BASE = 60.0 / FPS      # s symulacji na klatke filmu przy 1 s = 1 min (= 2 s)
AID = "r6509026_1"; J1, J2 = [int(j) for j in np.where(ids == AID)[0]]
w1, w2 = np.where(VIS[:, J1])[0], np.where(VIS[:, J2])[0]
if w1[0] > w2[0]: J1, J2, w1, w2 = J2, J1, w2, w1
A0, A1, B0, B1 = int(w1[0]), int(w1[-1]), int(w2[0]), int(w2[-1])
F1, F2 = np.arange(A0, A1 + 1), np.arange(B0, B1 + 1)
a1, a2 = POS[A0:A1 + 1, J1], POS[B0:B1 + 1, J2]; s1, s2 = SPD[A0:A1 + 1, J1] * 3.6, SPD[B0:B1 + 1, J2] * 3.6
WORKXY = a1[-1]
DEP1, ARR1, DEP2, ARR2 = (T0 + k * STEP for k in (A0, A1, B0, B1))
print("agent", AID, "dojazd", DEP1 / 3600, ARR1 / 3600, "powrot", DEP2 / 3600, ARR2 / 3600)
def agent_xy(f):
    if f <= A1: return np.array([np.interp(f, F1, a1[:, 0]), np.interp(f, F1, a1[:, 1])])
    if f < B0: return WORKXY
    return np.array([np.interp(f, F2, a2[:, 0]), np.interp(f, F2, a2[:, 1])])
def agent_v(f):
    if A0 <= f <= A1: return float(np.interp(f, F1, s1))
    if B0 <= f <= B1: return float(np.interp(f, F2, s2))
    return 0.0
TP = np.array([agent_xy(f) for f in range(A0, B1 + 1)])

# ---------- harmonogram: tt[o] = czas symulacji (s) w klatce filmu o; kinds[o] = ujecie
S = lambda s: int(s * FPS)
tt, kinds = [T0], []
def run(n, kind, dts=None):
    for i in range(n): kinds.append(kind); tt.append(tt[-1] + (BASE if dts is None else dts[i]))
n = S(10); k = np.arange(n); m = smooth(np.clip(np.minimum(k / 30, (n - 1 - k) / 30), 0, 1))   # poranek: do wyjazdu agenta (7:34) w 10 s, przyspieszone
D = (DEP1 - 6 * 60) - tt[-1]; vm0 = BASE + (D - BASE * n) / m.sum(); run(n, "S1", BASE + (vm0 - BASE) * m); run(S(3), "ZIN1"); run(int(np.ceil((ARR1 + 120 - tt[-1]) / BASE)), "FOL1"); run(S(3), "ZK")
n = S(10); k = np.arange(n); m = smooth(np.clip(np.minimum(k / 30, (n - 1 - k) / 30), 0, 1))   # praca: 10 s, plynne przyspieszenie
D = (DEP2 - 3 * 60) - tt[-1]; vm = BASE + (D - BASE * n) / m.sum(); run(n, "WORK", BASE + (vm - BASE) * m)
run(S(3), "ZIN2"); run(int(np.ceil((ARR2 + 120 - tt[-1]) / BASE)), "FOL2"); run(S(3), "HOLD"); run(S(3), "ZP")
n = S(10); k = np.arange(n); m = smooth(np.clip(np.minimum(k / 30, (n - 1 - k) / 30), 0, 1))   # reszta dnia do 20:00 w 10 s
D = (frames[-1] - 10) - tt[-1]; vm2 = BASE + (D - BASE * n) / m.sum(); run(n, "END", BASE + (vm2 - BASE) * m)
TT = np.array(tt); TOT = len(kinds); KS = {}
for o, kd in enumerate(kinds): KS.setdefault(kd, [o, 0])[1] += 1
print({k_: (v[0] / FPS, v[1] / FPS) for k_, v in KS.items()}, "razem", TOT / FPS, "s; szczyt tempa", vm * FPS / 60, "min/s")
assert TT[-1] < frames[-1]
ex = E[:, [0, 2]].ravel(); ey = E[:, [1, 3]].ravel()
PC = ((ex.min() + ex.max()) / 2, (ey.min() + ey.max()) / 2); PV = 1.12 * max(ex.max() - ex.min(), (ey.max() - ey.min()) * 9 / 16)   # caly powiat
KV = 9000.0; AV = 800.0
ease = lambda k: k * k * (3 - 2 * k)
mixlog = lambda a_, b_, k: float(np.exp(lerp(np.log(a_), np.log(b_), k)))
Z0 = np.zeros(2)
def state(o):
    kd = kinds[o]; f = (TT[o] - T0) / STEP; k = ease((o - KS[kd][0]) / KS[kd][1]); ag = agent_xy(f)
    if kd == "S1": return kd, f, PC, PV
    if kd == "ZIN1": return kd, f, tuple(lerp(np.array(PC), ag, k)), mixlog(PV, AV, k)
    if kd in ("FOL1", "FOL2", "HOLD"): return kd, f, tuple(ag), AV
    if kd == "ZK": return kd, f, tuple(lerp(ag, Z0, k)), mixlog(AV, KV, k)
    if kd == "WORK": return kd, f, (0, 0), KV
    if kd == "ZP": return kd, f, tuple(lerp(ag, np.array(PC), k)), mixlog(AV, PV, k)
    if kd == "END": return kd, f, PC, PV
    return kd, f, tuple(lerp(Z0, ag, k)), mixlog(KV, AV, k)      # ZIN2

# ---------- siec o szerokosci zaleznej od zoomu
net = G["net"].data; brd = G["border"].data
def set_net(w, bw=30.0):
    net.vertices.foreach_set("co", G["net_verts"](w).ravel()); net.update()
    brd.vertices.foreach_set("co", G["border_verts"](bw).ravel()); brd.update()

# ---------- nakladki: dzieci pustego obiektu na kamerze; jednostka = 1/1000 szerokosci kadru
ov = bpy.data.objects.new("overlay", None); sc.collection.objects.link(ov); ov.parent = cam; ov.location = (0, 0, -4000)
FONT, FONTB = (bpy.data.fonts.load(f"C:/Windows/Fonts/{n_}.ttf") for n_ in ("segoeui", "segoeuib"))   # Segoe UI: polskie znaki
import itertools
ZC = itertools.count(1)   # Workbench: kolejnosc nakladek = glebokosc (kazdy obiekt o 0.05 jedn. wyzej)
def mat(rgb, strength=1.0):
    m = bpy.data.materials.new("o"); m.diffuse_color = (*rgb, 1); return m
def text(x, y, size, rgb=(0.9, 0.93, 1), body="", align="LEFT", bold=False):
    c = bpy.data.curves.new("t", "FONT"); c.body = body; c.size = size; c.align_x = align; c.font = FONTB if bold else FONT
    o_ = bpy.data.objects.new("t", c); sc.collection.objects.link(o_); o_.parent = ov; o_.location = (x, y, next(ZC) * 0.05); c.materials.append(mat(rgb)); return o_
def line(rgb, n, w=1.6):
    c = bpy.data.curves.new("l", "CURVE"); c.dimensions = "3D"; c.bevel_depth = w; c.splines.new("POLY").points.add(n - 1)
    o_ = bpy.data.objects.new("l", c); sc.collection.objects.link(o_); o_.parent = ov; o_.location.z = next(ZC) * 0.05; c.materials.append(mat(rgb)); return o_
def setline(o_, xs, ys):
    pts = np.zeros((len(xs), 4), np.float32); pts[:, 0], pts[:, 1], pts[:, 3] = xs, ys, 1
    o_.data.splines[0].points.foreach_set("co", pts.ravel()); o_.data.update_tag()
def box(x0, y0, x1, y1, rgb, strength=1.0):
    me = bpy.data.meshes.new("b"); me.from_pydata([(x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0)], [], [(0, 1, 2, 3)])
    o_ = bpy.data.objects.new("b", me); sc.collection.objects.link(o_); o_.parent = ov; o_.location.z = next(ZC) * 0.05; me.materials.append(mat(rgb, strength)); return o_
def setbox(b, xa, xb):
    for v, x in zip(b.data.vertices, (xa, xb, xb, xa)): v.co.x = x
    b.data.update_tag()
GREY = (0.6, 0.65, 0.75)
hm = lambda t: f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}"
T_CLOCK = text(420, 700, 84, body="06:00", align="RIGHT", bold=True)     # marginesy: x +-420, y od -740 do 740 (pusty pas na krawedzi kadru)
T_TEMPO = text(420, 655, 25, (1, 0.85, 0.4), "", "RIGHT")
T_TIT = text(-420, 700, 52, body="", bold=True); T_SUB = text(-420, 625, 34, GREY, "")
SB, SBT = box(-420, 505, -420, 519, (0.9, 0.93, 1)), text(-420, 531, 26, GREY, ""); text(420, 505, 22, GREY, "Kutno, próbka 25% ruchu (MATSim)", "RIGHT")     # podzialka
GX0, GX1, GY = -10, 420, -690      # legenda predkosci = ta sama rampa co w materiale aut
ramp = G["cr"].color_ramp
for i in range(40): box(GX0 + (GX1 - GX0) * i / 40, GY, GX0 + (GX1 - GX0) * (i + 1) / 40, GY + 18, tuple(ramp.evaluate(i / 39))[:3])
text(GX0, GY + 32, 24, body="prędkość pojazdu (wolno → swobodnie)"); text(GX0, GY - 32, 24, body="0"); text(GX1, GY - 32, 24, body=f"{a.vmax*3.6:.0f} km/h", align="RIGHT")
FLG = []   # legenda blyskow: tylko na poczatku
for k, (rgb, lab) in enumerate([(HOME, "start: dom"), (WORK, "dojazd do pracy"), (ENTRY, "wjazd do miasta")]):
    FLG += [box(-420, -724 + k * 34, -394, -702 + k * 34, rgb) if False else box(-420, -716 + (2 - k) * 34 - 4, -394, -716 + (2 - k) * 34 + 20, rgb), text(-380, -716 + (2 - k) * 34, 24, body=lab)]
AXF = NF - 1; NP = 220; AXT = AXF * STEP
CX0, CX1, CY0, CY1 = -420, 420, -575, -500
box(CX0, CY0 - 2, CX1, CY0, (0.4, 0.45, 0.55))
cnt = VIS.sum(1).astype(float); msp = np.array([np.minimum(SPD[f][VIS[f]], 25).mean() * 3.6 if VIS[f].any() else 0 for f in range(NF)])
GF = np.arange(NP) * AXF / (NP - 1); CN = np.interp(GF, np.arange(NF), cnt) / cnt.max(); CS = np.interp(GF, np.arange(NF), msp) / VK
L_CNT, L_SPD = line((0.2, 0.9, 1), NP, 2.0), line((1.0, 0.6, 0.15), NP, 2.0)
for hh in (6, 10, 14, 18): text(CX0 + (CX1 - CX0) * (hh * 3600 - T0) / AXT, CY0 - 32, 22, GREY, f"{hh:02d}:00", "CENTER")
text(CX0, CY1 + 16, 24, (0.2, 0.9, 1), "pojazdy w sieci"); text(CX0 + 300, CY1 + 16, 24, (1, 0.6, 0.15), f"średnia prędkość (0–{VK:.0f} km/h)")
tx = lambda t: -420 + 840 * (t - T0) / AXT        # os czasu panelu agenta = caly zbakowany dzien
RED = (1, 0.15, 0.1)
AG = [text(-420, -330, 32, (1, 0.35, 0.3), "agent " + AID, bold=True), text(-420, -372, 22, GREY, "dom (niebieski) · podróż (czerwony) · praca (biały)"),
      box(-420, -415, 420, -395, (0.15, 0.3, 0.55)), box(tx(DEP1), -415, tx(ARR1), -395, RED), box(tx(ARR1), -415, tx(DEP2), -395, (1, 1, 1)), box(tx(DEP2), -415, tx(ARR2), -395, RED),
      text(-420, -447, 22, GREY, "06:00"), text(420, -447, 22, GREY, hm(frames[-1]), "RIGHT")]
BAR_C = box(0, -421, 0, -389, (1, 0.8, 0.1)); AG.append(BAR_C)
trail_c = bpy.data.curves.new("trail", "CURVE"); trail_c.dimensions = "3D"; trail_c.splines.new("POLY").points.add(len(TP) - 1)
trail = bpy.data.objects.new("trail", trail_c); sc.collection.objects.link(trail); trail_c.materials.append(mat((1, 0.15, 0.1), 1.0))
mk_m = bpy.data.meshes.new("mk"); mk = bpy.data.objects.new("mk", mk_m); b_ = bmesh.new(); bmesh.ops.create_cube(b_, size=1); b_.to_mesh(mk_m); b_.free()
sc.collection.objects.link(mk); mk_m.materials.append(mat((1, 1, 1), 6))
FL_END = S(7)      # blyski aktywnosci tylko w pierwszych 7 s
NICE = [100, 200, 500, 1000, 2000, 5000, 10000, 20000]

def caption(kd, o, t, f):
    if kd == "S1": return ("Cały powiat", "błyski: początek aktywności\n(dom / praca / wjazd do miasta)" if o < FL_END else "poranny ruch dojazdowy")
    if kd == "ZIN1": return ("Wybieramy agenta", f"mieszkaniec Kutna ({AID})\nrano jedzie z domu do pracy")
    if kd in ("FOL1", "FOL2"):
        d0, d1 = (DEP1, ARR1) if kd == "FOL1" else (DEP2, ARR2)
        tit = "Jedzie do pracy" if kd == "FOL1" else "Wraca do domu"
        if t < d0: return (tit, "jeszcze stoi")
        if t > d1: return ("Dojechał do pracy" if kd == "FOL1" else "Jest w domu", f"podróż zajęła {(d1 - d0) / 60:.0f} min")
        return (tit, f"{agent_v(f):.0f} km/h · {(t - d0) / 60:.0f} min jazdy")
    if kd == "ZK": return ("Agent jest w pracy", "oddalamy się na Kutno")
    if kd == "WORK": return ("Agent w pracy", f"od {hm(ARR1)} do {hm(DEP2)}\nczas przyspieszony, auta jeżdżą dalej")
    if kd == "ZIN2": return ("Koniec pracy", "agent wraca do domu")
    if kd == "HOLD": return ("Jest w domu", f"podróż zajęła {(ARR2 - DEP2) / 60:.0f} min")
    if kd == "ZP": return ("Oddalamy się", "na cały powiat")
    return ("Reszta dnia", "czas przyspieszony do 20:00")

def apply(o):
    o = min(max(o, 0), TOT - 1); shot, f, c, orth = state(o); t = TT[o]
    cs_ = max(3.2, orth / 430); fs = max(6, orth / 215)
    cam.location = (c[0], c[1], 5000); cd.ortho_scale = orth; ov.scale = (orth / 1000,) * 3
    set_net(float(np.clip(orth / 1000, 2.5, 60)), float(max(6, orth / 470)))
    f0 = min(int(f), NF - 2); u = f - f0
    co = np.zeros((N, 3), np.float32); co[:, :2] = lerp(POS[f0], POS[f0 + 1], u); co[:, 2] = 3.0; co[~VIS[f0]] = (1e7, 1e7, -1e4)
    pm.vertices.foreach_set("co", co.ravel()); fi_ = f0 if u < .5 else f0 + 1
    pm.attributes["heading"].data.foreach_set("value", HEAD[fi_]); pm.attributes["speed"].data.foreach_set("value", SPD[fi_]); pm.update()
    mod[sid] = cs_
    ag = (t - EVT) / FADE; on = (ag >= 0) & (ag < 1) & (o < FL_END)
    fc = np.zeros((NE, 3), np.float32); fc[:, :2] = np.where(on[:, None], EXY, 1e7); fc[:, 2] = np.where(on, 6.0, -1e4)
    fm.vertices.foreach_set("co", fc.ravel()); fm.attributes["age"].data.foreach_set("value", np.where(on, ag, 1.0).astype(np.float32))
    fm.attributes["cat"].data.foreach_set("value", CAT); fm.update(); fmod[fid] = fs
    for o_ in FLG: o_.hide_render = o >= FL_END
    T_CLOCK.data.body = hm(t); r = (TT[o + 1] - TT[o]) * FPS / 60
    T_TEMPO.data.body = "1 s filmu = 1 min symulacji" if r < 1.05 else f"1 s filmu = {r:.0f} min (przyspieszone)"
    T_TIT.data.body, T_SUB.data.body = caption(shot, o, t, f)
    L = max([n_ for n_ in NICE if n_ <= orth * 0.18] or [100]); setbox(SB, -420, -420 + L / (orth / 1000)); SBT.data.body = f"{L/1000:g} km" if L >= 1000 else f"{L} m"
    kk = np.minimum(GF, f); xs = CX0 + (CX1 - CX0) * kk / AXF
    setline(L_CNT, xs, CY0 + (CY1 - CY0) * np.interp(kk, GF, CN)); setline(L_SPD, xs, CY0 + (CY1 - CY0) * np.interp(kk, GF, CS))
    inT = shot != "S1"
    for o_ in AG: o_.hide_render = not inT
    trail.hide_render = mk.hide_render = not inT
    if inT:
        j = int(np.clip(f - A0, 0, len(TP) - 1)); pts = np.ones((len(TP), 4), np.float32); pts[:, :2] = TP; pts[:, 2] = 1
        pts[j + 1:, :2] = TP[j]; trail_c.splines[0].points.foreach_set("co", pts.ravel()); trail_c.bevel_depth = max(4, orth / 300); trail_c.update_tag()
        p = agent_xy(f); mk.location = (p[0], p[1], 8); mk.scale = (cs_ * 4,) * 3
        xc = tx(t); setbox(BAR_C, xc - 2.5, xc + 2.5)

def on_story(scene, *_): apply(scene.frame_current)
bpy.app.handlers.frame_change_pre.clear(); bpy.app.handlers.frame_change_pre.append(on_story)
sc.frame_start, sc.frame_end = 0, TOT - 1
print("TOTAL output frames", TOT, "=", round(TOT / sa.fps, 1), "s")
if sa.story or sa.story_stills or sa.story_range:
    out = Path(a.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    for s in filter(None, sa.story_stills.split(",")):
        sc.frame_set(int(s)); sc.render.filepath = str(out / f"story6_{int(s):04d}.png"); bpy.ops.render.render(write_still=True)
    if sa.story or sa.story_range:
        if sa.story_range: sc.frame_start, sc.frame_end = sa.story_range
        sc.render.image_settings.file_format = "PNG"; sc.render.filepath = str(out / "f_"); bpy.ops.render.render(animation=True)   # klatki f_NNNN.png; mp4 skleja ffmpeg
