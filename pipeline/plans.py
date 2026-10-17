"""F4: lokalizacje (D7, D9, D11) i plans.xml.gz (home-car-work-car-home) z seeda.

Wejścia: F2 (sieć, obszar), F3 (scenarios/kutno/demand/*.csv), OSM (osm_features.py), BREC 2021 (obwody łódzkie, rejony PL).
Uruchom: uv run python -W ignore pipeline/plans.py [plans.xml.gz [sample [klucz=wartość ...]]]
  (sample nadpisuje config, np. 1.0 dla F6; klucz=wartość nadpisuje [plans], np. jobs_total=17486 dla D17/C)
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
from shapely import STRtree
from shapely.geometry import LineString, Point

cfg = tomllib.loads(Path("config/kutno.toml").read_text(encoding="utf-8"))
A, P = cfg["area"], cfg["plans"]
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("scenarios/kutno/plans.xml.gz")
if len(sys.argv) > 2:
    P["sample"] = float(sys.argv[2])
for kv in sys.argv[3:]:
    k, v = kv.split("=")
    P[k] = type(P[k])(v)
rng = np.random.default_rng(P["seed"])
KUTNO_CENTRE = Point(524805, 485023)  # FACT_CHECK #17

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
b["work_any"] = (b.building.isin(P["work_buildings"]) | b.amenity.notna() | b.shop.notna() | b.office.notna()
                 | ((b.building == "yes") & in_landuse(P["work_landuse"])))
b["work"] = b.work_any & b.pt.within(gmina_kutno)
b.loc[b.work, "residential"] = False
homes_b = b[b.residential].set_geometry("pt")
work_b = b[b.work].reset_index(drop=True)
work_out_b = b[b.work_any & ~b.work].set_geometry("pt")  # D17/O1: praca wyjeżdżających w gminach powiatu


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
nodes, entry, snap = {}, [], []
with gzip.open("scenarios/kutno/network.xml.gz", "rb") as f:
    for _, el in etree.iterparse(f, tag=("node", "link")):
        if el.tag == "node":
            nodes[el.get("id")] = Point(float(el.get("x")), float(el.get("y")))
        else:
            t = {a.get("name"): a.text for a in el.iter("attribute")}.get("type")
            if t in P["entry_road_types"]:
                entry.append((el.get("id"), el.get("from"), el.get("to")))
            if t not in P["snap_exclude_types"]:
                snap.append((el.get("id"), el.get("from"), el.get("to")))
        el.clear()
snap_ids = [l for l, _, _ in snap]
snap_tree = STRtree([LineString([nodes[a_], nodes[b_]]) for _, a_, b_ in snap])


def snap_links(xs, ys):
    """R3/E5: najbliższy link sieci bez autostrad, ekspresówek i łącznic (zamiast przypinania przez MATSim)."""
    src, dst = snap_tree.query_nearest([Point(x, y) for x, y in zip(xs, ys)], all_matches=False)
    assert (src == np.arange(len(src))).all()
    return [snap_ids[i] for i in dst]
interior = area.buffer(-P["entry_zone_m"])
border_links = entry
entry = pd.DataFrame([dict(link=l, x=nodes[b_].x, y=nodes[b_].y) for l, a_, b_ in border_links
                      if not interior.contains(nodes[a_]) and area.contains(nodes[b_])
                      and nodes[b_].distance(KUTNO_CENTRE) < nodes[a_].distance(KUTNO_CENTRE)])
# D17/O1: wyjazd = lustro wjazdu (link tych klas kończący się w strefie granicy, skierowany od Kutna)
exits = pd.DataFrame([dict(link=l, x=nodes[b_].x, y=nodes[b_].y) for l, a_, b_ in border_links
                      if not interior.contains(nodes[b_]) and area.contains(nodes[a_])
                      and nodes[b_].distance(KUTNO_CENTRE) > nodes[a_].distance(KUTNO_CENTRE)])
assert len(entry) and len(exits), "brak linków wjazdowych/wyjazdowych"
pd.concat([entry.assign(kind="entry"), exits.assign(kind="exit")]).to_csv(  # D19/K2-2: strefy graniczne tła
    "scenarios/kutno/demand/border_links.csv", index=False, lineterminator="\n")

# --- liczebności: largest remainder, żeby suma = round(sample x całość) --------------------------------
ob = pd.read_csv("scenarios/kutno/demand/workers_by_obwod.csv")
inb = pd.read_csv("scenarios/kutno/demand/inbound_by_gmina.csv", dtype={"home": str})
outb = pd.read_csv("scenarios/kutno/demand/outbound_by_gmina.csv", dtype={"work": str})
strata = pd.concat([
    pd.DataFrame({"kind": "resident", "key": ob.obwod_id.astype(str), "n": ob[f"work_in_kutno_{P['variant']}"]}),
    pd.DataFrame({"kind": "commuter", "key": inb.home, "n": inb.n.astype(float)}),
    pd.DataFrame({"kind": "outbound", "key": outb.work, "n": outb.n.astype(float)}),  # D17/O1
], ignore_index=True)


# D16/B, D17/O1: gminy spoza powiatu z centroidem dalej niż max_border_km od najbliższego wjazdu (wyjazdu) pomijamy
def border_dist(code, links):
    c = gmina_geom(code).centroid
    return float(np.sqrt((links.x - c.x) ** 2 + (links.y - c.y) ** 2).min())


ext = (strata.kind != "resident") & ~strata.key.str.startswith(A["teryt_powiat"])
strata["border_km"] = 0.0
strata.loc[ext, "border_km"] = [border_dist(k, entry if kind == "commuter" else exits) / 1000
                                for k, kind in zip(strata.key[ext], strata.kind[ext])]
strata["excluded"] = strata.border_km > P["max_border_km"]
strata["n_model"] = strata.n.where(~strata.excluded, 0)
# D17/C: miejsca pracy w Kutnie (mieszkańcy + przyjeżdżający) skalowane jednym współczynnikiem do jobs_total
jobs = strata.kind != "outbound"
if P["jobs_total"]:
    strata.loc[jobs, "n_model"] *= P["jobs_total"] / strata.n_model[jobs].sum()
# D19/K1-1: jadący autem w dzień roboczy = n × udział auta × (1 − praca z domu), wszystkie rodzaje jednakowo
strata["n_model"] *= P["car_share"] * (1 - P["work_from_home"])
exact = strata.n_model * P["sample"]
strata["agents"] = np.floor(exact).astype(int)
target = round(exact.sum())
rest = (exact - strata.agents).sort_values(ascending=False, kind="stable")
strata.loc[rest.index[:target - strata.agents.sum()], "agents"] += 1
assert strata.agents.sum() == target

# --- osoby -------------------------------------------------------------------------------------------
powiat = A["teryt_powiat"]
people = []  # (id, kind, key, home_x, home_y, home_link, home_src, border_m)
_homes = {}


def homes_in(obwod):
    if obwod not in _homes:
        _homes[obwod] = homes_b[homes_b.pt.within(obwody[obwod])]
    return _homes[obwod]


for s in strata[strata.agents > 0].itertuples():
    if s.kind == "outbound":  # D17/O1: dom w Kutnie, obwód losowany wagą pracujących (D5); praca dobierana niżej
        p_ob = (ob.employed_base / ob.employed_base.sum()).to_numpy()
        for k, o in enumerate(rng.choice(ob.obwod_id.to_numpy(), size=s.agents, p=p_ob)):
            if len(homes_in(int(o))):
                h = pick_buildings(homes_in(int(o)), 1).iloc[0]
                people.append((f"o{s.key}_{k}", s.kind, s.key, h.pt.x, h.pt.y, None, f"osm_{h.osm_id}", 0.0))
            else:  # jak mieszkańcy: obwód bez budynku mieszkalnego -> losowy punkt
                p = random_point(obwody[int(o)])
                people.append((f"o{s.key}_{k}", s.kind, s.key, p.x, p.y, None, "random_point", 0.0))
        continue
    if s.kind == "resident":
        poly = obwody[int(s.key)]
        cands = homes_in(int(s.key))
    elif s.key.startswith(powiat):
        poly = gmina_geom(s.key)
        cands = homes_b[homes_b.pt.within(poly)]
    else:
        c = gmina_geom(s.key).centroid
        e = entry.iloc[((entry.x - c.x) ** 2 + (entry.y - c.y) ** 2).idxmin()]
        for k in range(s.agents):
            people.append((f"c{s.key}_{k}", s.kind, s.key, e.x, e.y, e.link, "entry", c.distance(Point(e.x, e.y))))
        continue
    if len(cands):
        for k, h in enumerate(pick_buildings(cands, s.agents).itertuples()):
            people.append((f"{s.kind[0]}{s.key}_{k}", s.kind, s.key, h.pt.x, h.pt.y, None, f"osm_{h.osm_id}", 0.0))
    else:
        for k in range(s.agents):
            p = random_point(poly)
            people.append((f"{s.kind[0]}{s.key}_{k}", s.kind, s.key, p.x, p.y, None, "random_point", 0.0))

meta = pd.DataFrame(people, columns=["person", "kind", "key", "home_x", "home_y", "home_link", "home_src", "border_m"])
assert meta.person.is_unique
inside = meta.kind != "outbound"
w = pick_buildings(work_b, int(inside.sum()))
meta.loc[inside, "work_x"], meta.loc[inside, "work_y"] = w.pt.x.to_numpy(), w.pt.y.to_numpy()
meta.loc[inside, "work_src"] = [f"osm_{i}" for i in w.osm_id]
meta["work_link"] = None
for key, grp in meta[~inside].groupby("key", sort=False):  # D17/O1: praca wyjeżdżających
    if key.startswith(powiat):
        poly = gmina_geom(key)
        cands = work_out_b[work_out_b.pt.within(poly)]
        if len(cands):
            w = pick_buildings(cands, len(grp))
            meta.loc[grp.index, "work_x"], meta.loc[grp.index, "work_y"] = w.pt.x.to_numpy(), w.pt.y.to_numpy()
            meta.loc[grp.index, "work_src"] = [f"osm_{i}" for i in w.osm_id]
        else:
            for i in grp.index:
                p = random_point(poly)
                meta.loc[i, ["work_x", "work_y", "work_src"]] = p.x, p.y, "random_point"
    else:
        c = gmina_geom(key).centroid
        e = exits.iloc[((exits.x - c.x) ** 2 + (exits.y - c.y) ** 2).idxmin()]
        meta.loc[grp.index, ["work_x", "work_y", "work_link", "work_src"]] = e.x, e.y, e.link, "exit"
own = meta.home_link.isna()
meta.loc[own, "home_link"] = snap_links(meta.home_x[own], meta.home_y[own])
own = meta.work_link.isna()
meta.loc[own, "work_link"] = snap_links(meta.work_x[own], meta.work_y[own])

# --- godzina wyjazdu (D10): przedział z udziałem z profilu, jednostajnie w przedziale ---------------------
prof = pd.read_csv(P["departure_profile"])
k = rng.choice(len(prof), size=len(meta), p=(prof.share_pct / prof.share_pct.sum()).to_numpy())
meta["dep_s"] = (prof.from_h.to_numpy()[k] * 3600 + rng.uniform(0, 1, len(meta)) * (prof.to_h - prof.from_h).to_numpy()[k] * 3600).astype(int)
# D16/A: przyjeżdżający spoza powiatu dostają godzinę z profilu jako moment wjazdu na granicę sieci (bez doliczania dojazdu)
meta["start_s"] = meta.dep_s

# --- plans.xml.gz (bez tras; mtime=0, żeby sha256 był powtarzalny) ------------------------------------
root = etree.Element("population")
for r in meta.itertuples():
    person = etree.SubElement(root, "person", id=r.person)
    attrs = etree.SubElement(person, "attributes")  # subpopulation wymagana przez TripAnalysis (SimWrapper)
    for name, val in (("subpopulation", "person"), ("kind", r.kind)):
        etree.SubElement(attrs, "attribute", name=name, **{"class": "java.lang.String"}).text = val
    plan = etree.SubElement(person, "plan", selected="yes")
    home = dict(type="home", link=r.home_link, x=f"{r.home_x:.1f}", y=f"{r.home_y:.1f}")
    etree.SubElement(plan, "activity", **home, end_time=f"{r.start_s // 3600:02d}:{r.start_s // 60 % 60:02d}:{r.start_s % 60:02d}")
    etree.SubElement(plan, "leg", mode="car")
    etree.SubElement(plan, "activity", type="work", link=r.work_link, x=f"{r.work_x:.1f}", y=f"{r.work_y:.1f}", max_dur=P["work_max_dur"])
    etree.SubElement(plan, "leg", mode="car")
    etree.SubElement(plan, "activity", **home)
xml = etree.tostring(root, xml_declaration=True, encoding="utf-8", pretty_print=True,
                     doctype='<!DOCTYPE population SYSTEM "http://www.matsim.org/files/dtd/population_v6.dtd">')
with open(OUT, "wb") as f, gzip.GzipFile(fileobj=f, mode="wb", mtime=0, filename="") as gz:
    gz.write(xml)
stem = OUT.name.removesuffix(".xml.gz")
meta.to_csv(OUT.with_name(stem + "_meta.csv"), index=False)
strata.to_csv(OUT.with_name(stem + "_strata.csv"), index=False)
print(f"{OUT}: {len(meta)} osób (cel {target}); budynki mieszk. {len(homes_b)}, pracy {len(work_b)}, "
      f"linki wjazdowe {len(entry)}, wyjazdowe {len(exits)}; wg rodzaju {meta.kind.value_counts().to_dict()}; odcięte gminy > {P['max_border_km']} km: {int(strata.excluded.sum())} "
      f"({strata.n[strata.excluded].sum():.0f} os. w 100%); jobs_total {P['jobs_total']}; źródła domów: {meta.home_src.str.split('_').str[0].value_counts().to_dict()}")
