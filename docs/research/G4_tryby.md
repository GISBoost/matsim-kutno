# G4 — dane i wiedza do dodania trybów (car / pt / bike / walk)

Stan na 2026-10-17. Sesja badawcza etapu 2a: **nic w modelu nie zmieniono**, nie uruchamiano MATSim. Pobrane pliki leżą w `data/raw/g4/`.
Oznaczenia: **[plik]** = liczba odczytana lokalnie z pliku, **[WWW]** = ze strony/PDF-a pobranego w tej sesji, **[WebFetch]** = streszczenie narzędzia z kodu na GitHubie, nieczytane przeze mnie bezpośrednio (do weryfikacji w lokalnych źródłach, gdy G4 ruszy).

## 1. Podział modalny

### 1a. GUS „Mobilność transportowa ludności w Polsce w 2024 r.” — przejrzano wszystkie 47 arkuszy

Wynik: **brak podziału modalnego wg klasy miejscowości i brak „dom–praca × środek transportu”.**

| Co sprawdzono | Wniosek |
|---|---|
| Tabl. 1–13, 15–19 | Podział tylko wg województwa/regionu (np. „Warszawski stołeczny”, „Mazowiecki regionalny”), wg lokalizacji gospodarstwa. |
| Tabl. 14 (jedyna z klasami miejskich obszarów rynku pracy, arkusz `Klasy_miej_obsz_ryn_pr`) | To **macierz podróży ROZPOCZĘCIE × ZAKOŃCZENIE** (rdzeń / powiaty rozlewającego się miasta / pozostałe powiaty / poza województwem), **bez środka transportu i bez motywacji**. Klasy: 1 = miasto rdzeń, 2 = powiat rozlewającego się miasta rdzenia, reszta = „pozostałe powiaty”. W arkuszu `Klasy_…` nie ma ani miasta Kutna, ani powiatu kutnowskiego (szukałem po „Kutn”), więc Kutno należałoby do „pozostałych powiatów” woj. łódzkiego — czyli bez wydzielonej klasy. Użyteczne co najwyżej jako kontrola przepływów, nie trybów. |
| Tabl. 10 | Pary motywacji (dom→praca, praca→dom) **bez środka transportu**. Łódzkie: dom→praca 730 740, praca→dom 661 460 podróży na dzień roboczy (Polska 11 079 992 / 9 842 801). |
| Tabl. 13 | Środek transportu, ale **wszystkie cele łącznie**, kategorie nierozłączne („co najmniej jeden etap”). |
| Tabl. 17 | Wyjazdy ≥ 100 km (nie dojazdy codzienne). Odpada. |
| Tabl. 1 | Łódzkie: praca z domu 74 747, poza domem 892 407, mieszany 55 823 osób (7,3% / 87,2% / 5,5%). |
| Tabl. 32 (błędy względne tabl. 13), łódzkie | ogółem 2,2%; pieszo 6,8%; rower 16,3%; motorower/jednoślady 72,6%; samochód 3,9% (kierowca 3,9%, pasażer 8,4%); autobus miejski 10,3%; autobus międzymiastowy 23,3%; kolej 24,9%. Polska: pieszo 1,7%, rower 3,7%, samochód 1,0%, autobus miejski 2,5%. |

Udziały łódzkie wyliczone z tabl. 13 [plik] (liczba podróży / 3 958 088): pieszo 20,51%, rower 5,16%, samochód osobowy 60,11% (kierowca 47,86%, pasażer 12,25%), autobus miejski/podmiejski 7,19%, autobus międzymiastowy 1,43%, kolej 1,33%, jednoślady motorowe 0,17%. Suma > 100%, bo podróże wieloetapowe liczą się w kilku kategoriach (tabl. 12: w łódzkim 97,7% podróży jest jednoetapowych).

**Przybliżone widełki testu G4 z tabl. 32** (błąd względny liczby podróży; nie uwzględnia błędu mianownika): pieszo 20,5 ± 1,4 pp, rower 5,2 ± 0,8 pp, samochód 60,1 ± 2,3 pp, autobus 7,2 ± 0,7 pp. To jest przedział dla **województwa i wszystkich celów**, nie dla Kutna i dojazdów do pracy.

### 1b. Inne źródła (małe/średnie miasta PL, dojazdy do pracy)

| Źródło | Granulacja | Cel | Rok | Liczby | Błąd / uwagi | Dowód |
|---|---|---|---|---|---|---|
| **Bochnia**, Studium Transportowe, Etap I (miasto 30 051 mieszk., zbliżona do Kutna 42 tys.) | miasto, ankieta domowa (baza PESEL, geokodowanie) | **dom–praca** (wykres 6.2) | ankiety X 2016 | samochód 67%, autobus miejski 12%, bus 7%, pociąg 1%, rower 3%, pieszo 10% (suma 100%). Wszystkie cele obligatoryjne+zakupy: samochód 67%, autobus 12%, bus 5%, pociąg 1%, rower 2%, pieszo 13% | brak błędu, brak liczby ankiet w odczytanym tekście; dane sprzed 10 lat; wykres z wykresu kołowego, zaokrąglone do 1 pp | PDF s. 44–45 (wykresy 6.1–6.2), `data/raw/g4/bochnia_studium_mobilnosci_cz2.pdf`; URL w „Wierszach do manifestu” |
| **Radom i gminy GOFR**, SUMP 2030+ Raport diagnostyczny | miasto Radom (~190 tys.) i 10 gmin obszaru, ankieta, N = 750 respondentów GOFR | podróże **obligatoryjne** (praca+nauka), Radom (rys. 5.25) | ankiety X 2022 | Radom, obligatoryjne: pieszo 12,03%, indywidualna 61,41%, zbiorowa 19,09%, rower 7,47%; Radom, wszystkie podróże (rys. 5.24): 20,29 / 52,43 / 17,43 / 9,86; całe GOFR obligatoryjne (s. 134): samochód > 67%, rower 6,37%, zbiorowy 17,19%, pieszo 9,19% | etykiety rysunków nie są powiązane z liczbami w tekście PDF-a, kolejność przypisałem wg kolejności legendy — **zweryfikuj wzrokowo na rys. 5.25**; „indywidualna” = samochód+motocykl+pasażer; ankieta dotyczy także gmin wiejskich (n małe per gmina) | PDF s. 133–138, `data/raw/g4/radom_sump_diagnoza_2023.pdf` |
| **GUS Mobilność 2024, tabl. 13** | województwo łódzkie | wszystkie cele | IX–XI 2024 | j.w. | tabl. 32 | `gus_transport/…tablice.xlsx` |
| **NSP 2021** | gmina (macierz) | dojazdy do pracy | 2021 | tylko przepływy, **brak środka transportu** | Dane z rejestrów administracyjnych (ZUS/KRUS/podatki), nie z ankiety; potwierdzone przez stronę GUS „Dojazdy do pracy w świetle wyników NSP 2021” (opis metodologii) — wynik przeszukania nie wskazał podziału wg środka transportu, a w naszych plikach `gus/*.xlsx` słowa „środek/transport” nie występują poza tytułem publikacji | https://stat.gov.pl/spisy-powszechne/nsp-2021/nsp-2021-wyniki-ostateczne/dojazdy-do-pracy-w-swietle-wynikow-nsp-2021,8,2.html ; pełny PDF (~152 MB) nie przeglądany |
| **Wrocław KBR 2024** | miasto + 9 gmin | wszystkie cele | 2024 | udział auta < 40% (tylko komunikat) | zbyt duże miasto, tylko kontekst | https://www.wroclaw.pl/komunikacja/kompleksowe-badanie-ruchu-2024-we-wroclawiu-i-gminach-sasiednich-wyniki |
| **Kutno: SUMP / plan transportowy / KBR** | — | — | — | **nie znaleziono** w wyszukiwaniach (kilka zapytań, w tym extended). Nie oznacza, że nie istnieje: trzeba sprawdzić BIP Urzędu Miejskiego i Starostwa w Kutnie oraz dokumenty woj. łódzkiego | — |
| **Eurostat** | — | — | — | nie znalazłem tablicy udziału środków dojazdu do pracy wg stopnia urbanizacji dla PL; nie twierdzę, że jej nie ma | — | wyszukiwanie bez trafienia |

**Wniosek do decyzji:** nie ma twardego źródła dla Kutna. Najbliższe ankietowe odniesienia dla dom–praca w mieście 30–200 tys. to Bochnia (auto 67%, pieszo 10%, rower 3%, PT 20% łącznie z busami) i Radom (auto/indywidualna 61%, pieszo 12%, rower 7%, PT 19%). Łódzkie GUS (wszystkie cele) jest bardziej „zielone” (auto 60%, pieszo 20%), co jest oczekiwane, bo zakupy/odprowadzanie dzieci skracają podróże. Cel kalibracji dla dojazdów do pracy powinien więc być **przedziałem z tych źródeł** (z jawnym ZAŁOŻENIEM), a nie jedną liczbą.

## 2. Transport publiczny — dane

| Źródło | Co zawiera | Ważność | Licencja / status | Plik |
|---|---|---|---|---|
| **zbiorkom.live/kutno** (`data/raw/gtfs/kutno.zip`, już w repo) | `agency_name = zbiorkom.live/kutno`, kontakt `admin@zbiorkom.live`, `feed_version = 1228`; **13** `route_id` (1–12 i 14, nie 12), 1 031 wierszy trips, autobusy (`route_type=3`), `shapes.txt` jest | 2026-10-01 – 2026-12-31 | **Brak licencji w feedzie.** Strona zbiorkom.live/about wymienia sekcje „źródła danych, licencje, warunki” ale treść nie została pobrana przez narzędzie. Operatorem jest **MZK Kutno**; nie znalazłem GTFS ani strony otwartych danych MZK/UM Kutno. | `gtfs/kutno.zip` |
| **MZK Kutno / UM Kutno (oficjalne)** | Komunikat UM Kutno (dotyczy grudnia 2024, zebrany z wyników wyszukiwania): linie 1, 2, 5, 7, 9, 10, 11, 12, 14 + 3, 4, 6 w rozkładzie feryjnym; **posiadacze Kutnowskiej Karty Mieszkańca jeżdżą komunikacją miejską bezpłatnie**. Inny komunikat (bez daty): linie 13, 31, 35, 36, 37 zlikwidowane, a 1, 9, 12, 14 skrócone do granicy miasta po wypowiedzeniu porozumień przez sąsiednie gminy | — | Brak GTFS. Rozkłady w e-podroznik.pl (HTML). Można poprosić UM/MZK o GTFS (podstawy prawnej nie sprawdzałem). | https://um.kutno.pl/print/pdf/node/4338 |
| **Kolej: `polish_trains.zip`** (Mikołaj Kuranowski) | PKP Intercity, PolRegio, Koleje Mazowieckie, Koleje Wielkopolskie, **ŁKA**, Arriva, RegioJet i inni; 12 191 przystanków | **tylko 2026-10-17 – 2026-11-16** (feed odświeżany codziennie) | Warunki PKP PLK + Koleje Mazowieckie; w pliku `attributions.txt`: dane KM (zasady ponownego wykorzystywania informacji sektora publicznego, BIP KM), dane PLK (API otwarte, dostęp bezpłatny, rejestracja pdp-api.plk-sa.pl), GTFS: M. Kuranowski. **Nie jest to licencja CC dla całego feedu**; sprawdzić warunki PLK przed publikacją wyników opartych na danych. | `data/raw/g4/polish_trains.zip` |
| Kutno w feedzie kolejowym | przystanek `Kutno` (id 32201, 52,2270 N / 19,3487 E), `Kutno Azory`, `Nowe Kutnowskie` | — | — | — |
| Kursy zatrzymujące się w Kutnie (wtorek–czw. 2026-10-21, 180 kursów; sob. 24.10: 152) | IC 70, ŁKA 58, KM 26, PolRegio 18, Koleje Wielkopolskie 8 (kursy w obu kierunkach, liczone jako kursy) | — | — | policzone w tej sesji ze `stop_times`/`calendar_dates` |
| ŁKA GTFS (źródło własne) | link zmienia się co rok: `https://kolej-lka.pl/pliki/pn0e6eg45qcl4hd5/gtfs-2025-2026/zip/` (wg mkuran.pl) | rozkład 2025/26 | licencja nieznana (nie pobrano) | — |
| PKS / autobusy podmiejskie do gmin powiatu | **nie znalazłem żadnego GTFS** | — | — | — |
| Polregio | nie publikuje GTFS samodzielnie (odpowiedź Polregio cytowana w artykule spidersweb.pl z 2024), ale jest w zbiorczym feedzie Kuranowskiego | — | — | https://spidersweb.pl/2024/01/rozklady-jazdy-dostep-w-polsce.html |

**Konsekwencje:** (1) dla autobusu miejskiego jedyny dostępny GTFS ma niejasną licencję i obejmuje tylko 3 miesiące; (2) kolej jest dostępna, ale ważna tylko miesiąc od pobrania (dla G4 wybieramy jeden dzień typowy, np. wtorek 2026-10-20, i zapisujemy go jako wejście); (3) autobusów międzygminnych/PKS nie ma; (4) MZK Kutno ma darmowe przejazdy dla posiadaczy Karty Mieszkańca — to **silnie obniża koszt PT dla mieszkańców** i musi wejść do scoringu (cena 0) oraz do interpretacji kalibracji.

## 3. Rower i pieszo z OSM

Policzone lokalnie z `data/raw/osm/lodzkie-261015.osm.pbf`, przycięte do gm. Kutno (`scenarios/kutno/area/gmina.geojson`, 33,5 km², długość linii w EPSG:2180). Skrypt jednorazowy, nie dodany do repo.

| Obiekt | Długość [km] |
|---|---|
| `highway=cycleway` | 10,4 |
| `highway=path` + `bicycle=designated` | 11,9 |
| `highway=footway` + `bicycle=yes` | 0,2 |
| `pedestrian` + `bicycle=yes` | 0,4 |
| `track` + `bicycle=yes` | 0,4 |
| pasy/pobocza rowerowe (`cycleway[:side]=lane/opposite/separate`) | 0,8 / 0,1 / 0,1 |
| `highway=footway` (razem, głównie chodniki) | 165,3 (z tego 163,7 bez tagu `bicycle`) |
| jezdnie: residential 113,3; service 94,6; tertiary 32,5; primary 11,8; secondary 1,3; living_street 10,2; unclassified 0,5 | do ruchu rowerowego po jezdni |

Wniosek: dedykowanej infrastruktury rowerowej ~23 km (cycleway + path z designated), a jeździ się po jezdniach (~265 km dróg do 50 km/h). Rower jako tryb sieciowy ma sens tylko jako „po jezdniach + ścieżki”; dane o nawierzchni, wysokościach (Kutno płaskie) nie sprawdzane. Pieszo: chodniki 165 km, ale **w F2 sieć MATSim jest samochodowa**, więc pieszo = tryb teleportowany (odległość × współczynnik / prędkość).

## 4. MATSim 2026.0 — konfiguracja trybów

### 4a. Co jest w naszym uber-jarze (`unzip -l matsim/matsim-example-project-0.0.1-SNAPSHOT.jar`)

| Element | W jarze? |
|---|---|
| `SubtourModeChoice` (strategy + module + `SubtourModeChoiceConfigGroup`) | tak |
| `ChangeSingleTripMode`, `ChangeTripMode` (strategies) | tak |
| `org.matsim.contrib.gtfs.GtfsConverter`, `RunGTFS2MATSim` (stary konwerter, *contrib gtfs*) | tak |
| `org.matsim.application.prepare.pt.CreateTransitScheduleFromGtfs` (CLI `transit-from-gtfs` w contrib application) | tak |
| **pt2matsim** (ETH/IVT) | **nie** (brak klas `pt2matsim`) |
| `ch.sbb.matsim.routing.pt.raptor.*` (SwissRailRaptor), `SwissRailRaptorConfigGroup` | tak |
| `org.matsim.contrib.bicycle.*` (BicycleModule, BicycleConfigGroup) | tak |

`pt2matsim` wymagałby dopisania zależności do `matsim/pom.xml`, to zmiana kodu, której tu nie robiłem. Praktyczny wybór: **`transit-from-gtfs`** (z contrib application, jest w jarze) zamiast starego `RunGTFS2MATSim`.

### 4b. `transit-from-gtfs` [WebFetch z źródła 2026.0, do potwierdzenia przez `--help` w G4]

Opcje: `INPUT` (zip), `--name`, `--network`, `--date` (dzień usługi), `--output`, `--copy-late-early` (false), `--validate` (true), `--merge-stops`, `--pseudo-network` (`singleLinkBetweenStops` | `withLoopLinks`), `--shp` do filtrowania przystanków, CRS (domyślnie EPSG:4326 wejścia). Wyjście: `<name>-transitSchedule.xml.gz`, `<network>-with-pt.xml`, `<name>-transitVehicles.xml.gz`. Kod nie obsługuje przesiadek jawnie; wymusza `freespeed` pseudo-linków tak, by pojazdy wyrobiły rozkład (min. postój 30 s). Wniosek dla nas: wejście do konwertera powinno być w EPSG:2180 sieci, a wyjściowa sieć `with-pt` zastępuje `network.xml.gz` w configu PT (**drugi plik sieci — tylko dla scenariusza PT**, zgodnie z regułą „jedno miejsce generowania”, konwerter bierze naszą sieć).

### 4c. Mode choice

- **`SubtourModeChoice`** [kod, `javap` na jarze + WebFetch źródła]: parametry `modes` (domyślnie `car,pt,bike,walk`), `chainBasedModes` (`car,bike`), `considerCarAvailability` (**domyślnie `false`**, „for backward compatibility”), `probaForRandomSingleTripMode` (0,0), `coordDistance` (0,0), `behavior` (`fromSpecifiedModesToSpecifiedModes` | `fromAllModesToSpecifiedModes` | `betweenAllAndFewerConstraints`). Chain-based = tryb, którym cały łańcuch zaczynający się w domu musi być tym samym pojazdem (auto, rower). Przy home→work→home to jeden subtour, więc zmienia się tryb obu nóg razem.
- **`ChangeSingleTripMode`** (`ChangeModeConfigGroup`): `modes` domyślnie `car,pt`; `ignoreCarAvailability` **domyślnie `true`**; `modeSwitchBehavior`. Zmienia tryb jednej nogi (nie dba o łańcuch), więc dla rower/auto jest gorszy.
- **`carAvail`**: atrybut osoby (`always`/`never`/`sometimes`), uwzględniany dopiero gdy `considerCarAvailability=true` (dla SubtourModeChoice). Dane o licencjach/posiadaniu auta: GUS Mobilność tabl. 5–7 (wg województwa) i tabl. 2 (pojazdy); nic dla Kutna.
- **Wzorzec z literatury** (`docs/ZRODLA.md`, Medina Godoy): SubtourModeChoice waga 0,1, `carAvail`, rower jako tryb sieciowy, 60 iteracji, wyłączenie innowacji przy 0,7.
- **ASC/kalibracja**: `scoring → modeParams.constant` (per podróż, „probably buggy for multi-leg trips” w komentarzu kodu), `marginalUtilityOfTraveling_util_hr` (domyślnie -6,0 wg WebFetch ze źródła; sprawdzić w `ScoringConfigGroup` 2026.0 lokalnie), `marginalUtilityOfDistance_util_m`, `monetaryDistanceRate`, `dailyMonetaryConstant`. Kalibracja iteracyjna: dostrajać `constant` tak, by udział trybów w ostatnich iteracjach mieścił się w wybranym przedziale (sekcja 1). Obecny scoring w `config_25pct.xml` ma tylko `activityParams` home/work, więc **żadnych `modeParams`** — domyślne.
- **Replanning** w obecnym configu: `ChangeExpBeta` 0,8 + `ReRoute` 0,2 dla `subpopulation=person`, innowacja wyłączona po 0,8 iteracji. Dla G4 dochodzi `SubtourModeChoice` (waga ~0,1), strategia musi mieć `subpopulation=person` (gotcha z zasady projektu).

### 4d. Rower i pieszo

- Domyślnie **teleportowane** [WebFetch `RoutingConfigGroup`]: `bike` 15 km/h, `walk` 3 km/h (dokładnie: 4,17 m/s i 0,83 m/s wg komentarzy, `beelineDistanceFactor` 1,3), `pt` freespeed×2,0 w routerze „uproszczonym”, `ride` ×1,0. Komentarz kodu: „Travel time = (<beeline distance> * beelineDistanceFactor) / teleportedModeSpeed”. Teleportacja = rower nie zajmuje pojemności ulic ani nie obciąża auta (tak jak nogi `walk` dojścia dziś).
- **Sieciowy rower** (`routing.networkModes=car,bike`, `qsim.mainMode=car,bike`, linki z `allowedModes=car,bike`, `qsim.vehiclesSource=modeVehicleTypesFromVehiclesData`, typy pojazdów z `maximumVelocity` 15 km/h): wymaga zmiany generatora sieci (F2) i pliku pojazdów. `contrib bicycle` (`BicycleModule`) dodaje scoring od nawierzchni/typu drogi/nachylenia; `BicycleConfigGroup.checkConsistency` odrzuca `vehiclesSource=defaultVehicle` i `accessEgressType=none` [WebFetch]. Dla Kutna (płasko, 23 km dedykowanych ścieżek) ten dodatek ma niski zwrot.
- **Zalecenie (techniczne, nie decyzja):** G4-minimum = rower i pieszo **teleportowane** z jawnymi prędkościami w configu, PT z `transit-from-gtfs`, rower sieciowy dopiero jeśli ruch rowerowy ma wpływać na natężenia (dla Kutna prawdopodobnie nie).

### 4e. Minimalna propozycja konfiguracji G4 (do przetestowania 2 iteracjami zgodnie z zasady projektu pkt 9; nie testowana)

```xml
<module name="routing">
  <param name="networkModes" value="car" />
  <!-- bike/walk: teleportowane, prędkości jawnie (ZAŁOŻENIE do kalibracji) -->
  <parameterset type="teleportedModeParameters"><param name="mode" value="bike"/><param name="teleportedModeSpeed" value="4.17"/><param name="beelineDistanceFactor" value="1.3"/></parameterset>
  <parameterset type="teleportedModeParameters"><param name="mode" value="walk"/><param name="teleportedModeSpeed" value="0.83"/><param name="beelineDistanceFactor" value="1.3"/></parameterset>
</module>
<module name="transit"><param name="useTransit" value="true"/><param name="transitScheduleFile" value="…-transitSchedule.xml.gz"/><param name="vehiclesFile" value="…-transitVehicles.xml.gz"/><param name="transitModes" value="pt"/></module>
<module name="swissRailRaptor"/>  <!-- albo domyślny router; do wyboru w G4 -->
<module name="subtourModeChoice">
  <param name="modes" value="car,pt,bike,walk"/>
  <param name="chainBasedModes" value="car,bike"/>
  <param name="considerCarAvailability" value="true"/>
</module>
<!-- replanning: dodać SubtourModeChoice, subpopulation=person, weight 0.1; ChangeExpBeta/ReRoute jak dziś -->
<!-- scoring: modeParams constant (ASC) dla pt, bike, walk — start 0, kalibrować; pt monetaryDistanceRate/constant = 0 przy Karcie Mieszkańca -->
```

Uwagi: `walk` przy `pt` jest też trybem dojścia (access/egress), a `accessEgressType` domyślnie `accessEgressModeToLink` (teleportowane dojście). Plany muszą zawierać `carAvail` (jedno miejsce generowania: `pipeline/plans.py`), a pojazd `car` musi być dostępny wg tej samej reguły.

## 5. Wiersze do manifestu (`data/manifest.csv`, **nie edytowano** — do wklejenia)

```
data/raw/g4/polish_trains.zip,https://mkuran.pl/gtfs/polish_trains.zip,2026-10-17T11:35Z,31133210,18efea6db858577a1b2e841f394d47f182b8a944bd6c19d2ef02b3fe59708449
data/raw/g4/radom_sump_diagnoza_2023.pdf,https://www.radom.pl/wp-content/uploads/2023/07/SUMPGOFR_2022_Raport_Diagnostyczno-Strategiczny_2023.02.28.pdf,2026-10-17T11:37Z,19591914,423bfb8262abac5b8a65508ba0aff8c94e3cc6231b1e39a51fdcf49477cce452
data/raw/g4/bochnia_studium_mobilnosci_cz2.pdf,https://bip.malopolska.pl/e,pobierz,get.html?id=1587047,2026-10-17T11:37Z,9328502,fe794b454e0c13c9294c08b017718fa610db1c178bca9aad46f4e25182bf3323
```

(URL Bochni zawiera przecinki — w CSV wymaga cudzysłowu: `"https://bip.malopolska.pl/e,pobierz,get.html?id=1587047"`. Plik Bochni zapisał mi WebFetch, nie curl; czas pobrania ≈ 2026-10-17T11:37Z.)

## 6. Decyzje dla użytkownika (D17+)

1. **Zakres:** czy G4 w ogóle ruszamy (zmiana zakresu MVP, wymaga wpisu w `docs/projekt/DECISIONS.md`)? Konsekwencja: nowe wejścia (GTFS, `carAvail`), zmiana plans i configu.
2. **Cel kalibracji podziału modalnego:** (a) przedział z Bochni+Radomia dla dom–praca (auto ≈ 61–67%, pieszo 10–12%, rower 3–7%, PT 19–20%), (b) GUS łódzkie wszystkie cele (auto 60%, pieszo 20,5%), (c) szukać dalej (poprosić UM Kutno / Starostwo o SUMP lub KBR, zrobić własną ankietę). Rekomendacja: (a) z jawnym ZAŁOŻENIEM i szerokim przedziałem.
3. **PT — źródło i licencja:** użyć `kutno.zip` (zbiorkom.live, bez licencji) czy poprosić MZK Kutno o oficjalny GTFS? Kolej (feed Kuranowskiego): akceptujesz warunki PLK/KM i dzień referencyjny (np. wtorek 2026-10-20)?
4. **Czy modelować PT w ogóle w tej skali:** w Kutnie PT dom–praca to ~7–20% (Bochnia 20% z busami), a **MZK jest darmowy dla posiadaczy Karty Mieszkańca**. Czy cena = 0 dla wszystkich agentów (ZAŁOŻENIE do udokumentowania)?
5. **Rower: teleportowany czy sieciowy** (rekomendacja: teleportowany; sieciowy wymaga zmiany F2 i pojazdów).
6. **Pieszo jako tryb dom–praca:** tak (teleportowany), z limitem odległości? Bez niego pieszo z Kutna do Warszawy.
7. **`carAvail`:** brak danych lokalnych; skąd rozkład (GUS tabl. 5–7 wg województwa, wskaźnik motoryzacji gminy z BDL)? Wymaga osobnego źródła (nie szukane).
8. **Przyjeżdżający spoza powiatu (D16):** czy mogą zmieniać tryb (np. pociąg z Łodzi do Kutna)? Dziś wjeżdżają autem o godzinie z profilu; PT międzygminny nie ma GTFS poza koleją.
9. **Narzędzie PT:** `transit-from-gtfs` (jest w jarze, zalecane) czy dodać `pt2matsim` (zmiana `pom.xml`).

## 7. Czego nie zweryfikowałem

- Nie sprawdziłem warunków licencyjnych zbiorkom.live (strona „about” nie dała treści) ani PLK API (rejestracja).
- Nie otworzyłem PDF „Dojazdy do pracy w świetle wyników NSP 2021” (~152 MB); wniosek „brak środka transportu” opiera się na opisie GUS i na tym, że nasze pliki NSP go nie mają.
- Kod matsim-libs 2026.0 czytałem przez WebFetch (streszczenia narzędzia), poza `javap`/`unzip` na lokalnym jarze. Przed użyciem w G4: `--help` dla `transit-from-gtfs` i test 2 iteracji.
- Rys. 5.25 (Radom) i wykres 6.2 (Bochnia) zostały odczytane z tekstu PDF — warto raz obejrzeć wzrokowo.

## 8. Weryfikacja odczytu wartości 61–67% (2026-10-18, na zlecenie sesji README)

Strony PDF wyrenderowałem do obrazów i obejrzałem wzrokowo (nie tylko tekst).

- **Bochnia** (`bochnia_studium_mobilnosci_cz2.pdf`, PDF s. 45 = numer drukowany 44, *Wykres 6.2 „Podział zadań przewozowych w motywacji dom–praca”*): samochód osobowy **67%**, autobus miejski 12%, bus 7%, pociąg 1%, rower 3%, pieszo 10%. Odczyt poprawny. Wykres 6.3 (dom–zakupy, ten sam PDF s. 45) to osobna rzecz: auto 69%, pieszo 17%. Ankiety X 2016, miasto 30 051 mieszk.; liczby ankiet nie odczytałem.
- **Radom** (`radom_sump_diagnoza_2023.pdf`, s. 137 = numer drukowany 137, *Rys. 5.25 „… dla Radomia w podróżach obligatoryjnych w roku 2022”*): pieszo 12,03%, **komunikacja indywidualna 61,41%**, zbiorowa 19,09%, rower 7,47%. Kolejność etykiet potwierdzona na wykresie (to zamyka niepewność z sekcji 1b). Zastrzeżenia: (1) „obligatoryjne” = praca **i nauka**, nie sama praca; (2) „indywidualna” to nie tylko samochód (może obejmować pasażera i motocykl); (3) Rys. 5.24 (wszystkie podróże Radomia) to 52,43% indywidualna; (4) ankieta N = 750 dla całego GOFR, nie dla Radomia.
- **Wniosek:** „61–67%” to 61% (Radom, praca+nauka, komunikacja indywidualna) i 67% (Bochnia, tylko dom–praca, samochód). Nie są to wartości tej samej kategorii.

**Źródło dla dojazdów do pracy w łódzkim lub miastach 30–100 tys.:** w tej sesji nie znalazłem żadnego innego niż powyższe dwa (oba spoza łódzkiego, ankiety, bez błędu szacunku) i GUS Mobilność 2024 (łódzkie, wszystkie cele). Szukałem słowami kluczowymi (SUMP/KBR/studium transportowe), więc nie wykluczam istnienia innych dokumentów.

**Status trybów w planie (zgodnie z `docs/research/G4_tryby.md` i `G4_beeline.md`):** badawczo opisane, **niewdrożone** (zakres MVP zamrożony, wymaga decyzji D w `docs/projekt/DECISIONS.md`). Pieszo i rower: proponowane jako trybu teleportowane z `beelineDistanceFactor` ≈ 1,25 i ≈ 1,35 (pomiar na sieci OSM Kutna, `docs/research/G4_beeline.md`); PT: GTFS zbiorkom.live (niejasna licencja, 13 linii) + kolej z `polish_trains.zip`, **odłożone** do decyzji o licencji i źródle GTFS; MZK Kutno jest bezpłatny dla posiadaczy Karty Mieszkańca.
