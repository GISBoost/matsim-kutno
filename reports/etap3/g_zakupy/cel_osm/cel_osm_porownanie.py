"""D34: cel zakupów wg sklepów OSM (r93o, errand_dest=osm, tło z estymacji r93o) vs R9.3 (r93): zawrotki, GPR, opóźnienia, czasy podróży.
Wejście: artefakty GitHub Actions w output/r93o_gha/r93o-<v>-<id>/ (v = r93o, r93; id = s4711, s1, s2, p1, p2). Użycie: uv run python -W ignore reports/etap3/g_zakupy/cel_osm/cel_osm_porownanie.py
Rozrzut referencyjny = rozrzut seedów planów kontroli r93 (runy s4711, p1, p2), (max-min)/średnia na odcinek. Na bazie zakupy_porownanie.py (D32)."""
import io
import json
from pathlib import Path

import matplotlib
import pandas as pd
import zstandard

matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use("dark_background")

G = Path("output/r93o_gha"); H = Path("reports/etap3/g_zakupy/cel_osm")
RUNS = ["s4711", "s1", "s2", "p1", "p2"]; PL = [0, 3, 4]
CONTROL, LOCAL = [91124, 91866], [10045, 91892, 91119]
A = lambda v, r: G / f"r93o-{v}-{r}" / "analiza"
res = {}

# --- spójność ---------------------------------------------------------------------------------------------------------
plan = {"s4711": "p0", "s1": "p0", "s2": "p0", "p1": "p1", "p2": "p2"}
chk = {}
for v in ("r93o", "r93"):
    chk[v] = {}
    for r in RUNS:
        stem = f"plans_g3{v}{'' if plan[r] == 'p0' else plan[r]}_25pct"
        meta = pd.read_csv(f"scenarios/kutno_r91/meta_{v}_{plan[r]}.csv")
        ne = len(pd.read_csv(f"scenarios/kutno/{stem}_errands.csv"))
        exp = 2 * len(meta) + 2 * ne + len(pd.read_csv(f"scenarios/kutno/{stem}_tlo.csv")) + len(pd.read_csv(f"scenarios/kutno/{stem}_ciezkie.csv"))
        ce = json.load(open(A(v, r) / "check_events.json")); q = json.load(open(A(v, r) / "queues.json"))
        chk[v][r] = dict(nogi_car=ce["departures_by_mode"]["car"], oczekiwane=exp, stuck=ce["stuck"], przepelnione_gt2x=q.get("overfilled_links_gt2x"))
res["spojnosc"] = chk

# --- zawrotki -----------------------------------------------------------------------------------------------------------
zw = {v: [json.load(open(A(v, r) / "zawrotki.json")) for r in RUNS] for v in ("r93o", "r93")}  # liczone na runnerze (zdarzeń nie ma w artefaktach)
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
    s91, s9 = sec(lambda r: A("r93o", r), cls), sec(lambda r: A("r93", r), cls)
    gpr = pd.read_csv(A("r93", "s4711") / f"gpr_{cls}.csv").groupby("nr").gpr_light_dir.sum()
    fit = ~gpr.index.isin(CONTROL + LOCAL)
    mp = s9.iloc[:, PL]; spread = (mp.max(axis=1) - mp.min(axis=1)) / mp.mean(axis=1)
    ch = s91.median(axis=1) / s9.median(axis=1) - 1
    m91 = s91.median(axis=1)
    res["gpr_" + cls] = {"w_15proc_r93o": int(((m91 / gpr - 1).abs()[fit] <= .15).sum()), "w_15proc_r93": int(((s9.median(axis=1) / gpr - 1).abs()[fit] <= .15).sum()), "n_fit": int(fit.sum()),
                         "poza_15proc_r93o_proc": {int(k): round(float((m91[k] / gpr[k] - 1) * 100), 1) for k in gpr.index[fit] if abs(m91[k] / gpr[k] - 1) > .15},
                         "mediana_abs_zmiany_proc": round(float(ch.abs()[fit].median() * 100), 2), "maks_abs_zmiany_proc": round(float(ch.abs()[fit].max() * 100), 2),
                         "odcinki_ponad_rozrzut": int((ch.abs() > spread)[fit].sum()), "sekcje_ponad_rozrzut_proc": {int(k): round(float(ch[k] * 100), 1) for k in ch.index[(ch.abs() > spread) & fit]},
                         "mediana_rozrzutu_planow_proc": round(float(spread.median() * 100), 1),
                         "kontrolne_lokalne_r93o_proc_GPR": {int(k): round(float(m91[k] / gpr[k] * 100), 0) for k in CONTROL + LOCAL}}
    gp[cls] = dict(ch=ch, spread=spread, fit=fit)

# --- opóźnienia ------------------------------------------------------------------------------------------------------------------
dl = lambda v, r: json.load(open(A(v, r) / "delay.json"))["total_delay_veh_h"]
d91 = [dl("r93o", r) for r in RUNS]; d9 = [dl("r93", r) for r in RUNS]
cause = lambda v: {c: round(med([json.load(open(A(v, r) / "queues.json"))["delay_share_by_cause"][c] for r in RUNS]), 3) for c in ("capacity", "node", "spillback")}
res["opoznienia_veh_h_proby"] = {"r93o": d91, "r93": d9, "mediana_r93o": med(d91), "mediana_r93": med(d9), "rozrzut_planow_r93": round(max(d9[i] for i in PL) - min(d9[i] for i in PL), 1),
                                 "przyczyny_r93o": cause("r93o"), "przyczyny_r93": cause("r93")}


# --- czasy podróży dom -> praca mieszkańców -----------------------------------------------------------------------------------------
def trips(v, kinds=("r", "o", "c")):
    rows = []
    for r in RUNS:
        z = zstandard.ZstdDecompressor().stream_reader(open(G / f"r93o-{v}-{r}" / "output_trips.csv.zst", "rb")).read()
        t = pd.read_csv(io.BytesIO(z), sep=";", usecols=["person", "trav_time", "traveled_distance", "main_mode", "start_activity_type"])
        t = t[(t.main_mode == "car") & t.person.str[0].isin(list(kinds))]
        sec_ = pd.to_timedelta(t.trav_time).dt.total_seconds()
        rows.append(dict(n=len(t), czas_min=float(sec_.mean() / 60), dystans_km=float(t.traveled_distance.mean() / 1000)))
    return pd.DataFrame(rows, index=RUNS)


t91, t9 = trips("r93o"), trips("r93")
res["podroze_pracujacych_car"] = {"r93o": t91.mean().round(2).to_dict(), "r93": t9.mean().round(2).to_dict(),
                                  "rozrzut_planow_r93_czas_min": round(float(t9.czas_min.iloc[PL].max() - t9.czas_min.iloc[PL].min()), 2)}
res["podroze_zakupy_i_uslugi_car"] = {v: trips(v, ("e",)).mean().round(2).to_dict() for v in ("r93o", "r93")}
json.dump(res, open(H / "cel_osm_porownanie.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps(res, indent=1, ensure_ascii=False))

fig, ax = plt.subplots(1, 3, figsize=(18, 5.5))
kinds = ["r", "c", "o", "t", "h"]
w = .38
for i, (v, col) in enumerate((("r93", "#aaa"), ("r93o", "#4fc3f7"))):
    z = res["zawrotki"][v]["wg_rodzaju_mediana"]
    ax[0].bar([k + (i - .5) * w for k in range(5)], [z[k]["start_pct"] + z[k]["end_pct"] for k in kinds], w, color=col, label={"r93": "R9.3 (cel BDOT)", "r93o": "D34 (cel OSM)"}[v])
ax[0].set_xticks(range(5)); ax[0].set_xticklabels(["mieszk.", "dojeżdż.", "wyjeżdż.", "tło lekkie", "tło ciężkie"], fontsize=8)
ax[0].set_title("zawrotka na starcie + końcu trasy [% podróży]"); ax[0].legend()
for a_, cls in zip(ax[1:], ("lcv", "heavy")):
    g = gp[cls]; x = list(range(int(g["fit"].sum()))); ch, sp = g["ch"][g["fit"]] * 100, g["spread"][g["fit"]] * 100
    a_.fill_between(x, -sp.to_numpy(), sp.to_numpy(), color="#555", alpha=.6, label="rozrzut seedów planów r93")
    a_.bar(x, ch.to_numpy(), color="#4fc3f7", label="r93o vs r93 (mediana 5 runów)")
    a_.set_xticks(x); a_.set_xticklabels([str(i) for i in ch.index], rotation=90, fontsize=7); a_.axhline(0, color="w", lw=.5)
    a_.set_title(f"zmiana natężenia na odcinku GPR, {cls} [%]"); a_.legend(fontsize=8)
fig.suptitle("D34: cel zakupów wg sklepów OSM (r93o) vs R9.3 (r93)"); fig.tight_layout(); fig.savefig(H / "cel_osm_porownanie.png", dpi=130)
