"""G5/D22: walidacja czasów przejazdu i prędkości bazy R6 względem TomTom (i HERE). Walidacja, nie kalibracja.

Podkomendy (uv run python pipeline/traffic_providers.py <cmd> ...):
  sample                      próbka par, korytarzy i segmentów + podział na zestawy -> OUT/pairs.csv, segments.csv, split.csv
  run <tomtom|here> [--dry-run]
                              cały przebieg w jednym procesie: partie probe (test pkt 4.1), main (pary i korytarze × okna),
                              flow (segmenty, stan z chwili zapytania) -> metryki (traffic_metrics.compare) -> niezależna
                              kontrola (OUT/check_niezalezny.py, dane przez stdin) -> na dysk tylko agregaty:
                              OUT/metrics_<dostawca>.csv, przebieg_<dostawca>.json, wykres.

D22, wariant A (regulamin TomTom pkt 11.4, 11.6.1, 11.6.10, odczyt 2026-10-18): odpowiedzi dostawcy są tylko w pamięci
procesu. Nie ma surowych plików ani cache; wznowienie = ponowne requesty w budżecie. Do repo trafiają same agregaty
(bez czasów i prędkości dostawcy per para lub segment). Limit 5 QPS, backoff przy 429, budżet 400 liczony z logu.
Klucze: zmienne TOMTOM_API_KEY / HERE_API_KEY albo plik .env (gitignored). Log OUT/fetch_<dostawca>.log: czas UTC, kod HTTP,
licznik, partia, Cache-Control i URL z kluczem zastąpionym przez ***; bez treści odpowiedzi.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
import shapely
import zstandard
from lxml import etree
from pyproj import Transformer

OUT = Path("reports/etap2/g5_czasy_tomtom")
RUN = Path("output/g5r6_25pct_s4711")  # run, z którego bierzemy nogi i trasy modelu (plany seed 4711)
META = "scenarios/kutno/plans_g5r6_25pct_"
SEED = 4711  # config/kutno.toml [plans] seed
TO_WGS = Transformer.from_crs(2180, 4326, always_xy=True)  # x = E, y = N -> lon, lat (jedyna transformacja)

# Okna dnia roboczego (godzina z największym udziałem): rano 7-8 = max GBR 2022 dom-praca (32,3%) i Lisica lekkie (6,34%);
# popołudnie 15-16 = max Lisica lekkie (8,27%); południe 12-13. Zapytanie o środku okna.
WINDOWS = {"rano": "07:30", "poludnie": "12:30", "popoludnie": "15:30"}
# Dzień zapytań: najbliższy wtorek roboczy (2026-10-20, CEST +02:00). Model = uśredniony dzień roboczy, nie data.
DAY = "2026-10-20"
TZ = "+02:00"
# ZAŁOŻENIE: ciężarowe w trybie truck: 80 km/h jak w modelu (D20), wymiary typu `ciezki` (D9: 15 m × 2,5 m), pojazd
# komercyjny; masa, nacisk osi i wysokość = 0 (ograniczenia nieuwzględniane), bo model ich nie ma. Wariant: masa 40 t.
TRUCK = dict(vehicleMaxSpeed=80, vehicleLength=15, vehicleWidth=2.5, vehicleCommercial="true")
QPS = {"tomtom": 5, "here": 5}  # TomTom FAQ: 5-50 zależnie od API; bierzemy dolną granicę dla obu endpointów
BUDGET = 2000  # łącznie: 1237 do D23 krok 2; podniesione na polecenie użytkownika (krok 5 ok. 390)
BUDGET_DAY = 2000  # limit konta TomTom: 2 500 non-tile na dobę (informacja użytkownika 2026-10-18), z zapasem


def zread(p):
    return zstandard.ZstdDecompressor().stream_reader(open(p, "rb"))


def links():
    L = pd.read_csv(RUN / "output_links.csv.zst", sep=";", dtype={"link": str, "from_node": str, "to_node": str, "origid": str})
    g = shapely.from_wkt(L.geometry)
    L["x0"], L["y0"] = shapely.get_x(shapely.get_point(g, 0)), shapely.get_y(shapely.get_point(g, 0))
    L["x1"], L["y1"] = shapely.get_x(shapely.get_point(g, -1)), shapely.get_y(shapely.get_point(g, -1))
    L["ff"] = np.floor(L.length / L.freespeed) + 1  # I1: czas swobodny jak w QSim
    return L.set_index("link")


def wgs(x, y):
    lon, lat = TO_WGS.transform(x, y)
    return round(lat, 6), round(lon, 6)


def routes(persons):
    """Trasa pierwszej nogi car z experienced_plans runu (lista linków) dla podanych osób."""
    out = {}
    for _, p in etree.iterparse(zread(RUN / "output_experienced_plans.xml.zst"), tag="person"):
        pid = p.get("id")
        if pid in persons:
            r = next(lg.find("route") for lg in p.iter("leg") if lg.get("mode") == "car")
            out[pid] = r.text.split()
        p.clear()
    return out


def cmd_sample():
    L = links()
    rng = np.random.default_rng(SEED)
    legs = pd.read_csv(RUN / "output_legs.csv.zst", sep=";", dtype={"start_link": str, "end_link": str})
    legs = legs[(legs["mode"] == "car") & (legs.distance >= 1000)]  # pomijamy nogi < 1 km
    legs = legs[legs.trip_id.str.endswith("_1")]  # r/c/o: dom -> praca; t/h mają jedną podróż
    meta = pd.read_csv(META + "meta.csv").set_index("person")
    k = legs.person.str[0]
    ok = (k.isin(["t", "h", "r"])
          | ((k == "c") & legs.person.map(meta.home_src).eq("entry"))  # przyjeżdżający: link wjazdu na granicy -> praca
          | ((k == "o") & legs.person.map(meta.work_src).eq("exit")))  # wyjeżdżający: dom -> link wyjazdu na granicy
    legs = legs[ok].assign(kind=k[ok])
    n = {"r": 8, "c": 6, "o": 4, "t": 6, "h": 6}  # ok. 30 par, warstwowo po rodzaju
    s = pd.concat([legs[legs.kind == q].sample(m, random_state=rng.integers(1 << 31)) for q, m in n.items()])
    R = routes(set(s.person))
    rows = []
    for _, l in s.iterrows():
        a, b = l.start_link, l.end_link
        rows.append(dict(id=f"P_{l.person}", kind=l.kind, person=l.person, start_link=a, end_link=b,
                         o_x=L.x1[a], o_y=L.y1[a], d_x=L.x1[b], d_y=L.y1[b], model_dep_s4711=l.dep_time,
                         model_km=round(l.distance / 1000, 2), mode="truck" if l.kind == "h" else "car", route=" ".join(R[l.person])))

    # korytarze: końce = linki liczników GPR (gpr_linki.csv) albo centrum (ZAŁOŻENIE: centroid gminy Kutno, najbliższy
    # link primary/secondary/tertiary). Z dwóch linków licznika (oba kierunki) bierzemy ten, z którego trasa swobodna do celu
    # jest krótsza. Trasa modelu = najszybsza ścieżka po czasie swobodnym (tak router MATSim liczy pustą sieć).
    G = nx.DiGraph()
    G.add_weighted_edges_from(zip(L.from_node, L.to_node, L.ff), link=None)
    for lk, a, b in zip(L.index, L.from_node, L.to_node):
        G[a][b]["link"] = lk
    gpr = pd.read_csv("scenarios/kutno/validation/gpr_linki.csv", dtype={"nr": str, "link": str})
    gm = shapely.from_geojson(Path("scenarios/kutno/area/gmina.geojson").read_text(encoding="utf-8"))
    c = shapely.centroid(gm)
    cand = L[L.type.isin(["primary", "secondary", "tertiary"])]
    d = np.hypot((cand.x0 + cand.x1) / 2 - c.x, (cand.y0 + cand.y1) / 2 - c.y)
    centre = list(cand.index[np.argsort(d.values)[:2]])
    end = lambda nr: list(gpr.link[gpr.nr == nr]) if nr != "C" else centre
    corridors = [("K_dk92z_in", "91123", "C"), ("K_dk92w_in", "91869", "C"), ("K_dk60n_in", "91878", "C"),
                 ("K_dk60s_in", "91115", "C"), ("K_przejazd_we", "91869", "91124"), ("K_przejazd_ew", "91124", "91869"),
                 ("K_a1_ns", "71410", "91821"), ("K_a1_sn", "91821", "71410"), ("K_dk92z_out", "C", "91123"),
                 ("K_krosniewice", "91892", "91119")]

    def path(a, b):
        t, p = nx.single_source_dijkstra(G, L.to_node[a], L.from_node[b])
        return t + L.ff[b], [a] + [G[u][v]["link"] for u, v in zip(p, p[1:])] + [b]

    for cid, oa, ob in corridors:
        a, b = min(((a, b) for a in end(oa) for b in end(ob)), key=lambda ab: path(*ab)[0])
        p = path(a, b)[1]
        rows.append(dict(id=cid, kind="korytarz", person="", start_link=a, end_link=b, o_x=L.x1[a], o_y=L.y1[a],
                         d_x=L.x1[b], d_y=L.y1[b], model_dep_s4711="", model_km=round(L.length[p[1:]].sum() / 1000, 2),
                         mode="car", route=" ".join(p)))
    P = pd.DataFrame(rows)
    P[["o_lat", "o_lon"]] = [wgs(x, y) for x, y in zip(P.o_x, P.o_y)]
    P[["d_lat", "d_lon"]] = [wgs(x, y) for x, y in zip(P.d_x, P.d_y)]

    # segmenty: środek linku, klasy wg typu OSM i położenia (miasto = gmina Kutno; poza miastem = poza gminą i towns.wkt)
    towns = shapely.from_wkt(Path("scenarios/kutno/area/towns.wkt").read_text().strip())
    mx, my = (L.x0 + L.x1) / 2, (L.y0 + L.y1) / 2
    pts = shapely.points(mx, my)
    in_city, in_town = shapely.contains(gm, pts), shapely.contains(towns, pts)
    out = ~in_city & ~in_town
    t = L.type
    cls = pd.Series("", index=L.index)
    cls[in_city & t.isin(["primary", "secondary", "tertiary", "residential"])] = "miasto"
    cls[t.eq("motorway")] = "A1"
    cls[out & t.eq("primary")] = "DK_poza"  # ZAŁOŻENIE: DK ≈ primary (sieć nie ma numeru drogi)
    cls[out & t.eq("secondary")] = "DW_poza"  # ZAŁOŻENIE: DW ≈ secondary
    cls[out & t.isin(["tertiary", "unclassified"])] = "tert_uncl_poza"
    cand = L[(cls != "") & (L.length >= 300) & L.index.str.endswith("f")].assign(cls=cls, mx=mx, my=my)
    cand = cand.drop_duplicates("origid")
    ns = {"miasto": 6, "DK_poza": 5, "DW_poza": 4, "A1": 3, "tert_uncl_poza": 7}
    S = pd.concat([cand[cand.cls == q].sample(m, random_state=rng.integers(1 << 31)) for q, m in ns.items()])
    S = S.reset_index()[["link", "cls", "type", "length", "freespeed", "allowed_speed", "speed_source", "mx", "my"]]
    S["freespeed_kmh"] = (S.freespeed * 3.6).round(1)
    S["allowed_kmh"] = (S.allowed_speed * 3.6).round(1)
    S = S.drop(columns=["freespeed", "allowed_speed"])
    S[["lat", "lon"]] = [wgs(x, y) for x, y in zip(S.mx, S.my)]
    S.insert(0, "id", "S_" + S.link)

    # podział przestrzenny (pkt 4.1: przyszły departAt = typowy profil historyczny, kolejne dni nie są niezależne):
    # 1/3 każdej warstwy (rodzaj pary / korytarz / klasa segmentu) wyłącznie do walidacji, losowanie z seeda.
    sp = []
    for ids, strata in ((P.id, P.kind), (S.id, S.cls)):
        for q in sorted(strata.unique()):
            v = ids[strata == q].tolist()
            rng.shuffle(v)
            nv = round(len(v) / 3)
            sp += [dict(id=i, warstwa=q, zestaw="walidacja" if j < nv else "analiza") for j, i in enumerate(v)]
    OUT.mkdir(parents=True, exist_ok=True)
    P.round({"o_x": 1, "o_y": 1, "d_x": 1, "d_y": 1}).to_csv(OUT / "pairs.csv", index=False, lineterminator="\n")
    S.round({"length": 1, "mx": 1, "my": 1}).to_csv(OUT / "segments.csv", index=False, lineterminator="\n")
    pd.DataFrame(sp).to_csv(OUT / "split.csv", index=False, lineterminator="\n")
    print(P.groupby("kind").size(), S.groupby("cls").size(), pd.DataFrame(sp).groupby(["warstwa", "zestaw"]).size(), sep="\n")


# ---------------------------------------------------------------- pobieranie
GROUPS = ["A", "B", "C", "D", "E", "F"]  # D23, reports/etap2/g5_predkosci_d23/plan.md §1


def speed_groups(L):
    """Grupa D23 linku: typ OSM bez _link i położenie środka linku (miasto = towns.wkt, jak towns w CreateKutnoNetwork, D13)."""
    towns = shapely.from_wkt(Path("scenarios/kutno/area/towns.wkt").read_text().strip())
    urb = shapely.contains(towns, shapely.points((L.x0 + L.x1) / 2, (L.y0 + L.y1) / 2))
    t = L.type.str.replace("_link", "")
    return pd.Series(np.select([t.eq("motorway"),
                                ~urb & t.isin(["trunk", "primary", "secondary"]), ~urb & t.isin(["tertiary", "unclassified"]),
                                ~urb & t.isin(["residential", "living_street"]),
                                urb & t.isin(["trunk", "primary", "secondary", "tertiary"]),
                                urb & t.isin(["residential", "unclassified", "living_street"])],
                               GROUPS, "inne"), index=L.index)


def cmd_sample_d23(extra=None):
    """D23 krok 1: dobór tras z przewagą (>= 50% długości) każdej grupy, aż do >= 12 tras w analizie i >= 6 w walidacji
    na grupę (licząc trasy już w próbce). Trasa = najszybsza po czasie swobodnym sieci R6 (jak korytarze), długość 3-15 km
    (TAG M3.1 §4.3.3), dla D i F od 2 km. Końce: linki bez motorway/trunk/łącznic/zawrotek (jak przypinanie aktywności).
    Jedna trasa na link startowy. Nowe trasy dopisywane do pairs.csv i split.csv (stare wiersze bez zmian).
    extra = (grupa, n_analiza, n_walidacja): dobór dodatkowych tras jednej grupy (krok 2, decyzja użytkownika: C miało 11 tras)."""
    L = links()
    L["grp"] = speed_groups(L)
    P = pd.read_csv(OUT / "pairs.csv", dtype={"start_link": str, "end_link": str})
    sp = pd.read_csv(OUT / "split.csv")
    assert extra or not P.kind.str.startswith("D23").any(), "trasy D23 już są w pairs.csv"
    zs = sp.set_index("id").zestaw

    def share(route):
        r = L.loc[route[1:]]
        s = r.groupby("grp").length.sum()
        return s.idxmax(), s.max() / r.length.sum(), r.length.sum() / 1000

    have = {(g, z): 0 for g in GROUPS for z in ("analiza", "walidacja")}
    for _, p in P.iterrows():
        g, sh, _ = share(p.route.split())
        if sh >= 0.5 and g in GROUPS:
            have[(g, zs[p.id])] += 1
    need = {g: max(0, 12 - have[(g, "analiza")]) + max(0, 6 - have[(g, "walidacja")]) for g in GROUPS}
    print("istniejące trasy z przewagą grupy (analiza, walidacja):", {g: (have[(g, 'analiza')], have[(g, 'walidacja')]) for g in GROUPS})
    if extra:
        need = {g: (extra[1] + extra[2] if g == extra[0] else 0) for g in GROUPS}
    print("potrzebne nowe:", need)

    G = nx.DiGraph()
    for lk, a, b, t in zip(L.index, L.from_node, L.to_node, L.ff):
        G.add_edge(a, b, weight=t, link=lk)
    ok_end = ~L.type.isin(["motorway", "motorway_link", "trunk", "trunk_link", "boundary_turnaround"])
    ends = L[ok_end]
    by_from = ends.groupby("from_node").groups
    rng = np.random.default_rng(SEED + 23 + (1 if extra else 0))  # seed z config/kutno.toml, przesunięty dla D23 (+1: dobór)
    used = set(P.start_link)
    found = {g: [] for g in GROUPS}
    tries = 0
    while any(len(found[g]) < need[g] for g in GROUPS) and tries < 4000:
        tries += 1
        o = ends.index[rng.integers(len(ends))]
        if o in used:
            continue
        dist, paths = nx.single_source_dijkstra(G, L.to_node[o], cutoff=1500)
        cand = [d for n in dist for d in by_from.get(n, []) if d != o]
        rng.shuffle(cand)
        for d in cand[:400]:
            p = paths[L.from_node[d]]
            route = [o] + [G[u][v]["link"] for u, v in zip(p, p[1:])] + [d]
            g, sh, km = share(route)
            lo = 2 if g in ("D", "F") else 3
            if g in GROUPS and sh >= 0.5 and lo <= km <= 15 and len(found[g]) < need[g]:
                found[g].append((o, d, route, km, sh))
                break  # jedna trasa na link startowy
    print(f"losowań startów: {tries}; znalezione:", {g: len(v) for g, v in found.items()})

    rows, srows = [], []
    for g in GROUPS:
        lst = found[g]
        rng.shuffle(lst)
        nv = extra[2] if extra else max(0, 6 - have[(g, "walidacja")])
        off = int((P.kind == f"D23_{g}").sum())
        for i, (o, d, route, km, sh) in enumerate(lst):
            rid = f"D23{g}_{i + off:02d}"
            rows.append(dict(id=rid, kind=f"D23_{g}", person="", start_link=o, end_link=d, o_x=L.x1[o], o_y=L.y1[o],
                             d_x=L.x1[d], d_y=L.y1[d], model_dep_s4711="", model_km=round(km, 2), mode="car", route=" ".join(route)))
            srows.append(dict(id=rid, warstwa=f"D23_{g}", zestaw="walidacja" if i < nv else "analiza"))
    N = pd.DataFrame(rows)
    N[["o_lat", "o_lon"]] = [wgs(x, y) for x, y in zip(N.o_x, N.o_y)]
    N[["d_lat", "d_lon"]] = [wgs(x, y) for x, y in zip(N.d_x, N.d_y)]
    N = N.round({"o_x": 1, "o_y": 1, "d_x": 1, "d_y": 1})
    with open(OUT / "pairs.csv", "a", encoding="utf-8", newline="") as f:
        N[P.columns].to_csv(f, header=False, index=False, lineterminator="\n")
    with open(OUT / "split.csv", "a", encoding="utf-8", newline="") as f:
        pd.DataFrame(srows).to_csv(f, header=False, index=False, lineterminator="\n")
    print(pd.DataFrame(srows).groupby(["warstwa", "zestaw"]).size())


def api_key(provider):
    name = provider.upper() + "_API_KEY"
    if os.environ.get(name):
        return os.environ[name]
    if Path(".env").exists():
        for line in Path(".env").read_text(encoding="utf-8").splitlines():
            if line.startswith(name + "="):
                return line.split("=", 1)[1].strip().strip("\"'") or None  # wartość w cudzysłowie (styl .env)
    return None


def requests_for(provider, batch):
    """Lista (endpoint, params, meta) bez klucza API."""
    P = pd.read_csv(OUT / "pairs.csv")
    S = pd.read_csv(OUT / "segments.csv")
    reqs = []
    if provider == "tomtom":
        def route(r, when):
            ep = f"https://api.tomtom.com/routing/1/calculateRoute/{r.o_lat},{r.o_lon}:{r.d_lat},{r.d_lon}/json"
            p = dict(departAt=when, computeTravelTimeFor="all", traffic="true", routeType="fastest",
                     routeRepresentation="polyline", coordinatePrecision="full", travelMode=r["mode"])
            if r["mode"] == "truck":
                p.update(TRUCK)
            return ep, p
        flow = lambda s: ("https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/22/json",
                          dict(point=f"{s.lat},{s.lon}", unit="kmph"))
    else:
        def route(r, when):
            p = dict(transportMode=r["mode"], origin=f"{r.o_lat},{r.o_lon}", destination=f"{r.d_lat},{r.d_lon}",
                     departureTime=when, routingMode="fast", **{"return": "summary,polyline,typicalDuration"})
            if r["mode"] == "truck":
                p.update({"vehicle[speedCap]": round(80 / 3.6, 2), "vehicle[length]": 1500, "vehicle[width]": 250})
            return "https://router.hereapi.com/v8/routes", p
        flow = lambda s: ("https://data.traffic.hereapi.com/v7/flow",
                          {"in": f"circle:{s.lat},{s.lon};r=30", "locationReferencing": "shape"})
    if batch == "probe":  # pkt 4.1: ta sama para, przeszłość / teraz / dwa przyszłe wtorki (inny offset: koniec CEST 25.10)
        r = P[P.kind == "korytarz"].iloc[0]
        for when in ["2026-10-13T07:30:00+02:00", "now", f"{DAY}T07:30:00{TZ}", "2026-10-27T07:30:00+01:00"]:
            ep, p = route(r, when)
            reqs.append((ep, p, dict(id=r.id, when=when)))
    elif batch in ("main", "fit"):
        if batch == "fit":  # D23 krok 2: tylko zestaw analizy (walidacja nie może wpłynąć na f_g)
            sp = pd.read_csv(OUT / "split.csv").set_index("id").zestaw
            P = P[P.id.map(sp) == "analiza"]
        for _, r in P.iterrows():
            for w, hm in WINDOWS.items():
                ep, p = route(r, f"{DAY}T{hm}:00{TZ}")
                reqs.append((ep, p, dict(id=r.id, okno=w)))
    elif batch == "flow":
        for _, s in S.iterrows():
            ep, p = flow(s)
            reqs.append((ep, p, dict(id=s.id)))
    return reqs


def used_requests(provider, day=None):
    """Licznik zużycia = liczba wierszy w logu requestów (log zostaje między przebiegami, odpowiedzi nie); day = 'RRRR-MM-DD' UTC."""
    f = OUT / f"fetch_{provider}.log"
    if not f.exists():
        return 0
    return sum(1 for line in f.open(encoding="utf-8") if day is None or line.startswith(day))


def fetch(provider, batch, dry=False, test=False):
    """Requesty partii; odpowiedzi tylko w pamięci procesu (D22, wariant A: regulamin TomTom 11.4 zabrania przechowywania).
    Wznowienie przerwanego przebiegu = ponowne requesty (bez cache na dysku); budżet liczony z logu."""
    reqs = requests_for(provider, batch)
    if test:  # --test: 1 para × 3 okna i 2 segmenty, sprawdza całą ścieżkę kodu na prawdziwych odpowiedziach
        reqs = reqs[:3] if batch in ("main", "fit") else reqs[:2] if batch == "flow" else reqs
    used = used_requests(provider)
    print(f"{provider}/{batch}: requestów {len(reqs)}; zużyte dotąd {used}, budżet {BUDGET}")
    if dry:
        return []
    today = used_requests(provider, datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    if used + len(reqs) > BUDGET or today + len(reqs) > BUDGET_DAY:
        sys.exit(f"przekroczony budżet requestów (łącznie {used}/{BUDGET}, dziś UTC {today}/{BUDGET_DAY}), przerywam")
    key = api_key(provider)
    if not key:
        sys.exit(f"brak {provider.upper()}_API_KEY (zmienna środowiskowa albo .env)")
    kparam = "key" if provider == "tomtom" else "apiKey"
    recs = []
    with (OUT / f"fetch_{provider}.log").open("a", encoding="utf-8") as log:
        for ep, p, meta in reqs:
            url = ep + "?" + urllib.parse.urlencode({**p, kparam: key})
            masked = ep + "?" + urllib.parse.urlencode({**p, kparam: "***"})
            for attempt in range(6):
                t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                try:
                    with urllib.request.urlopen(url, timeout=60) as resp:
                        code, body, hdr = resp.status, resp.read().decode("utf-8"), dict(resp.headers)
                except urllib.error.HTTPError as e:
                    code, body, hdr = e.code, e.read().decode("utf-8", "replace"), dict(e.headers)
                used += 1
                assert key not in masked
                # log: czas UTC, kod HTTP, licznik, batch, Cache-Control, URL z kluczem ***; bez treści odpowiedzi
                log.write(f"{t0}\t{code}\t{used}\t{batch}\t{hdr.get('Cache-Control')}\t{masked}\n")
                log.flush()
                if code in (401, 403):  # zły klucz: przerwij od razu, nie zużywaj budżetu (pierwszy przebieg: 149 × 401)
                    sys.exit(f"HTTP {code} (uwierzytelnienie), przerywam po {used} requestach")
                if code != 429:
                    break
                time.sleep(2 ** attempt)  # backoff przy 429
            try:
                body = json.loads(body)
            except ValueError:
                pass
            recs.append(dict(utc=t0, http=code, meta=meta, body=body, cache_control=hdr.get("Cache-Control")))
            time.sleep(1 / QPS[provider])
    return recs


def probe_summary(recs):
    """Pkt 4.1: przeszłość / teraz / dwa przyszłe wtorki dla jednego korytarza. Do raportu tylko kody i ilorazy."""
    out = {}
    s = {r["meta"]["when"]: r for r in recs}
    get = lambda r: r["body"]["routes"][0]["summary"] if r["http"] == 200 else None
    for w, r in s.items():
        x = get(r)
        out[w] = dict(http=r["http"], blad=None if x else str(r["body"])[:200],
                      departureTime=x.get("departureTime") if x else None,
                      tt_do_hist=round(x["travelTimeInSeconds"] / x["historicTrafficTravelTimeInSeconds"], 4) if x else None,
                      live_do_hist=round(x["liveTrafficIncidentsTravelTimeInSeconds"] / x["historicTrafficTravelTimeInSeconds"], 4) if x else None)
    a, b = get(s[f"{DAY}T07:30:00{TZ}"]), get(s["2026-10-27T07:30:00+01:00"])
    if a and b:
        out["hist_20_10_do_27_10"] = round(a["historicTrafficTravelTimeInSeconds"] / b["historicTrafficTravelTimeInSeconds"], 4)
        out["noTraffic_20_10_do_27_10"] = round(a["noTrafficTravelTimeInSeconds"] / b["noTrafficTravelTimeInSeconds"], 4)
    return out


def cmd_run_fit(provider, dry, test):
    """D23 krok 2: trasy analizy × 3 okna -> kontrole geometrii -> dopasowanie f_g (w pamięci) -> na dysk tylko agregaty."""
    sys.path.insert(0, str(Path(__file__).parent))
    import traffic_metrics as tm
    recs = fetch(provider, "fit", dry, test)
    if dry:
        return
    R, Sg, Mt, kontrole, _ = tm.compare(provider, recs)
    ok = R[(R.d_start_m <= 50) & (R.d_end_m <= 50)]
    kontr = {k: v for k, v in kontrole.items() if k not in ("pary_trasa_ponizej_70pct",)}
    kontr["trasy_wyłączone_ponad_50m"] = sorted(set(R.id) - set(ok.id))
    print("kontrole:", json.dumps(kontr, ensure_ascii=False, default=str))
    if test:
        print("TEST: http", [r["http"] for r in recs], "obserwacji", len(ok))
        return
    T, s = tm.fit_factors(ok[["id", "okno", "hist_s"]])
    out = tm.OUT_D23
    T.round(4).to_csv(out / f"fit_f_g_{provider}.csv", index=False, lineterminator="\n")
    Mt[Mt.zestaw == "analiza"].round(4).to_csv(out / f"metrics_r6_analiza_{provider}.csv", index=False, lineterminator="\n")
    meta = dict(dostawca=provider, wyslane_utc=[min(r["utc"] for r in recs), max(r["utc"] for r in recs)], requesty=len(recs),
                http=pd.Series([r["http"] for r in recs]).value_counts().to_dict(), kontrole=kontr, dopasowanie=s)
    json.dump(meta, open(out / f"fit_{provider}.json", "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False, default=float)
    plt = tm.plt
    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = np.arange(len(T))
    ax.errorbar(x, T.f_dopasowane, yerr=[T.f_dopasowane - T.p05, T.p95 - T.f_dopasowane], fmt="o", color="#4fc3f7", capsize=4,
                label="f_g dopasowane, przedział 90% (bootstrap)")
    ax.scatter(x, T.f_final, marker="x", color="#ffb74d", zorder=3, label="f_final (nieidentyfikowalne → 0,8)")
    ax.axhline(tm.F_D13, color="w", ls="--", lw=0.8, label="D13: 0,8")
    names = {"A": "A autostrada", "B": "B DK/DW poza", "C": "C tert./uncl. poza", "D": "D osiedlowe poza", "E": "E główne miasto", "F": "F lokalne miasto"}
    ax.set_xticks(x, [f"{names[g]}\n(n {n}, {k:.0f} km)" for g, n, k in zip(T.grupa, T.trasy_z_przewaga, T.km_w_trasach)], fontsize=7)
    ax.set_ylabel("f_g = freespeed / limit"); ax.set_ylim(0.45, 1.15); ax.legend(fontsize=7)
    ax.set_title(f"D23: współczynnik prędkości per grupa, dopasowany do {provider} historic (zestaw analizy, 3 okna)", fontsize=9)
    fig.tight_layout(); fig.savefig(out / f"fit_f_g_{provider}.png", dpi=140)
    print(T.round(3).to_string())
    print(json.dumps(s, indent=1, default=float))


def cmd_run(provider, dry, test=False, fit=False):
    """Cały przebieg w jednym procesie: requesty -> metryki -> niezależna kontrola -> agregaty na dysk; odpowiedzi znikają."""
    if fit:
        return cmd_run_fit(provider, dry, test)
    import subprocess
    sys.path.insert(0, str(Path(__file__).parent))
    import traffic_metrics as tm
    batches = {b: fetch(provider, b, dry, test) for b in ("probe", "main", "flow")}
    if dry:
        return
    if test:
        R, Sg, Mt, kontrole, indep_in = tm.compare(provider, batches["main"] + batches["flow"])
        print("TEST: http", [r["http"] for v in batches.values() for r in v], "probe", json.dumps(probe_summary(batches["probe"]), default=str))
        print("TEST: trasy", len(R), "segmenty", len(Sg), "metryki", Mt.shape, "kontrole", json.dumps({k: v for k, v in kontrole.items() if k != "problemy"}, default=str))
        print("TEST: problemy", kontrole["problemy"])
        return
    t_start = min(r["utc"] for v in batches.values() for r in v)
    t_end = max(r["utc"] for v in batches.values() for r in v)
    pr = probe_summary(batches["probe"]) if provider == "tomtom" else {}
    R, Sg, Mt, kontrole, indep_in = tm.compare(provider, batches["main"] + batches["flow"])
    # niezależna kontrola mediany i MAPE: osobny skrypt (nie importuje naszych modułów), dane przez stdin, bez zapisu na dysk
    chk = subprocess.run([sys.executable, "-I", str(OUT / "check_niezalezny.py")], input=json.dumps(indep_in),
                         capture_output=True, text=True, check=True)
    indep = json.loads(chk.stdout)
    zgodne = all(abs(Mt.set_index(["porownanie", "zestaw", "grupa", "okno"]).loc[tuple(k.split("|")), c] - v) < 1e-9
                 for k, d in indep.items() for c, v in d.items())
    n_req = {b: len(v) for b, v in batches.items()}
    meta = dict(dostawca=provider, wyslane_utc=[t_start, t_end], requesty=n_req, requesty_razem=sum(n_req.values()),
                requesty_dry_run=len(requests_for(provider, "probe")) + len(requests_for(provider, "main")) + len(requests_for(provider, "flow")),
                http=pd.Series([r["http"] for v in batches.values() for r in v]).value_counts().to_dict(),
                cache_control=sorted({str(r["cache_control"]) for v in batches.values() for r in v}),
                probe=pr, kontrole=kontrole, kontrola_niezalezna=indep, kontrola_niezalezna_zgodna=zgodne)
    json.dump(meta, open(OUT / f"przebieg_{provider}.json", "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False, default=str)
    Mt.round(4).to_csv(OUT / f"metrics_{provider}.csv", index=False, lineterminator="\n")
    tm.plots(provider, Mt)
    tm.plot_errors(provider, Mt, OUT / f"g5_czasy_{provider}_bledy.png")
    # mapa z wartościami dostawcy per obiekt: poza repo (output/ jest w .gitignore), D22 wariant A
    Path("output/g5_czasy_tomtom").mkdir(parents=True, exist_ok=True)
    tm.mapa(provider, R, Sg, Path("output/g5_czasy_tomtom") / f"mapa_{provider}.png")
    tm.scatter_speeds(provider, R, Sg, Path("output/g5_czasy_tomtom") / f"rozrzut_predkosci_{provider}.png")
    print(json.dumps(meta, indent=1, ensure_ascii=False, default=str))
    print(Mt.round(3).to_string())


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "sample":
        cmd_sample()
    elif a[0] == "sample_d23":
        cmd_sample_d23((a[1], int(a[2]), int(a[3])) if len(a) > 1 else None)
    elif a[0] == "run":
        cmd_run(a[1], "--dry-run" in a, "--test" in a, "--fit" in a)
