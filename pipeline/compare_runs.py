"""Porównanie dwóch runów MATSim (np. F5 10% vs F6 100%): czasy podróży, prędkość car wg godziny, score.

Użycie: uv run python pipeline/compare_runs.py <out_png> <label1>=<output_dir1> <label2>=<output_dir2>
Wyjście: <out_png> + <out_png bez .png>.json.
"""
import csv
import io
import json
import statistics as st
import sys
from pathlib import Path

import matplotlib
import zstandard

matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use("dark_background")  # mapy w ciemnym motywie (prośba użytkownika)

png, runs = sys.argv[1], dict(a.split("=", 1) for a in sys.argv[2:])
hms = lambda s: sum(int(x) * m for x, m in zip(s.split(":"), (3600, 60, 1)))
rd = lambda p: list(csv.DictReader(io.TextIOWrapper(zstandard.ZstdDecompressor().stream_reader(open(p, "rb")),
                                                    encoding="utf-8"), delimiter=";"))
q = lambda xs, p: sorted(xs)[int(p * (len(xs) - 1))]

stats, data = {}, {}
for label, d in runs.items():
    d = Path(d)
    trips = rd(d / "output_trips.csv.zst")
    car = [l for l in rd(d / "output_legs.csv.zst") if l["mode"] == "car"]
    tt = {k: [hms(t["trav_time"]) / 60 for t in trips if t["person"][0] == k] for k in ("r", "c", "o")}
    tt = {k: v for k, v in tt.items() if v}  # o = wyjeżdżający (D17), tylko gdy są w planach
    speed_h = {}
    for l in car:
        if hms(l["trav_time"]) > 0:
            speed_h.setdefault(hms(l["dep_time"]) // 3600, []).append(float(l["distance"]) / hms(l["trav_time"]) * 3.6)
    score = [float(r["avg_executed"]) for r in csv.DictReader(open(d / "scorestats.csv"), delimiter=";")]
    data[label] = dict(tt=tt, speed_h=speed_h, score=score)
    stats[label] = {
        "trips": len(trips),
        "trav_time_min_median": {k: round(st.median(v), 1) for k, v in tt.items()},
        "trav_time_min_p90": {k: round(q(v, 0.9), 1) for k, v in tt.items()},
        "car_speed_kmh_median_by_dep_hour": {h: round(st.median(v), 1) for h, v in sorted(speed_h.items()) if len(v) >= 20},
        "score_avg_executed_first_last": [round(score[0], 1), round(score[-1], 1)],
    }
json.dump(stats, open(png.removesuffix(".png") + ".json", "w", encoding="utf-8", newline="\n"), indent=2, ensure_ascii=False)

fig, axs = plt.subplots(1, 3, figsize=(16, 5))
cols = ["#2e86ab", "#d1495b", "#f6c85f", "#6fcf97"]
for (label, dd), c in zip(data.items(), cols):
    for k, ls in (("r", "-"), ("c", "--"), ("o", ":")):
        if k not in dd["tt"]:
            continue
        xs = sorted(dd["tt"][k])
        axs[0].plot(xs, [i / len(xs) for i in range(len(xs))], color=c, ls=ls,
                    label=f"{label}: {dict(r='mieszkańcy', c='przyjeżdżający', o='wyjeżdżający')[k]}")
    hs = [h for h, v in sorted(dd["speed_h"].items()) if len(v) >= 20]
    axs[1].plot(hs, [st.median(dd["speed_h"][h]) for h in hs], "o-", color=c, label=label)
    axs[2].plot(dd["score"], color=c, label=label)
axs[0].set_title("czas podróży [min] (dystrybuanta)", fontsize=10); axs[0].set_xlim(0, 90); axs[0].legend(fontsize=8)
axs[1].set_title("mediana prędkości nogi car wg godziny wyjazdu [km/h]", fontsize=10); axs[1].legend(fontsize=8)
axs[2].set_title("score: avg executed wg iteracji", fontsize=10); axs[2].legend(fontsize=8)
fig.suptitle(" vs ".join(runs), fontsize=12)
fig.tight_layout(); fig.savefig(png, dpi=120)
print(json.dumps(stats, ensure_ascii=False))
