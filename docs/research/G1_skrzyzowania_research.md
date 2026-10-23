# Skrzyżowania, pierwszeństwo i sygnalizacja w MATSim: research i rekomendacje

Data: 2026-10-23. Zakres: tylko research, bez zmian w modelu. Powód: po G1 (`reports/etap3/g1_skrzyzowania/g1.md`) wiadomo, że zakazy skrętu nie zmieniają wyników, a `f_E` i `f_F` dalej zawierają opóźnienia węzłów. Pytanie: **jak MATSim modeluje skrzyżowania i co z tym zrobić w Kutnie**.

Źródła czytane w całości: kurs TU Berlin (transkrypcje wykładów i seminariów, slajdy), kod i konfiguracje `matsim-berlin` i `matsim-kelheim` (klony, commity niżej), model Wiednia (`references/`), rozdział 12 książki MATSim (Grether, Thunig 2016), Thunig i in. 2019, Rakow i in. 2024 (Berlin), Nippold i in. 2021, Nagel i in. 1997 (TRANSIMS), dokumentacja SUMO o skrzyżowaniach, klasy jara MATSim 2026.0 (`javap`). Źródła czytane tylko na poziomie streszczenia są oznaczone „(abstrakt)”. Lista i status w `docs/ZRODLA.md`.

## 1. Wniosek w czterech zdaniach

1. **QSim nie modeluje skrzyżowania.** Węzeł jest punktem bez wymiaru i bez czasu. Przepustowość daje wyłącznie link wylotowy z kolejki, a pierwszeństwo, konflikty i opóźnienie węzła nie istnieją, chyba że dołożymy contrib `signals`.
2. **Twórcy MATSim robią to inaczej, niż my.** W Open Berlin v6 opóźnienia skrzyżowań i pierwszeństwo są wstawiane **do parametrów linków** (przepustowość i prędkość swobodna wyznaczane osobno dla trzech typów węzła: sygnalizacja, „prawej ręki”, z pierwszeństwem), z modelu uczonego na symulacji SUMO. W Kelheim i Wiedniu nie ma nic poza domyślną przepustowością na pas i sygnalizacji nie ma w żadnym z trzech modeli. Nagel mówi to wprost: dla pojedynczych skrzyżowań „użyj Visum albo SUMO”, MATSim to poziom planistyczny.
3. **Nasz zabieg (`f_E`, `f_F` jako „prędkość z opóźnieniem węzła”) jest standardem w mezoskopowych modelach** (Rakow, Kreuschner, Nagel 2024: „free speed każdego linku musi uwzględniać opóźnienia od świateł i znaków nawet bez zatorów”). Problemem nie jest sam pomysł, tylko to, że mamy **jeden współczynnik na klasę drogi**, a opóźnienie zależy od typu węzła, liczby pasów, wlotów i hierarchii dróg.
4. **Sygnalizacji świetlnej w MATSim nie opłaca się dodawać bez planów sygnalizacji** (Nagel: „sygnalizacja jest łatwa do wstawienia, ale potrzeba dobrych programów sygnalizacji, a trudno je zdobyć”). Dla Kutna (ok. 30 skrzyżowań z sygnałami) brak źródła danych. Rekomendacja w sekcji 6: najpierw klasyfikacja węzłów i przepustowość wlotów wg typu węzła, jako jawny eksperyment z wariantami.

## 2. Jak MATSim 2026.0 działa w węźle (kurs + kod)

### 2.1 Co mówi kurs TU Berlin

- Wykład 1: kolejka na końcu linku obsługiwana z „stawką” (capacity). Przykład Nagela: 1800 poj./h to jeden pojazd na 2 s; **światło czerwone przez połowę czasu daje 900 poj./h**, czyli sygnalizację można przybliżyć obniżeniem przepustowości o udział czerwonego. Model kolejki jest jak kolejki w sieciach komputerowych: bufor wejściowy i wyjściowy, a przepełnienie powoduje zator cofający się po sieci (spillback). „Kinematic wave” to ten sam model plus „dziury” wędrujące wstecz.
- Wykład 1: „**to jest symulacja planistyczna**; jeśli chcesz patrzeć na pojedyncze skrzyżowania, lepiej użyć VISUM albo SUMO; odpowiednik to statyczne przydziały regionalne”. Wielopasmowy ruch jest słabo odwzorowany, „wszyscy są uwięzieni za najwolniejszym”.
- Wykład 2: zdarzenia `link leave` i `link enter` rozdziela „przejazd przez skrzyżowanie”, który **nie zajmuje czasu**, ale „mógłby w przyszłych wersjach”. Link ma length, capacity, freespeed, number of lanes; freespeed to „coś jak limit prędkości, bo ludzie jeżdżą szybciej”.
- Wykład 3: przepustowość „fizycznie niemożliwa” (1 pas, 3600 poj./h) jest automatycznie naprawiana przez dodanie pasów. Pas ma ok. 2000 poj./h, „ze światłem jeszcze mniej”. W planowaniu transportu „capacity jest ważniejsze niż geometria”.
- Wykład 4: `flowCapacityFactor` i `storageCapacityFactor` razem z próbką; `stuckTime` rozwiązuje gridlock (zawracanie na pełnym linku), pojazd jest wciskany po czasie; kinematic waves „jedyne ustawienie, które ma sens”.
- Wykład 6: sygnalizacja i lanes „stosunkowo łatwo wstawić, ale potrzeba dobrych programów sygnalizacji i są trudne do zdobycia”. Wykład 9: pojazd transportu publicznego ma PCE, bo „zużywa więcej przepustowości na skrzyżowaniach”.
- Seminarium 10: „jesteśmy symulacją mezoskopową, mamy system kolejkowy, ale nie coś tak szczegółowego jak SUMO czy VISUM”.

### 2.2 Co robi kod QSim (jar 2026.0, `javap`, zweryfikowane)

- **Domyślne przejście przez węzeł:** `QSimConfigGroup.nodeTransitionLogic` = `emptyBufferAfterBufferRandomDistribution_dontBlockNode`. Wlot do węzła wybierany losowo, a wagą jest przepustowość wlotu (`QNodeImpl.updatePriorities` czyta `Link.getCapacity`). Dostępne warianty: `…_nodeBlockedWhenSingleOutlinkFull`, `moveVehByVehRandomDistribution_*`, `moveVehByVehDeterministicPriorities_nodeBlockedWhenSingleOutlinkFull`. Nasze configi tego nie ustawiają (domyślne).
- **Pierwszeństwo w QSim: nie ma.** Są tylko wagi wlotów oparte o przepustowość. Droga główna i podporządkowana o tej samej przepustowości są równoważne.
- **`TurnAcceptanceLogic`** (interfejs w QSim): domyślnie `DefaultTurnAcceptanceLogic`; `SignalTurnAcceptanceLogic` dochodzi przy contrib `signals`.
- **`DisallowedNextLinks`:** żadna klasa `qnetsimengine` ich nie czyta, routery Speedy tak. To ustalenie z G1 (zakazy obowiązują przy wyznaczaniu tras, nie w QSim).
- **Link przez „Passing queue”, `linkDynamics`:** używamy PassingQ (D20).

### 2.3 Sygnalizacja i pierwszeństwo: contrib `signals` (jar 2026.0 + rozdział 12 książki)

- Dane: **systemy sygnalizacji, grupy sygnałów, sterowanie (fixed-time, `sylvia`, `laemmerFix`), amber, intergreens.** Sygnał stoi na końcu linku albo pasa (`lanes`). Pasy (`org.matsim.lanes`) dają osobne kolejki dla manewrów (zakręty), bo jedna kolejka na link blokuje wszystkich za pierwszym stojącym (rys. 12.2 i 12.3 w rozdziale).
- Wg rozdziału: „większość scenariuszy MATSim z sygnalizacją jest zbudowana z pasami; kod jest dobrze przetestowany”, przepustowość rośnie liniowo z czasem zielonego. MATSim **nie ma wykrywania kolizji**, więc intergreens służą tylko do walidacji zdarzeń.
- **Pierwszeństwo:** `SignalSystemsConfigGroup.intersectionLogic` ma trzy wartości: `NONE`, `CONFLICTING_DIRECTIONS_NO_TURN_RESTRICTIONS`, `CONFLICTING_DIRECTIONS_AND_TURN_RESTRICTIONS`. Pakiet `data/conflicts` ma obiekty `Direction` (od linku do linku, w węźle i systemie sygnalizacji) z listami: `conflictingDirections`, `directionsWithRightOfWay`, `directionsWhichMustYield`, `nonConflictingDirections`. **Czyli pierwszeństwo i konflikty kierunków istnieją w MATSim, ale zaszyte w modelu danych sygnalizacji** (klucz: `SignalSystem` + węzeł). Czy da się to użyć dla węzła bez sygnałów (np. system bez grup), nie sprawdziłem. To pytanie do testu 2 iteracji.
- Wynik z literatury: Cottbus (Grether 2014, w rozdziale 12): różnice między „bez sygnalizacji”, stałymi czasami i sygnalizacją ruchową są **małe w lekko obciążonej sieci** (dojazdy do pracy), a duże dopiero przy nieoczekiwanym ruchu (mecz: do 15 min na podróżnego przy 2000 dodatkowych pojazdów). Thunig i in. 2019: optymalizacja programów światłem dla 22 skrzyżowań Cottbus dała zysk czasu, ale tylko ok. 70% zysku z modelu analitycznego odtworzono w MATSim, a kluczowe było odwzorowanie pasów i wspólnej przepustowości pasa (zakręty na jednym pasie dzielą przepustowość).
- Alternatywa „gruba” z rozdziału: efekt sygnalizacji przez **zmienną w czasie przepustowość linku** (Charypar 2008, time-variant network), czyli to, co Nagel opisuje na wykładzie 1 (czerwone połowę czasu daje połowę przepustowości).

## 3. Porównanie modeli (z plików, nie z pamięci)

Wersje: `matsim-berlin` gałąź `release/v6`, commit `04d23cd` (2025-01-13); `matsim-kelheim` master, commit `d9135c6` (2025-11-26); Wiedeń 2023.2 (`e8dc348`); Kutno R8.

| cecha | Kutno (R7b → R8) | Kelheim v3.1 | Open Berlin v6 | Wiedeń 2023.2 |
|---|---|---|---|---|
| sieć | OSM → `SupersonicOsmNetworkReader`, węzły tylko skrzyżowania | OSM → **SUMO `netconvert`** (`--tls.guess-signals`, `--tls.join`, `--junctions.join`, `--roundabouts.guess`) → `prepare network-from-sumo` | to samo + `--lane-restrictions REDUCE_CAR_LANES`, potem `clean-network … --remove-turn-restrictions` | OSM → **pt2matsim** (375 tys. linków) |
| sygnalizacja w modelu | brak | brak (w repozytorium nie ma kodu `signals`; SUMO zgaduje światła tylko przy budowie sieci) | brak (w repozytorium jedyna wzmianka to komentarz w `RunBerlinScenario`; brak plików sygnalizacji) | brak |
| typ węzła w parametrach linków | brak | brak | **tak: `traffic_light`, `right_before_left`, `priority`** | brak |
| przepustowość linku | domyślne Supersonic na pas: 600 (7313 z 10 383 linków), 1200, 1500, 3000… | z konwertera SUMO (pasy) | `apply-network-params freespeed capacity` (model `BerlinNetworkParams`), potem HBS dla `residential`, `living_street` (`--capacity-bounds 0.3 --decrease-only`) | 600 (263 tys. z 375 tys. linków), 1000, 1500, 3000… (domyślne pt2matsim) |
| prędkość swobodna | limit × `f_g`, 6 grup (D23, dopasowane do TomTom) | Makefile nie ustawia nic poza domyślnymi konwertera `network-from-sumo` (opcja `--free-speed-factor` „obniżenie dla linków miejskich” istnieje, wartości domyślnej nie sprawdzałem) | model `speedRelative` per typ węzła, potem kalibracja do tras online (Rakow, Nagel 2024b) | nie sprawdzałem (pt2matsim z OSM) |
| QSim | PassingQ, `queue`, stuck 30 s | FIFO, kinematicWaves, stuck 30 s, `useLanes=false` | kinematicWaves, stuck 30 s (D18, `ZRODLA`) | domyślne, `flowCapacityFactor=0,10836`, ruch ciężarowy jako −10% przepustowości |
| próbka | 25% | 25% | 10% (3% i 1%) | ok. 10,8% |

Wnioski z porównania:
- **Kelheim, najbliższy analog Kutna, nie robi niczego więcej niż my z węzłami**: sieć z SUMO i przepustowość na pas. Jego jakość kalibracji opiera się na licznikach i trybach, a nie na modelu węzłów.
- **Berlin v6 to jedyny z czterech, który modeluje wpływ skrzyżowań, i robi to w parametrach linków.** Zakazy skrętu z OSM Berlin **usuwa** (`--remove-turn-restrictions`), czyli nasz wynik G1 („zakazy nic nie zmieniają”) jest zgodny z praktyką twórców.
- Wiedeń i Kelheim traktują przepustowość jako domyślną, a kalibrację przenoszą na prędkość, ruch tła i tryby. To nasza obecna ścieżka (D23, G5).

### 3.1 Jak działa ścieżka Berlina (mechanizm do przejęcia)

`ApplyNetworkParams` (matsim-libs, `org.matsim.application.prepare.network.params`, jest w naszym jarze) dla każdego linku bierze **cechy z sieci SUMO** i stosuje model dla typu węzła docelowego linku. Cechy (z wygenerowanego kodu `BerlinNetworkParams_speedRelative_traffic_light`): długość, prędkość, liczba pasów, zmiana prędkości i liczby pasów względem poprzedniego linku, liczba linków wylotowych, liczba pasów wlotowych do węzła, **czy link ma niższy / równy / wyższy priorytet niż inne wloty**, czy droga to secondary lub wyższa, primary lub wyższa, motorway, link łączący. Model to drzewa decyzyjne (generowany kod, parametry liści dostrojone). Wyjście: **względna prędkość swobodna** (współczynnik, domyślne granice 0,25–1,03) i **przepustowość** (domyślne dolne granice względem teoretycznej: **0,4 dla sygnalizacji, 0,6 dla „prawej ręki”, 0,8 dla pierwszeństwa**, parametr `--capacity-bounds`). Cechy o liczbie pasów rozstrzyga SUMO; dla dróg `residential` i `living_street` Berlin dodatkowo obniża przepustowość wg HBS (niemiecka metodyka wymiarowania).

Model uczono na symulacji SUMO każdego typu węzła (Rakow, Nagel 2024b, abstrakt: SUMO daje dane uczące, a następnie dopasowanie do czasów przejazdu między punktami z usług online obniża błąd o 30–60% względem „jednej obniżki dla wszystkich dróg miejskich”).

## 4. Co mówi literatura

| źródło | co z niego wiemy | ograniczenia |
|---|---|---|
| Grether, Thunig 2016, rozdz. 12 MATSim book (CC-BY) | mechanika sygnalizacji w MATSim, pasy, brak kolizji, zalecenie lanes, alternatywa time-variant capacity (Charypar 2008); Cottbus: różnice małe bez zatoru | stan 2016, nowe kontrybucje (laemmer, intersection logic) opisane w kodzie, nie w rozdziale |
| Thunig, Scheffler, Strehler, Nagel 2019, Procedia CS 151 | sprzężenie optymalizacji stałych programów i MATSim; konflikty zakrętów z programu bazowego; pasy konieczne | tylko 22 skrzyżowania Cottbus, programy z danych miasta |
| Rakow, Kreuschner, Nagel 2024 (EWGT, Open Berlin) | w modelach mezoskopowych światła nie są modelowane, więc **free speed musi uwzględniać opóźnienia świateł i znaków nawet bez zatorów**; przepustowość skrzyżowań z SUMO | szczegóły sieci w [24] i [26] |
| Rakow, Nagel 2024b, Procedia CS 238 (abstrakt) | SUMO jako źródło danych uczących dla modelu prędkości swobodnej, dopasowanie do czasów online, błąd −30 do −60% | tylko abstrakt, pełny tekst za paywallem (403) |
| Nippold, Wagner, Banse Bueno, Rakow 2021 (SUMO Conf.) | w sieci Düsseldorfu każdy węzeł z sygnalizacją zasymulowano w SUMO: **średnio 1131 poj./h na pas przy 100% pojazdów konwencjonalnych (min 24, maks 1766)**, wobec 1800 do 2000 poj./h na pas w modelach planistycznych; pojazdy autonomiczne obniżają przepustowość prawie liniowo; wyniki wprowadzane do MATSim | tylko węzły z sygnalizacją, kalibracja pod AV |
| Nagel i in. 1997, TRANSIMS (arXiv adap-org/9710003) | ruchy niechronione (ustąp, stop, lewoskręt) modelowane przez **akceptację luki** w ruchu kolidującym; ona wyznacza przepływ; maks. przepływ na sygnalizacji wyznacza reguła ruchu | automat komórkowy, mikro, nie MATSim |
| SUMO, dokumentacja skrzyżowań | pojazd bez pierwszeństwa hamuje wcześnie i wjeżdża, gdy jest luka; heurystyka no-block; parametr `impatience` | mikro; w MATSim nie ma odpowiednika |
| Tampère i in. 2011 (generyczny model węzła, za arXiv 1601.01054, 1509.04995, 1608.07623) | węzeł w modelach przepływowych: popyt, podaż, **priorytety wlotów**; gdy priorytet = przepustowość, odtwarza model węzła bez sygnalizacji (to w zasadzie wariant, który ma MATSim) | tylko streszczenia z wyszukiwarki, artykułu nie czytałem |
| Sallard, Balac, „Modeling Crossroads in MATSim: …Traffic-Signaled Intersections” | tytuł dotyczy dokładnie naszego pytania | **nieczytane**, nie znalazłem tekstu |
| Natterer i in., GNN przepustowość Paryż (arXiv 2408.06762) | tytuł; kalibracja przepustowości metodą uczoną | **nieczytane** |

Kontekst praktyczny: **mezoskopowe modele (MATSim, Dynameq-podobne) nie rozdzielają prędkości od węzłów, a standardem jest dopasowanie `freespeed` i `capacity` do czasów przejazdu i liczników**. Rozdzielenie dwóch efektów (prędkość swobodna a opóźnienie węzła) wymaga albo modelu mikro (SUMO), albo jawnych danych o węzłach.

## 5. Co wiemy o Kutnie (nasze dane)

- **OSM w obszarze sieci:** 40 węzłów `highway=traffic_signals`, 107 `give_way`, 16 `stop`, 4 `mini_roundabout`, 945 `crossing`, 14 elementów uspokojenia ruchu; ronda (62 drogi, 119 linków, jednokierunkowe). W obszarze miast: 36 sygnałów, 59 `give_way`, 8 `stop`.
- **Sprostowanie do G1:** w raporcie G1 napisałem, że sygnalizacja to 4 węzły sieci. To prawda dla id węzłów, ale **wszystkie 40 sygnałów leży w odległości ≤ 30 m od węzła sieci** (18 ≤ 15 m), bo OSM stawia je na linii zatrzymania, a Supersonic zostawia węzły skrzyżowań. Przypisanie do najbliższego węzła daje **33 węzły sieci i 85 linków wlotowych** (tertiary 43, residential 22, primary 16, secondary 2, living_street 2); część (np. stopień 1/1 i 2/2) to sygnały przejść dla pieszych w środku odcinka, więc realnie ok. 25 do 29 skrzyżowań z sygnalizacją. Sygnalizacja jest zatem możliwa do zlokalizowania, ale **programów sygnalizacji nie mamy**.
- **R7b, rozkład opóźnień wg przyczyny** (`queues.py`): węzeł 49%, spillback 30%, przepustowość 21% (a opóźnienie całkowite jest małe: 4,3% czasu w sieci). **To, co model uważa za opóźnienie węzła, już jest w QSim**, bo wlot jest ograniczony przepustowością wylotu. Natomiast opóźnienie w warunkach swobodnych jest w `f_E` i `f_F` (0,85 i 0,55), czyli niewidoczne w rozkładzie.
- **G1:** zakazy skrętu nie zmieniają wyników (zmiana ≤ 0,8% wobec rozrzutu planów 4–5%).
- **Zawrotki:** 40 na 100 podróży ma zawrotkę **na początku lub końcu** trasy (aktywność przypięta do linku skierowanego, zob. F1), w środku tras 0 (R7b). To potencjalnie **większe źródło opóźnień niż skrzyżowania** i nie ma nic wspólnego z węzłami.

## 6. Jak implementować opóźnienia i sygnalizację: opcje

| # | opcja | co dokładnie | dane | koszt | efekt | ryzyko |
|---|---|---|---|---|---|---|
| 0 | **stan obecny**: opóźnienie w `f_g` | jeden współczynnik na klasę drogi i miasto/poza (D23) | TomTom (zużyte) | 0 | zgodne z praktyką, ale grube: miesza klasy węzłów | nie rozdziela efektów; każda zmiana `f` wymaga R7c |
| 1 | **przepustowość wlotów wg typu węzła** | klasyfikacja węzłów (sygnały OSM, `give_way`/`stop`, rondo, równorzędne) i obniżenie `capacity` wlotów podporządkowanych; wartości jak w Berlinie jako dolne granice (0,4 / 0,6 / 0,8) albo własne z wariantami | OSM (mamy) | mały: jedna funkcja w `CreateKutnoNetwork` | wpływ zależy od obciążenia: przy kolejkach w mieście może być zauważalny, w ruchu swobodnym zero | wartości to ZAŁOŻENIA z Niemiec (zasada prawej ręki jest też w PL, ale reguły znaków inne); wpływ niemierzalny bez niezależnych danych |
| 2 | **prędkość swobodna wg typu węzła** (rozdzielenie `f` od węzłów) | `f` osobno dla linków wlotowych do węzła z sygnalizacją i bez, albo model Berlina (`GermanyNetworkParams_*` jest w jarze) z cechami policzonymi z naszej sieci | cechy z naszej sieci OK; typ węzła z OSM; trening wymagałby SUMO | średni; uczenie: duży | rozdzielenie opóźnień od `f`, o co chodziło w G1 | wymaga nowych danych kalibracyjnych (TomTom, D22), SUMO to instalacja globalna (pytać) |
| 3 | **lanes (pasy skrętu)** | osobna kolejka na zakręt, przepustowość wspólna na pas | liczba i przeznaczenie pasów (OSM `lanes`, `turn:lanes` rzadko) | wysoki | realistyczny spillback na wlotach | brak danych w OSM dla większości skrzyżowań |
| 4 | **contrib `signals`** (stałe programy) | systemy, grupy, fazy, intergreens, opcjonalnie `intersectionLogic` | **programy sygnalizacji miasta**, których nie mamy | wysoki | tylko ok. 25 skrzyżowań | bez danych wymyślamy programy, a Nagel i Cottbus pokazują, że w lekko obciążonej sieci różnica jest mała |
| 5 | **pierwszeństwo bez sygnałów** (`Direction` z `directionsWhichMustYield`) | prawdopodobnie przez system sygnalizacji bez grup (nie zweryfikowane) | hierarchia dróg z OSM | średni + test | pierwszeństwo kierunków | niepewne wsparcie dla węzłów bez sygnałów |
| 6 | **własna logika węzła** (akceptacja luki jak TRANSIMS/SUMO) | nowy `TurnAcceptanceLogic` / `QNode` | brak (parametry z literatury) | bardzo wysoki | pierwszeństwo, lewoskręty | poza duchem MATSim jako symulacji planistycznej; nie robić |
| 7 | **time-variant capacity** (Charypar 2008) | przepustowość linku zmienna w dobie dla wlotów z sygnałami (np. ×(zielone/cykl)) | udział zielonego (nie mamy) | średni | efekt sygnalizacji „gruba” | brak udziału zielonego; ZAŁOŻENIE |

## 7. Rekomendacje dla naszego modelu

1. **Nie wprowadzać sygnalizacji (opcje 4, 5, 6) i pasów (3) w Kutnie teraz.** Brak programów sygnalizacji, a literatura (Cottbus) i Nagel pokazują, że sygnalizacja w lekko obciążonej sieci (nasz przypadek: opóźnienie to 4,3% czasu w sieci) zmienia wyniki mało. **Zostawić jako opcję na później** (ROADMAP „sygnalizacja”), gdy będzie źródło programów.
2. **Wniosek metodyczny dla `f_E` i `f_F`:** zostają jak są i dalej „zawierają opóźnienia węzłów”, to praktyka Berlina (Rakow 2024). Poprawa nie polega na „uwolnieniu” `f`, tylko na **zróżnicowaniu `f` wg typu węzła** (opcja 2) lub przynajmniej na rozdzieleniu: wlot do skrzyżowania z sygnalizacją i bez.
3. **Kolejny eksperyment, jeśli chcemy dalej w tę stronę (G1b, osobna decyzja w `DECISIONS`):** opcja 1 (klasyfikacja węzłów z OSM i obniżenie `capacity` wlotów) w trzech wariantach, z wartościami jawnie oznaczonymi jako ZAŁOŻENIE ze źródłem (Berlin: 0,4 / 0,6 / 0,8 jako dolne granice względem teoretycznej) i ocenianymi **tylko względem rozrzutu seedów planów** (kryterium jak w G1). Spodziewany efekt jest mały i to jest hipoteza do sprawdzenia, nie obietnica.
4. **Sprawdzić zawrotki na początku i końcu trasy** (40 na 100 podróży). To tańsze niż węzły i może wyjaśniać część opóźnień oraz asymetrię czasów tam i z powrotem (F1). Test: aktywności przypięte do linku w obie strony albo wybór linku wg strony domu.
5. **Jeśli kiedyś ML Berlina (opcja 2):** policzyć cechy z naszej sieci (długość, prędkość, pasy, liczba wylotów, priorytet wg hierarchii OSM, typ węzła), uruchomić `GermanyNetworkParams` z jara i porównać z naszym `f_g` **jako hipotezę**, nie jako zamiennik: model trenowano na niemieckich skrzyżowaniach (SUMO), przeniesienie do Polski nieprzetestowane. Pełna metoda wymaga SUMO (instalacja globalna, pytać) i nowych requestów TomTom (D22).
6. **Test przed wdrożeniem każdej zmiany (zasada z CLAUDE.md):** 2 iteracje na MATSim 2026, potem 25% × 3 seedy + 2 seedy planów, **teraz maks. 50 iteracji** (nowe ustalenie użytkownika). Uwaga: 100 vs 400 iteracji dawało różnicę ≤ 0,4 km/h i GPR ≤ 0,004 (GitHub Actions), natomiast **50 iteracji nie było testowane**; trzeba to sprawdzić na jednym runie przed porównaniami.
7. **Zapisać w `DECISIONS` (nowy wpis przy G1b):** zakres, wartości ZAŁOŻEŃ z wariantami i źródło (Berlin).

## 8. Ograniczenia tego researchu

- Pełnych tekstów Rakow i Nagel 2024b oraz Sallard i Balac nie czytałem (paywall lub brak dostępu), tylko abstrakty i wyniki wyszukiwania. Wnioski o ML Berlina opierają się na **kodzie wygenerowanych modeli w repozytorium** i opisach parametrów w jarze, nie na artykule.
- Semantykę pakietu `data/conflicts` ustaliłem z nazw metod, bez testu w działającym scenariuszu.
- Nagrania wideo kursu nie były odsłuchiwane. Czytałem transkrypcje (`.txt` w archiwum `G:\ARCHIWUM_pulpit_2026-10-01\pulpit_MATSim.7z`, rozpakowane tylko do katalogu tymczasowego sesji) i slajdy w markdown. Podsumowanie kursu z lipca (`kurs_TU_Berlin_podsumowanie.md`) nie obejmuje węzłów i sygnalizacji.
- Wartości Berlina (0,4 / 0,6 / 0,8) to **dolne granice względem teoretycznej przepustowości w narzędziu**, a nie pomiary; samo narzędzie dostraja je modelem. Nie przenosić wprost do Kutna bez testu.
- Model Wiednia ma licencję CC BY-NC 4.0 (użycie tylko niekomercyjne, dane nie trafiają do repo); tu użyłem tylko jego statystyk sieci.
