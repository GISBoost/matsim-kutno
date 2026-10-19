"""Statystyki współczynnika objazdu f = d_sieć / d_euklides z wyników QGIS (output/g4_beeline/od_s110_*.csv)."""
import pandas as pd, numpy as np, sys
B = "output/g4_beeline/"
bins = [0, 1000, 2000, 3000, 4000, 5000, 7000, 12000]
res = []
for m in ["walk", "bike", "car"]:
    try: d = pd.read_csv(B + f"od_s110_{m}.csv")
    except FileNotFoundError: continue
    d["tot"] = d.glen + d.snap_s + d.snap_e          # trasa po sieci + proste dojścia do sieci
    d["f"] = d.tot / d.euclid
    d["f_net"] = d.glen / d.euclid                   # bez dojść do sieci
    d["bin"] = pd.cut(d.euclid, bins)
    d["mode"] = m
    res.append(d)
    q = d.f.quantile([.05, .25, .5, .75, .95]).round(3).to_dict()
    print(f"\n== {m}: n={len(d)}  średnia f={d.f.mean():.3f}  mediana={d.f.median():.3f}  Σtot/Σeuclid={d.tot.sum()/d.euclid.sum():.3f}  "
          f"f bez dojść={d.f_net.mean():.3f}  snap_s śr={d.snap_s.mean():.0f} m  snap_e śr={d.snap_e.mean():.0f} m")
    print("kwantyle f:", q, " max:", round(d.f.max(), 2))
    t = d.groupby("bin", observed=True).agg(n=("f", "size"), euclid=("euclid", "mean"), f_mean=("f", "mean"), f_med=("f", "median"),
                                            f_ratio=("tot", lambda s: s.sum() / d.loc[s.index, "euclid"].sum()))
    print(t.round(3).to_string())
al = pd.concat(res)
al.to_csv(B + "od_all.csv", index=False)
# wspólne pary (te same id w trzech trybach)
p = al.pivot_table(index="id", columns="mode", values="f")
print("\nkorelacja f między trybami (wspólne pary):\n", p.corr().round(3))
