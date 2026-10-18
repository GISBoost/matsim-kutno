"""Niezależna kontrola mediany model/dostawca i MAPE (prompt §8). Nie importuje pipeline/; czyta pliki modelu sam,
wartości dostawcy dostaje przez stdin (JSON, tylko w pamięci, D22 wariant A). Wynik: JSON na stdout.
Tylko grupa „wszystkie”: swobodny_model (okno rano), okno_vs_hist (każde okno), segment_freeflow."""
import csv
import json
import statistics
import sys
from pathlib import Path

D = Path(__file__).parent
inp = json.load(sys.stdin)
zestaw = {r["id"]: r["zestaw"] for r in csv.DictReader(open(D / "split.csv", encoding="utf-8"))}
model = {(r["id"], r["okno"]): r for r in csv.DictReader(open(D / "model_times.csv", encoding="utf-8"))}
seg = {r["id"]: float(r["freespeed_kmh"]) for r in csv.DictReader(open(D / "segments.csv", encoding="utf-8"))}
acc = {}
for r in inp["trasy"]:
    m = model[(r["id"], r["okno"])]
    z = zestaw[r["id"]]
    acc.setdefault(f"okno_vs_hist|{z}|wszystkie|{r['okno']}", []).append((float(m["model_med"]), r["hist_s"]))
    if r["okno"] == "rano":
        acc.setdefault(f"swobodny_model|{z}|wszystkie|-", []).append((float(m["ff_model_s"]), r["free_s"]))
for r in inp["segmenty"]:
    acc.setdefault(f"segment_freeflow|{zestaw[r['id']]}|wszystkie|-", []).append((seg[r["id"]], r["dost_free_kmh"]))
out = {k: {"mediana_model_do_dost": statistics.median(a / b for a, b in v),
           "MAPE_pct": 100 * sum(abs(a - b) / b for a, b in v) / len(v)} for k, v in acc.items()}
print(json.dumps(out))
