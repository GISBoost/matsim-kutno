"""F4: lokalizacje (D7, D9, D11) i plans.xml.gz (home-car-work-car-home) z seeda.

Wejścia: F2 (sieć, obszar), F3 (scenarios/kutno/demand/*.csv), OSM (osm_features.py), BREC 2021 (obwody łódzkie, rejony PL).
Uruchom: uv run python -W ignore pipeline/plans.py [plans.xml.gz [sample [klucz=wartość ...]]]
  (sample nadpisuje config, np. 1.0 dla F6; klucz=wartość nadpisuje [plans], np. jobs_total=17486 dla D17/C)
Wyjścia: scenarios/kutno/plans.xml.gz (domyślnie), scenarios/kutno/plans_meta.csv (osoba -> źródło, obwód/gmina, budynki).
"""
import gzip
import sys
from collections import defaultdict
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
homes_b["hid"] = [f"osm_{i}" for i in homes_b.osm_id]
if P["home_source"] == "bdot":  # D28/G3: dom = budynek BDOT10k jedno- lub wielorodzinny, waga = obrys × kondygnacje (area_m2 to tu waga)
    bd = pyogrio.read_dataframe(P["home_bdot"], encoding="utf-8", columns=["LOKALNYID", "KATEGORIAISTNIENIA", "PRZEWAZAJACAFUNKCJABUDYNKU",
                                                                          "LICZBAKONDYGNACJI"])
    bd = bd[(bd.KATEGORIAISTNIENIA == "eksploatowany") & bd.PRZEWAZAJACAFUNKCJABUDYNKU.isin(P["home_bdot_functions"])].copy()
    assert bd.LOKALNYID.is_unique and len(bd), "BDOT: brak budynków mieszkalnych albo powtórzone LOKALNYID"
    bd["area_m2"] = bd.geometry.area * bd.LICZBAKONDYGNACJI.fillna(1).clip(lower=1)
    bd["hid"] = "bdot_" + bd.LOKALNYID.astype(str)
    homes_b = bd.assign(pt=bd.geometry.representative_point()).set_geometry("pt")[["hid", "area_m2", "pt"]]
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
nodes, entry, snap, nbr, lk = {}, [], [], defaultdict(set), {}
with gzip.open("scenarios/kutno/network.xml.gz", "rb") as f:
    for _, el in etree.iterparse(f, tag=("node", "link")):
        if el.tag == "node":
            nodes[el.get("id")] = Point(float(el.get("x")), float(el.get("y")))
        else:
            t = {a.get("name"): a.text for a in el.iter("attribute")}.get("type")
            lk[el.get("id")] = (el.get("from"), el.get("to"), float(el.get("length")), float(el.get("freespeed")))
            nbr[el.get("from")].add(el.get("to")); nbr[el.get("to")].add(el.get("from"))
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


# --- D29: kierunek linku przypięcia wg trasy swobodnej (bez zawrotki na początku i końcu trasy) ---------------------
# Aktywność ma jeden link; na ulicy dwukierunkowej połowa agentów dostawała kierunek przeciwny do celu i zawracała (35% podróży).
# snap_mode = "route": kandydaci = najbliższy link i jego link odwrotny, wybór po najkrótszej trasie swobodnej (length/freespeed).
# Start liczy się od końca linku odjazdu, cel od początku linku przyjazdu wraz z jego przejechaniem (jak QSim). "nearest" = R9.
_by_nodes = {(lk[l][0], lk[l][1]): l for l in snap_ids}
REV = {l: _by_nodes.get((lk[l][1], lk[l][0])) for l in snap_ids}  # link odwrotny (ta sama para węzłów), jeśli jest w puli przypięcia
if P["snap_mode"] == "route":
    from scipy.sparse import csr_matrix
    from scipy.sparse.csgraph import dijkstra
    nid = {n: i for i, n in enumerate(nodes)}
    best = {}
    for l, (a_, b_, ln, fs) in lk.items():
        best[(nid[a_], nid[b_])] = min(best.get((nid[a_], nid[b_]), 1e18), ln / fs)
    gr = csr_matrix(([v for v in best.values()], ([k[0] for k in best], [k[1] for k in best])), shape=(len(nid), len(nid)))
    _row = {}

    def _t(n1, n2):
        i = nid[n1]
        if i not in _row:
            _row[i] = dijkstra(gr, directed=True, indices=i)
        return _row[i][nid[n2]]

    def cost(a, b):
        """czas swobodny: odjazd z linku a (od jego końca) do przyjazdu na link b (z jego przejechaniem)"""
        return _t(lk[a][1], lk[b][0]) + lk[b][2] / lk[b][3]

    def cand_lists(xs, ys):
        src, dst = snap_tree.query_nearest([Point(x, y) for x, y in zip(xs, ys)], all_matches=True)
        out = [set() for _ in xs]
        for s_, d_ in zip(src, dst):
            out[s_].add(snap_ids[d_])
        for c in out:
            c |= {REV[l] for l in list(c) if REV.get(l)}
        return [sorted(c) for c in out]


interior = area.buffer(-P["entry_zone_m"])
# audyt G5/K1: PBF obejmuje tylko łódzkie, więc DK92 (zach.) i DK60 (płn.) kończą się ślepo 1,9-2,3 km przed krawędzią obszaru.
# Ślepy koniec (węzeł z jednym sąsiadem) drogi wjazdowej to też granica sieci.
dead = {n for n, s in nbr.items() if len(s) == 1}
edge = lambda n: n in dead or not interior.contains(nodes[n])
border_links = entry
entry = pd.DataFrame([dict(link=l, x=nodes[b_].x, y=nodes[b_].y) for l, a_, b_ in border_links
                      if edge(a_) and area.contains(nodes[b_])
                      and nodes[b_].distance(KUTNO_CENTRE) < nodes[a_].distance(KUTNO_CENTRE)])
# D17/O1: wyjazd = lustro wjazdu (link tych klas kończący się w strefie granicy, skierowany od Kutna)
exits = pd.DataFrame([dict(link=l, x=nodes[b_].x, y=nodes[b_].y) for l, a_, b_ in border_links
                      if edge(b_) and area.contains(nodes[a_])
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
        c = homes_b[homes_b.pt.within(obwody[obwod])]
        if not len(c) and P["home_source"] == "bdot":  # D28: budynek na granicy obwodu ma punkt w sąsiednim (np. 6509902)
            d = homes_b.pt.distance(obwody[obwod])
            if d.min() <= P["home_nearest_max_m"]:
                c = homes_b[d == d.min()]
                print(f"obwód {obwod}: brak domu w obwodzie, najbliższy {c.hid.iloc[0]} w {d.min():.0f} m")
        _homes[obwod] = c
    return _homes[obwod]


for s in strata[strata.agents > 0].itertuples():
    if s.kind == "outbound":  # D17/O1: dom w Kutnie, obwód losowany wagą pracujących (D5); praca dobierana niżej
        p_ob = (ob.employed_base / ob.employed_base.sum()).to_numpy()
        for k, o in enumerate(rng.choice(ob.obwod_id.to_numpy(), size=s.agents, p=p_ob)):
            if len(homes_in(int(o))):
                h = pick_buildings(homes_in(int(o)), 1).iloc[0]
                people.append((f"o{s.key}_{k}", s.kind, s.key, h.pt.x, h.pt.y, None, h.hid, 0.0))
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
            people.append((f"{s.kind[0]}{s.key}_{k}", s.kind, s.key, h.pt.x, h.pt.y, None, h.hid, 0.0))
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
own_w = meta.work_link.isna()
meta["home_link_end"] = None
if P["snap_mode"] == "nearest":
    meta.loc[own, "home_link"] = snap_links(meta.home_x[own], meta.home_y[own])
    meta.loc[own_w, "work_link"] = snap_links(meta.work_x[own_w], meta.work_y[own_w])
    meta["home_link_end"] = meta.home_link
    meta["work_link_end"] = meta.work_link
else:
    # D29: dom na starcie i dom na końcu to dwie aktywności, więc mogą mieć różne linki; praca ma jeden link na przyjazd i odjazd.
    # Przyjeżdżający spoza powiatu (wjazd graniczny) kończą dzień na linku wyjazdowym tej samej drogi (lustro wjazdu).
    zroad = pd.read_csv("scenarios/kutno/demand/border_zones.csv").drop_duplicates("link").set_index("link").road
    ex_set = set(exits.link)
    all_by_nodes = {(v[0], v[1]): l for l, v in lk.items()}

    def mirror(l):
        r = all_by_nodes.get((lk[l][1], lk[l][0]))
        if r in ex_set:
            return r
        c = exits[exits.link.map(zroad) == zroad.get(l)]
        if not len(c):
            return l
        x, y = nodes[lk[l][1]].x, nodes[lk[l][1]].y
        return c.iloc[((c.x - x) ** 2 + (c.y - y) ** 2).argmin()].link

    hc = [None] * len(meta); wc = [None] * len(meta)
    ci = meta.index[own]; cj = meta.index[own_w]
    for i, c in zip(ci, cand_lists(meta.home_x[own], meta.home_y[own])):
        hc[i] = c
    for i, c in zip(cj, cand_lists(meta.work_x[own_w], meta.work_y[own_w])):
        wc[i] = c
    hl, hle, wl = [], [], []
    for i, r in enumerate(meta.itertuples()):
        Ha = hc[i] if hc[i] is not None else [r.home_link]            # linki odjazdu z domu
        He = hc[i] if hc[i] is not None else [mirror(r.home_link)]    # linki przyjazdu do domu
        W = wc[i] if wc[i] is not None else [r.work_link]
        w = min(W, key=lambda w_: min(cost(a, w_) for a in Ha) + min(cost(w_, d) for d in He))
        hl.append(min(Ha, key=lambda a: cost(a, w))); hle.append(min(He, key=lambda d: cost(w, d))); wl.append(w)
    meta["home_link"], meta["home_link_end"], meta["work_link"] = hl, hle, wl
    meta["work_link_end"] = meta.work_link
    if P["work_split"] == "on":
        # D31 (krok 4A): praca = dwie aktywności (przyjazd, odjazd) z osobnymi linkami, między nimi teleportowana noga walk o długości 0 m.
        # Jedna aktywność ma jeden link, więc dojazd i powrót zawracały przy pracy (52% i 25% podróży, D29). Kierunek przyjazdu dobierany
        # do linku odjazdu z domu, kierunek odjazdu do linku przyjazdu do domu (niezależnie). Wyjeżdżający: odjazd z linku wjazdowego tej drogi.
        en_set = set(entry.link)

        def mirror_in(l):
            r = all_by_nodes.get((lk[l][1], lk[l][0]))
            if r in en_set:
                return r
            c = entry[entry.link.map(zroad) == zroad.get(l)]
            if not len(c):
                return l
            x, y = nodes[lk[l][1]].x, nodes[lk[l][1]].y
            return c.iloc[((c.x - x) ** 2 + (c.y - y) ** 2).argmin()].link

        hl, hle, wl, wle = [], [], [], []
        for i, r in enumerate(meta.itertuples()):
            Ha = hc[i] if hc[i] is not None else [r.home_link]
            He = hc[i] if hc[i] is not None else [mirror(r.home_link)]
            Wa = wc[i] if wc[i] is not None else [r.work_link]
            Wd = wc[i] if wc[i] is not None else [mirror_in(r.work_link)]
            a_, wa_ = min(((x, y) for x in Ha for y in Wa), key=lambda xy: cost(*xy))
            wd_, d_ = min(((x, y) for x in Wd for y in He), key=lambda xy: cost(*xy))
            hl.append(a_); wl.append(wa_); wle.append(wd_); hle.append(d_)
        meta["home_link"], meta["home_link_end"], meta["work_link"], meta["work_link_end"] = hl, hle, wl, wle

# --- godzina wyjazdu (D10): przedział z udziałem z profilu, jednostajnie w przedziale ---------------------
prof = pd.read_csv(P["departure_profile"])
k = rng.choice(len(prof), size=len(meta), p=(prof.share_pct / prof.share_pct.sum()).to_numpy())
meta["dep_s"] = (prof.from_h.to_numpy()[k] * 3600 + rng.uniform(0, 1, len(meta)) * (prof.to_h - prof.from_h).to_numpy()[k] * 3600).astype(int)
# D16/A: przyjeżdżający spoza powiatu dostają godzinę z profilu jako moment wjazdu na granicę sieci (bez doliczania dojazdu)
meta["start_s"] = meta.dep_s

# --- D19/K2-2: ruch tła (lekkie), O-D z background_od.py, godzina z profilu Lisica --------------------------
# D20: to samo dla ciężkich (heavy_od, prefiks "h", profil heavy_pct). Lekkie losowane pierwsze, więc przy tym samym
# background_od ich plany są identyczne jak bez ciężkich.
BG_COLS = ["person", "o", "d", "o_link", "o_x", "o_y", "d_link", "d_x", "d_y", "start_s"]
border = pd.concat([entry, exits]).drop_duplicates("link").set_index("link")
_bld = {}


def ends(kind, zone, n, pool=b):
    """n końców podróży w strefie: link graniczny albo budynek gminy z puli (losowanie wagą powierzchni, jak D7/D11)."""
    if kind != "gmina":
        return [zone] * n, [border.x[zone]] * n, [border.y[zone]] * n
    if (zone, len(pool)) not in _bld:
        _bld[(zone, len(pool))] = pool[pool.pt.within(gmina_geom(zone))].set_geometry("pt")
    h = pick_buildings(_bld[(zone, len(pool))], n)
    return [None] * n, h.pt.x.tolist(), h.pt.y.tolist()


def background(path, prefix, profile_col, pool=b):
    if not path:
        return pd.DataFrame(columns=BG_COLS)
    od = pd.read_csv(path, dtype={"o": str, "d": str})
    ex = od.trips_day * P["sample"]
    od["agents"] = np.floor(ex).astype(int)
    rest = (ex - od.agents).sort_values(ascending=False, kind="stable")
    od.loc[rest.index[:round(ex.sum()) - od.agents.sum()], "agents"] += 1
    rows = []
    for r in od[od.agents > 0].itertuples():
        ol, ox, oy = ends(r.o_kind, r.o, r.agents, pool)
        dl, dx, dy = ends(r.d_kind, r.d, r.agents, pool)
        rows += [(f"{prefix}{r.o}_{r.d}_{k}", r.o, r.d, ol[k], ox[k], oy[k], dl[k], dx[k], dy[k]) for k in range(r.agents)]
    bg = pd.DataFrame(rows, columns=BG_COLS[:-1])
    hp = pd.read_csv(P["background_profile"])
    h = rng.choice(len(hp), size=len(bg), p=(hp[profile_col] / hp[profile_col].sum()).to_numpy())
    bg["start_s"] = (hp.hour_from.to_numpy()[h] * 3600 + rng.uniform(0, 3600, len(bg))).astype(int)
    if P["snap_mode"] == "nearest":
        for e in ("o", "d"):
            own = bg[f"{e}_link"].isna()
            bg.loc[own, f"{e}_link"] = snap_links(bg[f"{e}_x"][own], bg[f"{e}_y"][own])
    else:  # D29: kierunki linków początku i końca wg trasy swobodnej; wjazd i wyjazd graniczny zostają
        oc = {i: c for i, c in zip(bg.index[bg.o_link.isna()], cand_lists(bg.o_x[bg.o_link.isna()], bg.o_y[bg.o_link.isna()]))}
        dc = {i: c for i, c in zip(bg.index[bg.d_link.isna()], cand_lists(bg.d_x[bg.d_link.isna()], bg.d_y[bg.d_link.isna()]))}
        ol_, dl_ = [], []
        for i, r in bg.iterrows():
            O, D = oc.get(i, [r.o_link]), dc.get(i, [r.d_link])
            a, b_ = min(((a_, d_) for a_ in O for d_ in D), key=lambda ad: cost(*ad))
            ol_.append(a); dl_.append(b_)
        bg["o_link"], bg["d_link"] = ol_, dl_
    assert bg.person.is_unique and len(bg) == round(ex.sum())
    return bg


bg = background(P["background_od"], "t", "light_pct")
hv = background(P["heavy_od"], "h", "heavy_pct", b[b.work_any] if P.get("heavy_ends", "all") == "work" else b)  # audyt D9

# --- D32 (krok 4C): zakupy i usługi mieszkańców, osobne wyjścia home -> shop|service -> home (errands.py, własny seed) ----------------
er = pd.DataFrame()
if P["errands"] == "on":
    import errands
    er = errands.draw(P, homes_in, gmina_kutno)
    if P["snap_mode"] == "nearest":
        er["home_link"] = er["home_link_end"] = snap_links(er.home_x, er.home_y)
        er["dst_link"] = snap_links(er.dst_x, er.dst_y)
    else:  # jak D29: dom start i dom koniec to osobne linki, link celu = najkrótsza trasa tam i z powrotem
        hl_, hle_, dl_ = [], [], []
        for H, D in zip(cand_lists(er.home_x, er.home_y), cand_lists(er.dst_x, er.dst_y)):
            d = min(D, key=lambda w_: min(cost(a, w_) for a in H) + min(cost(w_, e) for e in H))
            hl_.append(min(H, key=lambda a: cost(a, d))); hle_.append(min(H, key=lambda e: cost(d, e))); dl_.append(d)
        er["home_link"], er["home_link_end"], er["dst_link"] = hl_, hle_, dl_

# --- D35 (wariant c): łańcuchy dnia pracujących mieszkańców, tylko auto (osobny generator chain_seed; "off" = R9.4 bajt w bajt) -------
# GUS Mobilność 2024, tabl. 10, łódzkie: podwożenie–praca / dom–praca = udział dojazdów do pracy z podwiezieniem (escort przed pracą);
# (dom–praca − praca–dom) / dom–praca × udział zakupów i usług wśród celów „dom–inne” = postój po pracy (zakupy/usługi przed powrotem).
# Postój po pracy przejmuje cel i typ wylosowanego osobnego wyjścia D32, które znika: łączna liczba zakupów zostaje zgodna z GUS.
if P.get("chains", "off") == "on":
    meta["esc_x"] = meta["esc_y"] = meta["stop_x"] = meta["stop_y"] = np.nan
    meta["esc_link"] = meta["stop_link"] = meta["stop_type"] = None
    crng = np.random.default_rng(P["chain_seed"])
    res = meta.index[meta.kind == "resident"]
    sch = pyogrio.read_dataframe(P["home_bdot"], encoding="utf-8", columns=["KATEGORIAISTNIENIA", "PRZEWAZAJACAFUNKCJABUDYNKU"])
    sch = sch[(sch.KATEGORIAISTNIENIA == "eksploatowany") & (sch.PRZEWAZAJACAFUNKCJABUDYNKU == P["chain_escort_function"])]
    sch = sch.geometry.representative_point()
    sch = sch[sch.within(gmina_kutno)].reset_index(drop=True)
    esc = crng.choice(res, size=round(P["chain_escort_share"] * len(res)), replace=False)
    near = sch.iloc[[int(sch.distance(Point(x, y)).idxmin()) for x, y in zip(meta.home_x[esc], meta.home_y[esc])]]  # ZAŁOŻENIE: najbliższa szkoła
    meta.loc[esc, "esc_x"], meta.loc[esc, "esc_y"] = near.x.to_numpy(), near.y.to_numpy()
    sv = np.flatnonzero(er.etype.isin(["shop", "service"]))  # D36: postój po pracy tylko z zakupów i usług
    k = min(len(sv), round(P["chain_after_work_share"] * len(res)))
    stop = crng.choice(res, size=k, replace=False)
    moved = er.iloc[np.sort(sv[crng.choice(len(sv), size=k, replace=False)])]
    meta.loc[stop, "stop_x"], meta.loc[stop, "stop_y"] = moved.dst_x.to_numpy(), moved.dst_y.to_numpy()
    meta.loc[stop, "stop_type"] = moved.etype.to_numpy()
    er = er.drop(moved.index).reset_index(drop=True)
    for col, (a_col, b_col) in (("esc", ("home_link", "work_link")), ("stop", ("work_link_end", "home_link_end"))):
        idx = meta.index[meta[f"{col}_x"].notna()]
        if P["snap_mode"] == "nearest":
            meta.loc[idx, f"{col}_link"] = snap_links(meta[f"{col}_x"][idx], meta[f"{col}_y"][idx])
        else:  # link postoju = najkrótsza trasa swobodna z poprzedniej aktywności i do następnej (jak D29)
            meta.loc[idx, f"{col}_link"] = [min(D, key=lambda d: cost(a, d) + cost(d, b_)) for D, a, b_ in
                                            zip(cand_lists(meta[f"{col}_x"][idx], meta[f"{col}_y"][idx]), meta[a_col][idx], meta[b_col][idx])]

# --- plans.xml.gz (bez tras; mtime=0, żeby sha256 był powtarzalny) ------------------------------------
if P["attributes"] == "on":  # D30: wiek, płeć, prawo jazdy, carAvail; osobny generator (attr_seed), reszta planów bez zmian
    from attributes import Attrs
    meta = meta.join(Attrs(P).agents(meta))
root = etree.Element("population")
for r in meta.itertuples():
    person = etree.SubElement(root, "person", id=r.person)
    attrs = etree.SubElement(person, "attributes")  # subpopulation wymagana przez TripAnalysis (SimWrapper)
    for name, val in (("subpopulation", "person"), ("kind", r.kind)):
        etree.SubElement(attrs, "attribute", name=name, **{"class": "java.lang.String"}).text = val
    if P["attributes"] == "on":
        etree.SubElement(attrs, "attribute", name="age", **{"class": "java.lang.Integer"}).text = str(r.age)
        for name, val in (("sex", r.sex), ("license", r.license), ("carAvail", r.carAvail)):
            etree.SubElement(attrs, "attribute", name=name, **{"class": "java.lang.String"}).text = val
    plan = etree.SubElement(person, "plan", selected="yes")
    home = dict(type="home", link=r.home_link, x=f"{r.home_x:.1f}", y=f"{r.home_y:.1f}")
    etree.SubElement(plan, "activity", **home, end_time=f"{r.start_s // 3600:02d}:{r.start_s // 60 % 60:02d}:{r.start_s % 60:02d}")
    etree.SubElement(plan, "leg", mode="car")
    if isinstance(getattr(r, "esc_link", None), str):  # D35: podwiezienie przed pracą
        etree.SubElement(plan, "activity", type="escort", link=r.esc_link, x=f"{r.esc_x:.1f}", y=f"{r.esc_y:.1f}", max_dur=P["chain_escort_dur"])
        etree.SubElement(plan, "leg", mode="car")
    etree.SubElement(plan, "activity", type="work", link=r.work_link, x=f"{r.work_x:.1f}", y=f"{r.work_y:.1f}", max_dur=P["work_max_dur"])
    if r.work_link_end != r.work_link:  # D31: osobny link odjazdu z pracy (aktywność 1 s, noga walk 0 m)
        etree.SubElement(plan, "leg", mode="walk")
        etree.SubElement(plan, "activity", type="work", link=r.work_link_end, x=f"{r.work_x:.1f}", y=f"{r.work_y:.1f}", max_dur="00:00:01")
    etree.SubElement(plan, "leg", mode="car")
    if isinstance(getattr(r, "stop_link", None), str):  # D35: zakupy lub usługi po pracy
        etree.SubElement(plan, "activity", type=r.stop_type, link=r.stop_link, x=f"{r.stop_x:.1f}", y=f"{r.stop_y:.1f}", max_dur=P["errand_dur"])
        etree.SubElement(plan, "leg", mode="car")
    etree.SubElement(plan, "activity", **{**home, "link": r.home_link_end})
for sub, df in (("tlo", bg), ("ciezkie", hv)):  # D19/K2-2, D20: jedna podróż tlo_start -> tlo_end
    for r in df.itertuples():
        person = etree.SubElement(root, "person", id=r.person)
        attrs = etree.SubElement(person, "attributes")
        for name, val in (("subpopulation", sub), ("kind", sub)):
            etree.SubElement(attrs, "attribute", name=name, **{"class": "java.lang.String"}).text = val
        plan = etree.SubElement(person, "plan", selected="yes")
        etree.SubElement(plan, "activity", type="tlo_start", link=r.o_link, x=f"{r.o_x:.1f}", y=f"{r.o_y:.1f}",
                         end_time=f"{r.start_s // 3600:02d}:{r.start_s // 60 % 60:02d}:{r.start_s % 60:02d}")
        etree.SubElement(plan, "leg", mode="car")
        etree.SubElement(plan, "activity", type="tlo_end", link=r.d_link, x=f"{r.d_x:.1f}", y=f"{r.d_y:.1f}")
for r in er.itertuples():  # D32: kierowca jedzie autem z domu do sklepu lub punktu usługowego i wraca
    person = etree.SubElement(root, "person", id=r.person)
    attrs = etree.SubElement(person, "attributes")
    for name, val in (("subpopulation", "person"), ("kind", "errand")):
        etree.SubElement(attrs, "attribute", name=name, **{"class": "java.lang.String"}).text = val
    etree.SubElement(attrs, "attribute", name="age", **{"class": "java.lang.Integer"}).text = str(r.age)
    for name, val in (("sex", r.sex), ("license", r.license), ("carAvail", r.carAvail)):
        etree.SubElement(attrs, "attribute", name=name, **{"class": "java.lang.String"}).text = val
    plan = etree.SubElement(person, "plan", selected="yes")
    home = dict(type="home", x=f"{r.home_x:.1f}", y=f"{r.home_y:.1f}")
    etree.SubElement(plan, "activity", **home, link=r.home_link, end_time=f"{r.start_s // 3600:02d}:{r.start_s // 60 % 60:02d}:{r.start_s % 60:02d}")
    etree.SubElement(plan, "leg", mode="car")
    etree.SubElement(plan, "activity", type=r.etype, link=r.dst_link, x=f"{r.dst_x:.1f}", y=f"{r.dst_y:.1f}",
                     max_dur=r.dur if isinstance(getattr(r, "dur", None), str) else P["errand_dur"])  # D36: czas wg typu
    etree.SubElement(plan, "leg", mode="car")
    etree.SubElement(plan, "activity", **home, link=r.home_link_end)
if len(hv):  # D20: pojazdy z pliku (qsim.vehiclesSource=fromVehiclesData): osobowy pce 1, ciężarowy heavy_pce i 80 km/h
    for person in root:
        etree.SubElement(person[0], "attribute", name="vehicles", **{"class": "org.matsim.vehicles.PersonVehicles"}).text =             '{"car":"%s"}' % person.get("id")
xml = etree.tostring(root, xml_declaration=True, encoding="utf-8", pretty_print=True,
                     doctype='<!DOCTYPE population SYSTEM "http://www.matsim.org/files/dtd/population_v6.dtd">')
with open(OUT, "wb") as f, gzip.GzipFile(fileobj=f, mode="wb", mtime=0, filename="") as gz:
    gz.write(xml)
stem = OUT.name.removesuffix(".xml.gz")
meta.to_csv(OUT.with_name(stem + "_meta.csv"), index=False)
strata.to_csv(OUT.with_name(stem + "_strata.csv"), index=False)
bg.to_csv(OUT.with_name(stem + "_tlo.csv"), index=False)
if len(er):
    er.to_csv(OUT.with_name(stem + "_errands.csv"), index=False)
if len(hv):
    hv.to_csv(OUT.with_name(stem + "_ciezkie.csv"), index=False)
    NS = "http://www.matsim.org/files/dtd"
    vd = etree.Element("vehicleDefinitions", nsmap={None: NS, "xsi": "http://www.w3.org/2001/XMLSchema-instance"})
    vd.set("{http://www.w3.org/2001/XMLSchema-instance}schemaLocation", f"{NS} {NS}/vehicleDefinitions_v2.0.xsd")
    for tid, length, vmax, pce in (("car", 7.5, None, 1.0), ("ciezki", 15.0, 80 / 3.6, P["heavy_pce"])):
        vt = etree.SubElement(vd, "vehicleType", id=tid)
        etree.SubElement(vt, "capacity", seats="1", standingRoomInPersons="0")
        etree.SubElement(vt, "length", meter=str(length))
        etree.SubElement(vt, "width", meter="2.5" if tid == "ciezki" else "1.0")
        if vmax:
            etree.SubElement(vt, "maximumVelocity", meterPerSecond=f"{vmax:.4f}")
        etree.SubElement(vt, "passengerCarEquivalents", pce=str(pce))
        etree.SubElement(vt, "networkMode", networkMode="car")
    heavy_ids = set(hv.person)
    for person in root:
        etree.SubElement(vd, "vehicle", id=person.get("id"), type="ciezki" if person.get("id") in heavy_ids else "car")
    with open(OUT.with_name(stem + "_vehicles.xml.gz"), "wb") as f, gzip.GzipFile(fileobj=f, mode="wb", mtime=0, filename="") as gz:
        gz.write(etree.tostring(vd, xml_declaration=True, encoding="utf-8", pretty_print=True))
print(f"{OUT}: {len(meta)} osób (cel {target}); budynki mieszk. {len(homes_b)}, pracy {len(work_b)}, "
      f"linki wjazdowe {len(entry)}, wyjazdowe {len(exits)}; wg rodzaju {meta.kind.value_counts().to_dict()}; odcięte gminy > {P['max_border_km']} km: {int(strata.excluded.sum())} "
      f"({strata.n[strata.excluded].sum():.0f} os. w 100%); jobs_total {P["jobs_total"]}; tło {len(bg)}; ciężkie {len(hv)} (pce {P.get("heavy_pce")}); źródła domów: {meta.home_src.str.split('_').str[0].value_counts().to_dict()}")
