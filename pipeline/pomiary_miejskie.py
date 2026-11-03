"""Model vs pomiary WIOŚ 2013 na ulicach Kutna (K1–K5), cel przeskalowany do 2025 (S1, reports/etap3/g_pomiary_miejskie/wios2013.py).

Użycie: uv run python -W ignore pipeline/pomiary_miejskie.py <out_prefix> <output_dir> [<output_dir> ...]   (seedy jednego wariantu)
Model: wjazdy na linki przekroju (oba kierunki) z eventów × 1/próbka, osobno lekkie (r/c/o/t) i ciężkie (h), średnia i rozrzut seedów.
Cel 2025 = doba 2013 × f: f_suma (suma korytarzy DK, wariant główny) i f_s1 (korytarz kierunku punktu, wariant).
Wyjście: <out_prefix>.csv, <out_prefix>.json. To kontrola rzędu wielkości (pomiar jednodobowy, rozrzut doby K1 ±35%), nie kalibracja.
"""
import io
import json
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd
import zstandard
from lxml import etree

out, runs = sys.argv[1], [Path(a) for a in sys.argv[2:]]
w = pd.read_csv("scenarios/kutno/validation/wios2013_linki.csv", dtype={"link": str})
want, pat = set(w.link), re.compile(r'type="entered link" link="([^"]+)" vehicle="(.)')


def sample(d):
    c = etree.parse(str(d / "output_config.xml"))
    return float(c.find(".//module[@name='qsim']/param[@name='flowCapacityFactor']").get("value"))


def counts(d):
    c = Counter()
    with zstandard.ZstdDecompressor().stream_reader(open(d / "output_events.xml.zst", "rb")) as f:
        for line in io.TextIOWrapper(f, encoding="utf-8"):
            m = pat.search(line)
            if m and m[1] in want:
                c[(m[1], "h" if m[2] == "h" else "l")] += 1
    return c


per_run = []
for d in runs:
    c, s = counts(d), sample(d)
    per_run.append(w.assign(lekkie=w.link.map(lambda l: c[(l, "l")] / s), ciezkie=w.link.map(lambda l: c[(l, "h")] / s))
                    .groupby("pkt")[["lekkie", "ciezkie"]].sum())
m = pd.concat(per_run, keys=range(len(runs)))
m["razem"] = m.lekkie + m.ciezkie
pts = w.groupby("pkt").first()[["ulica", "doba_2013", "ciezkie_proc", "korytarz", "f_s1", "f_suma"]]
t = pts.join(m.groupby(level=1).mean().add_prefix("model_")).join(m.razem.groupby(level=1).agg(["min", "max"]).add_prefix("model_razem_"))
t["cel_2025"] = t.doba_2013 * t.f_suma
t["cel_2025_korytarz"] = t.doba_2013 * t.f_s1
t["model_proc_celu"] = 100 * t.model_razem / t.cel_2025
t["model_proc_celu_korytarz"] = 100 * t.model_razem / t.cel_2025_korytarz
t["model_ciezkie_proc"] = 100 * t.model_ciezkie / t.model_razem
t.round(3).to_csv(out + ".csv", lineterminator="\n")
rank = lambda s: list(s.sort_values(ascending=False).index)
rep = {"runs": [str(d) for d in runs], "punkty": t.round(1).reset_index().to_dict(orient="records"),
       "suma": {"cel_2025": round(float(t.cel_2025.sum())), "model": round(float(t.model_razem.sum())),
                "model_proc_celu": round(float(100 * t.model_razem.sum() / t.cel_2025.sum()), 1)},
       "kolejnosc_pomiar": rank(t.doba_2013), "kolejnosc_model": rank(t.model_razem)}
json.dump(rep, open(out + ".json", "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False)
print(t[["ulica", "doba_2013", "cel_2025", "cel_2025_korytarz", "model_razem", "model_razem_min", "model_razem_max",
         "model_proc_celu", "ciezkie_proc", "model_ciezkie_proc"]].round(1).to_string())
print(json.dumps({k: rep[k] for k in ("suma", "kolejnosc_pomiar", "kolejnosc_model")}, ensure_ascii=False))
