"""Inwarianty runu (instrukcja §3.4) bez importu z pipeline/: pojazdy z pliku (pce, 80 km/h), rozłączne id r/c/o/t/h,
starty z jezdni A1 tylko z wjazdów granicznych, liczba nóg car = 2 × pracujący + tło + ciężkie, liczba tła = round(Σ macierzy × 0,25).

Użycie: uv run python -W ignore reports/etap2/audyt_g5/poprawki/skrypty/c8_invariants.py <output_dir> <macierz_lcv> <macierz_heavy>
"""
import io
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd
import zstandard
from lxml import etree

d, lcv, heavy = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
z = lambda p: zstandard.ZstdDecompressor().stream_reader(open(p, "rb"))
ns = "{http://www.matsim.org/files/dtd}"
vt, veh = {}, {}
for _, el in etree.iterparse(z(d / "output_vehicles.xml.zst"), tag=(ns + "vehicleType", ns + "vehicle")):
    if el.tag == ns + "vehicleType":
        mv = el.find(ns + "maximumVelocity")
        vt[el.get("id")] = (float(el.find(ns + "passengerCarEquivalents").get("pce")), float(mv.get("meterPerSecond")) if mv is not None else None)
    else:
        veh[el.get("id")] = el.get("type")
types = Counter((v[0], veh_t) for v, veh_t in ((k, t) for k, t in veh.items()))
ok_veh = all(t == ("ciezki" if v.startswith("h") else "car") for v, t in veh.items()) and vt["ciezki"][0] == 2.5 \
    and abs(vt["ciezki"][1] * 3.6 - 80) < 0.01 and vt["car"][0] == 1.0
kinds = Counter(v[0] for v in veh)
link_type = {}
for _, el in etree.iterparse(z(d / "output_network.xml.zst"), tag="link"):
    link_type[el.get("id")] = next((a.text for a in el.iter("attribute") if a.get("name") == "type"), None)
    el.clear()
bz = set(pd.read_csv("scenarios/kutno/demand/border_links.csv").link)
pat = re.compile(r'type="vehicle enters traffic"[^>]*?(?:link="([^"]+)"[^>]*vehicle="([^"]+)"|vehicle="([^"]+)"[^>]*link="([^"]+)")')
legs, bad_a1 = Counter(), 0
with z(d / "output_events.xml.zst") as f:
    for line in io.TextIOWrapper(f, encoding="utf-8"):
        m = pat.search(line)
        if m:
            link, v = (m[1], m[2]) if m[1] else (m[4], m[3])
            legs[v[0]] += 1
            bad_a1 += link_type[link] == "motorway" and link not in bz
exp_t = round(pd.read_csv(lcv).trips_day.sum() * 0.25)
exp_h = round(pd.read_csv(heavy).trips_day.sum() * 0.25)
workers = kinds["r"] + kinds["c"] + kinds["o"]
r = {"vehicle_types": vt, "vehicles_by_prefix": dict(kinds), "vehicles_ok": ok_veh,
     "prefixes_only_rcoth": set(kinds) <= set("rcoth"),
     "legs_by_prefix": dict(legs), "legs_total": sum(legs.values()), "legs_expected": 2 * workers + kinds["t"] + kinds["h"],
     "tlo_agents": kinds["t"], "tlo_expected": exp_t, "heavy_agents": kinds["h"], "heavy_expected": exp_h,
     "starts_on_A1_not_border": bad_a1}
r["ok"] = (ok_veh and r["prefixes_only_rcoth"] and r["legs_total"] == r["legs_expected"] and kinds["t"] == exp_t
           and kinds["h"] == exp_h and bad_a1 == 0 and all(legs[k] == 2 * kinds[k] for k in "rco"))
print(d, r)
sys.exit(0 if r["ok"] else 1)
