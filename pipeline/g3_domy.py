"""G3 (badanie, bez zmian modelu): BDOT10k vs OSM, wykluczenia jak w R5, siatki GUS NSP 2021 vs domy agentów.
Uruchom: uv run python -W ignore pipeline/g3_domy.py   -> reports/etap2/g3_domy/*.json|csv|png
"""
import json
import tomllib
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyogrio
def pearsonr(x, y):
    return (pd.Series(np.asarray(x)).corr(pd.Series(np.asarray(y))),)


def spearmanr(x, y):
    return (pd.Series(np.asarray(x)).rank().corr(pd.Series(np.asarray(y)).rank()),)

plt.style.use("dark_background")
OUT = Path("reports/etap2/g3_domy")
OUT.mkdir(parents=True, exist_ok=True)
RES = {}
cfg = tomllib.loads(Path("config/kutno.toml").read_text(encoding="utf-8"))
P = cfg["plans"]
# lista wykluczeń z R5: easy-R5/tools/realtime_delay_cities/dasymetric_pop.py (EXCL_BUILDINGS)
EXCL = set("""no garage garages carport shed outbuilding roof greenhouse greenhouse_horticulture construction industrial
warehouse retail commercial office manufacture transportation service hangar parking hospital school kindergarten university
college church chapel mosque synagogue temple cathedral civic public government train_station bridge bunker military stable
barn farm_auxiliary cowshed sty slurry_tank transformer_tower kiosk hut boathouse ruins collapsed abandoned tent grandstand
tribune stadium sports_hall sports_centre pavilion container trailer storage_tank silo digester gasometer water_tower
cooling_tower chimney supermarket kingdom_hall shrine toilets carriageway guardhouse gatehouse hotel motel hostel prison sauna""".split())

# --- geometrie ---------------------------------------------------------------------------------------
gmina_kutno = gpd.read_file("scenarios/kutno/area/gmina.geojson").geometry.iloc[0]
powiat = gpd.read_file("scenarios/kutno/area/powiat.geojson").geometry.union_all()
g10 = pyogrio.read_dataframe("data/raw/brec/gml/AreaStatisticalUnit_10.xml",
                             columns=["LocationString", "thematicId|ThematicIdentifier|identifier"]).to_crs("EPSG:2180")
g10["uid"] = g10["thematicId|ThematicIdentifier|identifier"].astype(int)
obwody = g10[(g10.LocationString.astype(str).str.zfill(7) == "1002011") & (g10.uid > 999_999)].set_index("uid").geometry
rej = gpd.read_file("data/raw/brec/rej_pl/SU_BREC_2021_REJ.shp", columns=["GMINA"])
gminy = rej.dissolve(by="GMINA").geometry
gminy = gminy[gminy.index.str.startswith("1002")]
gminy_gdf = gpd.GeoDataFrame({"gmina": gminy.index}, geometry=gminy.values)

# --- OSM: obecny model (kopia logiki plans.py) vs lista wykluczeń R5 -----------------------------------------
b = gpd.read_file("scenarios/kutno/osm/features.gpkg", layer="buildings")
lu = gpd.read_file("scenarios/kutno/osm/features.gpkg", layer="landuse")
b["pt"] = b.geometry.representative_point()
b["area_m2"] = b.geometry.area
pts = b.set_geometry("pt")


def in_landuse(kinds):
    return pts.index.isin(gpd.sjoin(pts[["pt"]], lu[lu.landuse.isin(kinds)][["geometry"]], predicate="within").index)


b["in_lu_res"] = in_landuse(["residential"])
b["cur"] = b.building.isin(P["residential_buildings"]) | ((b.building == "yes") & b.in_lu_res
                                                          & b.amenity.isna() & b.shop.isna() & b.office.isna())
b["work"] = (b.building.isin(P["work_buildings"]) | b.amenity.notna() | b.shop.notna() | b.office.notna()
             | ((b.building == "yes") & in_landuse(P["work_landuse"]))) & b.pt.within(gmina_kutno)
b.loc[b.work, "cur"] = False
# R5: wszystko poza EXCL (po tagu building); dodatkowo wariant R5+: bez amenity/shop/office i bez budynków pracy w gm. Kutno
b["r5"] = ~b.building.isin(EXCL)
b["r5p"] = b.r5 & ~b.work & b.amenity.isna() & b.shop.isna() & b.office.isna()
b["pt_pow"] = b.pt.within(powiat)

# --- BDOT10k ------------------------------------------------------------------------------------------
bd = pyogrio.read_dataframe("data/raw/g3/bdot10k/x/PL.PZGiK.340.BDOT10k.1002__OT_BUBD_A.gpkg", encoding="utf-8")
bd = bd[bd.KATEGORIAISTNIENIA == "eksploatowany"].copy()
bd["area_m2"] = bd.geometry.area
bd["pt"] = bd.geometry.representative_point()
bd["mieszk"] = bd.FUNKCJAOGOLNABUDYNKU == "budynki mieszkalne"
bd["kond"] = bd.LICZBAKONDYGNACJI
bd["gmina"] = gpd.sjoin(bd.set_geometry("pt")[["pt"]], gminy_gdf, predicate="within", how="left")["gmina"].reindex(bd.index)
b["gmina"] = gpd.sjoin(pts[["pt"]], gminy_gdf, predicate="within", how="left")["gmina"].reindex(b.index)
bd["w_kutno"] = bd.pt.within(gmina_kutno)
b["w_kutno"] = b.pt.within(gmina_kutno)
pts = b.set_geometry("pt")

RES["bdot"] = dict(
    n_all=int(pyogrio.read_info("data/raw/g3/bdot10k/x/PL.PZGiK.340.BDOT10k.1002__OT_BUBD_A.gpkg")["features"]),
    n_eksploatowany=int(len(bd)),
    wersja=str(bd.WERSJA.max()),
    funkcja_ogolna=bd.FUNKCJAOGOLNABUDYNKU.value_counts().to_dict(),
    przewazajaca_mieszkalne=bd[bd.mieszk].PRZEWAZAJACAFUNKCJABUDYNKU.value_counts(dropna=False).to_dict(),
    kondygnacje_wypelnione_pct=float(bd.kond.notna().mean() * 100),
    kondygnacje_mieszkalne_hist=bd[bd.mieszk].kond.value_counts(dropna=False).sort_index().to_dict(),
    zrodlo_geometrii=bd.ZRODLODANYCHGEOMETRYCZNYCH.value_counts(dropna=False).to_dict(),
)
cov = []
for name, mb, mo in (("gm. Kutno", bd.w_kutno, b.w_kutno), ("powiat 1002", bd.pt.within(powiat), b.pt_pow)):
    cov.append(dict(zakres=name,
                    bdot_budynki=int(mb.sum()), bdot_mieszk=int((mb & bd.mieszk).sum()),
                    bdot_mieszk_km2=float(bd.area_m2[mb & bd.mieszk].sum() / 1e6),
                    bdot_mieszk_kond_km2=float((bd.area_m2 * bd.kond.fillna(1))[mb & bd.mieszk].sum() / 1e6),
                    osm_budynki=int(mo.sum()), osm_obecny_mieszk=int((mo & b.cur).sum()), osm_obecny_km2=float(b.area_m2[mo & b.cur].sum() / 1e6),
                    osm_r5=int((mo & b.r5).sum()), osm_r5_km2=float(b.area_m2[mo & b.r5].sum() / 1e6),
                    osm_r5plus=int((mo & b.r5p).sum()), osm_r5plus_km2=float(b.area_m2[mo & b.r5p].sum() / 1e6)))
pd.DataFrame(cov).to_csv(OUT / "pokrycie_bdot_osm.csv", index=False)
RES["pokrycie"] = cov

# --- zgodność OSM <-> BDOT: punkt reprezentatywny OSM w budynku BDOT (po największym pokryciu: jedna para na budynek OSM) ---
j = gpd.sjoin(pts[["pt", "building", "cur", "r5", "r5p", "w_kutno", "area_m2"]], bd[["geometry", "FUNKCJAOGOLNABUDYNKU", "PRZEWAZAJACAFUNKCJABUDYNKU", "kond", "mieszk"]],
              predicate="within", how="left").reset_index().drop_duplicates("index").set_index("index")
b["bd_fun"] = j.FUNKCJAOGOLNABUDYNKU.reindex(b.index)
b["bd_mieszk"] = j.mieszk.reindex(b.index).fillna(False).astype(bool)
b["bd_kond"] = j.kond.reindex(b.index)
b["bd_match"] = b.bd_fun.notna()
pts = b.set_geometry("pt")
kt = b[b.w_kutno]
RES["zgodnosc_osm_bdot_gm_kutno"] = dict(
    osm_budynki=int(len(kt)), z_odpowiednikiem_w_bdot=int(kt.bd_match.sum()),
    bez_odpowiednika_wg_tagu=kt[~kt.bd_match].building.value_counts().head(12).to_dict(),
)
conf = []
for nm in ("cur", "r5", "r5p"):
    sub = kt[kt.bd_match]
    tp = int((sub[nm] & sub.bd_mieszk).sum()); fp = int((sub[nm] & ~sub.bd_mieszk).sum())
    fn = int((~sub[nm] & sub.bd_mieszk).sum()); tn = int((~sub[nm] & ~sub.bd_mieszk).sum())
    conf.append(dict(wariant=nm, osm_mieszk_i_bdot_mieszk=tp, osm_mieszk_bdot_niemieszk=fp, osm_niemieszk_bdot_mieszk=fn, oba_niemieszk=tn,
                     precision=tp / (tp + fp), recall=tp / (tp + fn),
                     fp_pow_m2=float(sub.area_m2[sub[nm] & ~sub.bd_mieszk].sum()), fn_pow_m2=float(sub.area_m2[~sub[nm] & sub.bd_mieszk].sum())))
pd.DataFrame(conf).to_csv(OUT / "zgodnosc_osm_bdot_gm_kutno.csv", index=False)
RES["zgodnosc_konfuzja"] = conf
RES["fp_wg_funkcji_bdot_r5"] = kt[kt.bd_match & kt.r5 & ~kt.bd_mieszk].bd_fun.value_counts().to_dict()
RES["fp_wg_tagu_osm_r5"] = kt[kt.bd_match & kt.r5 & ~kt.bd_mieszk].building.value_counts().head(8).to_dict()
RES["fn_wg_tagu_osm_cur"] = kt[kt.bd_match & ~kt.cur & kt.bd_mieszk].building.value_counts().head(8).to_dict()
RES["osm_tag_vs_kond"] = dict(
    yes_mieszk_bdot_kond=kt[(kt.building == "yes") & kt.bd_mieszk].bd_kond.value_counts().sort_index().to_dict(),
    apartments_kond=kt[(kt.building == "apartments") & kt.bd_mieszk].bd_kond.value_counts().sort_index().to_dict(),
)

# --- wpływ R5 na rozkład: per obwód i per gmina --------------------------------------------------------------
def agg(df, key, polys):
    g = df.groupby(key)
    t = pd.DataFrame({
        "cur_m2": g.apply(lambda x: x.area_m2[x.cur].sum()), "r5_m2": g.apply(lambda x: x.area_m2[x.r5p].sum()),
        "cur_n": g.apply(lambda x: x.cur.sum()), "r5_n": g.apply(lambda x: x.r5p.sum()),
        "bdot_m2": g.apply(lambda x: x.area_m2[x.bd_mieszk.fillna(False).astype(bool)].sum())})
    return t.reindex(polys).fillna(0)


b["obwod"] = np.nan
oj = gpd.sjoin(pts[["pt"]], gpd.GeoDataFrame({"uid": obwody.index}, geometry=obwody.values), predicate="within", how="left")
b["obwod"] = oj.uid.reset_index().drop_duplicates("index").set_index("index").uid.reindex(b.index)
ob_t = agg(b[b.obwod.notna()], "obwod", obwody.index)
ob_t["delta_m2"] = ob_t.r5_m2 - ob_t.cur_m2
ob_t["delta_pct"] = 100 * ob_t.delta_m2 / ob_t.cur_m2.replace(0, np.nan)
ob_t["bdot_m2"] = agg(b[b.obwod.notna()], "obwod", obwody.index).bdot_m2
ob_w = pd.read_csv("scenarios/kutno/demand/workers_by_obwod.csv").set_index("obwod_id")
ob_t["pracujacy_w_kutnie"] = ob_w.work_in_kutno_base.reindex(ob_t.index)
ob_t["pow_obwodu_m2"] = obwody.area.reindex(ob_t.index)
ob_t["cur_zero"] = ob_t.cur_n == 0
ob_t["r5_zero"] = ob_t.r5_n == 0
ob_t.to_csv(OUT / "wplyw_r5_per_obwod.csv")
RES["r5_obwody"] = dict(
    n_obwodow=int(len(ob_t)),
    cur_m2_suma=float(ob_t.cur_m2.sum()), r5_m2_suma=float(ob_t.r5_m2.sum()),
    obwody_bez_domu_cur=int(ob_t.cur_zero.sum()), obwody_bez_domu_r5=int(ob_t.r5_zero.sum()),
    obwody_bez_domu_cur_ale_z_pracujacymi=int((ob_t.cur_zero & (ob_t.pracujacy_w_kutnie > 0)).sum()),
    pracujacy_w_obwodach_bez_domu_cur=float(ob_t.pracujacy_w_kutnie[ob_t.cur_zero].sum()),
    pracujacy_w_obwodach_bez_domu_r5=float(ob_t.pracujacy_w_kutnie[ob_t.r5_zero].sum()),
    obwody_zmiana_ponad_20pct=int((ob_t.delta_pct.abs() > 20).sum()), obwody_zmiana_ponad_50pct=int((ob_t.delta_pct.abs() > 50).sum()),
    top10_przyrost_m2=ob_t.delta_m2.sort_values(ascending=False).head(10).round(0).to_dict(),
    top10_przyrost_pct=ob_t.delta_pct.replace([np.inf], np.nan).sort_values(ascending=False).head(10).round(1).to_dict(),
)
# przesunięcie masy: L1 między udziałami powierzchni w obrębie obwodu nie ma sensu (n z obwodu stałe) -> miara: ile % agentów
# zmieniłoby budynek-klasę (udział nowych budynków w puli obwodu, ważony pracującymi)
newshare = (1 - ob_t.cur_m2 / ob_t.r5_m2.replace(0, np.nan))
RES["r5_obwody"]["udzial_nowej_powierzchni_w_puli_wazony_pracujacymi_pct"] = float(
    (newshare.fillna(1) * ob_t.pracujacy_w_kutnie).sum() / ob_t.pracujacy_w_kutnie.sum() * 100)

gm_t = agg(b[b.gmina.notna()], "gmina", gminy.index)
gm_t["delta_m2"] = gm_t.r5_m2 - gm_t.cur_m2
gm_t["delta_pct"] = 100 * gm_t.delta_m2 / gm_t.cur_m2.replace(0, np.nan)
gm_t["udzial_nowej_w_puli_pct"] = 100 * (1 - gm_t.cur_m2 / gm_t.r5_m2.replace(0, np.nan))
gm_t.to_csv(OUT / "wplyw_r5_per_gmina.csv")
RES["r5_gminy"] = gm_t.round(1).to_dict(orient="index")
# rozbicie przyrostu wg tagu (cały powiat)
new = b[b.r5p & ~b.cur & b.pt_pow]
RES["r5_przyrost_wg_tagu_powiat"] = new.groupby("building").area_m2.agg(["count", "sum"]).sort_values("sum", ascending=False).head(10).round(0).to_dict("index")
RES["r5_przyrost_yes_poza_landuse_res_powiat"] = int(((new.building == "yes") & ~new.in_lu_res).sum())
RES["r5_przyrost_wg_bdot_funkcji_gm_kutno"] = b[b.r5p & ~b.cur & b.w_kutno].bd_fun.fillna("brak w BDOT").value_counts().to_dict()
RES["r5_przyrost_m2_bdot_mieszk_vs_nie_gm_kutno"] = {
    "bdot_mieszk": float(b.area_m2[b.r5p & ~b.cur & b.w_kutno & b.bd_mieszk.fillna(False).astype(bool)].sum()),
    "bdot_niemieszk_lub_brak": float(b.area_m2[b.r5p & ~b.cur & b.w_kutno & ~b.bd_mieszk.fillna(False).astype(bool)].sum())}

# --- siatka GUS: 250 m i 1 km vs domy agentów i powierzchnie budynków -----------------------------------------
bb = tuple(gpd.GeoSeries([powiat], crs="EPSG:2180").to_crs(3035).buffer(2000).total_bounds)
g250 = pyogrio.read_dataframe("data/raw/g3/gus_grid/g250/NSP2021_TOT_grid250m.shp", bbox=bb)
g250 = g250.set_crs(3035, allow_override=True)
g250["TOT"] = g250.TOT.astype(float)
RES["gus_250"] = dict(komorek_w_bbox_powiatu=int(len(g250)), suma_TOT=float(g250.TOT.sum()), nan=int(g250.TOT.isna().sum()),
                      min=float(g250.TOT.min()), max=float(g250.TOT.max()), male_1_4=int(g250.TOT.between(1, 4).sum()))
c1k = pyogrio.read_dataframe("data/raw/g3/gus_grid/x/GRID_NSP2021_RES.shp", bbox=tuple(gpd.GeoSeries([powiat], crs="EPSG:2180").buffer(2000).total_bounds)).set_crs(2180, allow_override=True)
RES["gus_1km"] = dict(komorek=int(len(c1k)), suma_RES=float(c1k.RES.sum()))
g250 = g250.to_crs(2180)
g250["cx"] = g250.geometry.centroid.x
g250["cy"] = g250.geometry.centroid.y
g250["gmina"] = gpd.sjoin(g250[["geometry"]].set_geometry(g250.geometry.centroid), gminy_gdf, predicate="within", how="left")["gmina"].reindex(g250.index)
g250["w_kutno"] = g250.geometry.centroid.within(gmina_kutno)
kutno_cells = g250[g250.w_kutno].copy()
RES["gus_250"]["suma_TOT_gm_kutno_centroidy"] = float(kutno_cells.TOT.sum())

# agenci: domy rezydentów (25%) + dojeżdżający z powiatu
meta = pd.read_csv("scenarios/kutno/plans_25pct_meta.csv")
meta = meta[meta.home_src.str.startswith("osm_") | (meta.home_src == "random_point")]
ag = gpd.GeoDataFrame(meta, geometry=gpd.points_from_xy(meta.home_x, meta.home_y), crs="EPSG:2180")
RES["agenci"] = dict(n=int(len(ag)), rezydenci=int((ag.kind == "resident").sum()), dojezdzajacy_z_domem_osm=int((ag.kind == "commuter").sum()),
                     random_point=int((ag.home_src == "random_point").sum()))


def cell_counts(cells, pts_gdf, col):
    j = gpd.sjoin(pts_gdf[["geometry"]], cells[["geometry"]], predicate="within", how="inner")
    return j.groupby("index_right").size().reindex(cells.index).fillna(0).rename(col)


def corr_row(name, x, y):
    return dict(zmienna=name, pearson=float(pearsonr(x, y)[0]), spearman=float(spearmanr(x, y)[0]),
                n_komorek=int(len(x)))


def surface(df_mask, weight=None, cells=None):
    """suma powierzchni (lub waga) budynków z maską per komórka siatki (po punkcie reprezentatywnym)"""
    sub = pts[df_mask][["pt", "area_m2"]].copy()
    sub["w"] = sub.area_m2 * (weight[df_mask] if weight is not None else 1)
    j = gpd.sjoin(sub.set_geometry("pt")[["pt", "w"]], cells[["geometry"]], predicate="within", how="inner")
    return j.groupby("index_right").w.sum().reindex(cells.index).fillna(0)


rows = []
bdp = bd.set_geometry("pt")
for label, cells, sel_res_only in (("gm. Kutno, rezydenci (agenci)", kutno_cells, True), ("powiat, wszyscy agenci z domem w OSM", g250, False)):
    a = ag[ag.kind == "resident"] if sel_res_only else ag[ag.home_src.str.startswith("osm_") & ag.key.astype(str).str.startswith("1002") | (ag.kind == "resident")]
    cells = cells.copy()
    cells["agenci"] = cell_counts(cells, a, "agenci")
    cells["osm_cur_m2"] = surface(b.cur, cells=cells)
    cells["osm_r5_m2"] = surface(b.r5p, cells=cells)
    sub = bdp[bdp.mieszk]
    j = gpd.sjoin(sub[["pt", "area_m2", "kond"]], cells[["geometry"]], predicate="within", how="inner")
    cells["bdot_m2"] = j.groupby("index_right").area_m2.sum().reindex(cells.index).fillna(0)
    cells["bdot_kond_m2"] = (j.assign(w=j.area_m2 * j.kond.fillna(1)).groupby("index_right").w.sum()).reindex(cells.index).fillna(0)
    cells["bdot_n"] = j.groupby("index_right").size().reindex(cells.index).fillna(0)
    mask = cells.TOT > 0
    for col in ("agenci", "osm_cur_m2", "osm_r5_m2", "bdot_m2", "bdot_kond_m2", "bdot_n"):
        r = corr_row(col, cells.loc[mask, col], cells.loc[mask, "TOT"]); r["zakres"] = label; rows.append(r)
    if sel_res_only:
        kc = cells
    else:
        pc = cells
cor = pd.DataFrame(rows)[["zakres", "zmienna", "n_komorek", "pearson", "spearman"]]
cor.to_csv(OUT / "korelacje_siatka_250m.csv", index=False)
RES["korelacje_250m"] = cor.round(3).to_dict("records")

# 1 km (agregacja 250 m do kratek 1 km przez dzielenie współrzędnych w układzie 2180 nie pasuje do siatki 1 km GUS -> użyj oficjalnej 1 km)
rows = []
c1 = c1k.copy()
c1["w_kutno"] = c1.geometry.centroid.within(gmina_kutno)
for label, cells, a in (("1 km, gm. Kutno, rezydenci", c1[c1.w_kutno].copy(), ag[ag.kind == "resident"]),
                        ("1 km, powiat, agenci z domem w powiecie", c1.copy(), ag[(ag.kind == "resident") | ag.key.astype(str).str.startswith("1002")])):
    cells["agenci"] = cell_counts(cells, a, "agenci")
    cells["osm_cur_m2"] = surface(b.cur, cells=cells)
    cells["osm_r5_m2"] = surface(b.r5p, cells=cells)
    j = gpd.sjoin(bdp[bdp.mieszk][["pt", "area_m2", "kond"]], cells[["geometry"]], predicate="within", how="inner")
    cells["bdot_m2"] = j.groupby("index_right").area_m2.sum().reindex(cells.index).fillna(0)
    cells["bdot_kond_m2"] = j.assign(w=j.area_m2 * j.kond.fillna(1)).groupby("index_right").w.sum().reindex(cells.index).fillna(0)
    m = cells.RES > 0
    for col in ("agenci", "osm_cur_m2", "osm_r5_m2", "bdot_m2", "bdot_kond_m2"):
        r = corr_row(col, cells.loc[m, col], cells.loc[m, "RES"]); r["zakres"] = label; rows.append(r)
cor1 = pd.DataFrame(rows)[["zakres", "zmienna", "n_komorek", "pearson", "spearman"]]
cor1.to_csv(OUT / "korelacje_siatka_1km.csv", index=False)
RES["korelacje_1km"] = cor1.round(3).to_dict("records")

# --- mapy ------------------------------------------------------------------------------------------------------
kc = kc.copy()
kc["agenci_skala"] = kc.agenci / kc.agenci.sum() * kc.TOT.sum()  # agenci przeskalowani do liczby mieszkańców gm. Kutno
kc["roznica"] = kc.agenci_skala - kc.TOT
Path(OUT / "siatka250_kutno_porownanie.gpkg").unlink(missing_ok=True)
kc.drop(columns=["cx", "cy", "fid"]).to_file(OUT / "siatka250_kutno_porownanie.gpkg", driver="GPKG")
vmax = float(np.percentile(np.abs(kc.roznica), 98))
fig, ax = plt.subplots(1, 3, figsize=(21, 7.5))
pm = float(kc.TOT.quantile(0.99))
kc.plot(column="TOT", cmap="magma", vmin=0, vmax=pm, ax=ax[0], legend=True, legend_kwds=dict(shrink=0.7))
kc.plot(column="agenci_skala", cmap="magma", vmin=0, vmax=pm, ax=ax[1], legend=True, legend_kwds=dict(shrink=0.7))
kc.plot(column="roznica", cmap="RdBu_r", vmin=-vmax, vmax=vmax, ax=ax[2], legend=True, legend_kwds=dict(shrink=0.7))
for a_, t in zip(ax, ("GUS NSP 2021: mieszkańcy / 250 m", "domy agentów (25%), przeskalowane do sumy GUS", "różnica: agenci − GUS (czerwony = nadmiar agentów)")):
    a_.set_title(t, fontsize=11); a_.set_aspect("equal"); a_.axis("off")
    gpd.GeoSeries([gmina_kutno], crs=2180).boundary.plot(ax=a_, color="white", lw=0.6)
fig.suptitle(f"G3: Kutno, siatka GUS 250 m (r Pearson = {cor.query('zmienna==\"agenci\"').pearson.iloc[0]:.2f})")
fig.tight_layout(); fig.savefig(OUT / "mapa_agenci_vs_gus_250m.png", dpi=130); plt.close(fig)

# scatter: który wariant powierzchni lepiej tłumaczy GUS
fig, ax = plt.subplots(1, 4, figsize=(20, 5))
for a_, col, t in zip(ax, ("osm_cur_m2", "osm_r5_m2", "bdot_m2", "bdot_kond_m2"), ("OSM obecny", "OSM jak R5", "BDOT10k mieszkalne", "BDOT10k mieszkalne × kondygnacje")):
    m = kc.TOT > 0
    a_.scatter(kc.loc[m, col], kc.loc[m, "TOT"], s=6, alpha=0.5, color="#4fc3f7")
    a_.set_title(f"{t}\nPearson {pearsonr(kc.loc[m, col], kc.loc[m, 'TOT'])[0]:.2f}, Spearman {spearmanr(kc.loc[m, col], kc.loc[m, 'TOT'])[0]:.2f}", fontsize=10)
    a_.set_xlabel("powierzchnia obrysów w komórce 250 m [m²]"); a_.set_ylabel("mieszkańcy GUS")
fig.tight_layout(); fig.savefig(OUT / "scatter_powierzchnia_vs_gus_250m.png", dpi=120); plt.close(fig)

# mapa wpływu R5 per obwód
og = gpd.GeoDataFrame(ob_t, geometry=obwody.reindex(ob_t.index).values)
fig, ax = plt.subplots(1, 2, figsize=(15, 7.5))
og.plot(column="delta_pct", cmap="viridis", ax=ax[0], legend=True, legend_kwds=dict(shrink=0.7, label="% przyrostu powierzchni mieszkalnej"),
        missing_kwds=dict(color="#444444"))
og.plot(column="delta_m2", cmap="viridis", ax=ax[1], legend=True, legend_kwds=dict(shrink=0.7, label="m² przyrostu"))
og[og.cur_zero].boundary.plot(ax=ax[0], color="red", lw=1.2)
for a_, t in zip(ax, ("R5 vs obecny: zmiana powierzchni (%), czerwony = obwód bez domu w obecnym modelu", "R5 vs obecny: przyrost powierzchni [m²]")):
    a_.set_title(t, fontsize=10); a_.set_aspect("equal"); a_.axis("off")
fig.tight_layout(); fig.savefig(OUT / "mapa_wplyw_r5_obwody.png", dpi=130); plt.close(fig)

# mapa budynków: różnica klasyfikacji w gm. Kutno (R5 dodaje, BDOT mieszkalne)
fig, ax = plt.subplots(figsize=(10, 10))
gpd.GeoSeries([gmina_kutno], crs=2180).boundary.plot(ax=ax, color="white", lw=0.6)
sel = b[b.w_kutno]
sel[sel.cur].plot(ax=ax, color="#4fc3f7", lw=0, label="obecny model")
sel[sel.r5p & ~sel.cur].plot(ax=ax, color="#ff9800", lw=0, label="dodaje R5")
sel[~sel.cur & sel.bd_mieszk.fillna(False).astype(bool) & ~sel.r5p].plot(ax=ax, color="#e91e63", lw=0, label="BDOT mieszkalne, nie w OSM-modelu ani R5")
ax.legend(loc="lower left"); ax.set_aspect("equal"); ax.axis("off")
ax.set_title("Budynki mieszkalne w gm. Kutno: obecny model, dodatek R5, braki wg BDOT10k")
fig.tight_layout(); fig.savefig(OUT / "mapa_budynki_kutno.png", dpi=130); plt.close(fig)

# --- wariant z kondygnacjami BDOT: wpływ na pulę obwodu (udział budynków wielokondygnacyjnych) ----------------
bk = b[b.w_kutno & b.cur].copy()
bk["w_area"] = bk.area_m2
bk["w_kond"] = bk.area_m2 * bk.bd_kond.fillna(1)
o = bk.groupby("obwod").agg(area=("w_area", "sum"), area_kond=("w_kond", "sum"))
o["ratio"] = o.area_kond / o.area
RES["kondygnacje"] = dict(
    srednia_kond_wazona_powierzchnia_cur_gm_kutno=float(bk.w_kond.sum() / bk.w_area.sum()),
    udzial_cur_z_kond_w_bdot_pct=float(bk.bd_kond.notna().mean() * 100),
    obwody_ratio_min_max=[float(o.ratio.min()), float(o.ratio.max())],
    apartments_cur_powierzchnia_udzial_pct=float(bk.w_area[bk.building == "apartments"].sum() / bk.w_area.sum() * 100),
    apartments_cur_udzial_po_kond_pct=float(bk.w_kond[bk.building == "apartments"].sum() / bk.w_kond.sum() * 100),
)
# ile agentów by się przesunęło do wieloKond. (przybliżenie): suma |udział_kond - udział_pow| /2 w obwodach, wazone pracującymi
sh = bk.assign(s1=bk.w_area / bk.groupby("obwod").w_area.transform("sum"), s2=bk.w_kond / bk.groupby("obwod").w_kond.transform("sum"))
tv = sh.groupby("obwod").apply(lambda x: (x.s1 - x.s2).abs().sum() / 2)
RES["kondygnacje"]["TV_rozkladu_budynkow_w_obwodzie_sr_wazona_pracujacymi_pct"] = float(
    (tv * ob_w.work_in_kutno_base.reindex(tv.index)).sum() / ob_w.work_in_kutno_base.reindex(tv.index).sum() * 100)

# --- oczekiwany rozkład domów rezydentów (bez szumu losowania) dla wariantów wag vs GUS 250 m ------------------------
# agenci = obwód n × udział wagi budynku w obwodzie; tu liczymy oczekiwanie, więc korelacja ocenia WYBÓR BUDYNKÓW wewnątrz obwodu
bd["obwod"] = gpd.sjoin(bdp[["pt"]] if False else bd.set_geometry("pt")[["pt"]], gpd.GeoDataFrame({"uid": obwody.index}, geometry=obwody.values), predicate="within", how="left").uid.reset_index().drop_duplicates("index").set_index("index").uid.reindex(bd.index)
nw = ob_w.work_in_kutno_base
variants = {
    "OSM obecny": (b[b.cur & b.obwod.notna()].set_index(b[b.cur & b.obwod.notna()].index), b.area_m2),
    "OSM jak R5 (bez pracy/amenity)": (b[b.r5p & b.obwod.notna()], b.area_m2),
    "BDOT mieszkalne, pow.": (bd[bd.mieszk & bd.obwod.notna()], bd.area_m2),
    "BDOT mieszkalne, pow. × kond.": (bd[bd.mieszk & bd.obwod.notna()], bd.area_m2 * bd.kond.fillna(1)),
    "BDOT mieszkalne, liczba budynków": (bd[bd.mieszk & bd.obwod.notna()], pd.Series(1.0, index=bd.index)),
}
exp_rows, expcols = [], {}
for name, (sub, w) in variants.items():
    s = sub.assign(w=w.reindex(sub.index))
    s["wn"] = s.w / s.groupby("obwod").w.transform("sum") * nw.reindex(s.obwod).to_numpy()
    s = s.set_geometry("pt") if "pt" in s else s
    j = gpd.sjoin(s[["pt", "wn"]].set_geometry("pt"), kutno_cells[["geometry"]], predicate="within", how="inner")
    e = j.groupby("index_right").wn.sum().reindex(kutno_cells.index).fillna(0)
    expcols[name] = e
    m = kutno_cells.TOT > 0
    exp_rows.append(dict(wariant=name, pearson=float(pearsonr(e[m], kutno_cells.TOT[m])[0]), spearman=float(spearmanr(e[m], kutno_cells.TOT[m])[0]),
                         MAE_udzialow_pp=float((e / e.sum() * 100 - kutno_cells.TOT / kutno_cells.TOT.sum() * 100).abs().sum() / 2)))
pd.DataFrame(exp_rows).to_csv(OUT / "oczekiwany_rozklad_vs_gus_250m.csv", index=False)
RES["oczekiwany_rozklad_vs_gus_250m"] = exp_rows
RES["obwod_bez_domu_cur"] = {int(k): float(nw.get(k, np.nan)) for k in ob_t.index[ob_t.cur_zero]}
fig, ax = plt.subplots(1, len(expcols), figsize=(5 * len(expcols), 5))
for a_, (name, e) in zip(ax, expcols.items()):
    tmp = kutno_cells.assign(d=e / e.sum() * kutno_cells.TOT.sum() - kutno_cells.TOT)
    tmp.plot(column="d", cmap="RdBu_r", vmin=-vmax, vmax=vmax, ax=a_)
    a_.set_title(f"{name}\nTV={exp_rows[list(expcols).index(name)]['MAE_udzialow_pp']:.1f} pp", fontsize=9); a_.axis("off"); a_.set_aspect("equal")
fig.suptitle("Oczekiwana liczba domów − GUS (mieszkańcy / 250 m), przeskalowane do sumy GUS; czerwony = nadmiar modelu")
fig.tight_layout(); fig.savefig(OUT / "mapa_wariantow_vs_gus_250m.png", dpi=120); plt.close(fig)
with open(OUT / "g3_wyniki.json", "w", encoding="utf-8") as f:
    json.dump(RES, f, ensure_ascii=False, indent=1, default=str)
print(json.dumps(RES, ensure_ascii=False, indent=1, default=str)[:12000])
