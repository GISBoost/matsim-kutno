# Krok 4: nowa estymacja O-D (K1 + K2 + I4) i sygnały ostrzegawcze macierzy

Data: 2026-10-18. Plan: `plan_poprawek.md` krok 4. Decyzja: D21 (pkt „krok 4”).

## Przewidywanie (przed zmianą)

- R1 na nowych planach: zmiana tylko na drogach z nowymi wjazdami (DK60 N, DK92 W), 105 osób próbki, setki poj./dobę.
- Estymacja z nowym R1 ≈ diagnostyka z kroku 3 (różnice < 1%), bo R1 zmienia się lokalnie.
- Sygnały ostrzegawcze: macierze R4 flagowane (fantom K1), R6 bez fantomu. Końce ciężkich w budynkach mieszkalnych i gospodarczych ok. 50%, jak w audycie, dopóki nie zmienię losowania.

## 1. R1 po K1 (sam popyt pracujących)

- Plany `scenarios/kutno/plans_g5r1k1_25pct.xml.gz` (`plans.py … background_od= heavy_od=`): walidator ok, sha256 powtarzalny (`k4_r1/validate.log`). Względem starych planów R1 różni się 105 osób (90 przyjeżdżających i 15 wyjeżdżających), a różnica dotyczy wyłącznie linku granicznego.
- Runy `output/g5r1k1_25pct_s{4711,1,2}` (100 iteracji, config 25% z PassingQ; stary R1 miał FIFO, przy samych osobowych bez znaczenia): **7 478 nóg car na każdym seedzie, 0 stuck** (`k4_r1/check_s*.json`).
- Porównanie z R1 starym (średnie z 3 seedów, `k4_r1/r1*_light.csv`): A1 71410 568 → 72 i nowy odcinek 11104 0 → 512. Dojeżdżający z Gostynina wjeżdżają teraz DK60 N zamiast A1. Pozostałe odcinki zmieniają się o −127 … +129 poj./dobę (Objazdowa +129, bo ruch z DK60 N jedzie przez miasto). **Zgodnie z przewidywaniem.**

## 2. Estymacja R6

`background_od.py 30 r6_{lcv,heavy}_gpr output/g5r1k1_25pct_s{4711,1,2} cls=… drop=10045,91892,91119`: cel SDRDR (K2), 11 + 11 stref per droga (I4), cel 11104. Macierze `scenarios/kutno/demand/background_od_r6_{lcv,heavy}_gpr.csv`, raporty `k4_od/k2_od_r6_*.json|png`. Macierze R4 bez zmian.

| | R4 lekkie (cel SDRR) | **R6 lekkie** | R4 ciężkie (cel SDRR) | **R6 ciężkie** |
|---|---|---|---|---|
| podróże/dobę (100%) | 85 203 | **65 905** | 25 312 | **22 990** |
| tranzyt granica–granica | 21 594 | 14 863 | 6 290 | 9 762 |
| granica–gmina | 33 654 | 42 677 | 8 292 | 11 939 |
| gmina–gmina | 29 954 | 8 364 | 10 730 | 1 290 |
| odcinki dopasowania (trasy swobodne) | 100% | 100% (RMSE 0,8) | 100% | 100% (RMSE 6,1) |
| Objazdowa 91124 (kontrolny) | 130% | 123% | 68% | 29% |
| Bitwy pod Kutnem 91866 (kontrolny) | 91% | 75% | 72% | 78% |

R6 lekkie różnią się od diagnostyki kroku 3 o 6 podróży/dobę. **Zgodnie z przewidywaniem.**

## 3. Sygnały ostrzegawcze (`pipeline/od_warnings.py`, kod 1 przy przekroczeniu)

Progi (ZAŁOŻENIA, uzasadnienie w docstringu):
- S1: gęstość podróży gminy ≤ 10× Kutna. Kutno ma niską gęstość, bo jego ruch zewnętrzny to modelowane dojazdy; zwykłe gminy mają 0,4–7×.
- S2: ≤ 35% km tła po drogach bez licznika. To sygnał słaby, bo pracujący w R1 mają 58% (dojazd od drzwi do drzwi, `c4_local_km.json`).
- S3: ≤ 25% końców ciężkich w budynkach mieszkalnych i gospodarczych.
- S4: ≤ 500 podróży/dobę w parach Dąbrowice / Krośniewice-m. / Krośniewice-w.

| | S1 maks. gęstość / Kutno | S2 km po drogach bez licznika | S3 końce ciężkich mieszk. + gosp. | S4 trójka | flagi |
|---|---|---|---|---|---|
| R4 lekkie | **44,8×** (Dąbrowice) | **40,2%** | – | **24 041** | S1, S2, S4 |
| R4 ciężkie | **73,4×** (Krośniewice-m.) | **39,7%** | **50,8%** | **9 523** | S1–S4 |
| **R6 lekkie** | 5,1× (Krośniewice-m.) | 30,5% | – | 142 | brak |
| **R6 ciężkie** | 4,8× (Krośniewice-m.) | 19,4% | **0,0%** | 0 | brak |

- Top 10 par z powierzchnią budynków obu stref: `k4_od/warn_r6.json` (`top10`). Największa para lekkich to gm. wiejska Kutno (986 tys. m² budynków) ↔ DK60 płd., ok. 4 000 podróży/dobę w każdą stronę. Kutno-miasto ma 2 322 tys. m².
- Kontrola S2 na eventach R4 (`skrypty/c4_local_km.py`): tło lekkie 41,6%, ciężkie 39,1%. Wartości z tras swobodnych w `od_warnings.py` to 40,2% i 39,7%, więc metody są zgodne.
- Kontrola niezależna inwariantów (`skrypty/c4_od_check.py`, `c4_od_check.log`). R6: 0 par Kutno → Kutno, strefy graniczne tylko jako linki zewnętrzne łańcuchów, 0 zawracań, trójka i gęstość zgodne z `od_warnings.py`. Macierz R4 jako kontrola negatywna: 577 wierszy ze starymi strefami (link = strefa), 2 zawracania, trójka 24 041. Kontrola działa.

## 4. Ciężkie: końce w budynkach pracy (audyt D9)

- Przy losowaniu z wszystkich budynków gminy (stan R4) 54% końców ciężkich wypada w budynkach mieszkalnych i gospodarczych (`od_warnings.py` z wag losowania; sjoin końców z planów R4 `skrypty/c4_heavy_ends.py`: 19,2% + 31,2%, czyli audyt).
- **ZAŁOŻENIE (`config/kutno.toml heavy_ends = "work"`):** końce ciężkich w gminach powiatu (także w Kutnie) to budynki pracy, tak jak `work_any` w `plans.py`: typy `work_buildings`, amenity/shop/office oraz `building=yes` w landuse przemysłowym, handlowym i usługowym. Losowanie odbywa się wagą powierzchni. Tak samo w `background_od.py cls=heavy` (20 punktów na gminę i waga a priori gminy = powierzchnia budynków pracy). Wariant bazowy `heavy_ends = "all"` zostaje do porównań.
- Po zmianie końce ciężkich w planach (sjoin): 99,9% w budynkach „innych”, czyli magazyny 29%, przemysłowe 21%, `yes` w strefach 20%, szkoły 7%, handel 7%.
- Regresja: przy `heavy_ends=all` plany wychodzą bit w bit jak przed zmianą (sha256 9dc096af…), a przy `work` tło lekkie się nie zmienia (cmp `_tlo.csv`).
- Wpływ na odcinki kontrolne (ciężkie, trasy swobodne): `all` daje Objazdową 72% i Bitwy 61%, `work` daje 29% i 78%. Mechanizm sprawdziłem w parach przez Objazdową. W `all` ciężkie z A1 płn. jechały do domów i budynków gospodarczych Krzyżanowa (658/dobę przez Objazdową). W `work` ciężkie do Kutna kończą w strefach przemysłowych przy węźle A1 Kutno Wsch. i nie jadą Objazdową. Objazdowa dla ciężkich jest więc niedoszacowana. Nie stroję pod nią wariantu (I2: odcinki kontrolne nie mogą wybierać wariantu). Run R6 pokaże, czy kongestia to zmienia.

## 5. Wariant odrzucony: cel GPR na strefach granicznych

Kontrola dodatkowa: podróże przez strefę względem natężenia GPR jej odcinka × 0,5. W R6 bilans stref jest zły na drogach, gdzie odcinek GPR strefy nie ma licznika w sieci: DK91 płn.-zach. **4,3×**, DK91 płd.-zach. **0,16×**, DK92 wsch. 0,29×, DW573 0,47×. DK60 płd. ma 2,2×, mimo że ma licznik 91115. Licznik jest spełniony, ale część par omija go zjazdami do wsi gm. wiejskiej Kutno.

Sprawdziłem dwa warianty z celem na linku strefy (`background_od.py zone_cnt=1`):
- **wszystkie strefy:** cel strefy DK60 płd. jest sprzeczny z licznikiem 91115 na tym samym odcinku (strefa 126%, licznik 65%, RMSE 187). Powstaje nowy fantom: para gmin 1002082 → 1002052 z 6 370 podróży/dobę;
- **tylko strefy bez licznika w sieci** (5 dróg): bilans stref 100%, ale S2 38%, S4 616, gmina 1002082 ma 9,4× gęstości Kutna, gmina–gmina 8 364 → 20 145, Objazdowa 162% (`warn_r6var_zones.*`). Ruch dopisany do stref DK91 i DK92 wsch. nie ma licznika na trasie i rozchodzi się drogami lokalnymi.

Oba odrzucone, bo przekraczają progi sygnałów ostrzegawczych. To zadanie, do którego te sygnały powstały. Zła równowaga stref DK91 i DK92 wsch. zostaje jako **znana rozbieżność** R6. Rozwiązaniem byłaby sieć z sąsiednich województw (wariant pełny K1), w której liczniki 71306 i 91103 leżą wewnątrz sieci, albo poprawna struktura relacji na DK91d (liczniki 91892 i 91119 są dziś wyłączone z dopasowania, D19). Kod wariantu zostaje jako opcja (domyślnie wyłączona).

## Testy

- R1: 3 × `check_events.py --expect-car-legs 7478` ok, 0 stuck.
- Walidator planów R1 ok, sha256 powtarzalny.
- Macierze R6: odtworzone bit w bit drugim uruchomieniem; `od_warnings.py` kod 0; `c4_od_check.py` ok.
- Plany z `heavy_ends`: regresja `all` bit w bit, `work` bez zmiany tła lekkiego.
- Przegląd diffu: ręcznie (`plans.py`, `background_od.py`, `od_warnings.py`, `kutno.toml`); bez ustaleń poza poprawionym błędem `dtype` w S2 (pusta trasa).

## ZAŁOŻENIA dodane

1. Progi S1–S4 (wyżej).
2. `heavy_ends = "work"`: końce ciężkich w budynkach pracy.
3. Bilans stref bez celu (wariant z celem odrzucony), rozbieżność DK91/DK92 wsch. opisana.
