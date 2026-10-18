"""Audyt G5: niezależne przeliczenie model / GPR z liczników eventów (a1_events.py) i z surowych tabel GPR.

Użycie: uv run python reports/etap2/audyt_g5/skrypty/a4_gpr.py
Cel na kierunek: SDRDR (DW: SDRR) × udział klasy × 0,5 (A1: udział kierunku z gpr_linki.csv) — jak w raportach (wariant „raport”),
oraz wariant „sdrdr_struct”: udział klasy ze struktury rodzajowej SDRDR (dk_sdrdr.xlsx), a nie SDRR.
Model = Σ entered (pierwsza litera id) / 0,25, średnia z seedów.
"""
import json

import numpy as np
import pandas as pd

g = pd.read_csv("scenarios/kutno/validation/gpr_linki.csv", dtype={"link": str})
STRUCT = ["motocykle", "osobowe", "mikrobusy", "lekkie_ciez", "ciez_bez_przycz", "ciez_z_przycz", "autobusy", "ciagniki"]
d = pd.read_excel("data/raw/g5/gpr2025/dk_sdrdr.xlsx", header=None, skiprows=10)
dr = pd.DataFrame({"nr": pd.to_numeric(d[0], errors="coerce"), "sdrdr_x": pd.to_numeric(d[8], errors="coerce")})
for i, c in enumerate(STRUCT):
    dr[c + "_dr"] = pd.to_numeric(d[9 + i], errors="coerce")
dr = dr.dropna(subset=["nr"]).drop_duplicates("nr")
g = g.merge(dr, on="nr", how="left")
assert (g.sdrdr.isna() | (g.sdrdr == g.sdrdr_x)).all(), "SDRDR w gpr_linki != dk_sdrdr.xlsx"
CLS = {"light": ["motocykle", "osobowe", "mikrobusy"], "lcv": ["motocykle", "osobowe", "mikrobusy", "lekkie_ciez"],
       "heavy": ["ciez_bez_przycz", "ciez_z_przycz", "autobusy", "ciagniki"]}
KIND = {"light": "rcot", "lcv": "rcot", "heavy": "h"}
CITY, LOCAL = [91124, 91866], [10045, 91892, 91119]


def model(runs, kinds):
    vals = []
    for r in runs:
        e = json.load(open(f"reports/etap2/audyt_g5/wyniki/ev_{r}.json"))["counter_entered_by_class"]
        vals.append(g.link.map(lambda l: sum(e.get(f"{l}|{k}", 0) for k in kinds) / 0.25))
    return pd.concat(vals, axis=1)


def table(runs, cls, struct="sdr"):
    base = g.sdrdr.where(g.sdrdr.notna(), g.sdr)
    if struct == "sdr":
        share = g[CLS[cls]].sum(axis=1) / g.sdr
    else:  # SDRDR ma własną strukturę dla DK; DW (brak SDRDR) zostają przy SDRR
        sh_dr = g[[c + "_dr" for c in CLS[cls]]].sum(axis=1) / g.sdrdr
        share = sh_dr.where(g.sdrdr.notna(), g[CLS[cls]].sum(axis=1) / g.sdr)
    gpr = base * share * g.udzial_kier
    m = model(runs, KIND[cls])
    t = pd.DataFrame({"nr": g.nr, "droga": g.droga, "gpr": gpr, "model": m.mean(axis=1), "mmin": m.min(axis=1), "mmax": m.max(axis=1)})
    s = t.groupby(["nr", "droga"], sort=False).sum().reset_index()
    s["ratio"] = s.model / s.gpr
    s["spread"] = (s.mmax - s.mmin) / s.model
    fit = ~s.nr.isin(CITY)
    fit14 = fit & ~s.nr.isin(LOCAL)
    grp = lambda m: round(float(s[m].model.sum() / s[m].gpr.sum()), 3)
    return s, {"A1": grp(s.droga == "A1"), "DK_Kutno": grp(s.nr.isin([91124, 91866, 91869])),
               "fit14_sum": grp(fit14), "fit14_in15": int(((s.ratio - 1).abs() <= 0.15)[fit14].sum()),
               "fit14_median_abs_dev": round(float((s.ratio - 1).abs()[fit14].median()), 3),
               "Objazdowa": round(float(s[s.nr == 91124].ratio.iloc[0]), 3), "Bitwy": round(float(s[s.nr == 91866].ratio.iloc[0]), 3),
               "Obj+Bitwy": grp(s.nr.isin(CITY)),
               "local": {int(n): round(float(s[s.nr == n].ratio.iloc[0]), 3) for n in LOCAL},
               "seed_spread_median": round(float(s.spread.median()), 4), "seed_spread_max": round(float(s.spread.max()), 4),
               "out15": {int(r.nr): round(float(r.ratio), 3) for r in s[fit14 & ((s.ratio - 1).abs() > 0.15)].itertuples()}}


out = {}
R3 = ["g5r3_25pct_s4711", "g5r3_25pct_s1", "g5r3_25pct_s2"]
for name, runs, cls in (("R3_3seeds_light", R3, "light"), ("R3_s4711_light", R3[:1], "light"),
                        ("R4_lcv", ["g5r4_25pct_s4711"], "lcv"), ("R4_heavy", ["g5r4_25pct_s4711"], "heavy"),
                        ("R5_lcv", ["g5r5_25pct_s4711"], "lcv"), ("R5_heavy", ["g5r5_25pct_s4711"], "heavy")):
    for struct in ("sdr", "sdrdr"):
        s, rep = table(runs, cls, struct)
        out[f"{name}|{struct}"] = rep
        if struct == "sdr":
            s.round(3).to_csv(f"reports/etap2/audyt_g5/wyniki/gpr_{name}.csv", index=False)
# różnice per seed R3 (max-min)/średnia: per kierunek-link i per odcinek
s, _ = table(R3, "light")
print(s[["nr", "droga", "gpr", "model", "ratio", "spread"]].round(3).to_string())
# udział klasy SDR vs SDRDR per odcinek DK
sh = g.drop_duplicates("nr")[["nr", "droga", "sdr", "sdrdr"] + CLS["heavy"] + [c + "_dr" for c in CLS["heavy"]] + ["lekkie_ciez", "lekkie_ciez_dr"]].copy()
sh["heavy_sdr"] = sh[CLS["heavy"]].sum(axis=1) / sh.sdr
sh["heavy_sdrdr"] = sh[[c + "_dr" for c in CLS["heavy"]]].sum(axis=1) / sh.sdrdr
sh["heavy_target_ratio"] = sh.heavy_sdrdr / sh.heavy_sdr
light = ["motocykle", "osobowe", "mikrobusy", "lekkie_ciez"]
sh2 = g.drop_duplicates("nr")
sh["lcv_target_ratio"] = (sh2[[c + "_dr" for c in light]].sum(axis=1) / sh2.sdrdr) / (sh2[light].sum(axis=1) / sh2.sdr)
print(sh[["nr", "droga", "heavy_sdr", "heavy_sdrdr", "heavy_target_ratio", "lcv_target_ratio"]].round(3).to_string())
out["share_sdr_vs_sdrdr"] = sh[["nr", "heavy_sdr", "heavy_sdrdr", "heavy_target_ratio", "lcv_target_ratio"]].round(4).to_dict(orient="records")
json.dump(out, open("reports/etap2/audyt_g5/wyniki/gpr_recompute.json", "w", encoding="utf-8"), indent=1)
for k, v in out.items():
    if k != "share_sdr_vs_sdrdr":
        print(k, v)
