"""Pobiera z BDL (bez klucza) dane dla Kutna (miasto 051011902011) i zapisuje JSON do data/raw/g2/bdl_kutno.json."""
import json, pathlib
from g2_bdl import get
U = "051011902011"
VARS = {"P4508 ogółem (siedziba pracy głównej)": 1735396, "P4508 mężczyźni": 1735397, "P4508 kobiety": 1735398,
        "P4507 ogółem wg miejsca zamieszkania": 1735394, "P4507 w podmiotach ≤5 pracujących": 1735395}
out = {}
for k, v in VARS.items():
    d = get(f"data/by-unit/{U}", **{"var-id": v, "year": [2023, 2024, 2025]})
    out[k] = [{x["id"]: [(y["year"], y["val"]) for y in x["values"]]} for x in d["results"]]
    print(k, out[k])
p = pathlib.Path(__file__).parents[1] / "data/raw/g2/bdl_kutno.json"
p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
