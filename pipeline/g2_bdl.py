"""Pomocnik do BDL API (bez klucza): python pipeline/g2_bdl.py units|subj|vars|data ..."""
import sys, json, urllib.request, urllib.parse
B = "https://bdl.stat.gov.pl/api/v1/"
def get(path, **kw):
    kw.update(format="json", lang="pl")
    url = B + path + "?" + urllib.parse.urlencode(kw, doseq=True)
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.load(r)
if __name__ == "__main__":
    cmd, *a = sys.argv[1:]
    if cmd == "units":
        for r in get("units/search", name=a[0], level=a[1], **{"page-size": 50})["results"]: print(r["id"], r["name"], r["parentId"])
    elif cmd == "subj":
        for r in get("subjects/search", name=a[0], **{"page-size": 50})["results"]: print(r["id"], r["levels"], r["name"][:160])
    elif cmd == "vars":  # subject-id
        for r in get("variables", **{"subject-id": a[0], "page-size": 100})["results"]: print(r["id"], r.get("n1"), "|", r.get("n2"), "|", r.get("measureUnitName"), r.get("level"))
    elif cmd == "data":  # var-id unit-id years...
        d = get(f"data/by-variable/{a[0]}", **{"unit-id": a[1], "year": a[2:], "page-size": 100})
        print(json.dumps(d["results"], ensure_ascii=False, indent=1))
