"""D19/K2-2: macierz O-D ruchu tła (pojazdy lekkie, doba, 100%) estymowana z liczników GPR 2025.

Użycie: uv run python -W ignore pipeline/background_od.py <tau_min> <out_tag> <model_output_dir> [<output_dir> ...]   (seedy runu bez tła, np. R1)
Strefy: wjazdy (początek) i wyjazdy (koniec) na granicy sieci (`scenarios/kutno/demand/border_links.csv`, z plans.py) oraz
gminy powiatu kutnowskiego: K punktów na gminę = budynki losowane wagą powierzchni (jak agenci w plans.py), przypięte do
najbliższego linku poza motorway/trunk (snap_exclude_types). Incydencja ułamkowa: udział z K par punktów (k-ty punkt
początku z k-tym punktem końca), których trasa przechodzi przez licznik. Wersja z jednym węzłem na gminę (do R2) nie
zgadzała się z trasami agentów (reports/g5_kalibracja/g5_r2.md). Link startowy nie jest liczony (MATSim zaczyna na jego końcu).
Pary wewnątrz gminy dozwolone dla gmin powiatu poza gm. miejską Kutno: bez nich liczniki ruchu lokalnego (Żychlin, Krośniewice)
wypełniały się podróżami przez całe miasto (Krośniewice -> Żychlin przez Objazdową).
Liczniki (cel): GPR SDRDR (DW: SDRR) × udział lekkich × kierunek (jak g5_baseline.py) MINUS natężenie modelu bez tła.
Do dopasowania odcinki poza miastem i Sklęczkowska 91869; 91124 i 91866 zostają do walidacji poza próbą (D19/K4, W2).
Metoda: trasy swobodne (length/freespeed), pary O-D, których trasa przechodzi przez co najmniej jeden licznik dopasowania,
macierz a priori grawitacyjna T0_ij = w_o · w_d · exp(−t_ij / tau), potem mnożnikowa korekta:
T_ij *= exp(Σ_l f_ijl · log(cel_l / przypisane_l) / max(1, Σ_l f_ijl)), przypisane_l = Σ T_ij f_ijl. Średnia ważona (bez kroku ∝ f)
dawała parom z f ≈ 0,05 mnożnik 20× i przeładowanie dróg bez liczników (Objazdowa 506%).
w strefy-gminy = powierzchnia obrysów budynków gminy / średnia; w wjazdu/wyjazdu = 1.
ZAŁOŻENIE: postać a priori i tau (brak danych o O-D tła); tau podawane jako wariant (15/30/60 min), nie dobierane pod miasto.
Płaska macierz (tau = inf) dała 2× za dużo na odcinkach miejskich. Pary bez licznika na trasie = 0 (tło tylko tam, gdzie zmierzone).
D20: opcja cls= wybiera klasę pojazdów celu: light (domyślnie, D19: osobowe + mikrobusy + motocykle), lcv (light + dostawcze ≤ 3,5 t),
heavy (ciężarowe > 3,5 t bez i z przyczepami, autobusy, ciągniki; model bez tła = 0, bo dojazdy to osobowe; trasy z prędkością
ograniczoną do 80 km/h, Prawo o ruchu drogowym art. 20 ust. 3 pkt 2). Udział klasy ze struktury rodzajowej GPR (SDR).
E1 (po R4): routes=<output_dir runu z tłem> init=<macierz O-D tego runu>: incydencja z tras wybranych planów w ostatniej
iteracji (agenci t…/h… danej klasy, id = <prefiks><o>_<d>_<k>; udział agentów pary przejeżdżających przez licznik, bez linku
startowego), dla par bez agentów w runie incydencja z tras swobodnych. Start z macierzy init (tylko jej pary), model bez tła
dla lcv = pracujący (r/c/o) z eventów tego runu, czyli w stanie z kongestią.
bound=F (tylko z init): każda para w przedziale [T_init / F, T_init · F]. Bez tego para będąca jedynym nośnikiem licznika
rosła bez ograniczeń (Kutno -> Krośniewice-miasto 1 415 -> 13 257 podróży/dobę, Objazdowa 211%; reports/g5_kalibracja/g5_r5.md).
Wyjście: scenarios/kutno/demand/background_od_<tag>.csv (o_kind, o, d_kind, d, tt_min, trips_day), reports/g5_kalibracja/k2_od_<tag>.{json,png}.
"""
import gzip
import io
import json
import re
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib
import networkx as nx
import numpy as np
import pandas as pd
import tomllib
import zstandard
from lxml import etree
from shapely import STRtree
from shapely.geometry import LineString, Point

matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use("dark_background")  # ciemny motyw (prośba użytkownika)

CITY = [91124, 91866]  # D19/K4, W2: walidacja poza próbą (Sklęczkowska 91869 w dopasowaniu)
TAU, TAG = float(sys.argv[1]), sys.argv[2]
BORDER_W = TAG.endswith("_cap")  # wariant: waga wjazdu/wyjazdu = capacity linku / średnia (A1 >> DW)
runs = [Path(a) for a in sys.argv[3:] if "=" not in a]
OPT = dict(a.split("=", 1) for a in sys.argv[3:] if "=" in a)  # iters=N (wczesne zatrzymanie), drop=nr,nr (liczniki pominięte)
ITERS = int(OPT.get("iters", 300))
DROP = [int(x) for x in OPT["drop"].split(",")] if OPT.get("drop") else []
CLS = OPT.get("cls", "light")
CLS_COLS = {"light": ["lekkie_osob"], "lcv": ["lekkie_osob", "lekkie_ciez"],
            "heavy": ["ciez_bez_przycz", "ciez_z_przycz", "autobusy", "ciagniki"]}[CLS]
VMAX = 80 / 3.6 if CLS == "heavy" else np.inf  # D20: prędkość maksymalna ciężarowych
ROUTES = Path(OPT["routes"]) if OPT.get("routes") else None
INIT = pd.read_csv(OPT["init"], dtype={"o": str, "d": str}) if OPT.get("init") else None
K = 20  # punkty na gminę
P = tomllib.loads(Path("config/kutno.toml").read_text(encoding="utf-8"))
POWIAT = P["area"]["teryt_powiat"]

# --- sieć ---------------------------------------------------------------------------------------------
nodes, G, ltype, lnodes, lcap = {}, nx.DiGraph(), {}, {}, {}
with gzip.open("scenarios/kutno/network.xml.gz", "rb") as f:
    for _, el in etree.iterparse(f, tag=("node", "link")):
        if el.tag == "node":
            nodes[el.get("id")] = (float(el.get("x")), float(el.get("y")))
        else:
            a, b, lid = el.get("from"), el.get("to"), el.get("id")
            t = float(el.get("length")) / min(float(el.get("freespeed")), VMAX)
            ltype[lid] = {x.get("name"): x.text for x in el.iter("attribute")}.get("type")
            lnodes[lid] = (a, b)
            lcap[lid] = float(el.get("capacity"))
            if not G.has_edge(a, b) or G[a][b]["t"] > t:
                G.add_edge(a, b, t=t, link=lid)
        el.clear()

# --- strefy: punkty dostępu (węzeł startu, link końcowy) -------------------------------------------------------
rng = np.random.default_rng(P["plans"]["seed"])
snap_ids = [l for l in lnodes if ltype[l] not in P["plans"]["snap_exclude_types"]]
tree = STRtree([LineString([nodes[lnodes[l][0]], nodes[lnodes[l][1]]]) for l in snap_ids])
bl = pd.read_csv("scenarios/kutno/demand/border_links.csv")
zones = []  # kind, id, x, y, w, starts [(node)], ends [(node, last_link)]
for r in bl.itertuples():
    a, b = lnodes[r.link]
    if r.kind == "entry":   # start na końcu linku wjazdowego
        zones.append(("entry", r.link, r.x, r.y, np.nan, [b] * K, None))
    else:                   # koniec: wjazd na link wyjazdowy
        zones.append(("exit", r.link, r.x, r.y, np.nan, None, [(a, r.link)] * K))
rej = gpd.read_file("data/raw/brec/rej_pl/SU_BREC_2021_REJ.shp", columns=["GMINA"])
gm = rej[rej.GMINA.str.startswith(POWIAT)].dissolve(by="GMINA").geometry
bld = gpd.read_file("scenarios/kutno/osm/features.gpkg", layer="buildings")
bld["pt"], bld["a"] = bld.geometry.representative_point(), bld.geometry.area
for code, geom in gm.items():
    inb = bld[bld.pt.within(geom)]
    pick = inb.iloc[rng.choice(len(inb), size=K, p=(inb.a / inb.a.sum()).to_numpy())]
    _, li = tree.query_nearest(list(pick.pt), all_matches=False)
    ls = [snap_ids[i] for i in li]
    zones.append(("gmina", code, float(np.average(inb.pt.x, weights=inb.a)), float(np.average(inb.pt.y, weights=inb.a)),
                  inb.a.sum(), [lnodes[l][1] for l in ls], [(lnodes[l][0], l) for l in ls]))
Z = pd.DataFrame(zones, columns=["kind", "id", "x", "y", "w", "starts", "ends"])
Z["w"] = (Z.w / Z.w.mean()).fillna(1.0)
if BORDER_W:
    b = Z.kind != "gmina"
    cap = Z[b].id.map(lcap)  # id strefy granicznej = link wjazdu/wyjazdu
    Z.loc[b, "w"] = cap / cap.mean()
O, D = Z[Z.kind != "exit"].reset_index(drop=True), Z[Z.kind != "entry"].reset_index(drop=True)

# --- liczniki --------------------------------------------------------------------------------------------
g = pd.read_csv("reports/g5_walidacja/gpr_linki.csv", dtype={"link": str})
g["gpr"] = g[[c + "_dr" for c in CLS_COLS]].sum(axis=1) * g.udzial_kier  # audyt K2: struktura SDRDR (DW: SDRR, ZAŁOŻENIE)
vol = []
for d in runs:
    c = etree.parse(str(d / "output_config.xml"))
    s = float(c.find(".//module[@name='qsim']/param[@name='flowCapacityFactor']").get("value"))
    l = pd.read_csv(d / "output_links.csv.zst", sep=";", dtype={"link": str}).set_index("link")
    vol.append(g.link.map(l.vol_car).fillna(0) / s)
g["model"] = pd.concat(vol, axis=1).mean(axis=1) if CLS != "heavy" else 0.0
if ROUTES is not None and CLS != "heavy":  # E1: pracujący z eventów runu z tłem (vol_car zawiera tam też tło)
    s = float(etree.parse(str(ROUTES / "output_config.xml")).find(".//module[@name='qsim']/param[@name='flowCapacityFactor']").get("value"))
    want, kc = set(g.link), {}
    pat = re.compile(r'type="entered link" link="([^"]+)" vehicle="([rco])')
    with zstandard.ZstdDecompressor().stream_reader(open(ROUTES / "output_events.xml.zst", "rb")) as f:
        for line in io.TextIOWrapper(f, encoding="utf-8"):
            m = pat.search(line)
            if m and m[1] in want:
                kc[m[1]] = kc.get(m[1], 0) + 1
    g["model"] = g.link.map(lambda l: kc.get(l, 0) / s)
g["target"] = (g.gpr - g.model).clip(lower=0)
g["fit"] = ~g.nr.isin(CITY + DROP)
cnt = {r.link: i for i, r in g.iterrows()}

# --- trasy i incydencja ułamkowa ------------------------------------------------------------------------
pairs = []  # (oi, di, tt_min, {indeks licznika: udział})
for oi, o in O.iterrows():
    sp = {n: nx.single_source_dijkstra(G, n, weight="t") for n in set(o.starts)}
    for di, d in D.iterrows():
        same = o.kind == "gmina" and d.kind == "gmina" and o.id == d.id
        if (same and o.id == P["area"]["teryt_gmina"]) or (not same and np.hypot(o.x - d.x, o.y - d.y) < 1500):
            continue  # ruch wewnątrz Kutna to inne cele mieszkańców (poza tłem); zawracanie na tej samej granicy
        hits, tts, ok = {}, [], 0
        for k in range(K):
            dist, path = sp[o.starts[k]]
            en, last = d.ends[(k + same) % K]  # w tej samej gminie: inny budynek końca niż początku
            if en not in path:
                continue
            ok += 1
            tts.append(dist[en])
            pth = path[en]
            for l in [G[a][b]["link"] for a, b in zip(pth, pth[1:])] + [last]:
                if l in cnt:
                    hits[cnt[l]] = hits.get(cnt[l], 0) + 1
        if ok:
            pairs.append((oi, di, float(np.mean(tts)) / 60, {h: c / ok for h, c in hits.items()}))
route_pairs = 0
if ROUTES is not None:  # E1: incydencja z tras runu
    pre = "h" if CLS == "heavy" else "t"
    agents, hits_r = {}, {}
    plans = etree.iterparse(zstandard.ZstdDecompressor().stream_reader(open(ROUTES / "output_plans.xml.zst", "rb")), tag="person")
    for _, el in plans:
        pid = el.get("id")
        if pid.startswith(pre):
            o, d = pid[1:].split("_")[:2]
            pl = [x for x in el.findall("plan") if x.get("selected") == "yes"][0]
            r = pl.find("leg[@mode='car']/route")
            links = (r.text or "").split()[1:]
            agents[(o, d)] = agents.get((o, d), 0) + 1
            hc = hits_r.setdefault((o, d), {})
            for h in {cnt[l] for l in links if l in cnt}:
                hc[h] = hc.get(h, 0) + 1
        el.clear()
    new = []
    for p in pairs:
        key = (str(O.id[p[0]]), str(D.id[p[1]]))
        if key in agents:
            route_pairs += 1
            p = (p[0], p[1], p[2], {h: c / agents[key] for h, c in hits_r[key].items()})
        new.append(p)
    pairs = new
F = [p for p in pairs if any(g.fit[h] for h in p[3])]
T = np.array([O.w[p[0]] * D.w[p[1]] * np.exp(-p[2] / TAU) for p in F])
if INIT is not None:  # E1: start z macierzy runu, tylko jej pary
    t0 = {(r.o, r.d): r.trips_day for r in INIT.itertuples()}
    T = np.array([t0.get((str(O.id[p[0]]), str(D.id[p[1]])), 0.0) for p in F])
T_init, BOUND = T.copy(), float(OPT.get("bound", "inf"))
fit = g.fit.to_numpy()
idx = [np.array(list(p[3].keys()), dtype=int) for p in F]
frac = [np.array(list(p[3].values())) for p in F]
for it in range(ITERS):
    assigned = np.zeros(len(g))
    for t, i, f in zip(T, idx, frac):
        assigned[i] += t * f
    ratio = np.clip(np.where(assigned > 0, np.maximum(g.target, 1) / np.maximum(assigned, 1e-9), 1), 0.05, 20)
    for k, (i, f) in enumerate(zip(idx, frac)):
        m = fit[i]
        T[k] *= np.exp(np.sum(f[m] * np.log(ratio[i[m]])) / max(1.0, np.sum(f[m])))  # krok ∝ udział: para rzadko przez licznik prawie się nie zmienia
    if INIT is not None and np.isfinite(BOUND):
        T = np.clip(T, T_init / BOUND, T_init * BOUND)
assigned = np.zeros(len(g))
for t, i, f in zip(T, idx, frac):
    assigned[i] += t * f
g["background"] = assigned
g["model_plus_bg"] = g.model + g.background

od = pd.DataFrame([dict(o_kind=O.kind[p[0]], o=O.id[p[0]], d_kind=D.kind[p[1]], d=D.id[p[1]], tt_min=round(p[2], 1),
                        trips_day=round(t, 2)) for t, p in zip(T, F)])
od = od[od.trips_day >= 0.5].sort_values("trips_day", ascending=False)
od.to_csv(f"scenarios/kutno/demand/background_od_{TAG}.csv", index=False, lineterminator="\n")

sec = g.groupby("nr", sort=False).agg(droga=("droga", "first"), fit=("fit", "first"), gpr=("gpr", "sum"), model=("model", "sum"),
                                      background=("background", "sum")).reset_index()
sec["model_plus_bg"] = sec.model + sec.background
sec["ratio_before"], sec["ratio_after"] = sec.model / sec.gpr, sec.model_plus_bg / sec.gpr
geh = lambda m, c: np.sqrt(2 * (m - c) ** 2 / (m + c)) / np.sqrt(24)  # GEH godzinowy ze średniej godziny doby (orientacyjnie)
sec["geh_hourly_mean"] = geh(sec.model_plus_bg, sec.gpr)
kz = lambda k: od[(od.o_kind == k) | (od.d_kind == k)].trips_day.sum()
rep = {"runs": [str(d) for d in runs], "cls": CLS, "routes": str(ROUTES), "init": OPT.get("init"), "pairs_with_route_incidence": route_pairs, "bound": OPT.get("bound"), "tau_min": TAU, "iters": ITERS, "dropped_counts": DROP, "zones": Z.kind.value_counts().to_dict(), "od_pairs_with_count": len(F),
       "od_pairs_kept": len(od), "trips_day_100pct": round(float(od.trips_day.sum())),
       "trips_by_type": {"tranzyt_wjazd_wyjazd": round(float(od[(od.o_kind == "entry") & (od.d_kind == "exit")].trips_day.sum())),
                         "granica_gmina": round(float(od[(od.o_kind == "entry") & (od.d_kind == "gmina")].trips_day.sum()
                                                      + od[(od.o_kind == "gmina") & (od.d_kind == "exit")].trips_day.sum())),
                         "gmina_gmina": round(float(od[(od.o_kind == "gmina") & (od.d_kind == "gmina")].trips_day.sum())),
                         "w_tym_wewnatrz_gminy": round(float(od[(od.o_kind == "gmina") & (od.o == od.d)].trips_day.sum()))},
       "fit_links_rmse": round(float(np.sqrt(((g.model_plus_bg - g.gpr)[g.fit] ** 2).mean())), 1),
       "sections": sec.round(3).to_dict(orient="records"),
       "top_od": od.head(15).to_dict(orient="records"),
       "top_od_via_city": {str(nr): sorted([dict(o=O.id[p[0]], d=D.id[p[1]], trips=round(float(t)),
                                                 fit_counts=sorted({int(g.nr[h]) for h in p[3] if g.fit[h]}))
                                            for t, p in zip(T, F) if any(g.nr[h] == nr for h in p[3])],
                                           key=lambda r: -r["trips"])[:8] for nr in CITY}}
json.dump(rep, open(f"reports/g5_kalibracja/k2_od_{TAG}.json", "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False)

fig, axs = plt.subplots(1, 2, figsize=(15, 6.5), gridspec_kw={"width_ratios": [1.3, 1]})
s = sec.sort_values("gpr")
y = np.arange(len(s))
ax = axs[0]
ax.barh(y + 0.27, s.gpr, 0.27, color="#6c757d", label=f"GPR ({CLS}, SDRDR)")
ax.barh(y, s.model, 0.27, color="#2e86ab", label="model bez tła (R1)")
ax.barh(y - 0.27, s.model_plus_bg, 0.27, color="#f18f01", label="model + tło (trasy swobodne)")
ax.set_yticks(y); ax.set_yticklabels([f"{r.droga} {r.nr}{'  [walidacja]' if not r.fit else ''}" for r in s.itertuples()], fontsize=8)
ax.set_xlabel("poj./dobę, oba kierunki"); ax.legend(fontsize=8, loc="lower right")
ax.set_title(f"K2: dopasowanie tła do GPR, tau = {TAU:g} min (miasto poza próbą)", fontsize=10)
ax = axs[1]
for r in od.head(60).itertuples():
    o, d = O[O.id == r.o].iloc[0], D[D.id == r.d].iloc[0]
    ax.plot([o.x, d.x], [o.y, d.y], color="#f18f01", alpha=0.25, lw=0.3 + r.trips_day / od.trips_day.max() * 6)
ax.scatter(Z[Z.kind == "gmina"].x, Z[Z.kind == "gmina"].y, s=20, color="#3ddc97", zorder=5, label="gminy powiatu")
ax.scatter(Z[Z.kind != "gmina"].x, Z[Z.kind != "gmina"].y, s=8, color="#d1495b", zorder=5, label="wjazdy / wyjazdy")
ax.set_aspect("equal"); ax.set_axis_off(); ax.legend(fontsize=8)
ax.set_title(f"60 największych relacji tła ({rep['trips_day_100pct']} podróży/dobę w 100%)", fontsize=10)
fig.tight_layout(); fig.savefig(f"reports/g5_kalibracja/k2_od_{TAG}.png", dpi=120)
print(json.dumps({k: v for k, v in rep.items() if k not in ("sections", "top_od")}, ensure_ascii=False, indent=1))
print(sec[["nr", "droga", "fit", "gpr", "model", "background", "model_plus_bg", "ratio_before", "ratio_after"]].round(2).to_string())
