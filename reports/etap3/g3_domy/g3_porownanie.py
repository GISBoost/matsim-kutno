"""G3 (D28): R9 (domy BDOT10k, O-D re-estymowane, 50 it.) vs R8 (domy OSM, k=1,0 z G1b, 50 it.) i vs R7b (100 it.).
Uruchom: uv run python -W ignore reports/etap3/g3_domy/g3_porownanie.py   -> g3_porownanie.json, g3_porownanie.png
Rozrzut referencyjny = rozrzut seedów planów referencji (runy s4711, p1, p2), (max-min)/średnia na odcinek (audyt I3).
Referencja główna: g1b k=1,0 (ta sama sieć R8 i 50 iteracji; plany R7b)."""
import io
import json
from pathlib import Path

import matplotlib
import pandas as pd
import zstandard

matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use("dark_background")

H = Path("reports/etap3/g3_domy")
RUNS = ["s4711", "s1", "s2", "p1", "p2"]; PL = [0, 3, 4]
NEW = {"s4711": "g3r9_25pct_s4711", "s1": "g3r9_25pct_s1", "s2": "g3r9_25pct_s2", "p1": "g3r9p1_25pct_s4711", "p2": "g3r9p2_25pct_s4711"}
REF8 = lambda r: Path(f"output/g1b_gha/g1b-k10-{r}")
R7 = {"s4711": "g5r7b_25pct_s4711", "s1": "g5r7b_25pct_s1", "s2": "g5r7b_25pct_s2", "p1": "g5r7bp1_25pct_s4711", "p2": "g5r7bp2_25pct_s4711"}
CONTROL, LOCAL = [91124, 91866], [10045, 91892, 91119]
new_dir = lambda r: Path("output") / NEW[r]
res = {}

# --- 1. spójność runów R9: nogi car z planów, stuck, przepełnione linki -------------------------------------------
plan_of = {"s4711": "g3r9", "s1": "g3r9", "s2": "g3r9", "p1": "g3r9p1", "p2": "g3r9p2"}
chk = {}
for r in RUNS:
    p = Path("scenarios/kutno") / f"plans_{plan_of[r]}_25pct"
    meta = pd.read_csv(str(p) + "_meta.csv")
    exp = 2 * len(meta) + len(pd.read_csv(str(p) + "_tlo.csv")) + len(pd.read_csv(str(p) + "_ciezkie.csv"))
    ce = json.load(open(new_dir(r) / "analiza/check_events.json"))
    q = json.load(open(new_dir(r) / "analiza/queues.json"))
    chk[r] = dict(nogi_car=ce["departures_by_mode"]["car"], oczekiwane=exp, stuck=ce["stuck"], przepelnione_gt2x=q.get("overfilled_links_gt2x"),
                  osoby_dep_ne_arr=len(ce["persons_dep_ne_arr"]))
res["spojnosc_runow"] = chk


# --- 2. GPR: R9 vs R8@50it. i R7b@100it. ------------------------------------------------------------------------------
def sections(base, cls):
    return pd.concat([pd.read_csv(base(r) / f"gpr_{cls}.csv").groupby("nr").agg(m=("model_dir", "sum")).m for r in RUNS], axis=1)


gp = {}
for cls in ("lcv", "heavy"):
    s9 = sections(lambda r: new_dir(r) / "analiza", cls)
    s8 = sections(lambda r: REF8(r) / "analiza", cls)
    s7 = pd.concat([pd.read_csv(f"reports/etap2/g5_predkosci_d23/r7b/gpr_{R7[r]}_{cls}.csv").groupby("nr").agg(m=("model_dir", "sum")).m for r in RUNS], axis=1)
    gpr = pd.read_csv(REF8("s4711") / f"analiza/gpr_{cls}.csv").groupby("nr").gpr_light_dir.sum()
    fit = ~gpr.index.isin(CONTROL + LOCAL)
    out = {}
    for nm, ref in (("R8_50it", s8), ("R7b_100it", s7)):
        mp = ref.iloc[:, PL]; spread = (mp.max(axis=1) - mp.min(axis=1)) / mp.mean(axis=1)
        ch = s9.median(axis=1) / ref.median(axis=1) - 1
        out[nm] = {"w_15proc_ref": int(((ref.median(axis=1) / gpr - 1).abs()[fit] <= .15).sum()),
                   "mediana_abs_zmiany_proc": round(float(ch.abs()[fit].median() * 100), 2), "maks_abs_zmiany_proc": round(float(ch.abs()[fit].max() * 100), 2),
                   "odcinki_ponad_rozrzut": int((ch.abs() > spread)[fit].sum()), "mediana_rozrzutu_planow_proc": round(float(spread.median() * 100), 1),
                   "zmiana_suma_proc": round(float((s9.median(axis=1).sum() / ref.median(axis=1).sum() - 1) * 100), 2),
                   "sekcje_ponad_rozrzut_proc": {int(k): round(float(ch[k] * 100), 1) for k in ch.index[(ch.abs() > spread) & fit]}}
        if nm == "R8_50it":
            gp[cls] = dict(ch=ch, spread=spread, fit=fit)
    m9 = s9.median(axis=1)
    out["w_15proc_R9"] = int(((m9 / gpr - 1).abs()[fit] <= .15).sum()); out["n_fit"] = int(fit.sum())
    out["poza_15proc_R9_proc"] = {int(k): round(float((m9[k] / gpr[k] - 1) * 100), 1) for k in gpr.index[fit] if abs(m9[k] / gpr[k] - 1) > .15}
    out["odcinki_kontrolne_lokalne_R9_proc_GPR"] = {int(k): round(float(m9[k] / gpr[k] * 100), 0) for k in CONTROL + LOCAL}
    res["gpr_" + cls] = out

# --- 3. opóźnienia i przyczyny -------------------------------------------------------------------------------------------
dl = lambda base, r: json.load(open(base(r) / "analiza/delay.json"))["total_delay_veh_h"]
d9 = [dl(new_dir, r) for r in RUNS]; d8 = [dl(REF8, r) for r in RUNS]
cause = lambda base: {c: round(sorted(json.load(open(base(r) / "analiza/queues.json"))["delay_share_by_cause"][c] for r in RUNS)[2], 3) for c in ("capacity", "node", "spillback")}
res["opoznienia_veh_h_proby"] = {"R9": d9, "R8_50it": d8, "mediana_R9": sorted(d9)[2], "mediana_R8": sorted(d8)[2],
                                 "rozrzut_planow_R9": round(max(d9[i] for i in PL) - min(d9[i] for i in PL), 1),
                                 "rozrzut_planow_R8": round(max(d8[i] for i in PL) - min(d8[i] for i in PL), 1),
                                 "przyczyny_mediana_R9": cause(new_dir), "przyczyny_mediana_R8": cause(REF8)}


# --- 4. podróże mieszkańców (domy się zmieniły): czas i dystans podróży car z domu agentów r i o ------------------------
def trips(base):
    rows = []
    for r in RUNS:
        z = zstandard.ZstdDecompressor().stream_reader(open(base(r) / "output_trips.csv.zst", "rb")).read()
        t = pd.read_csv(io.BytesIO(z), sep=";", usecols=["person", "trav_time", "traveled_distance", "euclidean_distance", "main_mode", "start_activity_type"])
        t = t[(t.main_mode == "car") & t.person.str[0].isin(["r", "o"]) & (t.start_activity_type == "home")]
        sec = pd.to_timedelta(t.trav_time).dt.total_seconds()
        rows.append(dict(n=len(t), czas_min=float(sec.mean() / 60), dystans_km=float(t.traveled_distance.mean() / 1000), euklides_km=float(t.euclidean_distance.mean() / 1000)))
    return pd.DataFrame(rows, index=RUNS)


t9, t8 = trips(new_dir), trips(REF8)
res["podroze_dom_praca_rezydenci_wyjezdzajacy"] = {"R9_srednie_runow": t9.mean().round(2).to_dict(), "R8_50it_srednie_runow": t8.mean().round(2).to_dict(),
                                                    "rozrzut_planow_R8_czas_min": round(float(t8.czas_min.iloc[PL].max() - t8.czas_min.iloc[PL].min()), 2),
                                                    "rozrzut_planow_R8_dystans_km": round(float(t8.dystans_km.iloc[PL].max() - t8.dystans_km.iloc[PL].min()), 2)}
json.dump(res, open(H / "g3_porownanie.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps(res, indent=1, ensure_ascii=False))

# --- wykres ------------------------------------------------------------------------------------------------------------------
fig, ax = plt.subplots(1, 3, figsize=(18, 5.5))
for a_, cls in zip(ax[:2], ("lcv", "heavy")):
    g = gp[cls]; x = list(range(int(g["fit"].sum())))
    ch, sp = g["ch"][g["fit"]] * 100, g["spread"][g["fit"]] * 100
    a_.fill_between(x, -sp.to_numpy(), sp.to_numpy(), color="#555", alpha=.6, label="rozrzut seedów planów R8")
    a_.bar(x, ch.to_numpy(), color="#4fc3f7", label="R9 vs R8 (mediana 5 runów)")
    a_.set_xticks(x); a_.set_xticklabels([str(i) for i in ch.index], rotation=90, fontsize=7)
    a_.set_title(f"zmiana natężenia na odcinku GPR, {cls} [%]"); a_.axhline(0, color="w", lw=.5); a_.legend(fontsize=8)
w = .38
ax[2].bar([i - w / 2 for i in range(5)], d8, w, color="#aaa", label="R8 (domy OSM), 50 it.")
ax[2].bar([i + w / 2 for i in range(5)], d9, w, color="#4fc3f7", label="R9 (domy BDOT), 50 it.")
ax[2].set_xticks(range(5)); ax[2].set_xticklabels(RUNS); ax[2].set_title("opóźnienie dobowe [poj.-h próbki]"); ax[2].legend(fontsize=8)
fig.suptitle("G3 (D28): domy z BDOT10k vs OSM")
fig.tight_layout(); fig.savefig(H / "g3_porownanie.png", dpi=130)
