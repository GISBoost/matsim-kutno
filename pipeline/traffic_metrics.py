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
import os
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
    """b = dostawca (wartość odniesienia). TAG M3.1 (DfT, maj 2026), tab. 3: czas modelu w 15% albo 1 min, jeśli to więcej;
    aneks C.3.10 (mikrosymulacja): w 15% i w 60 s jednocześnie. Kryterium wytycznych: > 85% tras."""
    r, e = d[a] / d[b], (d[a] - d[b]).abs()
    rmse = math.sqrt((e ** 2).mean())
    return dict(n=len(d), mediana_model_do_dost=r.median(), MAPE_pct=(e / d[b]).mean() * 100,
                RMSPE_pct=math.sqrt(((e / d[b]) ** 2).mean()) * 100,  # RMSE z odchyłek względnych (m - o) / o
                RMSE_s=rmse, MAE_s=e.mean(),
                pRMSE_pct=rmse / d[b].mean() * 100, pMAE_pct=e.mean() / d[b].mean() * 100,  # FHWA 2010: RMSE / średnia obserwacji
                srednia_dost_s=d[b].mean(),
                TAG_15pct_lub_1min_pct=(e <= np.maximum(0.15 * d[b], 60)).mean() * 100,
                TAG_15pct_i_1min_pct=((e <= 0.15 * d[b]) & (e <= 60)).mean() * 100)


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
                                MAE_kmh=(dk.model_kmh - dk.dost_free_kmh).abs().mean(),
                                RMSE_kmh=math.sqrt(((dk.model_kmh - dk.dost_free_kmh) ** 2).mean()),
                                RMSPE_pct=math.sqrt((((dk.model_kmh - dk.dost_free_kmh) / dk.dost_free_kmh) ** 2).mean()) * 100,
                                pRMSE_pct=math.sqrt(((dk.model_kmh - dk.dost_free_kmh) ** 2).mean()) / dk.dost_free_kmh.mean() * 100,
                                pMAE_pct=(dk.model_kmh - dk.dost_free_kmh).abs().mean() / dk.dost_free_kmh.mean() * 100,
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
    return R_all, Sg_all, Mt, kontrole, indep_in  # wszystkie obiekty (także > 50 m) dla mapy; metryki tylko z przefiltrowanych


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


def plot_errors(provider, Mt, out):
    """Agregaty: RMSE i MAE czasu tras [s] po oknach, MAE/RMSE prędkości segmentów [km/h], udział tras w kryterium TAG."""
    fig, ax = plt.subplots(1, 3, figsize=(17, 5))
    w = Mt[Mt.grupa == "wszystkie"]
    t = w[w.porownanie.isin(["swobodny_model", "okno_vs_hist"])].copy()
    t["co"] = np.where(t.porownanie == "swobodny_model", "swobodny", t.okno)
    order = ["swobodny", "rano", "poludnie", "popoludnie"]
    x = np.arange(len(order))
    for a, cols, ttl in ((ax[0], ["RMSE_s", "MAE_s"], "Czas trasy: RMSE i MAE [s]"),
                         (ax[2], ["TAG_15pct_lub_1min_pct", "TAG_15pct_i_1min_pct"], "Trasy w kryterium TAG M3.1 [%]")):
        i = 0
        for z_, cs in (("analiza", ("#4fc3f7", "#0288d1")), ("walidacja", ("#ffb74d", "#f57c00"))):
            d = t[t.zestaw == z_].set_index("co").reindex(order)
            for cc, col in zip(cols, cs):
                lab = cc.split("_")[0] if cc.endswith("_s") else ("15% lub 1 min" if "lub" in cc else "15% i 1 min")
                b = a.bar(x + (i - 1.5) * 0.2, d[cc], 0.2, color=col, label=f"{z_}: {lab}")
                a.bar_label(b, fmt="%.0f", fontsize=7)
                i += 1
        a.set_xticks(x, order); a.set_title(ttl, fontsize=10)
        a.legend(fontsize=7, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.08))
    ax[2].set_ylim(0, 100)
    ax[2].axhline(85, color="w", ls="--", lw=0.8)
    ax[2].text(-0.45, 87, "wytyczna TAG: > 85% tras", fontsize=7)
    s = Mt[Mt.porownanie == "segment_freeflow"]
    piv = s.pivot_table(index="grupa", columns="zestaw", values=["MAE_kmh", "RMSE_kmh"])
    nn = s.pivot_table(index="grupa", columns="zestaw", values="n").reindex(piv.index).fillna(0).astype(int)
    piv.columns = [f"{b}: {a.split('_')[0]}" for a, b in piv.columns]
    piv.plot.barh(ax=ax[1], color=["#0288d1", "#f57c00", "#4fc3f7", "#ffb74d"][:piv.shape[1]], width=0.8)
    for cont in ax[1].containers:
        ax[1].bar_label(cont, fmt="%.0f", fontsize=7)
    ax[1].set_yticks(range(len(piv.index)), [f"{g} (n {' / '.join(map(str, nn.loc[g].tolist()))})" for g in piv.index])
    ax[1].set_title("Prędkość swobodna segmentu: MAE i RMSE [km/h]\n(n analiza / walidacja)", fontsize=10)
    ax[1].legend(fontsize=7, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.08)); ax[1].set_ylabel("")
    fig.suptitle(f"R6 vs {provider}: błędy (agregaty; analiza = 2/3 próbki, walidacja = 1/3; model = uśredniony dzień roboczy)", fontsize=10)
    fig.tight_layout(); fig.savefig(out, dpi=130)
    plt.close(fig)


def scatter_speeds(provider, R, Sg, out):
    """Rozrzut prędkości: symulowana (x) vs dostawca (y), prosta MNK y = ax + b i R² (wszystkie punkty w metrykach).
    Trasy: prędkość = długość / czas (model: trasa modelu; dostawca: jego trasa). Wartości per obiekt, więc plik poza repo."""
    R = R[(R.d_start_m <= 50) & (R.d_end_m <= 50)]
    Sg = Sg[Sg.dist_m <= 50]
    rr, rf = R[R.okno == "rano"], R[R.okno == "rano"]
    panels = [("Segmenty: prędkość swobodna", Sg.id, Sg.model_kmh, Sg.dost_free_kmh, "freespeed linku", "freeFlowSpeed"),
              ("Trasy: prędkość w ruchu swobodnym", rf.id, rf.km / (rf.ff_model_s / 3600), rf.dost_km / (rf.free_s / 3600),
               "model, sieć D13", "noTraffic"),
              ("Trasy: prędkość rano 07:30", rr.id, rr.km / (rr.model_med / 3600), rr.dost_km / (rr.hist_s / 3600),
               "model, mediana 5 runów", "historic")]
    sp = pd.read_csv(OUT / "split.csv").set_index("id").zestaw
    fig, ax = plt.subplots(1, 3, figsize=(17, 5.8))
    for a, (ttl, ids, x, y, xl, yl) in zip(ax, panels):
        z = ids.map(sp).values
        for zs, c in (("analiza", "#4fc3f7"), ("walidacja", "#ffb74d")):
            m = z == zs
            a.scatter(x[m], y[m], s=36, color=c, edgecolors="w", lw=0.5, label=f"{zs} (n {m.sum()})", zorder=3)
        k, b = np.polyfit(x, y, 1)
        r2 = np.corrcoef(x, y)[0, 1] ** 2
        lo, hi = 0, max(x.max(), y.max()) * 1.05
        xx = np.array([x.min(), x.max()])
        a.plot(xx, k * xx + b, "w--", lw=1.2, zorder=2)
        a.plot([lo, hi], [lo, hi], color="#888", lw=0.8, ls=":", zorder=1, label="y = x")
        a.text(0.04, 0.95, f"y = {k:.4f}x {'+' if b >= 0 else '−'} {abs(b):.4f}\nR² = {r2:.4f}".replace(".", ","), transform=a.transAxes,
               va="top", fontsize=9, bbox=dict(facecolor="black", edgecolor="w"))
        a.set_xlim(lo, hi); a.set_ylim(lo, hi); a.set_aspect("equal"); a.grid(alpha=0.25)
        a.set_xlabel(f"Symulowana prędkość ({xl}) [km/h]"); a.set_ylabel(f"{provider} ({yl}) [km/h]")
        a.set_title(ttl, fontsize=10); a.legend(fontsize=7, loc="lower right")
    fig.suptitle(f"R6 vs {provider}: rozrzut prędkości (prosta MNK na wszystkich punktach; model = uśredniony dzień roboczy)", fontsize=10)
    fig.tight_layout(); fig.savefig(out, dpi=140)
    plt.close(fig)


def mapa(provider, R, Sg, out):
    """Mapa próbki: trasy modelu (kolor = czas rano model / dostawca), segmenty (kolor = freespeed / freeFlowSpeed, etykieta
    model/dostawca km/h). Wartości dostawcy per obiekt, więc plik poza repo (output/, D22 wariant A)."""
    from matplotlib import cm
    from matplotlib.colors import TwoSlopeNorm
    L = links()
    P = pd.read_csv(OUT / "pairs.csv", dtype={"start_link": str, "end_link": str}).set_index("id")
    S = pd.read_csv(OUT / "segments.csv").set_index("id")
    gm = shapely.from_geojson(Path("scenarios/kutno/area/gmina.geojson").read_text(encoding="utf-8"))
    major = shapely.from_wkt(L.geometry[L.type.isin(["motorway", "primary", "secondary", "tertiary"])])
    norm, cmap = TwoSlopeNorm(1.0, 0.6, 1.4), cm.coolwarm
    x0, y0, x1, y1 = shapely.bounds(gm)
    zoom = (x0 - 1500, x1 + 1500, y0 - 1500, y1 + 1500)  # przybliżenie: gmina Kutno + 1,5 km
    inside = lambda x, y: zoom[0] <= x <= zoom[1] and zoom[2] <= y <= zoom[3]
    fig, axx = plt.subplots(2, 3, figsize=(24, 14), gridspec_kw=dict(width_ratios=[1.45, 1, 0.5]))
    ax, side = axx[:, :2], axx[:, 2]
    for a in side:
        a.axis("off")
    for a in ax.ravel():
        for ln in major:
            c = shapely.get_coordinates(ln)
            a.plot(c[:, 0], c[:, 1], color="#555", lw=0.4, zorder=1)
        c = shapely.get_coordinates(shapely.boundary(gm))
        a.plot(c[:, 0], c[:, 1], color="#aed581", lw=1, zorder=2)
        a.set_aspect("equal"); a.set_xticks([]); a.set_yticks([])
    for a in ax[:, 1]:
        a.set_xlim(zoom[:2]); a.set_ylim(zoom[2:])
    # trasy: numer na trasie, lista numerów z wartościami w ramce (etykiety w mieście się nakładały)
    rr = R[R.okno == "rano"].reset_index(drop=True)
    legend = []
    for i, r in rr.iterrows():
        p = P.loc[r.id]
        c = np.vstack([shapely.get_coordinates(shapely.from_wkt(L.geometry[x])) for x in p.route.split()])
        v = r.model_med / r.hist_s
        nr = i + 1
        legend.append(f"{nr:2d} {r.id[2:20]:<18} {r.model_med / 60:4.1f}/{r.hist_s / 60:4.1f} min  {v:.2f}")
        for a in ax[0]:
            a.plot(c[:, 0], c[:, 1], color=cmap(norm(v)), lw=2.4 if p.kind == "korytarz" else 1.3, alpha=0.9, zorder=3)
            a.scatter([p.o_x], [p.o_y], s=14, c="w", zorder=4)
            a.scatter([p.d_x], [p.d_y], s=14, marker="s", c="w", zorder=4)
        # numer: punkt trasy w 40% długości (żeby nie siadał na wspólnym celu w centrum)
        m = c[int(len(c) * 0.4)]
        a = ax[0, 1] if inside(*m) else ax[0, 0]
        a.annotate(str(nr), m, fontsize=8, color="w", weight="bold", zorder=5,
                   bbox=dict(boxstyle="round,pad=0.1", fc=cmap(norm(v)), ec="none", alpha=0.85))
    ax[0, 0].set_title(f"Trasy (n {len(rr)}): czas rano 07:30, model (mediana 5 runów) / {provider} historic\n"
                       "kółko start, kwadrat cel; numery w ramce obok", fontsize=10)
    ax[0, 1].set_title("Trasy: przybliżenie na Kutno", fontsize=10)
    side[0].text(0.0, 1.0, "nr id                 model/" + provider + " iloraz\n" + "\n".join(legend), transform=side[0].transAxes,
                 fontsize=7, family="monospace", va="top", ha="left", color="w")
    for _, s in Sg.iterrows():
        q = S.loc[s.id]
        ok = s.dist_m <= 50
        v = q.freespeed_kmh / s.dost_free_kmh
        lab = f"{q.cls}\n{q.freespeed_kmh:.0f}/{s.dost_free_kmh:.0f} km/h" + ("" if ok else f"\n> 50 m ({s.dist_m:.0f} m)")
        for a, show in ((ax[1, 0], not inside(q.mx, q.my)), (ax[1, 1], inside(q.mx, q.my))):
            if ok:
                a.scatter([q.mx], [q.my], s=90, color=cmap(norm(v)), edgecolors="w", zorder=4)
            else:
                a.scatter([q.mx], [q.my], s=70, color="#999", marker="x", zorder=4)
            if show:
                a.annotate(lab, (q.mx, q.my), xytext=(5, 5), textcoords="offset points", fontsize=7.5,
                           color="w" if ok else "#999", zorder=5)
    ax[1, 0].set_title(f"Segmenty (n {len(Sg)}): freespeed modelu / {provider} freeFlowSpeed\n"
                       f"etykieta: klasa, model / {provider} km/h; x = punkt > 50 m (poza metrykami)", fontsize=10)
    ax[1, 1].set_title("Segmenty: przybliżenie na Kutno (etykiety punktów w mieście)", fontsize=10)
    fig.colorbar(cm.ScalarMappable(norm=norm, cmap=cmap), ax=side[1], fraction=0.5, location="left",
                 label=f"model / {provider} (trasy: > 1 model wolniejszy; segmenty: < 1 model wolniejszy)")
    fig.suptitle(f"Próbka walidacji R6 vs {provider} (EPSG:2180, zielona linia = gmina Kutno, szare = drogi motorway–tertiary)", fontsize=12)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.93, bottom=0.02, wspace=0.04, hspace=0.12)
    fig.savefig(out, dpi=110)
    plt.close(fig)


# ---------------------------------------------------------------- D23: dopasowanie f_g (plan reports/etap2/g5_predkosci_d23/plan.md §2)
OUT_D23 = Path("reports/etap2/g5_predkosci_d23")
F_LO, F_HI, F_D13 = 0.5, 1.1, 0.8


class RouteModel:
    """Czas swobodny trasy jako funkcja f_g: sum L / min(limit * f_g, v_cap) + 0,5 s na link (średnio floor(x) + 1, I1).
    Linki poza grupami (zawrotki) mają stały freespeed. Ciężkie: v_cap = 80 km/h (D20). Pierwszy link trasy pomijany
    (noga car startuje na jego końcu)."""

    def __init__(self, ids):
        import traffic_providers as tp
        L = tp.links()
        L["grp"] = tp.speed_groups(L)
        self.groups = tp.GROUPS
        gi = {g: i for i, g in enumerate(self.groups)}
        P = pd.read_csv(OUT / "pairs.csv", dtype={"start_link": str, "end_link": str}).set_index("id")
        r_idx, length, allowed, gidx, fixed_v, cap = [], [], [], [], [], []
        for k, i in enumerate(ids):
            p = P.loc[i]
            route = p.route.split()[1:]
            x = L.loc[route]
            r_idx += [k] * len(x)
            length += x.length.tolist()
            allowed += x.allowed_speed.fillna(0).tolist()
            gidx += [gi.get(g, -1) for g in x.grp]
            fixed_v += x.freespeed.tolist()
            cap += [VMAX_HEAVY if p["mode"] == "truck" else np.inf] * len(x)
        self.ids, self.n = list(ids), len(ids)
        self.r, self.L, self.a, self.g = np.array(r_idx), np.array(length), np.array(allowed), np.array(gidx)
        self.v0, self.cap = np.array(fixed_v), np.array(cap)
        grouped = self.g >= 0
        # D13: freespeed = limit × 0,8 dla wszystkich linków w grupach (kontrola spójności z siecią R6)
        assert np.allclose(self.v0[grouped], self.a[grouped] * F_D13, rtol=1e-6), "freespeed != 0,8 × allowed_speed"
        self.nlinks = np.bincount(self.r, minlength=self.n)
        km = pd.DataFrame(dict(r=self.r, g=self.g, L=self.L))
        self.km = km[km.g >= 0].groupby("g").L.sum().reindex(range(len(self.groups)), fill_value=0) / 1000

    def times(self, f, sel=None):
        v = np.where(self.g >= 0, self.a * np.asarray(f)[np.maximum(self.g, 0)], self.v0)
        v = np.minimum(v, self.cap)
        t = np.bincount(self.r, self.L / v, minlength=self.n) + 0.5 * self.nlinks
        return t if sel is None else t[sel]


def fit_factors(H, seed=4711 + 23, n_boot=1000):  # seed z config/kutno.toml + 23 (jak sample_d23)
    """H: id, okno, hist_s (dostawca, tylko zestaw analizy). Zwraca tabelę f_g z przedziałem 90% (bootstrap po trasach),
    flagą identyfikowalności i metrykami przed (f = 0,8) i po dopasowaniu (przewidywanie bez nowego runu: Delta z R6 stałe)."""
    from scipy.optimize import least_squares
    ids = sorted(H.id.unique())
    rm = RouteModel(ids)
    M = pd.read_csv(OUT / "model_times.csv").set_index(["id", "okno"])
    H = H.copy()
    H["k"] = H.id.map({i: k for k, i in enumerate(ids)})
    base = rm.times([F_D13] * len(rm.groups))
    # Delta = kongestia R6 (mediana 5 runów) ponad czas swobodny tej samej formuły przy f = 0,8
    H["delta"] = [M.loc[(i, w), "model_med"] - base[k] for i, w, k in zip(H.id, H.okno, H.k)]
    k_arr, d_arr, y_arr = H.k.values, H.delta.values, np.log(H.hist_s.values)

    def resid(f, rows):
        return np.log(rm.times(f)[k_arr[rows]] + d_arr[rows]) - y_arr[rows]

    allrows = np.arange(len(H))
    x0 = np.full(len(rm.groups), F_D13)
    sol = least_squares(resid, x0, bounds=(F_LO, F_HI), args=(allrows,))
    rng = np.random.default_rng(seed)
    by_route = [np.flatnonzero(k_arr == k) for k in range(rm.n)]
    boot = []
    for _ in range(n_boot):
        pick = rng.integers(rm.n, size=rm.n)
        rows = np.concatenate([by_route[k] for k in pick])
        boot.append(least_squares(resid, sol.x, bounds=(F_LO, F_HI), args=(rows,)).x)
    boot = np.array(boot)
    lo, hi = np.percentile(boot, 5, axis=0), np.percentile(boot, 95, axis=0)
    # trasy z przewagą grupy (>= 50% długości) w zestawie dopasowania
    km_r = pd.DataFrame(dict(r=rm.r, g=rm.g, L=rm.L)).query("g >= 0").pivot_table(index="r", columns="g", values="L", aggfunc="sum").fillna(0)
    dom = km_r.idxmax(axis=1)[km_r.max(axis=1) / km_r.sum(axis=1) >= 0.5]
    T = pd.DataFrame(dict(grupa=rm.groups, f_dopasowane=sol.x, p05=lo, p95=hi, km_w_trasach=rm.km.values,
                          trasy_z_przewaga=[int((dom == i).sum()) for i in range(len(rm.groups))]))
    T["identyfikowalna"] = (T.trasy_z_przewaga >= 12) & ((T.p95 - T.p05) / 2 <= 0.1)
    T["f_final"] = np.where(T.identyfikowalna, T.f_dopasowane, F_D13)
    T["na_granicy"] = np.isclose(T.f_dopasowane, F_LO) | np.isclose(T.f_dopasowane, F_HI)

    def metr(f):
        e = rm.times(f)[k_arr] + d_arr
        rel = (e - H.hist_s.values) / H.hist_s.values
        return dict(MAPE_pct=np.abs(rel).mean() * 100, RMSPE_pct=np.sqrt((rel ** 2).mean()) * 100,
                    mediana_model_do_dost=float(np.median(e / H.hist_s.values)),
                    TAG_15pct_lub_1min_pct=float((np.abs(e - H.hist_s.values) <= np.maximum(0.15 * H.hist_s.values, 60)).mean() * 100))
    summary = dict(n_tras=rm.n, n_obserwacji=len(H), n_boot=n_boot, przed_f08=metr(x0), po_f_dopasowane=metr(sol.x),
                   po_f_final=metr(T.f_final.values), koszt_przed=float((resid(x0, allrows) ** 2).sum()),
                   koszt_po=float((resid(sol.x, allrows) ** 2).sum()), status_optymalizacji=int(sol.status))
    return T, summary


def cmd_selftest_fit():
    """Syntetyczny dostawca: czasy z modelu przy znanych f_g (+ Delta z R6) × szum log-normalny 5%; dopasowanie musi je odtworzyć."""
    sp = pd.read_csv(OUT / "split.csv").set_index("id").zestaw
    M = pd.read_csv(OUT / "model_times.csv")
    M = M[M.id.map(sp) == "analiza"]
    ids = sorted(M.id.unique())
    rm = RouteModel(ids)
    f_true = np.array([0.95, 0.92, 0.70, 0.62, 0.75, 0.66])
    base, t = rm.times([F_D13] * 6), rm.times(f_true)
    k = M.id.map({i: j for j, i in enumerate(ids)}).values
    rng = np.random.default_rng(1)
    H = pd.DataFrame(dict(id=M.id.values, okno=M.okno.values,
                          hist_s=(t[k] + (M.model_med.values - base[k])) * np.exp(rng.normal(0, 0.05, len(M)))))
    T, s = fit_factors(H, n_boot=200)
    T["f_true"] = f_true
    print(T.round(3).to_string())
    print(json.dumps(s, indent=1, default=float))
    err = (T.f_dopasowane - T.f_true).abs()
    assert (err < 0.06).all(), err
    assert ((T.p05 <= T.f_true) & (T.f_true <= T.p95)).sum() >= 5
    # bez szumu i przy f = 0,8: koszt 0 (spójność formuły z model_times)
    H0 = pd.DataFrame(dict(id=M.id.values, okno=M.okno.values, hist_s=M.model_med.values))
    T0, s0 = fit_factors(H0, n_boot=5)
    assert np.allclose(T0.f_dopasowane, F_D13, atol=1e-3) and s0["koszt_przed"] < 1e-12, (T0, s0)
    print("selftest_fit ok: f_g odtworzone (błąd maks. %.3f), przy danych = model f = 0,8 i koszt 0" % err.max())


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
    tmp = Path(os.environ.get("TEMP", ".")) / "g5_selftest"
    tmp.mkdir(exist_ok=True)
    plot_errors("tomtom", Mt, tmp / "bledy.png")
    mapa("tomtom", R, Sg, tmp / "mapa.png")
    scatter_speeds("tomtom", R, Sg, tmp / "rozrzut.png")
    assert "MAE_s" in Mt and "RMSE_kmh" in Mt and Mt.TAG_15pct_lub_1min_pct.max() <= 100
    print("selftest: wykresy w", tmp)
    print("selftest ok: metryki odtwarzają współczynniki 0,8 / 0,9 / 1,2, overlap = 1, dystans segmentu < 1 m")
    print("flexpoly:", flexpoly("BFoz5xJ67i1B1B7PzIhaxL7Y")[:2])  # przykład ze specyfikacji: (50.10228, 8.69821), ...


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "model":
        cmd_model()
    elif a[0] == "selftest_fit":
        cmd_selftest_fit()
    elif a[0] == "selftest":
        cmd_selftest()
