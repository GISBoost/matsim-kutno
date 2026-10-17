"""G6: MATSim events -> pozycje pojazdow na klatke (.npz) + linie sieci (.npz) dla Blendera.
Uruchom: uv run python pipeline/g6_bake.py [--run output/d16_25pct_s4711] [--t0 21600 --t1 32400 --step 5]
Scena: 1 jednostka Blendera = 1 m, origin = (524805, 485023) EPSG:2180 (x=E, y=N)."""
import argparse, io, random, re, time
from pathlib import Path
import numpy as np
import zstandard
from lxml import etree

ORIGIN = (524805.0, 485023.0)
ATTR = re.compile(r'(\w+)="([^"]*)"')
TYPES = ("vehicle enters traffic", "entered link", "left link", "vehicle leaves traffic")


def lines(path):
    r = zstandard.ZstdDecompressor().stream_reader(open(path, "rb"))
    return io.TextIOWrapper(r, encoding="utf8", newline="")


def read_network(path):
    nodes, links = {}, {}
    for _, el in etree.iterparse(zstandard.ZstdDecompressor().stream_reader(open(path, "rb")), tag=("node", "link"), load_dtd=False, no_network=True):
        a = el.attrib
        if el.tag == "node":
            nodes[a["id"]] = (float(a["x"]) - ORIGIN[0], float(a["y"]) - ORIGIN[1])
        else:
            links[a["id"]] = (a["from"], a["to"], float(a["length"]), float(a["freespeed"]))
        el.clear()
    return nodes, links


def bake(run, t0, t1, step):
    nodes, links = read_network(run / "output_network.xml.zst")
    seg = {k: (*nodes[f], *nodes[t]) for k, (f, t, _, _) in links.items()}  # x0,y0,x1,y1
    cur, tracks, ntr = {}, [], {}  # veh -> knots [(t,x,y)] ; finished tracks [(veh,knots)]
    nev = 0
    for line in lines(run / "output_events.xml.zst"):
        if 'type="' not in line or not any(f'"{t}"' in line for t in TYPES):
            continue
        d = dict(ATTR.findall(line))
        t = float(d["time"])
        if t > t1:
            break
        nev += 1
        ty, v = d["type"], d["vehicle"]
        if ty == "vehicle enters traffic":
            x0, y0, x1, y1 = seg[d["link"]]
            p = float(d.get("relativePosition", 1.0))
            cur[v] = [(t, x0 + p * (x1 - x0), y0 + p * (y1 - y0))]
        elif v not in cur:
            continue
        elif ty == "entered link":
            cur[v].append((t, *seg[d["link"]][:2]))
        else:  # left link / leaves traffic: koniec linku
            cur[v].append((t, *seg[d["link"]][2:]))
            if ty == "vehicle leaves traffic":
                tracks.append((v, cur.pop(v)))
    tracks += list(cur.items())  # ucieta oknem
    tracks = [(v, k) for v, k in tracks if k[-1][0] >= t0]
    frames = np.arange(t0, t1 + 1e-9, step)
    F, N = len(frames), len(tracks)
    pos = np.zeros((F, N, 2), np.float32); vis = np.zeros((F, N), bool)
    head = np.zeros((F, N), np.float32); spd = np.zeros((F, N), np.float32)
    for j, (v, kn) in enumerate(tracks):
        a = np.array(kn); tt = a[:, 0]
        pos[:, j, 0] = np.interp(frames, tt, a[:, 1]); pos[:, j, 1] = np.interp(frames, tt, a[:, 2])
        vis[:, j] = (frames >= tt[0]) & (frames <= tt[-1])
        dx, dy, dt = np.diff(a[:, 1]), np.diff(a[:, 2]), np.diff(tt)
        h = np.arctan2(dy, dx); s = np.hypot(dx, dy) / np.maximum(dt, 1e-3)
        for i in range(1, len(h)):  # odcinek zerowy: dziedzicz kierunek
            if dx[i] == 0 and dy[i] == 0: h[i] = h[i - 1]
        i = np.clip(np.searchsorted(tt, frames, side="right") - 1, 0, len(h) - 1) if len(h) else None
        if i is not None: head[:, j] = h[i]; spd[:, j] = s[i]
    ids = np.array([v for v, _ in tracks])
    print(f"events={nev} tracks={N} frames={F} pos={pos.nbytes/1e6:.0f} MB")
    return dict(ids=ids, frames=frames, pos=pos, visible=vis, heading=head, speed=spd), tracks, nodes, links


def check(run, tracks, links, nodes, data, n=3, seed=1):
    """Test (a): 3 losowe pojazdy; sekwencje linkow z eventow (osobny odczyt) vs pozycje z .npz."""
    random.seed(seed)
    pick = random.sample([j for j, (_, k) in enumerate(tracks) if len(k) > 8], n)
    want = {tracks[j][0] for j in pick}
    seqs = {v: [] for v in want}  # (t_enter, t_left, link)
    for line in lines(run / "output_events.xml.zst"):
        if 'vehicle="' not in line or not any(f'"{t}"' in line for t in TYPES): continue
        d = dict(ATTR.findall(line))
        if d["vehicle"] in want and d["time"] and float(d["time"]) <= data["frames"][-1]:
            s = seqs[d["vehicle"]]
            if d["type"] in ("entered link", "vehicle enters traffic"): s.append([float(d["time"]), None, d["link"]])
            elif s and s[-1][1] is None: s[-1][1] = float(d["time"])
    for j in pick:
        v = tracks[j][0]; s = [x for x in seqs[v] if x[1] is not None]
        ok = 0
        for f, t in enumerate(data["frames"]):
            if not data["visible"][f, j]: continue
            for te, tl, l in s:
                if te <= t <= tl:
                    x0, y0, x1, y1 = [c for c in (*nodes[links[l][0]], *nodes[links[l][1]])]
                    p = data["pos"][f, j].astype(float); a = np.array([x0, y0]); b = np.array([x1, y1])
                    u = np.clip(np.dot(p - a, b - a) / max(np.dot(b - a, b - a), 1e-9), 0, 1)
                    dist = np.linalg.norm(p - (a + u * (b - a)))
                    assert dist < 0.5, (v, t, l, dist)
                    ok += 1; break
        assert ok > 3, (v, ok)
        # pojazd widoczny tylko w [pierwszy enter, ostatni left] trasy (okno)
        vf = data["frames"][data["visible"][:, j]]
        assert vf[0] >= s[0][0] - 1e-6 and vf[-1] <= s[-1][1] + 1e-6, (v, vf[[0, -1]], s[0][0], s[-1][1])
        print(f"check OK {v}: {ok} klatek na linkach z eventow, {len(s)} linkow")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="output/d16_25pct_s4711"); ap.add_argument("--out", default="output/g6_blender")
    ap.add_argument("--t0", type=float, default=6 * 3600); ap.add_argument("--t1", type=float, default=9 * 3600)
    ap.add_argument("--step", type=float, default=5.0)
    ap.add_argument("--no-check", action="store_true")
    a = ap.parse_args(); run, out = Path(a.run), Path(a.out); out.mkdir(parents=True, exist_ok=True)
    t = time.time()
    data, tracks, nodes, links = bake(run, a.t0, a.t1, a.step)
    np.savez_compressed(out / "vehicles.npz", **data, step=a.step, origin=ORIGIN)
    ek = list(links)
    edges = np.array([(*nodes[links[k][0]], *nodes[links[k][1]]) for k in ek], np.float32)
    np.savez_compressed(out / "network.npz", edges=edges, freespeed=np.array([links[k][3] for k in ek], np.float32))
    print(f"bake {time.time()-t:.1f}s -> {out}")
    if not a.no_check: check(run, tracks, links, nodes, data)
