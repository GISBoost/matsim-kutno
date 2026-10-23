"""G1 (D26): R8 (R7b + zakazy skrętu) vs R7b, te same plany. Użycie: uv run python -W ignore reports/etap3/g1_skrzyzowania/g1_porownanie.py
Wejście: output/g5r7b_*, output/g1r8_* (5 runów każdy), GPR csv z g5_baseline (R7b w reports/etap2/g5_predkosci_d23/r7b/, R8 w tym folderze).
Rozrzut referencyjny = rozrzut seedów planów R7b (3 plany, ten sam seed MATSim): (max - min) / średnia na odcinek (audyt I3).
Opóźnienie na linku jak w link_delay.py (floor(length/v)+1 s, ciężkie min(v, 80 km/h)), liczone raz na run i cache'owane w delay_links_<run>.csv."""
import io
import json
import math
import sys
from collections import Counter
from pathlib import Path

import matplotlib
import pandas as pd
import zstandard
from lxml import etree

matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use("dark_background")

H = Path("reports/etap3/g1_skrzyzowania")
R7D = Path("reports/etap2/g5_predkosci_d23/r7b")
B = ["_25pct_s4711", "_25pct_s1", "_25pct_s2", "p1_25pct_s4711", "p2_25pct_s4711"]
R7, R8 = [f"g5r7b{b}" for b in B], [f"g1r8{b}" for b in B]
PL = [0, 3, 4]  # indeksy runów z różnymi planami (seed MATSim 4711)
CONTROL, LOCAL = [91124, 91866], [10045, 91892, 91119]
z = lambda p: zstandard.ZstdDecompressor().stream_reader(open(p, "rb"))
res = {}

# --- 1. GPR ---
for cls in ("lcv", "heavy"):
    def sec(d, r):
        return pd.read_csv(d / f"gpr_{r}_{cls}.csv").groupby("nr").agg(gpr=("gpr_light_dir", "sum"), model=("model_dir", "sum"))
    s7 = [sec(R7D, r) for r in R7]; s8 = [sec(H, r) for r in R8]
    gpr = s7[0].gpr
    m7 = pd.concat([s.model for s in s7], axis=1); m8 = pd.concat([s.model for s in s8], axis=1)
    mp = m7.iloc[:, PL]
    spread = (mp.max(axis=1) - mp.min(axis=1)) / mp.mean(axis=1)
    med7, med8 = m7.median(axis=1), m8.median(axis=1)
    ch = med8 / med7 - 1
    fit = ~gpr.index.isin(CONTROL + LOCAL)
    t = pd.DataFrame({"gpr": gpr.round(0), "R7b_proc": (med7 / gpr * 100).round(0), "R8_proc": (med8 / gpr * 100).round(0),
                      "zmiana_proc": (ch * 100).round(2), "rozrzut_planow_proc": (spread * 100).round(1), "fit15": fit})
    t["ponad_rozrzut"] = t.zmiana_proc.abs() > t.rozrzut_planow_proc
    t.to_csv(H / f"g1_gpr_{cls}.csv")
    res[cls] = {"w_15proc_R7b": int(((med7 / gpr - 1).abs()[fit] <= .15).sum()), "w_15proc_R8": int(((med8 / gpr - 1).abs()[fit] <= .15).sum()),
                "n_fit": int(fit.sum()), "mediana_abs_zmiany_proc": round(float(ch.abs()[fit].median() * 100), 2),
                "maks_abs_zmiany_proc": round(float(ch.abs()[fit].max() * 100), 2), "odcinki_ponad_rozrzut": int(t.ponad_rozrzut.sum()),
                "mediana_rozrzutu_planow_proc": round(float(spread.median() * 100), 1)}

# --- 2. opóźnienia na linkach ---
def delays(run):
    f = H / f"delay_links_{run}.csv"
    if f.exists():
        return pd.read_csv(f, index_col=0)
    d = Path("output") / run
    free, freeh = {}, {}
    for _, el in etree.iterparse(z(d / "output_network.xml.zst"), tag="link"):
        fs, ln = float(el.get("freespeed")), float(el.get("length"))
        free[el.get("id")] = math.floor(ln / fs) + 1
        freeh[el.get("id")] = math.floor(ln / min(fs, 80 / 3.6)) + 1
        el.clear()
    enter, dl, n = {}, Counter(), Counter()
    for _, el in etree.iterparse(z(d / "output_events.xml.zst"), tag="event"):
        t, v = el.get("type"), el.get("vehicle")
        if t == "entered link":
            enter[v] = (el.get("link"), float(el.get("time")))
        elif t == "vehicle leaves traffic":
            enter.pop(v, None)
        elif t == "left link" and v in enter:
            lk, t0 = enter.pop(v)
            n[lk] += 1
            x = float(el.get("time")) - t0 - (freeh if v.startswith("h") else free)[lk]
            if x > 0:
                dl[lk] += x
        el.clear()
    df = pd.DataFrame({"n": pd.Series(n), "delay_s": pd.Series(dl)}).fillna(0)
    df.to_csv(f)
    return df

D7 = [delays(r) for r in R7]; D8 = [delays(r) for r in R8]
allx = sorted(set().union(*[d.index for d in D7 + D8]))
S7 = pd.concat([d.delay_s.reindex(allx).fillna(0) / 3600 for d in D7], axis=1)  # veh-h próbki
S8 = pd.concat([d.delay_s.reindex(allx).fillna(0) / 3600 for d in D8], axis=1)
tot7, tot8 = S7.sum(), S8.sum()
res["opoznienia_veh_h_proby"] = {"R7b": [round(x, 1) for x in tot7], "R8": [round(x, 1) for x in tot8],
                                 "mediana_R7b": round(float(tot7.median()), 1), "mediana_R8": round(float(tot8.median()), 1),
                                 "rozrzut_planow_R7b": round(float(tot7.iloc[PL].max() - tot7.iloc[PL].min()), 1)}
dl = S8.median(axis=1) - S7.median(axis=1)
noise = (S7.iloc[:, PL].max(axis=1) - S7.iloc[:, PL].min(axis=1))
res["linki_opoznienie"] = {"linkow": len(allx), "zmiana_abs_veh_h_suma": round(float(dl.abs().sum()), 1),
                           "linki_zmiana_ponad_rozrzut_planow": int(((dl.abs() > noise) & (dl.abs() > 0.05)).sum()),
                           "top_wzrost": {k: round(float(v), 2) for k, v in dl.nlargest(5).items()},
                           "top_spadek": {k: round(float(v), 2) for k, v in dl.nsmallest(5).items()}}
json.dump(res, open(H / "g1_porownanie.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps(res, indent=1, ensure_ascii=False))
dl.rename("diff_veh_h").to_csv(H / "g1_delay_diff_links.csv")
