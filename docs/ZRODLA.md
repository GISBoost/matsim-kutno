# ZRODLA: katalog źródeł i tego, co z nich wiemy

Aktualizacja: 2026-10-17. Pliki leżą w `data/raw/` (poza gitem). Pochodzenie każdego pliku (URL, data, sha256) jest w `data/manifest.csv`. Fakty sprawdzone przy starcie projektu są w `FACT_CHECK.md`.

Statusy: **UŻYTE** (w pipeline) · **POBRANE** (sprawdzone, jeszcze nieużyte) · **DO POZYSKANIA** (wiemy, że istnieje) · **DO SPRAWDZENIA** (nie wiemy, czy się nada).

## 1. Ludność i domy

| źródło | status | co daje | ograniczenia | gdzie |
|---|---|---|---|---|
| GUS NSP 2021, ludność w rejonach i obwodach spisowych (`gus/ludnosc_rejony_obwody_nsp2021.xlsx`) | UŻYTE (F3) | 232 obwody Kutna: płeć, ekonomiczne i 10-letnie grupy wieku. Suma 42 255. | Brak krzyżowania płci z wiekiem. Brak pracujących. | D5, `pipeline/demand.py` |
| GUS BREC 2021, geometria obwodów (`brec/AreaStatisticalUnit_10_2021.zip`) i rejonów krajowych (`brec/SU_BREC_2021_REJ.zip`) | UŻYTE (F3, F4) | Granice obwodów i gmin. | Miasta na prawach powiatu mają w BREC kody dzielnic. | D9, D11, `plans.py` |
| OSM, budynki (`osm/lodzkie-261015.osm.pbf`) | UŻYTE (F4) | Budynki mieszkalne jako domy, ważone powierzchnią obrysu. | `building:levels` w gm. Kutno: bloki 84%, ale `yes` (72% budynków) tylko 2%. 9 817 budynków `yes` poza `landuse=residential` nie jest liczonych jako domy (kod R5 je liczy). | D11, G3 |
| GUS siatki NSP 2021 (rezydenci, budynki i mieszkania; 1 km, katalog wymienia też 125/250/500 m) | DO SPRAWDZENIA | Kontrola rozkładu ludności niezależna od OSM. | Nie wiadomo, które warstwy da się pobrać w 250 m. | Portal Geostatystyczny |
| BDOT10k, budynki (GUGiK, paczki powiatowe shp/gpkg/gml, bezpłatne) | DO SPRAWDZENIA | Urzędowa funkcja budynku (mieszkalny jedno/wielorodzinny). | Nie sprawdziłem, czy jest liczba kondygnacji. | G3 |
| GUS statystyczne punkty adresowe (ATOM `geo.stat.gov.pl/atom-web/atom/ADR`) | DO SPRAWDZENIA | Punkty adresowe powiązane ze statystyką. | Nieznane atrybuty. | G2, G3 |
| Kod R5: `easy-R5/tools/realtime_delay_cities/dasymetric_pop.py` | REFERENCJA | Binarne ważenie dasymetryczne (Mennis 2003): ludność obwodu rozkładana proporcjonalnie do powierzchni obrysów budynków mieszkalnych. Bez kondygnacji (decyzja użytkownika 2026-09-10). Budynki mieszkalne to wszystkie poza listą wykluczeń. | To ta sama metoda co D11. Różni się tylko doborem budynków (lista wykluczeń vs lista typów). | G3 |

## 2. Praca i dojazdy

| źródło | status | co daje | ograniczenia | gdzie |
|---|---|---|---|---|
| GUS NSP 2021, tablice rynku pracy (`gus/rynek_pracy_nsp2021_tablice.xlsx`) | UŻYTE (F3) | Wskaźniki zatrudnienia (łódzkie, ekonomiczne grupy wieku). | Tylko województwo. | D5 |
| GUS NSP 2021, macierz przepływów do pracy (`gus/macierz_przeplywow_nsp2021.xlsx`) | UŻYTE (F3) | Przyjeżdżający do gminy Kutno: 8 186 osób. | Tylko najemni. Pomija przepływy < 3 osób i ruch wewnątrz gminy. Miejsce pracy to adres pracodawcy. | D3, D9, D16 |
| GUS, macierz dostępności gmin 2021 (`gus_transport/macierz_dostepnosci_20210331.xlsx`, 261 MB) | POBRANE | Czas przejazdu autem [s], droga [km] i ortodroma między wszystkimi 3 130 jednostkami gmin, plus centroidy WGS84. Wycinek do Kutna: `scenarios/kutno/demand/gus_czas_do_kutna_2021.csv`. Łódź 59 min, Łęczyca 33 min, Warszawa 103 min, Gdańsk 156 min. | Model drogowy GUS (OSM), bez kongestii. Centroid gminy, nie dom. | próg D16 w minutach; walidacja czasów w sieci |
| BDL GUS, „pracujący” wg gmin | DO POZYSKANIA | Suma kontrolna miejsc pracy w gm. Kutno. | Lokalne tablice zwykle **bez podmiotów do 9 osób** i bez rolników indywidualnych. | G2 |
| GUS „Pracujący w gospodarce narodowej” (mapa miesięczna) | DO SPRAWDZENIA | Także małe podmioty. | **Według gminy zamieszkania**, nie miejsca pracy. Do lokalizacji pracy się nie nadaje. | — |
| REGON (API BIR1.1, darmowy klucz na e-mail) | DO SPRAWDZENIA | Podmioty z adresem i PKD. | API odpowiada na zapytania o pojedyncze podmioty, nie udostępnia całej bazy. Nie potwierdziłem, czy jest klasa zatrudnienia. | G2 |

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
