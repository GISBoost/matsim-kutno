# R3 — krytyczna ocena modelu Kutno i katalog analiz MATSim (2026-10-16)

Źródła oceny:
- **[W]**: moja weryfikacja na danych i outputach F5/F6 (polecenie albo plik podany przy punkcie);
- **[A]**: niezależny agent-recenzent, który czytał repo i literaturę, bez uruchamiania czegokolwiek. Jego tezy sprawdziłem tam, gdzie się dało (dopisek „sprawdzone”);
- **[L]**: literatura lub dokumentacja (lista na końcu);
- **[O]**: ocena bez źródła.

**Werdykt.** Jako test techniczny pipeline'u (cel D2) model jest zrobiony porządnie i zgodnie z dobrą praktyką. Ma jednak dwa błędy merytoryczne i kilka wniosków sformułowanych mocniej, niż pozwalają dane. Mapy kongestii z F5/F6 nie nadają się do interpretacji: odzwierciedlają założenia D6/D7 i niezbiegnięty run, a nie ruch w Kutnie.

---

## 1. Co jest dobrze (zostawić)

| Element | Dlaczego |
|---|---|
| Rejestr decyzji D1–D14, ZAŁOŻENIA w configu, hierarchia źródeł, manifest danych z sha256 | Rzadko spotykana w projektach MATSim przejrzystość pochodzenia każdej liczby [A][O] |
| Testy semantyczne faz (eventy per osoba, 2N nóg, sha256 planów) zamiast „exit 0” | Regresje wychodzą od razu; smoke test w gicie [A] |
| D13: prędkości wg polskich limitów zamiast domyślnych niemieckich z Supersonic | Domyślne 15 km/h na drogach lokalnych to realny, często przeoczany błąd konwersji OSM [A] |
| Zawrotki na granicy + test `motorway_km ≥ 60` | Wykrył i naprawił utratę A1 przez NetworkCleaner. Test zapobiega powrotowi problemu [A] |
| Brak syntetycznych gospodarstw (IPF) | Przy łańcuchu h-w-h bez wyboru środka transportu atrybuty osób nic nie wnoszą. Nie udajemy obserwacji [A] |
| Godziny z GBR odczytane z wektorów PDF | Dokładny odczyt, odtwarzalny skryptem, bez szacowania „na oko” [A][W] |
| Brak TimeAllocationMutator przy godzinach ze źródła | Spójne z D14. Przy samym wyborze trasy domyślny scoring jest nieszkodliwy [A] |
| `flowCapacityFactor` = frakcja próbki | Zgodne z praktyką [L: Horni i in. 2016] |

## 2. Błędy, czyli wyniki złe nawet jako prototyp techniczny

**E1. Przyjeżdżający spoza powiatu startują z granicy o godzinie wyjazdu z domu.** [A, sprawdzone w `pipeline/plans.py`]
- `end_time` pochodzi z profilu GBR (wyjazd z domu), ale agent startuje z linku wjazdowego.
- Dotyczy 2 136 osób przy 100%. Na wjazdach (A1, DK92) i w pracy są za wcześnie o czas dojazdu do granicy (kilkanaście do kilkudziesięciu minut).
- Poprawka: przesunąć `end_time` o czas jazdy od centroidu gminy do linku wjazdowego. Można go przybliżyć odległością w linii prostej × współczynnik krętości ÷ prędkość, jako jawne ZAŁOŻENIE.

**E2. 20 iteracji to nie jest równowaga, a „stabilizacja score” to artefakt.** [A, sprawdzone w configu]
- `fractionOfIterationsToDisableInnovation=0.8` wyłącza ReRoute po iteracji 16. Potem ChangeExpBeta wybiera tylko spośród już istniejących planów, więc score musi się spłaszczyć. Napisałem w F5, że to „stabilizacja”. To był błąd interpretacji.
- Przy ReRoute 0,2 każdy agent dostaje średnio ok. 3 nowe trasy.
- Przesunięcie kolejek z DK92 (F5) na Metalową i Józefów (F6) pasuje do obrazu niezbiegniętego stanu.
- Run 100% trwa 4 min na 20 iteracji, więc 200 iteracji to ok. 40 min.

**E3. Próbka 10% ma `storageCapacityFactor` = 0,1.** [L: FAQ MATSim, sprawdzone]
- FAQ zaleca storage „a bit larger, e.g. (factor)^0.75”, czyli 0,18 przy 10%.
- Przy 0,1 kolejki przy małej próbce są sztucznie krótkie i szybko się zatykają.
- Ben-Dor i in. (2021): poniżej ok. 25% próbki główne statystyki ruchu mogą znacząco odbiegać [L, znany tylko abstrakt].

**E4. Wniosek w F6 „próbka 10% dobrze odwzorowuje 100%” jest za mocny.** [A][W]
- Mediany czasu podróży się zgadzają (16,8 vs 17,3 min), ale:
  - prędkość o 7:00 wynosi 27,4 vs 33,9 km/h,
  - ranking wąskich gardeł jest inny.
- Poprawne sformułowanie: zgodność tylko na poziomie zagregowanych rozkładów. Przy 25 tys. agentów 100% jest tanie, więc 10% zostaje wyłącznie do szybkich testów technicznych.

**E5. Kilkunastu agentów ma dom przypięty do jezdni A1.** [W: `output_activities.csv` × `output_links.csv`, F6]
- MATSim przypina aktywność bez linku do najbliższego linku sieci. 12 osób z domem w budynku OSM trafiło na `motorway` (24 aktywności).
- Dodatkowe 413 osób na motorway to zamierzone wjazdy graniczne (D9).
- Skala jest mała, ale praktyka to przypinanie do podsieci bez motorway, trunk i łącznic [A][O].
- Teza agenta, że duże hale są przyklejone do łącznic: **niepotwierdzona**. Żadna aktywność `work` nie leży na motorway ani na łącznicy [W].

## 3. Uproszczenia ograniczające interpretację (OK w MVP, ale zakaz wniosków o ulicach)

**S1. Brak ruchu tła.** Model nie zawiera:
- tranzytu na A1 i DK92,
- ciężarówek (strefa magazynowa!),
- podróży w innych celach (szkoła, zakupy, załatwianie spraw),
- wyjeżdżających z Kutna (2 669 osób, przeciwny kierunek).

Podróże do pracy to tylko część ruchu w szczycie [O]. Jednocześnie popyt pracowniczy jest zawyżony (S2), więc kierunek błędu na konkretnym linku jest nieznany [A]. Teza „wąskie gardło na Sklęczkowskiej” może być trafna z niewłaściwego powodu.

**S2. Zatrudnienie przeliczane na auto 1:1.** Brakuje czterech współczynników:
- obecność w pracy w przeciętny dzień (urlopy, L4, zmiany, praca zdalna, niepełny etat);
- udział auta (Kutno to węzeł kolejowy, a mediana dojazdu mieszkańców to 3,8 km, więc pieszych i rowerzystów jest sporo);
- liczba osób w samochodzie;
- rolnicy i pracujący w domu, którzy w ogóle nie dojeżdżają.

Szczytowy ruch aut jest więc prawdopodobnie zawyżony o kilkadziesiąt procent [A][O]. To jest D6, świadome, ale w F5/F6 i tak analizowałem kolejki na nazwanych ulicach.

**S3. Niespójne bazy w bilansie F3.** [A, sprawdzone z logiką `demand.py`]
- „Pracujący mieszkańcy” pochodzą z NSP i obejmują też samozatrudnionych oraz rolników. Odejmujemy od nich wyjeżdżających z macierzy, która liczy tylko najemnych. Liczba pracujących w Kutnie jest więc zawyżona.
- Przyjeżdżający (też tylko najemni) są zaniżeni.
- Macierz przypisuje pracę do siedziby firmy, więc część relacji (Łódź, Warszawa) może być fantomowa.
- Kontrola krzyżowa jest dostępna: 25 732 miejsc pracy vs BDL „pracujący” w gminie Kutno (BDL pomija firmy do 9 osób, co zaniża tę liczbę; R2).

**S4. Miejsca pracy ważone powierzchnią obrysu (D7).**
- Magazyn ma o rząd wielkości mniej pracowników na m² niż biuro, szkoła czy szpital, a piętra są pominięte.
- Top 5 budynków dostaje 13% agentów. Wąskie gardło SE jest mechanicznym skutkiem tej wagi, a nie odkryciem [A][W].

**S5. Profil godzin z Gdańska i stałe 8 h pracy.**
- Metropolia ma inny rozkład godzin niż przemysłowe Kutno ze zmianami 6/14/22.
- Stałe 8 h synchronizuje szczyt popołudniowy.
- Seria „praca–dom” z tego samego wykresu GBR może posłużyć jako niezależna kontrola powrotów [A].

**S6. Przepustowości domyślne Supersonic, model kolejkowy bez skrzyżowań.**
- Moja teza z F5, że „1 500 poj./h na pas jest w typowym zakresie”, nie ma źródła [A]. Wlot z sygnalizacją ma realnie mniej.
- Factor 0,8 na prędkości jest arbitralny.
- Brak porównania czasów przejazdu z danymi rzeczywistymi.

**S7. Brak walidacji.** Polska praktyka to GEH < 5 na ≥ 85% punktów pomiarowych [L: Jastrzębski 2016; CUPT ZMR]. Nie mamy ani jednego pomiaru.

**S8. Jeden seed.** Wariancja losowa nie jest znana [A][L: Mersini, Ziemke 2026, abstrakt].

**S9. Dojście piesze do sieci.** 1,2% nóg walk trwa ponad 10 min, maks. 28,5 min. To głównie przyjeżdżający z domów na wsi daleko od dróg w sieci [W]. Wpływ mały, ale zawyża czas podróży.

**Niezweryfikowane:** teza agenta, że przy `stuckTime=10 s` i `removeStuckVehicles=false` pojazdy są przepychane mimo braku miejsca, co maskuje kongestię przy 10%. Ustawienia potwierdzam [W: `output_config.xml`], ale liczby takich przepchnięć nie policzyłem.

## 4. Jakie statystyki można jeszcze policzyć

**Już w jarze, bez dodatkowych zależności.** Contribs `simwrapper` i `application` są w uber-jarze [W]. W `MatsimModelImplementation.java` linia `addOverridingModule(new SimWrapperModule())` jest zakomentowana. Po jej włączeniu run generuje dashboardy (przeglądarka SimWrapper czyta lokalny folder) [L: SimWrapper]:

| Dashboard / analiza | Co daje | Czego wymaga |
|---|---|---|
| `TripDashboard` / `TripAnalysis` | rozkłady odległości, czasów, godzin, macierze OD | nic |
| `TrafficDashboard` / `TrafficAnalysis` | **congestion index** i średnia prędkość per typ drogi i godzina | nic |
| `ODTripDashboard` | macierz podróży między strefami | plik stref (mamy obwody i gminy BREC) |
| `ActivityDashboard`, `DepartureTimeAnalysis`, `StuckAgentDashboard` | gęstość aktywności, godziny wyjazdów, utknięci | nic |
| `TrafficCountsDashboard` / `CountComparisonAnalysis` | porównanie z pomiarami, GEH | plik counts (np. z GPR) |
| `TravelTimeComparisonDashboard` | porównanie czasów z Google, TomTom, HERE, Mapbox | klucz API od użytkownika |
| `NoiseDashboard` / contrib `noise` | hałas drogowy (RLS-90), mapy imisji | nic dodatkowego; wynik zawyżony przez D6 |
| `EmissionsDashboard` / contrib `emissions` | CO₂, NOx, PM | tablice HBEFA (licencja) i typy pojazdów |
| `AccessibilityDashboard` | dostępność miejsc pracy z każdego punktu | POI / miejsca pracy |
| `ImpactAnalysisDashboard` | porównanie scenariuszy (np. przebudowa DK92) | dwa runy |

**Z obecnych outputów, własnym skryptem** [W: kolumny `output_links.csv`, `output_legs.csv`, eventy]:
- **VKT/VHT i średnia prędkość sieci** per godzina i typ drogi, a także opóźnienie w poj.-h (mamy w `link_delay.py`).
- **v/c per link i godzina.** Wolumeny godzinowe z eventów, capacity z sieci.
- **Select-link analysis.** Kto jedzie Sklęczkowską: z jakich gmin i obwodów, do jakich budynków. Od tego zależy, czy wąskie gardło to efekt D7.
- **Izochrony z centrum i dostępność** (czasy z routera MATSim po run).
- **Diagnostyka zbieżności:**
  - zmiana natężeń top-N linków między iteracjami,
  - udział agentów, którzy zmienili trasę,
  - rozrzut między seedami.
- **Linkstats** z MATSim. Dziś nie powstają, bo `writeLinkStatsInterval=50` > 20 iteracji [W]. Wystarczy ustawić np. 10.

## 5. Proponowane dalsze prace (kolejność)

**A. Naprawy (techniczne, bez nowych decyzji zakresu)**

1. **E1:** przesunąć `end_time` przyjeżdżających z wjazdów o szacowany czas dojazdu do granicy.
2. **E2/E3:**
   - run 100% ze 150–200 iteracjami;
   - kryterium zbieżności na natężeniach i czasach, a nie na score;
   - 3 seedy;
   - dla 10% `storageCapacityFactor=0.18`;
   - włączyć `writeLinkStatsInterval`.
3. **E5:** przypinać aktywności do podsieci bez motorway, trunk i łącznic.
4. **Raporty:** przeformułować wnioski F5/F6 („10% ≈ 100%”, „stabilizacja score”, ranking wąskich gardeł). Dopisane jako korekty w `reports/f5_run_10pct/f5_run.md` i `reports/f6_run_100pct/f6_run.md`.
5. **Narzędzia:**
   - włączyć `SimWrapperModule` (TrafficDashboard, TripDashboard);
   - select-link dla DK92.

**B. Popyt (wymaga nowych wpisów w DECISIONS)**

6. **S4:** wagi miejsc pracy wg typu budynku × liczba kondygnacji, potem REGON z klasą zatrudnienia. Kontrola sumy względem BDL (R2).
7. **S2:**
   - współczynnik obecności w pracy i udział auta jako jawne ZAŁOŻENIA z wariantami. Zmienia D6, więc to decyzja użytkownika.
   - Źródła do sprawdzenia: KBR innych miast średniej wielkości, GUS BAEL, praca zdalna.
8. **S3:** spójna baza bilansu, czyli najemni z najemnymi albo jawna korekta.

**C. Kalibracja i walidacja (wyjście poza MVP, D2)**

9. **S1:** ruch tła na A1 i DK92 z GPR 2020/21 (SDR + profil dobowy jako agenci tranzytowi) albo macierze ZMR CUPT (licencja).
10. **S7:**
    - punkty pomiarowe z GPR i ewentualnie pomiary miasta lub ZDP → `CountComparisonAnalysis` + GEH;
    - porównanie czasów przejazdu z API (wymaga klucza i zgody użytkownika).
11. Dopiero potem mapy kongestii jako wynik, a następnie przeniesienie metody na Łódź.

---

## Źródła

- Horni, Nagel, Axhausen (red.) 2016, *The Multi-Agent Transport Simulation MATSim*, Ubiquity Press, https://doi.org/10.5334/baw
- FAQ MATSim o `storageCapacityFactor` (mirror wiki, treść sprawdzona): https://github-wiki-see.page/m/matsim-org/matsim-code-examples/wiki/faq-48955430
- Ben-Dor, Ben-Elia, Benenson 2021, *Population downscaling in multi-agent transportation simulations*, SIMPAT 108 (abstrakt): https://engineering.tau.ac.il/sites/engineering.tau.ac.il/files/media_server/Engineering/ShlomoShmeltzer/Golan%20Ben%20Dor_2021_Population%20downscaling%20in%20multi-agent%20transportation%20simulations_%20A%20review%20and%20case%20study.pdf
- Llorca, Moeckel 2019, Procedia CS 151 (nieprzeczytane w całości): https://doi.org/10.1016/j.procs.2019.04.106
- Mersini, Ziemke 2026, Procedia CS 280 (abstrakt): https://trid.trb.org/View/2710974
- Ziemke, Kaddoura, Nagel 2019, The MATSim Open Berlin Scenario: https://doi.org/10.1016/j.procs.2019.04.120
- Charlton, Sana 2022, SimWrapper: https://svn.vsp.tu-berlin.de/repos/public-svn/publications/vspwp/2022/22-21/CharltonSana2022SimWrapper.pdf
- MATSim UM 2025, dashboardy SimWrapper: https://matsim.org/conferences/mum2025/abstracts/MUM25_paper_22.pdf
- MATSim install (SimWrapper jedną linią): https://matsim.org/install/
- Jastrzębski 2016, GEH w polskich modelach, TMiR: https://yadda.icm.edu.pl/baztech/element/bwmeta1.element.baztech-8786afa3-1ab2-4843-ab2c-52409c928a66/c/TMiR_6_2016_Jastrzebski.pdf
- CUPT, Zintegrowany Model Ruchu: https://zmr.cupt.gov.pl/
- GDDKiA, GPR 2020/21: https://www.gov.pl/web/gddkia/wyniki-generalnego-pomiaru-ruchu-202021-na-drogach-wojewodzkich
