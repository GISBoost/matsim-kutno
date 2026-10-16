# Budowa symulacji transportu opartej na agentach w MATSim dla Łodzi — etap badawczo-kierunkowy (wersja 2)

## TL;DR
- **Najbardziej realistyczna ścieżka dla Łodzi to adaptacja otwartego pipeline'u eqasim/synpp (Hörl & Balac) do danych polskich**: sieć z OSM przez pt2matsim, rozkłady z oficjalnego GTFS ZDiT Łódź, populacja syntetyczna z NSP 2021, a łańcuchy aktywności — tymczasowo z zewnętrznego badania ruchu, docelowo z KBR Łódź (realizowanego w latach 2026–2027).
- **Problem granularności OD jest rozwiązywalny — ale przez *generowanie*, nie mierzenie wewnątrzmiejskich przepływów.** Macierz dojazdów GUS jest międzygminna (Łódź = jedna gmina, więc jej wnętrze jest „niewidoczne"). Nie istnieje otwarta macierz OD wewnątrz Łodzi. Zamiast niej buduje się przepływy wewnątrzmiejskie z: (a) rozmieszczenia domów w **drobnej geografii GUS** (rejony statystyczne / obwody spisowe — BREC — oraz siatka 1 km / 125 m), (b) rozmieszczenia miejsc pracy z **rejestru REGON** (adresy jednostek lokalnych, branża PKD, klasa zatrudnienia), (c) rozkładu długości podróży z badania ruchu, (d) modelu wyboru celu (destination choice / grawitacyjny). **To jest właściwe miejsce dla Twoich „alternatywnych metod"**: Deep Gravity i dane FCD z TomTom służą tu jako generatory/walidatory wewnątrzmiejskiego OD, a nie jako podstawa populacji.
- **Synteza populacji to najtrudniejszy i najważniejszy krok** — dwuetapowy: najpierw „kto i gdzie mieszka" (agenci + cechy, metody IPF / próbkowanie / optymalizacja / modele generatywne), potem „co robią i dokąd jadą" (łańcuchy aktywności + lokalizacje przez statistical matching i destination choice). Sekcja 4 zawiera rozszerzone wyjaśnienie i ścieżkę dalszego uczenia się.
- **Wizualizacja open-source jest w pełni pokryta**: **SimWrapper** (VSP TU Berlin, przeglądarkowy, natywny dla MATSim, bez kodowania — konfiguracja w YAML) plus Twój własny warsztat — **QGIS z kontrolerem czasu** (animacja temporalna, którą już robisz z `@map_start_time`). Komercyjnej VIA można uniknąć.
- **Sprzęt jest wystarczający**: desktop z RTX 4070 i 32 GB RAM w zupełności wystarczy dla Łodzi na próbce 1–10%; GPU przyda się dopiero w metodach uczenia głębokiego (Deep Gravity), nie w rdzeniu MATSim.

## Najważniejsze ustalenia

1. **MATSim to dojrzały, otwartoźródłowy framework w Javie** oparty na ko-ewolucyjnej pętli iteracyjnej (plany → scoring → replanning → mobsim/QSim). Aktualne wydania: linia 2025.x/2026.x; wymaga JDK (Java 17+), Mavena i głównie dużo RAM.

2. **Ekosystem narzędzi jest gotowy do adaptacji**: `pt2matsim` (OSM+GTFS → sieć i rozkład), `eqasim`/`synpp` (pipeline populacji, sprawdzony m.in. w Ústí nad Labem — najbliższy metodologicznie precedens środkowoeuropejski), `SimWrapper` (wizualizacja).

3. **Polska ma wyjątkowo dobre otwarte dane** — i, co kluczowe dla Twojej uwagi, **dane o drobnej granularności przestrzennej**: geografia BREC (≈34 tys. rejonów statystycznych ≤2700 osób, ≈183 tys. obwodów spisowych ≤500 osób) oraz siatka 1 km / 125 m dają rozdzielczość *wewnątrz* miasta; rejestr REGON (≈4,3 mln podmiotów z adresami) daje rozmieszczenie miejsc pracy.

4. **Twoje „alternatywne metody" mają realne miejsce** — nie jako fundament, lecz jako warstwa generowania/walidacji wewnątrzmiejskiego OD: Deep Gravity operuje na poziomie drobnych oczek (nadaje się do przepływów wewnątrz miasta), a dane FCD/probe z TomTom to Twój unikalny atut (rzeczywiste obserwowane przepływy i prędkości) — z zastrzeżeniem licencyjnym.

5. **Metoda „elektoralna" (obwody wyborcze)** jest obarczona błędem ekologicznym; lepiej jako warstwa pomocnicza/badawcza (np. profilowanie postaw wobec mobilności) niż podstawa populacji — zwłaszcza że BREC daje twarde dane demograficzne w drobniejszym i czystszym ujęciu.

## Szczegóły

### CZĘŚĆ 1 — MATSim: fundamenty i działanie

**Czym jest MATSim.** Otwartoźródłowy framework w Javie (ok. 2006, ETH Zurich + TU Berlin). Podręcznik referencyjny — *The Multi-Agent Transport Simulation MATSim* (red. Horni, Nagel, Axhausen, Ubiquity Press 2016, DOI 10.5334/baw, CC-BY, za darmo na matsim.org/the-book/) — to podstawowe źródło. Paradygmat behawioralny: ruch to konsekwencja decyzji pojedynczych syntetycznych podróżnych realizujących plan dnia.

**Pętla ko-ewolucyjna** (rdzeń) — trzy kroki w iteracjach:
- **Mobsim / QSim** — wykonanie planów w symulacji ruchu (domyślnie mezoskopowy model kolejkowy na łączach). Szybszy silnik **Hermes** (z SBB) daje ok. 2,5× przyspieszenie.
- **Scoring** — ocena planów funkcją użyteczności (Charypar-Nagel): nagroda za czas na aktywnościach, kary za czas/koszt podróży i spóźnienia.
- **Replanning** — część agentów mutuje plany (trasa, czas, środek transportu — mode choice), reszta wybiera wg score. Zbiór planów agenta to jego „choice set".

Zbieżność: gdy średni score się stabilizuje; typowo **250+ iteracji** (bywa 500).

**Kluczowe pliki wejściowe** (XML, zwykle .xml.gz):
- **network.xml** — sieć drogowa (węzły + łącza z przepustowością, prędkością swobodną, liczbą pasów, dozwolonymi środkami). Wymaga **układu rzutowanego w metrach** (Polska: EPSG:2180 / PUWG 1992).
- **plans.xml / population.xml** — populacja: każdy `person` ma plan = sekwencja `activity` (dom, praca, szkoła, zakupy — z lokalizacją i czasem) przeplatanych `leg` (podróżami).
- **transitSchedule.xml** + **transitVehicles.xml** — rozkład i flota transportu zbiorowego.
- **facilities.xml** (opcjonalny) — obiekty aktywności (miejsca pracy, sklepy, szkoły).
- **config.xml** — plik sterujący.

**Struktura config.xml (lekko — do rozwinięcia później).** Zbiór modułów: `network`, `plans`, `controler` (liczba iteracji, katalog wyjściowy), `qsim` (m.in. `flowCapacityFactor`/`storageCapacityFactor` przy próbkowaniu populacji), `scoring`/`planCalcScore` (parametry użyteczności per aktywność i środek), `replanning`/`strategy` (strategie mutacji i ich wagi), `global` (układ współrzędnych, wątki, ziarno losowe). Ustalone ziarno → reprodukowalność.

**Pliki wyjściowe i analiza**: `output/` z m.in. `output_events.xml.gz` (strumień wszystkich zdarzeń — podstawa analiz), `output_plans.xml.gz`, statystyki score per iteracja, `ITERS/`. Analiza: udziały modalne, czasy/odległości podróży, obciążenie łączy, napełnienie linii TZ.

**Ekosystem / przygotowanie danych**:
- **pt2matsim** (matsim-org/pt2matsim) — sieć i zmapowany rozkład z OSM + GTFS (`OsmMultimodalNetworkConverter`, `Gtfs2TransitSchedule`, `PublicTransitMapper`).
- **GTFS2MATSim** — alternatywny konwerter GTFS.
- wbudowany **OSM network reader** w matsim-libs.
- **eqasim/synpp** — do populacji (Część 2 i 4).

**Stack i sprzęt**:
- Java: JDK (Java 17+ dla najnowszych wydań); Maven; start: `matsim-example-project` (import jako projekt Maven, uruchomienie `MATSimGUI`).
- RAM to główne wąskie gardło: duże scenariusze (100 tys.+ agentów) — 16–32 GB; bardzo duże (1 mln+) — 50+ GB. Łódź (≈640–670 tys. mieszkańców) na próbce 1–10% zmieści się w desktopie z 32 GB.
- GPU (RTX 4070) **nie jest używane** przez rdzeń MATSim — przyda się dopiero w Deep Gravity/Imagery2Flow.
- **Downscaling**: symulacja próbki (1–25%) ze skalowaniem przepustowości (`flowCapacityFactor`, `storageCapacityFactor`).

### CZĘŚĆ 2 — Metody pozyskania danych o popycie i populacji: analiza porównawcza

> **Ważna zmiana ramy (Twoja uwaga nr 1).** Poniższe metody należy czytać przez pryzmat problemu granularności: macierz dojazdów GUS jest międzygminna, więc dla wnętrza Łodzi trzeba przepływy *wygenerować*. Metody satelitarne i dane operatorskie/FCD to właśnie narzędzia do drobnego OD — nie do budowy populacji. Szczegóły źródeł polskich w Części 3, mechanizm generowania OD w Części 4.

#### 2.1. Model mobilności z obrazów satelitarnych (Nature)
Dwa prawdopodobne tropy:
- **Deep Gravity** — Simini, Barlacchi, Luca, Pappalardo, *A Deep Gravity model for mobility flows generation*, **Nature Communications** 12:6576 (2021), DOI 10.1038/s41467-021-26752-4. Generuje **prawdopodobieństwa przepływów (macierze OD)** między jednostkami przestrzennymi z otwartych cech (użytkowanie terenu, sieć drogowa, POI z OSM) i sieci neuronowych. Kod: **github.com/scikit-mobility/DeepGravity** (PyTorch, przy `scikit-mobility`). Testowany na Anglii, Włoszech, stanie Nowy Jork.
- **Imagery2Flow** — *Predicting human mobility flows in cities using deep learning on satellite imagery*, **Nature Communications** 16 (2025), DOI 10.1038/s41467-025-65373-z. Przewiduje OD z obrazów satelitarnych 10–30 m przez grafowe sieci neuronowe.

**Ocena dla Łodzi (przewartościowana w świetle Twojej uwagi)**: **te metody są ważniejsze, niż sugerowała pierwsza wersja — właśnie ze względu na granularność.** Deep Gravity operuje na dowolnej teselacji (np. oczkach siatki albo obwodach spisowych), więc **potrafi wyprodukować przepływy *wewnątrz* miasta**, których macierz międzygminna GUS nie pokazuje. Nie zastępuje jednak syntezy populacji — daje macierz OD, nie osoby z łańcuchami aktywności. Do kalibracji/treningu potrzebuje „ground truth" o rzeczywistych przepływach; naturalne źródła w Polsce to macierz dojazdów GUS (dla szkieletu międzygminnego) oraz — jeśli uzyskasz dostęp — dane FCD TomTom (dla przepływów wewnątrzmiejskich). **Werdykt**: włącz do pipeline'u jako *opcjonalny generator/walidator wewnątrzmiejskiego OD* na etapie po MVP; kod jest otwarty i reużywalny. To też mocny wątek doktorski (GIS + ML).

#### 2.2. Paryż / Île-de-France — eqasim (Hörl & Balac) na danych INSEE
Wzorcowy, w pełni otwarty scenariusz. Referencje: Hörl & Balac, *Synthetic population and travel demand for Paris and Île-de-France based on open and publicly available data*, **Transportation Research Part C** 130 (2021) 103291; oraz „Data in Brief" 39 (2021) 107622. Kod: **github.com/eqasim-org/ile-de-france** i **github.com/eqasim-org/synpp**.

**Metodologia** (do zaadaptowania):
- **Dane wejściowe** (i ich polskie odpowiedniki): spis (próbka ~30% ważona przez INSEE → **NSP 2021 / BREC / siatka GUS**), przepływy dom–praca/szkoła (RP-MOBPRO/MOBSCO → **macierz dojazdów GUS**), dochody (FiLoSoFi → BDL/ubóstwo BDL), spis usług/obiektów (BPE → **REGON + BDOT10k + POI OSM**), krajowe/regionalne badanie podróży (**ENTD/EGT → KBR Łódź 2026–2027, tymczasowo KBR Wrocław/krajowe**), strefy IRIS (→ **rejony statystyczne BREC**), rejestr firm (SIRENE → **REGON**), baza adresowa (BD-TOPO/IGN → **punkty adresowe PRG**).
- **Synteza populacji**: przy wysokim wskaźniku próbkowania spisu — **bezpośrednie próbkowanie** ważone liczbą ludności; alternatywy: **IPF** i **statistical matching**.
- **Aktywności**: łańcuch dnia przypisywany przez **statistical matching** do rekordów badania podróży wg cech (wiek, płeć…).
- **Lokalizacja aktywności**: dom losowany w strefie; praca/szkoła przypisywane tak, by odtworzyć macierz dojazdów, z wagą wg liczby zatrudnionych i docelowej długości dojazdu.

Precedens środkowoeuropejski: **Ústí nad Labem** (Applied Sciences 12(19):10032, 2022) — najbliższy metodologicznie wzorzec adaptacji dla kraju z danymi spisowymi i bez bogatego lokalnego badania podróży.

**Ocena dla Łodzi**: **najwyższa jakość i rekomendowany szkielet.** Główna luka: brak polskiego odpowiednika ENTD/EGT do czasu KBR Łódź.

#### 2.3. Aleksandria (Egipt) — dane Meta/Facebook
Praca: *Using Social Media Data to Construct an Agent-Based Model in a Data-Scarce Environment: A Case Study of Alexandria, Egypt*, **Journal of Urban Technology** 33(1), 2025 (DOI 10.1080/10630732.2025.2546785). Metoda dla środowisk ubogich w dane: OSM (sieć) + dane Meta + uzupełnianie braków (lokalizacje, środki, aktywności) technikami randomizacji. Produkty Meta: **HRSL** (gęstość ~30 m) i **Movement Range Maps** (mobilność z okresu COVID).

**Ocena dla Łodzi**: metoda powstała, bo Egipt **nie ma** dobrych danych spisowych. **Polska ma dane lepsze niż Meta.** HRSL dla Polski istnieje (HDX, baza 2020, CC-BY), ale statyczny i **nieaktualizowany od 2024**; produkty mobilnościowe Meta wygaszone (~kwiecień 2025), portal Data for Good zwinięty. **Wniosek**: dla Łodzi zbędna. Aktualne otwarte substytuty gęstości: **Kontur Population (H3 400 m)** i **GHS-POP (JRC)**.

#### 2.4. Pomysł własny — obwody wyborcze (PKW) jako proxy demograficzne
PKW/KBW publikuje wyniki na poziomie **obwodu głosowania** (serwis „Dane Wyborcze"). Kusi, by wnioskować z nich o profilu społeczno-ekonomicznym małych obszarów.

**Ograniczenia**: **błąd ekologiczny** (z agregatów nie wolno wnioskować o jednostkach); **niedopasowanie geometrii** (granice obwodów ≠ BREC ≠ siatka GUS); **selekcja** (głosujący ≠ populacja, zwłaszcza wg wieku); **nadmiarowość** (BREC i tak daje twarde wiek/płeć w drobniejszym ujęciu).

**Werdykt**: jako podstawa populacji — **niezalecane**. Jako **warstwa pomocnicza/walidacyjna albo wątek badawczy** (np. korelacja postaw wobec mobilności z wynikami wyborów) — dopuszczalne i oryginalne, pod warunkiem jawnego adresowania błędu ekologicznego. „Na później", nie na fundament.

#### Tabela porównawcza (skrót)
- **eqasim/INSEE→GUS**: dane w PL bardzo dobre; trudność średnia/wysoka; jakość najwyższa; licencje otwarte; **realność wysoka — rekomendowana**.
- **Satelity/Deep Gravity**: dane dobre (OSM+GUS+FCD jako trening); trudność wysoka (ML); jakość dobra **dla wewnątrzmiejskiego OD**; realność jako generator/walidator OD po MVP.
- **Meta/Aleksandria**: HRSL PL statyczny/wygaszany; jakość gorsza niż GUS; realność — zbędna dla PL.
- **Obwody wyborcze**: dane bardzo dobre (PKW); jakość niska (błąd ekologiczny); realność — tylko pomocniczo/walidacyjnie.

### CZĘŚĆ 3 — Polskie źródła danych (krytyczne) — z naciskiem na granularność

> **Rdzeń Twojej uwagi nr 1.** Poniżej rozdzielam trzy poziomy: (A) szkielet międzygminny OD, (B) drobna geografia dla domów i demografii *wewnątrz* miasta, (C) rozmieszczenie miejsc pracy. Dopiero razem dają wewnątrzmiejską rozdzielczość.

**(A) Szkielet międzygminny OD**
- **GUS „dojazdy do pracy" (macierz przepływów) NSP 2021** — międzygminna macierz dom–praca z rejestrów administracyjnych (dane podatkowe MF + ZUS), z charakterystyką wg płci i wieku; XLSX (~2,78 MB, Ośrodek Statystyki Miast US Poznań); próg poufności (przepływy międzygminne >9 osób). **Ograniczenie, które słusznie wskazałeś: Łódź to jedna gmina — macierz pokazuje tylko wjazdy/wyjazdy przez granicę miasta, nie ruch wewnątrz.** To „szkielet zewnętrzny" scenariusza.
- **GUS macierz dostępności** — odległości (w linii prostej i drogowe) oraz czasy przejazdu między gminami (stany na 2016 i 2021). Do parametryzacji i walidacji.
- **GPR (Generalny Pomiar Ruchu)** — natężenia na drogach krajowych/wojewódzkich (co 5 lat) — do walidacji obciążeń.

**(B) Drobna geografia — domy i demografia WEWNĄTRZ miasta (rozwiązanie problemu granularności)**
- **BREC — rejony statystyczne i obwody spisowe (GUS)**: to jest brakujący element. Obwód spisowy obejmuje obszar zamieszkały przez **nie więcej niż 500 osób** (≤200 mieszkań); w Polsce jest ich **≈182,8 tys.** Rejon statystyczny to agregat do 9 obwodów, **≤2700 osób** (≤999 mieszkań); jest ich **≈34,3 tys.** Granice są dostosowane do podziału administracyjnego i spójne z obrębami ewidencyjnymi. **Dla Łodzi oznacza to setki jednostek wewnątrz miasta** — właśnie tej rozdzielczości potrzebujesz do rozmieszczenia domów i przypisania cech demograficznych. Dostęp: **usługa INSPIRE ATOM** dla tematu „jednostki statystyczne" (feed `geo.stat.gov.pl/.../atom/SU`, zbiory `SU_BREC_*_OBW`/`_REJ`, formaty GML i SHP) oraz WMS/WFS Portalu Geostatystycznego; dane demograficzne (ludność) przypisane do BREC są udostępniane w temacie „rozmieszczenie ludności". To jest poziom, na którym powinna działać synteza populacji — **nie gmina, lecz obwód/rejon spisowy**.
- **Siatka GUS 1 km / 125 m (NSP 2021)** — ludność (i osobno budynki/mieszkania) w oczkach; komplementarna do BREC, wygodna do losowania lokalizacji domów. Dostęp: ATOM „rozmieszczenie ludności" (feed `.../atom/PD`), Portal Geostatystyczny. Uwaga: część oczek/obwodów z małą liczbą ludności ma wartości ukryte (tajemnica statystyczna) — wymaga obsługi w kodzie.
- **Punkty adresowe PRG (GUGiK)** — precyzyjna lokalizacja budynków mieszkalnych (masz doświadczenie z ~8,2 mln punktów). Pozwalają „posadzić" domy w konkretnych adresach wewnątrz obwodu. Odpowiednik BD-TOPO/IGN z eqasim.

**(C) Rozmieszczenie miejsc pracy — cele podróży służbowych WEWNĄTRZ miasta**
- **Rejestr REGON (GUS)** — Krajowy Rejestr Urzędowy Podmiotów Gospodarki Narodowej: **jawny, bezpłatny, ≈4,3 mln podmiotów**, z **adresem prowadzenia działalności (jednostki lokalnej)**, kodem branży **PKD**, formą prawną. Kluczowe pojęcie: **jednostka lokalna** = wyodrębniony adresowo zakład/oddział, gdzie prowadzona jest działalność — czyli faktyczne *miejsce pracy*, nie tylko siedziba. To jest brakująca warstwa „gdzie są miejsca pracy" wewnątrz Łodzi. Dostęp: wyszukiwarka REGON oraz **API BIR** (usługa sieciowa GUS) — nadaje się do masowego geokodowania. Uzupełnienie: **BDL „pracujący"** (liczba pracujących per gmina/sekcja PKD — do kalibracji sum brzegowych) oraz POI/landuse z **OSM** i **BDOT10k** (szkoły, uczelnie, handel — cele aktywności innych niż praca).

**Pozostałe źródła**
- **OpenStreetMap** — sieć drogowa (pokrycie Łodzi bardzo dobre) przez pt2matsim.
- **GTFS Łódź** — oficjalny feed: organizator **ZDiT**, publikacja przez `otwarte.miasto.lodz.pl` oraz KPD **dane.gov.pl** (dataset 1803: statyczny GTFS + GTFS-RT). Mirrory: `cdn.zbiorkom.live/gtfs/lodz.zip`, `przyjazdy.pl/latest/lodz.zip`. **Uwaga**: `mpk.lodz.pl/rozklady/...` to rozkłady HTML objęte prawem autorskim MPK, **nie** otwarty GTFS. Licencję potwierdź w `feed_info.txt` i metadanych dane.gov.pl (etykieta „MIT" z Transitland to prawdopodobnie uproszczenie agregatora).
- **BDOT10k, PRG, punkty adresowe (GUGiK)** — geoportal.gov.pl / `integracja.gugik.gov.pl` (paczki per powiat wg TERYT) lub wtyczka QGIS **„Pobieracz danych GUGiK"**. Otwarte, bezpłatne.
- **GHS-POP (JRC), Kontur Population, WorldPop** — otwarte, aktualne siatki populacji (dobre dla obszaru funkcjonalnego/podmiejskiego, uzupełnienie siatki GUS). Projekt **Creario** (Rieser, MUM 2025) buduje modele MATSim „dla dowolnego miejsca" z GHSL+WorldPop — szybki starter.
- **GUS — statystyki eksperymentalne / big data**: projekt **TranStat** (Gospostrateg) — „inteligentny system produkcji statystyk transportu drogowego… z wykorzystaniem wielkich wolumenów danych" — sygnalizuje, że GUS pracuje nad transportem opartym na big data, ale gotowych, otwartych, drobnych macierzy OD z telefonii **na razie nie publikuje**. Warto śledzić.
- **Dane FCD/probe z TomTom (Twój unikalny atut)** — rzeczywiste, wewnątrzmiejskie przepływy i prędkości (m.in. Flow Segment Data, Origin-Destination Analysis). To potencjalnie **najlepsze dostępne źródło wewnątrzmiejskiego OD i walidacji prędkości swobodnych sieci** — jakościowo powyżej wszystkiego otwartego. **Zastrzeżenie**: licencja/warunki użycia komercyjne; do projektu otwartego/naukowego wymaga świadomej decyzji o tym, co można opublikować, a co zostaje jako wewnętrzna walidacja. Rozważ jako osobny, wydzielony wątek (i ewentualny wyróżnik konkurencyjny w kontekście doktoratu/publikacji).

### CZĘŚĆ 4 — Pipeline i synteza populacji: od surowych danych do scenariusza

#### 4.0. Ogólna architektura pipeline'u
1. **Sieć z OSM** → pt2matsim → reprojekcja EPSG:2180, uproszczenie łączy.
2. **Rozkład TZ z GTFS** ZDiT → pt2matsim (`Gtfs2TransitSchedule` + `PublicTransitMapper`); wspólny układ rzutowany (GTFS jest w WGS84 — transformacja).
3. **Synteza populacji** (rdzeń — punkt 4.1).
4. **Generowanie wewnątrzmiejskiego OD i planów początkowych** (punkt 4.2).
5. **Konfiguracja i iteracje** → config.xml, 250+ iteracji na próbce (start 1%).
6. **Analiza i wizualizacja** → events → udziały modalne, obciążenia; walidacja z GPR/ZDiT/FCD; wizualizacja (punkt 4.3).

#### 4.1. Synteza populacji — najtrudniejszy krok (rozszerzenie — Twoja uwaga nr 2)

Synteza populacji to stworzenie „sztucznego spisu": listy osób i gospodarstw, których **łączne statystyki zgadzają się z danymi GUS**, a które jednocześnie są na tyle zróżnicowane, że oddają realną heterogeniczność mieszkańców. To dwa odrębne podproblemy — myl się je nagminnie, a to źródło większości błędów:

**Etap A — KTO i GDZIE mieszka (populacja + atrybuty + lokalizacja domu).**
Cel: wygenerować agentów z cechami (wiek, płeć, status na rynku pracy, wielkość gospodarstwa, ewentualnie dochód, posiadanie auta) i przypisać im miejsce zamieszkania **na poziomie BREC / oczka siatki**, nie gminy. Metody:
- **IPF (iterative proportional fitting)** — iteracyjne „dociąganie" wielowymiarowej tabeli, aż jej sumy brzegowe zgodzą się z zadanymi marginesami (np. liczba osób danego wieku i płci w rejonie statystycznym). Wymaga „ziarna" (tabeli wspólnej struktury cech) + marginesów per jednostka. Wynik trzeba **zintegeryzować** (wagi ułamkowe → cali ludzie); jakość zależy od metody zaokrąglenia.
- **Próbkowanie z mikrodanych (sample-based expansion)** — losowanie rzeczywistych rekordów z próbki spisowej z wagami, aż odtworzymy marginesy (podejście eqasim, gdy próbka spisu jest duża). Problem dla Polski: **publiczna próbka mikrodanych NSP 2021 nie jest tak dostępna jak francuska** — trzeba oprzeć się na marginesach BDL/BREC + ziarnie z innego źródła (np. mikrodane z badań budżetów gospodarstw, zagregaty BDL) albo wystąpić do GUS o dane jednostkowe.
- **Optymalizacja kombinatoryczna / simulated annealing** — dobór podzbioru rekordów minimalizujący rozbieżność z marginesami; dobra, gdy marginesów jest dużo.
- **Modele generatywne (nowszy nurt)** — sieci bayesowskie, VAE/GAN do generowania rekordów populacji; przydatne przy wielu skorelowanych atrybutach i rzadkich kombinacjach. To naturalny most do Twoich kompetencji ML (i lokalnego LLM/GPU).

**Etap B — CO robią i DOKĄD jadą (łańcuchy aktywności + lokalizacje celów).**
Cel: nadać każdemu agentowi realistyczny plan dnia (np. dom→praca→zakupy→dom, z czasami) i „posadzić" cele w przestrzeni.
- **Łańcuchy aktywności** — przypisywane przez **statistical matching**: dla agenta o danych cechach losujemy dzienny wzorzec podróży z rekordu **badania ruchu** o podobnych cechach. **To jest miejsce, gdzie brak KBR Łódź boli najbardziej** — do 2026–2027 trzeba pożyczyć wzorce (KBR Wrocław 2024 lub badanie krajowe) i jawnie zaznaczyć to jako ograniczenie.
- **Lokalizacja celów (destination choice)** — dom już mamy z Etapu A; pracę/szkołę/zakupy przypisujemy z puli obiektów (**REGON** dla pracy, **BDOT10k/OSM** dla usług i szkół) modelem wyboru celu ważonym atrakcyjnością (liczba miejsc pracy) i odległością/czasem, tak by **odtworzyć rozkład długości podróży z badania ruchu** oraz **szkielet międzygminny z macierzy GUS**.

**I tu domyka się problem granularności (uwaga nr 1):** wewnątrzmiejskie OD **nie jest wczytywane z gotowej macierzy** — ono **emerguje** z Etapu A × Etapu B: rozmieszczenie domów (BREC) × rozmieszczenie miejsc pracy (REGON) × rozkład długości podróży (badanie) × model wyboru celu. Macierz GUS pełni rolę więzu tylko na granicy miasta. Opcjonalnie: przepływy wewnątrzmiejskie z **Deep Gravity** lub **FCD TomTom** można wykorzystać jako dodatkowy więz/walidację modelu wyboru celu.

**Ścieżka dalszego uczenia się (kierunek do pogłębiania — o to prosiłeś):**
1. **Kod jako podręcznik**: przeczytaj pipeline **eqasim/ile-de-france** i silnik **synpp** „stage po stage" — to najlepszy działający wzorzec obu etapów. Prześledź, jak mapują źródła INSEE → zastąp je polskimi (Część 3).
2. **Teoria**: rozdziały o generowaniu popytu w książce MATSim (Horni i in. 2016); przeglądy syntezy populacji — m.in. prace o IPF i integeryzacji (Müller & Axhausen), oraz nowsze o metodach głębokich do popsynth (np. Sun & Erath). Case **Ústí nad Labem** (adaptacja eqasim w Europie Środkowej).
3. **Narzędzia alternatywne**: **PopulationSim/ActivitySim** (dojrzały ekosystem activity-based, dobre docs), **PopGen**, biblioteki wyboru celu / interakcji przestrzennej (**PySAL/spint**). Do OD z cech: **scikit-mobility + DeepGravity**.
4. **Ćwiczenie na mini-skali**: zsyntetyzuj populację jednego osiedla Łodzi (kilka rejonów statystycznych) zanim ruszysz na całe miasto — najszybciej nauczysz się pułapek integeryzacji i tajemnicy statystycznej.

#### 4.2. MVP i kolejność budowy
**Minimalny scenariusz startowy**: sieć **tylko samochodowa** (OSM) + populacja z BREC/siatki GUS + **proste łańcuchy dom–praca–dom** (cele pracy z REGON, długości kalibrowane do pożyczonego badania), próbka 1%, 100–250 iteracji. Dopiero potem: transport zbiorowy (GTFS), pełne łańcuchy aktywności, tryby rower/pieszy, kalibracja funkcji użyteczności, ewentualnie Deep Gravity/FCD jako więz OD.

**Gdzie AI (Claude Code) pomaga, a gdzie potrzebny jest Twój osąd**:
- **AI świetnie**: ETL danych GUS/GUGiK/GTFS/REGON, wywołania pt2matsim, geokodowanie przez API BIR REGON, parsowanie/walidacja XML, glue code synpp, automatyzacja pobierania (ATOM GUS, API GUGiK per TERYT), analiza wyjścia (matsim-tools), debug Javy/Mavena.
- **Twój osąd**: wybór i mapowanie źródeł, strefowanie (BREC vs własne rejony komunikacyjne), obsługa tajemnicy statystycznej, parametry scoringu, interpretacja błędu ekologicznego, decyzje o próbkowaniu i skalowaniu, walidacja z GPR/FCD, warunki licencyjne danych TomTom.

#### 4.3. Wizualizacja — open-source (Twoja trzecia uwaga; na razie sygnalnie)
Pełny łańcuch wizualizacji można zbudować bez narzędzi komercyjnych:
- **SimWrapper** (VSP TU Berlin) — otwarty, przeglądarkowy, **natywny dla MATSim**: obciążenia łączy, ruch agentów w czasie, mapy agregatowe, porównania scenariuszy, dashboardy. **Bez kodowania** — konfiguracja w plikach YAML wskazujących na Twoje pliki wyjściowe. Jest **contrib MATSim** (`contribs/simwrapper`), który generuje standardowe dashboardy po dodaniu jednej linii w kodzie Javy (`addOverridingModule(new SimWrapperModule())`). Narzędzie CLI `simwrapper` (PyPI, Python 3.7+) serwuje lokalne pliki do przeglądarki; współpracuje z `matsim-python`/`matsim-r`. To domyślny wybór.
- **QGIS + kontroler czasu** (Twój warsztat) — eksport zdarzeń/tras MATSim do CSV/GeoPackage i animacja temporalna, którą **już robisz** (`@map_start_time`). Idealne do publikacji, materiałów na GISBoost i integracji z Twoim workflow.
- **OTFVis** — starszy, otwarty wizualizator OpenGL wbudowany w MATSim (podgląd ruchu na żywo).
- **kepler.gl / deck.gl** — do efektownych wizualizacji przepływów OD (webowe, otwarte).
- **Do unikania przy wymogu open-source**: **VIA (Simunto)** — świetna, ale komercyjna (darmowy tier tylko dla małej liczby agentów).

### CZĘŚĆ 5 — Rekomendowany kierunek i plan etapowy

**Rekomendacja główna**: zbuduj scenariusz Łodzi jako **polską adaptację eqasim/synpp**, z macierzą dojazdów GUS jako **szkieletem międzygminnym**, a wewnątrzmiejskie OD **generuj** z: BREC/siatka GUS (domy) × REGON (praca) × pożyczone badanie ruchu (długości podróży) × model wyboru celu. Deep Gravity i FCD TomTom traktuj jako opcjonalne generatory/walidatory wewnątrzmiejskiego OD po MVP. Metoda elektoralna — warstwa badawcza. Wizualizacja — SimWrapper + QGIS.

**Roadmapa etapowa**:
1. **Etap badawczy (ten dokument)** — zamknięty. Decyzje: eqasim jako szkielet; BREC+REGON jako rozwiązanie granularności; SimWrapper+QGIS do wizualizacji.
2. **Pozyskanie danych** — OSM (Łódź + obszar funkcjonalny), GTFS ZDiT (potwierdź licencję), BREC (ATOM SU), siatka GUS 125 m/1 km + demografia, macierz dojazdów NSP 2021, REGON (API BIR, geokodowanie), PRG + BDOT10k, GHS-POP (backup); zdobądź pożyczone badanie ruchu (KBR Wrocław 2024/krajowe); zdecyduj o dostępie i warunkach FCD TomTom.
3. **Prototyp (Cowork)** — MVP samochodowy na próbce 1%; pt2matsim; synteza populacji na kilku rejonach statystycznych; weryfikacja sieci i szkieletu OD.
4. **Pełne kodowanie (Claude Code)** — adaptacja synpp do polskich źródeł (IPF/matching, integeryzacja, tajemnica statystyczna), dodanie TZ, generowanie wewnątrzmiejskiego OD, kalibracja, walidacja z GPR/FCD, dashboardy SimWrapper.
5. **Rozszerzenia badawcze** — Deep Gravity dla OD, warstwa elektoralna, scenariusze polityk (strefy ruchu, nowe linie tramwajowe), publikacja.

## Rekomendacje
1. **Prowadź syntezę populacji na poziomie BREC (rejony/obwody spisowe), nie gminy** — to bezpośrednio rozwiązuje problem granularności wewnątrzmiejskiej, który słusznie wskazałeś.
2. **Traktuj wewnątrzmiejskie OD jako *generowane*, nie mierzone**: BREC × REGON × rozkład długości podróży × model wyboru celu; macierz GUS to tylko więz na granicy miasta.
3. **Zacznij od MVP samochodowego na próbce 1%**, zanim dodasz GTFS, pełne aktywności i metody OD z ML/FCD.
4. **Przyjmij eqasim/synpp jako szkielet**; ucz się „po kodzie", startując od case'u **Ústí nad Labem**, nie od pełnego Paryża.
5. **Rozwiąż lukę „badania ruchu"**: do czasu KBR Łódź (2026–2027) użyj KBR Wrocław 2024/krajowego; zaplanuj podmianę na dane łódzkie jako osobny kamień milowy.
6. **Zdecyduj wcześnie o danych TomTom FCD** — potencjalnie najlepsze wewnątrzmiejskie OD/walidacja prędkości, ale rozstrzygnij warunki licencyjne (co publikowalne, co wewnętrzne).
7. **Wizualizacja od początku open-source**: SimWrapper (dashboardy) + QGIS temporal (Twój warsztat, materiały GISBoost); pomiń VIA.
8. **Sprzęt**: `-Xmx` 16–24 GB, próbka 1–10%, skalowanie przepustowości; GPU zostaw dla Deep Gravity.

## Zastrzeżenia
- **Największe ryzyko: brak aktualnego KBR dla Łodzi** — łańcuchy aktywności oparte na danych zastępczych do 2026–2027; obniża realizm zachowań (mniej — samego ruchu sieciowego).
- **Mikrodane spisowe**: publiczna próbka jednostkowa NSP 2021 nie jest tak dostępna jak francuska — synteza może wymagać oparcia na marginesach BDL/BREC + ziarnie z innego źródła albo wniosku do GUS o dane jednostkowe.
- **Tajemnica statystyczna GUS** — ukryte wartości w małych oczkach/obwodach; wymaga imputacji lub agregacji w kodzie.
- **REGON ≠ dokładna liczba miejsc pracy** — rejestr podaje podmioty/jednostki lokalne i klasy zatrudnienia, nie precyzyjną liczbę etatów; kalibruj sumami „pracujący" z BDL.
- **Dane FCD TomTom** — komercyjne; wymagają rozstrzygnięcia licencyjnego przed użyciem w otwartym/naukowym pipeline.
- **Licencja GTFS Łódź niepotwierdzona** — zweryfikuj u źródła (dane.gov.pl / `feed_info.txt`), nie polegaj na etykiecie „MIT" z Transitland.
- **Deep Gravity generuje OD, nie populację** — nie zastępuje syntezy; wymaga danych treningowych o rzeczywistych przepływach (macierz GUS / FCD).
- **Meta Data for Good wygaszane** — nie buduj na nim zależności.
- **Błąd ekologiczny** przy danych wyborczych — jeśli sięgniesz po warstwę elektoralną, zaadresuj go jawnie.
- **Dwie prace „Nature"** (Deep Gravity 2021 vs Imagery2Flow 2025) różnią się wejściem — potwierdź, którą widziałeś.

## Weryfikacja zastrzeżeń użytkownika (2026-07-01)

Poniższe siedem uwag zostało sprawdzone (web research + przegląd materiałów kursu TU Berlin) i rozstrzygnięte. Traktować jako wiążące doprecyzowanie powyższych sekcji — kolejni agenci nie powinni renegocjować tych punktów bez nowych informacji od użytkownika.

1. **„Brak tych danych → działamy na innym otwartym frameworku."** Potwierdzone i przyjęte jako zasada nadrzędna: MATSim + pt2matsim + eqasim/synpp + SimWrapper nie wymagają żadnego zamkniętego źródła do działania. Cały pipeline ma być od początku niezależny od danych zamkniętych/komercyjnych — nie tylko na etapie MVP (patrz punkt 5).

2. **„Sprawdź o co chodzi z tą próbką — dane dla jednego obwodu spisowego są dostępne."** Użytkownik miał rację, dokument mylił dwa pojęcia. GUS **jawnie i otwarcie publikuje agregaty demograficzne** (liczba osób wg płci i grup wieku) na poziomie obwodu spisowego i rejonu statystycznego z NSP 2021 (tabela GUS „Ludność w rejonach statystycznych i obwodach spisowych według płci, ekonomicznych i 10-letnich grup wieku"). To w pełni wystarcza jako marginesy do IPF. Zastrzeżenie o „mikrodanych spisowych" dotyczy czegoś innego: **jednostkowych, anonimizowanych rekordów osób/gospodarstw** (jak francuska próbka INSEE ~30%), które w Polsce nie są publicznie dostępne — tylko przez płatną „Pracownię Badacza" GUS (oddziały m.in. w Łodzi) dla uczelni/instytutów badawczych. **Wniosek: synteza populacji metodą IPF na poziomie BREC jest w pełni pokryta otwartymi danymi. Ograniczenie dotyczy wyłącznie alternatywnej metody „direct sampling", której nie musimy używać.**

3. **„To pewnie dotyczy nieistotnej ilości danych" (tajemnica statystyczna).** Prawdopodobnie trafne dla obszaru miejskiego: ukrywanie wartości w GUS dotyczy głównie rzadko zaludnionych oczek/obwodów (obszary wiejskie, pojedyncze budynki), a nie gęstej zabudowy miejskiej. Nie zweryfikowano liczbowo dla Łodzi — do policzenia dopiero po pobraniu realnych danych BREC (odsetek ukrytych rekordów). Traktować jako niskie ryzyko, nie jako blokującą przeszkodę.

4. — brak uwagi użytkownika, REGON zostaje bez zmian względem oryginalnej oceny.

5. **„FCD raczej niedostępne, kłóciłoby się to z zasadą otwartych frameworków."** Potwierdzone: dane FCD TomTom (Flow Segment Data, Origin-Destination Analysis) to produkt komercyjny wymagający płatnej licencji. **Decyzja projektowa: FCD TomTom jest wykluczone z pipeline'u na stałe, nie tylko odłożone jako opcja po MVP.**

6. **„Z danymi MPK jest różnie, raz są dostępne raz nie."** To osobny problem od tego, który opisuje reszta dokumentu. Dokument mówi o niejasności **licencji** (dataset 1803 na dane.gov.pl vs. HTML na mpk.lodz.pl, etykieta „MIT" od agregatora niepotwierdzona u źródła). Użytkownik wskazuje dodatkowo na **operacyjną niestabilność feedu** (bywa aktualny/dostępny, bywa nie). Oba problemy są realne i się nie wykluczają. Do zaadresowania na etapie pozyskiwania danych: sprawdzić `feed_info.txt` i historię publikacji datasetu, mieć plan B (mirror z Otwarte Dane Transportowe / przyjazdy.pl, lub w ostateczności własny parser rozkładów HTML z mpk.lodz.pl).

7. **„Deep Gravity raczej nieużyteczne, bo wymaga potwierdzenia danymi zbieranymi ręcznie — chodziło mi o Imagery2Flow."** Potwierdzone jako dwie osobne prace: Deep Gravity (Simini i in., Nature Communications 12:6576, 2021) i Imagery2Flow (Nature Communications 16, 2025, DOI 10.1038/s41467-025-65373-z, kod: github.com/GeoDS/Imagery2Flow). **Obie metody wymagają rzeczywistych danych o przepływach (ground truth) do treningu/walidacji** — krytyka użytkownika dotyczy w równym stopniu obu, nie tylko Deep Gravity. Jedyne w pełni otwarte źródło ground truth, jakim dysponujemy, to międzygminna macierz dojazdów GUS — zbyt gruboziarniste, by w pełni wytrenować/zwalidować te modele wewnątrz miasta. **Decyzja: obie metody pozostają opcjonalnym rozszerzeniem badawczym po MVP, nigdy fundamentem populacji czy OD.**

**Konsekwencja dla dalszej pracy**: pipeline ma być budowany jako w pełni otwarty i niezależny od zamkniętych/komercyjnych źródeł danych na każdym etapie projektu (nie tylko w MVP). FCD TomTom oraz modele wymagające go do walidacji są wykluczone z założenia.
