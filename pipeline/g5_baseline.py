"""G5.0: bazowa tabela model vs GPR 2025 (przed kalibracją). Bez zmian w modelu.

Użycie: uv run python -W ignore pipeline/g5_baseline.py <out_prefix> <output_dir> [<output_dir> ...]   (seedy jednego wariantu)
Cel GPR na kierunek: SDRDR (dzień roboczy; DW ma tylko SDRR) × udział pojazdów lekkich (osobowe + mikrobusy + motocykle,
ze struktury SDRR) × udział kierunku (A1 z tabeli GPR, pozostałe 0,5 = ZAŁOŻENIE z G5 §1.2).
Model: vol_car z output_links × 1/sampleSize, średnia z seedów; rozbicie wg rodzaju agenta (id: r/c/o) z eventów pierwszego seedu.
Wyjście: <out_prefix>.csv, <out_prefix>.json, <out_prefix>.png.
"""
import io
import json
import re
import sys
from collections import Counter
from pathlib import Path

import matplotlib
import pandas as pd
import zstandard
from lxml import etree

matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use("dark_background")  # ciemny motyw (prośba użytkownika)

out, runs = sys.argv[1], [Path(a) for a in sys.argv[2:]]
g = pd.read_csv("reports/g5_walidacja/gpr_linki.csv", dtype={"link": str})
g["light_share"] = g.lekkie_osob / g.sdr
g["base"] = g.sdrdr.where(g.sdrdr.notna(), g.sdr)
g["base_kind"] = g.sdrdr.notna().map({True: "SDRDR", False: "SDRR"})
g["gpr_light_dir"] = g.base * g.light_share * g.udzial_kier
g["gpr_all_dir"] = g.base * g.udzial_kier


def sample(d):
    c = etree.parse(str(d / "output_config.xml"))
    return float(c.find(".//module[@name='qsim']/param[@name='flowCapacityFactor']").get("value"))


vols = []
for d in runs:
    l = pd.read_csv(d / "output_links.csv.zst", sep=";", dtype={"link": str}).set_index("link")
    vols.append(g.link.map(l.vol_car) / sample(d))
g["model_dir"] = pd.concat(vols, axis=1).mean(axis=1)
g["model_min"], g["model_max"] = pd.concat(vols, axis=1).min(axis=1), pd.concat(vols, axis=1).max(axis=1)

want, kinds = set(g.link), Counter()
pat = re.compile(r'type="entered link" link="([^"]+)" vehicle="(.)')
with zstandard.ZstdDecompressor().stream_reader(open(runs[0] / "output_events.xml.zst", "rb")) as f:
    for line in io.TextIOWrapper(f, encoding="utf-8"):
        m = pat.search(line)
        if m and m[1] in want:
            kinds[(m[1], m[2])] += 1
s0 = sample(runs[0])
for k, name in (("r", "mieszk"), ("c", "przyj"), ("o", "wyjezdz"), ("t", "tlo")):
    g[f"model_{name}"] = g.link.map(lambda l: kinds[(l, k)] / s0)
g["ratio"] = g.model_dir / g.gpr_light_dir
g["gap_light_dir"] = g.gpr_light_dir - g.model_dir  # dobowa luka do zamknięcia (tło + inne cele podróży)
cols = ["nr", "droga", "nazwa", "rola", "link", "base_kind", "gpr_all_dir", "light_share", "gpr_light_dir", "model_dir",
        "model_min", "model_max", "model_mieszk", "model_przyj", "model_wyjezdz", "model_tlo", "ratio", "gap_light_dir"]
t = g[cols].round(3)
t.to_csv(out + ".csv", index=False, lineterminator="\n")

sec = g.groupby(["nr", "droga"], sort=False).agg(nazwa=("nazwa", "first"), gpr=("gpr_light_dir", "sum"),
                                                 model=("model_dir", "sum")).reset_index()
sec["ratio"] = sec.model / sec.gpr
sec["walidacja"] = sec.nr.isin([91124, 91866])  # D19/K4 W2: poza dopasowaniem tła
grp = lambda m: {"gpr": round(float(sec[m].gpr.sum())), "model": round(float(sec[m].model.sum())),
                 "ratio": round(float(sec[m].model.sum() / sec[m].gpr.sum()), 3)}
rep = {"runs": [str(d) for d in runs], "sections": len(sec),
       "A1": grp(sec.droga == "A1"),
       "DK_miejskie_Kutno": grp(sec.nr.isin([91124, 91866, 91869])),
       "DK_pozostale": grp(~sec.droga.isin(["A1"]) & sec.droga.str.match(r"^\d") & ~sec.nr.isin([91124, 91866, 91869])
                           & sec.nr.astype(str).str.startswith("9")),
       "DW": grp(sec.nr < 20000),
       "walidacja_poza_proba": {f"{r.droga} {r.nr}": round(float(r.ratio), 3) for r in sec[sec.walidacja].itertuples()},
       "dopasowanie": grp(~sec.walidacja),
       "per_section": sec.round(3).to_dict(orient="records")}
json.dump(rep, open(out + ".json", "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False)

fig, ax = plt.subplots(figsize=(13, 6))
sec = sec.sort_values("gpr")
lab = [f"{r.droga} {r.nr}{'  [walidacja]' if r.walidacja else ''}" for r in sec.itertuples()]
y = range(len(sec))
ax.barh([i + 0.2 for i in y], sec.gpr, height=0.4, color="#6c757d", label="GPR 2025: lekkie, oba kierunki (SDRDR; DW: SDRR)")
ax.barh([i - 0.2 for i in y], sec.model, height=0.4, color="#2e86ab", label=f"model ({len(runs)} seed(y), × 1/próbka)")
for i, r in zip(y, sec.itertuples()):
    ax.text(max(r.gpr, r.model) + 300, i, f"{r.ratio:.0%}", va="center", fontsize=8)
ax.set_yticks(list(y)); ax.set_yticklabels(lab, fontsize=8); ax.set_xlabel("poj./dobę")
ax.set_title(f"model vs GPR 2025 na 19 odcinkach: {runs[0].name}", fontsize=11)
ax.legend(fontsize=8, loc="lower right")
fig.tight_layout(); fig.savefig(out + ".png", dpi=120)
print(json.dumps({k: v for k, v in rep.items() if k != "per_section"}, ensure_ascii=False, indent=1))
print(t[["nr", "droga", "rola", "gpr_light_dir", "model_dir", "model_mieszk", "model_przyj", "model_wyjezdz", "model_tlo", "ratio"]].round(2).to_string())
