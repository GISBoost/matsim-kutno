"""Opcja (b) z lancuchy.md: czy ruch z zachodu omija Toruńską (K1) i ile ruchu mogłoby tam trafić przy innym wyborze trasy.

Artefakty GHA nie mają eventów, więc trasy nóg car z output_legs odtwarzamy Dijkstrą po czasie swobodnym
(length/freespeed + 1 s na link, jak w QSim), bez zakazów skrętu (D26, efekt poniżej rozrzutu seedów).
Kontrola przybliżenia: natężenia K1–K5 z tras vs natężenia z eventów (analiza/wios2013.json tego samego runu).
Dla każdej nogi liczymy też czas trasy wymuszonej przez K1 (dowolny kierunek): dodatek = t(o→K1→d) − t(o→d).

Wejście: output/r94c_gha/r94c-r93o-<run>/ (R9.4, runy s4711, p1, p2 = trzy seedy planów).
Użycie: uv run python -W ignore reports/etap3/g_pomiary_miejskie/k1_zachod.py
Wyjście: k1_zachod.json, k1_zachod.png, k1_zachod_mapa.png (obok skryptu)."""
import collections
import json
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
import zstandard
from lxml import etree
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra

matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use("dark_background")  # preferencja użytkownika

G, H = Path("output/r94c_gha"), Path(__file__).parent
RUNS, SAMPLE = ("s4711", "p1", "p2"), 0.25
z = lambda p: zstandard.ZstdDecompressor().stream_reader(open(p, "rb"))
K = pd.read_csv("scenarios/kutno/validation/wios2013_linki.csv")
K1 = K[K.pkt == "K1"].link.tolist()
BZ = pd.read_csv("scenarios/kutno/demand/border_zones.csv")
ZONE = BZ.set_index("link").road.to_dict()  # link wjazdu/wyjazdu -> nazwa strefy, np. "92 zach"
ZACH = {r for r in BZ.road if "zach" in r}  # strefy zachodnie: 92 zach, 91 płn-zach, 91 płd-zach, 60 płd-zach
KLASA = {"r": "mieszkańcy (praca)", "e": "mieszkańcy (zakupy)", "c": "przyjeżdżający", "o": "wyjeżdżający",
         "t": "tło lekkie", "h": "ciężkie"}

# --- sieć (taka sama we wszystkich runach) -------------------------------------------------------------------------
nodes, L = {}, []
for _, el in etree.iterparse(z(G / f"r94c-r93o-{RUNS[0]}" / "output_network.xml.zst"), tag=("node", "link")):
    if el.tag == "node":
        nodes[el.get("id")] = (float(el.get("x")), float(el.get("y")))
    elif "car" in el.get("modes"):
        a = {x.get("name"): x.text for x in el.iter("attribute")}
        L.append((el.get("id"), el.get("from"), el.get("to"), float(el.get("length")), float(el.get("freespeed")),
                  a.get("type"), a.get("speed_group")))
    el.clear()
L = pd.DataFrame(L, columns=["id", "fr", "to", "len", "fs", "type", "grp"]).set_index("id")
nid = {n: i for i, n in enumerate(nodes)}
L["a"], L["b"] = L.fr.map(nid), L.to.map(nid)
L["t"] = L.len / L.fs + 1.0  # QSim: czas przejazdu linku + 1 s
best = L.reset_index().sort_values("t").drop_duplicates(["a", "b"])  # równoległe linki: najszybszy
M = csr_matrix((best.t, (best.a, best.b)), shape=(len(nid),) * 2)
EDGE = dict(zip(zip(best.a, best.b), best.id))
XY = np.array(list(nodes.values()))


def legs(run):
    l = pd.read_csv(G / f"r94c-r93o-{run}" / "output_legs.csv.zst", sep=";",
                    usecols=["person", "mode", "start_link", "end_link"])
    l = l[l["mode"] == "car"].reset_index(drop=True)
    l["o"], l["d"] = L.b.reindex(l.start_link).to_numpy(), L.a.reindex(l.end_link).to_numpy()
    l["kl"] = l.person.str[0]
    l["z_od"], l["z_do"] = l.start_link.map(ZONE), l.end_link.map(ZONE)
    return l


# czasy z K1 do wszystkich węzłów i do K1 ze wszystkich węzłów (oba kierunki K1)
fromK1 = {k: dijkstra(M, indices=L.b[k]) + 0 for k in K1}
toK1 = {k: dijkstra(M.T.tocsr(), indices=L.a[k]) for k in K1}

res, flows = {}, {}
for run in RUNS:
    l = legs(run)
    vol = collections.Counter()
    t0, tk = np.full(len(l), np.nan), np.full(len(l), np.nan)
    via = np.zeros(len(l), bool)
    for o, g in l.groupby("o"):
        dist, pred = dijkstra(M, indices=int(o), return_predecessors=True)
        for i, r in g.iterrows():
            d = int(r.d)
            t0[i] = dist[d] + L.t[r.end_link]
            tk[i] = min(toK1[k][int(o)] + L.t[k] + fromK1[k][d] for k in K1) + L.t[r.end_link]
            path, n = [r.end_link] if r.end_link != r.start_link else [], d
            while n != o and n >= 0:
                p = pred[n]; path.append(EDGE[(p, n)]); n = p
            for x in path:
                vol[x] += 1
            via[i] = any(k in path for k in K1)
    l["t0"], l["dod"], l["via"] = t0, tk - t0, via
    l.loc[l.via, "dod"] = 0.0  # noga już jedzie przez K1 (także koniec na K1, gdzie wymuszenie liczyłoby K1 dwa razy)
    # kontrola: K1–K5 z tras vs z eventów (pojazdy osobowe + ciężkie, pce bez znaczenia: liczymy pojazdy)
    ev = pd.DataFrame(json.load(open(G / f"r94c-r93o-{run}" / "analiza" / "wios2013.json", encoding="utf-8"))["punkty"])
    kon = {p: {"trasy": round(sum(vol[x] for x in K[K.pkt == p].link) / SAMPLE), "eventy": int(m)}
           for p, m in zip(ev.pkt, ev.model_razem)}
    k1 = l[l.via]
    zach = l[l.z_od.isin(ZACH) | l.z_do.isin(ZACH)]
    zach_miasto = zach[zach.z_od.isna() | zach.z_do.isna()]  # jeden koniec w obszarze (nie tranzyt strefa–strefa)
    prog = [0, 15, 30, 60, 120, 180, 300, 600]
    res[run] = {
        "kontrola_K": kon,
        "K1_klasy_poj_doba": (k1.kl.map(KLASA).value_counts() / SAMPLE).round().astype(int).to_dict(),
        "K1_strefy_poj_doba": (pd.concat([k1.z_od, k1.z_do]).dropna().value_counts() / SAMPLE).round().astype(int).to_dict(),
        "zachod_miasto_nogi_poj_doba": round(len(zach_miasto) / SAMPLE),
        "zachod_miasto_przez_K1_proc": round(100 * zach_miasto.via.mean(), 1),
        "zachod_tranzyt_nogi_poj_doba": round((len(zach) - len(zach_miasto)) / SAMPLE),
        # ile pojazdów/dobę mogłoby dojść na K1, gdyby wszystkie nogi z dodatkiem ≤ X s jechały przez K1
        "potencjal_K1_poj_doba": {f"<= {p} s": round(float((l.dod <= p).sum()) / SAMPLE) for p in prog},
        "potencjal_K1_zachod_miasto": {f"<= {p} s": round(float((zach_miasto.dod <= p).sum()) / SAMPLE) for p in prog},
        "dodatek_mediana_s": {k: round(float(g.dod.median()), 0) for k, g in
                              {"wszystkie": l, "zachod_miasto": zach_miasto, "zachod_tranzyt": zach[~zach.index.isin(zach_miasto.index)]}.items()},
    }
    flows[run] = (vol, l)
    print(run, json.dumps(res[run], ensure_ascii=False))

# --- obwodnica vs Toruńska: typy i prędkości na trasie K1 i na trasach zachodnich -------------------------------------
vol, l = flows[RUNS[0]]
Kxy = K[K.pkt == "K1"].iloc[0][["x", "y"]].astype(float).to_numpy()
res["K1_link"] = L.loc[K1, ["len", "fs", "type", "grp"]].assign(fs_kmh=lambda d: (d.fs * 3.6).round(1)).drop(columns="fs").to_dict("index")
res["cel_2025"] = {"f_suma": 12910, "korytarz": 9644}
json.dump(res, open(H / "k1_zachod.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# --- wykres 1: potencjał K1 vs dodatek czasu --------------------------------------------------------------------------
fig, ax = plt.subplots(1, 2, figsize=(15, 5.5))
prog = np.arange(0, 601, 15)
for run, c in zip(RUNS, ("#4fc3f7", "#81c784", "#ffb74d")):
    l = flows[run][1]
    zm = l[(l.z_od.isin(ZACH) | l.z_do.isin(ZACH)) & (l.z_od.isna() | l.z_do.isna())]
    ax[0].plot(prog, [(l.dod <= p).sum() / SAMPLE for p in prog], color=c, label=f"wszystkie nogi, run {run}")
    ax[0].plot(prog, [(zm.dod <= p).sum() / SAMPLE for p in prog], color=c, ls="--", label=f"z/do zachodu, jeden koniec w obszarze, {run}")
for v, ls, lab in ((12910, "-", "cel 2025 f_suma (12 910)"), (9644, ":", "cel 2025 korytarz 91123 (9 644)")):
    ax[0].axhline(v, color="w", ls=ls, lw=1, label=lab)
ax[0].set_xlabel("dodatek czasu przy trasie przez K1 względem najszybszej [s]")
ax[0].set_ylabel("nogi car, które mogłyby jechać przez K1 [poj./dobę]")
ax[0].set_title("potencjał K1: ile ruchu ma trasę przez Toruńską niewiele dłuższą"); ax[0].legend(fontsize=7)
kl = pd.DataFrame({r: res[r]["K1_klasy_poj_doba"] for r in RUNS}).fillna(0)
kl.plot.barh(ax=ax[1], color=["#4fc3f7", "#81c784", "#ffb74d"])
ax[1].set_xlabel("pojazdy/dobę przez K1 (trasy odtworzone)"); ax[1].set_title("kto jedzie Toruńską w modelu (R9.4)")
fig.suptitle("K1 Toruńska: skład ruchu i potencjał zmiany trasy (R9.4, trasy po czasie swobodnym)")
fig.text(.01, .01, "Jak czytać. Lewy: dla każdej nogi car policzono, o ile sekund dłuższa byłaby trasa wymuszona przez K1 (oś X); oś Y = ile nóg "
         "(poj./dobę, ×4 z próbki 25%) ma dodatek ≤ X, czyli ile ruchu mogłoby jechać Toruńską, gdyby kierowcy akceptowali taki objazd. "
         "Linia ciągła = wszystkie nogi, przerywana = nogi z/do stref zachodnich z jednym końcem w obszarze. Białe linie = cel 2025 z pomiaru WIOŚ 2013.\n"
         "Prawy: kto przejeżdża przez K1 w modelu, wg klasy agenta, 3 seedy planów. Źródło: artefakty GHA run 41186041250 (r93o = R9.4), "
         "trasy odtworzone Dijkstrą (kontrola K1: 2 596 z tras vs 2 600 z eventów). Skrypt k1_zachod.py, opis w k1_zachod.md.",
         fontsize=8, va="bottom", wrap=True)
fig.tight_layout(rect=(0, .1, 1, 1)); fig.savefig(H / "k1_zachod.png", dpi=130)

# --- wykres 2: mapa ------------------------------------------------------------------------------------------------
fig, ax = plt.subplots(1, 2, figsize=(16, 8))
box = (Kxy[0] - 5000, Kxy[0] + 6000, Kxy[1] - 4500, Kxy[1] + 4000)
inb = lambda xy: (box[0] < xy[0] < box[1]) & (box[2] < xy[1] < box[3])
segs = [(XY[r.a], XY[r.b]) for r in L.itertuples() if inb(XY[r.a])]
l = flows[RUNS[0]][1]
zm = l[(l.z_od.isin(ZACH) | l.z_do.isin(ZACH))]
for a_, (title, sub) in zip(ax, (("wszystkie nogi z/do stref zachodnich (92 zach, 91 płn-/płd-zach, 60 płd-zach)", zm),
                                 ("nogi przez K1 (select link)", l[l.via]))):
    v = collections.Counter()
    for o, g in sub.groupby("o"):
        _, pred = dijkstra(M, indices=int(o), return_predecessors=True)
        for r in g.itertuples():
            n = int(r.d)
            while n != o and n >= 0:
                p = pred[n]; v[EDGE[(p, n)]] += 1; n = p
    for s in segs:
        a_.plot(*zip(*s), color="#444", lw=.4)
    mx = max(v.values())
    for x, c in v.items():
        a, b = XY[L.a[x]], XY[L.b[x]]
        if inb(a) and c / SAMPLE >= 20:
            a_.plot([a[0], b[0]], [a[1], b[1]], color="#ffb74d", lw=.5 + 6 * c / mx, alpha=.8)
    for k in K1:
        a_.plot(*Kxy, "o", color="#e57373", ms=10, mfc="none", mew=2)
    a_.annotate("K1 Toruńska", Kxy, xytext=(10, 10), textcoords="offset points", color="#e57373")
    a_.set_xlim(box[:2]); a_.set_ylim(box[2:]); a_.set_aspect("equal"); a_.set_title(title, fontsize=10)
    a_.set_xticks([]); a_.set_yticks([])
fig.suptitle(f"R9.4 run {RUNS[0]}: trasy (grubość ~ poj./dobę, pokazane ≥ 20 poj./dobę), EPSG:2180, okno 11 × 8,5 km")
fig.text(.01, .01, "Jak czytać. Szare = sieć MATSim. Pomarańczowe = linki, którymi jadą wybrane nogi car (trasy po czasie swobodnym), grubość proporcjonalna "
         "do liczby pojazdów/dobę. Czerwone kółko = punkt pomiaru K1 (ul. Toruńska, WIOŚ 2013). Lewy: nogi z/do stref zachodnich "
         "(wjazdy 92 zach, 91 płn-zach, 91 płd-zach, 60 płd-zach) — jadą obwodnicą południową, nie Toruńską. Prawy: wszystkie nogi przez K1 "
         "(select link) — Toruńska obsługuje głównie płn.-zach. część miasta i wsie za nią. Opis w k1_zachod.md.",
         fontsize=8, va="bottom", wrap=True)
fig.tight_layout(rect=(0, .06, 1, 1)); fig.savefig(H / "k1_zachod_mapa.png", dpi=110)
