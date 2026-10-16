"""F4: lokalizacje (D7, D9, D11) i plans.xml.gz (home-car-work-car-home) z seeda.

Wejścia: F2 (sieć, obszar), F3 (scenarios/kutno/demand/*.csv), OSM (osm_features.py), BREC 2021 (obwody łódzkie, rejony PL).
Uruchom: uv run python -W ignore pipeline/plans.py [plans.xml.gz]
Wyjścia: scenarios/kutno/plans.xml.gz (domyślnie), scenarios/kutno/plans_meta.csv (osoba -> źródło, obwód/gmina, budynki).
"""
import gzip
import sys
import tomllib
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
from lxml import etree
from shapely.geometry import Point

cfg = tomllib.loads(Path("config/kutno.toml").read_text(encoding="utf-8"))
A, P = cfg["area"], cfg["plans"]
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("scenarios/kutno/plans.xml.gz")
rng = np.random.default_rng(P["seed"])
KUTNO_CENTRE = Point(524805, 485023)  # FACT_CHECK #17

# --- liczebności: largest remainder, żeby suma = round(sample x całość) --------------------------------
ob = pd.read_csv("scenarios/kutno/demand/workers_by_obwod.csv")
inb = pd.read_csv("scenarios/kutno/demand/inbound_by_gmina.csv", dtype={"home": str})
strata = pd.concat([
    pd.DataFrame({"kind": "resident", "key": ob.obwod_id.astype(str), "n": ob[f"work_in_kutno_{P['variant']}"]}),
    pd.DataFrame({"kind": "commuter", "key": inb.home, "n": inb.n.astype(float)}),
], ignore_index=True)
exact = strata.n * P["sample"]
strata["agents"] = np.floor(exact).astype(int)
target = round(exact.sum())
rest = (exact - strata.agents).sort_values(ascending=False, kind="stable")
strata.loc[rest.index[:target - strata.agents.sum()], "agents"] += 1
assert strata.agents.sum() == target

# --- geometrie --------------------------------------------------------------------------------------
area = gpd.read_file("scenarios/kutno/area/network_area.geojson").geometry.iloc[0]
gmina_kutno = gpd.read_file("scenarios/kutno/area/gmina.geojson").geometry.iloc[0]
g10 = pyogrio.read_dataframe("data/raw/brec/gml/AreaStatisticalUnit_10.xml",
                             columns=["LocationString", "thematicId|ThematicIdentifier|identifier"]).to_crs("EPSG:2180")
g10["uid"] = g10["thematicId|ThematicIdentifier|identifier"].astype(int)
obwody = g10[(g10.LocationString.astype(str).str.zfill(7) == A["teryt_gmina"]) & (g10.uid > 999_999)].set_index("uid").geometry
rej = gpd.read_file("data/raw/brec/rej_pl/SU_BREC_2021_REJ.shp", columns=["GMINA"])
gminy = rej.dissolve(by="GMINA").geometry


def gmina_geom(code):
    """Miasta na prawach powiatu (Łódź, Warszawa...) mają w BREC kody dzielnic: łączymy po kodzie powiatu."""
    if code in gminy.index:
        return gminy[code]
    parts = gminy[gminy.index.str[:4] == code[:4]]
    assert len(parts) and code[2] == "6", code  # kod powiatu 6x = miasto na prawach powiatu
    return parts.union_all()


b = gpd.read_file("scenarios/kutno/osm/features.gpkg", layer="buildings")
lu = gpd.read_file("scenarios/kutno/osm/features.gpkg", layer="landuse")
b["pt"] = b.geometry.representative_point()
b["area_m2"] = b.geometry.area
pts = b.set_geometry("pt")


def in_landuse(kinds):
    return pts.index.isin(gpd.sjoin(pts[["pt"]], lu[lu.landuse.isin(kinds)][["geometry"]], predicate="within").index)


b["residential"] = b.building.isin(P["residential_buildings"]) | ((b.building == "yes") & in_landuse(["residential"])
                                                                   & b.amenity.isna() & b.shop.isna() & b.office.isna())
b["work"] = (b.building.isin(P["work_buildings"]) | b.amenity.notna() | b.shop.notna() | b.office.notna()
             | ((b.building == "yes") & in_landuse(P["work_landuse"]))) & b.pt.within(gmina_kutno)
b.loc[b.work, "residential"] = False
homes_b = b[b.residential].set_geometry("pt")
work_b = b[b.work].reset_index(drop=True)


def pick_buildings(cands, k):
    """k budynków losowanych ze zwracaniem, wagi = powierzchnia obrysu (D7, D11)."""
    i = rng.choice(len(cands), size=k, p=(cands.area_m2 / cands.area_m2.sum()).to_numpy())
    return cands.iloc[i]


def random_point(poly):
    x0, y0, x1, y1 = poly.bounds
    while True:
        p = Point(rng.uniform(x0, x1), rng.uniform(y0, y1))
        if poly.contains(p):
            return p


# --- wjazdy na granicy sieci (D9) --------------------------------------------------------------------
nodes, entry = {}, []
with gzip.open("scenarios/kutno/network.xml.gz", "rb") as f:
    for _, el in etree.iterparse(f, tag=("node", "link")):
        if el.tag == "node":
            nodes[el.get("id")] = Point(float(el.get("x")), float(el.get("y")))
        else:
            t = {a.get("name"): a.text for a in el.iter("attribute")}.get("type")
            if t in P["entry_road_types"]:
                entry.append((el.get("id"), el.get("from"), el.get("to")))
        el.clear()
interior = area.buffer(-P["entry_zone_m"])
entry = pd.DataFrame([dict(link=l, x=nodes[b_].x, y=nodes[b_].y) for l, a_, b_ in entry
                      if not interior.contains(nodes[a_]) and area.contains(nodes[b_])
                      and nodes[b_].distance(KUTNO_CENTRE) < nodes[a_].distance(KUTNO_CENTRE)])
assert len(entry), "brak linków wjazdowych"

# --- osoby -------------------------------------------------------------------------------------------
powiat = A["teryt_powiat"]
people = []  # (id, kind, key, home_x, home_y, home_link, home_src)
for s in strata[strata.agents > 0].itertuples():
    if s.kind == "resident":
        poly = obwody[int(s.key)]
        cands = homes_b[homes_b.pt.within(poly)]
    elif s.key.startswith(powiat):
        poly = gmina_geom(s.key)
        cands = homes_b[homes_b.pt.within(poly)]
    else:
        c = gmina_geom(s.key).centroid
        e = entry.iloc[((entry.x - c.x) ** 2 + (entry.y - c.y) ** 2).idxmin()]
        for k in range(s.agents):
            people.append((f"c{s.key}_{k}", s.kind, s.key, e.x, e.y, e.link, "entry"))
        continue
    if len(cands):
        for k, h in enumerate(pick_buildings(cands, s.agents).itertuples()):
            people.append((f"{s.kind[0]}{s.key}_{k}", s.kind, s.key, h.pt.x, h.pt.y, None, f"osm_{h.osm_id}"))
    else:
        for k in range(s.agents):
            p = random_point(poly)
            people.append((f"{s.kind[0]}{s.key}_{k}", s.kind, s.key, p.x, p.y, None, "random_point"))

meta = pd.DataFrame(people, columns=["person", "kind", "key", "home_x", "home_y", "home_link", "home_src"])
w = pick_buildings(work_b, len(meta))
meta["work_x"], meta["work_y"], meta["work_src"] = w.pt.x.to_numpy(), w.pt.y.to_numpy(), [f"osm_{i}" for i in w.osm_id]

# --- plans.xml.gz (bez tras; mtime=0, żeby sha256 był powtarzalny) ------------------------------------
root = etree.Element("population")
for r in meta.itertuples():
    plan = etree.SubElement(etree.SubElement(root, "person", id=r.person), "plan", selected="yes")
    home = dict(type="home", x=f"{r.home_x:.1f}", y=f"{r.home_y:.1f}")
    if isinstance(r.home_link, str):
        home["link"] = r.home_link
    etree.SubElement(plan, "activity", **home, end_time=P["home_end_time"])
    etree.SubElement(plan, "leg", mode="car")
    etree.SubElement(plan, "activity", type="work", x=f"{r.work_x:.1f}", y=f"{r.work_y:.1f}", max_dur=P["work_max_dur"])
    etree.SubElement(plan, "leg", mode="car")
    etree.SubElement(plan, "activity", **home)
xml = etree.tostring(root, xml_declaration=True, encoding="utf-8", pretty_print=True,
                     doctype='<!DOCTYPE population SYSTEM "http://www.matsim.org/files/dtd/population_v6.dtd">')
with open(OUT, "wb") as f, gzip.GzipFile(fileobj=f, mode="wb", mtime=0, filename="") as gz:
    gz.write(xml)
meta.to_csv(OUT.parent / "plans_meta.csv", index=False)
strata.to_csv(OUT.parent / "plans_strata.csv", index=False)
print(f"{OUT}: {len(meta)} osób (cel {target}); budynki mieszk. {len(homes_b)}, pracy {len(work_b)}, "
      f"linki wjazdowe {len(entry)}; źródła domów: {meta.home_src.str.split('_').str[0].value_counts().to_dict()}")
