"""G5: punkty GPR 2025 (GDDKiA) w obszarze sieci -> przypisanie do linków sieci Kutna.

Wejście: data/raw/g5/gpr2025/*.xlsx (wykazy + SDRR/SDRDR/SDRL), scenarios/kutno/network.xml.gz
Wyjście: reports/g5_walidacja/gpr_punkty.csv (jeden wiersz na punkt),
         reports/g5_walidacja/gpr_linki.csv (jeden wiersz na link: natężenie na kierunek)
Współrzędne bierzemy z lat/lon (WGS84 -> EPSG:2180, oś E,N), nie z kolumn X/Y GDDKiA (podpisane odwrotnie).
"""
import gzip
import math
import warnings
import xml.etree.ElementTree as ET

import geopandas as gpd
import pandas as pd
from pyproj import Transformer
from shapely.geometry import LineString, Point

warnings.filterwarnings("ignore")
RAW = "data/raw/g5/gpr2025/"
OUT = "reports/g5_walidacja/"
BBOX = (497056 - 5000, 467370 - 5000, 558819 + 5000, 507985 + 5000)  # z węzłów sieci + 5 km
tr = Transformer.from_crs(4326, 2180, always_xy=True)
STRUCT = ["motocykle", "osobowe", "mikrobusy", "lekkie_ciez", "ciez_bez_przycz", "ciez_z_przycz", "autobusy", "ciagniki"]


def num(x):
    return pd.to_numeric(str(x).replace(",", ".") if pd.notna(x) else x, errors="coerce")


def read_tab(f, first_val_col, ncols_struct=8):
    d = pd.read_excel(RAW + f, header=None, skiprows=10)
    out = pd.DataFrame({"nr": d[0].astype(str).str.strip()})
    v = d[list(range(first_val_col, first_val_col + 1 + ncols_struct))].map(num)
    out["sdr"] = v[first_val_col]
    for i, c in enumerate(STRUCT):
        out[c] = v[first_val_col + 1 + i]
    return out, d


def points():
    rows = []
    # drogi krajowe
    w = pd.read_excel(RAW + "dk_wykaz.xlsx", header=None, skiprows=11)
    for _, r in w.iterrows():
        base = dict(klasa="DK", nr=str(r[0]).strip(), droga=str(r[1]), nazwa=r[6], typ=r[7], miejsc=r[10], woj=r[30])
        for side, (la, lo) in (("P", (11, 12)), ("L", (15, 16))):
            if pd.notna(r[la]) and pd.notna(r[lo]):
                rows.append({**base, "strona": side, "lat": num(r[la]), "lon": num(r[lo])})
    # drogi wojewódzkie
    w = pd.read_excel(RAW + "dw_wykaz.xlsx", header=None, skiprows=11)
    for _, r in w.iterrows():
        rows.append(dict(klasa="DW", nr=str(r[0]).strip(), droga=str(r[1]), nazwa=r[5], typ=r[6], miejsc=r[12], woj=r[13],
                         strona="P", lat=num(r[8]), lon=num(r[9])))
    p = pd.DataFrame(rows).dropna(subset=["lat", "lon"])
    x, y = tr.transform(p.lon.values, p.lat.values)
    p["x"], p["y"] = x, y
    p = p[(p.x > BBOX[0]) & (p.x < BBOX[2]) & (p.y > BBOX[1]) & (p.y < BBOX[3])].copy()
    return p


def values(p):
    dk, dkraw = read_tab("dk_sdrr.xlsx", 8)
    dk["udz_lewy"], dk["udz_prawy"] = dkraw[17].map(num), dkraw[18].map(num)
    dw, _ = read_tab("dw_sdrr.xlsx", 7)
    dr, _ = read_tab("dk_sdrdr.xlsx", 8)
    dl, _ = read_tab("dk_sdrl.xlsx", 8)
    dr = dr[["nr", "sdr"]].rename(columns={"sdr": "sdrdr"})
    dl = dl[["nr", "sdr"]].rename(columns={"sdr": "sdrl"})
    dk = dk.merge(dr, on="nr", how="left").merge(dl, on="nr", how="left")
    sdrr = pd.concat([dk.assign(klasa="DK"), dw.assign(klasa="DW")])
    return p.merge(sdrr, on=["klasa", "nr"], how="left")


def links():
    rows, nodes = [], {}
    for _, e in ET.iterparse(gzip.open("scenarios/kutno/network.xml.gz")):
        if e.tag == "node":
            nodes[e.get("id")] = (float(e.get("x")), float(e.get("y")))
        elif e.tag == "link":
            a = {k.get("name"): k.text for k in e.iter("attribute")}
            rows.append(dict(link=e.get("id"), frm=e.get("from"), to=e.get("to"), hw=a.get("type"), origid=a.get("origid")))
            e.clear()
    g = pd.DataFrame(rows)
    g["geometry"] = [LineString([nodes[f], nodes[t]]) for f, t in zip(g.frm, g.to)]
    g["bearing"] = [math.degrees(math.atan2(l.coords[-1][0] - l.coords[0][0], l.coords[-1][1] - l.coords[0][1])) % 360 for l in g.geometry]
    return gpd.GeoDataFrame(g, crs=2180)


# klasa drogi GPR -> dozwolone typy OSM linku. ZAŁOŻENIE: A1 = motorway, S/DK = trunk/primary, DW = primary/secondary/tertiary.
def allowed(droga, klasa):
    d = droga.upper()
    if d.startswith("A") or d.startswith("S"):
        return {"motorway", "trunk"}
    return {"trunk", "primary", "secondary"} if klasa == "DK" else {"primary", "secondary", "tertiary", "trunk"}


def assign(p, g, maxd=60):
    out = []
    for _, r in p.iterrows():
        dual = r.klasa == "DK" and r.droga.upper()[0] in "AS"
        if dual and r.strona == "L":
            continue  # jezdnie A/S: punkt P -> najbliższa jezdnia, partner = jezdnia w przeciwnym kierunku
        pt = Point(r.x, r.y)
        c = g[g["hw"].isin(allowed(r.droga, r.klasa))].copy()
        c["d"] = c.geometry.distance(pt)
        c = c[c.d <= (150 if dual else maxd)].sort_values("d")
        if c.empty:
            continue
        l1 = c.iloc[0]
        found = [(l1, "najblizszy")]
        opp = c[((c.bearing - l1.bearing + 180) % 360 - 180).abs() > 150]
        opp = opp[opp.d <= (150 if dual else l1.d + 40)]
        if len(opp):
            found.append((opp.iloc[0], "przeciwny"))
        for l, how in found:
            out.append(dict(nr=r.nr, klasa=r.klasa, strona="P", link=l.link, osm_type=l.hw, origid=l.origid, dist_m=round(l.d, 1), rola=how))
    return pd.DataFrame(out)


if __name__ == "__main__":
    p = values(points())
    g = links()
    a = assign(p, g)
    p.drop(columns=["x", "y"]).assign(E=p.x.round(0), N=p.y.round(0)).to_csv(OUT + "gpr_punkty.csv", index=False)
    m = a.merge(p, on=["nr", "klasa", "strona"])
    # natężenie na kierunek: DK dwujezdniowe = udział kierunku z tabeli; reszta 50/50 (ZAŁOŻENIE, DW bez udziałów)
    def share(r):
        if r.klasa == "DK" and r.droga.upper()[0] in "AS":
            s = r.udz_prawy if r.rola == "najblizszy" else r.udz_lewy
            return s if pd.notna(s) else 0.5
        return 0.5
    m["udzial_kier"] = m.apply(share, axis=1)
    m["sdrr_kier"] = m.sdr * m.udzial_kier
    m["sdrdr_kier"] = m.sdrdr * m.udzial_kier
    m["droga"] = m.droga.str.replace("\n", "/")
    m["lekkie_osob"] = m.osobowe + m.mikrobusy + m.motocykle  # to porównujemy z autami modelu
    m["ciez_udzial"] = (m.lekkie_ciez + m.ciez_bez_przycz + m.ciez_z_przycz + m.autobusy) / m.sdr
    m.to_csv(OUT + "gpr_linki.csv", index=False)
    print(len(p), "punktów (strona P/L) w obszarze;", m.nr.nunique(), "odcinków przypisanych;", len(m), "wierszy link")
    print(p.groupby(["klasa", "woj"]).size())
