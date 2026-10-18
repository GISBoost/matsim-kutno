"""Audyt G5: które liczniki i jakie drogi obsługują największe pary O-D tła (trasy wybranych planów, ostatnia iteracja).

Użycie: uv run python reports/audyt_g5/skrypty/a5_od_routes.py <output_dir> <prefiks_pary> [...]   (np. t1002032_1002044 h1002032_1002044)
"""
import gzip
import sys
from collections import Counter
from pathlib import Path

import pandas as pd
import zstandard
from lxml import etree

run, prefixes = Path(sys.argv[1]), sys.argv[2:]
g = pd.read_csv("reports/g5_walidacja/gpr_linki.csv", dtype={"link": str})
cnt = dict(zip(g.link, g.nr))
lt, ll = {}, {}
with gzip.open("scenarios/kutno/network.xml.gz", "rb") as f:
    for _, el in etree.iterparse(f, tag="link"):
        lt[el.get("id")] = {a.get("name"): a.text for a in el.iter("attribute")}.get("type")
        ll[el.get("id")] = float(el.get("length"))
        el.clear()
res = {p: dict(n=0, hits=Counter(), km_type=Counter(), km=0.0) for p in prefixes}
for _, el in etree.iterparse(zstandard.ZstdDecompressor().stream_reader(open(run / "output_plans.xml.zst", "rb")), tag="person"):
    pid = el.get("id")
    for p in prefixes:
        if pid.startswith(p + "_"):
            pl = [x for x in el.findall("plan") if x.get("selected") == "yes"][0]
            links = (pl.find("leg[@mode='car']/route").text or "").split()[1:]
            r = res[p]
            r["n"] += 1
            for h in {cnt[l] for l in links if l in cnt}:
                r["hits"][h] += 1
            for l in links:
                r["km_type"][lt[l]] += ll[l] / 1000
                r["km"] += ll[l] / 1000
    el.clear()
for p, r in res.items():
    n = max(r["n"], 1)
    print(p, "agentów:", r["n"], "śr. km:", round(r["km"] / n, 1))
    print("  udział agentów przez licznik:", {k: round(v / n, 2) for k, v in r["hits"].most_common()})
    print("  km wg typu (udział):", {k: round(v / r["km"], 2) for k, v in r["km_type"].most_common(6)})
