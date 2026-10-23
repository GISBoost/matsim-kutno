"""Zawrotki na początku i końcu trasy (link -> link odwrotny w pierwszych/ostatnich 3 linkach): pomiar z eventów.
Użycie: uv run python -W ignore reports/etap3/g_zawrotki/zawrotki_pomiar.py <katalog_runu> <meta.csv> <wyjscie.json> [network.xml.gz]
Zawrotka = kolejne linki A (from u, to v) i B (from v, to u). Dodatkowy czas = czas przejazdu pary (start: tylko link B, bo link startowy opuszcza się od razu).
Podróż z eventów: 'vehicle enters traffic' -> 'vehicle leaves traffic' (nogi walk są teleportowane i nie mają linków)."""
import gzip
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
import zstandard
from lxml import etree

run, meta_f, out_f = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
NET = sys.argv[4] if len(sys.argv) > 4 else "scenarios/kutno/network.xml.gz"  # na GHA sieć leży w scenariuszu (ERRORS 33)
z = lambda p: zstandard.ZstdDecompressor().stream_reader(open(p, "rb"))
ends = {}
with gzip.open(NET, "rb") as f:
    for _, el in etree.iterparse(f, tag="link"):
        ends[el.get("id")] = (el.get("from"), el.get("to"), float(el.get("length")))
        el.clear()
rev = lambda a, b: ends[a][0] == ends[b][1] and ends[a][1] == ends[b][0]
cur, trips = {}, []
for _, el in etree.iterparse(z(run / "output_events.xml.zst"), tag="event"):
    t, v = el.get("type"), el.get("vehicle")
    if t == "vehicle enters traffic":
        cur[v] = [(el.get("link"), float(el.get("time")), float(el.get("time")))]
    elif t == "entered link" and v in cur:
        cur[v].append((el.get("link"), float(el.get("time")), None))
    elif t == "left link" and v in cur:
        l, t0, _ = cur[v][-1]
        cur[v][-1] = (l, t0, float(el.get("time")))
    elif t == "vehicle leaves traffic" and v in cur:
        s = cur.pop(v)
        l, t0, t1 = s[-1]
        s[-1] = (l, t0, float(el.get("time")))  # ostatni link: przejechany w całości do zakończenia
        trips.append((v, s))
    el.clear()
rows = []
for v, s in trips:
    L = [x[0] for x in s]
    dur = s[-1][2] - s[0][1]
    start = len(L) >= 2 and rev(L[0], L[1])
    t_start = (s[1][2] - s[1][1]) if start else 0.0
    n = len(L)
    end_i = [i for i in range(max(1, n - 3), n - 1) if rev(L[i], L[i + 1])] if n >= 3 else []
    t_end = sum(s[i][2] - s[i][1] + s[i + 1][2] - s[i + 1][1] for i in end_i[:1])
    mid = [i for i in range(1, n - 3) if rev(L[i], L[i + 1])]
    rows.append(dict(veh=v, kind=v[0], n_links=n, dur=dur, start_uturn=start, t_start=t_start, end_uturn=bool(end_i), t_end=t_end, mid_uturn=len(mid) > 0,
                     d_start=ends[L[1]][2] if start else 0.0, d_end=sum(ends[L[i]][2] + ends[L[i + 1]][2] for i in end_i[:1])))
df = pd.DataFrame(rows)
meta = pd.read_csv(meta_f)
res = {"trips": len(df)}
g = df.groupby("kind").agg(n=("veh", "size"), start_pct=("start_uturn", "mean"), end_pct=("end_uturn", "mean"), mid_pct=("mid_uturn", "mean"),
                           dur_mean_s=("dur", "mean"), t_start_s=("t_start", "sum"), t_end_s=("t_end", "sum"), dur_sum_s=("dur", "sum"))
g["extra_pct_of_time"] = (g.t_start_s + g.t_end_s) / g.dur_sum_s * 100
for c in ("start_pct", "end_pct", "mid_pct"):
    g[c] *= 100
res["wg_rodzaju"] = g.round(2).to_dict("index")
tot = df
res["razem"] = dict(start_pct=round(df.start_uturn.mean() * 100, 1), end_pct=round(df.end_uturn.mean() * 100, 1), mid_pct=round(df.mid_uturn.mean() * 100, 2),
                    any_pct=round((df.start_uturn | df.end_uturn).mean() * 100, 1), extra_veh_h=round((df.t_start.sum() + df.t_end.sum()) / 3600, 1),
                    total_veh_h=round(df.dur.sum() / 3600, 1), extra_pct=round((df.t_start.sum() + df.t_end.sum()) / df.dur.sum() * 100, 2),
                    mean_extra_s_on_uturn_trips=round(float((df.t_start + df.t_end)[df.start_uturn | df.end_uturn].mean()), 1),
                    mean_extra_m_on_uturn_trips=round(float((df.d_start + df.d_end)[df.start_uturn | df.end_uturn].mean()), 1))
# kierunek linku przypiętego: sufiks f/r
suf = lambda s: s.astype(str).str[-1]
res["sufiks_linku_przypiecia"] = {"dom": suf(meta.home_link).value_counts().to_dict(), "praca": suf(meta.work_link[meta.work_src != "exit"]).value_counts().to_dict()}
# podróże pracujących: tam (dep dom) i z powrotem
w = df[df.kind.isin(["r", "c", "o"])].copy()
w["trip_no"] = w.groupby("veh").cumcount()
res["pracujacy_tam_vs_z_powrotem"] = {("tam" if k == 0 else "z_powrotem"): dict(start_pct=round(x.start_uturn.mean() * 100, 1), end_pct=round(x.end_uturn.mean() * 100, 1),
                                                                                   dur_s=round(x.dur.mean(), 1)) for k, x in w.groupby("trip_no")}
json.dump(res, open(out_f, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps(res, indent=1, ensure_ascii=False))
