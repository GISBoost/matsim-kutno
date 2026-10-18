"""Audyt G5 (K1, D9), krok 4: sygnały ostrzegawcze macierzy O-D tła. Uruchamiać po każdej estymacji (background_od.py).

Użycie: uv run python -W ignore pipeline/od_warnings.py <out_prefix> lcv=<macierz.csv> heavy=<macierz.csv> [heavy_ends=all|work]
Kod wyjścia 1, gdy którykolwiek próg jest przekroczony. Wyjście: <out_prefix>.json.
S1 gęstość podróży gminy: podróże tła z początkiem lub końciem w gminie / powierzchnia obrysów budynków gminy, względem tej samej
   miary dla gm. miejskiej Kutno. Kutno ma niską gęstość, bo jego ruch zewnętrzny to głównie modelowane dojazdy do pracy, więc
   gminy po K1 + I4 mają 0,4–7× Kutna. Fantom K1 w R4: 45× (lekkie) i 73× (ciężkie). Próg 10× (ZAŁOŻENIE: rząd wielkości ponad
   Kutno, łapie anomalie typu K1, nie zwykłe różnice gmin). Top 10 par z powierzchniami obu stref w JSON.
S2 udział km tła na drogach bez licznika GPR (tertiary, unclassified, residential, living_street, service): trasy swobodne
   (jak w estymacji, ciężkie 80 km/h) z punktu strefy (link graniczny albo węzeł najbliższy środkowi ciężkości budynków gminy).
   Liczniki są tylko na drogach krajowych i wojewódzkich, więc tło jeżdżące drogami lokalnymi nie ma pomiaru. Próg 35% km
   (ZAŁOŻENIE): R4 z fantomem K1 ma 40%, po K1 + I4 27–31%; pracujący w R1 mają 58% (dojazd od drzwi do drzwi), więc to sygnał
   słaby, rozstrzygają S1 i S4. Informacyjnie: udział km par jeżdżących głównie (> 50% km) drogami bez licznika.
S3 końce ciężkich w budynkach mieszkalnych (residential_buildings z kutno.toml) i gospodarczych (farm_auxiliary, outbuilding, garage,
   shed): oczekiwany udział z wag losowania w plans.py (heavy_ends=all: wszystkie budynki gminy wagą powierzchni; work: budynki
   pracy jak work_any w plans.py). Audyt D9 (R4): 19,2% i 31,4%. Próg: oba razem ≤ 25% (ZAŁOŻENIE: ciężarowe kończą głównie
   w zakładach, magazynach, handlu i usługach).
S4 pary między Dąbrowice 1002032, Krośniewice-miasto 1002044, Krośniewice-obszar wiejski 1002045 (fantom K1, po poprawce ~50).
   Próg 500 podróży/dobę na klasę (ZAŁOŻENIE: ok. 1% tła).
"""
import gzip
import json
import sys
import tomllib
from pathlib import Path

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
from lxml import etree
from shapely import STRtree
from shapely.geometry import Point

out = sys.argv[1]
OPT = dict(a.split("=", 1) for a in sys.argv[2:])
P = tomllib.loads(Path("config/kutno.toml").read_text(encoding="utf-8"))
PL = P["plans"]
HEAVY_ENDS = OPT.get("heavy_ends", PL.get("heavy_ends", "all"))
LOCAL = {"tertiary", "tertiary_link", "unclassified", "residential", "living_street", "service"}
FARM = {"farm_auxiliary", "outbuilding", "garage", "shed"}
TRIO = {"1002032", "1002044", "1002045"}
LIM = {"S1_density_vs_kutno": 10.0, "S2_local_km_share": 0.35, "S3_heavy_res_farm_share": 0.25, "S4_trio_trips": 500}

rej = gpd.read_file("data/raw/brec/rej_pl/SU_BREC_2021_REJ.shp", columns=["GMINA"])
gm = rej[rej.GMINA.str.startswith(P["area"]["teryt_powiat"])].dissolve(by="GMINA")
b = gpd.read_file("scenarios/kutno/osm/features.gpkg", layer="buildings")
lu = gpd.read_file("scenarios/kutno/osm/features.gpkg", layer="landuse")
b["a"] = b.geometry.area
pt = b.copy()
pt["geometry"] = b.geometry.representative_point()
in_work_lu = pt.index.isin(gpd.sjoin(pt[["geometry"]], lu[lu.landuse.isin(PL["work_landuse"])][["geometry"]], predicate="within").index)
b["work_any"] = (b.building.isin(PL["work_buildings"]) | b.amenity.notna() | b.shop.notna() | b.office.notna()
                 | ((b.building == "yes") & in_work_lu))  # jak plans.py
b["cls"] = np.where(b.building.isin(PL["residential_buildings"]), "mieszkalne", np.where(b.building.isin(FARM), "gospodarcze", "inne"))
j = gpd.sjoin(pt[["geometry"]], gm.reset_index()[["GMINA", "geometry"]], predicate="within")
b["gmina"] = j.GMINA.reindex(b.index)
area = b.groupby("gmina").a.sum()

nodes, G, ltype = {}, {"lcv": nx.DiGraph(), "heavy": nx.DiGraph()}, {}
lnodes, llen = {}, {}
with gzip.open("scenarios/kutno/network.xml.gz", "rb") as f:
    for _, el in etree.iterparse(f, tag=("node", "link")):
        if el.tag == "node":
            nodes[el.get("id")] = (float(el.get("x")), float(el.get("y")))
        else:
            a_, b_, lid = el.get("from"), el.get("to"), el.get("id")
            L, v = float(el.get("length")), float(el.get("freespeed"))
            ltype[lid] = {x.get("name"): x.text for x in el.iter("attribute")}.get("type")
            lnodes[lid], llen[lid] = (a_, b_), L
            for c, vm in (("lcv", np.inf), ("heavy", 80 / 3.6)):
                t = L / min(v, vm)
                if not G[c].has_edge(a_, b_) or G[c][a_][b_]["t"] > t:
                    G[c].add_edge(a_, b_, t=t, link=lid)
        el.clear()
nid = list(nodes)
ntree = STRtree([Point(nodes[n]) for n in nid])
cent = {}
for code, k in b.dropna(subset=["gmina"]).groupby("gmina"):
    c = Point(np.average(k.geometry.centroid.x, weights=k.a), np.average(k.geometry.centroid.y, weights=k.a))
    cent[code] = nid[ntree.nearest(c)]


def point(kind, z, start):
    if kind == "gmina":
        return cent[z]
    return lnodes[z][1] if start else lnodes[z][0]


def check(cls, path):
    od = pd.read_csv(path, dtype={"o": str, "d": str})
    r = {"file": path, "trips_day": round(float(od.trips_day.sum()))}
    # S1
    g = pd.concat([od[od.o_kind == "gmina"][["o", "trips_day"]].rename(columns={"o": "z"}),
                   od[od.d_kind == "gmina"][["d", "trips_day"]].rename(columns={"d": "z"})]).groupby("z").trips_day.sum()
    dens = g / area.reindex(g.index) * 1000  # podróże/dobę na 1000 m² budynków
    kut = dens.get(P["area"]["teryt_gmina"], np.nan)
    r["S1_density_per_1000m2"] = dens.round(3).to_dict()
    r["S1_density_vs_kutno"] = round(float((dens / kut).max()), 2)
    r["S1_worst_gmina"] = str((dens / kut).idxmax())
    top = od.head(10).copy()
    top["area_o_tys_m2"] = [round(area.get(z, np.nan) / 1000) if k == "gmina" else None for k, z in zip(top.o_kind, top.o)]
    top["area_d_tys_m2"] = [round(area.get(z, np.nan) / 1000) if k == "gmina" else None for k, z in zip(top.d_kind, top.d)]
    r["top10"] = top.to_dict(orient="records")
    # S2
    km, kml, kmp = 0.0, 0.0, 0.0
    for o, grp in od.groupby(["o_kind", "o"]):
        s = point(o[0], o[1], True)
        dist, path_ = nx.single_source_dijkstra(G[cls], s, weight="t")
        for row in grp.itertuples():
            e = point(row.d_kind, row.d, False)
            if e not in path_:
                continue
            ls = [G[cls][u][v]["link"] for u, v in zip(path_[e], path_[e][1:])]
            if row.d_kind == "exit":
                ls.append(row.d)
            L = np.array([llen[l] for l in ls])
            loc = np.array([ltype[l] in LOCAL for l in ls], dtype=bool)
            km += row.trips_day * L.sum() / 1000
            kml += row.trips_day * L[loc].sum() / 1000
            if L.sum() and L[loc].sum() / L.sum() > 0.5:  # para jeździ głównie drogami bez licznika
                kmp += row.trips_day * L.sum() / 1000
    r["S2_km_day_100pct"], r["S2_local_km_share"] = round(km), round(kml / km, 3)
    r["S2_mostly_local_pairs_km_share"] = round(kmp / km, 3)
    # S3 (tylko ciężkie: oczekiwany udział końców wg wag losowania w plans.py)
    if cls == "heavy":
        cand = b[b.work_any] if HEAVY_ENDS == "work" else b
        sh = cand.groupby(["gmina", "cls"]).a.sum().unstack(fill_value=0)
        sh = sh.div(sh.sum(axis=1), axis=0)
        ends = pd.concat([od[od.o_kind == "gmina"][["o", "trips_day"]].rename(columns={"o": "z"}),
                          od[od.d_kind == "gmina"][["d", "trips_day"]].rename(columns={"d": "z"})]).groupby("z").trips_day.sum()
        w = (sh.reindex(ends.index).fillna(0).mul(ends, axis=0).sum() / ends.sum())
        r["S3_heavy_ends"] = HEAVY_ENDS
        r["S3_heavy_end_share"] = w.round(3).to_dict()
        r["S3_heavy_res_farm_share"] = round(float(w.get("mieszkalne", 0) + w.get("gospodarcze", 0)), 3)
    # S4
    r["S4_trio_trips"] = round(float(od[od.o.isin(TRIO) & od.d.isin(TRIO)].trips_day.sum()))
    r["flags"] = [k for k, lim in LIM.items() if k in r and r[k] > lim]
    return r


rep = {"limits": LIM, **{c: check(c, OPT[c]) for c in ("lcv", "heavy") if c in OPT}}
rep["ok"] = not any(rep[c]["flags"] for c in ("lcv", "heavy") if c in rep)
json.dump(rep, open(out + ".json", "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False, default=str)
for c in ("lcv", "heavy"):
    if c in rep:
        print(c, {k: v for k, v in rep[c].items() if k.startswith("S") and not k.startswith(("S1_density_per", "S3_heavy_end"))}, "flagi:", rep[c]["flags"])
print("ok" if rep["ok"] else "PRZEKROCZONE PROGI")
sys.exit(0 if rep["ok"] else 1)
