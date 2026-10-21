"""D23 krok 4: natężenia R7 vs R6 na odcinkach GPR (mediana z 5 runów, rozrzut seedów planów R6 jako próg).
Użycie: uv run python reports/etap2/g5_predkosci_d23/c7b_r7b_vs_r6.py  (z katalogu worktree; R6 z katalogu głównego ../MATSim)"""
import json
import pandas as pd

R6D = "../MATSim/reports/etap2/audyt_g5/poprawki/k8_ref/"
R7D = "reports/etap2/g5_predkosci_d23/r7b/"
R6 = ["g5r6_25pct_s4711", "g5r6_25pct_s1", "g5r6_25pct_s2", "g5r6p1_25pct_s4711", "g5r6p2_25pct_s4711"]
R7 = [r.replace("g5r6", "g5r7b") for r in R6]
PL6 = ["g5r6_25pct_s4711", "g5r6p1_25pct_s4711", "g5r6p2_25pct_s4711"]
CONTROL, LOCAL = [91124, 91866], [10045, 91892, 91119]
CLASS = {**{n: "A1" for n in (71410, 91820, 91821)}, **{n: "DK w Kutnie" for n in (91124, 91866, 91869)},
         **{n: "DW" for n in (10042, 10043, 10044, 10045, 10049)}}
res, rows = {}, []
for cls in ("lcv", "heavy"):
    def sec(d, r):
        t = pd.read_csv(f"{d}gpr_{r}_{cls}.csv")
        return t.groupby("nr").agg(gpr=("gpr_light_dir", "sum"), model=("model_dir", "sum"))
    s6 = {r: sec(R6D, r) for r in R6}; s7 = {r: sec(R7D, r) for r in R7}
    gpr = s6[R6[0]].gpr
    m6 = pd.concat([s6[r].model for r in R6], axis=1); m7 = pd.concat([s7[r].model for r in R7], axis=1)
    mp = pd.concat([s6[r].model for r in PL6], axis=1)
    spread = (mp.max(axis=1) - mp.min(axis=1)) / mp.mean(axis=1)
    med6, med7 = m6.median(axis=1), m7.median(axis=1)
    change = med7 / med6 - 1
    fit = ~gpr.index.isin(CONTROL + LOCAL)
    t = pd.DataFrame({"klasa": [CLASS.get(n, "DK pozostałe") for n in gpr.index], "gpr": gpr.round(0), "R6_proc_GPR": (med6 / gpr * 100).round(0),
                      "R7_proc_GPR": (med7 / gpr * 100).round(0), "zmiana_proc": (change * 100).round(1),
                      "rozrzut_planow_R6_proc": (spread * 100).round(1), "fit15": fit}, index=gpr.index)
    t["ponad_rozrzut"] = t.zmiana_proc.abs() > t.rozrzut_planow_R6_proc
    t.insert(0, "cls", cls); rows.append(t.reset_index())
    out = {}
    for k, g in t.groupby("klasa"):
        r6 = m6.loc[g.index].sum() / gpr[g.index].sum(); r7 = m7.loc[g.index].sum() / gpr[g.index].sum()
        out[k] = {"n": len(g), "R6": f"{r6.median()*100:.0f}% ({r6.min()*100:.0f}-{r6.max()*100:.0f})",
                  "R7": f"{r7.median()*100:.0f}% ({r7.min()*100:.0f}-{r7.max()*100:.0f})", "zmiana_pp": round((r7.median() - r6.median()) * 100, 1),
                  "ponad_rozrzut_odcinkow": int(g.ponad_rozrzut.sum())}
    f6 = ((med6 / gpr - 1).abs()[fit] <= .15).sum(); f7 = ((med7 / gpr - 1).abs()[fit] <= .15).sum()
    out["15_odcinkow"] = {"w_15proc_R6": int(f6), "w_15proc_R7": int(f7), "mediana_odchylki_R6": round(float((med6 / gpr - 1).abs()[fit].median()), 3),
                          "mediana_odchylki_R7": round(float((med7 / gpr - 1).abs()[fit].median()), 3),
                          "mediana_abs_zmiany_proc": round(float(change.abs()[fit].median() * 100), 1), "maks_abs_zmiany_proc": round(float(change.abs()[fit].max() * 100), 1)}
    res[cls] = out
pd.concat(rows).to_csv(R7D + "c7b_r7b_vs_r6.csv", index=False)
json.dump(res, open(R7D + "c7b_r7b_vs_r6.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps(res, indent=1, ensure_ascii=False))
