"""Opóźnienia na linkach (czas przejazdu − czas swobodny) z eventów MATSim + mapa.

Użycie: uv run python pipeline/link_delay.py <output_dir> <out_prefix>   (np. reports/f5_delay -> .json, .png)
Pierwszy link nogi (vehicle enters traffic) i ostatni (vehicle leaves traffic) nie są liczone.
"""
import collections
import json
import sys
from pathlib import Path

import matplotlib
import zstandard
from lxml import etree

matplotlib.use("Agg")
import matplotlib.pyplot as plt

out_dir, prefix = Path(sys.argv[1]), sys.argv[2]
z = lambda p: zstandard.ZstdDecompressor().stream_reader(open(p, "rb"))

nodes, L = {}, {}
for _, el in etree.iterparse(z(out_dir / "output_network.xml.zst"), tag=("node", "link")):
    if el.tag == "node":
        nodes[el.get("id")] = (float(el.get("x")), float(el.get("y")))
    else:
        L[el.get("id")] = dict(free=float(el.get("length")) / float(el.get("freespeed")), a=el.get("from"), b=el.get("to"),
                               cap=float(el.get("capacity")), type={x.get("name"): x.text for x in el.iter("attribute")}.get("type"))
    el.clear()

enter, delay, n, by_hour = {}, collections.Counter(), collections.Counter(), collections.Counter()
for _, el in etree.iterparse(z(out_dir / "output_events.xml.zst"), tag="event"):
    t, v = el.get("type"), el.get("vehicle")
    if t == "entered link":
        enter[v] = (el.get("link"), float(el.get("time")))
    elif t == "vehicle leaves traffic":
        enter.pop(v, None)
    elif t == "left link" and v in enter:
        lk, t0 = enter.pop(v)
        d = float(el.get("time")) - t0 - L[lk]["free"]
        n[lk] += 1
        if d > 0:
            delay[lk] += d
            by_hour[int(t0 // 3600)] += d
    el.clear()

report = {
    "total_delay_veh_h": round(sum(delay.values()) / 3600, 1),
    "delay_veh_h_by_hour": {h: round(v / 3600, 1) for h, v in sorted(by_hour.items()) if v >= 360},
    "top_links": [dict(link=lk, type=L[lk]["type"], capacity=L[lk]["cap"], vehicles=n[lk], delay_veh_h=round(d / 3600, 1),
                       avg_delay_s=round(d / n[lk]), coord_EN=[round(c) for c in nodes[L[lk]["b"]]])
                  for lk, d in delay.most_common(15)],
}
json.dump(report, open(prefix + ".json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)

fig, ax = plt.subplots(figsize=(10, 9))
for lk, l in L.items():
    (x1, y1), (x2, y2) = nodes[l["a"]], nodes[l["b"]]
    avg = delay[lk] / n[lk] if n[lk] else 0
    ax.plot([x1, x2], [y1, y2], color=plt.cm.inferno_r(min(avg / 300, 1)) if avg > 10 else "0.85",
            lw=0.4 + 3 * min(avg / 300, 1), zorder=2 if avg > 10 else 1)
for i, r in enumerate(report["top_links"][:5]):
    ax.annotate(str(i + 1), r["coord_EN"], fontsize=9, color="#0b3c5d", weight="bold", xytext=(4, 4), textcoords="offset points")
ax.text(0.01, 0.99, "\n".join(f"{i + 1}: {r['type']}, śr. {r['avg_delay_s']} s, {r['vehicles']} poj."
                               for i, r in enumerate(report["top_links"][:5])),
        transform=ax.transAxes, va="top", fontsize=8, family="monospace", bbox=dict(fc="white", ec="0.7"))
hot = [nodes[L[lk]["b"]] for lk, d in delay.items() if d / n[lk] > 30]
if hot:  # przybliżenie na obszar z opóźnieniami (+3 km)
    xs, ys = zip(*hot)
    ax.set_xlim(min(xs) - 3000, max(xs) + 3000); ax.set_ylim(min(ys) - 3000, max(ys) + 3000)
sm = plt.cm.ScalarMappable(cmap="inferno_r", norm=plt.Normalize(0, 300))
fig.colorbar(sm, ax=ax, shrink=0.6, label="średnie opóźnienie na linku [s] (skala ucięta na 300)")
ax.set_aspect("equal"); ax.ticklabel_format(useOffset=False, style="plain"); ax.tick_params(labelsize=7)
ax.set_title(f"opóźnienie względem czasu swobodnego: razem {report['total_delay_veh_h']} poj.-h", fontsize=10)
fig.tight_layout(); fig.savefig(prefix + ".png", dpi=120)
print(json.dumps({k: report[k] for k in ("total_delay_veh_h", "delay_veh_h_by_hour")}, ensure_ascii=False))
