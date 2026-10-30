"""F4: walidacja plans.xml.gz + mapa kontrolna.

Użycie: uv run python -W ignore pipeline/validate_plans.py <plans.xml.gz> <sample> <out_dir> [klucz=wartość ...]
  (sample i out_dir wymagane, out_dir musi istnieć: brak domyślnych katalogów, by nie nadpisać raportu fazy; klucz=wartość jak w plans.py, np. jobs_total=17486)
Test (TASKS F4): każda osoba ma dokładnie home-car-work-car-home (D31: albo home-car-work-walk-work-car-home); współrzędne w obszarze sieci; praca w gminie Kutno;
liczba osób = round(sample x (pracujący w Kutnie + przyjeżdżający)); ten sam sha256 po ponownym uruchomieniu plans.py.
Wyjście: <out_dir>/plans_<N>pct_plans.{json,png}. Kod 1, gdy test nie przechodzi; kod 2, gdy brak argumentów lub out_dir nie istnieje.
"""
import gzip
import hashlib
import json
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

import geopandas as gpd
import matplotlib
import pandas as pd
from lxml import etree
from shapely.geometry import Point

matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use("dark_background")  # mapy w ciemnym motywie (prośba użytkownika)

if len(sys.argv) < 4 or not Path(sys.argv[3]).is_dir():
    print("Użycie: validate_plans.py <plans.xml.gz> <sample> <out_dir> [klucz=wartość ...]  (out_dir musi istnieć)", file=sys.stderr)
    sys.exit(2)
path = Path(sys.argv[1])
P = tomllib.loads(Path("config/kutno.toml").read_text(encoding="utf-8"))["plans"]
P["sample"] = float(sys.argv[2])  # sample jak w plans.py
OVR = sys.argv[4:]
for kv in OVR:
    k, v = kv.split("=")
    P[k] = type(P[k])(v)
PHASE = f"plans_{round(P['sample'] * 100)}pct"
OUT = sys.argv[3]
f3 = json.load(open("scenarios/kutno/validation/f3_demand.json", encoding="utf-8"))
area = gpd.read_file("scenarios/kutno/area/network_area.geojson").geometry.iloc[0]
gmina = gpd.read_file("scenarios/kutno/area/gmina.geojson").geometry.iloc[0]
powiat = gpd.read_file("scenarios/kutno/area/powiat.geojson").geometry.iloc[0]

persons, bad_chain = [], []
ERR = ([], [])  # D32: zakupy i usługi (kind=errand): (poprawne, złe łańcuchy)
BG = {"tlo": ([], []), "ciezkie": ([], [])}  # D19/K2-2, D20: subpopulacja -> (poprawne, złe łańcuchy)
veh_attr = 0
with gzip.open(path, "rb") as f:
    for _, el in etree.iterparse(f, tag="person"):
        plans = el.findall("plan")
        seq = [c.get("type") if c.tag == "activity" else c.get("mode") for c in plans[0]] if len(plans) == 1 else []
        acts = plans[0].findall("activity") if plans else []
        at = {a.get("name"): a.text for a in el.iter("attribute")}
        sub = at.get("subpopulation")
        veh_attr += at.get("vehicles") == '{"car":"%s"}' % el.get("id")
        if at.get("kind") == "errand":  # D32: home -> shop|service -> home, start z end_time, pobyt z max_dur
            ok = (seq in (["home", "car", "shop", "car", "home"], ["home", "car", "service", "car", "home"]) and acts[0].get("end_time")
                  and acts[1].get("max_dur") and not acts[1].get("end_time") and sub == "person")
            ERR[0 if ok else 1].append(el.get("id"))
            el.clear()
            continue
        if sub in BG:  # D19/K2-2, D20: tło = jedna podróż tlo_start -> tlo_end, start z end_time
            ok = seq == ["tlo_start", "car", "tlo_end"] and acts[0].get("end_time") and not acts[1].get("end_time")
            BG[sub][0 if ok else 1].append(dict(id=el.get("id"), o=acts[0].get("link") if acts else None,
                                                 d=acts[-1].get("link") if acts else None))
            el.clear()
            continue
        split = seq == ["home", "car", "work", "walk", "work", "car", "home"]  # D31: praca = przyjazd + odjazd (osobne linki, noga walk 0 m)
        timing_ok = (len(acts) in (3, 4) and acts[0].get("end_time") and not acts[0].get("max_dur")
                     and all(a.get("max_dur") and not a.get("end_time") for a in acts[1:-1]))
        if (seq != ["home", "car", "work", "car", "home"] and not split) or not timing_ok:
            bad_chain.append(el.get("id"))
        else:
            h, w = (Point(float(a.get("x")), float(a.get("y"))) for a in acts[:2])
            persons.append(dict(id=el.get("id"), h=h, w=w, same_home=acts[0].get("x") == acts[-1].get("x")
                                and acts[0].get("y") == acts[-1].get("y")))
        el.clear()

df = pd.DataFrame(persons)
df["outbound"] = df.id.str.startswith("o")  # D17/O1: id wyjeżdżających = o<gmina pracy>_<k>
strata = pd.read_csv(path.with_name(path.name.removesuffix(".xml.gz") + "_strata.csv"), dtype={"key": str})
outb_total = strata.n[strata.kind == "outbound"].sum()  # D17/O1
assert abs(strata.n.sum() - f3["agents_100pct"][P["variant"]] - outb_total) < 1, "strata != F3"
assert outb_total == f3["outgoing_employees"]
excluded = strata[strata.excluded]  # D16/B, D17/O1
excl_out = excluded.n[excluded.kind == "outbound"].sum()
jobs_100 = P["jobs_total"] or f3["agents_100pct"][P["variant"]] - (excluded.n.sum() - excl_out)  # D17/C
car = P["car_share"] * (1 - P["work_from_home"])  # D19/K1-1
assert abs(strata.n_model[strata.kind != "outbound"].sum() - jobs_100 * car) < 1
expected = round(P["sample"] * car * (jobs_100 + outb_total - excl_out))
sha = hashlib.sha256(path.read_bytes()).hexdigest()
with tempfile.TemporaryDirectory() as d:
    subprocess.run([sys.executable, "-W", "ignore", "pipeline/plans.py", str(Path(d) / "plans.xml.gz"), str(P["sample"]), *OVR], check=True,
                   capture_output=True)
    sha2 = hashlib.sha256((Path(d) / "plans.xml.gz").read_bytes()).hexdigest()

meta = pd.read_csv(path.with_name(path.name.removesuffix(".xml.gz") + "_meta.csv"))
meta["dep_h"] = meta.dep_s / 3600  # wyjazd z domu albo wjazd na granicę (profil D14, D16/A)
link_type = {}
with gzip.open("scenarios/kutno/network.xml.gz", "rb") as f:
    for _, el in etree.iterparse(f, tag="link"):
        link_type[el.get("id")] = {a.get("name"): a.text for a in el.iter("attribute")}.get("type")
        el.clear()
own = meta.home_src != "entry"
bad_snap = int(meta[own].home_link.map(link_type).isin(P["snap_exclude_types"]).sum()
               + meta[meta.work_src != "exit"].work_link.map(link_type).isin(P["snap_exclude_types"]).sum())
missing_link = int((~meta.home_link.isin(link_type.keys())).sum() + (~meta.work_link.isin(link_type.keys())).sum())
if "home_link_end" in meta:  # D29: dom na końcu dnia ma własny link
    missing_link += int((~meta.home_link_end.isin(link_type.keys())).sum())
start_ok = bool((meta.start_s == meta.dep_s).all())  # D16/A
stem = path.name.removesuffix(".xml.gz")


def bg_report(sub, od_file):
    good, bad = BG[sub]
    tl = pd.DataFrame(good, columns=["id", "o", "d"])
    exp = round(pd.read_csv(od_file).trips_day.sum() * P["sample"]) if od_file else 0
    mf = path.with_name(f"{stem}_{sub}.csv")
    m = pd.read_csv(mf) if mf.exists() else pd.DataFrame(columns=["start_s"])
    miss = int((~tl.o.isin(link_type.keys())).sum() + (~tl.d.isin(link_type.keys())).sum())
    r = {"persons": len(tl) + len(bad), "expected": exp, "bad_chain_n": len(bad), "links_missing": miss,
         "same_link_od": int((tl.o == tl.d).sum()),
         "start_by_hour": (m.start_s // 3600).value_counts().sort_index().to_dict() if len(m) else {},
         "profile": P["background_profile"], "od_file": od_file}
    r["ok"] = r["persons"] == exp and not bad and miss == 0
    return r


tlo_report, heavy_report = bg_report("tlo", P["background_od"]), bg_report("ciezkie", P.get("heavy_od", ""))
veh_report = {"heavy": bool(heavy_report["persons"])}
if veh_report["heavy"]:  # D20: plik pojazdów, każda osoba ma swój pojazd, ciężkie typu ciezki z heavy_pce
    vt = etree.parse(gzip.open(path.with_name(stem + "_vehicles.xml.gz")))
    ns = {"v": "http://www.matsim.org/files/dtd"}
    types = {v.get("id"): v.get("type") for v in vt.findall("v:vehicle", ns)}
    pce = {t.get("id"): float(t.find("v:passengerCarEquivalents", ns).get("pce")) for t in vt.findall("v:vehicleType", ns)}
    hid = {x["id"] for x in BG["ciezkie"][0]}
    n_all = len(df) + len(bad_chain) + sum(len(a) + len(b) for a, b in BG.values()) + len(ERR[0]) + len(ERR[1])
    veh_report.update(vehicles=len(types), persons_all=n_all, persons_with_vehicle_attr=veh_attr, pce=pce,
                      heavy_type_ok=all(types.get(i) == "ciezki" for i in hid),
                      others_car=sum(t == "car" for t in types.values()) == len(types) - len(hid))
    veh_report["ok"] = (len(types) == n_all == veh_attr and veh_report["heavy_type_ok"] and veh_report["others_car"]
                        and pce.get("ciezki") == P["heavy_pce"])
else:
    veh_report["ok"] = veh_attr == 0
meta["dist_km"] = ((meta.home_x - meta.work_x) ** 2 + (meta.home_y - meta.work_y) ** 2) ** .5 / 1000
report = {
    "plans": str(path), "sha256": sha, "sha256_rerun": sha2, "deterministic": sha == sha2,
    "persons": len(df) + len(bad_chain), "expected": expected, "bad_chain": bad_chain[:10], "bad_chain_n": len(bad_chain),
    "home_outside_area": int((~df.h.apply(area.contains)).sum()),
    "work_outside_gmina": int((~df[~df.outbound].w.apply(gmina.contains)).sum()),
    "outbound": {"persons": int(df.outbound.sum()), "home_outside_gmina": int((~df[df.outbound].h.apply(gmina.contains)).sum()),
                 "work_inside_gmina": int(df[df.outbound].w.apply(gmina.contains).sum()),
                 "work_source": meta[meta.kind == "outbound"].work_src.str.split("_").str[0].value_counts().to_dict(),
                 "exit_links_used": meta[meta.work_src == "exit"].groupby("work_link").size().sort_values(ascending=False).to_dict(),
                 "excluded_persons_100pct": round(float(excl_out))},
    "jobs_in_kutno_100pct": round(float(jobs_100)), "jobs_total_override": P["jobs_total"], "car_factor": round(car, 4), "variant": P["variant"],
    "return_home_differs": int((~df.same_home).sum()),
    "activities_on_excluded_link_types": bad_snap, "activity_links_missing": missing_link,
    "start_equals_profile_time_ok": start_ok,
    "tlo": tlo_report,
    "ciezkie": heavy_report,
    "vehicles": veh_report,
    "excluded_gminas_gt_max_border_km": {"max_border_km": P["max_border_km"], "gminas": len(excluded),
                                         "persons_100pct": round(float(excluded.n.sum())),
                                         "top": excluded.sort_values("n", ascending=False).head(10)
                                         .apply(lambda r: f"{r.key}: {r.n:.0f} os., {r.border_km:.0f} km", axis=1).tolist()},
    "max_border_km_included": round(float(strata[~strata.excluded].border_km.max()), 1),
    "by_kind": meta.kind.value_counts().to_dict(),
    "home_source": meta.home_src.str.split("_").str[0].value_counts().to_dict(),
    "random_point_homes_keys": sorted(meta[meta.home_src == "random_point"].key.astype(str).unique().tolist()),
    "distinct_work_buildings": int(meta.work_src.nunique()),
    "top5_work_buildings_share": round(meta.work_src.value_counts().head(5).sum() / len(meta), 3),
    "entry_links_used": meta[meta.home_src == "entry"].groupby("home_link").size().sort_values(ascending=False).to_dict(),
    "home_work_crowfly_km_median": {k: round(v, 1) for k, v in meta.groupby("kind").dist_km.median().items()},
    "times": {"departure_profile": P["departure_profile"], "work_max_dur": P["work_max_dur"],
              "departure_by_hour": meta.dep_h.astype(int).value_counts().sort_index().to_dict()},
}
err_csv = path.with_name(path.name.removesuffix(".xml.gz") + "_errands.csv")
err_expected = len(pd.read_csv(err_csv)) if err_csv.exists() else 0
report["errands"] = {"ok_chain": len(ERR[0]), "bad_chain": len(ERR[1]), "expected": err_expected}
report["ok"] = (report["deterministic"] and not bad_chain and not ERR[1] and len(ERR[0]) == err_expected and report["persons"] == expected
                and report["home_outside_area"] == 0 and report["work_outside_gmina"] == 0 and report["return_home_differs"] == 0
                and report["outbound"]["home_outside_gmina"] == 0 and report["outbound"]["work_inside_gmina"] == 0
                and bad_snap == 0 and missing_link == 0 and start_ok
                and tlo_report["ok"] and heavy_report["ok"] and veh_report["ok"])
json.dump(report, open(f"{OUT}/{PHASE}_plans.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)

# --- mapa: domy, praca, wjazdy -------------------------------------------------------------------------
fig = plt.figure(figsize=(16, 8))
ax = fig.add_axes([0.01, 0.05, 0.47, 0.86])
gpd.GeoSeries([area]).boundary.plot(ax=ax, color="0.6", lw=1, ls="--")
gpd.GeoSeries([powiat]).boundary.plot(ax=ax, color="0.7", lw=1.2)
gpd.GeoSeries([gmina]).plot(ax=ax, color="#3b2f1e", edgecolor="#c47f17", lw=1)
o = meta[(meta.kind == "outbound") & (meta.work_src != "exit")]
ax.scatter(o.work_x, o.work_y, s=3, color="#3ddc97", alpha=0.6, label=f"praca wyjeżdżającego w powiecie ({len(o)})")
x = meta[meta.work_src == "exit"].groupby(["work_x", "work_y"]).size().reset_index(name="n")
ax.scatter(x.work_x, x.work_y, s=x.n * 4, color="#3ddc97", marker="s", edgecolor="w", lw=0.5, zorder=5,
           label=f"wyjazd poza powiat ({int(x.n.sum())} os., {len(x)} punktów)")
for kind, col in (("resident", "#2e86ab"), ("commuter", "#7b2cbf")):
    m = meta[(meta.kind == kind) & (meta.home_src != "entry")]
    ax.scatter(m.home_x, m.home_y, s=3, color=col, alpha=0.5, label=f"dom: {'mieszkaniec' if kind == 'resident' else 'przyjeżdżający z powiatu'} ({len(m)})")
e = meta[meta.home_src == "entry"].groupby(["home_x", "home_y"]).size().reset_index(name="n")
ax.scatter(e.home_x, e.home_y, s=e.n * 4, color="#d1495b", edgecolor="w", lw=0.5, zorder=5,
           label=f"wjazd spoza powiatu ({int(e.n.sum())} os., {len(e)} punktów)")
for r in e.itertuples():
    ax.annotate(str(r.n), (r.home_x, r.home_y), xytext=(5, 3), textcoords="offset points", fontsize=7, color="#d1495b")
ax.set_aspect("equal"); ax.set_axis_off(); ax.legend(loc="lower left", fontsize=8)
ax.set_title("domy agentów i punkty wjazdu", fontsize=10)

ax2 = fig.add_axes([0.5, 0.3, 0.3, 0.62])
gpd.GeoSeries([gmina]).plot(ax=ax2, color="#3b2f1e", edgecolor="#c47f17", lw=1)
wc = meta[meta.kind != "outbound"].groupby(["work_x", "work_y"]).size().reset_index(name="n")
ax2.scatter(wc.work_x, wc.work_y, s=wc.n * 2, color="#f18f01", alpha=0.6, edgecolor="w", lw=0.2)
ax2.set_aspect("equal"); ax2.set_axis_off()
ax2.set_title(f"miejsca pracy w Kutnie: {report['distinct_work_buildings']} budynków\n"
              f"(wielkość = liczba agentów; top 5 budynków = {report['top5_work_buildings_share']:.0%})", fontsize=10)

ax3 = fig.add_axes([0.84, 0.62, 0.14, 0.28])
for kind, col in (("resident", "#2e86ab"), ("commuter", "#7b2cbf"), ("outbound", "#3ddc97")):
    ax3.hist(meta[meta.kind == kind].dist_km, bins=range(0, 41), color=col, alpha=0.6, label=kind)
ax3.set_title("odl. dom-praca w linii prostej [km]", fontsize=9); ax3.legend(fontsize=7); ax3.tick_params(labelsize=7)
ax5 = fig.add_axes([0.84, 0.32, 0.14, 0.22])
prof = pd.read_csv(P["departure_profile"])
ax5.hist(meta.dep_h, bins=[h / 4 for h in range(0, 97)], color="#2e86ab", density=True, label="plans")
ax5.stairs(prof.share_pct / 100 / (prof.to_h - prof.from_h), [*prof.from_h, 24], color="#d1495b", label="GBR Rys. 46")
ax5.set_xlim(3, 14); ax5.set_title("wyjazd z domu [h]", fontsize=9); ax5.legend(fontsize=7); ax5.tick_params(labelsize=7)
ax4 = fig.add_axes([0.81, 0.02, 0.14, 0.26]); ax4.set_axis_off()
ax4.text(0, 1, "\n".join([
    f"osoby: {report['persons']} (oczekiwane {expected})",
    f"łańcuch h-car-w-car-h: {'OK' if not bad_chain else len(bad_chain)}",
    f"domy poza obszarem: {report['home_outside_area']}",
    f"praca poza gm. Kutno: {report['work_outside_gmina']}",
    f"sha256 powtórzony: {'OK' if report['deterministic'] else 'RÓŻNY'}",
    f"domy losowe (brak bud.): {report['home_source'].get('random', 0)}",
    f"wyjazd: GBR 2022 Rys. 46",
f"praca: {P['work_max_dur']} (ZAŁOŻENIE)",
]), va="top", fontsize=8, family="monospace")
fig.suptitle(f"{PHASE.upper()} plans {P['sample']:.0%} ({P['variant']}, miejsca pracy {jobs_100:.0f}) | {'ZALICZONA' if report['ok'] else 'NIE ZALICZONA'}", fontsize=12)
fig.savefig(f"{OUT}/{PHASE}_plans.png", dpi=120)
print(json.dumps(report, indent=1, ensure_ascii=False))
sys.exit(0 if report["ok"] else 1)
