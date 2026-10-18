"""Kontrola macierzy O-D (krok 4) bez importu z pipeline/: inwarianty i dwie liczby sygnałów ostrzegawczych liczone inaczej.

Użycie: uv run python -W ignore reports/etap2/audyt_g5/poprawki/skrypty/c4_od_check.py <macierz.csv> [...]
- brak par Kutno -> Kutno; strefy graniczne = linki zewnętrzne łańcuchów (border_zones.csv), wjazd tylko jako o, wyjazd tylko jako d;
- brak zawracania: wjazd i wyjazd z tej samej drogi (droga z border_zones.csv; grupowanie sprawdzone niezależnie w c3);
- S4: pary między 1002032 / 1002044 / 1002045; S1: gęstość gminy względem Kutna z sjoin budynków do BREC.
"""
import sys

import geopandas as gpd
import pandas as pd

bz = pd.read_csv("scenarios/kutno/demand/border_zones.csv")
road = dict(zip(bz.zone, bz.road))
ent, ext = set(bz.zone[bz.kind == "entry"]), set(bz.zone[bz.kind == "exit"])
rej = gpd.read_file("data/raw/brec/rej_pl/SU_BREC_2021_REJ.shp", columns=["GMINA"])
gm = rej[rej.GMINA.str.startswith("1002")].dissolve(by="GMINA").reset_index()
b = gpd.read_file("scenarios/kutno/osm/features.gpkg", layer="buildings")
b["a"] = b.area
b["geometry"] = b.centroid
area = gpd.sjoin(b, gm[["GMINA", "geometry"]], predicate="within").groupby("GMINA").a.sum()
for f in sys.argv[1:]:
    od = pd.read_csv(f, dtype={"o": str, "d": str})
    bad_kind = od[((od.o_kind == "entry") & ~od.o.isin(ent)) | ((od.d_kind == "exit") & ~od.d.isin(ext))
                  | ((od.o_kind == "gmina") & ~od.o.str.startswith("1002")) | (od.o_kind == "exit") | (od.d_kind == "entry")]
    kk = od[(od.o == "1002011") & (od.d == "1002011")]
    uturn = od[(od.o_kind == "entry") & (od.d_kind == "exit") & (od.o.map(road) == od.d.map(road))]
    trio = od[od.o.isin({"1002032", "1002044", "1002045"}) & od.d.isin({"1002032", "1002044", "1002045"})].trips_day.sum()
    g = pd.concat([od[od.o_kind == "gmina"].groupby("o").trips_day.sum(), od[od.d_kind == "gmina"].groupby("d").trips_day.sum()],
                  axis=1).fillna(0).sum(axis=1)
    dens = g / area.reindex(g.index)
    ok = bad_kind.empty and kk.empty and uturn.empty
    print(f, "podróże", round(od.trips_day.sum()), "| złe strefy", len(bad_kind), "| Kutno->Kutno", len(kk), "| zawracanie", len(uturn),
          "| trio", round(trio), "| maks. gęstość/Kutno", round((dens / dens["1002011"]).max(), 2), (dens / dens["1002011"]).idxmax(),
          "| OK" if ok else "| BŁĄD")
    assert ok
