"""D36: pozostałe cele GUS dom–X mieszkańców (r94e, errand_other=on, tło z estymacji r94e) vs R9.4 (r93o): zawrotki, GPR, opóźnienia, czasy podróży,
osobne wyjścia wg typu celu, pomiary miejskie WIOŚ 2013 (analiza/wios2013.json z pipeline/pomiary_miejskie.py).
Wejście: artefakty GitHub Actions w output/r94e_gha/r94e-<v>-<id>/ (v = r94e, r93o; id = s4711, s1, s2, p1, p2).
Użycie: uv run python -W ignore reports/etap3/g_inne_cele/inne_cele_porownanie.py
Rozrzut referencyjny = rozrzut seedów planów kontroli r93o (runy s4711, p1, p2), (max-min)/średnia na odcinek. Na bazie lancuchy_porownanie.py (D35)."""
import io
import json
from pathlib import Path

import matplotlib
import pandas as pd
import zstandard

matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use("dark_background")

V, C = "r94e", "r93o"
G = Path("output/r94e_gha"); H = Path("reports/etap3/g_inne_cele")
RUNS = ["s4711", "s1", "s2", "p1", "p2"]; PL = [0, 3, 4]
CONTROL, LOCAL = [91124, 91866], [10045, 91892, 91119]
A = lambda v, r: G / f"{V}-{v}-{r}" / "analiza"
res = {}

# --- spójność ---------------------------------------------------------------------------------------------------------
plan = {"s4711": "p0", "s1": "p0", "s2": "p0", "p1": "p1", "p2": "p2"}
chk = {}
for v in (V, C):
    chk[v] = {}
    for r in RUNS:
        stem = f"plans_g3{v}{'' if plan[r] == 'p0' else plan[r]}_25pct"
        meta = pd.read_csv(f"scenarios/kutno_r91/meta_{v}_{plan[r]}.csv")
        ne = len(pd.read_csv(f"scenarios/kutno/{stem}_errands.csv"))
        extra = sum(int(meta[c].notna().sum()) for c in ("esc_link", "stop_link") if c in meta)  # D35: każdy postój = +1 noga car
        exp = 2 * len(meta) + extra + 2 * ne + len(pd.read_csv(f"scenarios/kutno/{stem}_tlo.csv")) + len(pd.read_csv(f"scenarios/kutno/{stem}_ciezkie.csv"))
        ce = json.load(open(A(v, r) / "check_events.json")); q = json.load(open(A(v, r) / "queues.json"))
        chk[v][r] = dict(nogi_car=ce["departures_by_mode"]["car"], oczekiwane=exp, stuck=ce["stuck"], przepelnione_gt2x=q.get("overfilled_links_gt2x"))
res["spojnosc"] = chk

# --- zawrotki -----------------------------------------------------------------------------------------------------------
zw = {v: [json.load(open(A(v, r) / "zawrotki.json")) for r in RUNS] for v in (V, C)}  # liczone na runnerze (zdarzeń nie ma w artefaktach)
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
    s91, s9 = sec(lambda r: A(V, r), cls), sec(lambda r: A(C, r), cls)
    gpr = pd.read_csv(A(C, "s4711") / f"gpr_{cls}.csv").groupby("nr").gpr_light_dir.sum()
    fit = ~gpr.index.isin(CONTROL + LOCAL)
    mp = s9.iloc[:, PL]; spread = (mp.max(axis=1) - mp.min(axis=1)) / mp.mean(axis=1)
    ch = s91.median(axis=1) / s9.median(axis=1) - 1
    m91 = s91.median(axis=1)
    res["gpr_" + cls] = {"w_15proc_" + V: int(((m91 / gpr - 1).abs()[fit] <= .15).sum()), "w_15proc_" + C: int(((s9.median(axis=1) / gpr - 1).abs()[fit] <= .15).sum()), "n_fit": int(fit.sum()),
                         "poza_15proc_" + V + "_proc": {int(k): round(float((m91[k] / gpr[k] - 1) * 100), 1) for k in gpr.index[fit] if abs(m91[k] / gpr[k] - 1) > .15},
                         "mediana_abs_zmiany_proc": round(float(ch.abs()[fit].median() * 100), 2), "maks_abs_zmiany_proc": round(float(ch.abs()[fit].max() * 100), 2),
                         "odcinki_ponad_rozrzut": int((ch.abs() > spread)[fit].sum()), "sekcje_ponad_rozrzut_proc": {int(k): round(float(ch[k] * 100), 1) for k in ch.index[(ch.abs() > spread) & fit]},
                         "mediana_rozrzutu_planow_proc": round(float(spread.median() * 100), 1),
                         "kontrolne_lokalne_" + V + "_proc_GPR": {int(k): round(float(m91[k] / gpr[k] * 100), 0) for k in CONTROL + LOCAL}}
    gp[cls] = dict(ch=ch, spread=spread, fit=fit)

# --- opóźnienia ------------------------------------------------------------------------------------------------------------------
dl = lambda v, r: json.load(open(A(v, r) / "delay.json"))["total_delay_veh_h"]
d91 = [dl(V, r) for r in RUNS]; d9 = [dl(C, r) for r in RUNS]
cause = lambda v: {c: round(med([json.load(open(A(v, r) / "queues.json"))["delay_share_by_cause"][c] for r in RUNS]), 3) for c in ("capacity", "node", "spillback")}
res["opoznienia_veh_h_proby"] = {V: d91, C: d9, "mediana_" + V: med(d91), "mediana_" + C: med(d9), "rozrzut_planow_" + C: round(max(d9[i] for i in PL) - min(d9[i] for i in PL), 1),
                                 "przyczyny_" + V: cause(V), "przyczyny_" + C: cause(C)}


# --- czasy podróży dom -> praca mieszkańców -----------------------------------------------------------------------------------------
def trips(v, kinds=("r", "o", "c"), acts=None):
    rows = []
    for r in RUNS:
        z = zstandard.ZstdDecompressor().stream_reader(open(G / f"{V}-{v}-{r}" / "output_trips.csv.zst", "rb")).read()
        t = pd.read_csv(io.BytesIO(z), sep=";", usecols=["person", "trav_time", "traveled_distance", "main_mode", "start_activity_type", "end_activity_type"])
        t = t[(t.main_mode == "car") & t.person.str[0].isin(list(kinds))]
        if acts:  # podróże do lub z aktywności danego typu
            t = t[t.start_activity_type.isin(acts) | t.end_activity_type.isin(acts)]
        sec_ = pd.to_timedelta(t.trav_time).dt.total_seconds()
        rows.append(dict(n=len(t), czas_min=float(sec_.mean() / 60), dystans_km=float(t.traveled_distance.mean() / 1000)))
    return pd.DataFrame(rows, index=RUNS)


t91, t9 = trips(V), trips(C)
res["podroze_pracujacych_car"] = {V: t91.mean().round(2).to_dict(), C: t9.mean().round(2).to_dict(),
                                  "rozrzut_planow_" + C + "_czas_min": round(float(t9.czas_min.iloc[PL].max() - t9.czas_min.iloc[PL].min()), 2)}
res["podroze_wyjscia_wg_celu_car"] = {v: {a: trips(v, ("e",), [a]).mean().round(2).to_dict() for a in ("shop", "service", "visit", "leisure", "health", "escort")}
                                     for v in (V, C)}

# --- pomiary miejskie WIOŚ 2013 (cel 2025 = doba 2013 × f_suma) ------------------------------------------------------------
ww = {v: pd.concat([pd.DataFrame(json.load(open(A(v, r) / "wios2013.json", encoding="utf-8"))["punkty"]).set_index("pkt").model_razem for r in RUNS], axis=1)
      for v in (V, C)}
w0 = pd.DataFrame(json.load(open(A(C, "s4711") / "wios2013.json", encoding="utf-8"))["punkty"]).set_index("pkt")
res["pomiary_miejskie"] = {"cel_2025": w0.cel_2025.round(0).to_dict(), "cel_2025_korytarz": w0.cel_2025_korytarz.round(0).to_dict(),
                           **{f"model_{v}_mediana": ww[v].median(axis=1).round(0).to_dict() for v in ww},
                           **{f"proc_celu_{v}": (100 * ww[v].median(axis=1) / w0.cel_2025).round(1).to_dict() for v in ww},
                           **{f"suma_proc_celu_{v}": round(float(100 * ww[v].median(axis=1).sum() / w0.cel_2025.sum()), 1) for v in ww},
                           "zmiana_proc": (100 * (ww[V].median(axis=1) / ww[C].median(axis=1) - 1)).round(1).to_dict(),
                           "rozrzut_planow_proc": (100 * (ww[C].iloc[:, PL].max(axis=1) - ww[C].iloc[:, PL].min(axis=1))
                                                   / ww[C].iloc[:, PL].mean(axis=1)).round(1).to_dict()}
json.dump(res, open(H / "inne_cele_porownanie.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps(res, indent=1, ensure_ascii=False))

fig, ax = plt.subplots(1, 3, figsize=(18, 5.5))
pm = res["pomiary_miejskie"]; pts = list(pm["cel_2025"]); x = range(len(pts))
lo = [w0.doba_2013[p] for p in pts]; hi = [max(pm["cel_2025"][p], pm["cel_2025_korytarz"][p]) for p in pts]
ax[0].bar(x, [h - l for l, h in zip(lo, hi)], .8, bottom=lo, color="#555", label="pomiar 2013 → 2025 (pasmo ×1 do max(f_suma, f_korytarz))")
ax[0].scatter(x, [pm["cel_2025"][p] for p in pts], color="w", marker="_", s=400, label="cel 2025 (f_suma)")
for i, (v, col) in enumerate(((C, "#aaa"), (V, "#4fc3f7"))):
    ax[0].bar([k + (i - .5) * .3 for k in x], [pm[f"model_{v}_mediana"][p] for p in pts], .3, color=col,
              label={C: "R9.4 (r93o)", V: "D36 (r94e)"}[v] + ", mediana 5 runów")
ax[0].set_xticks(list(x)); ax[0].set_xticklabels([f"{p} {w0.ulica[p].split()[-1]}" for p in pts], fontsize=8)
ax[0].set_title("pomiary miejskie: poj./dobę, oba kierunki"); ax[0].legend(fontsize=7)
for a_, cls in zip(ax[1:], ("lcv", "heavy")):
    g = gp[cls]; x = list(range(int(g["fit"].sum()))); ch, sp = g["ch"][g["fit"]] * 100, g["spread"][g["fit"]] * 100
    a_.fill_between(x, -sp.to_numpy(), sp.to_numpy(), color="#555", alpha=.6, label="rozrzut seedów planów " + C)
    a_.bar(x, ch.to_numpy(), color="#4fc3f7", label=f"{V} vs {C} (mediana 5 runów)")
    a_.set_xticks(x); a_.set_xticklabels([str(i) for i in ch.index], rotation=90, fontsize=7); a_.axhline(0, color="w", lw=.5)
    a_.set_title(f"zmiana natężenia na odcinku GPR, {cls} [%]"); a_.legend(fontsize=8)
fig.suptitle("D36: pozostałe cele mieszkańców (r94e) vs R9.4 (r93o)")
fig.text(.01, .01, "Jak czytać. Lewy: pomiary miejskie WIOŚ K1–K5, poj./dobę oba kierunki; szary prostokąt = pasmo celu 2025 (doba 2013 bez wzrostu do max(f_suma, f_korytarz)), "
         "biała kreska = cel 2025 (f_suma 1,21), słupki = model R9.4 (szary) i D36 (niebieski), mediana 5 runów. "
         "Środek i prawy: zmiana natężenia D36 względem R9.4 na odcinkach GPR (oś X: numer odcinka), lekkie i ciężkie, mediana 5 runów; szare pasmo = rozrzut seedów planów R9.4 "
         "((max − min) / średnia, runy s4711, p1, p2). Źródło: artefakty GHA matsim-r93 variant=r94e control=r93o. Skrypt inne_cele_porownanie.py, opis w inne_cele.md.",
         fontsize=8, va="bottom", wrap=True)
fig.tight_layout(rect=(0, .1, 1, 1)); fig.savefig(H / "inne_cele_porownanie.png", dpi=130)
