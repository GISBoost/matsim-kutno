"""Pomiary ruchu WIOŚ 2013 w Kutnie (K1–K5) przypięte do linków sieci i przeskalowane do 2025 (S1: GPR 2010/2015/2025).

Użycie: uv run python -W ignore reports/etap3/g_pomiary_miejskie/wios2013.py
Wyjście: scenarios/kutno/validation/wios2013_linki.csv (oba kierunki przekroju) i wios2013.json obok skryptu.

Źródła liczb:
- WIOŚ Łódź, „Stan środowiska w woj. łódzkim w 2013”, rozdz. IV Hałas (data/raw/g_pomiary/wios_2013_halas.pdf),
  tab. IV.1 (K1, s. 130–131) i IV.2 (K2–K5, s. 131), przepisane ze skanu strony. Dzień 6–22 (16 h), noc 22–6.
- GPR 2010 (data/raw/g_pomiary/SDR_pkt_GPR2010_DK.pdf), GPR 2015 (WYNIKI_GPR2015_DK.pdf), GPR 2025 (data/raw/g5/gpr2025/dk_sdrr.xlsx
  przez scenarios/kutno/validation/gpr_linki.csv): SDR poj. silnikowych, odcinki DK wokół Kutna.
ZAŁOŻENIA:
- 2013 = interpolacja liniowa 2010–2015 (0,6 drogi); między pomiarami otwarto A1 przy Kutnie, więc pasmo 2013 = [GPR 2015, GPR 2010].
- K1: tylko doby z dniem roboczym (wg kalendarza 2013: śr–pt i pn), bo model to dzień roboczy.
- Przekrój = oba kierunki; punkt WIOŚ to adres posesji (OSM), link = najbliższy link sieci z OSM way o nazwie ulicy.
"""
import gzip
import json
from pathlib import Path

import geopandas as gpd
import osmium
import pandas as pd
import shapely.wkb as W
from lxml import etree
from shapely.geometry import LineString

HERE = Path(__file__).parent
PBF = "data/raw/osm/lodzkie-261015.osm.pbf"

# K1, tab. IV.1: data (pierwsza doba), dzień lekkie, dzień ciężkie, noc lekkie, noc ciężkie
K1 = pd.DataFrame([
    ("2013-06-12", 10249, 1826, 453, 47), ("2013-06-13", 12236, 2527, 474, 52), ("2013-06-14", 9129, 1315, 527, 79),
    ("2013-06-15", 9084, 1669, 478, 18), ("2013-06-16", 9046, 1751, 489, 94), ("2013-07-20", 6637, 1176, 371, 58),
    ("2013-07-21", 8104, 1632, 371, 42), ("2013-07-22", 7521, 1882, 467, 36), ("2013-09-04", 5152, 2148, 258, 63),
    ("2013-09-05", 7579, 2363, 247, 51), ("2013-09-06", 5557, 2006, 325, 72), ("2013-09-07", 7488, 2148, 708, 19)],
    columns=["data", "d_lek", "d_cie", "n_lek", "n_cie"])
K1["dzien_tyg"] = pd.to_datetime(K1.data).dt.day_name()
K1["roboczy"] = pd.to_datetime(K1.data).dt.dayofweek < 5  # dzień 6–22 przypada na datę początkową
K1["doba"] = K1[["d_lek", "d_cie", "n_lek", "n_cie"]].sum(axis=1)
K1["ciez"] = K1.d_cie + K1.n_cie
k1r = K1[K1.roboczy]

# punkty: id, ulica (OSM name), opis, doba dzień, doba noc, % ciężkich dzień, % ciężkich noc, korytarz GPR, adres (OSM) albo przecznica
PTS = [
    ("K1", "Toruńska", "Toruńska 7 (naprzeciw KPP)", None, None, None, None, "91123", ("Toruńska", "7")),
    ("K2", "Łąkoszyńska", "Łąkoszyńska 11", 6338, 573, 11.8, 10.5, "suma", ("Łąkoszyńska", "11")),
    ("K3", "Grunwaldzka", "Grunwaldzka 17 (kościół św. Jadwigi)", 3002, 141, 6.6, 18.4, "91125+91869", ("Grunwaldzka", "17")),
    ("K4", "Tadeusza Kościuszki", "brama terenów sportowych (al. Młodej Ligi = Centrum Małej Ligi Baseballowej)", 3222, 254, 9.2, 8.3, "11104", "Europejskie Centrum Małej Ligi Baseballowej"),
    ("K5", "Łęczycka", "Noskowskiego 1 (wsch. strona Łęczyckiej)", 7672, 464, 45.6, 14.2, "91115", ("Zygmunta Noskowskiego", "1")),
]

# SDR poj. silnikowych [2010, 2015, 2025]; 91125+91869: w 2010 jeden odcinek Kutno–Bedlno, 2015/2025 średnia ważona długością (6,72 / 7,30 km)
GPR = {"91123": (8269, 5989, 6241), "91124": (9978, 8803, 9341), "91115": (2850, 3108, 4089), "11104": (5983, 6577, 9351),
       "91125+91869": (6862, (5979 * 6.72 + 5789 * 7.30) / 14.02, (9872 * 6.72 + 9095 * 7.30) / 14.02)}
gp = pd.DataFrame(GPR, index=["y2010", "y2015", "y2025"]).T
gp["y2013"] = gp.y2010 + 0.6 * (gp.y2015 - gp.y2010)
gp.loc["suma"] = gp.sum()
gp["f"] = gp.y2025 / gp.y2013
gp["f_lo"] = gp.y2025 / gp[["y2010", "y2015"]].max(axis=1)
gp["f_hi"] = gp.y2025 / gp[["y2010", "y2015"]].min(axis=1)

# OSM: adresy i ulice
gm = gpd.read_file("scenarios/kutno/area/gmina.geojson").to_crs(2180).geometry.iloc[0]
names = {p[1] for p in PTS}
place = {p[8] for p in PTS if isinstance(p[8], str)}  # obiekt OSM (np. ośrodek sportowy) zamiast adresu
addr = {p[8] for p in PTS if isinstance(p[8], tuple)}
fab, ways, found = osmium.geom.WKBFactory(), [], {}
for o in osmium.FileProcessor(PBF).with_areas().with_locations():
    t = o.tags
    if o.is_way() and t.get("highway") and t.get("name") in names:
        try:
            ways.append((o.id, t["name"], W.loads(fab.create_linestring(o), hex=True)))
        except Exception:
            pass
    elif o.is_area() and t.get("name") in place:
        found.setdefault(t["name"], []).append(W.loads(fab.create_multipolygon(o), hex=True).centroid)
    elif o.is_area() and (t.get("addr:street"), t.get("addr:housenumber")) in addr:
        found.setdefault((t["addr:street"], t["addr:housenumber"]), []).append(
            W.loads(fab.create_multipolygon(o), hex=True).representative_point())
wg = gpd.GeoDataFrame(ways, columns=["origid", "name", "geometry"], crs=4326).to_crs(2180)
wg = wg[wg.intersects(gm.buffer(500))]
fg = {k: (s := gpd.GeoSeries(v, crs=4326).to_crs(2180))[s.within(gm)] for k, v in found.items()}  # ten sam adres bywa w innych gminach

nodes, links = {}, []
for ev, el in etree.iterparse(gzip.open("scenarios/kutno/network.xml.gz"), tag=("node", "link")):
    if el.tag == "node":
        nodes[el.get("id")] = (float(el.get("x")), float(el.get("y")))
    else:
        oid = el.find("attributes/attribute[@name='origid']")
        links.append((el.get("id"), el.get("from"), el.get("to"), int(oid.text) if oid is not None else -1))
    el.clear()
ln = pd.DataFrame(links, columns=["link", "fr", "to", "origid"])
ln = gpd.GeoDataFrame(ln, geometry=[LineString([nodes[a], nodes[b]]) for a, b in zip(ln.fr, ln.to)], crs=2180)

rows, rep = [], {}
for pid, street, opis, dz, nc, pd_, pn, kor, loc in PTS:
    st = wg[wg.name == street].union_all()
    pt = st.interpolate(st.project(fg[loc].iloc[0]))  # rzut posesji (K4: środka ośrodka sportowego) na oś ulicy
    cand = ln[ln.origid.isin(set(wg[wg.name == street].origid))].copy()
    cand["d"] = cand.distance(pt)
    best = cand.nsmallest(1, "d").iloc[0]
    pair = cand[(cand.fr == best.to) & (cand.to == best.fr)]  # przeciwny kierunek
    sel = [best] + ([pair.iloc[0]] if len(pair) else [])
    if pid == "K1":
        doba, ciez = k1r.doba.mean(), k1r.ciez.sum() / k1r.doba.sum() * 100
        doba_min, doba_max = k1r.doba.min(), k1r.doba.max()
    else:
        doba = dz + nc
        ciez = (dz * pd_ + nc * pn) / doba
        doba_min = doba_max = doba
    g = gp.loc[kor]
    rep[pid] = {"ulica": street, "opis": opis, "x": round(pt.x), "y": round(pt.y), "linki": [s.link for s in sel],
                "odl_m": round(float(best.d), 1), "doba_2013": round(doba), "doba_2013_min": int(doba_min), "doba_2013_max": int(doba_max),
                "ciezkie_proc_2013": round(float(ciez), 1), "korytarz_gpr": kor, "f_s1": round(float(g.f), 3),
                "f_s1_lo": round(float(g.f_lo), 3), "f_s1_hi": round(float(g.f_hi), 3), "f_suma": round(float(gp.loc["suma"].f), 3)}
    for s in sel:
        rows.append({"pkt": pid, "ulica": street, "link": s.link, "x": round(pt.x), "y": round(pt.y), "odl_m": round(float(s.d), 1),
                     "doba_2013": round(doba), "ciezkie_proc": round(float(ciez), 1), "korytarz": kor, "f_s1": round(float(g.f), 4),
                     "f_suma": round(float(gp.loc["suma"].f), 4)})

pd.DataFrame(rows).to_csv("scenarios/kutno/validation/wios2013_linki.csv", index=False, lineterminator="\n")
out = {"k1_doby": K1.assign(dzien_tyg=K1.dzien_tyg).to_dict(orient="records"),
       "k1_robocze": {"n": int(len(k1r)), "doba_srednia": round(float(k1r.doba.mean())), "rozrzut": [int(k1r.doba.min()), int(k1r.doba.max())],
                      "weekend_srednia": round(float(K1[~K1.roboczy].doba.mean()))},
       "gpr": gp.round(3).reset_index(names="korytarz").to_dict(orient="records"), "punkty": rep}
json.dump(out, open(HERE / "wios2013.json", "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False, default=str)
print(json.dumps({k: out[k] for k in ("k1_robocze", "punkty")}, ensure_ascii=False, indent=1))
print(gp.round(3).to_string())
