"""Audyt G5: geometria przypisania liczników GPR do linków (scenarios/kutno/validation/gpr_linki.csv).

Użycie: uv run python reports/etap2/audyt_g5/skrypty/a3_counters.py
Dla każdego licznika: azymut obu linków, czy są przeciwne (różnica ~180°), odległość od punktu GPR, typ, OSM ref/nazwa drogi
(z PBF po origid), strona punktu względem osi (lewa/prawa w kierunku jazdy linku). Plus: czy link licznika jest linkiem
granicznym (start/koniec agentów), czy jest linkiem startu/końca aktywności w planach R4.
"""
import gzip
import json
import math

import osmium
import pandas as pd
from lxml import etree

g = pd.read_csv("scenarios/kutno/validation/gpr_linki.csv", dtype={"link": str, "origid": str})
nodes, links = {}, {}
with gzip.open("scenarios/kutno/network.xml.gz", "rb") as f:
    for _, el in etree.iterparse(f, tag=("node", "link")):
        if el.tag == "node":
            nodes[el.get("id")] = (float(el.get("x")), float(el.get("y")))
        else:
            a = {x.get("name"): x.text for x in el.iter("attribute")}
            links[el.get("id")] = dict(a=el.get("from"), b=el.get("to"), len=float(el.get("length")), cap=float(el.get("capacity")),
                                       lanes=float(el.get("permlanes")), fs=float(el.get("freespeed")) * 3.6, type=a.get("type"),
                                       origid=a.get("origid"))
        el.clear()

want = set(g.origid)


class H(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.w = {}

    def way(self, w):
        if str(w.id) in want:
            self.w[str(w.id)] = {k: w.tags.get(k) for k in ("highway", "ref", "name", "oneway", "maxspeed", "lanes")}


h = H()
h.apply_file("data/raw/osm/lodzkie-261015.osm.pbf")

border = pd.read_csv("scenarios/kutno/demand/border_links.csv")
bset = set(border.link)
pl = pd.read_csv("scenarios/kutno/plans_g5r4_25pct_tlo.csv", dtype=str)
hv = pd.read_csv("scenarios/kutno/plans_g5r4_25pct_ciezkie.csv", dtype=str)
meta = pd.read_csv("scenarios/kutno/plans_g5r4_25pct_meta.csv", dtype=str)
act_links = pd.concat([pl.o_link, pl.d_link, hv.o_link, hv.d_link, meta.home_link, meta.work_link]).value_counts()

rows = []
for r in g.itertuples():
    L = links[r.link]
    (x1, y1), (x2, y2) = nodes[L["a"]], nodes[L["b"]]
    az = math.degrees(math.atan2(x2 - x1, y2 - y1)) % 360  # azymut od północy
    # odległość punktu od odcinka i strona (iloczyn wektorowy: >0 punkt po lewej od kierunku jazdy)
    dx, dy = x2 - x1, y2 - y1
    tt = max(0, min(1, ((r.x - x1) * dx + (r.y - y1) * dy) / (dx * dx + dy * dy)))
    dist = math.hypot(r.x - (x1 + tt * dx), r.y - (y1 + tt * dy))
    cross = dx * (r.y - y1) - dy * (r.x - x1)
    o = h.w.get(r.origid, {})
    rows.append(dict(nr=r.nr, droga=r.droga, rola=r.rola, link=r.link, az=round(az), dist_seg_m=round(dist, 1), dist_csv=r.dist_m,
                     punkt_strona="lewa" if cross > 0 else "prawa", len_m=round(L["len"]), type=L["type"], lanes=L["lanes"],
                     cap=L["cap"], fs_kmh=round(L["fs"]), osm_ref=o.get("ref"), osm_name=o.get("name"), osm_hw=o.get("highway"),
                     osm_oneway=o.get("oneway"), osm_maxspeed=o.get("maxspeed"), border=r.link in bset,
                     act_ends_on_link=int(act_links.get(r.link, 0)), udzial_kier=r.udzial_kier,
                     udz_l=r.udz_lewy, udz_p=r.udz_prawy))
t = pd.DataFrame(rows)
pairs = t.groupby("nr").az.agg(lambda s: abs(((s.iloc[0] - s.iloc[1]) + 180) % 360 - 180) if len(s) == 2 else None)
t["az_diff_pair"] = t.nr.map(pairs)
pd.set_option("display.width", 250)
print(t.to_string())
t.to_csv("reports/etap2/audyt_g5/wyniki/counters_geom.csv", index=False)
