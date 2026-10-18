"""Audyt G5: suma opóźnień przy różnych definicjach czasu swobodnego (niezależnie od link_delay.py / queues.py).

Użycie: uv run python reports/etap2/audyt_g5/skrypty/a2_delay.py <output_dir> <out_json>
Przejazd pośredni = entered -> left tego samego linku (bez linku startu, bez linku końca).
ff = length / min(freespeed, vmax klasy) (h: 80 km/h). Warianty opóźnienia:
  raw   = max(0, dt - ff)            (jak link_delay.py)
  m1    = max(0, dt - ff - 1)        (jak queues.py: +1 s na węzeł)
  qsim  = max(0, dt - (floor(ff)+1)) (najkrótszy możliwy czas przejazdu przy kroku 1 s, jeśli QSim zaokrągla w dół i dodaje 1 s)
Plus rozkład dt - ff w nocy (0-5 h), żeby zobaczyć, jaki jest najkrótszy czas przejazdu w pustej sieci.
"""
import io
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

import zstandard
from lxml import etree

d, out = Path(sys.argv[1]), sys.argv[2]
L = {}
for _, el in etree.iterparse(zstandard.ZstdDecompressor().stream_reader(open(d / "output_network.xml.zst", "rb")), tag="link"):
    L[el.get("id")] = (float(el.get("length")), float(el.get("freespeed")))
    el.clear()
pat = re.compile(r'time="([\d.]+)" type="(entered link|left link|vehicle leaves traffic)"[^>]*?(?:link="([^"]+)" )?vehicle="([^"]+)"')
enter = {}
tot = Counter()
night = Counter()
n = 0
with zstandard.ZstdDecompressor().stream_reader(open(d / "output_events.xml.zst", "rb")) as f:
    for line in io.TextIOWrapper(f, encoding="utf-8"):
        m = pat.search(line)
        if not m:
            continue
        t, typ, link, v = float(m[1]), m[2], m[3], m[4]
        if typ == "entered link":
            enter[v] = (link, t)
        elif typ == "vehicle leaves traffic":
            enter.pop(v, None)
        elif v in enter and enter[v][0] == link:
            lk, t0 = enter.pop(v)
            ln, fs = L[lk]
            ff = ln / min(fs, 80 / 3.6) if v[0] == "h" else ln / fs
            dt = t - t0
            n += 1
            tot["raw"] += max(0.0, dt - ff)
            tot["m1"] += max(0.0, dt - ff - 1)
            tot["qsim"] += max(0.0, dt - (math.floor(ff) + 1))
            if t0 < 5 * 3600:
                night[round(dt - ff, 1) if dt - ff < 3 else 3.0] += 1
rep = {"run": str(d), "traversals": n, "delay_veh_h": {k: round(v / 3600, 1) for k, v in tot.items()},
       "night_dt_minus_ff_hist": {str(k): v for k, v in sorted(night.items())[:40]},
       "night_share_dt_minus_ff_in_0_1": round(sum(v for k, v in night.items() if 0 <= k <= 1) / max(1, sum(night.values())), 4)}
json.dump(rep, open(out, "w", encoding="utf-8"), indent=1)
print(json.dumps({k: v for k, v in rep.items() if k != "night_dt_minus_ff_hist"}, indent=1))
