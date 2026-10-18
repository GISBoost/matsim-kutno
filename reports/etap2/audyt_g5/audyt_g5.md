# Audyt G5/D20: kod, kalibracja i walidacja (baza R4)

Data: 2026-10-18. Audytor: niezależna sesja Claude (tylko odczyt). Instrukcja: `reports/etap2/audyt_g5/prompt_audytu.md`.
Skrypty kontrolne są w `reports/etap2/audyt_g5/skrypty/` i nie importują kodu z `pipeline/`. Wyniki pośrednie są w `reports/etap2/audyt_g5/wyniki/`.
Nie zmieniałem kodu, configów, `scenarios/`, `data/` ani `output/g5r*`. Nie uruchamiałem MATSim.

## 1. Podsumowanie

Kod generujący plany i macierze jest deterministyczny. Plany R3, plany R4 z plikiem pojazdów oraz macierze O-D R4 (lekkie i ciężkie) odtworzyłem bit w bit. Liczby w raportach R3, R4 i R5 przeliczyłem niezależnie z eventów i zgadzają się co do punktu procentowego.

Kalibracja ma jednak dwa błędy strukturalne, które zmieniają wnioski:
1. **Brakuje stref granicznych na DK92 od zachodu (Kłodawa) i DK60 od północy (Gostynin).** PBF obejmuje tylko łódzkie, więc obie drogi kończą się w sieci ślepo. Licznik DK92 Chodów (91121) może się więc wypełnić tylko ruchem wewnętrznym. Estymacja zrobiła to nierealną parą Dąbrowice ↔ Krośniewice: ok. 18,7 tys. podróży lekkich i 8,2 tys. ciężkich na dobę. Te pary to 30% agentów tła (38% ciężkich) i jeżdżą głównie drogami tertiary i unclassified. To one tworzą „korek pod Krośniewicami” z R4.
2. **Udział klas pojazdów wzięty ze struktury SDRR zastosowano do SDRDR,** choć GPR podaje osobną strukturę dla dni roboczych. W dzień roboczy ciężkich jest na A1 1,42–1,48× więcej. Cel dla ciężkich jest więc zaniżony (A1 −30%), a dla lekkich zawyżony (A1 +13–19%). „A1 99% / 100%” to w dużej mierze efekt złego celu. Przy poprawnym celu R4 daje: lekkie A1 115%, ciężkie A1 68%, ciężkie 5/14 w ±15%.

Do tego `link_delay.py` liczy jako opóźnienie dyskretyzację czasu QSim, do 1 s na każdy link. Opóźnienie R4 to 521, a nie 820 poj.-h próbki. Odcinki walidacyjne (Objazdowa, Bitwy) brały też udział w wyborze wariantów, więc nie są już testem niezależnym.

**Ocena:** bazie R4 można ufać jako technicznie poprawnemu runowi z poprawną mechaniką (pojazdy, PassingQ, skalowanie, liczenie natężeń). Nie można jej ufać jako skalibrowanemu obrazowi ruchu tła i kongestii w powiecie, zwłaszcza wokół Krośniewic i dla ciężkich. Wnioski „A1 i DK w Kutnie zgadzają się z GPR” oraz „R5 przeuczony” są mocniejsze, niż pozwalają dane. **R4 na 3 seedach nie ma sensu przed poprawkami K1 i K2.**

## 2. Ustalenia

Liczba ustaleń: **KRYTYCZNE 2, ISTOTNE 4, DROBNE 9.**

### KRYTYCZNE

#### K1. Brak stref wjazdu i wyjazdu na DK92 (zachód) i DK60 (północ), skutek: fantomowa para Dąbrowice ↔ Krośniewice

- **Gdzie:** `pipeline/plans.py:110-121` (wybór linków granicznych: link musi zaczynać się w pasie 1 km od granicy obszaru sieci) i `pipeline/background_od.py:90-97` (strefy graniczne z `border_links.csv`). Źródło problemu: `data/raw/osm/lodzkie-261015.osm.pbf` obejmuje tylko woj. łódzkie, co odnotowano w `reports/etap1_mvp/f2_network/f2_network.md:49`.
- **Opis:** DK92 kończy się w sieci w węźle 3063418575 (504 407 E, 487 296 N), 2,3 km przed granicą obszaru. Ten węzeł ma jednego sąsiada, czyli to ślepy koniec. DK60 kończy się w węźle 2970197424 (528 777 E, 498 796 N), 1,9 km przed granicą, też z jednym sąsiadem. Żaden z nich nie jest wjazdem ani wyjazdem. Według `docs/research/G5_walidacja.md:86` ruch na DK60 Kutno–Gostynin to SDRR 9 351 (SCPR Lisica), a na DK92 Kłodawa–Krośniewice jest stacja 30025 (karta pobrana, nieanalizowana).
  - Licznik DK92 Chodów 91121 leży między ślepym końcem a Krośniewicami. Tranzytu z zachodu nie da się więc odtworzyć, a estymacja wypełnia 91121 i 91122 parami wewnątrz powiatu.
- **Scenariusz:** największe pary w `scenarios/kutno/demand/background_od_r4_lcv_cap.csv`:
  - lekkie: Dąbrowice (1002032) → Krośniewice-miasto (1002044) 9 454/dobę i w drugą stronę 9 277;
  - ciężkie: 4 399 i 3 805/dobę;
  - to samo w R3 (`background_od_r1_w2_frac_droplocal_cap.csv`: 8 008 + 7 884).
  - Dla porównania: wszystkie podróże tła z celem lub początkiem w Kutnie to 5 621/dobę (lekkie).
  - Trzy strefy Dąbrowice / Krośniewice-m. / Krośniewice-w. mają łącznie 0,92 mln m² obrysów budynków, a Kutno 2,32 mln m².
- **Dowód** (`skrypty/a5_od_routes.py output/g5r4_25pct_s4711 …`, `skrypty/a6_border.py`, `skrypty/a7_road_ends.py`, analiza `output_legs`):
  - para t1002032_1002044: 2 364 agentów w próbce. Tylko 27% przejeżdża przez 91121, a 19% przez 91122. Kilometry: tertiary 50%, unclassified 22%, primary 18%;
  - pary między trzema strefami to 8 391 z 27 629 agentów tła (30,4%), w tym 2 380 z 6 328 ciężkich (37,6%), i 14,4% kilometrów tła;
  - wszystkie linki primary/secondary w pasie 1 km od granicy obszaru są w `border_links.csv`. Nie ma tam żadnej DK92 z zachodu ani DK60 z północy.
- **Wpływ:**
  - Dopasowanie 91121 i 91122 w R3 (101% i 94%) oraz rozjazd w R4 (150% i 191%) są artefaktem tych par, a nie skutkiem „kongestii zmieniającej trasy”, jak opisuje `g5_r4.md`.
  - Największe opóźnienia R4 (drogi 600 poj./h pod Krośniewicami, `g5_r4.md` sekcja Kongestia) powstają z ruchu, którego w rzeczywistości prawdopodobnie nie ma.
  - E1/R5 tylko przesuwa ten sam fantom: w `background_od_r5b2_lcv_cap.csv` największa jest para 1002045 → 1002032 z 5 647/dobę.
  - Pośrednio dotyczy to też 91878 (DK60 Sójki): ruch z Gostynina musi wjechać przez A1 albo powstać w strefach wewnętrznych.
- **Poprawka (bez wdrażania):**
  - Wariant pełny: dociąć sieć z PBF łódzkie + wielkopolskie + mazowieckie, tak żeby drogi dochodziły do granicy obszaru.
  - Wariant minimalny: ręcznie dodać strefy wjazdu i wyjazdu na ślepych końcach DK92 W i DK60 N. Ich natężenie można oprzeć o SCPR 30025 i 14005 Lisica jako dodatkowe liczniki.
  - Dodać kontrolę automatyczną: każda droga DK/DW, która ma w sieci ślepy koniec wewnątrz obszaru, musi mieć strefę.
  - Dodać test sygnałów ostrzegawczych na macierzy: podróże pary względem powierzchni budynków stref oraz udział km pary poza drogami z licznikiem.

#### K2. Struktura rodzajowa SDRR zastosowana do SDRDR, choć GPR podaje strukturę dni roboczych

- **Gdzie:**
  - `pipeline/g5_gpr.py:65-67`: `read_tab("dk_sdrdr.xlsx", 8)` czyta strukturę SDRDR, ale zostawia tylko sumę (`dr[["nr", "sdr"]]`);
  - `pipeline/g5_baseline.py:34-37` i `pipeline/background_od.py:119`: cel = SDRDR × (klasa_SDRR / SDRR) × kierunek.
- **Opis:** `data/raw/g5/gpr2025/dk_sdrdr.xlsx` (tablica 3, kolumny 10–17) ma pełną strukturę rodzajową dnia roboczego. Sumy klas zgadzają się z SDRDR dla wszystkich 14 odcinków DK; sprawdziłem 71410: 10+14 723+40+2 915+704+9 732+79+0 = 28 203. W dzień roboczy udział ciężkich jest dużo wyższy niż średnio w tygodniu.
- **Dowód** (`skrypty/a4_gpr.py`, `wyniki/gpr_recompute.json`): stosunek celu ciężkich SDRDR-struktura / SDRR-struktura wynosi A1 1,42–1,48, DK w Kutnie 1,16–1,28, DK92/91d 1,17–1,45. Cel lekkich z dostawczymi: A1 0,84–0,88, miasto 0,96–0,97.

| model / cel GPR | wg raportu (struktura SDRR) | ze strukturą SDRDR |
|---|---|---|
| R4 lekkie, A1 | 99% | **115%** |
| R4 lekkie, DK w Kutnie | 108% | 112% |
| R4 lekkie, 14 odcinków w ±15% | 10/14 | 9/14 |
| R4 ciężkie, A1 | 100% | **68%** |
| R4 ciężkie, DK w Kutnie | 83% | **70%** |
| R4 ciężkie, 14 odcinków w ±15% | 11/14 | **5/14** |
| R3 lekkie (3 seedy), A1 | 101% | **122%** |

- **Wpływ:**
  - Klasy są źle rozdzielone na wszystkich DK, a w pojazdach umownych obciążenie jest zaniżone. A1, przekrój 71410, liczony moimi wzorami (pce zamiejskie WR-D-13): obecnie 21 103 lekkich + 7 100 ciężkich, czyli ok. 38,9 tys. pcu; ze strukturą SDRDR 17 683 + 10 520, czyli ok. 44,0 tys. pcu (+13%).
  - Tabela braku PCE w `g5_czasy_pce.md` §2.1 (A1 104%, DK w Kutnie 82%) też jest liczona na SDRR. Ze strukturą SDRDR wychodzi: A1 135–195% (mediana ok. 173%), Objazdowa 99%, Bitwy 64%, Sklęczkowska 99%.
  - DW mają tylko SDRR, więc dla nich to zostaje ZAŁOŻENIEM.
- **Poprawka:** w `g5_gpr.py` zapisać strukturę SDRDR (np. kolumny `*_dr`). Cel = suma klas SDRDR × kierunek; dla DW strukturę SDRR oznaczyć jako ZAŁOŻENIE. Potem przeliczyć macierze lekkie i ciężkie oraz tabelę PCE.

### ISTOTNE

#### I1. `link_delay.py` liczy dyskretyzację QSim jako opóźnienie (niespójne z `queues.py`)

- **Gdzie:** `pipeline/link_delay.py:43-46`: `d = t_out − t_in − ff`, a każde d > 0 trafia do sumy. Dla porównania `pipeline/queues.py:93` odejmuje dodatkowo 1 s.
- **Dowód** (`skrypty/a2_delay.py`, `wyniki/delay.log`): w nocy (0–5 h, pusta sieć) 98,8% przejazdów R4 (99,9% w R3) ma dt − ff ∈ [0; 1] s. To czysty efekt kroku 1 s.

| run | `link_delay.py` (raport) | bez artefaktu (−1 s) | najkrótszy czas QSim floor(ff)+1 |
|---|---|---|---|
| R3 s4711 | 359,0 | **149,5** | 154,3 |
| R4 s4711 | 819,6 | **521,3** | 540,3 |
| R5 s4711 | 692,6 | **401,9** | 419,3 |

- **Wpływ:**
  - Artefakt wynosi ok. 0,5 s × liczba przejazdów (R4: 2,03 mln przejazdów, ok. 300 poj.-h) i rośnie z wolumenem ruchu.
  - „Kongestia rośnie 2,3×” (R3 → R4) to w rzeczywistości ok. 3,5×. „R5 −16% vs R4” to ok. −23%.
  - Problem dotyczy też wcześniejszych porównań opóźnień (D18, R1: „41% mniej ruchu → 86% mniej opóźnień”).
  - Wnioski o 0 przepełnionych linków nie zależą od tego (to `queues.py`).
- **Poprawka:** w `link_delay.py` przyjąć ten sam czas swobodny co w `queues.py` (ff + 1 albo floor(ff) + 1) i przeliczyć delay_s* dla D18, R1–R5.

#### I2. Odcinki walidacyjne były używane przy wyborze wariantów, więc test nie jest już niezależny

- **Gdzie:**
  - `docs/research/G5_plan_kalibracji.md:108-120` (W2: Sklęczkowska przeniesiona do dopasowania po wyniku 140–173%);
  - `reports/etap2/g5_kalibracja/g5_r3.md` (tabela wariantów estymacji oceniana po kolumnach Objazdowa/Bitwy, „bez 3 liczników lokalnych” wybrany przy Objazdowej 134% zamiast 194%);
  - `g5_r4_vs_r5_decyzja.md` (wybór R4 na podstawie Objazdowa + Bitwy).
- **Opis:**
  - `CITY` jest spójne w kodzie: `background_od.py:53` i `g5_baseline.py:76` mają [91124, 91866], liczniki lokalne są pominięte przez `drop=` (`k2_od_r4_*.json`: `dropped_counts` [10045, 91892, 91119]).
  - Metodycznie jednak 91124 i 91866 trzykrotnie posłużyły do wyboru: W2, wyłączenie liczników lokalnych i R4 vs R5. Przestały więc być próbą niezależną.
  - Wyłączenie 10045, 91892 i 91119 uzasadniono wynikiem na Objazdowej. Ich niskie wartości (19–52%) raporty tłumaczą „brakiem ruchu lokalnego”, ale K1 pokazuje, że w tym rejonie działa też brak strefy DK92 W.
- **Wpływ na wnioski:** „R5 przeuczony” (decyzja, pkt 1) opiera się na 2 odcinkach i 1 seedzie, przy czym jeden się poprawił (Bitwy 86 → 93%), a drugi pogorszył (Objazdowa 132 → 148%). Różnica 16 pp na Objazdowej jest dużo większa od rozrzutu seedów R3 (0,5% na tym odcinku). Wniosek „R5 gorszy w mieście” jest więc poparty, ale „przeuczenie” to nadinterpretacja. Oba warianty dziedziczą K1 i K2.
- **Poprawka:** opisywać 91124 i 91866 jako „odcinki kontrolne użyte w wyborze wariantu”, nie „walidację poza próbą”. Do niezależnej walidacji przydałyby się dane spoza GPR (SCPR Lisica, 30025, pomiary miejskie z G5 §5.4).

#### I3. Rozrzut „3 seedów” obejmuje tylko losowość MATSim, a nie losowanie planów

- **Gdzie:** `config/kutno.toml:16` (`seed = 4711` dla planów) i `output/r3_runs.sh` (zmienia tylko `global.randomSeed`).
- **Opis:** R3 × 3 seedy ma identyczne plany (`plans_g5r3_25pct.xml.gz`). Rozrzut „mediana 0,6%, maks. 9,9%” potwierdziłem (`a4_gpr.py`: per link 0,6% / 9,9%, maksimum na 10045, gdzie w próbce jest 48–53 pojazdy). Nie obejmuje on jednak:
  - losowania budynków i punktów startu;
  - godzin z profilu;
  - zaokrągleń próbki 25% w parach O-D;
  - 20 punktów na gminę w estymacji.
- **Wpływ:** niepewność wyników 25% jest niedoszacowana. Zdanie „wnioski z 1 seeda się potwierdzają” dotyczy tylko losowości replanningu.
- **Poprawka:** do referencji dodać co najmniej 2 dodatkowe seedy planów (plans.py `seed=`, ewentualnie także seed punktów w `background_od.py`).

#### I4. Wagi a priori stref granicznych liczone per link węzła, a nie per drogę

- **Gdzie:** `pipeline/background_od.py:111-114`: waga = capacity linku / średnia, każdy link graniczny jest osobną strefą.
- **Dowód:** `border_links.csv` złączony z capacity z `output_links` R4 i ref OSM z `wyniki/border_candidates.csv` (`skrypty/a6_border.py`), suma capacity wjazdów per droga i komórka 5 km. Udział wag wjazdów:
  - DK60 płd. (8 linków w jednym węźle przy 520,1 / 475,5 tys.): 28,2%;
  - A1 płd. (3 linki): 23,1%;
  - DK91 płd.-zach. (6 linków): 19,5%;
  - **A1 płn.: 5,8%**;
  - DW573 i DW583: po 1,2%.
- **Opis:** zamiar był „A1 >> DW” (docstring linia 55). Tymczasem DK60 płd. ma a priori 5× wagę A1 płn. tylko dlatego, że węzeł na granicy ma wiele krótkich linków. Liczniki na tych samych drogach (91115, A1) korygują sumy, ale nie strukturę relacji. Według K5 to właśnie struktura relacji decyduje o podziale Objazdowa/Bitwy.
- **Wpływ:** nieznany ilościowo, prawdopodobnie wpływa na Objazdowa/Bitwy. Łamie opisane ZAŁOŻENIE.
- **Poprawka:** zgrupować linki graniczne w strefy per droga (ref + kierunek) i ważyć sumą capacity drogi albo SDR z GPR/SCPR.

### DROBNE

1. **Kierunek na A1 prawdopodobnie zamieniony.**
   - `pipeline/g5_gpr.py:101-102, 128-130`. Punkt GPR „P” leży między jezdniami: jest po lewej stronie obu linków (`skrypty/a3_counters.py`, `wyniki/counters_geom.csv`), a odległości to 7,9 / 10,5 m, 9,9 / 10,2 m i 7,2 / 12,7 m. „Najbliższy” wybiera się więc praktycznie losowo.
   - Na wszystkich trzech odcinkach `udz_prawy` dostała jezdnia północna (azymut 306–334°). Jeśli „prawy” oznacza kierunek rosnącego kilometraża A1 (na południe), to kierunki są zamienione. Konwencji GPR nie potwierdziłem w dokumentacji.
   - Wpływ ≤ 3,5% na kierunek, 0 na sumę odcinka.
2. **Udziały kierunków DK są w GPR, ale model używa 0,5.**
   - `g5_gpr.py:131`. `dk_sdrr.xlsx`, kolumny 18–19 („Kierunkowa struktura… Lewy/Prawy”) zawierają udziały dla wszystkich DK, np. 91119: 46/54, 91866: 52/48, 91122: 53/47.
   - 0,5 jest więc ZAŁOŻENIEM bez potrzeby. Błąd celu na kierunek sięga 7,7%. Najpierw trzeba ustalić konwencję lewy/prawy (pkt 1).
3. **R3 na 3 seedach to 13/14, a nie 12/14.**
   - `g5_r3.md`: odcinek 10044 to 2 772 / 3 261 = 0,85004, czyli mieści się w ±15%.
   - Raport podaje go jako „poza, 85,0%”. Wynik graniczny, bez wpływu na decyzje.
4. **Argument „GEH < 5” w K5 jest za słaby.**
   - Liczony ze średniej godziny doby (`background_od.py:222`). Dla Objazdowej przy udziale godziny szczytu 8% (profil Lisica 15–16: 8,3%) GEH ≈ 6,7. Nie jest to więc argument za akceptacją 129%.
5. **`reports/etap2/g5_kalibracja/pce_wrd13_gpr.csv` nie ma skryptu źródłowego.**
   - `grep pce_wrd13_gpr pipeline/` nic nie znajduje. Pliku nie da się odtworzyć, a liczony jest na strukturze SDRR (zob. K2).
6. **Configi nie zapisują stanu bazy R4.**
   - `scenarios/kutno/config_25pct.xml` wskazuje `plans_25pct.xml.gz`, nie ma `vehiclesSource` ani `vehiclesFile`. Bazę R4 daje tylko linia poleceń (`output/r3_runs.sh`, zmienne `PLANS` i `VEH`). Uruchomienie configu bez `VEH` z planami R4 daje inny model.
   - Sprawdziłem `output_config.xml` R4 i R5: `fromVehiclesData`, właściwy plik pojazdów, `PassingQ`, `flow = storage = 0,25`, `stuckTime` 30, kolejki `queue`. Run jest poprawny, ale nie wynika z configu.
7. **„Udział opóźnień w czasie jazdy 5,6% (R3: 2,7%)” w `g5_r4.md` dotyczy okna 6–9** (`queues.py` domyślnie), a stoi obok opóźnień dobowych. Pomija też przejazdy pierwszego i ostatniego linku.
8. **Źródło prędkości ORS nie jest zarchiwizowane.**
   - Wartości z `g5_gus_czasy.py:24-26` zgadzają się z bieżącym `VehicleFlagEncoder.java` (ORS main, pobrany curl-em do scratchpada w czasie audytu: motorway 100, trunk 85, primary 65, secondary 60, tertiary 50, unclassified 30, residential 30, `MAX_SPEED_FACTOR` 0,9).
   - To jednak nie jest wersja z 2021 r. (macierz GUS), a pliku nie ma w `data/manifest.csv`.
9. **Szczegóły typu `ciezki`.**
   - `plans.py:323`: długość 15 m i szerokość 2,5 m bez źródła. Nie sprawdzałem, czy QSim ich używa; storage liczy się według pce.
   - Klasa „ciężkie” obejmuje ciągniki rolnicze (ustawowo 40 km/h, art. 20 ust. 6 pkt 1), a model daje im 80 km/h. Na licznikach to 0–25 poj./dobę, więc pomijalne.
   - Końce ciężkich w strefach-gminach (`plans.py:245-252`, wszystkie budynki wagą powierzchni):
     - 19,2% w typach mieszkalnych;
     - 31,4% w budynkach gospodarczych (farm_auxiliary, outbuilding, garage, shed);
     - ok. 5% w warehouse/industrial;
     - zliczenie z sjoin końców z `plans_g5r4_25pct_ciezkie.csv`.
   - Raport R4 zna to uproszczenie, ale nie podaje jego skali.

## 3. Sprawdzone i poprawne

| co | dowód |
|---|---|
| Plany R3 odtwarzają się bit w bit obecnym `plans.py` | kopia skryptu z `border_links.csv` przekierowanym do scratchpada (`skrypty/plans_repro_copy.py`), override `background_od=…r1_w2_frac_droplocal_cap.csv heavy_od=`: sha256 d82e3961… = plik z 09:39, czyli sprzed commitu D20 (11:43) |
| Plany R4 i `_vehicles.xml.gz` odtwarzają się bit w bit | sha256 a278f526… i cbf74406… identyczne; `border_links.csv` identyczny (`cmp`) |
| Macierze `background_od_r4_{lcv,heavy}_cap.csv` odtwarzają się bit w bit | `skrypty/background_od_repro_copy.py` (wyjście do scratchpada), `cmp`: LCV_SAME, HEAVY_SAME |
| Konwencja liczenia natężeń jest spójna | estymacja: link startowy pominięty, końcowy liczony (`background_od.py:158`, E1 `[1:]` linia 174); `g5_baseline.py` liczy `entered link`, które nie powstaje na linku startowym. `vol_car` w `output_links` = `left link` (R4: 10 383/10 383 linków), w R1 = entered = left (łańcuchy zamknięte), więc odejmowanie R1 `vol_car` w estymacji jest spójne |
| Brak podwójnego liczenia klas | prefiksy id: r/c/o/t/h, linki bez „_” (`t4918991010000f_1931760520082f_69`). Nogi car R4: h 6 328, t 21 301, c 2 410, r 4 336, o 732 = 35 107 = 3 739·2 + 21 301 + 6 328; 0 stuck (`wyniki/ev_r4.log`) |
| Pojazdy z pliku są faktycznie użyte | `output_vehicles` R4: `ciezki` pce 2,5, `maximumVelocity` 22,2222; 6 328 pojazdów h typu `ciezki`, pozostałe `car`. Mediana prędkości ciężkich na A1: 67,9–80,0 km/h, osobowych 84,9–112 (`ev_r4_s4711.json`, `speeds_on_counters`), więc PassingQ działa |
| Configi 10/25/100% spójne | `diff`: różnią się tylko plikiem planów, katalogiem wyjścia, sampleSize i flow = storage (0,1 / 0,25 / 1,0); strategie dla `person`, `tlo`, `ciezkie`; PassingQ; stuckTime 30 |
| Starty z jezdni A1 wyłącznie z wjazdów granicznych | t\|motorway 5 854 i h\|motorway 1 734 = liczba agentów z `o_link` na 4 wjazdach A1 (`plans_g5r4_25pct_{tlo,ciezkie}.csv`). Pracujący na motorway: tylko c/o z wjazdu (61 + 87) |
| Liczniki leżą na właściwych drogach | ref OSM po origid: A1, 60, 60;92 (Objazdowa), 60 (Bitwy pod Kutnem), 91/91;92, 92, 573, 581, 583, 702; pary linków przeciwne (różnica azymutów 165–180°); żaden licznik nie jest linkiem granicznym (`wyniki/counters_geom.csv`) |
| Rozłączność próby i walidacji w kodzie | `CITY` = [91124, 91866] w `background_od.py:53` i `g5_baseline.py:76`; `dropped_counts` w `k2_od_r4_*.json` |
| Liczby z raportów (niezależnie z eventów, `a4_gpr.py`) | R3 3 seedy: A1 100,6%, DK w Kutnie 104,4%, dopasowanie 96,6%, Objazdowa 128,5%, Bitwy 84,0%. R4 lekkie: A1 99,0%, DK 108%, 10/14, mediana 6,0%, Objazdowa 132,1%, Bitwy 86,3%. R4 ciężkie: 99,6% / 82,6% / 11/14 / 70% / 77%. R5 lekkie: 12/14, mediana 0,4%, Objazdowa 147,6%. Suma Objazdowa + Bitwy: R4 110,7%, R5 122,0%. Zgodne z raportami (różnice ≤ 1 pp na 4 odcinkach z końcami aktywności na liczniku: raport R3 liczył `vol_car`) |
| Rozrzut seedów R3 | per link mediana 0,6%, maksimum 9,9% (10045), zgodnie z raportem |
| Skala próbki tła | 21 301 = round(85 203 × 0,25); 6 328 = 25 312 × 0,25; largest remainder w `plans.py:259-262`; × 1/0,25 w analizach |
| Profil Lisica | `config/hourly_profile_lisica2025.csv`: sumy 99,999 / 100,011; porównanie z renderem s. 9 `st_14005.pdf` (niebieska krzywa „Dni robocze”, lekkie: szczyt 15–16 8,3%; ciężkie: płaska, 6,8% o 9–10). Kolumny nie są zamienione |
| K1-1 | 0,64 × (1 − 0,073) = 0,5933 = `car_factor` w walidatorze; stosowane jednakowo do r/c/o (`plans.py:151`) |
| Limit 80 km/h w trasach estymacji ciężkich | `background_od.py:63, 78` (`min(freespeed, VMAX)`) |
| Pracujący w celu tła | R1 (FIFO, bez tła) vs pracujący w R4: różnice na odcinkach −204 … +188 poj./dobę (`wyniki/ev_r*`). Pomijalne poza Krośniewicami |
| WR-D-13-01 tab. 4.3.1 s. 28 | tekst PDF: osobowe 1,0/1,0/1,0; dostawcze 1,5/1,5/1,0; ciężarowe 2,5/2,5/2,0; z przyczepami 3,0/3,0/2,5; autobusy 2,5/2,5/2,0; ciągniki 3,0. Zgodne z ZRODLA |
| PoRD art. 20 | ust. 3 pkt 2a: 80 km/h (autostrada, ekspresowa, dwujezdniowa 2+2), 2b: 70 km/h; ust. 1: 50; ust. 2: 20. Zgodne z D13/D20 |
| Manifest | sha256 i rozmiar zgodne dla wszystkich 29 plików G5 (`gpr2025`, `scpr2025`, `lit`, `pce`), PBF łódzkie, BREC REJ, macierz dostępności GUS |
| Ruch tła wewnątrz Kutna wykluczony | `background_od.py:147`; brak par 1002011 → 1002011 w macierzach R4 |
| Nogi o zerowej długości | car z tym samym linkiem startu i końca: R4 r 2, h 1; nogi < 100 m: r 3, h 1 (`output_legs`) |

## 4. Niesprawdzone

- **Testu MATSim (2 iteracje) nie uruchamiałem.** Wszystkie ustalenia wynikają z istniejących outputów i przeliczeń offline.
- **Konwencja GDDKiA „kierunek lewy/prawy”** dla A1 i DK. Nie znalazłem definicji w `rd.txt`, więc pkt D1 i D2 są warunkowe.
- **Skill do przeglądu kodu.** Dostępne skille (`code-review`) przeglądają diff, a audytowany kod jest zacommitowany i nie ma diffu. Przegląd zrobiłem ręcznie, a każde ustalenie potwierdziłem poleceniem.
- **Kod Javy** (`CreateKutnoNetwork`, prędkości D13, zawrotki) oraz poprawność sieci poza rejonami liczników. Wizualnej kontroli w QGIS nie robiłem.
- **Ilościowy wpływ I4** (wagi a priori) i rozrzut wyników przy innym seedzie planów (I3). Wymagałoby to nowych estymacji i runów.
- **SCPR 30025 Dzięgielewo (DK92 W)** i rzeczywisty SDR na DK60 N: nie analizowałem karty `st_30025.pdf`.
- **`g5_gus_czasy_r3.py`, `turn_violations.py`, `demand.py`, `digitize_gbr.py`:** przeczytane pobieżnie albo wcale. Liczb „0,87; 0,76 → 0,84” nie przeliczałem.
- **Czy długość i szerokość typu pojazdu wpływają na QSim w MATSim 2026.**
- **Seedy R4/R5:** jest tylko po 1 seedzie, więc rozrzutu dla runów z ciężkimi nie da się ocenić.

## 5. Rekomendowana kolejność poprawek przed R4 × 3 seedy

1. **K1:** strefy na DK92 W i DK60 N (sieć z sąsiednich województw albo strefy na ślepych końcach) i kontrola ślepych końców DK/DW. Jeśli dostępne, SCPR 30025 i 14005 jako dodatkowe cele.
2. **K2:** struktura rodzajowa SDRDR w `g5_gpr.py`, nowe cele lekkich i ciężkich, przeliczenie tabeli PCE (ze skryptem zamiast samego CSV, D5).
3. **I4:** strefy graniczne zgrupowane per droga, wagi a priori per droga.
4. Nowa estymacja lekkich i ciężkich, potem kontrola sygnałów ostrzegawczych macierzy przed runem:
   - top pary względem powierzchni budynków stref;
   - udział km tła na drogach bez licznika;
   - udział końców ciężkich w budynkach mieszkalnych i gospodarczych.
5. **I1:** poprawka `link_delay.py`, przeliczenie opóźnień R3–R5 (i D18) dla porównań.
6. Run 25% na 1 seedzie, porównanie z GPR (struktura SDRDR). Odcinki 91124 i 91866 opisać jako kontrolne, nie niezależne (I2).
7. Dopiero potem referencja: 3 seedy MATSim **plus** 2 seedy planów (I3).
8. Drobne (D1–D9) przy okazji. D6 (config zapisuje plany i pojazdy bazy) przed runem referencyjnym, żeby baza była odtwarzalna z samego configu.
