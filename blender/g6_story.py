"""G6: dluzsza wizualizacja 'narracyjna' (flashe aktywnosci, sledzenie agenta, wykresy w kadrze, legenda).
Wersja 2 (1 s = 1 min, powiat -> agent -> Kutno -> powiat; --net-radius 1e9). Reuzywa sceny z g6_load.py (runpy). Render calosci / wybranych klatek:
 blender -b --factory-startup --python blender/g6_story.py -- --res 1280 720 --story
 blender -b --factory-startup --python blender/g6_story.py -- --res 1280 720 --story-stills 100,500,900
 ... --story-range 0 120   (fragment filmu)"""
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

# ---------- agent: mieszkaniec startujacy ~06:10-06:13 (zoom konczy sie o 06:13), najdluzszy przejazd <= 45 min i do 07:00
TEMPO = 60.0                         # s symulacji na 1 s filmu (1 s = 1 min)
FPS = sa.fps; DF = TEMPO / FPS / STEP  # klatek .npz na klatke filmu (0.4)
cand = []
for j in range(N):
    w = np.where(VIS[:, j])[0]
    if ids[j][0] == "r" and len(w) and 110 <= w[0] <= 156 and w[-1] < 720 and len(w) <= 540 and VIS[w[0] - 1, j] == 0: cand.append((len(w), j, w[0], w[-1]))
dur, AJ, A0, A1 = max(cand); print("agent", ids[AJ], "klatki", A0, A1, "czas", dur * STEP / 60, "min")
apos = POS[A0:A1 + 1, AJ]; aspd = SPD[A0:A1 + 1, AJ] * 3.6; AF = np.arange(A0, A1 + 1)

# ---------- harmonogram (klatki wyjscia): 10 s powiat | 3 s zoom na agenta | follow | 3 s zoom na Kutno | 10 s | 5 s zoom na powiat | 10 s
S = lambda s: int(s * FPS)
O1, O2 = S(10), S(13); O3 = max(O2 + S(5), int((A1 + 8) / DF)); O4 = O3 + S(3); O5 = O4 + S(10); O6 = O5 + S(5); TOT = O6 + S(10)
print("faza follow", (O3 - O2) / FPS, "s; razem", TOT / FPS, "s; koniec symulacji f =", TOT * DF)
assert TOT * DF < NF - 1
ex = np.concatenate([E[:, [0, 2]].ravel(), ]); ey = E[:, [1, 3]].ravel()
PC = ((ex.min() + ex.max()) / 2, (ey.min() + ey.max()) / 2); PV = 1.12 * max(ex.max() - ex.min(), (ey.max() - ey.min()) * 16 / 9)   # caly powiat
KV = 14000.0                                               # widok Kutna (wiekszy niz poprzednio)
AV = 1100.0                                                # widok agenta
ease = lambda k: k * k * (3 - 2 * k)
mixlog = lambda a_, b_, k: float(np.exp(lerp(np.log(a_), np.log(b_), k)))
def agent_xy(f):
    f = min(max(f, A0), A1); return np.array([np.interp(f, AF, apos[:, 0]), np.interp(f, AF, apos[:, 1])])
def state(o):
    """-> shot, f, cam(x,y), ortho"""
    f = o * DF
    if o < O1: return "S1", f, PC, PV
    if o < O2: k = ease((o - O1) / (O2 - O1)); return "ZIN", f, tuple(lerp(np.array(PC), agent_xy(f), k)), mixlog(PV, AV, k)
    if o < O3: return "FOL", f, tuple(agent_xy(f)), AV
    if o < O4: k = ease((o - O3) / (O4 - O3)); return "ZK", f, tuple(lerp(agent_xy(f), np.zeros(2), k)), mixlog(AV, KV, k)
    if o < O5: return "HK", f, (0, 0), KV
    if o < O6: k = ease((o - O5) / (O6 - O5)); return "ZP", f, tuple(lerp(np.zeros(2), np.array(PC), k)), mixlog(KV, PV, k)
    return "HP", f, PC, PV

# ---------- siec o szerokosci zaleznej od zoomu (jedna siatka, wierzcholki przeliczane co klatke)
net = G["net"].data; EA, EB = E[:, :2], E[:, 2:]; ED = EB - EA; EN = np.stack([-ED[:, 1], ED[:, 0]], 1) / np.maximum(np.hypot(ED[:, 0], ED[:, 1]), 1e-6)[:, None]
def set_net(w):
    h = EN * w / 2; v = np.concatenate([EA + h, EA - h, EB - h, EB + h], 0)
    net.vertices.foreach_set("co", np.c_[v, np.zeros(len(v))].astype(np.float32).ravel()); net.update()

# ---------- nakladki: dzieci pustego obiektu na kamerze; jednostka = 1/1000 szerokosci kadru (kadr 1000 x 562)
ov = bpy.data.objects.new("overlay", None); sc.collection.objects.link(ov); ov.parent = cam; ov.location = (0, 0, -10)
def mat(rgb, strength=1.0):
    m = bpy.data.materials.new("o"); m.use_nodes = True; t = m.node_tree; t.nodes.clear()
    e = t.nodes.new("ShaderNodeEmission"); e.inputs["Color"].default_value = (*rgb, 1); e.inputs["Strength"].default_value = strength
    o_ = t.nodes.new("ShaderNodeOutputMaterial"); t.links.new(e.outputs[0], o_.inputs[0]); return m
def text(x, y, size, rgb=(0.9, 0.93, 1), body="", align="LEFT"):
    c = bpy.data.curves.new("t", "FONT"); c.body = body; c.size = size; c.align_x = align
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
T_CLOCK = text(480, 232, 46, body="06:00", align="RIGHT")
text(480, 214, 12, (1, 0.85, 0.4), "tempo: 1 s filmu = 1 min symulacji", "RIGHT"); text(480, 199, 10, GREY, "Kutno, próbka 25% ruchu (MATSim)", "RIGHT")
T_TIT = text(-480, 238, 26, body=""); T_SUB = text(-480, 212, 14, GREY, "")
SB, SBT = box(-480, 180, -480, 186, (0.9, 0.93, 1)), text(-480, 190, 11, GREY, "")     # podzialka
GX0, GX1, GY = 255, 480, -255      # legenda predkosci = ta sama rampa co w materiale aut
ramp = G["cr"].color_ramp
for i in range(40): box(GX0 + (GX1 - GX0) * i / 40, GY, GX0 + (GX1 - GX0) * (i + 1) / 40, GY + 12, tuple(ramp.evaluate(i / 39))[:3])
text(GX0, GY + 20, 11, body="prędkość pojazdu (wolno → swobodnie)"); text(GX0, GY - 16, 11, body="0"); text(GX1, GY - 16, 11, body=f"{a.vmax*3.6:.0f} km/h", align="RIGHT")
for k, (rgb, lab) in enumerate([(HOME, "start: dom"), (WORK, "dojazd do pracy"), (ENTRY, "wjazd do miasta")]):
    box(255, -150 - k * 18, 267, -140 - k * 18, rgb); text(275, -149 - k * 18, 11, body=lab)
# wykres: pojazdy w sieci + srednia predkosc; os czasu = 06:00 .. koniec filmu zaokraglony do 15 min
FEND = TOT * DF; AXF = min(NF - 1, int(np.ceil(FEND * STEP / 900) * 900 / STEP)); NP = 150
CX0, CX1, CY0, CY1 = -480, 130, -262, -170
box(CX0, CY0 - 1, CX1, CY0, (0.4, 0.45, 0.55), 0.6)
cnt = VIS.sum(1).astype(float); msp = np.array([np.minimum(SPD[f][VIS[f]], 25).mean() * 3.6 if VIS[f].any() else 0 for f in range(NF)])
GF = np.arange(NP) * AXF / (NP - 1); CN = np.interp(GF, np.arange(NF), cnt) / cnt[:AXF + 1].max(); CS = np.interp(GF, np.arange(NF), msp) / 50
L_CNT, L_SPD = line((0.2, 0.9, 1), NP), line((1.0, 0.6, 0.15), NP)
for h in range(4):
    tt = 21600 + AXF * STEP * h / 3; text(CX0 + (CX1 - CX0) * h / 3, CY0 - 14, 10, GREY, f"{int(tt // 3600):02d}:{int(tt % 3600 // 60):02d}", "CENTER")
text(CX0, CY1 + 10, 11, (0.2, 0.9, 1), "pojazdy w sieci"); text(CX0 + 130, CY1 + 10, 11, (1, 0.6, 0.15), "średnia prędkość (0–50 km/h)")
TW = 3600.0; tx = lambda t: 250 + 230 * (t - frames[0]) / TW        # os czasu panelu agenta: 06:00-07:00
AG = [text(250, 168, 13, (1, 0.35, 0.3), "agent " + ids[AJ]), box(250, 128, 480, 138, (0.15, 0.3, 0.55)),
      text(250, 150, 10, GREY, "dom (niebieski) · podróż (czerwony) · praca (biały)"),
      text(250, 112, 10, GREY, "06:00"), text(480, 112, 10, GREY, "07:00", "RIGHT"), text(250, 84, 11, GREY, "prędkość agenta (0–60 km/h)"),
      box(250, 57, 480, 58, (0.4, 0.45, 0.55), 0.6)]
BAR_T, BAR_W, BAR_C = box(0, 128, 0, 138, (1, 0.2, 0.15)), box(0, 128, 0, 138, (1, 1, 1)), box(0, 124, 0, 142, (1, 1, 1), 3)
AGL = line((1, 0.35, 0.3), 60, 1.2); AG += [BAR_T, BAR_W, BAR_C, AGL]
trail_c = bpy.data.curves.new("trail", "CURVE"); trail_c.dimensions = "3D"; trail_c.splines.new("POLY").points.add(len(apos) - 1)
trail = bpy.data.objects.new("trail", trail_c); sc.collection.objects.link(trail); trail_c.materials.append(mat((1, 0.15, 0.1), 1.0))
mk_m = bpy.data.meshes.new("mk"); mk = bpy.data.objects.new("mk", mk_m); b_ = bmesh.new(); bmesh.ops.create_cube(b_, size=1); b_.to_mesh(mk_m); b_.free()
sc.collection.objects.link(mk); mk_m.materials.append(mat((1, 1, 1), 6))
KM = "agent " + ids[AJ]
TXT = {"S1": ("Cały powiat: sieć drogowa i ruch", "każda kropka to samochód · błyski: start aktywności (dom / praca / wjazd do miasta)"),
       "ZIN": ("Wybieramy jednego agenta", f"mieszkaniec Kutna ({ids[AJ]}) jedzie z domu do pracy"),
       "ZK": ("Wracamy do widoku Kutna", "agent dojechał do pracy"),
       "HK": ("Kutno: poranny ruch dojazdowy", "kolor pojazdu = prędkość na linku · czerwony = kolejka"),
       "ZP": ("Oddalamy się na cały powiat", "fiolet: pojazdy wjeżdżające do miasta spoza obszaru"),
       "HP": ("Cała sieć drogowa", "ruch narasta wraz z porannym szczytem")}
NICE = [100, 200, 500, 1000, 2000, 5000, 10000, 20000]

def apply(o):
    shot, f, c, orth = state(o)
    cs_ = max(3.2, orth / 640); fs = max(6, orth / 320); stren = 4.0
    cam.location = (c[0], c[1], 5000); cd.ortho_scale = orth; ov.scale = (orth / 1000,) * 3
    set_net(float(np.clip(orth / 450, 12, 160)))
    f0 = min(int(f), NF - 2); u = f - f0
    co = np.zeros((N, 3), np.float32); co[:, :2] = lerp(POS[f0], POS[f0 + 1], u); co[:, 2] = 3.0; co[~VIS[f0], 2] = -1e4
    pm.vertices.foreach_set("co", co.ravel()); fi_ = f0 if u < .5 else f0 + 1
    pm.attributes["heading"].data.foreach_set("value", HEAD[fi_]); pm.attributes["speed"].data.foreach_set("value", SPD[fi_]); pm.update()
    mod[sid] = cs_; ems.inputs["Strength"].default_value = stren
    t = lerp(frames[f0], frames[f0 + 1], u); ag = (t - EVT) / FADE; on = (ag >= 0) & (ag < 1)
    fc = np.zeros((NE, 3), np.float32); fc[:, :2] = EXY; fc[:, 2] = np.where(on, 6.0, -1e4)
    fm.vertices.foreach_set("co", fc.ravel()); fm.attributes["age"].data.foreach_set("value", np.where(on, ag, 1.0).astype(np.float32))
    fm.attributes["col"].data.foreach_set("color", ECOL.ravel()); fm.update(); fmod[fid] = fs
    T_CLOCK.data.body = f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}"
    # podpis: co sie dzieje teraz
    if shot == "FOL":
        j = f - A0; v = float(np.interp(f, AF, aspd)); el = int(max(0, min(j, A1 - A0)) * STEP // 60)
        st = "jeszcze w domu" if j < 0 else ("dojechał do pracy" if f > A1 else f"w drodze · {v:.0f} km/h · {el} min jazdy")
        T_TIT.data.body, T_SUB.data.body = f"Śledzimy agenta {ids[AJ]}", st
    else: T_TIT.data.body, T_SUB.data.body = TXT[shot]
    L = max([n for n in NICE if n <= orth * 0.18] or [100]); setbox(SB, -480, -480 + L / (orth / 1000)); SBT.data.body = f"{L/1000:g} km" if L >= 1000 else f"{L} m"
    kk = np.minimum(GF, f); xs = CX0 + (CX1 - CX0) * kk / AXF
    setline(L_CNT, xs, CY0 + (CY1 - CY0) * np.interp(kk, GF, CN)); setline(L_SPD, xs, CY0 + (CY1 - CY0) * np.interp(kk, GF, CS))
    inP = shot in ("ZIN", "FOL", "ZK"); inT = inP or shot in ("HK", "ZP")
    for o_ in AG: o_.hide_render = not inP
    trail.hide_render = mk.hide_render = not inT
    if inT:
        j = int(np.clip(f - A0, 0, len(apos) - 1)); pts = np.ones((len(apos), 4), np.float32); pts[:, :2] = apos; pts[:, 2] = 1
        pts[j + 1:, :2] = apos[j]; trail_c.splines[0].points.foreach_set("co", pts.ravel()); trail_c.bevel_depth = max(4, orth / 450); trail_c.update_tag()
        p = agent_xy(f); mk.location = (p[0], p[1], 8); mk.scale = (cs_ * 4,) * 3
    if inP:
        x0, x1, xc = tx(frames[A0]), tx(frames[A1]), tx(t)
        setbox(BAR_T, x0, min(max(xc, x0), x1)); setbox(BAR_W, x1, max(min(xc, 480), x1)); setbox(BAR_C, xc - 1, xc + 1)
        j = int(np.clip(f - A0, 0, len(apos) - 1)); m_ = np.minimum(np.arange(60) / 59 * (len(apos) - 1), j)
        setline(AGL, 250 + 230 * m_ / (len(apos) - 1), 58 + 55 * np.interp(m_, np.arange(len(apos)), aspd) / 60)

def on_story(scene, *_): apply(scene.frame_current)
bpy.app.handlers.frame_change_pre.clear(); bpy.app.handlers.frame_change_pre.append(on_story)
sc.frame_start, sc.frame_end = 0, TOT - 1
print("TOTAL output frames", TOT, "=", round(TOT / sa.fps, 1), "s")
if sa.story or sa.story_stills or sa.story_range:
    out = Path(a.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    for s in filter(None, sa.story_stills.split(",")):
        sc.frame_set(int(s)); sc.render.filepath = str(out / f"story2_{int(s):04d}.png"); bpy.ops.render.render(write_still=True)
    if sa.story or sa.story_range:
        if sa.story_range: sc.frame_start, sc.frame_end = sa.story_range
        sc.render.image_settings.file_format = "FFMPEG"; sc.render.ffmpeg.format = "MPEG4"; sc.render.ffmpeg.codec = "H264"
        sc.render.ffmpeg.constant_rate_factor = "MEDIUM"; sc.render.filepath = str(out / "story_v2.mp4"); bpy.ops.render.render(animation=True)
