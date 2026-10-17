"""R3/E2: zbieżność runu (natężenia i czasy, nie score) oraz zgodność między seedami.

Użycie: uv run python pipeline/convergence.py <out_prefix> <output_dir> [<output_dir> ...]
  - dla każdego runu: zmiana natężeń top-50 linków między kolejnymi linkstats (co 10 it.), dobowo i w godz. 7-8;
    godziny w aucie (ph_modestats.csv) per iteracja;
  - natężenia przeskalowane do 100% (1/sampleSize z output_config.xml);
  - dla >= 2 runów (różne seedy): GEH natężeń 7-8 i dobowych z ostatniej iteracji, udział linków z GEH < 5.
Wyjście: <out_prefix>.json, <out_prefix>.png.
"""
import csv
import io
import json
import math
import re
import sys
from pathlib import Path

import matplotlib
import zstandard

matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use("dark_background")  # mapy w ciemnym motywie (prośba użytkownika)

TOP_N, PEAK = 50, "HRS7-8avg"
prefix, dirs = sys.argv[1], [Path(d) for d in sys.argv[2:]]


def sample_size(d):  # linkstats są w pojazdach próbki; GEH liczy się na wartościach pełnej populacji
    return float(re.search(r'name="sampleSize" value="([^"]+)"', (d / "output_config.xml").read_text(encoding="utf-8")).group(1))


def linkstats(d):
    out, k = {}, 1 / sample_size(d)
    for f in (d / "ITERS").glob("it.*/*.linkstats.txt.zst"):
        rows = csv.DictReader(io.TextIOWrapper(zstandard.ZstdDecompressor().stream_reader(open(f, "rb")), encoding="utf-8"),
                              delimiter="\t")
        out[int(f.name.split(".")[0])] = {r["LINK"]: (k * float(r["HRS0-24avg"]), k * float(r[PEAK])) for r in rows}
    return dict(sorted(out.items()))


def geh(a, b):
    return math.sqrt(2 * (a - b) ** 2 / (a + b)) if a + b > 0 else 0.0


report, ls_all = {}, {}
fig, axs = plt.subplots(1, 3, figsize=(16, 4.8))
for d in dirs:
    ls = ls_all[d.name] = linkstats(d)
    its = list(ls)
    last = ls[its[-1]]
    top = sorted(last, key=lambda l: -last[l][0])[:TOP_N]
    change = {}
    for prev, cur in zip(its, its[1:]):
        dd = [abs(ls[cur][l][0] - ls[prev][l][0]) / ls[prev][l][0] for l in top if ls[prev][l][0] > 0]
        pk = [abs(ls[cur][l][1] - ls[prev][l][1]) / ls[prev][l][1] for l in top if ls[prev][l][1] > 0]
        change[cur] = (round(100 * sum(dd) / len(dd), 1), round(100 * sum(pk) / len(pk), 1))
    ph = [(int(r["Iteration"]), float(r["car_travel"])) for r in csv.DictReader(open(d / "ph_modestats.csv"), delimiter=";")]
    report[d.name] = {"linkstats_iterations": its,
                      "top50_mean_abs_change_pct_daily_peak7_8": change,
                      "car_hours_iter0_last": [round(ph[0][1]), round(ph[-1][1])],
                      "car_hours_last10_range_pct": round(100 * (max(v for _, v in ph[-10:]) - min(v for _, v in ph[-10:]))
                                                         / ph[-1][1], 2)}
    axs[0].plot(list(change), [v[0] for v in change.values()], "o-", label=f"{d.name} dobowo")
    axs[0].plot(list(change), [v[1] for v in change.values()], "x--", label=f"{d.name} 7-8")
    axs[1].plot(*zip(*ph), label=d.name)

if len(dirs) > 1:
    names = list(ls_all)
    finals = {n: ls_all[n][max(ls_all[n])] for n in names}
    ref = finals[names[0]]
    used = [l for l in ref if ref[l][0] >= 100]  # linki z min. 100 poj./dobę (100%) w pierwszym runie
    pairs = {}
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = finals[names[i]], finals[names[j]]
            g_day = [geh(a[l][0] / 24, b[l][0] / 24) for l in used]  # GEH na średniej godzinowej doby
            g_pk = [geh(a[l][1], b[l][1]) for l in used]
            pairs[f"{names[i]} vs {names[j]}"] = {
                "links": len(used), "geh_lt5_share_peak7_8": round(sum(g < 5 for g in g_pk) / len(g_pk), 3),
                "geh_lt5_share_daily_hourly_mean": round(sum(g < 5 for g in g_day) / len(g_day), 3),
                "geh_max_peak7_8": round(max(g_pk), 1)}
            axs[2].hist(g_pk, bins=40, alpha=0.5, label=f"{names[i]} vs {names[j]}")
    report["seed_comparison"] = pairs

axs[0].set_title(f"zmiana natężeń top-{TOP_N} linków vs poprzednie linkstats [%]", fontsize=9); axs[0].legend(fontsize=6)
axs[1].set_title("godziny w aucie (ph_modestats) wg iteracji", fontsize=9); axs[1].legend(fontsize=6)
axs[2].set_title("GEH natężeń 7-8 między seedami (linki >= 100 poj./d)", fontsize=9); axs[2].axvline(5, color="w", ls=":")
if len(dirs) > 1:
    axs[2].legend(fontsize=6)
fig.tight_layout(); fig.savefig(prefix + ".png", dpi=120)
json.dump(report, open(prefix + ".json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(json.dumps(report, ensure_ascii=False)[:2000])
