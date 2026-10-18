"""Audyt G5: gdzie w sieci kończą się DK92 (zachód), DK60 (północ), DW581 (północ) i czy koniec leży na granicy obszaru sieci.

Użycie: uv run python -W ignore reports/audyt_g5/skrypty/a7_road_ends.py
"""
import gzip
import geopandas as gpd
import osmium
from lxml import etree
from shapely.geometry import Point

area = gpd.read_file("scenarios/kutno/area/network_area.geojson").geometry.iloc[0]
woj = None
refs = {}


class H(osmium.SimpleHandler):
    def way(self, w):
        r = w.tags.get("ref")
        if r and w.tags.get("highway") in ("trunk", "primary", "secondary", "trunk_link", "primary_link"):
            refs[str(w.id)] = r


H().apply_file("data/raw/osm/lodzkie-261015.osm.pbf")
nodes, deg, L = {}, {}, []
with gzip.open("scenarios/kutno/network.xml.gz", "rb") as f:
    for _, el in etree.iterparse(f, tag=("node", "link")):
        if el.tag == "node":
            nodes[el.get("id")] = (float(el.get("x")), float(el.get("y")))
        else:
            a = {x.get("name"): x.text for x in el.iter("attribute")}
            L.append((el.get("id"), el.get("from"), el.get("to"), refs.get(a.get("origid"))))
        el.clear()
for want in ("92", "60", "581", "91"):
    ln = [l for l in L if l[3] and want in l[3].split(";")]
    pts = [nodes[n] for l in ln for n in l[1:3]]
    ext = {"min_x": min(pts), "max_y": max(pts, key=lambda p: p[1]), "min_y": min(pts, key=lambda p: p[1]), "max_x": max(pts)}
    print(want, len(ln), {k: (round(v[0]), round(v[1]), round(area.exterior.distance(Point(v)))) for k, v in ext.items()})
print("granica obszaru sieci (bbox):", [round(v) for v in area.bounds])
