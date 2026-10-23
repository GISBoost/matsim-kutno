"""R9.1 (D29) vs R9: zawrotki, GPR, opóźnienia, czasy podróży. Wejście: artefakty GitHub Actions w output/r91_gha/r91-<v>-<id>/ (v = r91, r9; id = s4711, s1, s2, p1, p2)
oraz lokalny R9 (output/g3r9_*) do sprawdzenia zgodności platform. Użycie: uv run python -W ignore reports/etap3/g_zawrotki/zawrotki_porownanie.py
Rozrzut referencyjny = rozrzut seedów planów R9 na GHA (runy s4711, p1, p2), (max-min)/średnia na odcinek."""
import io
import json
from pathlib import Path

import matplotlib
import pandas as pd
import zstandard

matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use("dark_background")

G = Path("output/r91_gha"); H = Path("reports/etap3/g_zawrotki")
RUNS = ["s4711", "s1", "s2", "p1", "p2"]; PL = [0, 3, 4]
LOCAL9 = {"s4711": "g3r9_25pct_s4711", "s1": "g3r9_25pct_s1", "s2": "g3r9_25pct_s2", "p1": "g3r9p1_25pct_s4711", "p2": "g3r9p2_25pct_s4711"}
CONTROL, LOCAL = [91124, 91866], [10045, 91892, 91119]
A = lambda v, r: G / f"r91-{v}-{r}" / "analiza"
res = {}

# --- spójność ---------------------------------------------------------------------------------------------------------
plan = {"s4711": "p0", "s1": "p0", "s2": "p0", "p1": "p1", "p2": "p2"}
chk = {}
for v in ("r91", "r9"):
    chk[v] = {}
    for r in RUNS:
        stem = f"plans_g3{v}{'' if plan[r] == 'p0' else plan[r]}_25pct"
        meta = pd.read_csv(f"scenarios/kutno/{stem}_meta.csv")
        exp = 2 * len(meta) + len(pd.read_csv(f"scenarios/kutno/{stem}_tlo.csv")) + len(pd.read_csv(f"scenarios/kutno/{stem}_ciezkie.csv"))
        ce = json.load(open(A(v, r) / "check_events.json")); q = json.load(open(A(v, r) / "queues.json"))
        chk[v][r] = dict(nogi_car=ce["departures_by_mode"]["car"], oczekiwane=exp, stuck=ce["stuck"], przepelnione_gt2x=q.get("overfilled_links_gt2x"))
res["spojnosc"] = chk

# --- zawrotki -----------------------------------------------------------------------------------------------------------
zw = {v: [json.load(open(A(v, r) / "zawrotki.json")) for r in RUNS] for v in ("r91", "r9")}  # liczone na runnerze (zdarzeń nie ma w artefaktach)
med = lambda xs: sorted(xs)[len(xs) // 2]
res["zawrotki"] = {v: {"razem_mediana": {k: med([z["razem"][k] for z in zw[v]]) for k in ("start_pct", "end_pct", "any_pct", "mid_pct", "extra_pct", "extra_veh_h", "mean_extra_s_on_uturn_trips")},
                       "wg_rodzaju_mediana": {kd: {k: round(med([z["wg_rodzaju"][kd][k] for z in zw[v]]), 2) for k in ("start_pct", "end_pct", "extra_pct_of_time")}
                                              for kd in zw[v][0]["wg_rodzaju"]},
                       "pracujacy_tam_vs_z_powrotem": zw[v][0]["pracujacy_tam_vs_z_powrotem"]} for v in zw}


# --- GPR -------------------------------------------------------------------------------------------------------------------
def sec(base, cls):
    return pd.concat([pd.read_csv(base(r) / f"gpr_{cls}.csv").groupby("nr").agg(m=("model_dir", "sum")).m for r in RUNS], axis=1)


gp = {}
for cls in ("lcv", "heavy"):
    s91, s9 = sec(lambda r: A("r91", r), cls), sec(lambda r: A("r9", r), cls)
    sl = sec(lambda r: Path("output") / LOCAL9[r] / "analiza", cls)
    gpr = pd.read_csv(A("r9", "s4711") / f"gpr_{cls}.csv").groupby("nr").gpr_light_dir.sum()
    fit = ~gpr.index.isin(CONTROL + LOCAL)
    mp = s9.iloc[:, PL]; spread = (mp.max(axis=1) - mp.min(axis=1)) / mp.mean(axis=1)
    ch = s91.median(axis=1) / s9.median(axis=1) - 1
    m91 = s91.median(axis=1)
    res["gpr_" + cls] = {"w_15proc_R91": int(((m91 / gpr - 1).abs()[fit] <= .15).sum()), "w_15proc_R9": int(((s9.median(axis=1) / gpr - 1).abs()[fit] <= .15).sum()), "n_fit": int(fit.sum()),
                         "poza_15proc_R91_proc": {int(k): round(float((m91[k] / gpr[k] - 1) * 100), 1) for k in gpr.index[fit] if abs(m91[k] / gpr[k] - 1) > .15},
                         "mediana_abs_zmiany_proc": round(float(ch.abs()[fit].median() * 100), 2), "maks_abs_zmiany_proc": round(float(ch.abs()[fit].max() * 100), 2),
                         "odcinki_ponad_rozrzut": int((ch.abs() > spread)[fit].sum()), "sekcje_ponad_rozrzut_proc": {int(k): round(float(ch[k] * 100), 1) for k in ch.index[(ch.abs() > spread) & fit]},
                         "mediana_rozrzutu_planow_proc": round(float(spread.median() * 100), 1),
                         "platformy_R9_GHA_vs_lokalnie_mediana_abs_proc": round(float((s9.median(axis=1) / sl.median(axis=1) - 1).abs()[fit].median() * 100), 2),
                         "kontrolne_lokalne_R91_proc_GPR": {int(k): round(float(m91[k] / gpr[k] * 100), 0) for k in CONTROL + LOCAL}}
    gp[cls] = dict(ch=ch, spread=spread, fit=fit)

# --- opóźnienia ------------------------------------------------------------------------------------------------------------------
dl = lambda v, r: json.load(open(A(v, r) / "delay.json"))["total_delay_veh_h"]
d91 = [dl("r91", r) for r in RUNS]; d9 = [dl("r9", r) for r in RUNS]
cause = lambda v: {c: round(med([json.load(open(A(v, r) / "queues.json"))["delay_share_by_cause"][c] for r in RUNS]), 3) for c in ("capacity", "node", "spillback")}
res["opoznienia_veh_h_proby"] = {"R91": d91, "R9_GHA": d9, "mediana_R91": med(d91), "mediana_R9": med(d9), "rozrzut_planow_R9": round(max(d9[i] for i in PL) - min(d9[i] for i in PL), 1),
                                 "przyczyny_R91": cause("r91"), "przyczyny_R9": cause("r9")}


# --- czasy podróży dom -> praca mieszkańców -----------------------------------------------------------------------------------------
def trips(v):
    rows = []
    for r in RUNS:
        z = zstandard.ZstdDecompressor().stream_reader(open(G / f"r91-{v}-{r}" / "output_trips.csv.zst", "rb")).read()
        t = pd.read_csv(io.BytesIO(z), sep=";", usecols=["person", "trav_time", "traveled_distance", "main_mode", "start_activity_type"])
        t = t[(t.main_mode == "car") & t.person.str[0].isin(["r", "o", "c"])]
        sec_ = pd.to_timedelta(t.trav_time).dt.total_seconds()
        rows.append(dict(n=len(t), czas_min=float(sec_.mean() / 60), dystans_km=float(t.traveled_distance.mean() / 1000)))
    return pd.DataFrame(rows, index=RUNS)


t91, t9 = trips("r91"), trips("r9")
res["podroze_pracujacych_car"] = {"R91": t91.mean().round(2).to_dict(), "R9": t9.mean().round(2).to_dict(),
                                  "rozrzut_planow_R9_czas_min": round(float(t9.czas_min.iloc[PL].max() - t9.czas_min.iloc[PL].min()), 2)}
json.dump(res, open(H / "zawrotki_porownanie.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps(res, indent=1, ensure_ascii=False))

fig, ax = plt.subplots(1, 3, figsize=(18, 5.5))
kinds = ["r", "c", "o", "t", "h"]
w = .38
for i, (v, col) in enumerate((("r9", "#aaa"), ("r91", "#4fc3f7"))):
    z = res["zawrotki"][v]["wg_rodzaju_mediana"]
    ax[0].bar([k + (i - .5) * w for k in range(5)], [z[k]["start_pct"] + z[k]["end_pct"] for k in kinds], w, color=col, label={"r9": "R9", "r91": "R9.1"}[v])
ax[0].set_xticks(range(5)); ax[0].set_xticklabels(["mieszk.", "dojeżdż.", "wyjeżdż.", "tło lekkie", "tło ciężkie"], fontsize=8)
ax[0].set_title("zawrotka na starcie + końcu trasy [% podróży]"); ax[0].legend()
for a_, cls in zip(ax[1:], ("lcv", "heavy")):
    g = gp[cls]; x = list(range(int(g["fit"].sum()))); ch, sp = g["ch"][g["fit"]] * 100, g["spread"][g["fit"]] * 100
    a_.fill_between(x, -sp.to_numpy(), sp.to_numpy(), color="#555", alpha=.6, label="rozrzut seedów planów R9")
    a_.bar(x, ch.to_numpy(), color="#4fc3f7", label="R9.1 vs R9 (mediana 5 runów)")
    a_.set_xticks(x); a_.set_xticklabels([str(i) for i in ch.index], rotation=90, fontsize=7); a_.axhline(0, color="w", lw=.5)
    a_.set_title(f"zmiana natężenia na odcinku GPR, {cls} [%]"); a_.legend(fontsize=8)
fig.suptitle("R9.1 (D29): kierunek linku przypięcia wg trasy"); fig.tight_layout(); fig.savefig(H / "zawrotki_porownanie.png", dpi=130)
