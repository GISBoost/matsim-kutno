"""D34: cele wypraw bdot (R9.3) vs osm (errand_dest=osm), plany 25% p0. Wejście: output/r93o/{bdot,osm}_p0_errands.csv."""
import json, sys
import numpy as np, pandas as pd, matplotlib.pyplot as plt
D = "reports/etap3/g_zakupy/cel_osm"
sh = pd.read_csv("scenarios/kutno/osm/shops.csv")
cx, cy = sh.x.median(), sh.y.median()  # centrum = mediana sklepów OSM (ul. Królewska)
E = {v: pd.read_csv(f"output/r93o/{v}_p0_errands.csv") for v in ("bdot", "osm")}
same = (E["bdot"][["person", "home_x", "home_y", "start_s"]] == E["osm"][["person", "home_x", "home_y", "start_s"]]).all().all()
out = {"te_same_osoby_domy_godziny": bool(same)}
for v, e in E.items():
    e["d_km"] = np.hypot(e.dst_x - e.home_x, e.dst_y - e.home_y) / 1000
    e["c_km"] = np.hypot(e.dst_x - cx, e.dst_y - cy) / 1000
    e["typ"] = e.person.str[1]
    r = {}
    for t, g in e.groupby("typ"):
        top = g.groupby(["dst_x", "dst_y"]).size().sort_values(ascending=False)
        r[t] = dict(n=len(g), cele=int(len(top)), top1_pct=round(100 * top.iloc[0] / len(g), 1), top5_pct=round(100 * top.head(5).sum() / len(g), 1),
                    dom_cel_med_km=round(g.d_km.median(), 2), dom_cel_lt1km_pct=round(100 * (g.d_km < 1).mean(), 1),
                    centrum_med_km=round(g.c_km.median(), 2), centrum_gt2km_pct=round(100 * (g.c_km > 2).mean(), 1))
    r["wszystkie"] = dict(n=len(e), dom_cel_med_km=round(e.d_km.median(), 2), dom_cel_lt1km_pct=round(100 * (e.d_km < 1).mean(), 1),
                          centrum_med_km=round(e.c_km.median(), 2), centrum_lt05km_pct=round(100 * (e.c_km < 0.5).mean(), 1))
    r["top_cele_s"] = e[e.typ == "s"].src.value_counts().head(5).to_dict()
    r["top_cele_c"] = e[e.typ == "c"].src.value_counts().head(5).to_dict()
    out[v] = r
json.dump(out, open(f"{D}/cel_osm.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
plt.style.use("dark_background")
fig, ax = plt.subplots(1, 2, figsize=(12, 4.8))
b = np.arange(0, 6.01, 0.25)
for v, col in (("bdot", "#fdae61"), ("osm", "#00e5ff")):
    ax[0].hist(E[v].d_km, bins=b, histtype="step", lw=2, color=col, label=f"{v} (mediana {E[v].d_km.median():.2f} km)")
    ax[1].hist(E[v].c_km, bins=b, histtype="step", lw=2, color=col, label=f"{v} (mediana {E[v].c_km.median():.2f} km)")
ax[0].set(title="Odległość dom – cel wyprawy", xlabel="km (w linii prostej)", ylabel="liczba wypraw (próbka 25%)")
ax[1].set(title="Odległość celu od centrum (ul. Królewska)", xlabel="km (w linii prostej)", ylabel="liczba wypraw (próbka 25%)")
for a in ax: a.legend()
fig.suptitle("Cele zakupów i usług: BDOT (baza R9.3) vs sklepy OSM (D34), plany 25% p0")
fig.tight_layout(); fig.savefig(f"{D}/cel_osm.png", dpi=120)
