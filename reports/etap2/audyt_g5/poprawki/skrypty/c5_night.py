"""Kontrola I1 (krok 5): najkrótszy czas przejazdu linku w QSim. Przejazdy pośrednie 0-5 h (pusta sieć) z eventów.

Użycie: uv run python reports/etap2/audyt_g5/poprawki/skrypty/c5_night.py <output_dir>
Dla każdej definicji czasu swobodnego (ff, ff + 1, floor(ff) + 1; ciężkie z min(v, 80 km/h)) rozkład dt - czas swobodny. Bez pipeline/.
"""
import io
import math
import re
import sys
from pathlib import Path

import numpy as np
import zstandard
from lxml import etree

d = Path(sys.argv[1])
L = {}
for _, el in etree.iterparse(zstandard.ZstdDecompressor().stream_reader(open(d / "output_network.xml.zst", "rb")), tag="link"):
    L[el.get("id")] = (float(el.get("length")), float(el.get("freespeed")))
    el.clear()
pat = re.compile(r'time="([\d.]+)" type="(entered link|left link|vehicle leaves traffic)"[^>]*?(?:link="([^"]+)"[^>]*vehicle="([^"]+)"|vehicle="([^"]+)"[^>]*link="([^"]+)")')
enter, rows = {}, []
with zstandard.ZstdDecompressor().stream_reader(open(d / "output_events.xml.zst", "rb")) as f:
    for line in io.TextIOWrapper(f, encoding="utf-8"):
        m = pat.search(line)
        if not m:
            continue
        t = float(m[1])
        if t > 5 * 3600:
            break
        link, veh = (m[3], m[4]) if m[3] else (m[6], m[5])
        if m[2] == "entered link":
            enter[veh] = (link, t)
        elif m[2] == "left link" and veh in enter and enter[veh][0] == link:
            ln, v = L[link]
            ff = ln / (min(v, 80 / 3.6) if veh[0] == "h" else v)
            rows.append((t - enter[veh][1], ff))
            enter.pop(veh)
        else:
            enter.pop(veh, None)
a = np.array(rows)
dt, ff = a[:, 0], a[:, 1]
for name, fr in (("ff", ff), ("ff+1", ff + 1), ("floor(ff)+1", np.floor(ff) + 1)):
    x = dt - fr
    print(f"{name:12s} n={len(x)} mediana={np.median(x):.3f} p01={np.quantile(x, .01):.3f} p99={np.quantile(x, .99):.3f} "
          f"udział |x|<1e-6: {np.mean(np.abs(x) < 1e-6):.3f}  udział x<-1e-6: {np.mean(x < -1e-6):.3f}  suma x>0 [h]: {x[x > 0].sum() / 3600:.2f}")
