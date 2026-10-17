"""G6/G5: gdzie i dlaczego stoją kolejki. Przejazdy linków z eventów -> opóźnienie, przepływ wylotowy, link następny.

Użycie: uv run python -W ignore pipeline/queues.py <output_dir> <out_prefix> [t0_h t1_h]   (domyślnie 6-9)
Wyjście: <out_prefix>.json, <out_prefix>.csv (wszystkie linki z opóźnieniem).
Dla każdego linku: przejazdy pośrednie (entered -> left tego samego pojazdu; linki startu i końca podróży pominięte,
bo tam pojazd czeka na wjazd do ruchu lub kończy w środku linku), czas swobodny = length / freespeed,
przepływ wylotowy w najgorszych 15 min przeskalowany do 100% (× 1/sampleSize) vs capacity linku,
najczęstszy link następny i jego zapełnienie (pojazdy na linku vs pojemność składowania).
Przepełnienie: maks. liczba pojazdów na linku > 2 × (pojemność składowania + bufor), czyli skutek stuckTime.
Klasa przyczyny: "capacity" (wylot >= 90% capacity: link sam jest wąskim gardłem), "spillback" (wylot < 90%, a link
następny był pełny), "node" (żadne z dwóch: konkurencja na węźle albo kolejka w buforze).
"""
import gzip
import io
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
import zstandard
from lxml import etree

d, out = Path(sys.argv[1]), sys.argv[2]
T0, T1 = (float(sys.argv[3]) * 3600, float(sys.argv[4]) * 3600) if len(sys.argv) > 4 else (6 * 3600, 9 * 3600)
cfg = etree.parse(io.BytesIO(zstandard.ZstdDecompressor().stream_reader(open(d / "output_config.xml.zst", "rb")).read())
                  if (d / "output_config.xml.zst").exists() else str(d / "output_config.xml"))
p = lambda mod, name: cfg.find(f".//module[@name='{mod}']/param[@name='{name}']").get("value")
S = float(p("qsim", "storageCapacityFactor"))
F = float(p("qsim", "flowCapacityFactor"))
EFF_CELL = 7.5  # domyślne MATSim (network.effectiveCellSize w output_network); nadpisywane niżej, jeśli jest w pliku

links = {}
with zstandard.ZstdDecompressor().stream_reader(open(d / "output_network.xml.zst", "rb")) as f:
    for _, el in etree.iterparse(f, tag=("network", "link")):
        if el.tag == "link":
            a = {x.get("name"): x.text for x in el.iter("attribute")}
            links[el.get("id")] = dict(length=float(el.get("length")), freespeed=float(el.get("freespeed")),
                                       capacity=float(el.get("capacity")), lanes=float(el.get("permlanes")),
                                       type=a.get("type"), to=el.get("to"), frm=el.get("from"))
            el.clear()
        elif el.get("effectivecellsize"):
            EFF_CELL = float(el.get("effectivecellsize"))
for l in links.values():
    l["ff"] = l["length"] / l["freespeed"]
    l["storage"] = max(l["length"] * l["lanes"] / EFF_CELL * S, 1)  # jak QSim (min. 1 pojazd; QSim podnosi też do flowCap·ff)

pat = re.compile(r'time="([\d.]+)" type="(entered link|left link|vehicle enters traffic|vehicle leaves traffic)"[^>]*?'
                 r'(?:link="([^"]+)"[^>]*vehicle="([^"]+)"|vehicle="([^"]+)"[^>]*link="([^"]+)")')
enter, first, occ = {}, set(), Counter()
trav = []  # link, t_in, t_out, next link (wypełniane przy kolejnym entered)
last_trav = {}
occ_max_15 = defaultdict(int)  # (link, okno 15 min) -> maks. liczba pojazdów na linku
with zstandard.ZstdDecompressor().stream_reader(open(d / "output_events.xml.zst", "rb")) as f:
    for line in io.TextIOWrapper(f, encoding="utf-8"):
        m = pat.search(line)
        if not m:
            continue
        t, typ = float(m[1]), m[2]
        link, veh = (m[3], m[4]) if m[3] else (m[6], m[5])
        if t > T1 + 3600:
            break
        if typ == "entered link":
            if veh in last_trav:
                trav[last_trav.pop(veh)][3] = link
            enter[veh] = (link, t)
            occ[link] += 1
            if T0 <= t < T1:
                k = (link, int(t // 900))
                occ_max_15[k] = max(occ_max_15[k], occ[link])
        elif typ == "left link":
            if veh in enter and enter[veh][0] == link:
                if veh not in first and T0 <= t < T1:
                    last_trav[veh] = len(trav)
                    trav.append([link, enter[veh][1], t, None])
                occ[link] -= 1
            first.discard(veh)
            enter.pop(veh, None)
        elif typ == "vehicle enters traffic":
            first.add(veh)  # pierwszy link podróży: pomijamy (pojazd stoi w kolejce wjazdu)
            last_trav.pop(veh, None)
        else:  # leaves traffic
            if veh in enter:
                occ[enter[veh][0]] -= 1
                enter.pop(veh)
            last_trav.pop(veh, None)
            first.discard(veh)

tr = pd.DataFrame(trav, columns=["link", "t_in", "t_out", "next"])
tr["ff"] = tr.link.map(lambda l: links[l]["ff"])
tr["delay"] = (tr.t_out - tr.t_in - tr.ff - 1).clip(lower=0)  # QSim: +1 s na przejście węzła
tr["q15"] = (tr.t_out // 900).astype(int)
g = tr.groupby("link")
agg = pd.DataFrame({"n": g.size(), "delay_veh_h": g.delay.sum() / 3600, "n_gt60s": g.delay.apply(lambda x: (x > 60).sum()),
                    "delay_median_s": g.delay.median(), "delay_p90_s": g.delay.quantile(0.9)})
peak = tr.groupby(["link", "q15"]).size().groupby("link").max()  # najgorsze 15 min wylotu
agg["outflow_peak15_100pct_vph"] = peak * 4 / F
for c in ("type", "capacity", "lanes", "length", "freespeed", "storage"):
    agg[c] = agg.index.map(lambda l: links[l][c])
agg["outflow_vs_cap"] = agg.outflow_peak15_100pct_vph / agg.capacity
nxt = tr.dropna(subset=["next"]).groupby("link").next.agg(lambda x: x.value_counts().index[0])
agg["next"] = nxt
agg["next_share"] = tr.dropna(subset=["next"]).groupby("link").next.agg(lambda x: x.value_counts(normalize=True).iloc[0])
full = pd.Series({k: v for k, v in occ_max_15.items()})
occ_link = full.groupby(level=0).max()
agg["next_type"] = agg.next.map(lambda l: links[l]["type"] if isinstance(l, str) else None)
agg["next_capacity"] = agg.next.map(lambda l: links[l]["capacity"] if isinstance(l, str) else None)
agg["next_storage"] = agg.next.map(lambda l: links[l]["storage"] if isinstance(l, str) else None)
agg["next_occ_max"] = agg.next.map(lambda l: occ_link.get(l, 0) if isinstance(l, str) else None)
agg["next_full"] = agg.next_occ_max >= agg.next_storage.apply(lambda s: int(s))
indeg = Counter(l["to"] for l in links.values())
agg["node_inlinks"] = agg.index.map(lambda l: indeg[links[l]["to"]])
agg["cause"] = "node"
agg.loc[agg.next_full == True, "cause"] = "spillback"
agg.loc[agg.outflow_vs_cap >= 0.9, "cause"] = "capacity"
agg = agg.sort_values("delay_veh_h", ascending=False)
agg[agg.delay_veh_h > 0].round(3).to_csv(out + ".csv", lineterminator="\n")

# przepełnienie: QSim przy removeStuckVehicles=false po stuckTime wpycha pojazd na pełny link (kolejka się kompresuje)
ol = pd.DataFrame({"occ_max": occ_link})
ol["storage"] = ol.index.map(lambda l: links[l]["storage"])
ol["overfill"] = ol.occ_max / ol.storage.apply(lambda x: max(int(x), 1) + 1)  # +1: bufor wylotowy
over = ol[ol.overfill > 2].sort_values("occ_max", ascending=False)
tr["tt"] = tr.t_out - tr.t_in
tr["speed"] = tr.link.map(lambda l: links[l]["length"]) / tr.tt.clip(lower=1)
tot = agg.delay_veh_h.sum()
top = agg.head(20)
rep = {"run": str(d), "window_h": [T0 / 3600, T1 / 3600], "sample": F, "storage_factor": S, "effective_cell_m": EFF_CELL,
       "traversals_intermediate": len(tr), "share_traversals_delay_gt60s": round(float((tr.delay > 60).mean()), 4),
       "delay_veh_h_total_sample": round(float(tot), 1),
       "delay_share_by_cause": (agg.groupby("cause").delay_veh_h.sum() / tot).round(3).to_dict(),
       "delay_share_top20_links": round(float(top.delay_veh_h.sum() / tot), 3),
       "delay_share_by_type": (agg.groupby("type").delay_veh_h.sum() / tot).round(3).sort_values(ascending=False).to_dict(),
       "time_share_speed_lt_1_5mps": round(float(tr.tt[tr.speed < 1.5].sum() / tr.tt.sum()), 4),
       "time_share_in_delay": round(float(tr.delay.sum() / tr.tt.sum()), 4),
       "overfilled_links_gt2x": len(over), "overfilled_top": over.head(10).reset_index().round(2).to_dict(orient="records"),
       "top20": top.reset_index().round(2).to_dict(orient="records")}
json.dump(rep, open(out + ".json", "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False, default=str)
print(json.dumps({k: v for k, v in rep.items() if k != "top20"}, ensure_ascii=False, indent=1))
print(top[["type", "lanes", "capacity", "length", "n", "delay_veh_h", "delay_median_s", "outflow_peak15_100pct_vph",
           "outflow_vs_cap", "next_type", "next_capacity", "next_storage", "next_occ_max", "node_inlinks", "cause"]].round(2).to_string())
