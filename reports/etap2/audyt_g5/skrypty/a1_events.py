"""Audyt G5: niezależne liczniki z eventów jednego runu (bez importu kodu pipeline).

Użycie: uv run python reports/etap2/audyt_g5/skrypty/a1_events.py <output_dir> <out_json>
Liczy: entered/left per link i klasa (pierwsza litera id pojazdu), vol_car vs entered/left (konwencja),
prędkości na linkach liczników wg klasy, starty nóg car wg typu linku, nogi car z tym samym linkiem startu i końca, stuck.
"""
import gzip
import io
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
import zstandard
from lxml import etree

run, out = Path(sys.argv[1]), sys.argv[2]
g = pd.read_csv("scenarios/kutno/validation/gpr_linki.csv", dtype={"link": str})
cnt_links = set(g.link)

ltype, llen, lfs = {}, {}, {}
with gzip.open("scenarios/kutno/network.xml.gz", "rb") as f:
    for _, el in etree.iterparse(f, tag="link"):
        ltype[el.get("id")] = {a.get("name"): a.text for a in el.iter("attribute")}.get("type")
        llen[el.get("id")] = float(el.get("length"))
        lfs[el.get("id")] = float(el.get("freespeed"))
        el.clear()

ev = re.compile(r'time="([^"]+)" type="([^"]+)"(.*)')
attr = re.compile(r'(\w+)="([^"]*)"')
entered, left = Counter(), Counter()
ent_cls, left_cls = Counter(), Counter()
t_in = {}
speeds = defaultdict(list)  # (link, cls) -> m/s
dep_type = Counter()
dep_link = {}
same_link_legs = Counter()
car_legs = Counter()
stuck = Counter()
with zstandard.ZstdDecompressor().stream_reader(open(run / "output_events.xml.zst", "rb")) as fh:
    for line in io.TextIOWrapper(fh, encoding="utf-8"):
        m = ev.search(line)
        if not m:
            continue
        t, typ, rest = float(m[1]), m[2], m[3]
        if typ == "entered link" or typ == "left link":
            a = dict(attr.findall(rest))
            l, v = a["link"], a["vehicle"]
            c = v[0]
            if typ == "entered link":
                entered[l] += 1
                if l in cnt_links:
                    ent_cls[(l, c)] += 1
                    t_in[v] = (l, t)
            else:
                left[l] += 1
                if l in cnt_links:
                    left_cls[(l, c)] += 1
                    if v in t_in and t_in[v][0] == l:
                        dt = t - t_in[v][1]
                        if dt > 0:
                            speeds[(l, c)].append(llen[l] / dt)
                t_in.pop(v, None)
        elif typ == "departure" and 'legMode="car"' in rest:
            a = dict(attr.findall(rest))
            car_legs[a["person"][0]] += 1
            dep_type[(a["person"][0], ltype.get(a["link"]))] += 1
            dep_link[a["person"]] = a["link"]
        elif typ == "arrival" and 'legMode="car"' in rest:
            a = dict(attr.findall(rest))
            if dep_link.get(a["person"]) == a["link"]:
                same_link_legs[a["person"][0]] += 1
        elif "stuck" in typ:
            stuck[typ] += 1

links = pd.read_csv(run / "output_links.csv.zst", sep=";", dtype={"link": str}).set_index("link")
cmp = pd.DataFrame({"vol_car": links.vol_car, "entered": pd.Series(entered), "left": pd.Series(left)}).fillna(0)
conv = {"vol_eq_entered": int((cmp.vol_car == cmp.entered).sum()), "vol_eq_left": int((cmp.vol_car == cmp.left).sum()),
        "links": len(cmp), "sum_vol": int(cmp.vol_car.sum()), "sum_entered": int(cmp.entered.sum()), "sum_left": int(cmp.left.sum())}
sp = {f"{l}|{c}": {"n": len(v), "median_kmh": round(float(pd.Series(v).median() * 3.6), 1),
                    "freespeed_kmh": round(lfs[l] * 3.6, 1), "type": ltype[l]} for (l, c), v in speeds.items()}
rep = {"run": str(run), "car_legs_by_class": dict(car_legs), "stuck": dict(stuck), "vol_car_convention": conv,
       "counter_entered_by_class": {f"{l}|{c}": n for (l, c), n in ent_cls.items()},
       "counter_left_by_class": {f"{l}|{c}": n for (l, c), n in left_cls.items()},
       "speeds_on_counters": sp,
       "car_departures_by_class_linktype": {f"{c}|{t}": n for (c, t), n in sorted(dep_type.items(), key=lambda x: -x[1])},
       "car_legs_same_start_end_link": dict(same_link_legs)}
json.dump(rep, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps({k: v for k, v in rep.items() if k not in ("counter_entered_by_class", "counter_left_by_class", "speeds_on_counters")}, indent=1))
