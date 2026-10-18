# G5: dane do walidacji modelu i ruchu tła

Data: 2026-10-17. Etap 2a (zbieranie danych). **Nie zmieniałem modelu ani nie uruchamiałem MATSim.** Plik jest generowany przez `pipeline/g5_doc.py` z szablonu `reports/etap2/g5_walidacja/szablon.md`; tabele liczą skrypty `pipeline/g5_gpr.py`, `g5_gus_czasy.py`, `g5_mapa.py`.

## 0. Wnioski w skrócie

1. **GPR 2025 (GDDKiA) jest dostępny i wystarcza** do walidacji natężeń na drogach krajowych i wojewódzkich. Nowszy niż 2020/21, więc 2020/21 nie pobierałem. W obszarze naszej sieci jest **19 odcinków pomiarowych** (3× A1, 11× DK, 5× DW). Wszystkie mają przypisane linki (oba kierunki), tabela w §1.3, mapa `reports/etap2/g5_walidacja/gpr_mapa.png`.
2. **Brak publicznych danych dla ulic Kutna poza drogami krajowymi.** Nie znalazłem pomiarów miejskich (UM, ZDM, plan transportowy). Przez miasto przechodzi DK60/DK92, więc Sklęczkowska, Objazdowa i ul. Bitwy pod Kutnem są w GPR. Drogi miejskie i powiatowe trzeba wyprosić od zarządców (§2).
3. **„Płatna A1” w Kutnie nie istnieje.** Odcinek Toruń–Stryków jest bezpłatny dla aut osobowych, a opłata e-TOLL dotyczy pojazdów > 3,5 t. Natężeń na węźle Kutno nie ma w źródłach publicznych poza GPR (§2).
4. **Godzinowy profil z GPR nie istnieje.** GPR daje tylko udziały 6–18 / 18–22 / 22–6. Godzinowe krzywe są na wykresach stacji ciągłej 14005 Lisica (DK60c, 13 km od Kutna) i wymagają digitalizacji (§1.4).
5. **Ruch tła: rekomendacja to agenci wjazd–wyjazd na granicy sieci**, z natężeniem z GPR pomniejszonym o to, co model już generuje (§3).
6. **Prędkości D13 nie są za niskie względem GUS.** Czas swobodny w sieci to mediana **0,76 × czas GUS** (sieć szybsza o ok. 24%), przy zgodnej długości tras (§4). Nie ma sygnału do podnoszenia prędkości.

## 1. GPR 2025 (Generalny Pomiar Ruchu, GDDKiA)

### 1.1. Co jest i skąd

Strona: <https://www.gov.pl/web/gddkia/generalny-pomiar-ruchu-2025>. Pobrane do `data/raw/g5/gpr2025/` (sha256 w §6).

| plik | zawartość |
|---|---|
| `dk_wykaz.xlsx` | wykaz odcinków pomiarowych dróg krajowych: numer odcinka, pikiety, współrzędne punktu pomiarowego (lat/lon i X/Y) dla jezdni prawej i lewej, rejon GDDKiA |
| `dk_sdrr.xlsx` | SDRR (średni dobowy ruch roczny, pojazdy silnikowe) + **struktura rodzajowa** (motocykle, osobowe, mikrobusy, lekkie ciężarowe, ciężarowe bez/z przyczepami, autobusy, ciągniki) + **struktura kierunkowa** (udział jezdni lewej/prawej) |
| `dk_sdrdr.xlsx`, `dk_sdrl.xlsx` | to samo dla dni roboczych (SDRDR) i lata lipiec–sierpień (SDRL) |
| `dk_odcpom_web.zip` | SHP odcinków (EPSG:2180, linie) z SDRR/SDRDR/SDRL, 2 424 odcinki |
| `dw_wykaz.xlsx`, `dw_sdrr.xlsx` | drogi wojewódzkie (zmierzone przez zarządców, w tym ZDW Łódź, metodą GDDKiA): tylko SDRR i struktura rodzajowa, bez kierunków i bez SDRDR |
| `ruch_drogowy_2025.pdf`, `rozklady_srodowiskowe.pdf`, `dw_synteza.pdf` | opisy, rozkłady w okresach doby |

- GPR jest wykonywany co 5 lat; w 2025 pomiar był automatyczny lub z wideorejestracji (ok. 2,4 tys. odcinków krajowych). GDDKiA **nie udostępnia danych z pojedynczych dni pomiarowych**, tylko średnie roczne. Dane godzinowe z GPR nie są publikowane.
- Wartość z tabeli jest **reprezentatywna dla całego odcinka pomiarowego** (między węzłami), nie dla punktu. Punkt pomiarowy służy tylko do przypisania do linku.
- Wersja GPR 2020/21 (drogi wojewódzkie opublikowane 11.01.2022) istnieje (<https://www.gov.pl/web/gddkia/wyniki-generalnego-pomiaru-ruchu-202021-na-drogach-wojewodzkich>), nie pobierałem. Do analizy trendu można dociągnąć.
- Współrzędne: kolumny „X/Y” GDDKiA są podpisane odwrotnie względem konwencji (Y = północ). Dlatego `g5_gpr.py` bierze **lat/lon i transformuje do EPSG:2180 (E, N)**.

### 1.2. Metoda przypisania do linków (`pipeline/g5_gpr.py`)

1. Punkt pomiarowy (lat/lon → EPSG:2180). Z 68 punktów (strony P/L) w ramce sieci +5 km tylko 19 odcinków leży przy drogach naszej sieci. Reszta jest poza powiatem (sieć = powiat z buforem, a nie prostokąt).
2. Kandydaci: linki odpowiedniej klasy OSM. **ZAŁOŻENIE:** A/S → `motorway`/`trunk`; DK → `trunk`/`primary`/`secondary`; DW → `primary`/`secondary`/`tertiary`/`trunk`.
3. Link najbliższy punktowi (odległość do odcinka między węzłami, bo sieć nie ma geometrii kształtu; próg 60 m, dla A1 150 m), plus link **w kierunku przeciwnym** (azymut różny o > 150°, w odległości ≤ 150 m dla A1 lub ≤ odległość + 40 m dla pozostałych).
4. Natężenie na kierunek: A1 = SDRR × udział jezdni z tabeli GPR (0,49–0,51); pozostałe = SDRR × 0,5 (**ZAŁOŻENIE**, w tabelach DK jednojezdniowych i DW nie ma udziałów kierunkowych).
5. Do porównania z autami w modelu liczy się `lekkie_osob` = osobowe + mikrobusy + motocykle (model ma tylko samochody osobowe). Kolumna „ciężki+” to udział lekkich ciężarowych, ciężarowych i autobusów.

Wyniki: `scenarios/kutno/validation/gpr_punkty.csv` (wszystkie 68 punktów z wartościami, także poza siecią) i `gpr_linki.csv` (38 wierszy: link × odcinek).

### 1.3. Tabela: odcinki GPR 2025 w sieci Kutna

SDRR, SDRDR, SDRL w poj./dobę, oba kierunki, wszystkie pojazdy silnikowe. W kolumnie „linki” w nawiasie: klasa OSM, odległość punktu od linku, **SDRR na ten kierunek**. Jeden odcinek GPR to jedna wartość dla wielu linków naszej sieci, więc porównując z modelem, sumuj ruch po całym odcinku, nie po jednym linku.

| droga | nr odc. | odcinek | miejscowość punktu | SDRR | SDRDR | SDRL | osob.+mikro+moto | ciężki+ | linki (oba kierunki) |
|---|---|---|---|---|---|---|---|---|---|
| DK A1 | 71410 | W. KOWAL /DK91/ - W. KUTNO PŁN. /DK60/ | MOP STRZELCE | 32006 | 28203 | 43079 | 21248 | 34% | `4506143660003f` (motorway, 8 m, 16278)<br>`12784695850001f` (motorway, 10 m, 15728) |
| DK A1 | 91820 | W. KUTNO PŁN. /DK60/ - W. KUTNO WSCH. /DK92/ | SÓJKI-PARCEL | 35101 | 32404 | 44923 | 23406 | 33% | `2908981330004f` (motorway, 10 m, 17508)<br>`2908981320004f` (motorway, 10 m, 17593) |
| DK A1 | 91821 | W. KUTNO WSCH. /DK92/ - W. PIĄTEK /DW703/ | KASZEWY | 36976 | 33216 | 47317 | 26528 | 28% | `2908962250003f` (motorway, 7 m, 18969)<br>`2915802350003f` (motorway, 13 m, 18007) |
| DK 60 | 91115 | TOPOLA KRÓL. /DK91/ - KUTNO /OBWODNICA (UL. OBJAZDOWA (DK92))/ | LESZNO | 4089 | 4531 | 3896 | 3592 | 12% | `5284376810020r` (primary, 21 m, 2044)<br>`5284376810020f` (primary, 21 m, 2044) |
| DK 60 | 91124 | KUTNO /OBWODNICA 1: UL. OBJAZDOWA (DK92) - DK92, DW702/ | KUTNO /UL. OBJAZDOWA/ | 9341 | 10605 | 9573 | 7010 | 25% | `3177068500003f` (primary, 1 m, 4670)<br>`2446692050004f` (primary, 3 m, 4670) |
| DK 60a/60 | 91866 | KUTNO /OBWODNICA 2: DK92, DW702 - UL. SKRAJNA/ | KUTNO /UL. BITWY POD KUTNEM/ | 8193 | 8689 | 8594 | 6756 | 17% | `2485778070001r` (primary, 0 m, 4096)<br>`2485778070001f` (primary, 0 m, 4096) |
| DK 60 | 91878 | KUTNO /UL. SKRAJNA/ - W. KUTNO PŁN. /A1/ | SÓJKI | 8375 | 8747 | 9133 | 6837 | 18% | `2337913730002f` (primary, 1 m, 4188)<br>`2337913730002r` (primary, 1 m, 4188) |
| DK 91d | 91892 | KROŚNIEWICE /OBWODNICA 1: W. BŁONIE (DK92) - W. BARDZINEK (DK92)/ | KROŚNIEWICE | 6219 | 6409 | 7132 | 3633 | 41% | `3971697130020f` (primary, 7 m, 3110)<br>`11417907930005f` (primary, 9 m, 3110) |
| DK 91d | 91119 | KROŚNIEWICE /OBWODNICA 2: W. BARDZINEK (DK92) - W. MORAWCE/ | KROŚNIEWICE | 2762 | 2441 | 3506 | 1802 | 34% | `535075590000f` (primary, 5 m, 1381)<br>`4224826410001f` (primary, 7 m, 1381) |
| DK 92 | 91121 | CHODÓW - KROŚNIEWICE /W. BARDZINEK (DK91)/ | PNIEWO | 4514 | 4739 | 4994 | 2765 | 39% | `3016672060001f` (primary, 0 m, 2257)<br>`3016672060001r` (primary, 0 m, 2257) |
| DK 92a | 91122 | KROŚNIEWICE /OBWODNICA: W. BŁONIE (DK91) - DW581/ | KROŚNIEWICE | 4903 | 5293 | 5437 | 3107 | 36% | `3016639930001f` (primary, 6 m, 2452)<br>`4510873690000f` (primary, 6 m, 2452) |
| DK 92a/92 | 91123 | KROŚNIEWICE /DW581/ - KUTNO /DK60/ | POMARZANY | 6241 | 6917 | 6458 | 4588 | 26% | `2059715680002f` (primary, 6 m, 3120)<br>`4619668920011f` (primary, 8 m, 3120) |
| DK 92 | 91869 | KUTNO /DK60, DW702/ - W. KUTNO WSCH. /A1/ | SOKÓŁ /UL. SKLĘCZKOWSKA/ | 9872 | 11309 | 9675 | 7456 | 24% | `4496570650002f` (primary, 3 m, 4936)<br>`4461609300002f` (primary, 3 m, 4936) |
| DK 92 | 91125 | W. KUTNO WSCH. /A1/ - BEDLNO /DW583/ | ZŁOTNIKI | 9095 | 10262 | 9470 | 5688 | 37% | `5011849660001f` (primary, 3 m, 4548)<br>`4909889060000f` (primary, 4 m, 4548) |
| DW 573 | 10042 | KAMIENIEC - GR. WOJ. (ŁÓDZKIE) - ŻYCHLIN /DW583/ | JASTRZĘBIA | 1849 |  |  | 1626 | 12% | `2835770890014r` (secondary, 2 m, 924)<br>`2835770890014f` (secondary, 2 m, 924) |
| DW 581 | 10043 | ŁANIĘTA /GR. WOJ. (ŁÓDZKIE)/ - KROŚNIEWICE /DK92/ | GRODNO | 2337 |  |  | 1748 | 25% | `2296014200004f` (secondary, 0 m, 1168)<br>`2296014200004r` (secondary, 0 m, 1168) |
| DW 583 | 10044 | BEDLNO /DK92/ - DOBRZELIN /UL. NARUTOWICZA (DW583)/ | DOBRZELIN | 3719 |  |  | 3261 | 12% | `12054176470011f` (secondary, 6 m, 1860)<br>`12054176470011r` (secondary, 6 m, 1860) |
| DW 583 | 10045 | DOBRZELIN /UL. NARUTOWICZA (DW583)/ - ŻYCHLIN /DW573/ | ŻYCHLIN UL. TRAUGUTTA | 7134 |  |  | 6485 | 9% | `13369519080005f` (secondary, 0 m, 3567)<br>`13369519080005r` (secondary, 0 m, 3567) |
| DW 702 | 10049 | KUTNO (DK92) - PIĄTEK /UL. ŁĘCZYCKA (DW703)/ | GÓRKI PĘCŁAWSKIE | 3727 |  |  | 2972 | 20% | `2497842320002r` (secondary, 0 m, 1864)<br>`2497842320002f` (secondary, 0 m, 1864) |

Obserwacje (liczby z tabeli, bez interpretacji wykraczającej poza dane):
- A1: 32–37 tys. poj./dobę, 28–34% ciężki+. Ruch rośnie ku wschodowi (węzeł Kutno Płn. → Kutno Wsch. → Piątek).
- DK60/DK92 przez Kutno: 8,2–9,9 tys. na odcinkach miejskich (Sklęczkowska 9 872, Objazdowa 9 341). Poza miastem DK92 ku Krośniewicom 4,5–6,2 tys.
- SDRDR jest o 4–15% wyższe od SDRR na odcinkach DK60/DK92, a SDRL wyższe od SDRR na A1 (47 tys. vs 37 tys. na odcinku Kutno Wsch. – Piątek). Wynika to z sezonowości (A1 jako trasa nad morze).

### 1.4. Rozkład w ciągu doby i współczynniki

| co | wartość | źródło |
|---|---|---|
| Udział ruchu 6–18 / 18–22 / 22–6 (wszystkie DK) | 72,5% / 16,2% / 11,3% | `rozklady_srodowiskowe.pdf`, tab. 1 |
| j.w., drogi międzynarodowe (A1 to E75; zakładam, że jest w tej klasie) | 70,7% / 16,8% / 12,5% | j.w. |
| j.w., pozostałe DK | 75,0% / 15,4% / 9,6% | j.w. |
| Udział ruchu w 30./50./100./150./200. godzinie roku względem SDRR, odcinki o charakterze gospodarczym | 10,0 / 9,5 / 9,0 / 8,5 / 8,5% | SCPR R02_06_2025 |
| Wahania tygodniowe, odcinki gospodarcze, współczynniki wzgl. średniej: pn–nd | 1,03 / 1,01 / 1,02 / 1,07 / 1,13 / 0,90 / 0,85 | SCPR R02_04_2025 |
| Godzinowe krzywe dla pojazdów lekkich i ciężkich, dni robocze | **tylko jako wykres** w karcie stacji 14005 Lisica (R03_03, R03_04, R03_12), 2025 | `data/raw/g5/scpr2025/st_14005.pdf` |

Stacje ciągłego pomiaru (SCPR) w pobliżu: 14005 Lisica (DK60c Kutno–Gostynin, typ 8+1, SDRR 2025 = 9 351, zgodne z GPR 11104) i 30025 Dzięgielewo (DK92 Kłodawa–Krośniewice, pobrana karta `st_30025.pdf`, niezanalizowana). Stacje „Kutno WS” (10044) i „Kutno PN” (10100) są wymienione w karcie województwa łódzkiego (`karta_lodz.pdf`), ale bez wartości SDRR 2025 w karcie, **do wyjaśnienia z GDDKiA**. Trzy stacje e-TOLL na A1 (10618, 10629, 10636, odcinki 91821, 91820, 71410) są w karcie „T-R” bez danych, a dane nie są publiczne.

**Czego brakuje:** godzinowych natężeń per odcinek. Do dystrybucji godzinowej z GPR nie ma danych, więc profil trzeba wziąć ze stacji 14005 (po digitalizacji, jak `pipeline/digitize_gbr.py` dla GBR) albo z podziału 3-okresowego. Decyzja §5.

## 2. Pomiary miejskie w Kutnie i A1

- **Urząd Miasta / ZDM / plan transportowy:** nie znalazłem publicznych pomiarów natężeń na skrzyżowaniach ani planu zrównoważonej mobilności Kutna z diagnozą ruchu (kilka wyszukiwań, w tym w trybie rozszerzonym). Wynik negatywny nie dowodzi, że dokumenty nie istnieją, tylko że nie ma ich w indeksowanej sieci. Źródła do zapytania: BIP UM Kutno, starostwo (ZDP Kutno: drogi powiatowe), GDDKiA Oddział w Łodzi, Rejon w Kutnie (przetarg GDDKiA Łódź obejmował realizację GPR 2025 w Rejonie Kutno, TED 7743-2025), ZDW Łódź (<https://www.zdw.lodz.pl/generlany_pomiar_ruchu.html>).
- **Co mamy w mieście:** tylko DK60/DK92 z GPR (Sklęczkowska 9 872, Objazdowa 9 341, Bitwy pod Kutnem 8 193, DW702 3 727 do Piątku). Ulice miejskie nie są pokryte.
- **A1 węzeł Kutno:** A1 Toruń–Stryków jest bezpłatna dla osobówek (płatny jest tylko koncesyjny odcinek Gdańsk–Toruń), więc nie ma bramek ani danych z poboru. e-TOLL dotyczy pojazdów > 3,5 t i jego dane nie są publiczne. Natężenia na odcinkach między węzłami: GPR (§1.3), 32–37 tys. poj./dobę, w tym 3 odcinki wokół Kutna.
- **Natężenia na rampach węzłów** (Kutno Płn., Wsch.): nie ma w GPR. Można je tylko oszacować jako różnicę natężeń sąsiednich odcinków A1 (bez rozróżnienia kierunków): 71410 → 91820 → 91821 = 32,0 → 35,1 → 37,0 tys. To są sumy dwukierunkowe, więc różnica to saldo, nie wjazdy.

## 3. Ruch tła/tranzyt w MATSim przy ograniczonym obszarze: przegląd metod

Źródła pierwotne przeczytane w całości lub fragmentarycznie (pliki w `data/raw/g5/lit/`).

| podejście | co robi | źródło | dla nas |
|---|---|---|---|
| **A. Agenci towarowi z liczników, stałe O-D, poza wyborem lokalizacji** | Uproszczeni agenci towarowi dodani na podstawie liczników BASt na głównych arteriach do i z Berlina; ich początki i cele są stałe i wyłączone z kalibracji lokalizacji. Autorzy zaznaczają, że liczniki to jedyny nieotwarty składnik wejścia, ale dostępny w większości regionów. Całość kalibrowana CaDyTS względem liczników. | Ziemke, Kaddoura, Nagel, *The MATSim Open Berlin Scenario* (VSP WP 19-01, `ziemke2019_openberlin.pdf`, sekcja 2.3) | **Najbliższe naszym danym** (GPR = odpowiednik BASt). |
| **B. Macierz krajowa → przycięcie tras do granicy obszaru** | Przejazdy ciężarówek z Verkehrsverflechtungsprognose 2030 są trasowane po sieci krajowej; przecięcie trasy z granicą obszaru badań staje się nowym początkiem/końcem, godzina odjazdu opóźniona o czas dojazdu do granicy. Liczba pojazdów kalibrowana (ładunek średni) do liczników ciężarówek BASt. Kategorie: obie końcówki w obszarze, jedna, tranzyt, poza. | Lu, Martins-Turner, Nagel, *Creating an agent-based long-haul freight transport model for Germany* (VSP WP 22-02, `lu2022_longhaul_freight.pdf`, §2.3, §3) | Metoda przenosi się koncepcyjnie. **Nie mamy odpowiednika VVP 2030 dla Polski** (nie sprawdziłem, czy istnieje otwarty). |
| **C. Pełny model wirtualny: dalekobieżny + małoskalowy ruch gospodarczy + tranzyt** | Trzy procesy: trasy towarowe (VVP 2030; pełne ładunki jako osobne tury, drobnica przez VRP), małoskalowy ruch gospodarczy, tranzyt towarowy; wyniki scalane z modelem osób. Autorzy piszą, że dane dla Ruhry są szczegółowsze niż dla innych regionów, więc model nie przenosi się wprost. | Ewert, Nagel, MUM 2025, paper 3 (`MUM25_paper_3_Ewert.pdf`), repo `matsim-scenarios/matsim-metropole-ruhr` | Za ciężkie i dane niedostępne dla Polski. |
| **D. Brak tła, jawnie** | Model bez pełnego ruchu gospodarczego i tranzytu daje zbyt niskie dobowe natężenia, szczególnie na autostradach; autorzy wymieniają brak tranzytu spoza Berlina/Brandenburgii i słabe dane o ruchu gospodarczym. | Rakow, Kreuschner, Nagel, MATSim Berlin EWGT 2024 (`rakow2024_berlin_commercial.pdf`) | Potwierdza oczekiwany wynik: model samych dojazdów będzie poniżej GPR, szczególnie na A1. |

Uwaga: README scenariuszy Kelheim i Leipzig nie opisuje ruchu tła (sprawdzone, nic nie ma), więc ich nie cytuję.

### Rekomendacja (podejście A, z elementem B)

1. **Cele:** natężenia SDRDR (dni robocze, bo model symuluje dzień roboczy) z GPR 2025 na odcinkach wchodzących/wychodzących z sieci i w jej wnętrzu.
2. **Tło = agenci typu „external”, `home`/`work` zastąpione aktywnościami na linkach granicznych** (wjazd – wyjazd), osobny typ pojazdu dla ciężkich (`lekkie ciężarowe + ciężarowe + autobusy`), osobna subpopulacja, wyłączona z mode choice i z `ReRoute` ograniczona do innowacji czasu wyjazdu, bez strategii zmiany celu.
3. **Ile pojazdów:** natężenie GPR na granicy minus to, co model już generuje (dojazdy mieszkańców, przyjeżdżający D16). Bez odjęcia policzymy dwa razy. Wymaga liczenia wjazdów z istniejącego runu (linkstats × 1/sampleSize).
4. **Skąd–dokąd (O-D tranzytu):** brak macierzy. Pierwsze przybliżenie: pary wjazd–wyjazd na tej samej drodze (A1 → A1, DK92 → DK92, DK60 → DK60) i przejazdy między drogami w węzłach, kalibrowane do liczników odcinkowych (CaDyTS nie jest konieczny na start). To jest decyzja do podjęcia, nie fakt z literatury.
5. **Przeliczniki PCE** dla ciężkich: wymagają źródła (HBS lub wytyczne GDDKiA). **Nie wpisuję wartości „typowych”.**
6. **Skala próbki:** natężenia tła × `sampleSize` (25%), tak samo jak populacja, bo `flowCapacityFactor` = frakcja próbki.
7. **Porównanie:** GEH względem GPR na 19 odcinkach (sumy po linkach odcinka). Przed dodaniem tła zrobić **bazową tabelę „model vs GPR”** (osobówki, SDRDR), żeby widać było lukę, którą tło ma zamknąć.

## 4. Czas przejazdu: macierz dostępności GUS vs czas swobodny w sieci

- **GUS:** czas przejazdu autem osobowym między centroidami gmin (`gus_czas_do_kutna_2021.csv`, kierunek gmina → Kutno), licznie przez **openrouteservice na danych OSM (Geofabrik)**, bez kongestii (plik `info`, arkusz macierzy). Modelu prędkości ORS nie sprawdzałem.
- **Sieć:** `networkx`, najkrótszy czas po `length / freespeed` (freespeed = 0,8 × dozwolona, D13) z węzła najbliższego centroidowi gminy do węzła najbliższego centroidowi Kutna (1002011, 57 m). Uwzględnione gminy z centroidem ≤ 3 km od węzła sieci (29 z 3 130; reszta poza powiatem z buforem). Skrypt `pipeline/g5_gus_czasy.py`, wynik `gus_vs_siec.csv`, wykres `gus_vs_siec.png`.

| gmina (TERYT) | odl. centroid–węzeł [m] | GUS [min] | sieć [min] | sieć/GUS | GUS [km] | sieć [km] | v GUS [km/h] | v sieć [km/h] |
|---|---|---|---|---|---|---|---|---|
| Kutno (1002062) | 188 | 9.4 | 6.6 | 0.70 | 6.8 | 4.3 | 43 | 40 |
| Krzyżanów (1002052) | 512 | 12.3 | 11.1 | 0.90 | 10.1 | 10.2 | 49 | 55 |
| Strzelce (1002102) | 40 | 15.3 | 13.5 | 0.88 | 11.2 | 11.5 | 44 | 51 |
| Oporów (1002092) | 508 | 16.8 | 14.3 | 0.85 | 12.7 | 14.9 | 45 | 63 |
| Witonia (1004082) | 497 | 19.9 | 16.9 | 0.85 | 16.0 | 16.2 | 48 | 58 |
| Łanięta (1002072) | 538 | 24.5 | 18.7 | 0.76 | 16.4 | 19.4 | 40 | 62 |
| Nowe Ostrowy (1002082) | 244 | 24.7 | 19.4 | 0.79 | 17.2 | 17.3 | 42 | 54 |
| Krośniewice - obszar wiejski (1002045) | 114 | 25.1 | 19.4 | 0.78 | 18.0 | 18.3 | 43 | 56 |
| Krośniewice - miasto (1002044) | 38 | 25.9 | 19.4 | 0.75 | 16.2 | 17.0 | 38 | 52 |
| Piątek - miasto (1004064) | 1276 | 26.5 | 24.4 | 0.92 | 22.1 | 26.1 | 50 | 64 |
| Piątek - obszar wiejski (1004065) | 2359 | 26.9 | 24.4 | 0.91 | 23.1 | 26.1 | 52 | 64 |
| Żychlin - miasto (1002114) | 74 | 27.1 | 19.9 | 0.73 | 21.0 | 19.4 | 46 | 58 |
| Bedlno (1002022) | 239 | 27.4 | 19.2 | 0.70 | 20.2 | 19.6 | 44 | 61 |
| Gostynin (1404011) | 2387 | 29.0 | 23.5 | 0.81 | 24.5 | 23.4 | 51 | 60 |
| Daszyna (1004022) | 830 | 29.2 | 20.8 | 0.71 | 22.6 | 20.6 | 46 | 60 |
| Dąbrowice (1002032) | 94 | 32.8 | 25.2 | 0.77 | 24.8 | 24.7 | 45 | 59 |
| Góra Świętej Małgorzaty (1004032) | 1423 | 34.0 | 20.8 | 0.61 | 26.4 | 21.9 | 47 | 63 |
| Lubień Kujawski - obszar wiejski (418115) | 2899 | 34.8 | 25.3 | 0.73 | 46.3 | 24.8 | 80 | 59 |
| Szczawin Kościelny (1404052) | 1951 | 35.1 | 23.6 | 0.67 | 25.2 | 25.6 | 43 | 65 |
| Lubień Kujawski - miasto (418114) | 2270 | 35.5 | 25.3 | 0.71 | 46.5 | 24.8 | 79 | 59 |
| Żychlin - obszar wiejski (1002115) | 413 | 36.3 | 25.8 | 0.71 | 25.6 | 25.4 | 42 | 59 |
| Bielawy (1005022) | 324 | 37.2 | 30.6 | 0.82 | 36.9 | 33.2 | 60 | 65 |
| Pacyna (1404032) | 169 | 37.5 | 26.9 | 0.72 | 31.4 | 29.6 | 50 | 66 |
| Chodów (3009032) | 544 | 39.9 | 32.3 | 0.81 | 29.0 | 31.7 | 44 | 59 |
| Chodecz - miasto (418064) | 1734 | 41.1 | 33.8 | 0.82 | 53.2 | 35.0 | 78 | 62 |
| Zduny (1005102) | 387 | 41.9 | 30.3 | 0.72 | 31.2 | 31.1 | 45 | 62 |
| Chodecz - obszar wiejski (418065) | 1042 | 43.9 | 33.8 | 0.77 | 55.3 | 35.0 | 76 | 62 |
| Kiernozia (1005052) | 2565 | 49.5 | 33.5 | 0.68 | 39.6 | 34.5 | 48 | 62 |
| Przedecz - obszar wiejski (3009115) | 1755 | 51.0 | 33.9 | 0.66 | 37.5 | 35.1 | 44 | 62 |

![GUS vs sieć](../../reports/etap2/g5_walidacja/gus_vs_siec.png)

**Podsumowanie (29 gmin):** mediana `czas sieci / czas GUS` = **0,76** (kwartyle 0,71–0,82, min 0,61, max 0,92). Długość tras: mediana 0,99, czyli **trasy są zgodne, różni się prędkość**: mediana średniej prędkości trasy 60 km/h (sieć) vs 46 km/h (GUS).

**Wnioski:**
1. Prędkości D13 (z factor 0,8) dają czasy **krótsze o ok. 24%** niż GUS/ORS, więc nie ma sygnału, że sieć jest zbyt wolna. Sieć jest raczej szybsza niż ORS.
2. Nie wiadomo, kto ma rację: **brak pomiaru niezależnego** (ORS to też model). Różnica może wynikać z założeń prędkości ORS albo z naszego `rural=90`/`factor=0,8`; źródła różnicy nie rozstrzygałem.
3. Odstępstwa od długości trasy: gm. Lubień Kujawski (0418114/0418115) i Chodecz (0418064/0418065): GUS 46–55 km, sieć 25–35 km (km_ratio 0,53–0,66). Ścieżki są inne, **do wyjaśnienia** (np. most/droga poza obszarem lub inny wybór trasy ORS). Gmina Kutno (wiejska, 1002062) ma ratio 0,70/0,64 przy snap 188 m.
4. Ograniczenie metody: centroid ≠ dom, a czas swobodny ≠ czas w szczycie. Test nie sprawdza kongestii, tylko spójność prędkości swobodnych.

## 5. Decyzje do podjęcia przez użytkownika

1. **Wybór podejścia do ruchu tła.** Rekomenduję A (agenci „external” z GPR minus ruch już generowany, §3). Alternatywy: B (wymaga macierzy krajowej, której nie mamy), brak tła (zostawić model dojazdów i walidować tylko korytarz Kutno–Kutno z ostrożnym wnioskiem).
2. **Którą wartość GPR uznać za cel:** SDRDR (dzień roboczy, rekomendowane) czy SDRR. Dla DW jest tylko SDRR.
3. **Digitalizacja profilu godzinowego** stacji 14005 Lisica (DK60c) jako profil tła i do porównania godzinowego, czy zostać przy podziale 3-okresowym (72,5/16,2/11,3%). Rekomenduję digitalizację: to jedyne godzinowe dane o ruchu drogowym w okolicy, a profil jest już w pobranym pliku.
4. **Pomiary miejskie:** czy wysyłać zapytania do UM Kutno, ZDP Kutno, GDDKiA Rejon Kutno, ZDW Łódź (e-mail/wniosek o informację publiczną). Bez tego walidacja obejmuje tylko drogi krajowe i wojewódzkie.
5. **Prędkości D13:** zostawić (rekomendacja; GUS nie wskazuje na zaniżenie), czy zdobyć niezależny pomiar czasów (np. kilka tras testowych w godzinach pozaszczytowych) i dopiero wtedy ruszać `factor`/`rural`.
6. **PCE dla ciężkich pojazdów:** wskazać źródło (wytyczne GDDKiA/HBS) zanim tło ciężarowe trafi do modelu.
7. **GPR 2020/21:** dociągnąć do analizy trendu , czy 2025 wystarcza.

## 6. Wiersze do manifestu (`data/manifest.csv`)

Nie edytowałem manifestu. Format: `path,url,downloaded_utc,bytes,sha256`. Pliki pochodne (`*.txt` z `pdftotext`, `shp/` rozpakowane z zip) pominięte.

```
data/raw/g5/gpr2025/dk_wykaz.xlsx,https://www.gov.pl/attachment/b3083bea-6336-45a9-b304-df68e95a3cb3,2026-10-17,518485,89a0838be762bd21d2d488fad9a6f6513729893eef17ddfe3ee3ef64de5cc978
data/raw/g5/gpr2025/dk_sdrr.xlsx,https://www.gov.pl/attachment/28194e66-2fb2-4dd7-becf-fedcf2b26908,2026-10-17,449806,dfa0756a15b0ecd358a44870a48a83eb11c472f48d97c98895c20ebc42fa4b58
data/raw/g5/gpr2025/dk_sdrdr.xlsx,https://www.gov.pl/attachment/a6686f5b-db6d-4077-b37b-b7758ffa805b,2026-10-17,338232,a179a4ff5f1025092b4b83700d1469cc1030d604dbdc134035a7472e3e4f2c2f
data/raw/g5/gpr2025/dk_sdrl.xlsx,https://www.gov.pl/attachment/364315a0-b9bd-4b18-a622-90697f60d66d,2026-10-17,338476,092687da01979fb804e026b278fe22362fab8d5b4e690cf15d0cc0517e5ea1e6
data/raw/g5/gpr2025/dk_odcpom_web.zip,https://www.gov.pl/attachment/7f8ca805-e384-4802-bf10-d36538e6ef84,2026-10-17,254875,568f2b787a9732d7b5b66f87716ede171825caf33a0ec676dfe9aeb12a7b1bb6
data/raw/g5/gpr2025/dw_wykaz.xlsx,https://www.gov.pl/attachment/866ec42e-25fe-41f1-9693-17712d7b0e38,2026-10-17,651384,dcab51ddb0d07b28110fbca3cd5a656a27a4251167f2830ec3ea8c6e92f8d389
data/raw/g5/gpr2025/dw_sdrr.xlsx,https://www.gov.pl/attachment/17ff216a-615f-4593-afa9-e62d5bffc738,2026-10-17,479837,f5eb1264e94ff1b6a61631401040739223d75861df390cfea6bb53d1ca241096
data/raw/g5/gpr2025/ruch_drogowy_2025.pdf,https://www.gov.pl/attachment/8d1e9123-12e8-4611-8397-d5b129e7630a,2026-10-17,5342750,92f4709c0516e9cfd9650498a290e54bac2340bb21bf059289d90078babc8938
data/raw/g5/gpr2025/rozklady_srodowiskowe.pdf,https://www.gov.pl/attachment/52b2e6d3-7104-4f1d-baa1-73ef172310ca,2026-10-17,1014837,9446a2ee9906eeaedcf7477c9182600dce7e44f5673fd3932854955b6a95eea8
data/raw/g5/gpr2025/dw_synteza.pdf,https://www.gov.pl/attachment/5b21e9c5-40f5-41c3-ae84-f0479b275669,2026-10-17,3900853,4c99eb2873c419599fc4dae6361846a68164deb2dd417d85aeb35912ae89d738
data/raw/g5/scpr2025/r02_04.pdf,https://www.gov.pl/attachment/3b78214f-a760-4336-a669-981d4c13978b,2026-10-17,90566,25014d3cd03445071410822f84b325b667e614b14ad34120c4bd75adf8477687
data/raw/g5/scpr2025/r02_05.pdf,https://www.gov.pl/attachment/4a8942cd-2508-4448-b215-02d45a1f8376,2026-10-17,105505,9ce4d9eeba23148e936a01987d83fed2e11805cb6e16c0f519ac8c25e831ec0c
data/raw/g5/scpr2025/r02_06.pdf,https://www.gov.pl/attachment/dd721b73-833d-462d-b44a-f7591ef0d0df,2026-10-17,83546,887dd281de0ea06122ea0347190be17f0258ed4acba00ee7569f20f661b7f106
data/raw/g5/scpr2025/karta_lodz.pdf,https://www.archiwum.gddkia.gov.pl/frontend/web/userfiles/articles/s/stacje-ciaglych-pomiarow-ruchu-d_41706/LODZ/2025/R00_02_10_2025.pdf,2026-10-17,307343,549ae64f8aeb7bca45106ecb0d09617c1badacafaced107d5ca6fc3c4cc96e2e
data/raw/g5/scpr2025/st_10617.pdf,https://www.archiwum.gddkia.gov.pl/frontend/web/userfiles/articles/s/stacje-ciaglych-pomiarow-ruchu-d_41706/LODZ/2025/10617_2025.pdf,2026-10-17,3712635,dfdd2761579b96847dae558fa107aa9f571ea3de79255d4f4b4e151d63890dc5
data/raw/g5/scpr2025/st_10636.pdf,https://www.archiwum.gddkia.gov.pl/frontend/web/userfiles/articles/s/stacje-ciaglych-pomiarow-ruchu-d_41706/LODZ/2025/10636_2025.pdf,2026-10-17,3673740,d819954057ff4528efebf7ec69c92b0757f0233617fa64552e127d5e3190e963
data/raw/g5/scpr2025/st_14005.pdf,https://www.archiwum.gddkia.gov.pl/frontend/web/userfiles/articles/s/stacje-ciaglych-pomiarow-ruchu-d_41706/WARSZAWA/2025/14005_2025.pdf,2026-10-17,3770146,d9438e26eb3edc6dbc2a59987658dc94246850ffadcc0575783d8f7d435f563d
data/raw/g5/scpr2025/st_30025.pdf,https://www.archiwum.gddkia.gov.pl/frontend/web/userfiles/articles/s/stacje-ciaglych-pomiarow-ruchu-d_41706/POZNAN/2025/30025_2025.pdf,2026-10-17,3857426,0d56d70abc005e75a1b84da89ff62f6f2bbbe178e4ff248e61f67bf137936b97
data/raw/g5/lit/MUM25_paper_3_Ewert.pdf,https://matsim.org/conferences/mum2025/abstracts/MUM25_paper_3.pdf,2026-10-17,223748,8c2edd7cfd6b0997db481e1b66afdde514e9b20b0e0ae3e323a229641a248177
data/raw/g5/lit/ewert_slides.pdf,https://matsim.org/conferences/mum2025/presentations/ewert.pdf,2026-10-17,2708554,23323f3700e968f4c8a304e4dab03a42d80a18324db73d1054dcb756e934c559
data/raw/g5/lit/lu2022_longhaul_freight.pdf,https://svn.vsp.tu-berlin.de/repos/public-svn/publications/vspwp/2022/22-02/LuEtAl2022LongHaulFreightGER_submitted.pdf,2026-10-17,10585866,c55211acffb4c029389657e5fca1ba3a89772afa241a52995c262ab085bef2fa
data/raw/g5/lit/rakow2024_berlin_commercial.pdf,https://svn.vsp.tu-berlin.de/repos/public-svn/publications/vspwp/2024/24-22/RakowEtAl_MATSimBerlinEWGT.pdf,2026-10-17,6729523,54b1e07e0f5cf9d4733efaa1b3ca4c71024a15a198aa4bd7559b7ab72a0c7f0d
data/raw/g5/lit/ziemke2019_openberlin.pdf,https://svn.vsp.tu-berlin.de/repos/public-svn/publications/vspwp/2019/19-01/ZiemkeEtAl2019OpenBerlinScenarioVSPWP.pdf,2026-10-17,2274661,5b6b7209a2e982edfc765a81e4ec4504d7bbf4eeccbccd72968b0f062e973dc8
```

## 7. Wiersze do `docs/ZRODLA.md` (propozycja, nie edytowałem)

- **GPR 2025 DK i DW (GDDKiA):** UŻYTE w G5. SDRR/SDRDR/SDRL + struktura rodzajowa i (A1) kierunkowa na 2 416 odcinkach DK, SDRR + struktura na DW; 19 odcinków w sieci Kutna. Ograniczenia: wartość na odcinek, nie punkt; bez godzin; DW bez kierunków i SDRDR.
- **SCPR 2025 (GDDKiA):** POBRANE (R02_04/05/06, karty stacji 14005, 30025, 10617, 10636, karta woj. łódzkiego). Godzinowe krzywe tylko jako wykres.
- **Literatura ruchu tła (VSP):** Ziemke 2019, Lu 2022, Rakow 2024, Ewert 2025 (patrz §3).
- **Macierz dostępności GUS vs sieć:** UŻYTE w G5 (§4).
