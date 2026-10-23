"""G3 (D28): oczekiwany rozkład domów rezydentów gm. Kutno vs siatka GUS NSP 2021 250 m, OSM (R7b) vs BDOT10k (R9).
Uruchom: uv run python -W ignore reports/etap3/g3_domy/g3_zgodnosc.py   -> g3_zgodnosc.json, g3_zgodnosc.csv, g3_zgodnosc_mapa.png
Oczekiwanie bez losowania: komórka dostaje sum_o N_o * w_b / W_o po budynkach b z punktem reprezentatywnym w obwodzie o
(N_o = pracujący obwodu z rejestru, work_in_kutno_reg; w_b wg wariantu), jak research docs/research/G3_domy.md §4.
Miara: TV = 0,5 * sum |p_model - p_GUS| po komórkach 250 m z centroidem w gm. Kutno (masa w złej komórce, pp).
Pule budynków budowane tak jak w pipeline/plans.py (kopia reguł OSM; BDOT wg config/kutno.toml).
"""
import json
import tomllib
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyogrio

plt.style.use("dark_background")
H = Path("reports/etap3/g3_domy")
cfg = tomllib.loads(Path("config/kutno.toml").read_text(encoding="utf-8"))
P = cfg["plans"]
gmina_kutno = gpd.read_file("scenarios/kutno/area/gmina.geojson").geometry.iloc[0]
g10 = pyogrio.read_dataframe("data/raw/brec/gml/AreaStatisticalUnit_10.xml",
                             columns=["LocationString", "thematicId|ThematicIdentifier|identifier"]).to_crs("EPSG:2180")
g10["uid"] = g10["thematicId|ThematicIdentifier|identifier"].astype(int)
obw = g10[(g10.LocationString.astype(str).str.zfill(7) == "1002011") & (g10.uid > 999_999)].set_index("uid").geometry
N = pd.read_csv("scenarios/kutno/demand/workers_by_obwod.csv").set_index("obwod_id")["work_in_kutno_reg"]

# --- pule domów -------------------------------------------------------------------------------------------
b = gpd.read_file("scenarios/kutno/osm/features.gpkg", layer="buildings")
lu = gpd.read_file("scenarios/kutno/osm/features.gpkg", layer="landuse")
b["pt"] = b.geometry.representative_point()
b["a"] = b.geometry.area
pts = b.set_geometry("pt")
in_lu = lambda kinds: pts.index.isin(gpd.sjoin(pts[["pt"]], lu[lu.landuse.isin(kinds)][["geometry"]], predicate="within").index)
b["res"] = b.building.isin(P["residential_buildings"]) | ((b.building == "yes") & in_lu(["residential"])
                                                           & b.amenity.isna() & b.shop.isna() & b.office.isna())
b["work_any"] = (b.building.isin(P["work_buildings"]) | b.amenity.notna() | b.shop.notna() | b.office.notna()
                 | ((b.building == "yes") & in_lu(P["work_landuse"])))
b.loc[b.work_any & b.pt.within(gmina_kutno), "res"] = False
osm = b[b.res].set_geometry("pt")[["a", "pt"]].rename(columns={"a": "w"})

bd = pyogrio.read_dataframe(P["home_bdot"], encoding="utf-8", columns=["LOKALNYID", "KATEGORIAISTNIENIA", "PRZEWAZAJACAFUNKCJABUDYNKU", "LICZBAKONDYGNACJI"])
bd = bd[(bd.KATEGORIAISTNIENIA == "eksploatowany") & bd.PRZEWAZAJACAFUNKCJABUDYNKU.isin(P["home_bdot_functions"])].copy()
bd["pt"] = bd.geometry.representative_point()
bd["a"] = bd.geometry.area
bd["floors"] = bd.LICZBAKONDYGNACJI.fillna(1).clip(lower=1)
pools = {"OSM (R7b)": osm,
         "BDOT obrys": bd.assign(w=bd.a).set_geometry("pt")[["w", "pt"]],
         "BDOT obrys × kondygnacje (R9)": bd.assign(w=bd.a * bd.floors).set_geometry("pt")[["w", "pt"]]}

# --- siatka GUS 250 m w gm. Kutno ---------------------------------------------------------------------------
bb = tuple(gpd.GeoSeries([gmina_kutno], crs="EPSG:2180").to_crs(3035).buffer(1000).total_bounds)
g = pyogrio.read_dataframe("data/raw/g3/gus_grid/g250/NSP2021_TOT_grid250m.shp", bbox=bb).set_crs(3035, allow_override=True).to_crs(2180)
g["TOT"] = g.TOT.astype(float)
g = g[g.geometry.centroid.within(gmina_kutno)].reset_index(drop=True)
gus = g.TOT / g.TOT.sum()

rows, cells = [], g[["geometry", "TOT"]].copy()
for name, pool in pools.items():
    exp = pd.Series(0.0, index=g.index)
    for o, poly in obw.items():
        if o not in N.index or N[o] <= 0:
            continue  # 6509213 tylko w geometrii (CLAUDE.md, gotcha BREC)
        c = pool[pool.pt.within(poly)]
        if not len(c) and "BDOT" in name:
            d = pool.pt.distance(poly)
            c = pool[d == d.min()] if d.min() <= P["home_nearest_max_m"] else c
        if not len(c):
            continue  # obwód bez kandydata: losowy punkt (poza porównaniem)
        j = gpd.sjoin(c[["w", "pt"]].set_geometry("pt"), g[["geometry"]], predicate="within", how="inner")
        exp = exp.add(j.groupby("index_right").w.sum() / c.w.sum() * N[o], fill_value=0)
    miss = N.sum() - exp.sum()  # masa w budynkach poza komórkami GUS albo w obwodach bez kandydata
    p = exp / exp.sum()
    cells[name] = exp
    rows.append(dict(wariant=name, pool_budynkow=int(len(pool)), TV_pp=round(float(0.5 * (p - gus).abs().sum() * 100), 2),
                     pearson=round(float(p.corr(gus)), 4), spearman=round(float(p.rank().corr(gus.rank())), 4),
                     masa_poza_siatka_proc=round(float(miss / N.sum() * 100), 2)))
res = pd.DataFrame(rows)
print(res.to_string(index=False))
res.to_csv(H / "g3_zgodnosc.csv", index=False)
json.dump({"komorek_GUS_gm_kutno": int(len(g)), "suma_GUS": float(g.TOT.sum()), "wyniki": rows}, open(H / "g3_zgodnosc.json", "w", encoding="utf-8"),
          indent=1, ensure_ascii=False)

cells["gus_p"] = gus
for n in list(pools)[::2]:
    cells["d_" + n] = (cells[n] / cells[n].sum() - gus) * g.TOT.sum()  # nadmiar (+) lub niedobór (-) mieszkańców
vm = float(np.percentile(np.abs(cells[["d_" + n for n in list(pools)[::2]]].to_numpy()), 98))
fig, ax = plt.subplots(1, 2, figsize=(14, 7))
for a_, n in zip(ax, list(pools)[::2]):
    cells.plot(column="d_" + n, cmap="RdBu_r", vmin=-vm, vmax=vm, ax=a_, legend=True, legend_kwds=dict(shrink=0.7))
    a_.set_title(f"{n}: oczekiwani rezydenci − GUS [os./250 m]\nTV {res.set_index('wariant').TV_pp[n]:.1f} pp", fontsize=11)
    a_.set_aspect("equal"); a_.axis("off")
    gpd.GeoSeries([gmina_kutno], crs=2180).boundary.plot(ax=a_, color="white", lw=0.5)
fig.suptitle("G3 (D28): nadmiar (czerwony) i niedobór (niebieski) rezydentów względem siatki GUS 250 m")
fig.tight_layout()
fig.savefig(H / "g3_zgodnosc_mapa.png", dpi=130)
