"""D34 (krok 4C, cel wypraw wg OSM): punkty sklepów OSM (shop=*) w gminie Kutno, EPSG:2180, z tego samego PBF co sieć.

Uruchom: uv run python -W ignore pipeline/osm_poi.py
Wyjście: scenarios/kutno/osm/shops.csv (osm_type n|a, osm_id, shop, name, x, y); obszar = punkt reprezentatywny.
"""
import csv
import osmium
import geopandas as gpd
from shapely import wkb
from shapely.geometry import Point

PBF = "data/raw/osm/lodzkie-261015.osm.pbf"
gm = gpd.read_file("scenarios/kutno/area/gmina.geojson").to_crs("EPSG:2180").geometry.iloc[0]
w, s, e, n = gpd.GeoSeries([gm], crs="EPSG:2180").to_crs("EPSG:4326").total_bounds
fab = osmium.geom.WKBFactory()
rows = []
for o in osmium.FileProcessor(PBF).with_areas().with_filter(osmium.filter.KeyFilter("shop")):
    if o.tags.get("shop") in (None, "no", "vacant"):
        continue
    if o.is_node():
        g, typ, oid = Point(o.location.lon, o.location.lat), "n", o.id
    elif o.is_area():
        try:
            g = wkb.loads(fab.create_multipolygon(o), hex=True).representative_point()
        except Exception:  # niedomknięte relacje w OSM
            continue
        typ, oid = "a", o.orig_id()
    else:
        continue  # otwarte drogi z shop (rzadkie) pomijamy
    if w <= g.x <= e and s <= g.y <= n:
        rows.append(dict(osm_type=typ, osm_id=oid, shop=o.tags["shop"], name=o.tags.get("name", ""), geometry=g))
p = gpd.GeoDataFrame(rows, crs="EPSG:4326").to_crs("EPSG:2180")
p = p[p.within(gm)].sort_values(["osm_type", "osm_id"])
p["x"], p["y"] = p.geometry.x.round(2), p.geometry.y.round(2)
p.drop(columns="geometry").to_csv("scenarios/kutno/osm/shops.csv", index=False, quoting=csv.QUOTE_MINIMAL)
print("sklepy", len(p)); print(p.shop.value_counts().head(15).to_string())
