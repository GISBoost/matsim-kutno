"""G1 audyt geometrii skrzyżowań (D26, bez zmian modelu): (1) węzły sieci = węzły OSM (id i położenie), (2) ronda: linki, jednokierunkowość,
(3) zawrotki w runach: przejścia link -> link odwrotny (te same końce) wg stopnia węzła. Użycie: uv run python -W ignore g1_audyt.py <run_dir> [<run_dir> ...]"""
import gzip
import io
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

import osmium
import pyproj
import zstandard

H = Path("reports/etap3/g1_skrzyzowania")
t = ET.parse(gzip.open("scenarios/kutno/network.xml.gz"))
nodes = {n.get("id"): (float(n.get("x")), float(n.get("y"))) for n in t.iter("node")}
links = {}
for l in t.iter("link"):
    a = {x.get("name"): x.text for x in l.iter("attribute")}
    links[l.get("id")] = (l.get("from"), l.get("to"), a.get("origid"), a.get("type"))
inn, out = Counter(), Counter()
for f, to, *_ in links.values():
    out[f] += 1; inn[to] += 1
tr = pyproj.Transformer.from_crs(4326, 2180, always_xy=True)


class Hd(osmium.SimpleHandler):
    def __init__(s):
        super().__init__(); s.pos = {}; s.ra = set()
    def node(s, n):
        if str(n.id) in nodes:
            s.pos[str(n.id)] = (n.location.lon, n.location.lat)
    def way(s, w):
        if w.tags.get("junction") in ("roundabout", "circular"):
            s.ra.add(str(w.id))


h = Hd(); h.apply_file(str(next(Path("data/raw/osm").glob("lodzkie-*.osm.pbf"))), locations=False)
missing = [n for n in nodes if n not in h.pos]
dist = [((tr.transform(*h.pos[n])[0] - x) ** 2 + (tr.transform(*h.pos[n])[1] - y) ** 2) ** .5 for n, (x, y) in nodes.items() if n in h.pos]
ra_links = [k for k, v in links.items() if v[2] in h.ra]
pair = {(f, to): k for k, (f, to, *_) in links.items()}
ra_with_reverse = [k for k in ra_links if (links[k][1], links[k][0]) in pair]
rep = {"wezly_sieci": len(nodes), "wezly_bez_odpowiednika_w_OSM": len(missing), "maks_przesuniecie_m": round(max(dist), 3),
       "ronda_drogi_OSM_w_sieci": len({links[k][2] for k in ra_links}), "ronda_linki": len(ra_links), "ronda_linki_z_odwrotnym": len(ra_with_reverse),
       "stopnie_wezlow_in_out": {f"{a}/{b}": c for (a, b), c in Counter((inn[n], out[n]) for n in nodes).most_common(8)}}
for rd in sys.argv[1:]:
    pat = re.compile(r'type="(entered link|vehicle enters traffic|vehicle leaves traffic)"[^>]*?(?:link="([^"]+)"[^>]*vehicle="([^"]+)"|person="[^"]+" link="([^"]+)" vehicle="([^"]+)")')
    cur, trips, uturn, kinds, pos = {}, 0, Counter(), Counter(), Counter()
    def close(seq):
        for i in range(1, len(seq)):
            p, lk = seq[i - 1], seq[i]
            if p in links and lk in links and links[p][0] == links[lk][1] and links[p][1] == links[lk][0]:
                n = links[p][1]
                uturn[p, lk] += 1
                kinds["slepy koniec (1/1)" if (inn[n], out[n]) == (1, 1) else "wezel 2/2 (zwykly wezel drogi)" if (inn[n], out[n]) == (2, 2) else "skrzyzowanie (stopien 3+)"] += 1
                pos["poczatek trasy (pierwsze 3 linki)" if i <= 2 else "koniec trasy (ostatnie 3 linki)" if i >= len(seq) - 2 else "srodek trasy"] += 1
    with zstandard.ZstdDecompressor().stream_reader(open(Path(rd) / "output_events.xml.zst", "rb")) as f:
        for line in io.TextIOWrapper(f, encoding="utf-8"):
            m = pat.search(line)
            if not m:
                continue
            typ, lk, veh = m[1], m[2] or m[4], m[3] or m[5]
            if typ == "vehicle enters traffic":
                trips += 1; cur[veh] = [lk]
            elif typ == "entered link":
                cur.setdefault(veh, []).append(lk)
            else:
                close(cur.pop(veh, []))
    rep[Path(rd).name] = {"podroze_car": trips, "zawrotki": int(sum(uturn.values())), "zawrotki_na_1000_podrozy": round(sum(uturn.values()) / trips * 1000, 2),
                          "wg_wezla": dict(kinds), "wg_polozenia_w_trasie": dict(pos), "top_pary": [[a, b, n] for (a, b), n in uturn.most_common(5)]}
json.dump(rep, open(H / "g1_audyt.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps(rep, indent=1, ensure_ascii=False))
