"""Audyt G5/I4: strefy graniczne ruchu tła per droga i kierunek (zamiast osobnej strefy na każdy link graniczny).

Użycie: uv run python -W ignore pipeline/border_zones.py   (po plans.py, który pisze border_links.csv)
Linki graniczne jednego rodzaju (wjazd albo wyjazd) połączone węzłami (koniec jednego = początek następnego) to jedna droga
przecinająca granicę sieci. Każdy taki łańcuch to jedna strefa. Id strefy = link zewnętrzny łańcucha (wjazd: pierwszy, od strony
granicy; wyjazd: ostatni), więc plans.py zamienia id strefy na link bez zmian w kodzie: agent startuje na końcu zewnętrznego
linku albo kończy na nim i przejeżdża resztę łańcucha jak każdy pojazd.
Droga (ref) z OSM po origid linku. Waga a priori strefy (używana w background_od.py): natężenie klasy pojazdów z najbliższego
punktu GPR 2025 na tej samej drodze (gpr_punkty.csv, kolumny `*_dr`: SDRDR, DW: SDRR jako ZAŁOŻENIE z K2). Gdy na drodze nie ma
punktu GPR w promieniu MAX_KM, gpr_nr zostaje puste i background_od.py się zatrzymuje (wagę trzeba wtedy ustalić jako ZAŁOŻENIE).
Kandydaci to punkty z gpr_punkty.csv (obszar sieci + 5 km). Przypisanie sprawdzone ręcznie z opisem odcinka (raport k3 poprawek):
na A1 płd. w pełnym wykazie bliżej jest 91822, ale leży za węzłem Piątek; wjazd leży na odcinku 91821 i ten jest wybierany.
Kontrola niezależna: reports/etap2/audyt_g5/poprawki/skrypty/c3_border_weights.py.
Wyjście: scenarios/kutno/demand/border_zones.csv (link, kind, zone, road, ref, gpr_nr, gpr_km, cap).
"""
import gzip
import math

import osmium
import pandas as pd
from lxml import etree

KUTNO = (524805, 485023)  # FACT_CHECK #17, jak plans.py
MAX_KM = 15  # ZAŁOŻENIE: dalej punkt GPR opisuje inny odcinek drogi

bl = pd.read_csv("scenarios/kutno/demand/border_links.csv")
want, L = set(bl.link), {}
with gzip.open("scenarios/kutno/network.xml.gz", "rb") as f:
    for _, el in etree.iterparse(f, tag="link"):
        if el.get("id") in want:
            a = {x.get("name"): x.text for x in el.iter("attribute")}
            L[el.get("id")] = (el.get("from"), el.get("to"), float(el.get("capacity")), a["origid"])
        el.clear()
bl["frm"], bl["to"], bl["cap"], bl["origid"] = zip(*bl.link.map(L))

ids = set(bl.origid)


class Ref(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.ref = {}

    def way(self, w):
        if str(w.id) in ids:
            self.ref[str(w.id)] = w.tags.get("ref")


h = Ref()
h.apply_file("data/raw/osm/lodzkie-261015.osm.pbf")
bl["ref"] = bl.origid.map(h.ref)
assert bl.ref.notna().all(), bl[bl.ref.isna()]

# łańcuchy: union-find po wspólnym węźle (to -> from) w obrębie rodzaju
parent = {l: l for l in bl.link}


def root(l):
    while parent[l] != l:
        parent[l] = parent[parent[l]]
        l = parent[l]
    return l


for kind, k in bl.groupby("kind"):
    by_from = dict(zip(k.frm, k.link))
    for l, t in zip(k.link, k.to):
        if t in by_from:
            parent[root(by_from[t])] = root(l)
bl["chain"] = bl.link.map(root)
zone = {}
for c, k in bl.groupby("chain"):
    assert k.ref.nunique() == 1 and k.kind.nunique() == 1, k
    end = k[~k.frm.isin(k.to)] if k.kind.iloc[0] == "entry" else k[~k.to.isin(k.frm)]  # link zewnętrzny łańcucha
    assert len(end) == 1, k
    zone[c] = end.link.iloc[0]
bl["zone"] = bl.chain.map(zone)
zx = bl.set_index("link").loc[bl.zone, ["x", "y"]].to_numpy()
compass = lambda x, y: ["wsch", "płn-wsch", "płn", "płn-zach", "zach", "płd-zach", "płd", "płd-wsch"][
    round(math.degrees(math.atan2(y - KUTNO[1], x - KUTNO[0])) / 45) % 8]
bl["road"] = [f"{r} {compass(x, y)}" for r, (x, y) in zip(bl.ref, zx)]
assert bl.groupby(["road", "kind"]).zone.nunique().max() == 1, "dwie strefy tej samej drogi i kierunku"

# punkt GPR: ta sama droga (dowolny z refów odcinka GPR, np. "60\n60c"), najbliższy do strefy
p = pd.read_csv("scenarios/kutno/validation/gpr_punkty.csv", dtype={"nr": str})
p["refs"] = p.droga.astype(str).str.split("\n")
gpr = {}
for z, (x, y) in zip(bl.zone, zx):
    r = bl.ref[bl.zone == z].iloc[0]
    c = p[p.refs.apply(lambda rs: r in rs)].copy()
    c["km"] = ((c.E - x) ** 2 + (c.N - y) ** 2) ** 0.5 / 1000
    c = c.sort_values("km")
    gpr[z] = (c.nr.iloc[0], round(c.km.iloc[0], 2)) if len(c) and c.km.iloc[0] <= MAX_KM else (None, None)
bl["gpr_nr"], bl["gpr_km"] = zip(*bl.zone.map(gpr))
out = bl[["link", "kind", "zone", "road", "ref", "gpr_nr", "gpr_km", "cap"]]
out.to_csv("scenarios/kutno/demand/border_zones.csv", index=False, lineterminator="\n")
pd.set_option("display.width", 200)
print(out.groupby(["road", "kind"]).agg(zone=("zone", "first"), links=("link", "size"), cap=("cap", "sum"),
                                        gpr_nr=("gpr_nr", "first"), gpr_km=("gpr_km", "first")).to_string())
