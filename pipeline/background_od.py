"""D19/K2-2: macierz O-D ruchu tła (pojazdy lekkie, doba, 100%) estymowana z liczników GPR 2025.

Użycie: uv run python -W ignore pipeline/background_od.py <tau_min> <out_tag> <model_output_dir> [<output_dir> ...]   (seedy runu bez tła, np. R1)
Strefy: wjazdy (początek) i wyjazdy (koniec) na granicy sieci (`scenarios/kutno/demand/border_links.csv`, z plans.py) oraz
gminy powiatu kutnowskiego (punkt = węzeł najbliższy środkowi ciężkości powierzchni budynków gminy).
Liczniki (cel): GPR SDRDR (DW: SDRR) × udział lekkich × kierunek (jak g5_baseline.py) MINUS natężenie modelu bez tła.
Do dopasowania odcinki poza miastem i Sklęczkowska 91869; 91124 i 91866 zostają do walidacji poza próbą (D19/K4, W2).
Metoda: trasy swobodne (length/freespeed), pary O-D, których trasa przechodzi przez co najmniej jeden licznik dopasowania,
macierz a priori grawitacyjna T0_ij = w_o · w_d · exp(−t_ij / tau), potem mnożnikowa korekta:
T_ij *= exp(średnia log(cel_l / przypisane_l) po licznikach na trasie).
w strefy-gminy = powierzchnia obrysów budynków gminy / średnia; w wjazdu/wyjazdu = 1.
ZAŁOŻENIE: postać a priori i tau (brak danych o O-D tła); tau podawane jako wariant (15/30/60 min), nie dobierane pod miasto.
Płaska macierz (tau = inf) dała 2× za dużo na odcinkach miejskich. Pary bez licznika na trasie = 0 (tło tylko tam, gdzie zmierzone).
Wyjście: scenarios/kutno/demand/background_od_<tag>.csv (o_kind, o, d_kind, d, tt_min, trips_day), reports/g5_kalibracja/k2_od_<tag>.{json,png}.
"""
import gzip
import json
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib
import networkx as nx
import numpy as np
import pandas as pd
import tomllib
from lxml import etree

matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use("dark_background")  # ciemny motyw (prośba użytkownika)

CITY = [91124, 91866]  # D19/K4, W2: walidacja poza próbą (Sklęczkowska 91869 w dopasowaniu)
TAU, TAG = float(sys.argv[1]), sys.argv[2]
BORDER_W = TAG.endswith("_cap")  # wariant: waga wjazdu/wyjazdu = capacity linku / średnia (A1 >> DW)
runs = [Path(a) for a in sys.argv[3:]]
P = tomllib.loads(Path("config/kutno.toml").read_text(encoding="utf-8"))
POWIAT = P["area"]["teryt_powiat"]

# --- sieć ---------------------------------------------------------------------------------------------
nodes, G, ltype, lnodes, lcap = {}, nx.DiGraph(), {}, {}, {}
with gzip.open("scenarios/kutno/network.xml.gz", "rb") as f:
    for _, el in etree.iterparse(f, tag=("node", "link")):
        if el.tag == "node":
            nodes[el.get("id")] = (float(el.get("x")), float(el.get("y")))
        else:
            a, b, lid = el.get("from"), el.get("to"), el.get("id")
            t = float(el.get("length")) / float(el.get("freespeed"))
            ltype[lid] = {x.get("name"): x.text for x in el.iter("attribute")}.get("type")
            lnodes[lid] = (a, b)
            lcap[lid] = float(el.get("capacity"))
            if not G.has_edge(a, b) or G[a][b]["t"] > t:
                G.add_edge(a, b, t=t, link=lid)
        el.clear()

# --- strefy ---------------------------------------------------------------------------------------------
bl = pd.read_csv("scenarios/kutno/demand/border_links.csv")
zones = []  # (kind, id, node_start, node_end, first_link, last_link, x, y)
for r in bl.itertuples():
    a, b = lnodes[r.link]
    if r.kind == "entry":   # tło zaczyna się na linku wjazdowym (aktywność na jego końcu)
        zones.append(("entry", r.link, b, None, r.link, None, r.x, r.y))
    else:                   # i kończy na linku wyjazdowym
        zones.append(("exit", r.link, None, a, None, r.link, r.x, r.y))
rej = gpd.read_file("data/raw/brec/rej_pl/SU_BREC_2021_REJ.shp", columns=["GMINA"])
gm = rej[rej.GMINA.str.startswith(POWIAT)].dissolve(by="GMINA").geometry
bld = gpd.read_file("scenarios/kutno/osm/features.gpkg", layer="buildings")
bld["pt"], bld["a"] = bld.geometry.representative_point(), bld.geometry.area
snap_nodes = {n for l, (a, b) in lnodes.items() if ltype[l] not in P["plans"]["snap_exclude_types"] for n in (a, b)}
sn = np.array(sorted(snap_nodes))
sxy = np.array([nodes[n] for n in sn])
for code, geom in gm.items():
    inb = bld[bld.pt.within(geom)]
    x, y = (np.average(inb.pt.x, weights=inb.a), np.average(inb.pt.y, weights=inb.a)) if len(inb) else geom.centroid.coords[0]
    n = sn[np.hypot(sxy[:, 0] - x, sxy[:, 1] - y).argmin()]
    zones.append(("gmina", code, n, n, None, None, x, y, inb.a.sum()))
Z = pd.DataFrame([z if len(z) == 9 else (*z, np.nan) for z in zones], columns=["kind", "id", "n_start", "n_end", "first", "last", "x", "y", "w"])
Z["w"] = (Z.w / Z.w.mean()).fillna(1.0)
if BORDER_W:
    b = Z.kind != "gmina"
    cap = Z[b].id.map(lcap)  # id strefy granicznej = link wjazdu/wyjazdu
    Z.loc[b, "w"] = cap / cap.mean()
O, D = Z[Z.kind != "exit"].reset_index(drop=True), Z[Z.kind != "entry"].reset_index(drop=True)

# --- liczniki --------------------------------------------------------------------------------------------
g = pd.read_csv("reports/g5_walidacja/gpr_linki.csv", dtype={"link": str})
g["gpr"] = g.sdrdr.where(g.sdrdr.notna(), g.sdr) * g.lekkie_osob / g.sdr * g.udzial_kier
vol = []
for d in runs:
    c = etree.parse(str(d / "output_config.xml"))
    s = float(c.find(".//module[@name='qsim']/param[@name='flowCapacityFactor']").get("value"))
    l = pd.read_csv(d / "output_links.csv.zst", sep=";", dtype={"link": str}).set_index("link")
    vol.append(g.link.map(l.vol_car).fillna(0) / s)
g["model"] = pd.concat(vol, axis=1).mean(axis=1)
g["target"] = (g.gpr - g.model).clip(lower=0)
g["fit"] = ~g.nr.isin(CITY)
cnt = {r.link: i for i, r in g.iterrows()}

# --- trasy i macierz incydencji -----------------------------------------------------------------------------
pairs, inc = [], []  # inc: lista indeksów liczników (wiersze g) na trasie pary
for oi, o in O.iterrows():
    dist, path = nx.single_source_dijkstra(G, o.n_start, weight="t")
    for di, d in D.iterrows():
        if o.kind == "gmina" and d.kind == "gmina" and o.id == d.id:
            continue
        if np.hypot(o.x - d.x, o.y - d.y) < 1500:  # zawracanie na tej samej granicy / ta sama strefa
            continue
        if d.n_end not in path:
            continue
        p = path[d.n_end]
        links = ([o["first"]] if o["first"] else []) + [G[a][b]["link"] for a, b in zip(p, p[1:])] + ([d["last"]] if d["last"] else [])
        hits = [cnt[l] for l in links if l in cnt]
        pairs.append((oi, di, dist[d.n_end] / 60, hits))
F = [p for p in pairs if any(g.fit[h] for h in p[3])]
T = np.array([O.w[p[0]] * D.w[p[1]] * np.exp(-p[2] / TAU) for p in F])
fit_idx = g.index[g.fit].to_numpy()
for it in range(300):
    assigned = np.zeros(len(g))
    for t, p in zip(T, F):
        assigned[p[3]] += t
    ratio = np.clip(np.where(assigned > 0, np.maximum(g.target, 1) / np.maximum(assigned, 1e-9), 1), 0.05, 20)
    for k, p in enumerate(F):
        h = [x for x in p[3] if g.fit[x]]
        T[k] *= np.exp(np.mean(np.log(ratio[h])))
assigned = np.zeros(len(g))
for t, p in zip(T, F):
    assigned[p[3]] += t
g["background"] = assigned
g["model_plus_bg"] = g.model + g.background

od = pd.DataFrame([dict(o_kind=O.kind[p[0]], o=O.id[p[0]], d_kind=D.kind[p[1]], d=D.id[p[1]], tt_min=round(p[2], 1),
                        trips_day=round(t, 2)) for t, p in zip(T, F)])
od = od[od.trips_day >= 0.5].sort_values("trips_day", ascending=False)
od.to_csv(f"scenarios/kutno/demand/background_od_{TAG}.csv", index=False, lineterminator="\n")

sec = g.groupby("nr", sort=False).agg(droga=("droga", "first"), fit=("fit", "first"), gpr=("gpr", "sum"), model=("model", "sum"),
                                      background=("background", "sum")).reset_index()
sec["model_plus_bg"] = sec.model + sec.background
sec["ratio_before"], sec["ratio_after"] = sec.model / sec.gpr, sec.model_plus_bg / sec.gpr
geh = lambda m, c: np.sqrt(2 * (m - c) ** 2 / (m + c)) / np.sqrt(24)  # GEH godzinowy ze średniej godziny doby (orientacyjnie)
sec["geh_hourly_mean"] = geh(sec.model_plus_bg, sec.gpr)
kz = lambda k: od[(od.o_kind == k) | (od.d_kind == k)].trips_day.sum()
rep = {"runs": [str(d) for d in runs], "tau_min": TAU, "zones": Z.kind.value_counts().to_dict(), "od_pairs_with_count": len(F),
       "od_pairs_kept": len(od), "trips_day_100pct": round(float(od.trips_day.sum())),
       "trips_by_type": {"tranzyt_wjazd_wyjazd": round(float(od[(od.o_kind == "entry") & (od.d_kind == "exit")].trips_day.sum())),
                         "granica_gmina": round(float(od[(od.o_kind == "entry") & (od.d_kind == "gmina")].trips_day.sum()
                                                      + od[(od.o_kind == "gmina") & (od.d_kind == "exit")].trips_day.sum())),
                         "gmina_gmina": round(float(od[(od.o_kind == "gmina") & (od.d_kind == "gmina")].trips_day.sum()))},
       "fit_links_rmse": round(float(np.sqrt(((g.model_plus_bg - g.gpr)[g.fit] ** 2).mean())), 1),
       "sections": sec.round(3).to_dict(orient="records"),
       "top_od": od.head(15).to_dict(orient="records"),
       "top_od_via_city": {str(nr): sorted([dict(o=O.id[p[0]], d=D.id[p[1]], trips=round(float(t)),
                                                 fit_counts=[int(g.nr[h]) for h in p[3] if g.fit[h]])
                                            for t, p in zip(T, F) if any(g.nr[h] == nr for h in p[3])],
                                           key=lambda r: -r["trips"])[:8] for nr in CITY}}
json.dump(rep, open(f"reports/g5_kalibracja/k2_od_{TAG}.json", "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False)

fig, axs = plt.subplots(1, 2, figsize=(15, 6.5), gridspec_kw={"width_ratios": [1.3, 1]})
s = sec.sort_values("gpr")
y = np.arange(len(s))
ax = axs[0]
ax.barh(y + 0.27, s.gpr, 0.27, color="#6c757d", label="GPR (lekkie, SDRDR)")
ax.barh(y, s.model, 0.27, color="#2e86ab", label="model bez tła (R1)")
ax.barh(y - 0.27, s.model_plus_bg, 0.27, color="#f18f01", label="model + tło (trasy swobodne)")
ax.set_yticks(y); ax.set_yticklabels([f"{r.droga} {r.nr}{'  [walidacja]' if not r.fit else ''}" for r in s.itertuples()], fontsize=8)
ax.set_xlabel("poj./dobę, oba kierunki"); ax.legend(fontsize=8, loc="lower right")
ax.set_title(f"K2: dopasowanie tła do GPR, tau = {TAU:g} min (miasto poza próbą)", fontsize=10)
ax = axs[1]
for r in od.head(60).itertuples():
    o, d = O[O.id == r.o].iloc[0], D[D.id == r.d].iloc[0]
    ax.plot([o.x, d.x], [o.y, d.y], color="#f18f01", alpha=0.25, lw=0.3 + r.trips_day / od.trips_day.max() * 6)
ax.scatter(Z[Z.kind == "gmina"].x, Z[Z.kind == "gmina"].y, s=20, color="#3ddc97", zorder=5, label="gminy powiatu")
ax.scatter(Z[Z.kind != "gmina"].x, Z[Z.kind != "gmina"].y, s=8, color="#d1495b", zorder=5, label="wjazdy / wyjazdy")
ax.set_aspect("equal"); ax.set_axis_off(); ax.legend(fontsize=8)
ax.set_title(f"60 największych relacji tła ({rep['trips_day_100pct']} podróży/dobę w 100%)", fontsize=10)
fig.tight_layout(); fig.savefig(f"reports/g5_kalibracja/k2_od_{TAG}.png", dpi=120)
print(json.dumps({k: v for k, v in rep.items() if k not in ("sections", "top_od")}, ensure_ascii=False, indent=1))
print(sec[["nr", "droga", "fit", "gpr", "model", "background", "model_plus_bg", "ratio_before", "ratio_after"]].round(2).to_string())
