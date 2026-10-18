# G5: walidacja czasów przejazdu (GUS) i źródło PCE dla ciężarowych

Data: 2026-10-18. Bez zmian w modelu. Wejście: R3 25% × 3 seedy (`output/g5r3_25pct_s{4711,1,2}`).

## 1. Czasy przejazdu: run R3 vs macierz dostępności GUS 2021

### 1.1 Dojazdy z gmin powiatu do Kutna w runie (z kongestią)

Skrypt `pipeline/g5_gus_czasy_r3.py`, wynik w `czasy/r3_vs_gus.{csv,json,png}`.
- Dane: nogi car przyjeżdżających z domem w budynku gminy powiatu, rano (dom → praca). Z 3 seedów to 2 691 nóg z 12 gmin.
- Czas swobodny liczę dla tej samej pary linków po `length/freespeed`, tak jak MATSim liczy nogę car.

| miara | wartość |
|---|---|
| kongestia (czas w runie / czas swobodny), mediana nóg | **1,05** (p90 1,13; wyjazdy 6–9: 1,06) |
| suma czasów w runie / suma czasów swobodnych | 1,07 |
| mediana per gmina: run / GUS | **0,87** |
| mediana per gmina: czas swobodny nóg / GUS | 0,81 |
| czas swobodny nóg (budynek → budynek) / czas swobodny centroid → centroid | 0,98 |

- Kongestia wydłuża dojazdy z powiatu średnio o 5–7%. Wynik zgadza się z opóźnieniem dobowym R3 (359–367 poj.-h próbki, 0 przepełnionych linków).
- Rozkład domów i miejsc pracy zamiast centroidów prawie nie zmienia czasu (0,98).
- Z kongestią model nadal jest szybszy od GUS o ok. 13%.
- Gminy z największą różnicą to Żychlin (obszar wiejski 0,55, miasto 0,69), Bedlno (0,60), Oporów (0,72) i Krośniewice wieś (0,74). Wszystkie mają dojazd drogami lokalnymi.

### 1.2 Skąd różnica: model prędkości ORS

GUS liczył macierz w openrouteservice (ORS) na danych OSM. Prędkości profilu car odczytałem z kodu ORS (`VehicleFlagEncoder.java`, docs/ZRODLA.md §5):
- **bez tagu `maxspeed`:** prędkość domyślna klasy, m.in. primary 65, secondary 60, tertiary 50, **unclassified 30**, residential 30 km/h;
- **z tagiem:** 0,9 × maxspeed.

W naszej sieci (D13) droga zamiejska bez tagu dostaje 90 × 0,8 = **72 km/h niezależnie od klasy**. Dotyczy to 2 069 km `unclassified` i 574 km `tertiary`.

Te same trasy przeliczone prędkościami ORS (`pipeline/g5_gus_czasy.py ors <run>`, wynik w `reports/g5_walidacja/gus_vs_siec_ors.{csv,png}`):

| | D13 (model) | prędkości ORS w naszej sieci |
|---|---|---|
| mediana czas sieci / GUS (29 gmin) | 0,76 | **0,84** |
| kwartyle | 0,71–0,82 | 0,81–0,94 |

- Prędkości domyślne dróg bez tagu tłumaczą ok. 1/3 różnicy.
- Reszta to prawdopodobnie kary ORS (nawierzchnia, residential z gęstymi węzłami, ronda), których nie odtwarzałem, oraz inne wersje OSM i ORS (2021).
- Z prędkościami ORS rozrzut rośnie (Piątek 1,49, Gostynin 1,26), bo trasy uciekają z dróg 30 km/h na objazdy.
- **Wniosek:** GUS/ORS to model, a nie pomiar. Nie da się nim wyznaczyć prędkości. Pokazuje tylko, że nasze 72 km/h na drogach lokalnych bez tagu to górna granica i że czasy nie są zaniżone. Do rozstrzygnięcia potrzebny byłby niezależny pomiar czasów (np. przejazdy próbne albo dane FCD), którego nie mamy.

## 2. Źródło PCE dla ciężarowych

**Znalezione: WR-D-13-01 „Wytyczne wykonywania analiz i prognoz ruchu drogowego” (2023), tab. 4.3.1** (`data/raw/g5/pce/`, manifest).

| kategoria GPR | miejski, bez sygnalizacji | miejski, z sygnalizacją | zamiejski |
|---|---|---|---|
| osobowe, mikrobusy | 1,0 | 1,0 | 1,0 |
| dostawcze ≤ 3,5 t | 1,5 | 1,5 | 1,0 |
| ciężarowe > 3,5 t bez przyczep | 2,5 | 2,5 | 2,0 |
| ciężarowe z przyczepami, ciągniki z naczepami | 3,0 | 3,0 | 2,5 |
| autobusy | 2,5 | 2,5 | 2,0 |
| ciągniki rolnicze | 3,0 | 3,0 | 3,0 |

- Kategorie odpowiadają strukturze rodzajowej GPR, więc liczniki przeliczają się bez dodatkowych założeń.
- Kontrola: instrukcja GDDKiA z 2025 r. (zarządzenie 18, drogi zamiejskie jednojezdniowe) liczy przepustowość w pojazdach rzeczywistych. Udział ciężkich wpływa w niej tylko przez pochylenie, więc na płaskim terenie efekt wynosi ok. 1%. Dotyczy jednak odcinków między węzłami. W modelu kongestia powstaje na linkach miejskich i węzłach, a dla nich WR-D-13 daje 2,5–3,0.

### 2.1 Skala brakującego ruchu (GPR 2025, `pce_wrd13_gpr.csv`)

Model ma dziś tylko lekkie: osobowe, mikrobusy i motocykle. Brakuje dostawczych (5–15% SDR) i ciężkich (> 3,5 t, autobusy, ciągniki).

| grupa odcinków | brakujący ruch w pojazdach umownych, w % ruchu lekkich (mediana) |
|---|---|
| A1 | **104%** |
| DK poza miastem | 76% |
| DK w Kutnie (Objazdowa, Bitwy pod Kutnem, Sklęczkowska) | **82%** (Objazdowa 82%, Bitwy 51%, Sklęczkowska 83%) |
| DW | 35% |

W pojazdach umownych obciążenie DK w mieście jest więc o ok. 50–80% większe niż w modelu. Przy obecnych 0 przepełnionych linkach to największy znany brak w kongestii.

## 3. Warianty dla ciężarowych (do decyzji, nic nie wdrożone)

| wariant | co | koszt | uwagi |
|---|---|---|---|
| **P1 (rekomendacja)** | (a) dostawcze dołączone do celu tła lekkiego (pce 1,0); (b) ciężkie jako druga subpopulacja `ciezkie`: osobna macierz O-D estymowana tą samą metodą R3 z liczników ciężkich GPR, profil godzinowy Lisica `heavy_pct` (już zdigitalizowany), typ pojazdu z `pce` = 2,5 (ZAŁOŻENIE: zamiejski z przyczepą = miejski bez przyczepy; na A1 i DK dominują zestawy z naczepą), wrażliwość 3,0 | ODME ok. 10 min, run R4 25% 1 seed ok. 25 min | Pełny obraz kongestii. Nowe ZAŁOŻENIE: jedna wartość pce zamiast podziału miasto/poza miastem (ograniczenie MATSim). Prędkość maksymalna ciężarowych wymaga źródła (limity z Prawa o ruchu drogowym, do sprawdzenia przed wdrożeniem). |
| P2 | tylko dostawcze do tła lekkiego | ODME + run ok. 30 min | Zamyka ok. 8% SDR, ciężkie zostają luką. Mała zmiana. |
| P3 | ciężkie bez agentów: capacity linków A1/DK × (lekkie / pojazdy umowne z GPR) | bez nowej macierzy | Statyczne (bez profilu godzinowego), działa tylko na linkach z licznikiem, a w mieście, gdzie są węzły, licznik jest tylko na 3 odcinkach. Odradzam. |

Czasy przejazdu (§1) nie wymagają decyzji. Proponuję zostawić prędkości D13 jako górną granicę, z wnioskiem zapisanym w G5.
