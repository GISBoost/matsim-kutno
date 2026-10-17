# G2: dane o liczbie i lokalizacji miejsc pracy w Kutnie

Data badania: 2026-10-17. Zakres: tylko zbieranie danych i ocena; model (D7) bez zmian. Pliki w `data/raw/g2/`, skrypty `pipeline/g2_*.py`.

## 1. Wynik w skrócie

1. **Jest kotwica liczby miejsc pracy dla samego Kutna, nowsza i lepsza niż w ZRODLA.md zakładano.** BDL GUS ma od 2023 r. tablicę **„Pracujący w gospodarce narodowej wg płci i siedziby pracy głównej” (P4508)** na poziomie gminy. Kutno (miasto, TERC 1002011, BDL `051011902011`): **17 486 (2024), 17 251 (2025)**. Dane z rejestrów ZUS/KRUS, więc obejmują też podmioty ≤ 9 osób i rolników ubezpieczonych w KRUS.
2. **To jest liczba „wg adresu siedziby płatnika”, nie faktycznego miejsca pracy.** Ta sama konwencja co macierz dojazdów NSP 2021 (adres pracodawcy). Oddział firmy z siedzibą w Warszawie liczy się w Warszawie. Dla Kutna to błąd w obie strony, którego z danych publicznych nie da się oszacować.
3. **Model F3 ma dziś o ok. 47% więcej miejsc pracy niż ta kotwica**: 17 546 mieszkańców (wszyscy pracują w Kutnie) + 8 186 przyjeżdżających = 25 732 (PROGRESS.md:27) wobec 17 486 w BDL. Mieszkańców pracujących *gdziekolwiek* BDL podaje 17 255 (2024), czyli prawie dokładnie tyle, ile model przypisuje do pracy w Kutnie. Wniosek: z 17,5 tys. etatów w mieście ok. 8,2 tys. zajmują przyjezdni, więc w mieście pracuje tylko ok. 9,3 tys. mieszkańców (ok. 54%), a ok. 8 tys. wyjeżdża (D3 pomija wyjeżdżających). To decyzja dla użytkownika (sekcja 6).
4. **Granularniej niż gmina nie ma nic publicznego z liczbą pracujących.** Siatki GUS i punkty adresowe dotyczą ludności i budynków mieszkalnych. REGON daje lokalizację, ale zapytania są pojedyncze, a klasę wielkości zwraca tylko część raportów (niepotwierdzone). Lokalizację wewnątrz miasta zostaje szacować, a wagi „powierzchnia budynku” mogą zostać, tylko przeskalowane do kotwicy i z dodatkiem listy znanych dużych zakładów.

## 2. Tabela źródeł

| źródło | URL | granulacja | rok | definicja | ograniczenia | status |
|---|---|---|---|---|---|---|
| **BDL P4508** pracujący wg płci i siedziby pracy głównej | https://bdl.stat.gov.pl/api/v1/data/by-unit/051011902011?var-id=1735396&year=2024 (zmienne 1735396 ogółem, 1735397 M, 1735398 K) | gmina (poz. 6), roczne, stan na koniec miesiąca | 2023–2025 | Osoby pracujące wg adresu siedziby płatnika składek pracy głównej. Rejestry ZUS + KRUS (+ MF). Praca główna: jedna na osobę. | Bez podziału na PKD i wielkość podmiotu na poziomie gminy. Siedziba płatnika ≠ faktyczne miejsce. Dla brakujących adresów imputacja losowa wg udziału płatników w gminach województwa. | **pobrane** `bdl_kutno.json` |
| **BDL P4507** pracujący w podmiotach ≤ 5 pracujących, wg *miejsca zamieszkania* | …var-id=1735395 | gmina | 2023–2025 | Mieszkańcy gminy pracujący w mikropodmiotach (≤ 5). | Wg zamieszkania, nie pracy. Kontekst: ok. 16% mieszkańców pracujących. | **pobrane** |
| **BDL P2613** podmioty wg klas wielkości (REGON, wariant „rok”) | zmienne 74107 (ogółem), 74105 (0–9), 74103 (10–49), 74101 (50–249), 74099 (250–999), 74097 (1000+) | gmina | 2015–2025 | Podmioty gospodarki narodowej w REGON wg liczby pracujących. | Liczba *podmiotów*, nie osób. Siedziba podmiotu. | **pobrane** `bdl_podmioty_pkd.json` |
| **BDL P4500/P4502** pracujący wg sekcji PKD, NSP 2021 | …data/by-unit/051011902000?var-id=…&year=2021 | **tylko powiat** (poz. 5) | 2021 | Pracujący w tyg. 25–31.03.2021 (≥ 1 h pracy dla zarobku lub formalnie zatrudniony). P4502 = ludność rezydująca. | Powiat kutnowski, nie samo Kutno. | **pobrane** |
| BDL P4427, P1966, P2834 (NSP, wg PKD/faktycznego miejsca pracy) | — | tylko woj./makroregion (poz. 3) | 2021 | j.w. | Za gruba. | sprawdzone, nie pobierane |
| BDL P4456 pracujący wg wielkości podmiotu, płci i *zamieszkania* | — | powiat (poz. 5) i woj. | 2022–2026 | | Nie wg miejsca pracy i nie gmina. | sprawdzone, nie pobierane |
| **GUS zeszyt metodologiczny** „Pracujący w gospodarce narodowej wg źródeł administracyjnych” | https://stat.gov.pl/files/gfx/portalinformacyjny/pl/defaultaktualnosci/5818/9/1/1/zeszyt_metodologiczny_pracujacy_w_gospodarce_narodowej_wedlug_zrodel_administracyjnych_.pdf | — | od grudnia 2022 | Definicja P4508: „Przy prezentowaniu danych o pracujących według cech płatnika (adres siedziby płatnika, sekcja PKD płatnika) wykazywane są cechy płatnika pracy głównej” (s. 15). Prezentacja wg gminy siedziby pracy głównej i **wielkości płatnika (liczba pracujących u płatnika)** jest w zakresie badania (s. ok. 1304–1311 tekstu). | Mikrodane tylko w Operacyjnej Bazie Mikrodanych GUS (dostęp na wniosek). | **pobrane** (tło metodyczne) |
| GUS raport 2019 „Opracowanie metodologii i oszacowanie liczby pracujących … według głównego miejsca pracy … na poziomie powiatów” | https://stat.gov.pl/files/gfx/portalinformacyjny/pl/defaultaktualnosci/6329/5/1/1/raport_opracowanie_metodologii_i_oszacowanie_liczby_pracujacych_w_gospodarce_narodowej.pdf | powiat | 2019 | Stara metoda eksperymentalna. | Nieaktualne wobec P4508. | pobrane (tło, nieczytane w całości) |
| GUS ESRP „Eksperymentalne statystyki rynku pracy” | https://esrp.stat.gov.pl/ESRP/ | wg zeszytu: gminy, PKD, wielkość płatnika | — | Aplikacja wizualizacyjna do danych z rejestrów. | Serwer zwracał HTTP 503 (2026-10-17). Nie wiadomo, czy ma eksport i jaką granulację na gminę. | **do sprawdzenia** |
| NSP 2021, pracujący wg miejsca pracy | https://stat.gov.pl/spisy-powszechne/nsp-2021/nsp-2021-wyniki-ostateczne/dojazdy-do-pracy-w-swietle-wynikow-nsp-2021,8,2.html | woj./powiat, macierz gmina–gmina (już mamy) | 2021 | Dojazdy z rejestrów, miejsce pracy = adres pracodawcy. | Brak tablicy „pracujący wg miejsca pracy” na poziomie gminy poza macierzą (która pomija < 3 osób i ruch wewnątrz gminy). Nic poniżej gminy. | macierz już użyta (F3) |
| **GUS statystyczne punkty adresowe** (ATOM ADR) | https://geo.stat.gov.pl/atom-web/atom/ADR (GeoJSON 287 MB, SHP 337 MB, stan 1.01.2026, EPSG:2180) | punkt (budynek mieszkalny) | 2026 | Punkty adresowe **budynków mieszkalnych** z NOBC/TERYT. Atrybuty: `WW,PP,GG` (TERYT), `REJ` (rejon), `OBW` (obwód spisowy), `MSC`, `ULICA`, `NRADR`, `X,Y`, `TERYT`. | **Zero informacji o podmiotach i pracy.** Dla G2 bezużyteczne, dla G3 przydatne (patrz 5). | **pobrane**; wycinek Kutna `adr_kutno_2026_0.csv` (4 807 punktów, 241 par rejon/obwód) |
| GUS siatki NSP 2021 / Portal Geostatystyczny | https://portal.geo.stat.gov.pl/ ; ATOM `…/atom/PD` | siatka 1 km | 2021 | Rezydenci NSP 2021. | Nie znalazłem siatki podmiotów ani pracujących. Wyszukiwanie ogólne (nie sprawdzałem katalogu ręcznie). | brak danych o pracy |
| **REGON BIR1.1/1.2** (API SOAP) | https://api.stat.gov.pl/Home/RegonApi?lang=en | pojedynczy podmiot (wyszukiwanie po REGON, NIP, KRS) | bieżący | Adres, PKD, status. | Darmowe, klucz produkcyjny przez e-mail na regon_bir@stat.gov.pl (firma: nazwa, REGON, osoba kontaktowa, adresy IP, liczba zapytań/mies.; administracja: opis zastosowania). Limitów strona nie podaje. Klucz testowy (publiczny) łączy się z bazą testową ze starymi, zanonimizowanymi danymi. **Strona nie wspomina o klasie zatrudnienia**, dokumentacja techniczna (`GUS-Regon-ws-BIR11-Eng-docs_v1.11.zip`) nieczytana. Brak wyszukiwania po gminie/PKD (trzeba znać identyfikator). | do pozyskania, wymaga zgody/działania użytkownika |
| **CEIDG, Hurtownia danych** | https://dane.biznes.gov.pl | pojedyncze wpisy, raporty zbiorcze | bieżący | Rejestr jednoosobowych działalności. | Wymaga zarejestrowania i Profilu Zaufanego. Pola i format niesprawdzone. CEIDG nie ma liczby pracowników. Podmioty 0–9 dominują (95,9% w Kutnie wg P2613), ale większość to 1 osoba. | do pozyskania (opcja) |
| KRS (API) | https://api-krs.ms.gov.pl | podmiot | bieżący | Spółki, fundacje. | Nie sprawdzałem. Zwykle bez zatrudnienia (sprawozdania finansowe w innym module). | nie badane |
| **Urząd Miasta Kutno, tereny inwestycyjne** | https://um.kutno.pl/print/pdf/node/52 | strefa | nieznany (strona bez daty) | „Na terenie Kutnowskiej Strefy Ekonomicznej funkcjonuje ponad 60 firm … które zatrudniają ok. 9000 osób.” KPAP założony 1998, ok. 370 ha, dzielnica Sklęczki. | Bez daty, deklaracja urzędu. Obejmuje „strefę” szerzej niż podstrefa ŁSSE. | **pobrane** `um_kutno_node52.pdf` |
| **Urząd Miasta Kutno, lista zezwoleń Podstrefy Kutno** | https://um.kutno.pl/print/pdf/node/176 | firma (z powierzchnią działki w ha) | do 2020 r. | „29 zezwoleń … udziałem 23 firm. Zatrudnienie … ok. 2200 osób.” 39 wpisów z datą i powierzchnią działki (np. Fuji Seal 11,81 ha, Uma Investments 10,99 ha, Lampre 9,58 ha, Fresenius Kabi 7,66 ha, Kofola/Hoop 6,49 ha, DS Smith 6,33 ha, Printpack 6,52 ha). | Zatrudnienie tylko łączne. Powierzchnie to działki w zezwoleniu, nie hale. Lista bez adresów. | **pobrane** `um_kutno_node176.pdf` |
| Fresenius Kabi Polska | https://kutno.net.pl/wydarzenia/rozbudowuja-strategiczny-zaklad-w-tej-branzy-kutno-staje-sie-kluczowe-dla-calej-europy/YO83zInmy5jnwV14F02J | zakład | 27.05.2026 | 2 200 pracowników w Polsce (Kutno, Błonie, Stryków, Wrocław, Warszawa) łącznie. | Brak liczby dla Kutna. | tylko cytat |
| Polfarmex S.A. | https://www.aplikuj.pl/pracodawca/7974/polfarmex-s-a | zakład | nieznany | Sam podaje ok. 700–800 (profile: 501–1000). | Niespójne źródła wtórne. | tylko cytat, niezweryfikowane |

## 3. Liczby dla Kutna (miasto, TERC 1002011)

**Pracujący wg siedziby pracy głównej (P4508), osoby, stan na koniec miesiąca (źródło: BDL API, `data/raw/g2/bdl_kutno.json`):**

| rok | ogółem | mężczyźni | kobiety |
|---|---|---|---|
| 2023 | 17 460 | 9 162 | 8 298 |
| 2024 | 17 486 | 9 098 | 8 388 |
| 2025 | 17 251 | 8 929 | 8 322 |

**Pracujący wg miejsca zamieszkania (P4507 „ogółem”), czyli mieszkańcy Kutna pracujący gdziekolwiek:** 17 258 (2023), 17 255 (2024), 16 853 (2025). Z tego w podmiotach ≤ 5 pracujących: 2 851, 2 757, 2 673.

**Podmioty REGON wg klas wielkości (P2613, rok, gm. Kutno-miasto), źródło: `bdl_podmioty_pkd.json`:**

| rok | ogółem | 0–9 | 10–49 | 50–249 | 250–999 | 1000+ |
|---|---|---|---|---|---|---|
| 2021 | 4 402 | 4 184 | 154 | 57 | 7 | 0 |
| 2024 | 4 407 | 4 203 | 142 | 56 | 6 | 0 |
| 2025 | 4 429 | 4 231 | 140 | 52 | 6 | 0 |

Z samej klasy wielkości wynika dolne ograniczenie zatrudnienia w dużych zakładach: 6 podmiotów ≥ 250 (≥ 1 500 osób) i 52 podmioty 50–249 (2 600–12 900). To zgadza się co do rzędu wielkości z 17,5 tys. etatów, ale nie wskazuje, gdzie one są.

**Struktura branżowa (tylko powiat kutnowski, NSP 2021, P4500, pracujący wg PKD; to nie jest samo Kutno):** ogółem 41 491; przetwórstwo przemysłowe (C) 10 345 (24,9%); handel (G) 5 527 (13,3%); rolnictwo (A) 4 824 (11,6%); transport i magazynowanie (H) 3 632 (8,8%); administracja publiczna (O) 2 402 (5,8%); edukacja (P) 2 530 (6,1%); ochrona zdrowia (Q) 2 226 (5,4%); budownictwo (F) 2 388 (5,8%); administrowanie (N) 1 852 (4,5%). Kutno jako miasto ma ponad te proporcje więcej usług publicznych i handlu, a mniej rolnictwa, ale to nie jest pomiar (brak danych poniżej powiatu).

**Porównanie z modelem (PROGRESS.md:27):**

| wielkość | model F3 (100%) | BDL / GUS |
|---|---|---|
| miejsca pracy w Kutnie | 25 732 (17 546 + 8 186) | 17 486 (P4508, 2024) |
| mieszkańcy pracujący w Kutnie | 17 546 (wszyscy) | ok. 9,3 tys. (= 17 486 − 8 186 przyjezdnych, ostrożnie: patrz niżej) |
| mieszkańcy pracujący gdziekolwiek | n/d | 17 255 (P4507, 2024) |

Uwagi do porównania: (a) 8 186 przyjezdnych to NSP 2021 tylko pracownicy najemni i bez przepływów < 3 osób, a P4508 jest z 2024 r. i obejmuje samozatrudnionych, więc „9,3 tys.” to rząd wielkości, nie estymata. (b) NSP 2021 (stan: marzec 2021) a BDL 2024 to różne daty. (c) Warto sprawdzić, ile mieszkańców gm. Kutno pracuje w macierzy NSP 2021 *poza* Kutnem (wyjeżdżający), co jest dostępne w już pobranym pliku `macierz_przeplywow_nsp2021.xlsx` i pozwoli zweryfikować 54/46% bez nowych danych.

## 4. Czym zastąpić wagę „powierzchnia budynku” (D7)

Rozdzielam dwie sprawy, bo źródła dają je osobno:

**A. Ile miejsc pracy (kotwica sumy).** Użyć BDL P4508: 17 486 (2024) jako wartość docelową liczby miejsc pracy w Kutnie, ze zmienną wersją 17 251 (2025) i 17 460 (2023) jako wariantami (wszystkie pod 1,5% różnicy, więc rok nie ma znaczenia). To zastępuje „brak kotwicy”.

**B. Gdzie w mieście (rozkład przestrzenny).** Danych poniżej gminy brak. Najlepsza dostępna kombinacja:
1. Zostawić OSM jako bazę przestrzenną (budynki + landuse z D7).
2. **Wagi z typu funkcji i powierzchni, a nie z samej powierzchni**: różna gęstość etatów na m² dla przemysłu/magazynu (niska), biur i handlu (wysoka), szkół i szpitala (obiekty publiczne). Gęstości muszą pochodzić ze źródła (np. norma planistyczna lub literatura) albo być jawnym ZAŁOŻENIEM z wariantami (CLAUDE.md zakazuje „typowych” liczb bez źródła).
3. **Kalibracja do struktury branżowej** z P4500 (powiat), jako jedyny twardy pomiar struktury, z zastrzeżeniem, że to powiat (rolnictwo A trzeba wyłączyć lub wyrzucić, bo jest poza miastem).
4. **Lista kotwic dużych zakładów** z lokalizacjami (REGON/OSM/ręczna kontrola): w KSE/Sklęczkach ok. 9 000 osób wg urzędu (nie weryfikowalne, a przekracza połowę wszystkich 17,5 tys. etatów, co jest sprzeczne z P4508: albo deklaracja jest zawyżona/dotyczy szerszego obszaru, albo siedziby firm leżą poza Kutnem, albo dotyczy innej daty). **Nie używać 9 000 jako kotwicy bez wyjaśnienia**; 2 200 w podstrefie ŁSSE jest spójne z P4508 (ok. 13% etatów).

Czego nie robić: odtwarzać pojedynczych pracodawców z ogłoszeń o pracę (nieweryfikowalne), ani wnioskować lokalizacji pracujących z punktów adresowych GUS (to budynki mieszkalne).

**Użyteczne uboczne odkrycie dla G3 (domy):** punkty adresowe ADR (4 807 w Kutnie, 241 par rejon/obwód) to niezależna lista *budynków mieszkalnych* wg urzędowego rejestru z przypisanym obwodem spisowym. Można porównać z liczbą budynków mieszkalnych z OSM w obwodach i użyć jako kontroli lub wag zamiast obrysów (każdy punkt = 1 budynek). Nie ma liczby kondygnacji ani mieszkań. Surowy zestaw jest w `adr_kutno_2026_0.csv`.

## 5. Ograniczenia i niepewności (do wiadomości, nie do ukrywania)

- **Efekt siedziby płatnika.** Firmy z siedzibą w Kutnie i oddziałami poza nim zawyżają P4508 Kutna, a oddziały firm z siedzibą poza Kutnem (część zakładów strefy) są liczone tam, gdzie siedziba. Brak sposobu pomiaru wielkości błędu. Zgodna konwencja z macierzą NSP (też adres pracodawcy) ogranicza niespójność w modelu, ale nie błąd wobec rzeczywistości.
- **Obecność w pracy (D6).** P4508 to *pracujący*, nie osoby obecne w danym dniu. Urlopy, choroby, praca zdalna i zmiany nocne wchodzą do D6/D14, nie do kotwicy.
- **Rolnicy KRUS** są w sumie, ale praca na gospodarstwie to nie dojazd. W gminie miejskiej Kutno to margines (sekcja A w powiecie ma 11,6%, w mieście znacznie mniej), ale nie jest rozdzielone.
- **Praca w Kutnie dla mieszkańców innych gmin poniżej progu 3 osób** nie ma w macierzy NSP, ale ma w P4508. To jedna z możliwych przyczyn, że 17,5 tys. etatów jest wyższe niż „mieszkańcy zostający + 8 186”.
- **Rok.** P4508 jest z 2023–2025, mieszkańcy z NSP 2021, macierz z NSP 2021.
- Wiersze z pliku ESRP i BIR (klasa wielkości) niepotwierdzone, bo serwer ESRP nie odpowiedział, a dokumentacja BIR1.1 (zip) nie była czytana.

## 6. Rekomendacja dla G2 i decyzje użytkownika

**Użyć:** (1) BDL P4508 jako kotwicę sumy miejsc pracy; (2) NSP macierz (już w projekcie) dla przyjezdnych; (3) OSM z wagami typ×powierzchnia dla lokalizacji; (4) P2613 + P4500 jako kontrola struktury wielkościowej i branżowej; (5) opcjonalnie REGON do weryfikacji kilkudziesięciu największych zakładów (≥ 50 osób wg P2613 to tylko ok. 58 podmiotów).

**Decyzje, które musi podjąć użytkownik (nie ja):**
1. **Czy łączna liczba miejsc pracy ma być 17 486 (BDL 2024), a nie 25 732?** To wymaga zmiany D3/D9: część mieszkańców (ok. 46% pracujących wg oszacowania rzędu wielkości) pracuje poza Kutnem, więc w modelu nie jedzie do Kutna (D3 „wyjeżdżający poza MVP”). Alternatywa: zostawić 25 732 jako „górne ograniczenie” i opisać jako wariant.
2. **Czy zgadzasz się na jedno z dwóch podejść do wyjeżdżających**: (a) usunąć ich z popytu w Kutnie (agent z domem w Kutnie i pracą poza gminą nie generuje ruchu wewnątrz sieci, albo generuje tylko wyjazd do granicy jak D16 w drugą stronę); (b) zostawić jak dziś. Dane do (a) są już w macierzy NSP.
3. **Źródło gęstości etatów na m² dla typów obiektów** (przemysł, magazyn, handel, biuro, publiczne): wskazać źródło albo zaakceptować jawne ZAŁOŻENIE z trzema wariantami.
4. **Czy występować o klucz REGON** (e-mail do regon_bir@stat.gov.pl, nie wysyłałem) i czy warto, skoro klasa zatrudnienia jest niepotwierdzona. Moja rekomendacja: najpierw przeczytać dokumentację BIR1.1 (zip ze strony API), zanim cokolwiek się wysyła.
5. **Czy wnioskować o mikrodane GUS** (Operacyjna Baza Mikrodanych) z P4508 po gminie, PKD i wielkości płatnika. Daje to jedyny prawdziwy rozkład branżowo-wielkościowy dla Kutna, ale to procedura formalna poza zakresem MVP.

## 7. Wiersze do manifestu (`data/manifest.csv`)

Nie edytuję manifestu (własność innej sesji). Wiersze gotowe do wklejenia; `downloaded_utc` = czas pobrania/utworzenia 2026-10-17. Dla plików wygenerowanych z API/wycinka URL wskazuje zapytanie lub plik wyjściowy.

```csv
path,url,downloaded_utc,bytes,sha256
data/raw/g2/bdl_kutno.json,https://bdl.stat.gov.pl/api/v1/data/by-unit/051011902011?var-id=1735396&var-id=1735397&var-id=1735398&var-id=1735394&var-id=1735395&year=2023&year=2024&year=2025 (5 zapytań; skrypt pipeline/g2_bdl_kutno.py),2026-10-17T11:35Z,980,c02a1d132e008b95720aa07b870bef9588b9537a065e87d378a885d9b347c8b0
data/raw/g2/bdl_podmioty_pkd.json,https://bdl.stat.gov.pl/api/v1/data/by-unit/{051011902011|051011902000} (P2613 zm. 74097-74107; P4500/P4502; skrypt pipeline/g2_bdl_podmioty.py),2026-10-17T11:36Z,5506,6ac2a2a5d316e56a8a68d1ae64ca4f492ae66cb291518e79f19646c8f664928c
data/raw/g2/ADR_NOBC_2026_0_GJ.zip,https://geo.stat.gov.pl/atom-web/download/?fileId=d1b044cae07f65d38654c0852cd3ed16&name=ADR_NOBC_2026_0_GJ.zip,2026-10-17T11:37Z,287088108,0d6cc74a0384d776353fcd0b37d4fa745fd2b323d7f7c4ecb0a2fa101a6e4591
data/raw/g2/adr_kutno_2026_0.csv,wycinek z ADR_NOBC_2026_0_GJ.zip (TERYT=1002011; skrypt pipeline/g2_adr_kutno.py),2026-10-17T11:40Z,399609,6f1ff36cc822c513213c544c6064a794e0508e7a783e08aa615a46d52eaf28b1
data/raw/g2/gus_zeszyt_pracujacy_adm.pdf,https://stat.gov.pl/files/gfx/portalinformacyjny/pl/defaultaktualnosci/5818/9/1/1/zeszyt_metodologiczny_pracujacy_w_gospodarce_narodowej_wedlug_zrodel_administracyjnych_.pdf,2026-10-17T11:38Z,648076,4d4c0361e96f3983838af0b57fa17faf43fcf0af70330310225a5c3b7a086809
data/raw/g2/gus_raport_pracujacy_powiaty.pdf,https://stat.gov.pl/files/gfx/portalinformacyjny/pl/defaultaktualnosci/6329/5/1/1/raport_opracowanie_metodologii_i_oszacowanie_liczby_pracujacych_w_gospodarce_narodowej.pdf,2026-10-17T11:38Z,7678826,0a6786781900fccbd8ef1cfbd55b140641a50ab2c0cc55f187c4b76590bf7989
data/raw/g2/um_kutno_node52.pdf,https://um.kutno.pl/print/pdf/node/52,2026-10-17T11:37Z,995508,54a951859213b9cf932f78b67def5f8fcf25b74dc334b2186b4e2a3c67729f77
data/raw/g2/um_kutno_node176.pdf,https://um.kutno.pl/print/pdf/node/176,2026-10-17T11:37Z,905952,02c7468f6038f4168fd7a230e4a4c475ee7e23a6676f5cf85024407a0e74d3f8
```

Pliki `*.txt` w `data/raw/g2/` to ekstrakty tekstu z powyższych PDF (pochodne, bez wpisu).

## 8. Jak odtworzyć

```
uv run python pipeline/g2_bdl_kutno.py     # P4508, P4507
uv run python pipeline/g2_bdl_podmioty.py  # P2613, P4500, P4502
uv run python -I pipeline/g2_adr_kutno.py  # wycinek ADR (po pobraniu zip)
```
`pipeline/g2_bdl.py` to pomocnik do przeglądania katalogu BDL (`units`, `subj`, `vars`, `data`).

## 9. Poprawka do `docs/ZRODLA.md` (do wprowadzenia przez właściciela pliku)

- Wiersz „BDL GUS, pracujący wg gmin”: status → POBRANE; **P4508 jest wg siedziby pracy (płatnika), nie zamieszkania, z rejestrów ZUS/KRUS, a więc zawiera małe podmioty** (hipoteza „zwykle bez ≤ 9” dotyczy starszych tablic z badania 1-7 i nie dotyczy P4508 od grudnia 2022).
- Wiersz ADR: status → POBRANE; atrybuty bez informacji o podmiotach.
- Wiersz REGON: nadal DO SPRAWDZENIA; dokumentacja potwierdza zapytania po REGON/NIP/KRS, klucz przez e-mail, brak podanych limitów.
