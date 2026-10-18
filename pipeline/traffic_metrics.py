"""G5/D22: metryki model R6 vs dostawca (TomTom / HERE) dla par, korytarzy i segmentów z traffic_providers.py.

Użycie:
  uv run python pipeline/traffic_metrics.py model            czasy modelu (5 runów R6) -> OUT/model_times.csv, model_legs_check.csv
  compare(...) wołane z traffic_providers.py run (odpowiedzi tylko w pamięci, D22 wariant A); zwraca agregaty i kontrole
  uv run python pipeline/traffic_metrics.py selftest         test na danych syntetycznych (bez sieci)

Czas modelu pary w oknie = przejazd sondy po trasie modelu (linki z experienced_plans; korytarz: trasa swobodna) z czasem
przejazdu linku = średnia z eventów (entered/left link) pojazdów lekkich, które wjechały na link w tej godzinie; bez
przejazdów: czas swobodny floor(L/v)+1 (I1). Sonda startuje na końcu linku startowego (jak noga car w MATSim) i przesuwa
zegar link po linku. Ciężkie: max(czas lekkich, floor(L/min(v, 80 km/h))+1) (D20). Dzięki temu ta sama para ma czas w każdym
z 5 runów, także w runach z innym seedem planów (inne osoby). Kontrola: czas sondy vs trav_time nogi agenta (3 seedy MATSim).
Czasów nie skalujemy przez próbkę. Model = uśredniony dzień roboczy, nie data.
"""
import json
import math
import sys
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
import shapely
import zstandard
from lxml import etree
from pyproj import Transformer

matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use("dark_background")  # ciemny motyw (prośba użytkownika)

OUT = Path("reports/etap2/g5_czasy_tomtom")
META = "scenarios/kutno/plans_g5r6_25pct_"
CACHE = Path("output/g5_czasy_tomtom")  # tt linków per run (duże, poza gitem)
RUNS = [Path(f"output/{r}") for r in ("g5r6_25pct_s4711", "g5r6_25pct_s1", "g5r6_25pct_s2", "g5r6p1_25pct_s4711", "g5r6p2_25pct_s4711")]
WIN_H = {"rano": 7.5, "poludnie": 12.5, "popoludnie": 15.5}  # środek okna, jak departAt w traffic_providers.py
VMAX_HEAVY = 80 / 3.6  # D20
# ORS: prędkości jak w pipeline/g5_gus_czasy.py (wariant ors, VehicleFlagEncoder): tag -> 0,9 × maxspeed, bez tagu -> klasa
ORS_KMH = {"motorway": 100, "motorway_link": 60, "trunk": 85, "trunk_link": 60, "primary": 65, "primary_link": 50,
           "secondary": 60, "secondary_link": 50, "tertiary": 50, "tertiary_link": 40, "unclassified": 30,
           "residential": 30, "living_street": 10, "service": 20, "road": 20, "track": 15}
TO_2180 = Transformer.from_crs(4326, 2180, always_xy=True)
z = lambda p: zstandard.ZstdDecompressor().stream_reader(open(p, "rb"))


def links():
    L = pd.read_csv(RUNS[0] / "output_links.csv.zst", sep=";", dtype={"link": str}).set_index("link")
    L["ff"] = np.floor(L.length / L.freespeed) + 1
    L["ff_h"] = np.floor(L.length / np.minimum(L.freespeed, VMAX_HEAVY)) + 1
    v = np.where(L.speed_source == "tag", 0.9 * L.allowed_speed, L.type.map(ORS_KMH).fillna(30) / 3.6)
    L["ff_ors"] = L.length / np.where(L.speed_source == "boundary_turnaround", L.freespeed, v)
    return L


def link_tt(run):
    """Średni czas przejazdu linku per godzina wjazdu, pojazdy lekkie (bez h…); cache w output/."""
    f = CACHE / f"linktt_{run.name}.csv.gz"
    if f.exists():
        return pd.read_csv(f, dtype={"link": str})
    enter, acc = {}, {}
    for _, el in etree.iterparse(z(run / "output_events.xml.zst"), tag="event"):
        t, v = el.get("type"), el.get("vehicle")
        if t == "entered link" and not v.startswith("h"):
            enter[v] = (el.get("link"), float(el.get("time")))
        elif t == "vehicle leaves traffic":
            enter.pop(v, None)
        elif t == "left link" and v in enter:
            lk, t0 = enter.pop(v)
            k = (lk, int(t0 // 3600))
            s, n = acc.get(k, (0.0, 0))
            acc[k] = (s + float(el.get("time")) - t0, n + 1)
        el.clear()
    d = pd.DataFrame([(lk, h, s / n, n) for (lk, h), (s, n) in acc.items()], columns=["link", "hour", "tt", "n"])
    CACHE.mkdir(parents=True, exist_ok=True)
    d.to_csv(f, index=False)
    return d


def probe(route, t0, tt, ff, heavy_ff=None):
    """Czas przejazdu od końca pierwszego linku do końca ostatniego, zegar przesuwany link po linku."""
    t = t0
    for lk in route[1:]:
        x = tt.get((lk, int(t // 3600)), ff[lk])
        t += max(x, heavy_ff[lk]) if heavy_ff is not None else x
    return t - t0


def cmd_model():
    L = links()
    P = pd.read_csv(OUT / "pairs.csv", dtype={"start_link": str, "end_link": str})
    ff, ffh = L.ff.to_dict(), L.ff_h.to_dict()
    rows = []
    for run in RUNS:
        d = link_tt(run)
        tt = dict(zip(zip(d.link, d.hour), d.tt))
        for _, p in P.iterrows():
            r = p.route.split()
            hv = ffh if p["mode"] == "truck" else None
            for w, h in WIN_H.items():
                rows.append(dict(id=p.id, run=run.name, okno=w, model_s=probe(r, h * 3600, tt, ff, hv)))
    M = pd.DataFrame(rows)
    g = M.groupby(["id", "okno"]).model_s.agg(model_med="median", model_min="min", model_max="max").reset_index()
    fr = []
    for _, p in P.iterrows():
        r = p.route.split()[1:]
        fr.append(dict(id=p.id, ff_model_s=sum((ffh if p["mode"] == "truck" else ff)[x] for x in r),
                       ff_ors_s=(np.maximum(L.ff_ors[r], L.length[r] / VMAX_HEAVY) if p["mode"] == "truck" else L.ff_ors[r]).sum(), km=L.length[r].sum() / 1000))
    g = g.merge(pd.DataFrame(fr), on="id")
    g.round(1).to_csv(OUT / "model_times.csv", index=False, lineterminator="\n")

    # kontrola sondy: nogi agentów z próbki w 3 seedach MATSim (te same osoby), czas sondy przy faktycznym wyjeździe
    chk = []
    for run in RUNS[:3]:
        d = link_tt(run)
        tt = dict(zip(zip(d.link, d.hour), d.tt))
        lg = pd.read_csv(run / "output_legs.csv.zst", sep=";", dtype={"start_link": str, "end_link": str})
        lg = lg[(lg["mode"] == "car") & lg.trip_id.str.endswith("_1") & lg.person.isin(P.person.dropna())]
        for _, l in lg.iterrows():
            p = P[P.person == l.person].iloc[0]
            t0 = pd.to_timedelta(l.dep_time).total_seconds()
            chk.append(dict(id=p.id, run=run.name, dep=l.dep_time, leg_s=pd.to_timedelta(l.trav_time).total_seconds(),
                            probe_s=probe(p.route.split(), t0, tt, ff, ffh if p["mode"] == "truck" else None)))
    C = pd.DataFrame(chk)
    C["ratio"] = C.probe_s / C.leg_s
    C.round(3).to_csv(OUT / "model_legs_check.csv", index=False, lineterminator="\n")
    print(g.groupby("okno")[["model_med", "ff_model_s"]].median())
    print("sonda / noga agenta: mediana %.3f, p5 %.3f, p95 %.3f (n=%d)" % (C.ratio.median(), C.ratio.quantile(.05), C.ratio.quantile(.95), len(C)))


# ---------------------------------------------------------------- dostawcy
def flexpoly(s):
    """Dekoder HERE flexible polyline (lat, lon) - specyfikacja heremaps/flexible-polyline."""
    tbl = {c: i for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")}
    vals, cur, sh = [], 0, 0
    for ch in s:
        v = tbl[ch]
        cur |= (v & 0x1F) << sh
        if v & 0x20:
            sh += 5
        else:
            vals.append(cur)
            cur, sh = 0, 0
    prec = vals[1] & 15
    third = (vals[1] >> 4) & 7
    f, out, la, lo, i = 10 ** prec, [], 0, 0, 2
    dec = lambda u: ~(u >> 1) if u & 1 else u >> 1
    while i < len(vals):
        la += dec(vals[i]); lo += dec(vals[i + 1]); i += 3 if third else 2
        out.append((la / f, lo / f))
    return out


def parse(provider, rec):
    """Rekord jsonl -> dict z czasami [s], długością [m] i geometrią (lista lat, lon). None przy błędzie."""
    b = rec.get("body")
    if rec["http"] != 200 or not isinstance(b, dict):
        return None
    if "flowSegmentData" in b:  # TomTom flow, unit=kmph
        f = b["flowSegmentData"]
        return dict(free_kmh=f["freeFlowSpeed"], cur_kmh=f["currentSpeed"], confidence=f.get("confidence"), frc=f.get("frc"),
                    geom=[(c["latitude"], c["longitude"]) for c in f["coordinates"]["coordinate"]])
    if "results" in b:  # HERE flow v7, prędkości w m/s
        best = b["results"]
        if not best:
            return None
        f = best[0]
        return dict(free_kmh=f["currentFlow"]["freeFlow"] * 3.6, cur_kmh=f["currentFlow"].get("speed", np.nan) * 3.6,
                    confidence=f["currentFlow"].get("confidence"), frc=None,
                    geom=[(p["lat"], p["lng"]) for lk in f["location"]["shape"]["links"] for p in lk["points"]])
    if "routes" in b and provider == "tomtom":
        s = b["routes"][0]["summary"]
        return dict(free_s=s["noTrafficTravelTimeInSeconds"], hist_s=s["historicTrafficTravelTimeInSeconds"],
                    live_s=s["liveTrafficIncidentsTravelTimeInSeconds"], tt_s=s["travelTimeInSeconds"], m=s["lengthInMeters"],
                    geom=[(p["latitude"], p["longitude"]) for lg in b["routes"][0]["legs"] for p in lg["points"]])
    if "routes" in b:  # HERE routing v8: sumy po sekcjach
        sec = b["routes"][0]["sections"]
        g = lambda k: sum(x["summary"][k] for x in sec)
        return dict(free_s=g("baseDuration"), hist_s=g("typicalDuration"), live_s=np.nan, tt_s=g("duration"), m=g("length"),
                    geom=[pt for x in sec for pt in flexpoly(x["polyline"])])
    return None


def xy(geom):
    lat, lon = np.array(geom).T
    return np.column_stack(TO_2180.transform(lon, lat))


def overlap(geom, route, L):
    """Udział długości trasy dostawcy w buforze 25 m od geometrii trasy modelu."""
    m = shapely.union_all(shapely.from_wkt(L.geometry[route].values)).buffer(25)
    c = xy(geom)
    seg = shapely.linestrings(np.stack([c[:-1], c[1:]], axis=1))  # odcinek po odcinku: trasy z zawrotką liczą się dwa razy
    tot = shapely.length(seg).sum()
    return shapely.length(shapely.intersection(seg, m)).sum() / tot if tot else np.nan


def stats(d, a, b):
    r = d[a] / d[b]
    return dict(n=len(d), mediana_model_do_dost=r.median(), MAPE_pct=(abs(d[a] - d[b]) / d[b]).mean() * 100,
                RMSE_s=math.sqrt(((d[a] - d[b]) ** 2).mean()))


def compare(provider, recs):
    L = links()
    P = pd.read_csv(OUT / "pairs.csv", dtype={"start_link": str, "end_link": str}).set_index("id")
    S = pd.read_csv(OUT / "segments.csv").set_index("id")
    sp = pd.read_csv(OUT / "split.csv").set_index("id")
    M = pd.read_csv(OUT / "model_times.csv")
    rr, sr, chk = [], [], []
    for rec in recs:
        x, meta = parse(provider, rec), rec["meta"]
        if x is None:
            chk.append(dict(id=meta["id"], problem=f"http {rec['http']} / brak wyniku"))
            continue
        i = meta["id"]
        if i in S.index:  # segment: odległość geometrii odpowiedzi od środka linku (kontrola < 50 m)
            s = S.loc[i]
            dist = shapely.distance(shapely.LineString(xy(x["geom"])) if len(x["geom"]) > 1 else shapely.points(xy(x["geom"])[0]),
                                    shapely.points(s.mx, s.my))
            sr.append(dict(id=i, cls=s.cls, model_kmh=s.freespeed_kmh, dost_free_kmh=x["free_kmh"], dost_cur_kmh=x["cur_kmh"],
                           confidence=x["confidence"], frc=x["frc"], dist_m=dist, utc=rec["utc"]))
        elif "okno" in meta:
            p = P.loc[i]
            o = xy(x["geom"][:1])[0], xy(x["geom"][-1:])[0]
            rr.append(dict(id=i, kind=p.kind, okno=meta["okno"], **{k: x[k] for k in ("free_s", "hist_s", "live_s", "tt_s")},
                           dost_km=x["m"] / 1000, overlap=overlap(x["geom"], p.route.split(), L),
                           d_start_m=math.dist(o[0], (p.o_x, p.o_y)), d_end_m=math.dist(o[1], (p.d_x, p.d_y))))
    R = pd.DataFrame(rr).merge(M, on=["id", "okno"]) if rr else pd.DataFrame()
    Sg = pd.DataFrame(sr)
    met = []
    for D in (R, Sg):
        if not D.empty:
            D["zestaw"] = D.id.map(sp.zestaw)
    # §8: punkt odpowiedzi dalej niż 50 m od punktu zapytania = dostawca przypiął inną drogę; poza metrykami, lista w kontrolach
    R_all, Sg_all = R, Sg
    if not R.empty:
        R = R[(R.d_start_m <= 50) & (R.d_end_m <= 50)].copy()
    if not Sg.empty:
        Sg = Sg[Sg.dist_m <= 50].copy()
    if not R.empty:
        R["grupa"] = np.where(R.overlap >= 0.7, R.kind, R.kind + "_trasa<70%")
        for z_, d in R.groupby("zestaw"):
            for k, dk in [("wszystkie", d), ("trasa>=70%", d[d.overlap >= 0.7])] + list(d.groupby("grupa")):
                # 1) czas swobodny: model (sieć, trasa modelu) vs noTraffic / baseDuration; ORS jako trzecie źródło.
                dd = dk[dk.okno == "rano"]  # czas swobodny nie zależy od okna: jedna obserwacja na parę
                if dd.empty:
                    continue
                met.append(dict(porownanie="swobodny_model", zestaw=z_, grupa=k, okno="-", **stats(dd, "ff_model_s", "free_s")))
                met.append(dict(porownanie="swobodny_ors", zestaw=z_, grupa=k, okno="-", **stats(dd, "ff_ors_s", "free_s")))
                met.append(dict(porownanie="dlugosc_trasy", zestaw=z_, grupa=k, okno="-", n=len(dd),
                                mediana_model_do_dost=(dd.km / dd.dost_km).median()))
                # 2) czas w oknie: mediana 5 runów vs historyczny profil dostawcy dla departAt; kongestia obu stron
                for w, dw in dk.groupby("okno"):
                    met.append(dict(porownanie="okno_vs_hist", zestaw=z_, grupa=k, okno=w, **stats(dw, "model_med", "hist_s"),
                                    model_min_do_dost=(dw.model_min / dw.hist_s).median(), model_max_do_dost=(dw.model_max / dw.hist_s).median()))
                    met.append(dict(porownanie="kongestia", zestaw=z_, grupa=k, okno=w, n=len(dw),
                                    model_okno_do_swobodny=(dw.model_med / dw.ff_model_s).median(),
                                    dost_hist_do_swobodny=(dw.hist_s / dw.free_s).median()))
    if not Sg.empty:
        for z_, d in Sg.groupby("zestaw"):
            for k, dk in [("wszystkie", d)] + list(d.groupby("cls")):
                met.append(dict(porownanie="segment_freeflow", zestaw=z_, grupa=k, okno="-", n=len(dk),
                                mediana_model_do_dost=(dk.model_kmh / dk.dost_free_kmh).median(),
                                MAPE_pct=(abs(dk.model_kmh - dk.dost_free_kmh) / dk.dost_free_kmh).mean() * 100,
                                roznica_kmh_mediana=(dk.model_kmh - dk.dost_free_kmh).median(),
                                model_kmh_mediana=dk.model_kmh.median(), dost_kmh_mediana=dk.dost_free_kmh.median()))
    Mt = pd.DataFrame(met)
    # kontrole §8 (agregaty, bez wartości dostawcy per obiekt)
    ids = set(pd.read_csv(META + "meta.csv").person) | set(pd.read_csv(META + "tlo.csv").person) | set(pd.read_csv(META + "ciezkie.csv").person)
    kontrole = dict(
        problemy=chk,
        pary_osoby_w_planach_R6=bool(P.person.dropna().isin(ids).all()),
        trasy_n=len(R_all), segmenty_n=len(Sg_all), trasy_w_metrykach=len(R), segmenty_w_metrykach=len(Sg),
        trasy_start_m_maks=round(R_all.d_start_m.max(), 1) if len(R) else None, trasy_koniec_m_maks=round(R_all.d_end_m.max(), 1) if len(R) else None,
        trasy_start_lub_koniec_ponad_50m=int(((R_all.d_start_m > 50) | (R_all.d_end_m > 50)).sum()) if len(R) else None,
        pary_trasa_ponizej_70pct=sorted(R.loc[R.overlap < 0.7, "id"].unique().tolist()) if len(R) else None,
        overlap_mediana=round(R.overlap.median(), 3) if len(R) else None,
        segment_dist_m_maks=round(Sg_all.dist_m.max(), 1) if len(Sg) else None,
        segmenty_ponad_50m=sorted(Sg_all.loc[Sg_all.dist_m > 50, "id"].tolist()) if len(Sg) else None,
        segment_freeflow_kmh_zakres=[float(Sg_all.dost_free_kmh.min()), float(Sg_all.dost_free_kmh.max())] if len(Sg) else None,
        segment_confidence_mediana=float(Sg_all.confidence.median()) if len(Sg) else None,
        frc=Sg_all.frc.value_counts().to_dict() if len(Sg) else None,
        trasa_dost_do_model_czas_swobodny_zakres=[round(float((R.free_s / R.ff_model_s).min()), 3), round(float((R.free_s / R.ff_model_s).max()), 3)] if len(R) else None)
    indep_in = dict(trasy=R[["id", "okno", "free_s", "hist_s"]].to_dict("records") if len(R) else [],
                    segmenty=Sg[["id", "dost_free_kmh"]].to_dict("records") if len(Sg) else [])
    return R, Sg, Mt, kontrole, indep_in


def plots(provider, Mt):
    """Tylko agregaty (wariant A): mediana model / dostawca po grupach, analiza vs walidacja."""
    if Mt.empty:
        return
    fig, ax = plt.subplots(1, 3, figsize=(16, 5))
    sel = [("swobodny_model", "-", "Czas swobodny trasy: model / noTraffic"),
           ("okno_vs_hist", "rano", "Czas rano 07:30: model (mediana 5 runów) / historic"),
           ("segment_freeflow", "-", "Prędkość swobodna segmentu: freespeed / freeFlowSpeed")]
    for k, (por, okno, t) in enumerate(sel):
        d = Mt[(Mt.porownanie == por) & (Mt.okno == okno)].pivot_table(index="grupa", columns="zestaw", values="mediana_model_do_dost")
        if d.empty:
            continue
        d.plot.barh(ax=ax[k], color=["#4fc3f7", "#ffb74d"][:d.shape[1]], width=0.75)
        ax[k].axvline(1, color="w", ls="--", lw=0.8)
        ax[k].set_title(t, fontsize=9); ax[k].set_xlabel("mediana model / " + provider); ax[k].set_ylabel("")
    fig.suptitle(f"R6 (uśredniony dzień roboczy) vs {provider} — agregaty, 1 = zgodność", fontsize=10)
    fig.tight_layout(); fig.savefig(OUT / f"g5_czasy_{provider}.png", dpi=130)


def cmd_selftest():
    """Syntetyczny dostawca = model × znany współczynnik; metryki muszą go odtworzyć."""
    P = pd.read_csv(OUT / "pairs.csv")
    S = pd.read_csv(OUT / "segments.csv")
    M = pd.read_csv(OUT / "model_times.csv")
    L = links()
    to_ll = Transformer.from_crs(2180, 4326, always_xy=True)
    recs = []
    for _, m in M.iterrows():
        p = P[P.id == m.id].iloc[0]
        r = p.route.split()
        pts = [L.geometry[x] for x in r[1:]]  # dostawca startuje na końcu linku startowego
        xs = [c for w in pts for c in shapely.get_coordinates(shapely.from_wkt(w)).tolist()]
        geom = [tuple(reversed(to_ll.transform(*c))) for c in xs]
        body = {"routes": [{"summary": {"noTrafficTravelTimeInSeconds": m.ff_model_s / 0.8, "historicTrafficTravelTimeInSeconds": m.model_med / 0.9,
                                        "liveTrafficIncidentsTravelTimeInSeconds": 0, "travelTimeInSeconds": 0, "lengthInMeters": m.km * 1000},
                            "legs": [{"points": [{"latitude": a, "longitude": b} for a, b in geom]}]}]}
        recs.append(dict(http=200, body=body, utc="", meta=dict(id=m.id, okno=m.okno)))
    for _, s in S.iterrows():
        g = shapely.get_coordinates(shapely.from_wkt(L.geometry[s.link])).tolist()
        body = {"flowSegmentData": {"freeFlowSpeed": s.freespeed_kmh / 1.2, "currentSpeed": 1, "confidence": 1, "frc": "FRC0",
                                    "coordinates": {"coordinate": [dict(zip(("latitude", "longitude"), reversed(to_ll.transform(*c)))) for c in g]}}}
        recs.append(dict(http=200, body=body, utc="", meta=dict(id=s.id)))
    R, Sg, Mt, kontrole, indep_in = compare("tomtom", recs)
    w = Mt[Mt.grupa == "wszystkie"].set_index(["porownanie", "zestaw", "okno"])
    for zs in ("analiza", "walidacja"):
        assert abs(w.loc[("swobodny_model", zs, "-"), "mediana_model_do_dost"] - 0.8) < 1e-6
        assert abs(w.loc[("segment_freeflow", zs, "-"), "mediana_model_do_dost"] - 1.2) < 1e-6
        for o in WIN_H:
            assert abs(w.loc[("okno_vs_hist", zs, o), "mediana_model_do_dost"] - 0.9) < 1e-6
    assert (R.overlap > 0.99).all(), R.loc[R.overlap <= 0.99, ["id", "overlap"]].drop_duplicates().to_string()
    assert (Sg.dist_m < 1).all() and (R.d_start_m < 1).all() and (R.d_end_m < 1).all(), (Sg.dist_m.max(), R_all.d_start_m.max())
    assert set(R.id) | set(Sg.id) == set(pd.read_csv(OUT / "split.csv").id)
    assert kontrole["pary_osoby_w_planach_R6"] and not kontrole["problemy"]
    import subprocess  # niezależna kontrola: osobny proces, dane przez stdin
    ind = json.loads(subprocess.run([sys.executable, "-I", str(OUT / "check_niezalezny.py")], input=json.dumps(indep_in),
                                    capture_output=True, text=True, check=True).stdout)
    mi = Mt.set_index(["porownanie", "zestaw", "grupa", "okno"])
    assert ind and all(abs(mi.loc[tuple(k.split("|")), c] - v) < 1e-9 for k, d in ind.items() for c, v in d.items()), ind
    print("selftest ok: metryki odtwarzają współczynniki 0,8 / 0,9 / 1,2, overlap = 1, dystans segmentu < 1 m")
    print("flexpoly:", flexpoly("BFoz5xJ67i1B1B7PzIhaxL7Y")[:2])  # przykład ze specyfikacji: (50.10228, 8.69821), ...


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "model":
        cmd_model()
    elif a[0] == "selftest":
        cmd_selftest()
