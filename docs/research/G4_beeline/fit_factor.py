"""Dopasowanie: (1) tot = a*euclid + b (OLS), (2) jeden mnożnik f na pełny rozkład odległości par (waga binów pełne/próbka),
(3) wykres f(d). Wejście: output/g4_beeline/od_all.csv, pairs.csv. Wyjście: reports/etap2/g4_beeline/f_vs_dist.png"""
import pandas as pd, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.style.use("dark_background")
od = pd.read_csv("output/g4_beeline/od_all.csv"); full = pd.read_csv("output/g4_beeline/pairs.csv")
bins = [0, 1000, 2000, 3000, 4000, 5000, 7000, 12000]
full["bin"] = pd.cut(full.euclid, bins); od["bin"] = pd.cut(od.euclid, bins)
wfull = full.bin.value_counts(normalize=True)
out = []; fig, ax = plt.subplots(1, 2, figsize=(13, 5))
for m, c in (("walk", "#5ad"), ("bike", "#fb4"), ("car", "#f66")):
    d = od[od["mode"] == m].copy()
    a, b = np.polyfit(d.euclid, d.tot, 1)
    wsamp = d.bin.value_counts(normalize=True); d["w"] = d.bin.map(wfull / wsamp).astype(float)
    f_unb = (d.w * d.tot).sum() / (d.w * d.euclid).sum()                # nieobciążony w sumie dystansu
    f_med = np.average(d.f if "f" in d else d.tot / d.euclid)           # (średnia f, dla porównania)
    fr = d.tot / d.euclid
    cand = np.arange(1.0, 2.2, 0.01)
    mae = [(d.w * (d.tot - f * d.euclid).abs()).sum() / d.w.sum() for f in cand]
    f_mae = cand[int(np.argmin(mae))]
    out.append((m, len(d), round(a, 3), round(b, 0), round(f_unb, 3), round(f_mae, 2), round(np.average(fr, weights=d.w), 3),
                round(float((d.w * (d.tot - 1.3 * d.euclid).abs()).sum() / d.w.sum()), 0), round(float((d.w * (d.tot - f_unb * d.euclid).abs()).sum() / d.w.sum()), 0)))
    g = d.groupby("bin", observed=True).apply(lambda x: pd.Series({"e": x.euclid.mean(), "f": x.tot.sum() / x.euclid.sum()}))
    ax[0].plot(g.e / 1000, g.f, "o-", color=c, label=f"{m}: Σsieć/Σlinia")
    ax[0].plot(g.e / 1000, a + b / g.e, "--", color=c, alpha=.5)
    ax[1].hist(fr.clip(upper=3), bins=60, color=c, alpha=.5, label=m)
ax[0].axhline(1.3, color="w", ls=":", label="domyślne 1,3"); ax[0].axhline(1.6, color="g", ls=":", label="hipoteza 1,6")
ax[0].set_xlabel("odległość w linii prostej [km]"); ax[0].set_ylabel("f = trasa/linia"); ax[0].legend(); ax[0].set_title("Kutno: współczynnik objazdu (pary dom–praca z planów)")
ax[1].set_xlabel("f (ucięte przy 3)"); ax[1].legend(); ax[1].set_title("rozkład f na parę")
plt.tight_layout(); import os; os.makedirs("reports/etap2/g4_beeline", exist_ok=True); plt.savefig("reports/etap2/g4_beeline/f_vs_dist.png", dpi=130)
t = pd.DataFrame(out, columns=["tryb", "n", "a (OLS)", "b [m]", "f nieobciążony (Σ)", "f min MAE", "śr. f ważona", "MAE@1,3 [m]", "MAE@f_nieob [m]"])
print(t.to_string(index=False)); t.to_csv("output/g4_beeline/fit.csv", index=False)
