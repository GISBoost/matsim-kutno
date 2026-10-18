"""Krok 8 (I3): rozrzut referencji R6 per licznik, osobno dla seedów MATSim (4711/1/2, plany seed 4711) i seedów planów (4711/1/2, MATSim 4711).

Użycie: uv run python reports/etap2/audyt_g5/poprawki/skrypty/c8_ref.py
Wejście: tabele g5_baseline.py per run (k8_ref/gpr_<run>_<cls>.csv) i opóźnienia link_delay.py (k8_ref/delay_<run>.json).
Rozrzut = (max − min) / średnia, w skali odcinka (oba kierunki). Wynik: k8_ref/c8_ref.json, k8_ref/c8_spread.png (ciemny motyw).
"""
import json

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use("dark_background")

D = "reports/etap2/audyt_g5/poprawki/k8_ref/"
MATSIM = ["g5r6_25pct_s4711", "g5r6_25pct_s1", "g5r6_25pct_s2"]
PLANS = ["g5r6_25pct_s4711", "g5r6p1_25pct_s4711", "g5r6p2_25pct_s4711"]
CONTROL, LOCAL = [91124, 91866], [10045, 91892, 91119]
res, sec_all = {}, {}
for cls in ("lcv", "heavy"):
    sec = {}
    for r in sorted(set(MATSIM + PLANS)):
        t = pd.read_csv(f"{D}gpr_{r}_{cls}.csv")
        sec[r] = t.groupby("nr").agg(gpr=("gpr_light_dir", "sum"), model=("model_dir", "sum"))
    gpr = sec[MATSIM[0]].gpr
    out = {}
    for name, runs in (("seedy_MATSim", MATSIM), ("seedy_planow", PLANS)):
        m = pd.concat([sec[r].model for r in runs], axis=1)
        spread = (m.max(axis=1) - m.min(axis=1)) / m.mean(axis=1)
        ratio = m.mean(axis=1) / gpr
        fit = ~ratio.index.isin(CONTROL + LOCAL)
        out[name] = {"spread_median": round(float(spread[fit].median()), 4), "spread_max": round(float(spread[fit].max()), 4),
                     "spread_max_nr": int(spread[fit].idxmax()),
                     "spread_control": {int(n): round(float(spread[n]), 4) for n in CONTROL},
                     "ratio_mean": ratio.round(3).to_dict(), "fit15_in15": int(((ratio[fit] - 1).abs() <= 0.15).sum()),
                     "fit15_median_abs_dev": round(float((ratio[fit] - 1).abs().median()), 3),
                     "A1": round(float(m.mean(axis=1)[[71410, 91820, 91821]].sum() / gpr[[71410, 91820, 91821]].sum()), 3),
                     "DK_Kutno": round(float(m.mean(axis=1)[[91124, 91866, 91869]].sum() / gpr[[91124, 91866, 91869]].sum()), 3),
                     "per_run_ratio": {r: (sec[r].model / gpr).round(3).to_dict() for r in runs}}
        sec_all[(cls, name)] = spread
    res[cls] = out
dl = {r: json.load(open(f"{D}delay_{r}.json", encoding="utf-8"))["total_delay_veh_h"] for r in sorted(set(MATSIM + PLANS))}
res["delay_veh_h_sample"] = dl
json.dump(res, open(D + "c8_ref.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
fig, axs = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
for ax, cls in zip(axs, ("lcv", "heavy")):
    a, b = sec_all[(cls, "seedy_MATSim")], sec_all[(cls, "seedy_planow")]
    x = range(len(a))
    ax.bar([i - 0.2 for i in x], a * 100, 0.4, color="#2e86ab", label="seedy MATSim")
    ax.bar([i + 0.2 for i in x], b * 100, 0.4, color="#f18f01", label="seedy planów")
    ax.set_xticks(list(x)); ax.set_xticklabels([str(n) for n in a.index], rotation=90, fontsize=7)
    ax.set_title(f"R6, {cls}: rozrzut per odcinek (max − min) / średnia", fontsize=10); ax.legend(fontsize=8)
axs[0].set_ylabel("%")
fig.tight_layout(); fig.savefig(D + "c8_spread.png", dpi=120)
for cls in ("lcv", "heavy"):
    for k, v in res[cls].items():
        print(cls, k, {x: y for x, y in v.items() if x not in ("ratio_mean", "per_run_ratio")})
print("opóźnienia", dl)
