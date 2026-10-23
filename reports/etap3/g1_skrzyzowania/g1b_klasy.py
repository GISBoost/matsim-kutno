"""G1b: klasyfikacja węzłów sieci R8 wg tagów OSM i rang dróg. Użycie: uv run python -W ignore g1b_klasy.py"""
import gzip, json
from collections import Counter
from pathlib import Path
import osmium, pyproj
from lxml import etree

net = etree.parse(gzip.open("scenarios/kutno/network.xml.gz")).getroot()
nodes = {n.get("id"): (float(n.get("x")), float(n.get("y"))) for n in net.iter("node")}
links = {}
for l in net.iter("link"):
    a = {x.get("name"): x.text for x in l.iter("attribute")}
    links[l.get("id")] = dict(f=l.get("from"), t=l.get("to"), cap=float(l.get("capacity")), hw=a.get("type"), way=a.get("origid"))
RANK = {"motorway": 6, "motorway_link": 6, "trunk": 5, "trunk_link": 5, "primary": 4, "primary_link": 4, "secondary": 3, "secondary_link": 3,
        "tertiary": 2, "tertiary_link": 2, "unclassified": 1, "residential": 1, "living_street": 0}
inn, out = {}, {}
for k, v in links.items():
    inn.setdefault(v["t"], []).append(k); out.setdefault(v["f"], []).append(k)
tr = pyproj.Transformer.from_crs(4326, 2180, always_xy=True)
class H(osmium.SimpleHandler):
    def __init__(s): super().__init__(); s.tag = {}; s.pos = {}
    def node(s, n):
        hw = n.tags.get("highway"); rw = n.tags.get("railway")
        if hw in ("traffic_signals", "give_way", "stop", "mini_roundabout") or n.tags.get("traffic_signals"):
            s.tag[n.id] = hw or "traffic_signals"; s.pos[n.id] = tr.transform(n.location.lon, n.location.lat)
h = H(); h.apply_file(str(next(Path("data/raw/osm").glob("lodzkie-*.osm.pbf"))), locations=True)
xy = list(nodes.items())
def nearest(p, r=30):
    best = min(xy, key=lambda kv: (kv[1][0]-p[0])**2 + (kv[1][1]-p[1])**2)
    d = ((best[1][0]-p[0])**2 + (best[1][1]-p[1])**2) ** .5
    return best[0] if d <= r else None
cls = {}  # węzeł sieci -> klasa
for oid, t in h.tag.items():
    nid = str(oid) if str(oid) in nodes else nearest(h.pos[oid])
    if nid: cls.setdefault(nid, set()).add(t)
res = Counter(); inflow = Counter(); caps = {}
for n, ts in cls.items():
    ins = inn.get(n, [])
    if len(ins) < 2: res["pominięte: <2 wloty (ślepy/przejście)"] += 1; continue
    mx = max(RANK.get(links[i]["hw"], 1) for i in ins)
    for t in ts:
        res[t] += 1
        for i in ins:
            lo = RANK.get(links[i]["hw"], 1) < mx
            key = f"{t}|{'podporządkowany' if lo else 'główny/równorzędny'}"
            inflow[key] += 1; caps.setdefault(key, []).append(links[i]["cap"])
print("węzły z tagiem po mapowaniu:", len(cls), dict(res))
for k, v in sorted(inflow.items()): print(k, v, "cap mediana", sorted(caps[k])[len(caps[k])//2])
# równorzędne bez znaków: węzły stopnia >=3 w mieście bez tagu
untag = [n for n in nodes if n not in cls and len(inn.get(n, [])) >= 3]
print("skrzyżowania 3+ wloty bez tagu:", len(untag), "wszystkich 3+:", sum(1 for n in nodes if len(inn.get(n, [])) >= 3))
json.dump({"tagowane": dict(res), "wloty": dict(inflow)}, open("reports/etap3/g1_skrzyzowania/g1b_klasy.json", "w"), ensure_ascii=False, indent=1)
