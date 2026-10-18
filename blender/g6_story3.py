"""G6: film v3 - historia jednego agenta (powiat -> dojazd do pracy -> Kutno w przyspieszeniu na czas pracy -> powrot do domu).
Dane: output/g6_blender_day (bake --t1 54600 --step 10). Reuzywa sceny z g6_load.py (runpy). Render:
 blender -b --factory-startup --python blender/g6_story3.py -- --data output/g6_blender_day --res 1280 720 --net-radius 1e9 --story
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
sc.render.fps = sa.fps; sc.eevee.taa_render_samples = 16
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
fmat = bpy.data.materials.new("flash"); fmat.use_nodes = True; t = fmat.node_tree; t.nodes.clear()
ac = t.nodes.new("ShaderNodeAttribute"); ac.attribute_name = "col"; ac.attribute_type = "GEOMETRY"
aa = t.nodes.new("ShaderNodeAttribute"); aa.attribute_name = "age"; aa.attribute_type = "GEOMETRY"
inv = t.nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0
sq = t.nodes.new("ShaderNodeMath"); sq.operation = "MULTIPLY"; sq2 = t.nodes.new("ShaderNodeMath"); sq2.operation = "MULTIPLY"; sq2.inputs[1].default_value = 8.0
fe = t.nodes.new("ShaderNodeEmission"); fo_out = t.nodes.new("ShaderNodeOutputMaterial")
t.links.new(aa.outputs["Fac"], inv.inputs[1]); t.links.new(inv.outputs[0], sq.inputs[0]); t.links.new(inv.outputs[0], sq.inputs[1])
t.links.new(sq.outputs[0], sq2.inputs[0]); t.links.new(sq2.outputs[0], fe.inputs["Strength"]); t.links.new(ac.outputs["Color"], fe.inputs["Color"])
tr = t.nodes.new("ShaderNodeBsdfTransparent"); mx = t.nodes.new("ShaderNodeMixShader"); t.links.new(sq.outputs[0], mx.inputs[0])   # zanika przezroczystoscia
t.links.new(tr.outputs[0], mx.inputs[1]); t.links.new(fe.outputs[0], mx.inputs[2]); t.links.new(mx.outputs[0], fo_out.inputs[0])
fsm.inputs["Material"].default_value = fmat


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
run(S(10), "S1"); run(S(3), "ZIN1"); run(int(np.ceil((ARR1 + 120 - tt[-1]) / BASE)), "FOL1"); run(S(3), "ZK")
n = S(10); k = np.arange(n); m = smooth(np.clip(np.minimum(k / 30, (n - 1 - k) / 30), 0, 1))   # praca: 10 s, plynne przyspieszenie
D = (DEP2 - 3 * 60) - tt[-1]; vm = BASE + (D - BASE * n) / m.sum(); run(n, "WORK", BASE + (vm - BASE) * m)
run(S(3), "ZIN2"); run(int(np.ceil((ARR2 + 120 - tt[-1]) / BASE)), "FOL2"); run(S(3), "HOLD")
TT = np.array(tt); TOT = len(kinds); KS = {}
for o, kd in enumerate(kinds): KS.setdefault(kd, [o, 0])[1] += 1
print({k_: (v[0] / FPS, v[1] / FPS) for k_, v in KS.items()}, "razem", TOT / FPS, "s; szczyt tempa", vm * FPS / 60, "min/s")
assert TT[-1] < frames[-1]
ex = E[:, [0, 2]].ravel(); ey = E[:, [1, 3]].ravel()
PC = ((ex.min() + ex.max()) / 2, (ey.min() + ey.max()) / 2); PV = 1.12 * max(ex.max() - ex.min(), (ey.max() - ey.min()) * 16 / 9)   # caly powiat
KV = 14000.0; AV = 1100.0
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
    return kd, f, tuple(lerp(Z0, ag, k)), mixlog(KV, AV, k)      # ZIN2

# ---------- siec o szerokosci zaleznej od zoomu
net = G["net"].data; EA, EB = E[:, :2], E[:, 2:]; ED = EB - EA; EN = np.stack([-ED[:, 1], ED[:, 0]], 1) / np.maximum(np.hypot(ED[:, 0], ED[:, 1]), 1e-6)[:, None]
def set_net(w):
    h = EN * w / 2; v = np.concatenate([EA + h, EA - h, EB - h, EB + h], 0)
    net.vertices.foreach_set("co", np.c_[v, np.zeros(len(v))].astype(np.float32).ravel()); net.update()

# ---------- nakladki: dzieci pustego obiektu na kamerze; jednostka = 1/1000 szerokosci kadru
ov = bpy.data.objects.new("overlay", None); sc.collection.objects.link(ov); ov.parent = cam; ov.location = (0, 0, -10)
FONT, FONTB = (bpy.data.fonts.load(f"C:/Windows/Fonts/{n_}.ttf") for n_ in ("segoeui", "segoeuib"))   # Segoe UI: polskie znaki
def mat(rgb, strength=1.0):
    m = bpy.data.materials.new("o"); m.use_nodes = True; t = m.node_tree; t.nodes.clear()
    e = t.nodes.new("ShaderNodeEmission"); e.inputs["Color"].default_value = (*rgb, 1); e.inputs["Strength"].default_value = strength
    o_ = t.nodes.new("ShaderNodeOutputMaterial"); t.links.new(e.outputs[0], o_.inputs[0]); return m
def text(x, y, size, rgb=(0.9, 0.93, 1), body="", align="LEFT", bold=False):
    c = bpy.data.curves.new("t", "FONT"); c.body = body; c.size = size; c.align_x = align; c.font = FONTB if bold else FONT
    o_ = bpy.data.objects.new("t", c); sc.collection.objects.link(o_); o_.parent = ov; o_.location = (x, y, 0); c.materials.append(mat(rgb)); return o_
def line(rgb, n, w=1.6):
    c = bpy.data.curves.new("l", "CURVE"); c.dimensions = "3D"; c.bevel_depth = w; c.splines.new("POLY").points.add(n - 1)
    o_ = bpy.data.objects.new("l", c); sc.collection.objects.link(o_); o_.parent = ov; c.materials.append(mat(rgb)); return o_
def setline(o_, xs, ys):
    pts = np.zeros((len(xs), 4), np.float32); pts[:, 0], pts[:, 1], pts[:, 3] = xs, ys, 1
    o_.data.splines[0].points.foreach_set("co", pts.ravel()); o_.data.update_tag()
def box(x0, y0, x1, y1, rgb, strength=1.0):
    me = bpy.data.meshes.new("b"); me.from_pydata([(x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0)], [], [(0, 1, 2, 3)])
    o_ = bpy.data.objects.new("b", me); sc.collection.objects.link(o_); o_.parent = ov; me.materials.append(mat(rgb, strength)); return o_
def setbox(b, xa, xb):
    for v, x in zip(b.data.vertices, (xa, xb, xb, xa)): v.co.x = x
    b.data.update_tag()
GREY = (0.6, 0.65, 0.75)
T_CLOCK = text(480, 226, 46, body="06:00", align="RIGHT", bold=True)
T_TEMPO = text(480, 208, 13, (1, 0.85, 0.4), "", "RIGHT"); text(480, 192, 10, GREY, "Kutno, próbka 25% ruchu (MATSim)", "RIGHT")
T_TIT = text(-480, 236, 28, body="", bold=True); T_SUB = text(-480, 208, 15, GREY, "")
SB, SBT = box(-480, 176, -480, 182, (0.9, 0.93, 1)), text(-480, 186, 11, GREY, "")     # podzialka
GX0, GX1, GY = 255, 480, -255      # legenda predkosci = ta sama rampa co w materiale aut
ramp = G["cr"].color_ramp
for i in range(40): box(GX0 + (GX1 - GX0) * i / 40, GY, GX0 + (GX1 - GX0) * (i + 1) / 40, GY + 12, tuple(ramp.evaluate(i / 39))[:3])
text(GX0, GY + 20, 11, body="prędkość pojazdu (wolno → swobodnie)"); text(GX0, GY - 16, 11, body="0"); text(GX1, GY - 16, 11, body=f"{a.vmax*3.6:.0f} km/h", align="RIGHT")
FLG = []   # legenda blyskow: tylko na poczatku
for k, (rgb, lab) in enumerate([(HOME, "start: dom"), (WORK, "dojazd do pracy"), (ENTRY, "wjazd do miasta")]):
    FLG += [box(255, -150 - k * 18, 267, -140 - k * 18, rgb), text(275, -151 - k * 18, 11, body=lab)]
# wykres: pojazdy w sieci + srednia predkosc, os czasu = caly zbakowany dzien
AXF = NF - 1; NP = 220; AXT = AXF * STEP
CX0, CX1, CY0, CY1 = -480, 130, -262, -170
box(CX0, CY0 - 1, CX1, CY0, (0.4, 0.45, 0.55), 0.6)
cnt = VIS.sum(1).astype(float); msp = np.array([np.minimum(SPD[f][VIS[f]], 25).mean() * 3.6 if VIS[f].any() else 0 for f in range(NF)])
GF = np.arange(NP) * AXF / (NP - 1); CN = np.interp(GF, np.arange(NF), cnt) / cnt.max(); CS = np.interp(GF, np.arange(NF), msp) / 50
L_CNT, L_SPD = line((0.2, 0.9, 1), NP), line((1.0, 0.6, 0.15), NP)
for hh in (6, 9, 12, 15): text(CX0 + (CX1 - CX0) * (hh * 3600 - T0) / AXT, CY0 - 14, 10, GREY, f"{hh:02d}:00", "CENTER")
text(CX0, CY1 + 10, 11, (0.2, 0.9, 1), "pojazdy w sieci"); text(CX0 + 130, CY1 + 10, 11, (1, 0.6, 0.15), "średnia prędkość (0–50 km/h)")
tx = lambda t: 250 + 230 * (t - T0) / AXT        # os czasu panelu agenta = caly zbakowany dzien
AG = [text(250, 168, 13, (1, 0.35, 0.3), "agent " + AID, bold=True), box(250, 128, 480, 138, (0.15, 0.3, 0.55)),
      box(tx(DEP1), 128, tx(ARR1), 138, (1, 0.2, 0.15)), box(tx(ARR1), 128, tx(DEP2), 138, (1, 1, 1)), box(tx(DEP2), 128, tx(ARR2), 138, (1, 0.2, 0.15)),
      text(250, 150, 10, GREY, "dom (niebieski) · podróż (czerwony) · praca (biały)"),
      text(250, 112, 10, GREY, "06:00"), text(480, 112, 10, GREY, f"{int(frames[-1] // 3600):02d}:{int(frames[-1] % 3600 // 60):02d}", "RIGHT")]
BAR_C = box(0, 122, 0, 144, (1, 0.8, 0.1), 3); AG.append(BAR_C)
trail_c = bpy.data.curves.new("trail", "CURVE"); trail_c.dimensions = "3D"; trail_c.splines.new("POLY").points.add(len(TP) - 1)
trail = bpy.data.objects.new("trail", trail_c); sc.collection.objects.link(trail); trail_c.materials.append(mat((1, 0.15, 0.1), 1.0))
mk_m = bpy.data.meshes.new("mk"); mk = bpy.data.objects.new("mk", mk_m); b_ = bmesh.new(); bmesh.ops.create_cube(b_, size=1); b_.to_mesh(mk_m); b_.free()
sc.collection.objects.link(mk); mk_m.materials.append(mat((1, 1, 1), 6))
hm = lambda t: f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}"
FL_END = S(7)      # blyski aktywnosci tylko w pierwszych 7 s
NICE = [100, 200, 500, 1000, 2000, 5000, 10000, 20000]

def caption(kd, o, t, f):
    if kd == "S1": return ("Cały powiat: sieć drogowa i ruch", "błyski: początek aktywności (dom / praca / wjazd do miasta)" if o < FL_END else "poranny ruch dojazdowy")
    if kd == "ZIN1": return ("Wybieramy jednego agenta", f"mieszkaniec Kutna ({AID}) rano jedzie z domu do pracy")
    if kd in ("FOL1", "FOL2"):
        A, B_, d0, d1 = (A0, A1, DEP1, ARR1) if kd == "FOL1" else (B0, B1, DEP2, ARR2)
        tit = "Agent jedzie do pracy" if kd == "FOL1" else "Agent wraca z pracy do domu"
        if t < d0: return (tit, "jeszcze stoi")
        if t > d1: return ("Agent dojechał do pracy" if kd == "FOL1" else "Agent jest w domu", f"podróż zajęła {(d1 - d0) / 60:.0f} min")
        return (tit, f"{agent_v(f):.0f} km/h · {(t - d0) / 60:.0f} min jazdy")
    if kd == "ZK": return ("Agent jest w pracy", "oddalamy się na Kutno")
    if kd == "WORK": return (f"Agent w pracy (od {hm(ARR1)} do {hm(DEP2)})", "czas przyspieszony · reszta miasta dalej jeździ")
    if kd == "ZIN2": return ("Koniec pracy", "agent wraca do domu")
    return ("Agent jest w domu", f"podróż zajęła {(ARR2 - DEP2) / 60:.0f} min")

def apply(o):
    o = min(max(o, 0), TOT - 1); shot, f, c, orth = state(o); t = TT[o]
    cs_ = max(3.2, orth / 640); fs = max(6, orth / 320)
    cam.location = (c[0], c[1], 5000); cd.ortho_scale = orth; ov.scale = (orth / 1000,) * 3
    set_net(float(np.clip(orth / 450, 12, 160)))
    f0 = min(int(f), NF - 2); u = f - f0
    co = np.zeros((N, 3), np.float32); co[:, :2] = lerp(POS[f0], POS[f0 + 1], u); co[:, 2] = 3.0; co[~VIS[f0]] = (1e7, 1e7, -1e4)
    pm.vertices.foreach_set("co", co.ravel()); fi_ = f0 if u < .5 else f0 + 1
    pm.attributes["heading"].data.foreach_set("value", HEAD[fi_]); pm.attributes["speed"].data.foreach_set("value", SPD[fi_]); pm.update()
    mod[sid] = cs_
    ag = (t - EVT) / FADE; on = (ag >= 0) & (ag < 1) & (o < FL_END)
    fc = np.zeros((NE, 3), np.float32); fc[:, :2] = np.where(on[:, None], EXY, 1e7); fc[:, 2] = np.where(on, 6.0, -1e4)
    fm.vertices.foreach_set("co", fc.ravel()); fm.attributes["age"].data.foreach_set("value", np.where(on, ag, 1.0).astype(np.float32))
    fm.attributes["col"].data.foreach_set("color", ECOL.ravel()); fm.update(); fmod[fid] = fs
    for o_ in FLG: o_.hide_render = o >= FL_END
    T_CLOCK.data.body = hm(t); r = (TT[o + 1] - TT[o]) * FPS / 60
    T_TEMPO.data.body = "tempo: 1 s filmu = 1 min symulacji" if r < 1.05 else f"tempo: 1 s filmu = {r:.0f} min symulacji (przyspieszone)"
    T_TIT.data.body, T_SUB.data.body = caption(shot, o, t, f)
    L = max([n_ for n_ in NICE if n_ <= orth * 0.18] or [100]); setbox(SB, -480, -480 + L / (orth / 1000)); SBT.data.body = f"{L/1000:g} km" if L >= 1000 else f"{L} m"
    kk = np.minimum(GF, f); xs = CX0 + (CX1 - CX0) * kk / AXF
    setline(L_CNT, xs, CY0 + (CY1 - CY0) * np.interp(kk, GF, CN)); setline(L_SPD, xs, CY0 + (CY1 - CY0) * np.interp(kk, GF, CS))
    inT = shot != "S1"
    for o_ in AG: o_.hide_render = not inT
    trail.hide_render = mk.hide_render = not inT
    if inT:
        j = int(np.clip(f - A0, 0, len(TP) - 1)); pts = np.ones((len(TP), 4), np.float32); pts[:, :2] = TP; pts[:, 2] = 1
        pts[j + 1:, :2] = TP[j]; trail_c.splines[0].points.foreach_set("co", pts.ravel()); trail_c.bevel_depth = max(4, orth / 450); trail_c.update_tag()
        p = agent_xy(f); mk.location = (p[0], p[1], 8); mk.scale = (cs_ * 4,) * 3
        xc = tx(t); setbox(BAR_C, xc - 1, xc + 1)

def on_story(scene, *_): apply(scene.frame_current)
bpy.app.handlers.frame_change_pre.clear(); bpy.app.handlers.frame_change_pre.append(on_story)
sc.frame_start, sc.frame_end = 0, TOT - 1
print("TOTAL output frames", TOT, "=", round(TOT / sa.fps, 1), "s")
if sa.story or sa.story_stills or sa.story_range:
    out = Path(a.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    for s in filter(None, sa.story_stills.split(",")):
        sc.frame_set(int(s)); sc.render.filepath = str(out / f"story3_{int(s):04d}.png"); bpy.ops.render.render(write_still=True)
    if sa.story or sa.story_range:
        if sa.story_range: sc.frame_start, sc.frame_end = sa.story_range
        sc.render.image_settings.file_format = "FFMPEG"; sc.render.ffmpeg.format = "MPEG4"; sc.render.ffmpeg.codec = "H264"
        sc.render.ffmpeg.constant_rate_factor = "MEDIUM"; sc.render.filepath = str(out / "story_v3.mp4"); bpy.ops.render.render(animation=True)
