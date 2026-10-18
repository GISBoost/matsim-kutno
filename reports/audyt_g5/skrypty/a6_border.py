"""Audyt G5: czy każda droga krajowa/wojewódzka przecinająca granicę sieci ma strefę wjazdu i wyjazdu (border_links.csv).

Użycie: uv run python reports/audyt_g5/skrypty/a6_border.py
Dla linków motorway/trunk/primary/secondary w pasie 1 km przy granicy obszaru sieci: ref z OSM (po origid), czy link
jest w border_links.csv i — jeśli nie — który warunek plans.py go odrzuca (kierunek do centrum Kutna liczony po prostej).
"""
import gzip

import geopandas as gpd
import osmium
import pandas as pd
from lxml import etree
from shapely.geometry import Point

area = gpd.read_file("scenarios/kutno/area/network_area.geojson").geometry.iloc[0]
interior = area.buffer(-1000)
C = Point(524805, 485023)
nodes, rows = {}, []
with gzip.open("scenarios/kutno/network.xml.gz", "rb") as f:
    for _, el in etree.iterparse(f, tag=("node", "link")):
        if el.tag == "node":
            nodes[el.get("id")] = Point(float(el.get("x")), float(el.get("y")))
        else:
            a = {x.get("name"): x.text for x in el.iter("attribute")}
            if a.get("type") in ("motorway", "trunk", "primary", "secondary"):
                rows.append((el.get("id"), el.get("from"), el.get("to"), a.get("type"), a.get("origid")))
        el.clear()
b = set(pd.read_csv("scenarios/kutno/demand/border_links.csv").link)
cand = []
for l, fa, tb, _t, _o in rows:
    A, B = nodes[fa], nodes[tb]
    if interior.contains(A) and interior.contains(B):
        continue
    cand.append(dict(link=l, type=None, origid=None, ax=round(A.x), ay=round(A.y), bx=round(B.x), by=round(B.y),
                     a_out_interior=not interior.contains(A), b_out_interior=not interior.contains(B),
                     a_in_area=area.contains(A), b_in_area=area.contains(B),
                     towards_centre=B.distance(C) < A.distance(C), in_border_csv=l in b))
    cand[-1]["type"], cand[-1]["origid"] = [r for r in rows if r[0] == l][0][3:5]
c = pd.DataFrame(cand)
want = set(c.origid)


class H(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.ref = {}

    def way(self, w):
        if str(w.id) in want:
            self.ref[str(w.id)] = (w.tags.get("ref"), w.tags.get("name"))


h = H()
h.apply_file("data/raw/osm/lodzkie-261015.osm.pbf")
c["ref"] = c.origid.map(lambda o: h.ref.get(o, (None, None))[0])
c["name"] = c.origid.map(lambda o: h.ref.get(o, (None, None))[1])
c["cell"] = (c.bx // 3000).astype(str) + "_" + (c.by // 3000).astype(str)
s = c.groupby(["ref", "cell"], dropna=False).agg(n=("link", "size"), in_csv=("in_border_csv", "sum"), type=("type", "first"),
                                                x=("bx", "mean"), y=("by", "mean"), name=("name", "first")).reset_index()
pd.set_option("display.width", 220)
print(s.sort_values(["ref", "x"]).to_string())
c.to_csv("reports/audyt_g5/wyniki/border_candidates.csv", index=False)
