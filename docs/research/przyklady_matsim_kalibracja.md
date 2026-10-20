# Przykłady MATSim: jak zbierają dane i jak kalibrują

**Autor: Grok, 2026-10-18.** Przegląd źródeł, nie decyzja. Nie zastępuje `docs/projekt/DECISIONS.md`. Liczb z tego pliku nie wolno wstawiać do modelu Kutna bez ponownego odczytu cytowanego źródła.

Data odczytu stron: 2026-10-18. Punkt startu: [matsim.org/examples](https://www.matsim.org/examples/). Przeczytane dosłownie: 4 studia przypadków (Show Cases), 28 kart galerii, strona [Open-Data MATSim Models](https://www.matsim.org/install/open-data-models) podlinkowana z tej samej strony. Za każdą kartą, która podaje publikację, repozytorium albo rozdział książki, zszedłem do tego źródła na tyle, na ile tekst był publicznie czytelny. Pełnego tekstu części PDF nie udało się wyciągnąć (captcha ScienceDirect, część rozdziałów Ubiquity bez treści w HTML). Te luki są oznaczone wprost.

Sama strona pisze, że galeria miesza projekty studenckie, modele pokazowe bez kalibracji i modele używane przez praktyków. Jakość nie jest jednolita. To jest rama tego raportu.

Książka Horni, Nagel i Axhausen (red.), *The Multi-Agent Transport Simulation MATSim*, Ubiquity Press 2016, DOI [10.5334/baw](https://doi.org/10.5334/baw), CC-BY 4.0, część IV, ma ponad 40 studiów przypadków. Galeria na stronie jest wyborem, nie pełnym katalogiem książki. Rozdziały spoza galerii są tylko wypisane w §8, bez streszczenia metod, bo ich pełnego tekstu w tej sesji nie czytałem.

## 1. Wspólny szkielet eksperymentu

Tam, gdzie model ma służyć decyzji, a nie tylko filmowi, badacze układają pracę w tej kolejności:

1. **Rok bazowy i obszar.** Najpierw odtworzenie obserwowanego dnia (zwykle przeciętny dzień roboczy), dopiero potem scenariusze (nowa infrastruktura, opłata, flota, ewakuacja). Vorarlberg, Izmir, Quito, Gauteng, BVG i ARUP idą tą drogą. Modele pokazowe (część filmów w galerii) tego kroku nie mają.
2. **Podaż osobno od popytu.** Sieć drogowa (OSM albo sieć z modelu statycznego EMME/VISUM) i, jeśli jest transport zbiorowy, rozkład (GTFS albo sieć przewoźnika) przez `pt2matsim` albo odpowiednik. Prędkości swobodne z OSM bywają świadomie obniżane, bo nie zawierają świateł i przyspieszeń. W Open Berlin (Ziemke, Kaddoura, Nagel, VSP Working Paper 19-01, 2019) prędkości wewnątrz miasta z OSM zmniejszono o połowę właśnie z tego powodu. Sygnalizacji nie było w danych.
3. **Populacja syntetyczna, nie odtworzone osoby.** Spis, macierz dojazdów, rejestr zakładów, ankieta dzienniczkowa. Osoba w modelu jest losowaniem z rozkładów, nie rekordem z ankiety. eqasim (Île-de-France) i Open Berlin opisują to wprost.
4. **Łańcuch dnia, nie sama macierz O-D.** Aktywności z godziną i trybem. Macierz ze starego modelu (Poznań VISUM, Szwecja SAMPERS, Caracas, Izmir) jest tylko punktem startu, z którego składa się plany.
5. **Próbka i przepustowość.** Otwarte scenariusze VSP ustawiają `flowCapacityFactor` i `storageCapacityFactor` równe frakcji próbki. Berlin: 10%. Kelheim i Lipsk: 25%. Wiedeń: 12,5% mobilnej populacji powyżej 5 lat. Meksyk: 1%. README Kelheim ostrzega, że model jest skalibrowany na 25% i wynik 1% „może być trochę odchylony”.
6. **Kalibracja w dwóch warstwach, które nie wolno mieszać.** Warstwa zachowania (udziały trybów, rozkłady odległości, grupy osób) i warstwa natężeń (liczniki). Dojrzałe modele robią obie, ale różnie decydują, czy licznik wchodzi do funkcji celu, czy zostaje tylko sprawdzianem.
7. **Scenariusz polityki na zamrożonym modelu bazowym.** Innowacja planów jest włączona w kalibracji i wyłączana pod koniec (`fractionOfIterationsToDisableInnovation`), żeby wynik przestał dryfować. Open Berlin w kroku lokalizacji używa wagi strategii innowacyjnych 0,05.
8. **Walidacja jest osobnym zdaniem.** Zgodność z daną, której użyto do strojenia, nie jest walidacją. Open Berlin po kalibracji lokalizacji **wyłącza CaDyTS** i sprawdza, czy natężenia zostają (test stabilności). SBB porównuje model z ankietą, licznikami drogowymi i kolejowymi oraz z własnymi danymi przewoźnika. Joinville pokazuje 20 przekrojów i autorzy sami piszą, że kalibracji jeszcze nie ma.

## 2. Skąd biorą popyt

Siedem rodzin. W jednym modelu zwykle są dwie albo trzy naraz.

### 2.1. Ankieta dzienniczkowa (wzorzec zachowania)

Daje łańcuch aktywności, czas, tryb i odległość dla próby osób. Nie daje natężenia na ulicy.

| model | badanie | co z niego biorą |
|---|---|---|
| Open Berlin | SrV 2008 (Berlin) i MiD 2008 | walidacja udziałów trybów i właściwości podróży; nie jest generatorem planów |
| Niemcy (Illenberger, DB, galeria + rozdz. 70 książki) | MiD 2008 | losowa realizacja ankiety krajowej jako plany; ok. 4 mln agentów w pełnym scenariuszu, film pokazuje 500 tys. |
| SBB SIMBA MOBi | Mikrozensus Mobilność i Transport, fala 2015 (co 5 lat; od 2025 także aplikacja) | kryteria kalibracji: udziały trybów (podróże i kilometry), grupy osób, klasy odległości, czasy aktywności |
| Wiedeń AIT | Österreich unterwegs 2013/14 (Tomschy i in. 2016) | synteza populacji w narzędziu PAM (Arup), przeskalowana do populacji 2020 |
| eqasim Île-de-France | ENTD 2008 (krajowa); opcjonalnie EMP 2019 i regionalna EGT 2010, jeśli jest dostęp | łańcuchy aktywności dopasowane do atrybutów osoby |
| Santiago (galeria) | ankieta O-D 2012 | dzienniczki; współczynniki ekspansji do próbek 1% i 10% |
| Seul | Household Travel Survey 2012 | synteza popytu; obszar metropolitalny 21,5 mln, symulowane 10% |
| Tel Awiw | Israel National Travel Habits Survey 1996 | hierarchia logitów: główny przystanek tury, przystanki pośrednie warunkowo |
| Joinville | ankieta podróży miasta + spis 2010 | popyt i demografia; pierwsza wersja tylko samochód, 135 652 agentów |
| Sioux Falls (scenariusz testowy Chakirov i Fourie 2014) | ankieta i użytkowanie terenu miasta | populacja heterogeniczna; **to nie jest model prawdziwego Sioux Falls** |
| Vorarlberg | „Mobilität in Vorarlberg 2013” | populacja plus zewnętrzny model wyboru trybu (największa wiarygodność) |

### 2.2. Spis, dojazdy, rejestry, budynki (gdzie ludzie są)

Daje wagi i miejsca, nie zachowanie w ciągu dnia.

- **Open Berlin (Ziemke i in. 2019):** Zensus 2011 (płeć, 11 klas wieku, pracujący, studenci na gminę), statystyka dojazdów Bundesagentur für Arbeit 2010 (tylko ubezpieczeni społecznie, więc skalowana do spisu), 447 rejonów LOR w Berlinie jako losowy dom, CORINE jako maska użytkowania terenu przy losowaniu współrzędnej. Dzieci poniżej 18 lat pominięte. Jedno gospodarstwo na agenta, bez struktur gospodarstw.
- **eqasim, Île-de-France** (dokumentacja pipeline, stan odczytu 2026-10-18): spis RP 2022, macierze dojazdów do pracy i nauki RP-MOBPRO / RP-MOBSCO 2022, podatki Filosofi 2021, rejestr usług BPE 2025, podział IRIS, rejestr przedsiębiorstw SIRENE (geolokalizowany), budynki BD TOPO, adresy BAN. Pipeline: gospodarstwa i osoby, lokalizacje aktywności pierwotnych, łańcuchy z ankiety, lokalizacje wtórne. Walidacja populacji: porównanie ze spisem i z ankietą, zanim w ogóle ruszy symulacja. Ten sam szkielet przeniesiony na Tuluzę, Lyon, Nantes, Korsykę i (osobno, w slajdach Hörla) na Monachium.
- **Wiedeń:** adresy BEV i gęstość GEOSTAT dla domów; statystyka zakładów dla pracy; dla samego Wiednia miejsca pracy przypięte do budynków (Churanek i Steinnocher 2017), nie do średniej dzielnicy. Obiekty głównie z OSM (654 tys.).
- **Gauteng:** spis i strefy z GIS. Najpierw tylko dojazdy samochodem, potem łańcuchy pojazdów dostawczych (Joubert i in. 2010).
- **Joinville:** spis 2010 plus użytkowanie terenu od miasta jako obiekty.

### 2.3. Gotowy model statyczny albo activity-based

Popyt nie powstaje w MATSim. MATSim dostaje wynik innego modelu i robi przypisanie dynamiczne.

| model | źródło planów |
|---|---|
| Poznań (od 2012) | poranny szczyt 1 h z PTV VISUM wydziału planowania miasta, rozciągnięty na 5:00–12:00. Sieć OSM, ponad 13,6 tys. węzłów |
| Szwecja (otwarty 10%) | SAMPERS (pasażerowie) i SAMGODS (towary), modele krajowe; sieć OSM, PT z GTFS. Cel: elektryfikacja i drogi elektryczne (Bischoff i in. 2019, MT-ITS) |
| Toronto | TASHA (activity-based, już istniał). Sieć z EMME/2. Od 2011 dokładanie PT. Planowano TASHA jako moduł przeplanowania MATSim |
| Tel Awiw | własny model activity-based (logit zagnieżdżony), bez powrotu do macierzy O-D. Sieć z EMME/2 |
| Los Angeles (otwarty, UC Davis + VSP) | dane Southern California Association of Governments (SCAG). README nie opisuje procedury kalibracji; odsyła do wewnętrznego Google Doc |
| Caracas (strefa Los Ruices) | macierz O-D tylko poranna, od firmy, która robiła wcześniejsze studium. Popołudnie odwrócone, bo strefa rano „konsumuje”, po południu „produkuje”. Start ok. 7:30 |
| Izmir (Mutlu, praca dyplomowa 2010) | strefy, użytkowanie terenu i ruch samochodowy z planu transportowego miasta. 47 stref wewnętrznych |
| Monachium (galeria, 2010) | ruch wewnętrzny z MiD 2002; dojeżdżający z Federalnego Urzędu Pracy; towary z ministerstwa transportu. Sieć VISUM |
| Berlin historyczny, ok. 2006 | „model Kuttera” / Berliner Personenverkehrs-Modell. Sieć miasta, ok. 10 tys. węzłów. Porzucony z powodu danych |
| Berlin BVG 2010 (rozdz. 53 książki) | ankiety na zlecenie BVG i PTV. Pełny PT, w tym promy. Prognoza na 2015. Strona BVG nie podaje metody kalibracji |

### 2.4. Telefon i GPS

- **Dakar:** dane z wyzwania D4D (rekordy telefonii). Sieć OSM. Oprogramowanie SPOT. Praca: Gueye i in., PDF na stronie galerii.
- **USA kontynentalne** (Gurram, Sivaraman, Apple, Pinjari 2019): jeden dzień, środa 6 marca 2019, surowe obserwacje GPS. Z 30,5 mln urządzeń zostawiono 2,7 mln „wysoko widocznych i mobilnych”. Sieć OSM na Amerykę Północną. MATSim dostaje gotowe łańcuchy dnia z GPS, nie generuje ich z ankiety. Wynik: 1,5 mld rekordów trajektorii, VMT na stan i natężenie na link.

To jest inna filozofia niż spis plus ankieta: popyt jest obserwacją śladu, nie modelem wyboru. Powtarzalność zależy od jednego dnia i od filtra urządzeń.

### 2.5. Transakcje operatora

- **Santiago:** karta Bip! do rozmycia godzin startu po ekspansji ankiety. Winiety na autostradach płatnych. Colectivos (wspólne taksówki) dokładane później.
- **Rotterdam** (rozdz. 81 książki, nie ma go w galerii): karta miejska do zarządzania przychodem w PT.
- **SBB:** wejścia i wyjścia na stacjach, obciążenia odcinków, badania O-D kolei, dane korporacyjne. Mikrozensus zostaje wzorcem zachowania, liczniki wzorcem wielkości.
- **MOIA:** popyt na ridepooling brany z własnej eksploatacji (Hamburg od kwietnia 2019). Zwick i Axhausen (STRC 2020) porównują algorytmy DRT i AMoD na tym popycie. Popyt się nie uczy między iteracjami. Trzy iteracje MATSim służą temu, żeby relokacja pojazdów widziała popyt z poprzedniej iteracji.

### 2.6. Kupiona populacja

Senozon dostarcza plany do otwartych scenariuszy, których pipeline syntezy nie jest w repozytorium: **Kelheim**, **Hamburg**, **Metropole Ruhr** (licencja wejścia CC-BY-NC). Wczesne SIMBA MOBi 1.0 (kwiecień 2018) też startowało z planów Senozon/ETH. Od MOBi.plans SBB generuje plany samo (Scherr i in., STRC 2019).

### 2.7. Ruch towarowy i tło

- Open Berlin: uproszczeni agenci towarowi z liczników BASt na arteriach wlotowych. Ich początki i końce są **stałe** i nie wchodzą do kalibracji lokalizacji. Liczniki nie rozróżniają typów, więc kalibracja idzie na wszystkie pojazdy, a towar jest w modelu po to, żeby osobowe nie musiały same wypełnić licznika.
- Wiedeń: towar **nie jest agentem**. `flowCapacityFactor` i `storageCapacityFactor` ścięte o ok. 10%, liczniki też obniżone.
- Niemcy (galeria): O-D z urządzeń nawigacyjnych jako drugi cel kalibracji obok 2500 stacji.
- RPA, kraj: syntetyczna populacja pojazdów ciężarowych z sieci złożonej zależnej od ścieżki (Joubert i Axhausen 2013).
- Gauteng, studium myta GFIP: osobowe tylko dom-praca-dom, komercyjne z pełnym łańcuchem, plus PT i ruch zewnętrzny z modelu Saturn używanego przez SANRAL.
- Szwecja: SAMGODS obok SAMPERS.

### 2.8. Ewakuacja i sygnały (popyt uproszczony świadomie)

- **Padang:** wszyscy w domu („ewakuacja o 3 w nocy”), start 28 min przed tsunami. Cel to czas ewakuacji i gardziele, nie zgodność z licznikiem.
- **Aliaga:** wybuch w strefie przemysłowej. Wszyscy w domu. Trzy scenariusze miejsc zbiórki. Porównanie MATSim z Cube Avenue, nie z licznikiem dnia zwykłego.
- **Quito, pierwsza praca:** 20 tys. agentów, dwa przebiegi, 70 sygnalizacji, sieć OSM 8192 linków na obszarze ok. 5×8 km. Algorytm ewolucyjny szuka nastaw świateł minimalizujących średni czas. Druga praca: udział PT/samochód oraz pojemność i częstotliwość BRT jako zmienne optymalizacji wielokryterialnej.

## 3. Jak kalibrują

### 3.1. CaDyTS: licznik jako dopłata do oceny planu

Rozdział 32 książki (Nagel, Zilske, Flötteröd; DOI [10.5334/baw.32](https://doi.org/10.5334/baw.32)). Pełnego tekstu rozdziału w tej sesji nie wyciągnąłem. Działanie w Open Berlin jest opisane operacyjnie w VSPWP 19-01 i tego opisu używam.

CaDyTS dokłada do oceny planu składnik zależny od tego, czy przejazd agenta zmniejsza błąd na licznikach godzinowych. Plan zgodny z obserwacją dostaje dodatni offset, plan sprzeczny ujemny. Offset jest stałą alternatywy w modelu wyboru planu. Procedura siedzi w pętli iteracyjnej, więc popyt przesuwa się w stronę liczników.

W Open Berlin krok lokalizacji wygląda tak:

- CEMDAP (specyfikacja przeniesiona z Los Angeles, parametry **nie** są przestawiane) puszczony 5 razy. Pięć planów na agenta to zbiór wyboru lokalizacji.
- Próbka 10%. W tym kroku **wszyscy** jadą po sieci samochodowej. Przepustowość podniesiona odwrotnością udziału samochodu (0,31 zamiast 0,10), żeby dynamika odpowiadała światu, w którym tylko samochody są na sieci. Autorzy piszą wprost, że założenie „wzorce przestrzenne trybów są podobne” jest fałszywe i ma być naprawione w kroku trybu.
- 346 stacji, 8304 godzinowe wartości (250 stacji miasta, 96 autostradowych).
- Aktywności pocięte na klasy czasu trwania (np. zakupy do 600 s, 600–1200 s), żeby wartość czasu była realistyczna.
- Towar z BASt stoi w miejscu.

Krok trybu jest **ręczny i bez CaDyTS**. Agenci zmieniają tryb, godzinę (±2 h) i trasę. Samochód i PT są na sieci. Rower i pieszo to teleport z czasem z odległości w linii prostej i prędkości trybu. Pasażer (`ride`) jedzie teleportem z czasem samochodu po zatłoczonej trasie, a jego udział jest zamrożony. Tryb łańcuchowy (samochód, rower) zmienia się dla całej tury. GTFS Verkehrsverbund Berlin-Brandenburg 2017. Po wyłączeniu CaDyTS liczniki są sprawdzianem stabilności: wybory wymuszone przez licznik mają zostać, gdy dopłata zniknie.

To jest najważniejsza lekcja metodyczna z Berlina: licznik stroi lokalizację, ankieta stroi tryb, a na końcu licznik nie ma prawa dalej ciągnąć wyboru.

### 3.2. Stałe trybu (ASC), często osobno w klasach odległości

Rakow i in., VSP Working Paper 24-22 (PDF na publicznym SVN VSP, odczyt indeksu 2026-10-18), o nowszej generacji Open Berlin:

- lokalizacje: nadal kilka wiarygodnych planów na agenta, wybór planu dociągany do liczników;
- tryby: automatyczna aktualizacja stałych alternatyw. Jedna stała jest zamrożona (zwykle 0), bo liczą się tylko różnice. Po symulacji

  `ASC_i ← ASC_i + ln(z_i) − ln(m_i) − (ln(z_0) − ln(m_0))`

  gdzie `z` to udział obserwowany, `m` symulowany, indeks 0 to tryb zamrożony. Pętla, aż różnica w punktach procentowych zejdzie pod próg. Autorzy piszą, że w eqasim ten krok nadal bywa ręczny, a u nich jest automatyczny.

Wersja v7 Open Berlin jest opisana w Rakow (2026), *From Data to Simulation*, według noty wydania na GitHubie. Tej pracy nie czytałem. Z noty wydania: rowery routowane po sieci (jeszcze bez zdarzeń na linkach), ponowna kalibracja stałych, referencyjne tryby części osób (tryb zaobserwowany, nie tylko udział zagregowany).

**Wiedeń** (README `ait-energy/matsim-model-vienna`, 2023.2) łączy oba podejścia:

- cel udziałów trybów bierze się z populacji zsyntetyzowanej z ankiety, nie z osobnej tabeli;
- cztery plany na agenta z różnymi lokalizacjami, więc wybór planu pośrednio wybiera obiekty;
- CaDyTS przez 250 z 750 iteracji na ok. 180 stacjach automatycznych (Wiedeń 2015, samochody i ciężarowe, godzinowo; autostrady ASFINAG 2016, tylko samochody);
- `TimeAllocationMutator` z zakresem 1 h tylko przez pierwsze 25 iteracji;
- 10 równolicznych subpopulacji o różnych wartościach czasu, z modelu klas ukrytych (Greene i Hensher 2003) na zmiennych społeczno-ekonomicznych, plus osobna subpopulacja ruchu kordonowego. Parametry wyboru trybu są oszczędniejszą wersją modelu Schmida i in. (2019) na danych RP i SP.

Ruch kordonowy: podróż obcięta na granicy obszaru, wlot i wylot przypięte do linku we właściwym kierunku (na autostradzie to ma znaczenie). Dla PT wlotem jest duża stacja kolejowa.

**SBB, grudzień 2017 – kwiecień 2018** (Scherr, Bützberger, Frischknecht, STRC 2018): kalibrowane są parametry scoringu. 46 statystyk z Mikrozensusu 2015, w tym udziały trybów w podróżach i w kilometrach, globalnie i w grupach osób, oraz udziały w klasach odległości. Osobne parametry dla grup (np. rodzaj biletu PT), bo zachowanie grup się różni. Scherr i in. (EJTIR 2020, DOI 10.18757/ejtir.2020.20.4.4463) opisują ten sam model jako reakcję agentów na podaż przy równowadze preferencji i ograniczeń. Pełnego PDF EJTIR w tej sesji nie czytałem.

**Vorarlberg:** tryb nadawany **przed** MATSim, zewnętrznym modelem największej wiarygodności. MATSim nie jest tu miejscem kalibracji trybu.

**Santiago (galeria):** „kalibracja względem podziału modalnego i natężeń, metodami ręcznymi i automatycznymi”. Nazwy algorytmu galeria nie podaje. Rozdział 84 książki (Kickhöfer i Tirachini) nie został w tej sesji odczytany.

**eqasim, Monachium** (slajdy Hörla z warsztatu populacji syntetycznych, 2024, nie artykuł): po generacji trzeba skalibrować ASC modelu wyboru i poprawić przepustowości; walidacja wobec MiD 2011 (udziały, mediany odległości), przepływów PT i czasów samochodu na 1000 losowych podróżach wobec API TomTom.

**MUM 2026, Szwajcaria** (abstrakt Dib i in., paper 20, oraz prezentacja Sallarda): stałe trybu aktualizowane wewnątrz jednej symulacji, osobno dla 26 kantonów, bez setek niezależnych runów. Cel: Mikrozensus. Abstrakt mówi o zgodności udziałów w kantonach. To jest nowszy wariant §3.2, nie osobny zbiór danych.

### 3.3. Ręczna korekta sieci

Gdy licznik się nie zgadza, a popyt jest już z ankiety, część zespołów poprawia prędkość i przepustowość, nie ocenę agenta. Open Berlin: połowa prędkości OSM w mieście. eqasim Monachium: „adjusting capacities”. Izmir i Caracas: atrybuty sieci poprawiane ręcznie względem OSM. Caracas testuje kilka wag przeplanowania godziny wyjazdu i zostawia wariant najbliższy licznikom. To jest kalibracja przez wybór scenariusza zachowania, nie przez CaDyTS.

### 3.4. Czego świadomie nie kalibrują

- **Kelheim, Lipsk, Meksyk** piszą w README, że kalibracja uwzględnia liczniki, podział modalny i (Kelheim, Lipsk) rozkłady odległości według trybu. Procedura jest w Google Doc, którego nie ma publicznie. Nie da się z README odtworzyć wag ani kolejności kroków.
- **Joinville:** porównanie 20 linków, szczyt 7–8. Autorzy: danych za mało, kalibracja konieczna w następnej wersji. Miasto zapowiadało ponad sto stacji i nową ankietę.
- **Quito, Padang, Aliaga, ruch lotniczy:** kryterium to czas, emisja albo pojemność operacyjna, nie GEH.
- **Sioux Falls:** scenariusz testowy algorytmów. Zgodność z miastem nie jest celem.
- **MOIA w cytowanej pracy:** popyt zamrożony, kalibruje się podaż ridepoolingu (flota, wstawianie kursu, relokacja), nie wybór trybu mieszkańców.
- **USA GPS:** nie ma strojenia ASC. Jest filtr urządzeń i porównanie z VMT oraz z licznikami Florydy.

### 3.5. Projekt scenariusza po bazie

| kto | co zmienia, gdy baza już stoi |
|---|---|
| Vorarlberg | trzy scenariusze na 10%: rozkład PT, inwestycje urbanistyczne, ładowarki. Baza policzona na 10% i na 100%. Bez towarów i bez ruchu urlopowego |
| Izmir | trzy przeprawy przez zatokę. Wybór według zmiany natężenia na linkach łączących i na linkach już pełnych oraz według kosztu inwestycji |
| Gauteng | myto GFIP: zniżki pory dnia, e-tag, klasa pojazdu, PT. Wynik oglądany jako rozpłaszczenie szczytu i objazd ciężarowych poza szczytem |
| BVG | zamknięcie Tegel i otwarcie BER; później projekt avoev (pojazdy autonomiczne wobec PT klasycznego) |
| ARUP BERTIE | horyzont 2040: EV, ruch aktywny, jazda, pakiety łączone. Obszar Transport East, ok. 5 mln osób, dojazdy do Londynu |
| ARUP MONTY | krajowy model Nowej Zelandii. Opłaty kordonowe i obszarowe, zamknięcia po powodzi 2023, druga przeprawa w Auckland. MATSim jest silnikiem interakcji na sieci wewnątrz większego zestawu modeli statystycznych |
| Quito | nastawy sygnalizacji; potem udział trybów i oferta BRT |
| Szwecja | elektryfikacja floty i Electric Road Systems na modelu dalekobieżnym |

## 4. Jak walidują i jakimi liczbami

Metryki, które w tych źródłach naprawdę padają:

| sprawdzian | gdzie występuje | uwaga |
|---|---|---|
| wykres licznik symulacja/obserwacja, wszystkie godziny i stacje | Open Berlin, po kroku 1 i po kroku 2 | krok 2 bez CaDyTS jest testem stabilności |
| udział trybu wobec ankiety, czasem osobno SrV i MiD | Berlin, Wiedeń, SBB, Santiago | SrV i MiD dla Berlina **różnią się**. Ziemke i in. mówią o tym wprost. Jeden „prawdziwy” udział nie istnieje |
| udział trybu w klasach odległości i w grupach osób | SBB (46 statystyk), nowszy Berlin (nota v7: wiek, dochód, zatrudnienie) | zagregowany udział potrafi zejść się przy złym rozkładzie odległości |
| rozkład odległości według trybu | README Kelheim i Lipska | procedura niepubliczna |
| rozkład godzin | SBB (STRC 2019: czas poza domem, rozkład doby) | porównanie z Mikrozensusem; w momencie tamtego tekstu kalibracja nie była skończona |
| macierz dojazdów | SBB, slajd MUM 2019: BfS wobec MOBi na regionach MS | błąd względny na mapie |
| SQV, %MAE, %RMSE | Scherr, Manser, Bützberger 2020, *Transportation Research Procedia* 49, 30–43, model MOBi 2.0 z czerwca 2019 | liczby poniżej, z indeksowanego tekstu PDF, nie z lokalnej kopii |
| korelacja rang VMT wobec FHWA, liczniki Florydy, RMSE wobec modeli regionalnych Florydy | Gurram i in. 2019 | rangi zgodne, wartości bezwzględne rozjechane |
| czasy przejazdu wobec routera zewnętrznego | eqasim Monachium, 1000 podróży, TomTom | to jest walidacja sieci i przypisania, nie popytu |
| porównanie dwóch symulatorów | Aliaga: MATSim i Cube Avenue | zgodność narzędzi, nie zgodność ze zliczeniem |
| tylko wzrok | większość filmów w galerii | strona sama odróżnia to od modelu skalibrowanego |

Liczby SBB z indeksu PDF Scherr i in. 2020 (przed użyciem odczytać artykuł):

| | wsiadania i wysiadania, stacje kolejowe | potoki pasażerów, odcinki | liczniki drogowe |
|---|---|---|---|
| N | 1143 | 3848 | 2455 |
| %MAE | 22,2 | 11,4 | 20,7 |
| %RMSE | 62,2 | 20,3 | 31,3 |
| udział SQV ≥ 0,9 | 55,6% | 55,3% | 35,4% |

Ten sam tekst: błąd względny natężeń drogowych na mapie kraju w pasie ±10%, z wyjątkami (zachód Berna, oś północ-południe przez Alpy). Potoki kolejowe w większości w pasie ±5%. Poniżej 4% liczników pasażerskich ma jakość „unsatisfactory” w ich skali SQV. Próg „good” w tabeli to SQV ≥ 0,85, „mediocre” ≥ 0,8, „sufficient” ≥ 0,7. Drogowe SQV ≥ 0,9 jest wyraźnie rzadsze niż kolejowe, co zgadza się z tym, że model należy do przewoźnika kolejowego i kolej była celem kalibracji.

Open Berlin, liczby z VSPWP 19-01, które dało się odczytać bez rozjechanej tabeli: dorośli Berlin+Brandenburgia, próbka 10%, sieć 73 689 węzłów i 159 039 linków samochodowych, 346 stacji, 8304 zliczenia godzinowe, pięć planów CEMDAP, czynniki przepustowości 0,10 w kroku trybu. Udziały z tabeli 3 i stałe z tabeli 2 **nie są tu przepisane**: ekstrakcja PDF pomieszała kolumny. Przed użyciem tych liczb trzeba otworzyć PDF.

## 5. Karty: studia przypadków na stronie

### SBB, SIMBA MOBi

Od 2017, model całej Szwajcarii, decyzje o ofercie pasażerskiej. Architektura (slajdy i STRC 2019): `MOBi.synpop` (BFS, SBB, ARE; FaLC, STATPOP, STATENT), `MOBi.plans` (generacja planów), `MOBi.sim` (MATSim). Ruch graniczny z statystyki dojeżdżających przygranicznych FSO. Kalibracja i walidacja: §3.2 i §4. Kod: [SchweizerischeBundesbahnen/matsim-sbb](https://github.com/SchweizerischeBundesbahnen/matsim-sbb). Wkład do rdzenia: SwissRailRaptor (domyślny router PT) i `railsim` (ruch kolejowy od 2023, inna jednostka SBB). Rozszerzenia: deterministyczny PT i KPI. Prezentacja FOSDEM 2024 jest linkiem ze strony, nie była tu streszczana godzina po godzinie.

### MOIA

Konsulting ridepoolingu. Miasta eksploatacji: Hamburg, Hanower. Koncepcje: Monachium, Zurych, Graz. Wizualizacja MIA (Simunto). Metoda z publikacji, nie ze strony: popyt z własnych zamówień, podaż w contrib DRT (heurystyka wstawiania, ograniczenia czasu oczekiwania i podróży, relokacja pustych pojazdów z poprzedniej iteracji). Bischoff, Maciejewski, Nagel, IEEE ITSC 2017, jest opisem algorytmu, nie kalibracji miasta. Strona nie podaje, jak dopasowują model do miasta, w którym MOIA jeszcze nie jeździ.

### ARUP

City Modelling Lab od 2019. BERTIE (Transport East) i MONTY (ministerstwo NZ) opisane w §3.5. Artykuły na Medium (`arupcitymodelling`) mają być technicznym dziennikiem przygotowania danych. W tej sesji nie przeczytałem całego bloga. Narzędzia otwarte, przydatne jako wzorzec pipeline, nie jako skalibrowany model: [PAM](https://github.com/arup-group/pam) (popyt), [GeNet](https://github.com/arup-group/genet) (sieć), [Osmox](https://github.com/arup-group/osmox) (obiekty z OSM), [Elara](https://github.com/arup-group/elara) (eventy), [Londinium](https://github.com/arup-group/londinium) (mały zbiór półsyntetyczny do testów). PAM jest też narzędziem syntezy Wiednia.

### BVG

Pierwszy model komercyjny 2010, z PTV. Tegel i BER. Opis w rozdziale 53 książki, nieodczytanym tutaj poza kartą strony. Później partner projektu avoev (TU Berlin, UDE). Strona nie podaje ankiety, liczników ani metryki.

## 6. Karty: galeria

Kolejność jak na [matsim.org/examples](https://www.matsim.org/examples/) w dniu odczytu.

| karta | popyt | podaż | kalibracja i walidacja | gdzie czytać dalej |
|---|---|---|---|---|
| Dakar | CDR z D4D | OSM | strona nie podaje metryki | Gueye i in., PDF na stronie galerii |
| USA | GPS jednego dnia, filtr do 2,7 mln urządzeń | OSM | korelacja rang VMT z FHWA; liczniki Florydy; RMSE podobny do modeli regionalnych Florydy; błąd bezwzględny duży | Gurram i in. 2019 |
| Open Île-de-France | eqasim, §2.2 | OSM + rozkłady, osobny etap pipeline | walidacja populacji wobec spisu i ankiety; kalibracja symulacji opisana jako osobna praca (ASC, przepustowości w implementacji monachijskiej) | Hörl i Balac 2021, TRC 130, 103291; docs eqasim-france |
| Paryż 2018 (Simunto dla GeoTwin) | spis, macierz dojazdów, dzienniczek; otwarte dane | OSM | strona nie podaje kalibracji. 10% z ok. 10 mln. Samochód, PT, pieszo i rower teleportem, taksówki stałe, car-sharing jako dowód techniczny | karta galerii. To nie jest eqasim |
| Szwecja | SAMPERS + SAMGODS | OSM, GTFS | konwersja modelu statycznego, nie ankieta. Otwarte 10% | Bischoff i in. 2019; repo `matsim-sweden` |
| Santiago | ankieta O-D 2012, współczynniki ekspansji, rejestr gruntów do losowania lokalizacji, karta Bip! do godzin | OSM, GTFS, winiety | ręcznie i automatycznie: podział modalny i natężenia. Szczegół algorytmu nieodczytany | galeria; rozdz. 84; SVN VSP `countries/cl/santiago`; repo `matsim-santiago` |
| Wiedeń | §2.1, §3.2 | OSM 2021 + GTFS (pt2matsim), SwissRailRaptor | udziały z populacji syntetycznej; CaDyTS 250/750; ok. 180 stacji | README AIT 2023.2; Müller i in. 2022, Sustainability 14(1):428 |
| Birmingham, AL | „małe dane” i dane otwarte; ride-hailing | model cyfrowego bliźniaka miasta średniego | trzy artykuły o budowie przy małej ilości danych i o mikromobilności. Treści artykułów nie czytałem, są za DOI w karcie | Guo i in. IEEE BigData 2019; Khalil i in. 2021 i SIGSPATIAL 2022; GitHub UberSim |
| Vorarlberg | ankieta 2013, plan użytkowania, POI, demografia. Ok. 380 tys. mieszkańców, cały kraj związkowy | OSM, poprawiana do routowalności | tryb z modelu zewnętrznego. Baza 10% i 100%. Bez towarów i urlopowiczów | Endbericht PDF na stronie galerii (niemiecki). Nieodczytany w całości |
| Niemcy | losowa realizacja MiD 2008, ok. 4 mln agentów, pełny dzień | główne drogi OSM, 360 tys. linków, ponad 4 mln obiektów | 2500 stacji i potoki O-D z nawigacji | galeria; rozdz. 70. Nowsze repo `matsim-germany` nie było tu rozbierane |
| Poznań | VISUM, szczyt poranny, rozciągnięty do południa | OSM | strona nie podaje dopasowania do liczników. Osobny wątek: 1000 taksówek, 5000 kursów, 2% z 250 tys. podróży indywidualnych w szczycie, dyspozycja on-line | rozdz. 79 |
| Singapur | HITS od LTA, użytkowanie URA, NAVTEQ | sieć Ordóñeza, PT Chakirova | film badawczy, „bez znaczenia dla polityki”. Liczniki i ERP przygotowywał Shah. Metryki na stronie brak | rozdz. 57; Vimeo FCL |
| Tel Awiw | model ABM na ankiecie 1996 | EMME/2 | strona: w planie lepsze lokalizacje wtórne i wybór lokalizacji w symulacji, żeby zejść do rozkładów czasu i odległości. Wyników tego kroku brak | rozdz. 91 |
| RPA, towar krajowy | łańcuchy z sieci złożonej | kraj | papier „w przygotowaniu” w chwili karty. Metoda bazowa: Joubert i Axhausen 2013 | galeria |
| Ruch lotniczy nad Europą | OAG Aviation | pojemności pasów w trakcie prac, gdy kartę pisano | pokaz doby, nie kalibracja popytu pasażerskiego | rozdz. 68 (kolej i lotnictwo europejskie; związek z tą kartą nie jest na stronie udowodniony) |
| Gauteng | spis; potem łańcuchy towarowe; w studium myta także Saturn (ruch zewnętrzny) | GIS, nie OSM | liczniki przygotowane w 2008 jako krok walidacji. Strona nie podaje GEH. Eksperyment to objazd po mycie | Joubert i in. 2010; rozdz. 69; PDF SATC 2010 na stronie |
| Padang | wszyscy w domu | ewakuacja | czas dojścia, nie licznik | rozdz. 76 |
| Monachium (galeria 2010) | MiD 2002, dojazdy, towary | VISUM | cel: emisje, nie raport dopasowania natężeń. Inny byt niż eqasim-Monachium z 2024 | rozdz. 58 |
| Seul | HHTS 2012, synteza, 10% z 21,5 mln | 16 384 węzłów, 32 768 linków, w tym buspasy i chodniki | „szczegóły w książce” | rozdz. 86. Nieodczytany |
| Joinville | spis 2010 + ankieta miasta. 135 652 agentów samochodem, reszta usunięta | shapefile IPPUJ, naprawa spójności NetworkX/QGIS | 20 linków, 7–8 rano. Autorzy: kalibracji brak, stacji za mało | galeria; rozdz. 72 |
| Sioux Falls | ankieta, spis, użytkowanie, macierz LeBlanc i in. 1975 jako szkielet pracy. Dochód gospodarstwa, wiek, płeć, samochód z ordered probit Giuliano i Dargay 2006 | sieć klasyczna wzbogacona o PT | scenariusz testowy, nie model miasta | Chakirov i Fourie 2014, IVT; rozdz. 59; `examples/siouxfalls2014` w kodzie MATSim |
| Quito | dwa przebiegi syntetyczne, nie ankieta dnia | OSM, główne i zbiorcze | optymalizacja świateł i oferty BRT. Walidacja wobec liczników nie jest opisana | Armas i Aguirre, lista prac na karcie; rozdz. 80 |
| Zurych | spis, mikrozensus, spis przedsiębiorstw. Pełne łańcuchy, czasy aktywności, tryb początkowy | sieć planistyczna, ponad 24 tys. węzłów, cała Szwajcaria i korytarze | porównanie z ok. 160 stacjami w regionie i ponad 500 w kraju. W filmie: 10%, 181 484 agentów, którzy choć raz wjechaliby w koło 30 km od Bellevue. Wybór samochód / nie-samochód | rozdz. 56 i 55. Historyczny rdzeń, z którego wyrosły modele krajowe |
| Berlin (karta) | najpierw model Kuttera, 10% kierowców, ponad 160 tys. agentów, szybko porzucony. Potem model BVG 2010 | sieć miasta, potem pełny PT | „problemy z danymi” przy pierwszej wersji. Metodyki BVG karta nie powtarza | rozdz. 53 i 54. Potem Open Berlin, §3.1, którego karta galerii jeszcze nie opisuje |
| Toronto | TASHA | EMME/2 | pierwsza symulacja w tydzień, bo popyt już był. PT od 2011. Metryki na stronie brak | rozdz. 93 |
| Aliaga | wszyscy w domu, trzy zestawy miejsc zbiórki | OSM ręcznie | porównanie czasu ewakuacji MATSim z Cube Avenue | Onelcin, Mutlu, Alver, Safety Science 60, 2013 |
| Caracas | macierz poranna, dzień domknięty odwróceniem | OSM plus atrybuty od firmy | kilka wag przeplanowania; zostawiony wariant najbliższy licznikom. Jeden ekran, nie rozkład błędu | rozdz. 65. Praca licencjacka Ampuero i Gómez, UCV |
| Izmir | plan transportowy, 47 stref | OSM ręcznie | „verification ratios” wobec stacji. Definicji wskaźnika strona nie podaje | Mutlu 2010, praca dyplomowa, Ege University |

## 7. Modele otwarte podlinkowane ze strony, których nie ma w galerii

Lista z [install/open-data-models](https://www.matsim.org/install/open-data-models) i z organizacji GitHub `matsim-scenarios` w dniu 2026-10-18. README czytane tam, gdzie kalibracja jest w pierwszym akapicie. Reszta repozytoriów istnieje, ale ich README nie wnosi metody (albo jest puste).

Wspólne zdanie trzech README VSP (Kelheim, Lipsk, i w wariancie Meksyku): scenariusz jest skalibrowany na **liczniki, podział modalny i rozkład odległości według trybu** (Meksyk: liczniki i podział modalny). Próbka Kelheim i Lipsk 25%, Meksyk 1%. Popyt Kelheim i Hamburg od Senozon. Metodyki krok po kroku w publicznych README nie ma.

| repozytorium | co dało się ustalić |
|---|---|
| `matsim-berlin` | §3.1 i §3.2. Bieżące README v6.4: kalibracja na liczniki, podział modalny, rozkłady odległości według trybu. Duże pliki na SVN VSP |
| `matsim-kelheim` | małe miasto i okolica, projekt KelRide. 25%. Popyt Senozon. Najbliższy publiczny analog skali „miasto powiatowe” w zestawie VSP. DOI 10.5281/zenodo.13132756 (v3.1.1). v3.0 zmieniło wybór trybu z pojedynczej podróży na subtour, GTFS, sieć i dane kalibracyjne |
| `matsim-leipzig` | 25%, ta sama formułka kalibracji. Google Doc niepubliczny |
| `matsim-hamburg` | popyt Senozon. O kalibracji README milczy |
| `matsim-metropole-ruhr` | z Regionalverband Ruhr. Popyt Senozon, CC-BY-NC. Domyślnie 3%, config 10% „nie jest w pełni zrelaksowanym stanie skalibrowanym”. Starsze `matsim-ruhrgebiet` (Stiftung Mercator, NEMO) |
| `matsim-mexico-city` | 1% CDMX + ZMVM. Liczniki i podział modalny |
| `matsim-los-angeles` | UC Davis + VSP, dane SCAG, grant Caltrans. README nie opisuje kalibracji |
| `matsim-sweden` | jak karta galerii |
| `matsim-ile-de-france` | jak eqasim |
| `matsim-santiago`, `matsim-joinville`, `matsim-munich` | odpowiedniki kart. README Monachium i Santiago nie były bogatsze niż karty |
| `ait-energy/matsim-model-vienna` | §3.2 |
| RPA, Joubert | sieci i populacje w wiki `matsim-code-examples`. Metodyki tam nie czytałem |
| przykłady w drzewie `matsim-org/matsim/examples` | demonstracja funkcji i testy, w tym Sioux Falls. To nie są modele miast |
| reszta org `matsim-scenarios` widziana 2026-10-18 | san-francisco, world, duesseldorf, nyc, stuttgart, sao-paulo, serengeti-park-hodenhagen, actitopp-ch, velbert, vulkaneifel, gladbeck, scenario-template, lausitz, california, melbourne-example-project, switzerland-freight, switzerland-railway, kyoto, oberlausitz-dresden, dresden, hannover, oslo, gunma. Nie czytałem ich README w tej sesji. Szablon `matsim-scenario-template` jest miejscem, od którego VSP każe zaczynać nowe miasto |

Starsze otwarte scenariusze VSP leżą też w [publicznym SVN](https://svn.vsp.tu-berlin.de/repos/public-svn/matsim/scenarios/).

## 8. Książka 2016: rozdziały, których galeria nie ma

Część IV zaczyna się rozdziałem 52, „Scenarios Overview” (Rieser i in.). Potem studia. Poniżej tylko te, których **nie** ma jako karty na stronie przykładów. Pełnego tekstu nie czytałem. Lista po to, żeby następna sesja wiedziała, gdzie szukać, a nie żeby udawać, że metoda jest już streszczona.

Baoding (61), Barcelona (62), Belgia i powodzie (63), Bruksela (64), Chociebuż i sygnalizacja (66), Dublin (67), Hamburg-Wilhelmsburg i ewakuacja (71), Londyn (73), Nelson Mandela Bay (74), Nowy Jork (75), Patna (77), Filipiny i pojazdy ratunkowe (78), Rotterdam i karta miejska (81), Samara (82), San Francisco Bay, SmartBay (83), Seattle (85), Szanghaj (87), Soczi (88), Sztokholm (89), Tampa i emisje (90), Tokio i hiperaścieżki (92), Trondheim (94), Yarrawonga i Mulwala, transport na życzenie (95), Jokohama (96).

Rozdziały pokrywające się z galerią, nadal nieodczytane w całości w tej sesji: 53 Berlin BVG, 54 Berlin CEMDAP-CaDyTS, 55 Szwajcaria, 56 Zurych, 57 Singapur, 58 Monachium, 59 Sioux Falls, 60 Aliaga, 65 Caracas, 68 lotnictwo i kolej, 69 Gauteng, 70 Niemcy, 72 Joinville, 79 Poznań, 80 Quito, 84 Santiago, 86 Seul, 91 Tel Awiw, 93 Toronto.

Rozdział 32 (CaDyTS) jest metodą, nie miastem. Zasada użyta w §3.1 pochodzi z opisu operacyjnego w VSPWP 19-01, nie z parafrazy całego rozdziału.

## 9. Co z tego jest przenośne jako metoda

Bez nowych parametrów do configu.

1. **Najpierw populacja i łańcuch, potem symulacja, potem licznik.** eqasim waliduje syntezę wobec spisu i ankiety, zanim porówna natężenia. Błąd na liczniku przy złej liczbie miejsc pracy albo złym udziale trybu nie mówi, który element jest zły.
2. **Dwie rodziny celu.** Ankieta (albo jej odpowiednik: Mikrozensus, SrV, Österreich unterwegs) trzyma zachowanie: udział trybu, udział w klasie odległości, grupa osób, godzina. Licznik trzyma wielkość na przekroju. Modele, które mają obie, nie wkładają ich do jednej wagi na stałe.
3. **CaDyTS jest narzędziem lokalizacji albo testem, nie zastępstwem ankiety.** W Berlinie jest włączony przy wyborze planu spośród pięciu lokalizacji i wyłączony przy wyborze trybu. Zostawienie go włączonego przy scenariuszu polityki wciąga błąd sieci w popyt. Test stabilności (ten sam run bez dopłaty) jest częścią metody, nie ozdobą.
4. **Stałe trybu aktualizuje się logarytmem stosunku udziałów**, z jedną stałą zamrożoną, w pętli krótkich symulacji albo wewnątrz iteracji (Rakow i in. 24-22; abstrakt MUM 2026 o kantonach). Ręczne kręcenie ASC jest w tych tekstach opisane jako stan, z którego eqasim dopiero wychodzi.
5. **Udział zagregowany nie wystarcza.** SBB ma 46 statystyk, w tym klasy odległości i grupy osób. Kelheim i Lipsk dopisują rozkład odległości według trybu. Model, który trafia w jeden udział samochodu i pudłuje odległość, jest uznawany za nieskalibrowany.
6. **Towar i tranzyt albo są agentami na wlocie, albo jawnym ścięciem przepustowości.** Berlin: agenci z licznika kordonowego, zamrożeni. Wiedeń: ok. 10% pojemności i obniżenie liczników, bez agentów. Oba sposoby są udokumentowane. Żaden nie polega na tym, że osobowe „same” wypełnią GPR.
7. **Próbka, na której się kalibruje, jest próbką, na której się raportuje.** Kelheim mówi to w README wprost. Open Berlin publikuje 10%, 3% i 1%, a kalibracja opisana w 19-01 jest na 10%.
8. **Sieć OSM bez korekty prędkości nie jest modelem czasu.** Berlin obniża prędkości miejskie o połowę, bo nie ma świateł. To jest kalibracja podaży, osobna od ASC.
9. **Dane z jednego dużego miasta albo z modelu statycznego są u nich punktem startu, nie dowodem.** Poznań, Szwecja, Toronto, Tel Awiw, Izmir, Caracas tak robią i albo kalibrują dalej do licznika, albo zostają modelem pokazowym. Galeria obu nie rozróżnia, dopóki nie ma wykresu.
10. **Małe miasto w zestawie publicznym VSP to Kelheim (25%, Senozon, liczniki + tryby + odległości), nie Berlin.** Procedura Kelheim nie jest w repozytorium. Jest w Google Doc. Następny krok, jeśli ten wzorzec ma być powtórzony, to ten dokument albo artykuł KelRide, nie karta galerii.

Czego ten przegląd nie rozstrzyga: jakie wagi scoringu, jakie ASC i jaki próg GEH albo SQV przyjąć dla Kutna. Tych liczb tu nie ma, albo są przypisane do innego miasta i innego roku.

## 10. Luki tego przeglądu

- Rozdziały książki z §8: znam tytuł i numer DOI, nie treść.
- Google Doc wewnętrzne Berlin, Kelheim, Lipsk, Hamburg, Meksyk, Los Angeles, Szwecja: linki są w README, dostęp ograniczony.
- Blog Arup na Medium: nieprzeczytany w całości.
- Artykuły Birmingham, Seul, Singapur, Vorarlberg Endbericht, praca Mutlu: znam, że istnieją, nie znam tabel.
- Rakow 2026 (*From Data to Simulation*): wskazany przez GitHub v7, nieczytany.
- PDF Scherr i in. 2020: liczby SQV z indeksu wyszukiwarki, nie z pliku w `data/raw`.
- Tabela 2 i 3 w VSPWP 19-01: ekstrakcja pomieszała kolumny, więc udziałów i ASC Berlina tu nie ma.
- Repozytoria z końca §7: sam fakt istnienia, bez metody.

Przy dopisywaniu do tego pliku: nowa sekcja albo akapit z datą i podpisem, kto czytał źródło. Nie poprawiać cudzych liczb po cichu.

## 11. Źródła

Strony, stan 2026-10-18:

- <https://www.matsim.org/examples/>
- karty `/examples/sbb`, `/examples/moia`, `/examples/arup`, `/examples/bvg`
- karty `/gallery/` wypisane w §6
- <https://www.matsim.org/install/open-data-models>
- <https://www.matsim.org/the-book/>

Publikacje i repozytoria, z których wzięte są twierdzenia o metodzie:

- Ziemke, Kaddoura, Nagel (2019), *The MATSim Open Berlin Scenario*, VSP Working Paper 19-01. <https://svn.vsp.tu-berlin.de/repos/public-svn/publications/vspwp/2019/19-01/ZiemkeEtAl2019OpenBerlinScenarioVSPWP.pdf>
- Rakow i in., VSP Working Paper 24-22, `RakowEtAl_MATSimBerlinEWGT.pdf` w `publications/vspwp/2024/24-22/` na tym samym SVN.
- Horni, Nagel, Axhausen (red.) (2016), DOI 10.5334/baw. Rozdz. 32 i część IV.
- Hörl, Balac (2021), TRC 130, 103291. Dokumentacja danych: <https://eqasim-org.github.io/eqasim-france/population/population_data.html>
- README: `matsim-scenarios/matsim-berlin` (gałąź `release/v6`), `matsim-kelheim`, `matsim-leipzig`, `matsim-hamburg`, `matsim-metropole-ruhr`, `matsim-mexico-city`, `matsim-los-angeles` (gałąź `v1.1`), `matsim-sweden`, `ait-energy/matsim-model-vienna`.
- Scherr, Bützberger, Frischknecht (2018), STRC, *Micro Meets Macro*. <https://www.strc.ch/2018/Scherr_EtAl.pdf>
- Scherr, Joshi, Manser, Frischknecht, Métrailler (2019), STRC, *MOBi.plans*. <https://www.strc.ch/2019/Scherr_EtAl.pdf>
- Scherr, Manser, Bützberger (2020), Transportation Research Procedia 49, 30–43. DOI 10.1016/j.trpro.2020.09.004. Liczby z indeksu PDF.
- Zwick, Axhausen (2020), STRC, *Analysis of Ridepooling Strategies with MATSim*. <https://strc.ch/2020/Zwick_Axhausen.pdf>
- Gurram, Sivaraman, Apple, Pinjari (2019), streszczenie na karcie galerii USA.
- Bischoff, Márquez-Fernández, Domingues-Olavarría, Maciejewski, Nagel (2019), MT-ITS, DOI 10.1109/MTITS.2019.8883384.
- Joubert, Axhausen (2013), Transportation. Link ze strony galerii RPA.
- Müller, Straub, Richter, Rudloff (2022), Sustainability 14(1):428. DOI 10.3390/su14010428. Cytowanie wskazane przez README Wiednia.
- Noty wydań `matsim-berlin` na GitHubie (v6.x, v7) o zakresie kalibracji, bez zastępowania artykułu.
- Abstrakty MUM 2026 na matsim.org (Szwajcaria, stałe kantonalne; SBB, generacja planów w Javie). Czytane jako abstrakty, nie jako artykuły.

**Grok, 2026-10-18.**
