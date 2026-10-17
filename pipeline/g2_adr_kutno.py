"""Wycina z krajowego GeoJSON statystycznych punktów adresowych (GUS ADR, 1.01.2026) punkty gm. Kutno (TERYT 1002011)
-> data/raw/g2/adr_kutno_2026_0.csv (EPSG:2180). Strumieniowo, plik krajowy ma 3,3 GB po rozpakowaniu."""
import zipfile, json, csv, io, collections
Z = "data/raw/g2/ADR_NOBC_2026_0_GJ.zip"; OUT = "data/raw/g2/adr_kutno_2026_0.csv"
rows = []; n = 0
with zipfile.ZipFile(Z) as z, z.open(z.namelist()[0]) as f:
    for line in io.TextIOWrapper(f, encoding="utf-8", errors="replace"):
        n += 1
        if '"TERYT": "1002011"' not in line: continue
        p = json.loads(line.strip().rstrip(","))["properties"]; rows.append(p)
keys = ["NPAD_ID","REJ","OBW","MSC","ULICA","NRADR","X","Y","TERYT"]
with open(OUT, "w", newline="", encoding="utf-8") as g:
    w = csv.DictWriter(g, keys, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
print("linie", n, "punkty Kutno", len(rows), "obwody", len({(r['REJ'], r['OBW']) for r in rows}))
print(collections.Counter(r["MSC"] for r in rows).most_common(5))
