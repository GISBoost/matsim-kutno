"""Ile przejazdów w runie łamie zakazy skrętu z OSM (konwerter sieci ich nie czyta, DisallowedNextLinks puste).

Użycie: uv run python -W ignore pipeline/turn_violations.py <output_dir> <out_prefix> [link_id ...]   (linki do rozbicia, np. liczniki GPR)
Zakazy: relacje OSM type=restriction (from way, via node, to way) z data/raw/osm/lodzkie-*.osm.pbf.
no_*  -> zakazana para (link drogi from kończący się w via, link drogi to zaczynający się w via);
only_* -> zakazane wszystkie inne wyjazdy z via dla linku drogi from. Węzły sieci = id węzłów OSM (Supersonic), link.origid = id drogi.
Pomijam relacje z via = droga (rzadkie) i zakazy z wyjątkami tylko dla innych pojazdów (restriction:hgv itp.).
Wyjście: <out_prefix>.json (liczba zakazanych przejść w sieci, przejazdy łamiące, top par, udział na wskazanych linkach).
"""
import io
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import osmium
import pandas as pd
import zstandard

run, out, watch = Path(sys.argv[1]), sys.argv[2], set(sys.argv[3:])
L = pd.read_csv(run / "output_links.csv.zst", sep=";", dtype={"link": str, "from_node": str, "to_node": str})
L = L[L.origid.notna()].assign(way=lambda d: d.origid.astype("int64").astype(str))
ends_at = defaultdict(list)    # (way, via) -> linki drogi way kończące się w via
starts_at = defaultdict(list)  # (way, via) -> linki drogi way zaczynające się w via
out_of = defaultdict(list)     # via -> wszystkie linki wychodzące z via
for r in L.itertuples():
    ends_at[(r.way, r.to_node)].append(r.link)
    starts_at[(r.way, r.from_node)].append(r.link)
    out_of[r.from_node].append(r.link)


class H(osmium.SimpleHandler):
    def __init__(s):
        super().__init__()
        s.rel = []

    def relation(s, r):
        if r.tags.get("type") != "restriction":
            return
        kind = r.tags.get("restriction") or r.tags.get("restriction:motorcar")
        if not kind:
            return
        m = {"from": [], "to": [], "via": []}
        for x in r.members:
            if x.role in m:
                m[x.role].append((x.type, str(x.ref)))
        if len(m["via"]) == 1 and m["via"][0][0] == "n" and m["from"] and m["to"]:
            s.rel.append((r.id, kind, m["from"][0][1], m["via"][0][1], m["to"][0][1]))


h = H()
h.apply_file(next(Path("data/raw/osm").glob("lodzkie-*.osm.pbf")))
forbid = {}  # (link_in, link_out) -> (rel_id, kind)
for rid, kind, fw, via, tw in h.rel:
    ins = ends_at.get((fw, via), [])
    if not ins:
        continue
    tos = set(starts_at.get((tw, via), []))
    if kind.startswith("no_"):
        bad = tos
    elif kind.startswith("only_"):
        bad = set(out_of.get(via, [])) - tos
    else:
        continue
    for a in ins:
        for b in bad:
            forbid[(a, b)] = (rid, kind)

pat = re.compile(r'type="(entered link|vehicle enters traffic|vehicle leaves traffic)"[^>]*?(?:link="([^"]+)"[^>]*vehicle="([^"]+)"|person="[^"]+" link="([^"]+)" vehicle="([^"]+)")')
last, viol, trips, viol_trips, kinds = {}, Counter(), 0, set(), Counter()
trip_viol, watch_tot, watch_viol = {}, Counter(), Counter()
trip_links = defaultdict(list)
with zstandard.ZstdDecompressor().stream_reader(open(run / "output_events.xml.zst", "rb")) as f:
    for line in io.TextIOWrapper(f, encoding="utf-8"):
        m = pat.search(line)
        if not m:
            continue
        typ, link, veh = m[1], m[2] or m[4], m[3] or m[5]
        if typ == "vehicle enters traffic":
            trips += 1
            last[veh], trip_viol[veh], trip_links[veh] = link, False, []
        elif typ == "entered link":
            if (last.get(veh), link) in forbid:
                viol[(last[veh], link)] += 1
                trip_viol[veh] = True
            last[veh] = link
            trip_links[veh].append(link)
        else:
            if trip_viol.pop(veh, False):
                viol_trips.add(veh)
                kinds[veh[0]] += 1
            for l in set(trip_links.pop(veh, [])) & watch:
                watch_tot[l] += 1
                watch_viol[l] += 1 if veh in viol_trips and kinds else 0
            last.pop(veh, None)

rep = {"run": str(run), "restrictions_osm_via_node": len(h.rel), "forbidden_link_pairs_in_network": len(forbid),
       "car_trips": trips, "violating_transitions": int(sum(viol.values())),
       "violating_trips_by_kind_last_trip": dict(kinds),
       "top_pairs": [dict(link_in=a, link_out=b, n=n, rel=forbid[(a, b)][0], kind=forbid[(a, b)][1]) for (a, b), n in viol.most_common(15)],
       "watch_links": {l: {"traversals": watch_tot[l]} for l in watch}}
json.dump(rep, open(out + ".json", "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False)
print(json.dumps({k: v for k, v in rep.items() if k != "top_pairs"}, ensure_ascii=False, indent=1))
for p in rep["top_pairs"]:
    print(p)
