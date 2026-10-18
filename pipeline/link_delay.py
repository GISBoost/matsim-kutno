"""Opóźnienia na linkach (czas przejazdu − czas swobodny) z eventów MATSim + mapa.

Użycie: uv run python pipeline/link_delay.py <output_dir> <out_prefix>   (np. reports/f5_delay -> .json, .png)
Pierwszy link nogi (vehicle enters traffic) i ostatni (vehicle leaves traffic) nie są liczone.
D20: pojazdy ciężkie (id "h…") mają czas swobodny z prędkością min(freespeed, 80 km/h), inaczej limit prędkości liczyłby się jako opóźnienie.
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
plt.style.use("dark_background")  # mapy w ciemnym motywie (prośba użytkownika)

out_dir, prefix = Path(sys.argv[1]), sys.argv[2]
VMAX_HEAVY = 80 / 3.6  # D20, Prawo o ruchu drogowym art. 20 ust. 3 pkt 2
z = lambda p: zstandard.ZstdDecompressor().stream_reader(open(p, "rb"))

nodes, L = {}, {}
for _, el in etree.iterparse(z(out_dir / "output_network.xml.zst"), tag=("node", "link")):
    if el.tag == "node":
        nodes[el.get("id")] = (float(el.get("x")), float(el.get("y")))
    else:
        L[el.get("id")] = dict(free=float(el.get("length")) / float(el.get("freespeed")),
                               free_h=float(el.get("length")) / min(float(el.get("freespeed")), VMAX_HEAVY), a=el.get("from"), b=el.get("to"),
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
        d = float(el.get("time")) - t0 - L[lk]["free_h" if v.startswith("h") else "free"]
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
    if not n[lk]:  # nikt nie przejechał
        style = dict(color="0.3", lw=0.4, zorder=1)
    elif avg <= 10:  # ruch bez opóźnienia (≤ 10 s)
        style = dict(color="#2f5f7a", lw=0.8, zorder=2)
    else:
        style = dict(color=plt.cm.autumn_r(min(avg / 300, 1)), lw=0.8 + 3 * min(avg / 300, 1), zorder=3)
    ax.plot([x1, x2], [y1, y2], **style)
ax.plot([], [], color="0.3", label=f"bez ruchu ({sum(1 for lk in L if not n[lk])} linków)")
ax.plot([], [], color="#2f5f7a", label=f"ruch, opóźnienie ≤ 10 s ({sum(1 for lk in L if n[lk] and delay[lk] / n[lk] <= 10)})")
ax.plot([], [], color="#c0392b", lw=2, label=f"opóźnienie > 10 s ({sum(1 for lk in L if n[lk] and delay[lk] / n[lk] > 10)})")
ax.legend(loc="lower right", fontsize=8)
for i, r in enumerate(report["top_links"][:5]):
    ax.annotate(str(i + 1), r["coord_EN"], fontsize=9, color="#7fd3ff", weight="bold", xytext=(4, 4), textcoords="offset points")
ax.text(0.01, 0.99, "\n".join(f"{i + 1}: {r['type']}, śr. {r['avg_delay_s']} s, {r['vehicles']} poj."
                               for i, r in enumerate(report["top_links"][:5])),
        transform=ax.transAxes, va="top", fontsize=8, family="monospace", bbox=dict(fc="0.12", ec="0.5"))
hot = [nodes[L[lk]["b"]] for lk, d in delay.items() if d / n[lk] > 30]
if hot:  # przybliżenie na obszar z opóźnieniami (+3 km)
    xs, ys = zip(*hot)
    ax.set_xlim(min(xs) - 3000, max(xs) + 3000); ax.set_ylim(min(ys) - 3000, max(ys) + 3000)
sm = plt.cm.ScalarMappable(cmap="autumn_r", norm=plt.Normalize(0, 300))
fig.colorbar(sm, ax=ax, shrink=0.6, label="średnie opóźnienie na linku [s] (skala ucięta na 300)")
ax.set_aspect("equal"); ax.ticklabel_format(useOffset=False, style="plain"); ax.tick_params(labelsize=7)
ax.set_title(f"opóźnienie względem czasu swobodnego: razem {report['total_delay_veh_h']} poj.-h", fontsize=10)
fig.tight_layout(); fig.savefig(prefix + ".png", dpi=120)
print(json.dumps({k: report[k] for k in ("total_delay_veh_h", "delay_veh_h_by_hour")}, ensure_ascii=False))
