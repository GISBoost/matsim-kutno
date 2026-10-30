"""D32 (krok 4C): zakupy i usługi mieszkańców Kutna jako osobne wyjścia home -> shop|service -> home (kierowca, auto).

Generator osób i lokalizacji; linki i XML robi plans.py (errands = "on"). Własny generator losowy (errand_seed), więc reszta planów
nie zmienia się (errands = "off" odtwarza R9.2 bajt w bajt).
Liczba wyjść: stawka na osobę 6+ z GUS Mobilność 2024 (łódzkie, tabl. 10 dom-zakupy w centrach handlowych, dom-inne zakupy, dom-usługi, / osoby 6+
z tabl. 4) x populacja Kutna 6+ (population_kutno.csv, NSP 2021) x udział jazd autem jako kierowca (errand_car_share, ZAŁOŻENIE: Radom
fakultatywne 53,2% x 0,797 kierowców) x próbka. Uczestnicy: osoby 18+ z license=yes i carAvail != never, waga = odsetek osób robiących
zakupy i usługi w grupie wieku (GUS Budżet czasu 2023, tabl. 2). Cel: budynki BDOT10k w gm. Kutno, waga = obrys. Godzina: GBR 2022 rys. 46 dom-inne.
D34 (errand_dest = "osm"): cele zakupów c i s = sklepy OSM (osm_poi.py), c = OSM_C, s = pozostałe shop=*; punkt = budynek BDOT ze sklepem
(do errand_poi_m), waga = liczba sklepów typu w budynku. Usługi u bez zmian (BDOT). "bdot" odtwarza R9.3 bajt w bajt.
"""
import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio

TYPES = {  # kod, typ aktywności, klucz stawki GUS, funkcje przeważające BDOT10k celu
    "c": ("shop", "errand_gus_shop_cc", ["centrum handlowe", "hipermarket lub supermarket"]),
    "s": ("shop", "errand_gus_shop", ["dom towarowy lub handlowy", "obiekt handlowo-usługowy"]),
    "u": ("service", "errand_gus_service", ["bank", "inny urząd administracji publicznej", "urząd miasta", "urząd gminy",
                                            "starostwo powiatowe", "placówka operatora pocztowego"]),
}
OSM_C = ["supermarket", "mall", "department_store"]  # D34: typ c wg OSM


def osm_pool(code, bd, P):
    """D34: cele c|s ze sklepów OSM; każdy sklep -> najbliższy budynek BDOT do errand_poi_m (inaczej punkt sklepu), waga = liczba sklepów."""
    sh = pd.read_csv(P["errand_shops"], keep_default_na=False)
    sh = sh[sh.shop.isin(OSM_C) == (code == "c")]
    pt = gpd.GeoDataFrame(sh, geometry=gpd.points_from_xy(sh.x, sh.y), crs=bd.crs)
    j = gpd.sjoin_nearest(pt, bd[["PRZEWAZAJACAFUNKCJABUDYNKU", "pt", "geometry"]], how="left", max_distance=P["errand_poi_m"])
    j = j[~j.index.duplicated()]  # remis odległości: pierwszy budynek
    hit = j.index_right.notna()
    j["key"] = np.where(hit, "b" + j.index_right.astype("Int64").astype(str), "p" + j.osm_type + j.osm_id.astype(str))
    j["pt"] = [bd.pt.loc[int(i)] if h else g for i, h, g in zip(j.index_right.fillna(-1), hit, j.geometry)]
    j["PRZEWAZAJACAFUNKCJABUDYNKU"] = np.where(hit, "osm:" + j.shop + " / " + j.PRZEWAZAJACAFUNKCJABUDYNKU.fillna(""), "osm:" + j.shop)
    g = j.groupby("key", sort=True)
    return pd.DataFrame(dict(PRZEWAZAJACAFUNKCJABUDYNKU=g.PRZEWAZAJACAFUNKCJABUDYNKU.first(), pt=g.pt.first(),
                             area_m2=g.size().astype(float))).reset_index(drop=True)  # area_m2 = waga (liczba sklepów)


def draw(P, homes_in, gmina):
    """DataFrame wyjść: person, atrybuty osoby, współrzędne domu i celu, typ, start_s. homes_in(obwod) -> budynki mieszkalne (kolumny pt, area_m2)."""
    rng = np.random.default_rng(P["errand_seed"])
    pop = pd.read_csv("scenarios/kutno/demand/population_kutno.csv")
    n6 = int((pop.age >= 6).sum())
    bd = pyogrio.read_dataframe(P["home_bdot"], encoding="utf-8", columns=["KATEGORIAISTNIENIA", "PRZEWAZAJACAFUNKCJABUDYNKU"])
    bd = bd[(bd.KATEGORIAISTNIENIA == "eksploatowany")].copy()
    bd["pt"] = bd.geometry.representative_point()
    bd = bd[bd.pt.within(gmina)].copy()
    bd["area_m2"] = bd.geometry.area
    part = pd.read_csv(P["errand_participation"])
    w_age = lambda a: part.share_pct[(part.age_from <= a) & (a <= part.age_to)].iloc[0] if a >= 15 else 0.0
    el = pop[(pop.age >= 18) & pop.license & (pop.carAvail != "never")].copy()
    el = el[el.obwod.map(lambda o: len(homes_in(int(o))) > 0)].copy()  # obwód bez budynku mieszkalnego pomijamy (bez losowania punktu)
    el["w"] = el.age.map(w_age)
    prof = pd.read_csv(P["errand_departure"])
    prof = prof[prof.to_h - prof.from_h == 1]  # tylko przedziały godzinne (bez 0-5 i 20-24)
    rows = []
    for code, (atype, rate_key, funcs) in TYPES.items():
        if P.get("errand_dest", "bdot") == "osm" and code in "cs":
            pool = osm_pool(code, bd, P)
        else:
            pool = bd[bd.PRZEWAZAJACAFUNKCJABUDYNKU.isin(funcs)].reset_index(drop=True)
        assert len(pool), (code, funcs)
        target = round(P[rate_key] / P["errand_gus_pop6"] * n6 * P["errand_car_share"] * P["sample"])
        pick = rng.choice(len(el), size=target, replace=False, p=(el.w / el.w.sum()).to_numpy())
        who = el.iloc[pick]
        dst = pool.iloc[rng.choice(len(pool), size=target, p=(pool.area_m2 / pool.area_m2.sum()).to_numpy())]
        k = rng.choice(len(prof), size=target, p=(prof.share_pct / prof.share_pct.sum()).to_numpy())
        start = (prof.from_h.to_numpy()[k] * 3600 + rng.uniform(0, 3600, target)).astype(int)
        for j, (r, d) in enumerate(zip(who.itertuples(), dst.itertuples())):
            c = homes_in(int(r.obwod))
            h = c.iloc[rng.choice(len(c), p=(c.area_m2 / c.area_m2.sum()).to_numpy())]
            rows.append(dict(person=f"e{code}{j}", etype=atype, src=d.PRZEWAZAJACAFUNKCJABUDYNKU,
                             obwod=r.obwod, age=r.age, sex=r.sex, license="yes", carAvail=r.carAvail, home_x=h.pt.x, home_y=h.pt.y, hid=h.hid,
                             dst_x=d.pt.x, dst_y=d.pt.y, start_s=int(start[j])))
    return pd.DataFrame(rows)
