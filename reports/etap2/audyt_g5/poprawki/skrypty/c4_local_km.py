"""Kontrola S2 (krok 4): udział km na drogach bez licznika GPR wg rodzaju agenta, z eventów runu (entered link × długość linku).

Użycie: uv run python reports/etap2/audyt_g5/poprawki/skrypty/c4_local_km.py <output_dir> [...]
Rodzaj = pierwsza litera id pojazdu (r/c/o pracujący, t tło lekkie, h ciężkie). Bez importu z pipeline/.
"""
import io
import json
import re
import sys
from collections import Counter
from pathlib import Path

import zstandard
from lxml import etree

LOCAL = {"tertiary", "tertiary_link", "unclassified", "residential", "living_street", "service"}
res = {}
for d in map(Path, sys.argv[1:]):
    L = {}
    for _, el in etree.iterparse(zstandard.ZstdDecompressor().stream_reader(open(d / "output_network.xml.zst", "rb")), tag="link"):
        t = next((a.text for a in el.iter("attribute") if a.get("name") == "type"), None)
        L[el.get("id")] = (float(el.get("length")), t in LOCAL)
        el.clear()
    km, loc = Counter(), Counter()
    pat = re.compile(r'type="entered link" link="([^"]+)" vehicle="(.)')
    with zstandard.ZstdDecompressor().stream_reader(open(d / "output_events.xml.zst", "rb")) as f:
        for line in io.TextIOWrapper(f, encoding="utf-8"):
            m = pat.search(line)
            if m:
                ln, lo = L[m[1]]
                km[m[2]] += ln
                loc[m[2]] += ln * lo
    res[str(d)] = {k: {"km_sample": round(km[k] / 1000), "local_share": round(loc[k] / km[k], 3)} for k in sorted(km)}
    w = "rco"
    res[str(d)]["pracujacy"] = round(sum(loc[k] for k in w) / sum(km[k] for k in w), 3)
    print(d, res[str(d)])
json.dump(res, open("reports/etap2/audyt_g5/poprawki/k4_od/c4_local_km.json", "w", encoding="utf-8"), indent=1)
