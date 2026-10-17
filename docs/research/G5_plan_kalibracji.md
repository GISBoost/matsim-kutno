# G5: plan kalibracji względem GPR 2025 (do decyzji przed runami)

Data: 2026-10-17. Punkt wyjścia: run referencyjny D18 (25%, 3 seedy). Dane: `docs/research/G5_walidacja.md` (GPR 2025, SCPR, literatura ruchu tła). Bazowa tabela: `reports/g5_kalibracja/g5_0_baseline.{csv,json,png}` (`pipeline/g5_baseline.py`).

## 0. Punkt startowy: model vs GPR (pojazdy lekkie, SDRDR, doba, sumy po odcinku)

| grupa odcinków | GPR | model | model / GPR |
|---|---|---|---|
| A1 (3 odcinki) | 64 161 | 4 689 | **7%** |
| DK w Kutnie: Objazdowa 91124, Bitwy pod Kutnem 91866, Sklęczkowska 91869 | 23 665 | 13 235 | **56%** (65%, 28%, 71%) |
| pozostałe DK (Krośniewice, DK92 za A1, DK60 Leszno i Sójki) | 34 217 | 5 543 | 16% |
| DW (573, 581, 583, 702) | 16 092 | 1 112 | 7% |

Skąd ruch modelu na tych odcinkach:
- Sklęczkowska: głównie przyjeżdżający (2 180–2 460 / kierunek), wyjeżdżający ok. 500, mieszkańcy 72–328.
- A1: przyjeżdżający i wyjeżdżający z dalszych gmin. Mieszkańców prawie nie ma.

**Czego model nie ma, a GPR liczy:**
1. Tranzyt (A1, DK92, DK60).
2. Ruch między innymi gminami powiatu (Żychlin, Krośniewice), który w ogóle nie dotyczy Kutna.
3. Podróże inne niż praca (zakupy, szkoła, sprawy, ruch służbowy).
4. Ruch dostawczy: GPR liczy go osobno, a w celu „lekkie” go nie ma.

**Co model ma za dużo:**
- 100% dojazdów do pracy autem. Dla dom–praca w miastach 30–190 tys. auto ma 61–67% (Bochnia, Radom; G4).
- Praca z domu: 7,3% całkiem i 5,5% w trybie mieszanym (łódzkie, GUS Mobilność 2024, G4).

Dlatego 56% na DK w mieście nie znaczy „brakuje 44% ruchu”. Część brakującego ruchu (tranzyt, inne cele) jest przykryta nadmiarem dojazdów.

**Zasada:** najpierw popyt (kto jedzie, ile i kiedy), dopiero potem sieć. Dobowe liczniki nie pozwolą skalibrować capacity ani dynamiki QSim. Dopasowanie capacity do GPR przy niepełnym popycie ukryłoby brak popytu w parametrach sieci.

## 1. Kroki i warianty

### K1. Dojazdy do pracy: udział auta i obecność w pracy (bez trybów, tylko skala popytu car)

| wariant | co robi | uwagi |
|---|---|---|
| K1-0 | bez zmian (100% auto, 100% obecnych) | dzisiejszy stan, górna granica |
| **K1-1** | losowe pominięcie agentów: udział auta 0,64 (środek przedziału 61–67%, Bochnia/Radom) × obecność (1 − 0,073 praca z domu) ≈ 0,59 | ZAŁOŻENIE: źródła z innych miast. Mieszkańcy, przyjeżdżający i wyjeżdżający jednakowo. Jednocześnie zawęża MVP (nie wszyscy pracujący jadą autem), więc wymaga decyzji D. |
| K1-2 | jak K1-1, ale z przedziałem 0,61 i 0,67 jako warianty wrażliwości | +2 zestawy runów |

Przy K1-1 model na DK w mieście spadnie z ok. 56% do ok. 33% GPR, więc luka do zamknięcia tłem będzie większa.

### K2. Ruch tła (subpopulacja `tlo`, poza zmianą celu i trybu, tylko `ReRoute`)

| wariant | strefy | jak dobrać O-D | uwagi |
|---|---|---|---|
| K2-0 | brak tła | – | dzisiaj |
| K2-1 | tylko wjazdy i wyjazdy na granicy sieci (31 + 31 linków D9/D17) | estymacja macierzy O-D z liczników: macierz a priori (grawitacja z natężeń GPR na wjazdach), trasy swobodne, korekta proporcjonalna do 19 odcinków | Tranzyt A1/DK. Nie odda ruchu Żychlin–Krośniewice, bo ten nie przekracza granicy sieci. |
| **K2-2** | K2-1 + centroidy pozostałych gmin powiatu (budynki jak dla domów przyjeżdżających) | jak K2-1 | Obejmuje też ruch lokalny w powiecie. Rekomendacja (podejście A z G5 §3 rozszerzone o strefy wewnętrzne). |
| +H | K2-x + ciężarowe z GPR jako osobny typ pojazdu z PCE | jak wyżej | **PCE wymaga źródła** (wytyczne GDDKiA / HBS), a nie mam go jeszcze. Ciężkie to 24–37% na DK, więc bez nich kongestia jest zaniżona. |

**Test uczciwości:** O-D tła dopasowuję tylko do odcinków podmiejskich (A1, DK i DW poza miastem). Trzy odcinki w mieście (91124, 91866, 91869) zostają **do walidacji poza próbą**. Wtedy dopasowanie w mieście jest testem, a nie wynikiem dopasowania.
**Cel:** SDRDR (dzień roboczy). Dla DW jest tylko SDRR, oznaczone w tabeli.
**Skala:** liczba agentów tła × sampleSize, jak populacja.

### K3. Profil godzinowy tła

| wariant | źródło | uwagi |
|---|---|---|
| K3-1 | podział GPR 6–18 / 18–22 / 22–6 (72,5 / 16,2 / 11,3%), równomiernie w przedziałach | Gotowe, ale bez szczytu. Zaniża tło w godzinie szczytu. |
| **K3-2** | krzywe godzinowe dnia roboczego ze stacji SCPR 14005 Lisica (DK60c, 13 km), digitalizacja jak `digitize_gbr.py` | Jedyne godzinowe dane drogowe w okolicy (rekomendacja G5). Osobno lekkie i ciężkie. |

### K4. Walidacja (po każdym kroku)

- **Doba:** model / GPR i GEH na 19 odcinkach. Osobno odcinki dopasowania i 3 odcinki miejskie (poza próbą).
- **Szczyt:** natężenie modelu w godzinie 7–8 vs GPR SDRDR × udział godziny szczytu z profilu Lisica (dopiero po K3-2).
- **Kongestia:** suma opóźnień, przepełnione linki (`queues.py`), mediany czasów. Bez danych o czasach przejazdu w szczycie to tylko diagnostyka, nie cel.

### K5. Wrażliwość sieci (nie kalibracja: dobowe liczniki tego nie rozstrzygną)

| wariant | co | uwagi |
|---|---|---|
| S-0 | queue, stuckTime 30, capacity domyślne Supersonic (tertiary 600, primary 1 500 poj./h/pas) | D18 |
| S-1 | kinematicWaves (jak Berlin, Kelheim) | Test D18: +56% opóźnień przy tych samych trasach |
| S-2 | capacity per klasa z innego źródła | **Wymaga wskazania źródła** (np. polskie wytyczne przepustowości skrzyżowań lub HBS). Bez tego nie ruszam. |

Prawdziwa kalibracja sieci wymaga danych, których nie ma publicznie: pomiarów godzinowych na ulicach miasta (zapytanie do UM/ZDP/GDDKiA Rejon Kutno, G5 §5.4) albo czasów przejazdu w szczycie.

## 2. Proponowana kolejność i koszt

1. **Bez MATSim:** digitalizacja Lisica (K3-2) i budowa popytu tła K2-2 (estymacja O-D na trasach swobodnych). Kontrola: natężenia tła na odcinkach dopasowania ≈ GPR − model.
2. **Run R1 = D18 + K1-1** (25% × 3 seedy, ok. 14 min).
3. **Run R2 = R1 + K2-2 + K3-2**, lekkie. Tło w skali 25% to szacunkowo 5–8 tys. agentów (populacja 6,3 tys.). Run potrwa 30–40 min, zgłoszę przed startem.
4. **Wrażliwość na R2:** S-1 (kinematicWaves), ewentualnie +H i S-2, gdy będą źródła PCE i capacity.
5. Raport `reports/g5_kalibracja/`, decyzje D19+.

## 3. Decyzje do podjęcia

1. **K1:** czy skalować dojazdy autem (K1-1, 0,59) mimo że to zmiana założenia MVP „wszyscy jadą autem”? Alternatywa: K1-0 i świadomość, że model zawyża dojazdy.
2. **K2:** wariant tła (rekomendacja K2-2) i czy ciężarowe (+H) teraz, czy po znalezieniu źródła PCE.
3. **K3:** digitalizacja Lisica (rekomendacja) czy podział 3-okresowy.
4. **Walidacja poza próbą:** zgoda, żeby 3 odcinki miejskie nie brały udziału w dopasowaniu.
5. **Dane miejskie:** czy przygotować wnioski o pomiary (UM Kutno, ZDP, GDDKiA Rejon Kutno). Wysyła użytkownik.

## 4. Stan po krokach bez MATSim (2026-10-17, D19)

- **K1-1:** `car_share = 0.64` i `work_from_home = 0.073` w `config/kutno.toml`, plans.py skaluje popyt o 0,593. Plany 25%: 3 739 osób, walidacja ok.
- **Run R1** (D18 + K1-1, 25% × 3 seedy, `reports/g5_kalibracja/r1/`): 7 478 nóg car, 0 stuck.
  - Opóźnienia 106–113 poj.-h próbki wobec 735–854 w D18. 41% mniej ruchu daje o 86% mniej opóźnień, więc kongestia jest silnie nieliniowa.
  - Model / GPR: A1 3%, DK w mieście 30%, pozostałe DK 8%, DW 4%.
- **K3-2:** `pipeline/digitize_lisica.py` → `config/hourly_profile_lisica2025.csv`. Lekkie i ciężkie, dzień roboczy, sumy 100,0%. Udział godzin 6–18 dla lekkich to 77,7%, szczyt 15–16: 8,3%.
- **K2-2:** `pipeline/background_od.py` (estymacja O-D z 16 odcinków poza miastem):
  - 13 gmin powiatu, 31 wjazdów i 31 wyjazdów; ok. 62–64 tys. podróży tła na dobę w 100%;
  - odcinki dopasowania wychodzą 1,00 poza kilkoma: 91121 = 0, 10045 i 91122 = 0,5, 91119 = 1,5;
  - **walidacja poza próbą nie przechodzi:**

| wariant a priori | Objazdowa 91124 | Bitwy pod Kutnem 91866 | Sklęczkowska 91869 |
|---|---|---|---|
| płaska (τ = ∞), na D18 | 207% | 87% | 201% |
| grawitacja τ = 15 / 30 / 60 min, na D18 | 166 / 184 / 193% | 90–92% | 207–214% |
| grawitacja τ = 30, na R1 | 168% | 93% | 173% |
| τ = 30 + waga wjazdu = capacity linku, na R1 | 155% | 94% | 140% |

**Przyczyna:** luka na A1 (ok. 22 tys. poj. lekkich na kierunek) dzieli się między tranzyt A1 i relacje A1 ↔ Kutno przez węzeł Kutno Wsch. i Sklęczkowską. Podobnie luka na DK92 do Krośniewic (91123) dzieli się na relacje Krośniewice ↔ Kutno i Krośniewice ↔ dalej przez Kutno. Żaden licznik poza miastem nie rozróżnia tych relacji, a wtedy ruch przez miasto wynika tylko z założeń a priori.

**Opcje (decyzja):**
- **W1:** dopasowanie do wszystkich 19 odcinków. Miasto pasuje z konstrukcji, ale nie zostaje nic do walidacji.
- **W2 (rekomendacja):** Sklęczkowska (91869) wchodzi do dopasowania, bo jako jedyna wiąże ruch z węzła A1 Kutno Wsch. Objazdowa (91124) i Bitwy pod Kutnem (91866) zostają do walidacji poza próbą.
- **W3:** zostać przy 3 odcinkach poza próbą i szukać innego a priori (np. udział tranzytu na A1 z innego źródła, którego teraz nie mam).

## 5. W2 (decyzja użytkownika, 2026-10-17) i plan na następną sesję

Sklęczkowska 91869 wchodzi do dopasowania. Wariant: τ = 30 min, waga wjazdu = capacity linku. Plik `scenarios/kutno/demand/background_od_r1_w2_cap.csv`, raport `reports/g5_kalibracja/k2_od_r1_w2_cap.{json,png}`.
- Walidacja poza próbą na trasach swobodnych, przed MATSim: **Objazdowa 91124: 141% GPR** (bez W2: 155%), **Bitwy pod Kutnem 91866: 94%**.
- Niedopasowane odcinki: 91121 DK92 Chodów–Krośniewice = 0, bo żadna trasa O-D nie przechodzi przez ten link. 10045 DW583 Żychlin i 91122 Krośniewice ≈ 0,5, bo to ruch wewnątrz gmin, którego strefa-gmina z jednym węzłem nie oddaje. 91119 = 1,5.

**Do zrobienia (start jutro, przed pierwszą symulacją z tłem):**
1. plans.py: agenci tła z `background_od_r1_w2_cap.csv`.
   - Subpopulacja `tlo`, łańcuch `tlo_start` – car – `tlo_end`.
   - Wjazd i wyjazd na linkach granicznych, w gminie losowy budynek wg powierzchni.
   - Godzina z `hourly_profile_lisica2025.csv` (lekkie).
   - Liczba = trips_day × sample (największe reszty).
2. Configi: `activityParams` dla `tlo_start`/`tlo_end` (ZAŁOŻENIE w komentarzu) oraz strategie ChangeExpBeta i ReRoute dla `subpopulation=tlo`.
3. `validate_plans.py`: osobny test dla `tlo` (liczba = suma OD × próbka, łańcuch, linki istnieją).
4. Test 2 iteracji, potem **R2 = R1 + tło, 25%, 1 seed** (runy pośrednie na 1 seedzie, 3 seedy tylko dla wyników referencyjnych). W próbce 25% to ok. 15,5 tys. agentów tła plus 3,7 tys. pracujących, więc run będzie kilka razy dłuższy. Czas trzeba oszacować po teście.
5. Porównanie R2 z GPR (`g5_baseline.py`): Objazdowa i Bitwy pod Kutnem poza próbą, do tego opóźnienia i kolejki (`queues.py`).
