"""G5: brakujący ruch dostawczy i ciężki w pojazdach umownych (PCE WR-D-13-01 tab. 4.3.1) na punktach GPR 2025.

Wejście: scenarios/kutno/validation/gpr_punkty.csv (g5_gpr.py). Wyjście: reports/etap2/g5_kalibracja/pce_wrd13_gpr.csv.
Uruchom: uv run python pipeline/g5_pce.py [sdrr]
  domyślnie struktura dnia roboczego (SDRDR; DW mają tylko SDRR, ZAŁOŻENIE), `sdrr` = stara wersja tabeli (audyt G5/K2).
"""
import sys

import pandas as pd

SDRR = "sdrr" in sys.argv[1:]
CITY = [91124, 91866, 91869]  # DK w Kutnie (jak g5_baseline.py): Objazdowa, Bitwy pod Kutnem, Sklęczkowska
# WR-D-13-01 (2023) tab. 4.3.1: miejski (z sygnalizacją i bez mają te same wartości dla tych kategorii) / zamiejski
PCE = {"miejski": dict(lekkie_ciez=1.5, ciez_bez_przycz=2.5, ciez_z_przycz=3.0, autobusy=2.5, ciagniki=3.0),
       "zamiejski": dict(lekkie_ciez=1.0, ciez_bez_przycz=2.0, ciez_z_przycz=2.5, autobusy=2.0, ciagniki=3.0)}
HEAVY = ["ciez_bez_przycz", "ciez_z_przycz", "autobusy", "ciagniki"]

p = pd.read_csv("scenarios/kutno/validation/gpr_punkty.csv", dtype={"nr": str}).drop_duplicates(["klasa", "nr"])
c = (lambda k: p[k]) if SDRR else (lambda k: p[k + "_dr"])
tot = p.sdr if SDRR else p.sdrdr.fillna(p.sdr)
lek = c("osobowe") + c("mikrobusy") + c("motocykle")
p["obszar"] = p.nr.astype(int).isin(CITY).map({True: "miejski", False: "zamiejski"})
pcu = sum(c(k) * p.obszar.map({o: v[k] for o, v in PCE.items()}) for k in PCE["miejski"])
t = pd.DataFrame({"nr": p.nr, "droga": p.droga, "obszar": p.obszar, "sdr": tot, "lekkie": lek,
                  "dostawcze_pct": (100 * c("lekkie_ciez") / tot).round(1),
                  "ciezkie_pct": (100 * sum(c(k) for k in HEAVY) / tot).round(1),
                  "brak_poj_pct_lekkich": (100 * (tot - lek) / lek).round().astype(int),
                  "brak_pcu_pct_lekkich": (100 * pcu / lek).round().astype(int)})
t.to_csv("reports/etap2/g5_kalibracja/pce_wrd13_gpr" + ("_sdrr" if SDRR else "") + ".csv", index=False, lineterminator="\n")
d = t.droga.str.replace("\n", "/")
grp = {"A1": d == "A1", "DK poza miastem": p.klasa.eq("DK") & (d != "A1") & (t.obszar == "zamiejski"),
       "DK w Kutnie": t.obszar == "miejski", "DW": p.klasa.eq("DW")}
for k, m in grp.items():
    print(f"{k}: mediana {t[m].brak_pcu_pct_lekkich.median():.0f}% (min {t[m].brak_pcu_pct_lekkich.min()}, max {t[m].brak_pcu_pct_lekkich.max()}, n={m.sum()})")
print(t[t.obszar == "miejski"][["nr", "brak_pcu_pct_lekkich"]].to_string(index=False))
