"""Kontrola I4 (niezależna od pipeline/): udziały wag a priori wjazdów per droga przed (capacity per link) i po (GPR per droga).

Użycie: uv run python -W ignore reports/etap2/audyt_g5/poprawki/skrypty/c3_border_weights.py [k2_od_<tag>.json ...]
Inna metoda grupowania niż border_zones.py: linki graniczne tej samej drogi (ref z PBF) w odległości < 3 km od siebie = jedna droga.
Natężenia GPR prosto z tabel GDDKiA (dk_sdrdr.xlsx tablica 3, dw_sdrr.xlsx; współrzędne z wykazów, WGS84 -> 2180), nie z gpr_punkty.csv.
Podane pliki JSON estymacji: porównanie z polem border_weights (udziały wjazdów muszą się zgadzać do 0,1 pp).
"""
import gzip
import json
import sys

import numpy as np
import osmium
import pandas as pd
from lxml import etree
from pyproj import Transformer

bl = pd.read_csv("scenarios/kutno/demand/border_links.csv")
cap, orig = {}, {}
with gzip.open("scenarios/kutno/network.xml.gz", "rb") as f:
    for _, el in etree.iterparse(f, tag="link"):
        cap[el.get("id")] = float(el.get("capacity"))
        orig[el.get("id")] = next((a.text for a in el.iter("attribute") if a.get("name") == "origid"), None)
        el.clear()
bl["cap"], bl["origid"] = bl.link.map(cap), bl.link.map(orig)
want = set(bl.origid)


class H(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.r = {}

    def way(self, w):
        if str(w.id) in want:
            self.r[str(w.id)] = w.tags.get("ref")


h = H()
h.apply_file("data/raw/osm/lodzkie-261015.osm.pbf")
bl["ref"] = bl.origid.map(h.r)
bl["grp"] = ""
for (kind, ref), k in bl.groupby(["kind", "ref"]):  # klastrowanie po odległości (pojedyncze wiązanie, 3 km)
    lab = list(range(len(k)))
    xy = k[["x", "y"]].to_numpy()
    for i in range(len(k)):
        for j in range(len(k)):
            if np.hypot(*(xy[i] - xy[j])) < 3000:
                a, b = lab[i], lab[j]
                lab = [min(a, b) if v in (a, b) else v for v in lab]
    bl.loc[k.index, "grp"] = [f"{ref}#{int(xy[lab.index(v)][0] // 1000)}" for v in lab]

tr = Transformer.from_crs(4326, 2180, always_xy=True)
num = lambda s: pd.to_numeric(s.astype(str).str.replace(",", "."), errors="coerce")
pts = []
w = pd.read_excel("data/raw/g5/gpr2025/dk_wykaz.xlsx", header=None, skiprows=11)
pts.append(pd.DataFrame({"nr": num(w[0]), "droga": w[1].astype(str), "lat": num(w[11]), "lon": num(w[12])}))
w = pd.read_excel("data/raw/g5/gpr2025/dw_wykaz.xlsx", header=None, skiprows=11)
pts.append(pd.DataFrame({"nr": num(w[0]), "droga": w[1].astype(str), "lat": num(w[8]), "lon": num(w[9])}))
pts = pd.concat(pts).dropna()
pts["E"], pts["N"] = tr.transform(pts.lon.to_numpy(), pts.lat.to_numpy())
d = pd.read_excel("data/raw/g5/gpr2025/dk_sdrdr.xlsx", header=None, skiprows=10)  # tablica 3: kol. 9-16 struktura SDRDR
dk = pd.DataFrame({"nr": num(d[0]), "lcv": d[[9, 10, 11, 12]].apply(num).sum(axis=1), "heavy": d[[13, 14, 15, 16]].apply(num).sum(axis=1)})
d = pd.read_excel("data/raw/g5/gpr2025/dw_sdrr.xlsx", header=None, skiprows=10)  # DW: SDRR, kol. 8-15 struktura
dw = pd.DataFrame({"nr": num(d[0]), "lcv": d[[8, 9, 10, 11]].apply(num).sum(axis=1), "heavy": d[[12, 13, 14, 15]].apply(num).sum(axis=1)})
vol = pd.concat([dk, dw]).dropna(subset=["nr"]).drop_duplicates("nr").set_index("nr")

# Odcinek GPR, na którym leży wjazd: z opisu odcinka (od - do) i położenia, sprawdzone ręcznie (raport k3). Najbliższy punkt
# nie zawsze jest właściwy: na A1 płd. najbliższy jest 91822 (za węzłem Piątek, ~467 km N), a wjazd leży na 471,7 km N,
# czyli na odcinku 91821 „W. Kutno Wsch. - W. Piątek”.
SECTION = {"60#520": 91115, "A1#534": 91821, "91#512": 91103, "92#551": 91126, "702#533": 10049, "A1#520": 71410,
           "60#528": 11104, "91#509": 71306, "92#506": 91121, "583#548": 14067, "573#541": 14044}
ent = bl[bl.kind == "entry"]
rows = []
for g, k in ent.groupby("grp"):
    ref = k.ref.iloc[0]
    x, y = k.x.mean(), k.y.mean()
    c = pts[pts.droga.str.split("\n").apply(lambda rs: ref in rs)].copy()
    c["km"] = np.hypot(c.E - x, c.N - y) / 1000
    c = c.sort_values("km").drop_duplicates("nr")
    p = c[c.nr == SECTION[g]].iloc[0]
    rows.append(dict(droga=g, links=len(k), cap=k.cap.sum(), gpr_nr=int(p.nr), km=round(p.km, 1),
                     nearest=f"{int(c.nr.iloc[0])} ({c.km.iloc[0]:.1f} km)", lcv=vol.lcv[p.nr], heavy=vol.heavy[p.nr]))
t = pd.DataFrame(rows)
for c in ("cap", "lcv", "heavy"):
    t[f"udz_{c}"] = (t[c] / t[c].sum() * 100).round(1)
pd.set_option("display.width", 200)
print(t.sort_values("udz_cap", ascending=False).to_string(index=False))
res = {"entries": t.to_dict(orient="records")}
for jf in sys.argv[1:]:
    j = json.load(open(jf, encoding="utf-8"))
    bw = {k[len("entry "):]: v for k, v in j["border_weights"].items() if k.startswith("entry ")}
    s = pd.Series(bw) / sum(bw.values()) * 100
    cls = "heavy" if j["cls"] == "heavy" else "lcv"
    mine = sorted(t[f"udz_{cls}"].tolist())
    theirs = sorted(s.round(1).tolist())
    ok = len(mine) == len(theirs) and max(abs(a - b) for a, b in zip(mine, theirs)) <= 0.1
    print(jf, cls, "zgodne" if ok else "ROZBIEŻNE", theirs)
    res[jf] = {"cls": cls, "estimation_shares": s.round(2).to_dict(), "ok": ok}
    assert ok
json.dump(res, open("reports/etap2/audyt_g5/poprawki/c3_border_weights.json", "w", encoding="utf-8"), indent=1,
          ensure_ascii=False, default=float)
