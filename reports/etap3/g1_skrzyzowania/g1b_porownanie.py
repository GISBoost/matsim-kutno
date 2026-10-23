"""G1b (D27): k=0,8/0,6/0,4 vs k=1,0 (R8, 50 it., GitHub Actions). Użycie: uv run python -W ignore reports/etap3/g1_skrzyzowania/g1b_porownanie.py
Rozrzut referencyjny: rozrzut seedów planów przy k=1,0 (runy s4711, p1, p2), (max-min)/średnia na odcinek."""
import json
from pathlib import Path
import pandas as pd, zstandard, io
G = Path("output/g1b_gha"); H = Path("reports/etap3/g1_skrzyzowania")
RUNS = ["s4711", "s1", "s2", "p1", "p2"]; PL = [0, 3, 4]; K = ["10", "08", "06", "04"]
CONTROL, LOCAL = [91124, 91866], [10045, 91892, 91119]
A = lambda k, r: G / f"g1b-k{k}-{r}" / "analiza"
res = {}
for cls in ("lcv", "heavy"):
    sec = {k: pd.concat([pd.read_csv(A(k, r) / f"gpr_{cls}.csv").groupby("nr").agg(m=("model_dir", "sum")).m for r in RUNS], axis=1) for k in K}
    gpr = pd.read_csv(A("10", "s4711") / f"gpr_{cls}.csv").groupby("nr").gpr_light_dir.sum()
    fit = ~gpr.index.isin(CONTROL + LOCAL)
    base = sec["10"]; mp = base.iloc[:, PL]; spread = (mp.max(axis=1) - mp.min(axis=1)) / mp.mean(axis=1)
    med10 = base.median(axis=1); out = {}
    for k in K:
        med = sec[k].median(axis=1); ch = med / med10 - 1
        out[k] = {"w_15proc": int(((med / gpr - 1).abs()[fit] <= .15).sum()), "n_fit": int(fit.sum()),
                  "mediana_abs_zmiany_proc": round(float(ch.abs()[fit].median() * 100), 2), "maks_abs_zmiany_proc": round(float(ch.abs()[fit].max() * 100), 2),
                  "odcinki_ponad_rozrzut": int((ch.abs() > spread)[fit].sum()), "zmiana_suma_proc": round(float((med.sum() / med10.sum() - 1) * 100), 2)}
    out["mediana_rozrzutu_planow_proc"] = round(float(spread.median() * 100), 1)
    res[cls] = out
op = {}
for k in K:
    d = [json.load(open(A(k, r) / "delay.json"))["total_delay_veh_h"] for r in RUNS]
    q = [json.load(open(A(k, r) / "queues.json")) for r in RUNS]
    tt = []
    for r in RUNS:
        t = pd.read_csv(io.BytesIO(zstandard.ZstdDecompressor().stream_reader(open(G / f"g1b-k{k}-{r}" / "output_trips.csv.zst", "rb")).read()), sep=";", usecols=["main_mode", "trav_time"]) if False else None
        tt.append(None)
    op[k] = {"opoznienie_veh_h_runy": d, "mediana": sorted(d)[2], "rozrzut_planow": round(max(d[i] for i in PL) - min(d[i] for i in PL), 1),
             "przyczyny_mediana": {c: round(sorted(x["delay_share_by_cause"][c] for x in q)[2], 3) for c in ("capacity", "node", "spillback")},
             "stuck": [json.load(open(A(k, r) / "check_events.json"))["stuck"] for r in RUNS],
             "overfilled": [x.get("overfilled_links_gt2x") for x in q]}
res["opoznienia"] = op
json.dump(res, open(H / "g1b_porownanie.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps(res, indent=1, ensure_ascii=False))
