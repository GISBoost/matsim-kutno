"""BDL: podmioty REGON wg klas wielkości (P2613, 'rok') i pracujący wg sekcji PKD, NSP 2021 (P4500/P4502, powiat)."""
import json, pathlib
from g2_bdl import get
out = {}
names = {74107:"ogółem",74105:"0-9",74103:"10-49",74101:"50-249",74099:"250-999",74097:"1000+"}
for v, n in names.items():
    d = get("data/by-unit/051011902011", **{"var-id": v, "year": list(range(2015, 2026))})
    out[f"P2613 podmioty {n}"] = {y["year"]: y["val"] for x in d["results"] for y in x["values"]}
for sub, uid in (("P4500", 5), ("P4502", 5)):
    vs = get("variables", **{"subject-id": sub, "page-size": 100})["results"]
    for r in vs:
        d = get(f"data/by-unit/051011902000", **{"var-id": r["id"], "year": 2021})
        out[f"{sub} powiat kutnowski | {r['n1']}"] = {y["year"]: y["val"] for x in d["results"] for y in x["values"]}
pathlib.Path(__file__).parents[1].joinpath("data/raw/g2/bdl_podmioty_pkd.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
for k, v in out.items(): print(k, v)
