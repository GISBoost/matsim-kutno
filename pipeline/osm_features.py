"""F4: budynki i landuse z OSM (ten sam PBF co sieć) w obszarze sieci, EPSG:2180.

Uruchom: uv run python -W ignore pipeline/osm_features.py
Wyjście: scenarios/kutno/osm/features.gpkg (warstwy buildings, landuse).
"""
import osmium
import geopandas as gpd
from shapely import wkb

PBF = "data/raw/osm/lodzkie-261015.osm.pbf"
LANDUSE = {"residential", "industrial", "commercial", "retail"}
area = gpd.read_file("scenarios/kutno/area/network_area.geojson").to_crs("EPSG:4326")
w, s, e, n = area.total_bounds

fab = osmium.geom.WKBFactory()
buildings, landuse = [], []
fp = (osmium.FileProcessor(PBF).with_areas().with_filter(osmium.filter.KeyFilter("building", "landuse")))
for o in fp:
    if not o.is_area():
        continue
    tags = dict(o.tags)
    b, lu = tags.get("building"), tags.get("landuse")
    if not b and lu not in LANDUSE:
        continue
    try:
        g = wkb.loads(fab.create_multipolygon(o), hex=True)
    except Exception:  # niedomknięte relacje w OSM
        continue
    x, y = g.representative_point().coords[0]
    if not (w <= x <= e and s <= y <= n):
        continue
    rec = dict(osm_id=o.orig_id(), from_way=o.from_way(), geometry=g)
    if b:
        buildings.append(dict(rec, building=b, amenity=tags.get("amenity"), shop=tags.get("shop"), office=tags.get("office")))
    if lu in LANDUSE:
        landuse.append(dict(rec, landuse=lu))

out = "scenarios/kutno/osm/features.gpkg"
import os; os.makedirs("scenarios/kutno/osm", exist_ok=True)
for name, rows in (("buildings", buildings), ("landuse", landuse)):
    g = gpd.GeoDataFrame(rows, crs="EPSG:4326").to_crs("EPSG:2180")
    g = g[g.representative_point().within(gpd.read_file("scenarios/kutno/area/network_area.geojson").geometry.iloc[0])]
    g.to_file(out, layer=name, driver="GPKG")
    print(name, len(g))
