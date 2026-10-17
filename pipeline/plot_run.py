"""Podgląd runu MATSim: mapa aktywności i obciążenia linków + odjazdy w czasie + czasy podróży.

Użycie: uv run python pipeline/plot_run.py <output_dir> <out.png> [tytuł]
Czyta output_network.xml.zst, output_trips.csv.zst, output_activities.csv.zst, output_events.xml.zst.
"""
import collections
import csv
import io
import sys
from pathlib import Path

import matplotlib
import zstandard
from lxml import etree

matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use("dark_background")  # mapy w ciemnym motywie (prośba użytkownika)


def zopen(p):
    return zstandard.ZstdDecompressor().stream_reader(open(p, "rb"))


def read_csv(p):
    return list(csv.DictReader(io.TextIOWrapper(zopen(p), encoding="utf-8"), delimiter=";"))


def hms(s):
    h, m, sec = (int(x) for x in s.split(":"))
    return h * 3600 + m * 60 + sec


out_dir, png = Path(sys.argv[1]), sys.argv[2]
title = sys.argv[3] if len(sys.argv) > 3 else out_dir.name

nodes, links = {}, {}
for _, el in etree.iterparse(zopen(out_dir / "output_network.xml.zst"), tag=("node", "link")):
    if el.tag == "node":
        nodes[el.get("id")] = (float(el.get("x")), float(el.get("y")))
    else:
        links[el.get("id")] = (el.get("from"), el.get("to"))
    el.clear()

volume = collections.Counter()
for _, el in etree.iterparse(zopen(out_dir / "output_events.xml.zst"), tag="event"):
    if el.get("type") == "entered link":
        volume[el.get("link")] += 1
    el.clear()

trips = read_csv(out_dir / "output_trips.csv.zst")
acts = read_csv(out_dir / "output_activities.csv.zst")

fig = plt.figure(figsize=(13, 6.5))
ax = fig.add_axes([0.04, 0.08, 0.5, 0.82])
vmax = max(volume.values(), default=1)
for lid, (a, b) in links.items():
    v = volume.get(lid, 0)
    (x1, y1), (x2, y2) = nodes[a], nodes[b]
    ax.plot([x1, x2], [y1, y2], color="#d1495b" if v else "0.3", lw=0.3 + 5 * v / vmax, zorder=3 if v else 1)
# kropki pod linkami z ruchem, żeby ich nie zasłaniały
for typ, col, lab in (("home", "#2e86ab", "dom = start 1. i koniec 2. podróży"), ("work", "#f18f01", "praca")):
    pts = {(float(r["coord_x"]), float(r["coord_y"])) for r in acts if r["activity_type"] == typ}
    if pts:
        xs, ys = zip(*pts)
        ax.scatter(xs, ys, s=3, color=col, alpha=0.5, lw=0, label=f"{lab} ({len(pts)} pkt)", zorder=2)
ax.set_aspect("equal"); ax.legend(loc="best", fontsize=8, markerscale=4)
ax.set_title(f"aktywności i przejazdy po linkach (grubość = liczba wjazdów, max {vmax})", fontsize=9)
ax.ticklabel_format(useOffset=False, style="plain"); ax.tick_params(labelsize=7)

dep_h = [hms(t["dep_time"]) / 3600 for t in trips]
tt_min = [hms(t["trav_time"]) / 60 for t in trips]
ax2 = fig.add_axes([0.62, 0.56, 0.35, 0.34])
ax2.hist(dep_h, bins=[h / 4 for h in range(0, 30 * 4 + 1)], color="#2e86ab")
ax2.set_title(f"odjazdy w ciągu doby ({len(trips)} podróży)", fontsize=9); ax2.set_xlabel("godzina", fontsize=8)
lo, hi = min(dep_h), max(dep_h)
ax2.set_xlim(max(0, lo - 1), hi + 1)
ax3 = fig.add_axes([0.62, 0.08, 0.35, 0.34])
ax3.hist(tt_min, bins=30, color="#f18f01")
ax3.set_title(f"czas podróży [min], mediana {sorted(tt_min)[len(tt_min) // 2]:.1f}", fontsize=9)
fig.suptitle(title, fontsize=11)
fig.savefig(png, dpi=120)
print(png)
