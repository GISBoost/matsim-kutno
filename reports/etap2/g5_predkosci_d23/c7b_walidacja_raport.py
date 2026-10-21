"""D23 krok 5: raport walidacji R7b vs R6 z agregatów (walidacja_{r6,r7b}_tomtom.csv; odpowiedzi dostawcy nie są zapisane, D22).
Grupa D23 = kind D23_X łącznie z podgrupą „trasa<70%" (nakładanie trasy modelu na trasę dostawcy). Okna 07:30/12:30/15:30 łączone ważone n:
MAPE, MAE, RMSE, RMSPE, TAG i pRMSE (średnia z kwadratów i z obserwacji, tak jak na pełnych danych); mediana ilorazu = średnia z mediant okien (przybliżenie).
Użycie: uv run python reports/etap2/g5_predkosci_d23/c7b_walidacja_raport.py"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use("dark_background")

D = "reports/etap2/g5_predkosci_d23/r7b/"
T = {t: pd.read_csv(f"{D}walidacja_{t}_tomtom.csv") for t in ("r6", "r7b")}
base = lambda g: g.split("_trasa")[0]
rows = []
for t, df in T.items():
    d = df[df.porownanie == "okno_vs_hist"].copy()
    d["g"] = d.grupa.map(base)
    d = d[d.g != "wszystkie"].copy() if False else d
    for z, dz in d.groupby("zestaw"):
        # grupy podrzędne bez „wszystkie” i bez „trasa>=70%”: tylko rozłączne kind (+ podgrupa <70%)
        parts = dz[~dz.grupa.isin(["wszystkie", "trasa>=70%"])].copy()
        parts["G"] = parts.grupa.map(base)
        groups = {g: p for g, p in parts.groupby("G")}
        groups["WSZYSTKIE"] = parts
        groups["D23 A-F"] = parts[parts.G.str.startswith("D23_")]
        for g, p in groups.items():
            w = p.n
            n = w.sum()
            rows.append(dict(model=t, zestaw=z, grupa=g, n_obs=int(n), n_tras=round(n / 3, 1),
                             mediana_model_do_dost=(p.mediana_model_do_dost * w).sum() / n,
                             MAPE_pct=(p.MAPE_pct * w).sum() / n, RMSPE_pct=np.sqrt((p.RMSPE_pct ** 2 * w).sum() / n),
                             MAE_s=(p.MAE_s * w).sum() / n, RMSE_s=np.sqrt((p.RMSE_s ** 2 * w).sum() / n),
                             pRMSE_pct=np.sqrt((p.RMSE_s ** 2 * w).sum() / n) / ((p.srednia_dost_s * w).sum() / n) * 100,
                             TAG_pct=(p.TAG_15pct_lub_1min_pct * w).sum() / n))
R = pd.DataFrame(rows)
R.round(2).to_csv(D + "walidacja_r6_vs_r7b_grupy.csv", index=False)
pd.set_option("display.width", 250)
for z in ("walidacja", "analiza"):
    a = R[(R.zestaw == z) & (R.model == "r6")].set_index("grupa"); b = R[(R.zestaw == z) & (R.model == "r7b")].set_index("grupa")
    out = pd.concat({"R6": a, "R7b": b}, axis=1)
    print("=====", z); print(out.loc[sorted(a.index), [("R6", "n_tras"), ("R6", "mediana_model_do_dost"), ("R7b", "mediana_model_do_dost"), ("R6", "MAPE_pct"), ("R7b", "MAPE_pct"),
          ("R6", "RMSPE_pct"), ("R7b", "RMSPE_pct"), ("R6", "pRMSE_pct"), ("R7b", "pRMSE_pct"), ("R6", "MAE_s"), ("R7b", "MAE_s"), ("R6", "RMSE_s"), ("R7b", "RMSE_s"),
          ("R6", "TAG_pct"), ("R7b", "TAG_pct")]].round(2).to_string())
# swobodny i segmenty
for por in ("swobodny_model", "segment_freeflow"):
    for t, df in T.items():
        d = df[(df.porownanie == por) & df.grupa.isin(["wszystkie"])]
        print(por, t, d[["zestaw", "n", "mediana_model_do_dost", "MAPE_pct"]].round(3).to_string(index=False).replace("\n", " | "))
s = pd.concat({t: df[df.porownanie == "segment_freeflow"].set_index(["zestaw", "grupa"])[["n", "mediana_model_do_dost", "MAPE_pct", "MAE_kmh"]] for t, df in T.items()}, axis=1)
print(s.round(2).to_string()); s.round(3).to_csv(D + "walidacja_segmenty_r6_vs_r7b.csv")
# wykres: MAPE i TAG per grupa, walidacja i analiza
fig, ax = plt.subplots(1, 2, figsize=(14, 5))
gs = [g for g in sorted(R.grupa.unique()) if g.startswith("D23_") or g in ("D23 A-F", "WSZYSTKIE")]
for k, (col, ttl) in enumerate((("MAPE_pct", "MAPE czasu trasy [%] (3 okna łącznie)"), ("TAG_pct", "Trasy w kryterium TAG (15% lub 1 min) [%]"))):
    for i, (t, z, c) in enumerate((("r6", "analiza", "#0288d1"), ("r7b", "analiza", "#4fc3f7"), ("r6", "walidacja", "#f57c00"), ("r7b", "walidacja", "#ffb74d"))):
        v = R[(R.model == t) & (R.zestaw == z)].set_index("grupa").reindex(gs)[col]
        b = ax[k].bar(np.arange(len(gs)) + (i - 1.5) * 0.2, v, 0.2, color=c, label=f"{t.upper()} {z}")
    ax[k].set_xticks(range(len(gs)), [g.replace("D23_", "") for g in gs], rotation=0); ax[k].set_title(ttl, fontsize=10); ax[k].legend(fontsize=7)
ax[1].axhline(85, color="w", ls="--", lw=0.8); ax[1].set_ylim(0, 105)
fig.suptitle("D23 krok 5: walidacja TomTom historic, R6 vs R7b (agregaty; małe n w grupach, patrz tabela)", fontsize=10)
fig.tight_layout(); fig.savefig(D + "walidacja_r6_vs_r7b.png", dpi=130)
