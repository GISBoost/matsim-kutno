"""G1: mapa zakazów skrętu (węzły via z network_r8_zakazy.csv) i różnic opóźnień R8 − R7b (g1_delay_diff_links.csv), ciemny motyw.
Użycie: uv run python -W ignore reports/etap3/g1_skrzyzowania/g1_mapa.py"""
import gzip
import xml.etree.ElementTree as ET

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use("dark_background")
H = "reports/etap3/g1_skrzyzowania/"
t = ET.parse(gzip.open("scenarios/kutno/network.xml.gz"))
nodes = {n.get("id"): (float(n.get("x")), float(n.get("y"))) for n in t.iter("node")}
links = {l.get("id"): (l.get("from"), l.get("to")) for l in t.iter("link")}
z = pd.read_csv("scenarios/kutno/network_r8_zakazy.csv", sep=";", dtype=str)
d = pd.read_csv(H + "g1_delay_diff_links.csv", index_col=0).diff_veh_h
fig, (a, b) = plt.subplots(1, 2, figsize=(17, 8.5))
for ax in (a, b):
    for lk, (f, to) in links.items():
        (x1, y1), (x2, y2) = nodes[f], nodes[to]
        ax.plot([x1, x2], [y1, y2], color="0.28", lw=0.4, zorder=1)
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
vx = z.drop_duplicates(["relation", "via_node"])
kinds = {"no_u_turn": "#ff6b6b", "no_left_turn": "#ffd166", "no_right_turn": "#7fd3ff", "no_straight_on": "#c792ea"}
for k, g in vx.groupby("kind"):
    xs = [nodes[v][0] for v in g.via_node]; ys = [nodes[v][1] for v in g.via_node]
    a.scatter(xs, ys, s=22, color=kinds.get(k, "#8fd18f"), zorder=3, label=f"{k} ({len(g)})")
a.legend(loc="lower right", fontsize=8)
a.set_title(f"Zakazy skrętu z OSM: {len(vx)} relacji, {len(z)} par linków")
big = d[d.abs() > 0.05]
for lk, v in big.items():
    (x1, y1), (x2, y2) = nodes[links[lk][0]], nodes[links[lk][1]]
    b.plot([x1, x2], [y1, y2], color="#ff6b6b" if v > 0 else "#4ecdc4", lw=1 + min(abs(v) * 2, 5), zorder=3)
b.set_title(f"Zmiana opóźnienia R8 − R7b (mediana 5 runów), |Δ| > 0,05 poj.-h próbki: {len(big)} linków\nczerwony = więcej opóźnienia, turkus = mniej")
fig.tight_layout(); fig.savefig(H + "g1_mapa.png", dpi=130)
print("ok", len(big))
