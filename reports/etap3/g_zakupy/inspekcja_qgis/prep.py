"""Warstwy do inspekcji QGIS: pula celów zakupów/usług z BDOT (jak errands.py) i POI OSM shop/amenity w gm. Kutno."""
import sys, osmium, geopandas as gpd, pandas as pd, pyogrio
from shapely import wkb
from shapely.geometry import Point
OUT = sys.argv[1]
gm = gpd.read_file("scenarios/kutno/area/gmina.geojson").to_crs(2180).geometry.iloc[0]
# BDOT: wszystkie eksploatowane budynki w gminie, z flagą puli errands (te same funkcje co errands.TYPES)
sys.path.insert(0, "pipeline"); from errands import TYPES
f2t = {f: c for c, (_, _, fs) in TYPES.items() for f in fs}
bd = pyogrio.read_dataframe("data/raw/g3/bdot10k/x/PL.PZGiK.340.BDOT10k.1002__OT_BUBD_A.gpkg", encoding="utf-8")
bd = bd[bd.KATEGORIAISTNIENIA == "eksploatowany"]
bd = bd[bd.geometry.representative_point().within(gm)].copy()
bd["area_m2"] = bd.geometry.area.round(0)
bd["fun"] = bd.PRZEWAZAJACAFUNKCJABUDYNKU
bd["errand"] = bd.fun.map(f2t)
pool = bd[bd.errand.notna()][["fun", "errand", "area_m2", "LICZBAKONDYGNACJI", "geometry"]].copy()
for c in "csu":
    m = pool.errand == c; pool.loc[m, "w_pct"] = (100 * pool.area_m2[m] / pool.area_m2[m].sum()).round(2)
pool.to_file(OUT, layer="bdot_errand_pool", driver="GPKG")
# OSM: shop=* i amenity usługowe (węzły i obszary), punkt reprezentatywny
AM = {"bank", "post_office", "townhall", "courthouse", "police", "pharmacy", "marketplace", "clinic", "doctors", "dentist", "fuel",
      "restaurant", "fast_food", "cafe", "bar", "pub"}
w, s, e, n = gpd.GeoSeries([gm], crs=2180).to_crs(4326).total_bounds
fab = osmium.geom.WKBFactory(); rows = []
for o in osmium.FileProcessor("data/raw/osm/lodzkie-261015.osm.pbf").with_areas().with_filter(osmium.filter.KeyFilter("shop", "amenity")):
    t = dict(o.tags); sh, am = t.get("shop"), t.get("amenity")
    if not sh and am not in AM: continue
    try:
        if o.is_node(): g = Point(o.location.lon, o.location.lat)
        elif o.is_area(): g = wkb.loads(fab.create_multipolygon(o), hex=True).representative_point()
        else: continue
    except Exception: continue
    if not (w <= g.x <= e and s <= g.y <= n): continue
    rows.append(dict(osm_type="n" if o.is_node() else "a", osm_id=o.id if o.is_node() else o.orig_id(), shop=sh, amenity=am,
                     name=t.get("name"), building=t.get("building"), geometry=g))
poi = gpd.GeoDataFrame(rows, crs=4326).to_crs(2180)
poi = poi[poi.within(gm)].copy()
def cat(r):
    sh = r.shop if isinstance(r.shop, str) else None
    if sh in ("supermarket", "department_store", "mall", "wholesale", "doityourself", "hardware", "furniture", "electronics", "car"): return "c_duzy_handel"
    if sh: return "s_sklep"
    if r.amenity in ("bank", "post_office", "townhall", "courthouse", "police"): return "u_urzad_bank_poczta"
    if r.amenity in ("pharmacy", "clinic", "doctors", "dentist"): return "zdrowie"
    if r.amenity in ("restaurant", "fast_food", "cafe", "bar", "pub"): return "gastro"
    return "inne"
poi["kat"] = poi.apply(cat, axis=1)
# dopasowanie: POI wewnątrz / do 15 m od budynku BDOT -> jego funkcja
j = gpd.sjoin_nearest(poi, bd[["fun", "errand", "area_m2", "geometry"]], how="left", max_distance=15, distance_col="d_m")
j = j[~j.index.duplicated()]
poi[["bdot_fun", "bdot_errand", "bdot_area", "d_m"]] = j[["fun", "errand", "area_m2", "d_m"]]
poi.to_file(OUT, layer="osm_poi", driver="GPKG")
gpd.GeoDataFrame(geometry=[gm.boundary], crs=2180).to_file(OUT, layer="gmina", driver="GPKG")
print("BDOT budynki", len(bd), "pula", len(pool)); print(pool.groupby(["errand", "fun"]).agg(n=("area_m2", "size"), m2=("area_m2", "sum")))
print("OSM POI", len(poi)); print(poi.kat.value_counts())
print(pd.crosstab(poi.kat, poi.bdot_errand.fillna("-"), margins=True))
print("POI bez budynku BDOT w 15 m:", poi.bdot_fun.isna().sum())
print(poi[poi.bdot_errand.isna() & poi.bdot_fun.notna()].groupby("kat").bdot_fun.value_counts().groupby(level=0).head(6))
