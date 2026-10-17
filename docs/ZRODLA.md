# ZRODLA: katalog źródeł i tego, co z nich wiemy

Aktualizacja: 2026-10-17. Pliki leżą w `data/raw/` (poza gitem). Pochodzenie każdego pliku (URL, data, sha256) jest w `data/manifest.csv`. Fakty sprawdzone przy starcie projektu są w `FACT_CHECK.md`.

Statusy: **UŻYTE** (w pipeline) · **POBRANE** (sprawdzone, jeszcze nieużyte) · **DO POZYSKANIA** (wiemy, że istnieje) · **DO SPRAWDZENIA** (nie wiemy, czy się nada).

## 1. Ludność i domy

| źródło | status | co daje | ograniczenia | gdzie |
|---|---|---|---|---|
| GUS NSP 2021, ludność w rejonach i obwodach spisowych (`gus/ludnosc_rejony_obwody_nsp2021.xlsx`) | UŻYTE (F3) | 232 obwody Kutna: płeć, ekonomiczne i 10-letnie grupy wieku. Suma 42 255. | Brak krzyżowania płci z wiekiem. Brak pracujących. | D5, `pipeline/demand.py` |
| GUS BREC 2021, geometria obwodów (`brec/AreaStatisticalUnit_10_2021.zip`) i rejonów krajowych (`brec/SU_BREC_2021_REJ.zip`) | UŻYTE (F3, F4) | Granice obwodów i gmin. | Miasta na prawach powiatu mają w BREC kody dzielnic. | D9, D11, `plans.py` |
| OSM, budynki (`osm/lodzkie-261015.osm.pbf`) | UŻYTE (F4) | Budynki mieszkalne jako domy, ważone powierzchnią obrysu. | `building:levels` w gm. Kutno: bloki 84%, ale `yes` (72% budynków) tylko 2%. 9 817 budynków `yes` poza `landuse=residential` nie jest liczonych jako domy (kod R5 je liczy). | D11, G3 |
| GUS siatki NSP 2021 (`g3/gus_grid/`) | POBRANE (G3) | Ludność ogółem w siatce 250 m i 500 m (EPSG:3035) oraz rezydenci w siatce 1 km z płcią i wiekiem. Siatka 250 m w gm. Kutno: 285 komórek, suma 42 052. | Siatka 125 m jest tylko dla miast wojewódzkich. Budynki i mieszkania tylko w 1 km i tylko przez konto w Menedżerze Zasobów. Komórki 1–4 os. są chronione. | G3: kontrola domów |
| BDOT10k, powiat 1002 (`g3/bdot10k/1002_GPKG.zip`, wersja 2025-12-09) | POBRANE (G3) | `OT_BUBD_A`: funkcja budynku i **`LICZBAKONDYGNACJI` (wypełnione w 99,9%)**. W gm. Kutno 5 252 budynki mieszkalne, w powiecie 19 644. Wagi „obrys × kondygnacje” najlepiej odtwarzają siatkę GUS 250 m: masa w złej komórce 8,5 pp wobec 10,3 pp obecnie, korelacja surowej powierzchni 0,93 wobec 0,68. | 39% geometrii z ortofotomapy. Brak liczby mieszkań. 1 450 budynków OSM w Kutnie nie ma odpowiednika w BDOT. | G3: rekomendowane źródło wag |
| GUS statystyczne punkty adresowe (`g2/ADR_NOBC_2026_0_GJ.zip`, wycinek `g2/adr_kutno_2026_0.csv`) | POBRANE (G2) | Punkty adresowe **budynków mieszkalnych** z obwodem spisowym (Kutno: 4 807 punktów). | Nic o podmiotach i pracy. | G3: kontrola |
| Kod R5: `easy-R5/tools/realtime_delay_cities/dasymetric_pop.py` | REFERENCJA | Binarne ważenie dasymetryczne (Mennis 2003): ludność obwodu rozkładana proporcjonalnie do powierzchni obrysów budynków mieszkalnych. Bez kondygnacji (decyzja użytkownika 2026-09-10). Budynki mieszkalne to wszystkie poza listą wykluczeń. | Ta sama metoda co D11, inny dobór budynków. **G3: w Kutnie lista wykluczeń R5 pogarsza zgodność z GUS (10,3 → 11,6 pp)**, bo 79% dodanej powierzchni to wg BDOT budynki niemieszkalne. | G3 |

## 2. Praca i dojazdy

| źródło | status | co daje | ograniczenia | gdzie |
|---|---|---|---|---|
| GUS NSP 2021, tablice rynku pracy (`gus/rynek_pracy_nsp2021_tablice.xlsx`) | UŻYTE (F3) | Wskaźniki zatrudnienia (łódzkie, ekonomiczne grupy wieku). | Tylko województwo. | D5 |
| GUS NSP 2021, macierz przepływów do pracy (`gus/macierz_przeplywow_nsp2021.xlsx`) | UŻYTE (F3) | Przyjeżdżający do gminy Kutno: 8 186 osób. | Tylko najemni. Pomija przepływy < 3 osób i ruch wewnątrz gminy. Miejsce pracy to adres pracodawcy. | D3, D9, D16 |
| GUS, macierz dostępności gmin 2021 (`gus_transport/macierz_dostepnosci_20210331.xlsx`, 261 MB) | POBRANE | Czas przejazdu autem [s], droga [km] i ortodroma między wszystkimi 3 130 jednostkami gmin, plus centroidy WGS84. Wycinek do Kutna: `scenarios/kutno/demand/gus_czas_do_kutna_2021.csv`. Łódź 59 min, Łęczyca 33 min, Warszawa 103 min, Gdańsk 156 min. | Model drogowy GUS (OSM), bez kongestii. Centroid gminy, nie dom. | próg D16 w minutach; walidacja czasów w sieci |
| **BDL P4508** „Pracujący wg siedziby pracy głównej” (`g2/bdl_kutno.json`, API BDL, sprawdzone ręcznie) | POBRANE (G2) | **Kutno: 17 460 (2023), 17 486 (2024), 17 251 (2025).** Rejestry ZUS/KRUS, więc także małe podmioty. Mieszkańcy pracujący gdziekolwiek (P4507): 17 255 (2024). | Liczy według **siedziby płatnika**, nie faktycznego miejsca pracy (ta sama konwencja co macierz NSP). Brak PKD na poziomie gminy. **Model ma 25 732 miejsca pracy, o ok. 47% więcej.** | G2: kotwica sumy |
| BDL P2613 (podmioty REGON wg klas wielkości) i P4500 (pracujący wg PKD, tylko powiat, NSP 2021) (`g2/bdl_podmioty_pkd.json`) | POBRANE (G2) | Kutno 2024: 4 407 podmiotów, w tym 56 w klasie 50–249 i 6 w klasie 250–999. Powiat: przetwórstwo 24,9%, handel 13,3%, rolnictwo 11,6%. | Liczba podmiotów, nie osób. PKD tylko dla powiatu. | G2: kontrola struktury |
| UM Kutno: Kutnowska Strefa Ekonomiczna i Podstrefa ŁSSE (`g2/um_kutno_node52.pdf`, `node176.pdf`) | POBRANE (G2) | Podstrefa: 23 firmy, ok. 2 200 zatrudnionych, lista z powierzchnią działek. | „Ok. 9 000 w strefie” (bez daty) jest sprzeczne z P4508. Nie używać bez wyjaśnienia. | G2: kotwice dużych zakładów |
| GUS „Pracujący w gospodarce narodowej” (mapa miesięczna) | DO SPRAWDZENIA | Także małe podmioty. | **Według gminy zamieszkania**, nie miejsca pracy. Do lokalizacji pracy się nie nadaje. | — |
| REGON (API BIR1.1, darmowy klucz przez e-mail regon_bir@stat.gov.pl) | DO SPRAWDZENIA | Podmioty z adresem i PKD. | Zapytania tylko po REGON/NIP/KRS, bez wyszukiwania po gminie. Strona nie wspomina o klasie zatrudnienia, a dokumentacja (zip) jest nieprzeczytana. | G2: opcjonalna weryfikacja ok. 60 dużych zakładów |

## 3. Czas i tryby podróży

| źródło | status | co daje | ograniczenia | gdzie |
|---|---|---|---|---|
| GBR Gdańsk 2022, Raport 3a, Rys. 46 (`gbr/GBR2022_raport3a.pdf`) | UŻYTE (F5) | Godzinowy rozkład wyjazdów dom-praca. | Metropolia, nie Kutno. | D14 |
| GUS „Mobilność transportowa ludności w Polsce w 2024 r.” (`gus_transport/mobilnosc_…`: pdf, tablice, wykresy) | POBRANE | Badanie ankietowe CAPI/CATI, 16.09–24.11.2024, typowy dzień roboczy (wt–czw), osoby 6+. **Tabl. 13: podróże wg środka transportu i województwa.** Łódzkie (wszystkie cele): pieszo 20,5%, rower 5,2%, samochód 60,1% (kierowca 47,9%, pasażer 12,2%), autobus miejski 7,2%, autobus międzymiastowy 1,4%, kolej 1,3%, jednoślady 0,2% (Polska: 20,9 / 5,0 / 59,8 / 8,3 / 1,4 / 1,3). **Tabl. 1, łódzkie: praca z domu 7,3%, poza domem 87,2%, tryb mieszany 5,5%.** Tabl. 10: podróże dom-praca w łódzkim 730 740 na dzień. | **Tylko województwa**, bez podziału na wielkość miejscowości (w pliku jest arkusz klas miejskich obszarów rynku pracy, do sprawdzenia). **Podział modalny dla wszystkich celów łącznie, nie dla dojazdów do pracy.** Kategorie środków nie są rozłączne („co najmniej jeden etap”). Względne błędy szacunków są w tabl. 20–38. | G4 (cel kalibracji trybów), D6 (obecność w pracy) |
| GUS „Transport – wyniki działalności w 2025 r.” (`gus_transport/transport_wyniki_…`: pdf, zip z tablicami) | POBRANE | Dane z działalności przewoźników: pasażerowie kolei, komunikacji miejskiej i autobusów wg województw, flota pojazdów, drogi. | Brak poziomu miasta i podziału modalnego mieszkańców. Tylko kontekst. | G4 (tło) |
| GTFS Kutno (zbiorkom.live, `gtfs/kutno.zip`) | POBRANE | 12 linii, ważny do 2026-12-31. | Agregator z niejasną licencją. GTFS-RT nieaktualizowany. | G4 |

## 4. Literatura i praktyka MATSim (MUM 2026, `data/raw/mum2026/`)

- **Medina Godoy (Walencja, mobilność UPV, scenariusze awarii PT):**
  - sieć z OSM, PT z GTFS przez gtfs2matsim;
  - tryby car / bike / pt / walk, rower jako tryb sieciowy (`mainMode=car,bicycle`);
  - `SubtourModeChoice` waga 0,1, atrybut `carAvail`, 60 iteracji, innowacja wyłączana przy 0,7;
  - próbka 1–5%, kalibracja tylko podziału modalnego, nie natężeń.
  - Dla nas: wzór minimalnej konfiguracji mode choice w G4.
- **Lannes (Paryż, ekspozycja na zanieczyszczenia):**
  - na skali regionu wielkość próbki prawie nie ma znaczenia;
  - na skali lokalnej 5% daje duży błąd, a 25% ma małą losowość między powtórzeniami.
  - To niezależnie wspiera naszą decyzję o wynikach z 25% (D15).
- **Bell (Newcastle, MATSim → Blender):**
  - pipeline: węzły sieci do współrzędnych sceny (BlenderGIS);
  - eventy (`vehicle enters/leaves traffic`, `entered/left link`) → pozycja każdego pojazdu na każdą klatkę → `vehicleMotions.npz`;
  - w Blenderze jedna siatka punktów aktualizowana handlerem klatki, kształt pojazdu przez Geometry Nodes, render.
  - Przykład z prezentacji: 142 tys. pojazdów. Kodu nie znalazłem publicznie. Lokalnie są Blender 4.3 i 4.4.

## 5. Zebrane w sesjach równoległych G2–G6 (2026-10-17)

Pełne raporty: `docs/research/G2_miejsca_pracy.md`, `G3_domy.md`, `G4_tryby.md`, `G5_walidacja.md`, `G6_blender.md`. Pliki są w `data/raw/g2…g5/`, a sha256 każdego z nich sprawdzone przy dopisywaniu do manifestu.

| źródło | status | co daje | ograniczenia | gdzie |
|---|---|---|---|---|
| **GPR 2025 (GDDKiA)**: DK i DW, `g5/gpr2025/` | POBRANE (G5) | SDRR, SDRDR i SDRL, struktura rodzajowa, dla A1 także kierunkowa. 19 odcinków w sieci, przypisanych do linków (`reports/g5_walidacja/gpr_linki.csv`). Sklęczkowska (DK92) SDRR 9 872, Objazdowa (DK60) 9 341, A1 32–37 tys. poj./dobę (28–34% ciężkich). | Jedna wartość na cały odcinek. Brak godzin. DW bez SDRDR i bez kierunków. Brak ulic miejskich. | G5: cel walidacji |
| **SCPR 2025 (stacje ciągłe GDDKiA)**: `g5/scpr2025/` | POBRANE (G5) | Stacja 14005 Lisica (DK60c, 13 km od Kutna): krzywe godzinowe (tylko jako wykres). Współczynniki tygodniowe i udział godzin szczytowych w roku. | Profil godzinowy wymaga digitalizacji. | G5: profil tła |
| Literatura o ruchu tła (VSP): Ziemke 2019, Lu 2022, Rakow 2024, Ewert 2025 (`g5/lit/`) | POBRANE (G5) | Wzór „agenci external z liczników na granicy” (Open Berlin). | — | G5 |
| Macierz dostępności GUS vs nasza sieć (`reports/g5_walidacja/gus_vs_siec.csv`) | UŻYTE (G5) | 29 gmin: czas swobodny w sieci to mediana 0,76 × czas GUS (ORS), przy długości tras 0,99 × GUS. Sieć jest szybsza niż GUS, więc brak sygnału, że D13 zaniża prędkości. | ORS to też model, nie pomiar. | G5 |
| Bochnia, studium transportowe (2016) i Radom SUMP (2022) (`g4/`) | POBRANE (G4) | Podział modalny **dom–praca** w miastach 30–190 tys.: auto 61–67%, PT 19–20%, pieszo 10–12%, rower 3–7%. | Inne miasta. Wartości odczytane z tekstu wykresów, do weryfikacji wzrokowej. | G4: przedział kalibracji |
| GUS Mobilność 2024, tabl. 14 i 32 | POBRANE (G4) | Brak podziału wg klasy miejscowości oraz brak krzyżowania dom–praca × środek. Błędy względne dla łódzkiego: samochód 3,9%, pieszo 6,8%, rower 16,3%, autobus miejski 10,3%. | — | G4 |
| GTFS kolej, Kuranowski (`g4/polish_trains.zip`) | POBRANE (G4) | PKP IC, ŁKA, KM, PolRegio, KW. Kutno: 180 kursów we wtorek. | Ważny tylko 30 dni od pobrania. Warunki PLK/KM to nie licencja CC. | G4 |
| MZK Kutno | DO POZYSKANIA | Posiadacze Kutnowskiej Karty Mieszkańca jeżdżą bezpłatnie. Część linii skrócona do granicy miasta. | Brak oficjalnego GTFS. Feed zbiorkom.live nie ma licencji. | G4 |
| OSM rower (G4) | POLICZONE | W gm. Kutno ok. 23 km dedykowanej infrastruktury rowerowej (cycleway i path z `bicycle=designated`), 165 km chodników. | — | G4 |
| MATSim 2026 w naszym jarze (G4, `unzip -l`) | SPRAWDZONE | Są: `SubtourModeChoice`, `ChangeSingleTripMode`, `transit-from-gtfs` (contrib application), SwissRailRaptor, contrib bicycle. **Nie ma pt2matsim.** | Opisy opcji pochodzą z WebFetch, więc trzeba je potwierdzić przez `--help` i test 2 iteracji. | G4 |
| Prototyp Blendera (G6) | DZIAŁA | `pipeline/g6_bake.py` przetwarza 06–09 w 12 s (4 822 przejazdy, max 755 pojazdów jednocześnie). `blender/g6_load.py` w Blenderze 4.4: ok. 1 s na klatkę 1280×720, animacja 10 s w 57 s. Test na 3 pojazdach przechodzi. | Pojazdy to sześciany powiększone ×8, bez pasów i bez podkładu. | G6 |

## 6. Konfiguracje referencyjne MATSim (2026-10-17)

| źródło | status | co daje | ograniczenia | gdzie |
|---|---|---|---|---|
| matsim-berlin v6.3 config (`raw.githubusercontent.com/matsim-scenarios/matsim-berlin/6.x/input/v6.3/berlin-v6.3.config.xml`) | SPRAWDZONE (curl) | qsim: `stuckTime` 30, `trafficDynamics` kinematicWaves, `flowCapacityFactor` 0,1 | Inna skala (metropolia). Nie pobrane do `data/raw`. | D18 |
| matsim-kelheim v3.1 config (`raw.githubusercontent.com/matsim-scenarios/matsim-kelheim/master/input/v3.1/kelheim-v3.1-config.xml`) | SPRAWDZONE (curl) | qsim: `stuckTime` 30, kinematicWaves, próbka 25% (małe miasto, najbliższy analog Kutna) | Nie pobrane do `data/raw`. | D18 |
