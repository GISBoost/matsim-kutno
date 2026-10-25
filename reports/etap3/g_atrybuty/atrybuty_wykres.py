"""D30: wykres atrybutów: udział prawa jazdy wg grup (CEPiK surowy, po przesunięciu), populacja Kutna: licencja, always i pracujący wg wieku.
Użycie: uv run python -W ignore reports/etap3/g_atrybuty/atrybuty_wykres.py (po pipeline/attributes.py)"""
import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use("dark_background")
r = pd.read_csv("scenarios/kutno/demand/licence_rates.csv"); p = pd.read_csv("scenarios/kutno/demand/population_kutno.csv")
fig, ax = plt.subplots(1, 2, figsize=(13, 4.8))
for s, c in (("M", "#4fc3f7"), ("K", "#f48fb1")):
    q = r[r.sex == s]
    ax[0].plot(q.group, q.rate_raw, "--", color=c, label=f"{s} CEPiK / NSP 2021 (surowy)")
    ax[0].plot(q.group, q.rate, "-o", color=c, label=f"{s} baza D30 (M 65+ = 55-64, przesunięcie do 60,6%)")
ax[0].axhline(1, color="gray", lw=.5); ax[0].set_title("udział praw jazdy wg płci i grupy wieku (Polska, CEPiK 2019)"); ax[0].legend(fontsize=7)
b = pd.cut(p.age, list(range(-1, 95, 10)))
g = p.groupby(b, observed=True).agg(lic=("license", "mean"), alw=("carAvail", lambda s: (s == "always").mean()), emp=("employed", "mean"))
g.plot(ax=ax[1], marker="o"); ax[1].set_xticks(range(len(g))); ax[1].set_xticklabels([f"{int(i.left) + 1}-{int(i.right)}" for i in g.index], rotation=45, fontsize=8)
ax[1].set_title("Kutno, 42 255 os.: prawo jazdy, always, pracujący wg wieku"); fig.tight_layout(); fig.savefig("reports/etap3/g_atrybuty/atrybuty.png", dpi=130)
