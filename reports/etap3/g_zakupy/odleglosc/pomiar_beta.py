"""Pomiar wariantów odległości celu wypraw (A/B/C z docs/research/G_odleglosc_celu.md) na planach R9.4, bez generowania nowych planów.

Użycie: uv run python -W ignore reports/etap3/g_zakupy/odleglosc/pomiar_beta.py
Dla każdej wyprawy z plans_g3r94_25pct_errands.csv (dom, typ c/s/u) liczy czas swobodny autem dom → każdy cel z puli typu
(sieć scenarios/kutno/network.xml.gz, length/freespeed, jak plans.py snap_mode=route) i rozkład celu p_j ∝ W_j · exp(−β · t_ij).
Wynik to wartości oczekiwane rozkładu (nie jedno losowanie): udział t ≤ 5 / ≤ 15 min, średni t, odległość dom–cel w linii prostej,
udział < 1 km. β = 0 to obecny generator (R9.4); kontrola: wartość oczekiwana vs faktyczne losowanie w planach.
Wyjście: pomiar_beta.json, pomiar_beta.png obok skryptu.
"""
import gzip
import json
import sys
import tomllib
from pathlib import Path

import geopandas as gpd
import matplotlib
import numpy as np
import pandas as pd
import pyogrio
from lxml import etree
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from shapely import STRtree
from shapely.geometry import LineString, Point

sys.path.insert(0, "pipeline")
import errands  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
plt.style.use("dark_background")

HERE = Path(__file__).parent
BETAS = {"R9.4 (β=0)": 0.0, "C 0,033": 0.033, "A 0,08": 0.08, "B 0,14": 0.14}
cfg = tomllib.loads(Path("config/kutno.toml").read_text(encoding="utf-8"))
P = cfg["plans"]
er = pd.read_csv("scenarios/kutno/plans_g3r94_25pct_errands.csv")
er["code"] = er.person.str[1]

# sieć: graf czasu swobodnego i pula linków przypięcia (bez autostrad, ekspresówek, łącznic)
nodes, lk, snap = {}, {}, []
for _, el in etree.iterparse(gzip.open("scenarios/kutno/network.xml.gz"), tag=("node", "link")):
    if el.tag == "node":
        nodes[el.get("id")] = (float(el.get("x")), float(el.get("y")))
    elif "car" in el.get("modes"):
        lk[el.get("id")] = (el.get("from"), el.get("to"), float(el.get("length")), float(el.get("freespeed")))
        t = el.find("attributes/attribute[@name='type']")
        if (t.text if t is not None else "") not in P["snap_exclude_types"]:
            snap.append(el.get("id"))
    el.clear()
nid = {n: i for i, n in enumerate(nodes)}
best = {}
for a, b, ln, fs in lk.values():
    best[(nid[a], nid[b])] = min(best.get((nid[a], nid[b]), 1e18), ln / fs)
gr = csr_matrix((list(best.values()), ([k[0] for k in best], [k[1] for k in best])), shape=(len(nid), len(nid)))
tree = STRtree([LineString([nodes[lk[l][0]], nodes[lk[l][1]]]) for l in snap])
nearest = lambda xs, ys: [snap[i] for i in tree.query_nearest([Point(x, y) for x, y in zip(xs, ys)], all_matches=False)[1]]

# pule celów jak errands.draw (ten sam kod puli OSM)
gm = gpd.read_file("scenarios/kutno/area/gmina.geojson").geometry.iloc[0]
bd = pyogrio.read_dataframe(P["home_bdot"], encoding="utf-8", columns=["KATEGORIAISTNIENIA", "PRZEWAZAJACAFUNKCJABUDYNKU"])
bd = bd[bd.KATEGORIAISTNIENIA == "eksploatowany"].copy()
bd["pt"] = bd.geometry.representative_point()
bd = bd[bd.pt.within(gm)].copy()
bd["area_m2"] = bd.geometry.area
pools = {}
for code, (_, _, funcs) in errands.TYPES.items():
    pool = errands.osm_pool(code, bd, P) if code in "cs" else bd[bd.PRZEWAZAJACAFUNKCJABUDYNKU.isin(funcs)].reset_index(drop=True)
    pool = pool.assign(x=[p.x for p in pool.pt], y=[p.y for p in pool.pt], w=pool.area_m2 / pool.area_m2.sum())
    pool["link"] = nearest(pool.x, pool.y)
    pools[code] = pool

# czas swobodny [min]: od końca linku domu do początku linku celu + przejazd linku celu (jak plans.cost)
src = sorted({nid[lk[l][1]] for l in er.home_link})
D = dijkstra(gr, directed=True, indices=src)
row = {s: i for i, s in enumerate(src)}

res = {name: [] for name in BETAS}
TB, KB = np.arange(0, 21), np.arange(0, 10.5, 0.5)
H = {name: np.zeros(len(TB) - 1) for name in BETAS}
HK = {name: np.zeros(len(KB) - 1) for name in BETAS}
for r in er.itertuples():
    pool = pools[r.code]
    d = D[row[nid[lk[r.home_link][1]]]]
    t = (d[[nid[lk[l][0]] for l in pool.link]] + np.array([lk[l][2] / lk[l][3] for l in pool.link])) / 60
    km = np.hypot(pool.x - r.home_x, pool.y - r.home_y).to_numpy() / 1000
    ok = np.isfinite(t)
    for name, b in BETAS.items():
        p = np.where(ok, pool.w.to_numpy() * np.exp(-b * np.where(ok, t, 0)), 0)
        p /= p.sum()
        H[name] += np.histogram(np.where(ok, t, 99), bins=TB, weights=p)[0]
        HK[name] += np.histogram(km, bins=KB, weights=p)[0]
        res[name].append([p @ np.where(ok, t, 0), p[t <= 5].sum(), p[t <= 15].sum(), p @ km, p[km < 1].sum(), p[km > 3].sum()])
cols = ["t_min", "t_le5", "t_le15", "km", "km_lt1", "km_gt3"]
summary = {name: dict(zip(cols, np.mean(v, axis=0).round(4).tolist())) for name, v in res.items()}
# kontrola β=0: faktyczne losowanie w planach (linia prosta dom–cel)
km_plan = np.hypot(er.dst_x - er.home_x, er.dst_y - er.home_y) / 1000
summary["plany R9.4 (losowanie)"] = {"km": round(float(km_plan.mean()), 4), "km_lt1": round(float((km_plan < 1).mean()), 4),
                                     "km_gt3": round(float((km_plan > 3).mean()), 4)}
ref = {"GBR 2022 dom–inne (wszystkie tryby, Gdańsk)": {"t_le5": 0.109, "t_le15": 0.625, "t_min": 18}}
json.dump({"wypraw": len(er), "pule": {k: len(v) for k, v in pools.items()}, "warianty": summary, "kontrola": ref},
          open(HERE / "pomiar_beta.json", "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False)
print(pd.DataFrame(summary).T.to_string())

# wykres: rozkład czasu (wartość oczekiwana, koszyki 1 min) dla wariantów
fig, ax = plt.subplots(1, 2, figsize=(13, 5))
for (name, b), col in zip(BETAS.items(), ["#adb5bd", "#4cc9f0", "#f4a261", "#e76f51"]):
    h, hk = H[name], HK[name]
    s = summary[name]
    ax[0].step(TB[:-1], 100 * h / len(er), where="post", color=col, label=f"{name}: śr. {s['t_min']:.1f} min, ≤5 min {100*s['t_le5']:.0f}%")
    ax[1].step(KB[:-1], 100 * hk / len(er), where="post", color=col, label=f"{name}: śr. {s['km']:.2f} km, <1 km {100*s['km_lt1']:.0f}%")
ax[0].set_xlabel("czas swobodny autem dom → cel [min]"); ax[0].set_ylabel("% wypraw (koszyk 1 min)")
ax[1].set_xlabel("odległość dom–cel w linii prostej [km]"); ax[1].set_ylabel("% wypraw (koszyk 0,5 km)")
for a in ax:
    a.legend(fontsize=8)
fig.suptitle("Wyprawy zakupy i usługi R9.4 (25%, 711): rozkład celu przy różnych β (wartość oczekiwana)", fontsize=11)
fig.tight_layout(); fig.savefig(HERE / "pomiar_beta.png", dpi=120)
