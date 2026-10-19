# G3: dane do poprawy rozmieszczenia domów

Data: 2026-10-17. Badanie bez zmian w modelu (plans.py i configi nietknięte). Skrypt: `pipeline/g3_domy.py` (`uv run python -W ignore pipeline/g3_domy.py`), wyniki w `reports/etap2/g3_domy/` (`g3_wyniki.json` ma wszystkie liczby, `*.csv`, mapy `*.png`, log `run.log`).

## 1. Tabela źródeł

| Źródło | URL | Granulacja / rok | Atrybuty | Ograniczenia | Status |
|---|---|---|---|---|---|
| BDOT10k, paczka powiatowa 1002, GPKG (warstwa `OT_BUBD_A`) | https://opendata.geoportal.gov.pl/bdot10k/schemat2021/GPKG/10/1002_GPKG.zip | budynek (poligon), wersja danych 2025-12-09 | `FUNKCJAOGOLNABUDYNKU` (10 klas), `PRZEWAZAJACAFUNKCJABUDYNKU` (jedno-/wielorodzinny itd.), `LICZBAKONDYGNACJI` (wypełnione 99,9%), `KATEGORIAISTNIENIA`, `ZRODLODANYCHGEOMETRYCZNYCH` | Klasy nadrzędne grube: „mieszkalne” obejmuje też domy parafialne, opieki, klasztory (łącznie ~120 z 19 644). Brak liczby mieszkań i osób. 39% geometrii z ortofotomapy, nie z EGiB. | pobrane, 25,9 MB |
| GUS NSP 2021, ludność w siatce 250 m (ATOM GRID, SHP) | https://geo.stat.gov.pl/atom-web/atom/GRID (zbiór `NSP2021_250m`) | 250 m, cała Polska, EPSG:3035, NSP 2021 | tylko `TOT` (ogółem ludność) | Bez płci/wieku. Zbiór krajowy 172 MB (rozpakowany 3,3 GB, 5 mln komórek). Komórki z małą liczbą: GUS zastosował ochronę (w bbox powiatu 2 794 komórek ma 1–4 os.). Suma w bbox powiatu 134 848 (to bbox, nie granica). | pobrane |
| GUS NSP 2021, ludność w siatce 500 m (SHP) | ten sam ATOM, `NSP2021_500m` | 500 m, EPSG:3035 | `TOT` | j.w. | pobrane (zip), nieużyte w analizie |
| GUS NSP 2021, rezydenci w siatce 1 km (INSPIRE ATOM PD, SHP) | https://geo.stat.gov.pl/atom-web/atom/PD (`PD.GRID.2021`) | 1 km, EPSG:2180 | `RES`, `RES_MALE`, `RES_FEM`, `RES_0_14`, `RES_15_64`, `RES_65_` | Jedyna siatka z wiekiem/płcią. Wszystkie 315 857 komórek PL. | pobrane, 23,5 MB |
| GUS NSP 2021, ludność w siatce 125 m (XLS) | ATOM GRID, `GRID_2021_125m_xls` (47 MB) | 125 m | ludność ogółem | Według Portalu Geostatystycznego tylko miasta wojewódzkie (Kutna nie ma). | nie pobrane, bezużyteczne dla Kutna |
| GUS geometria siatek 125/250/500/1000 m (`GRID_GEO`) | ATOM GRID | geometria | — | 1,9 GB, niepotrzebne (250 m ma geometrię). | nie pobrane |
| GUS NSP 2021, budynki i mieszkania w siatce 1 km | Menedżer Zasobów Portalu Geostatystycznego, zasób nr 18483 (wg wiadomości portalu); brak w ATOM | 1 km | liczba budynków z mieszkaniami, mieszkań | Wymaga logowania do Menedżera Zasobów (eksport geojson/shp/csv). Nie sprawdzone, czy istnieje w 250 m: nic na to nie wskazuje. | **nie pobrane** (wymaga konta, nie tworzę kont) |

Wniosek do pkt 2: wartości są dla **250 m (tylko ogółem), 500 m (tylko ogółem) i 1 km (ze strukturą wieku)**. 125 m tylko dla miast wojewódzkich. Budynki/mieszkania tylko 1 km i przez konto.

## 2. BDOT10k vs OSM (pkt 1)

Powiat 1002 ma 47 314 budynków w BDOT10k, w tym 45 859 „eksploatowany” (używane dalej; reszta: zniszczony 761, nieczynny 524, w budowie 170).

| | gm. Kutno | powiat 1002 |
|---|---|---|
| BDOT10k budynki (eksploat.) | 9 343 | 45 859 |
| BDOT10k mieszkalne (liczba) | 5 252 | 19 644 |
| BDOT10k mieszkalne, obrys [km²] | 0,796 | 2,515 |
| BDOT10k mieszkalne, obrys × kondygnacje [km²] | 1,936 | 4,356 |
| OSM budynki | 10 159 | 48 220 |
| OSM obecny model (liczba / km²) | 7 447 / 0,914 | 22 415 / 2,719 |
| OSM wg listy R5 (po tagu): liczba / km² | 8 625 / 1,427 | 29 788 / 4,358 |
| OSM R5 bez pracy/amenity/shop/office: liczba / km² | 8 147 / 1,099 | 29 251 / 4,013 |

BDOT10k mieszkalne w powiecie: 18 425 jednorodzinnych, 1 095 wielorodzinnych (reszta: domy letniskowe, opieki, parafialne itd.). Kondygnacje mieszkalnych: 1 piętro 12 805, 2 – 5 754, 3 – 706, 4 – 86, 5 – 274, 6–8 – 19. Pokrycie OSM i BDOT liczbowo podobne (OSM 10 159 vs BDOT 9 343 w gm. Kutno). OSM ma budynki bez odpowiednika w BDOT (1 450 z 10 159 w gm. Kutno nie trafia punktem reprezentatywnym w żaden budynek BDOT; głównie `yes` 886 i `retail` 235).

**Zgodność funkcji** (gm. Kutno, budynki OSM z odpowiednikiem w BDOT, 8 709): osm_mieszk = „dom” w naszym modelu, bdot_mieszk = „budynki mieszkalne” w BDOT.

| wariant OSM | trafne | OSM mieszk, BDOT nie | OSM nie, BDOT mieszk | precision | recall | powierzchnia fałszywych dodatnich |
|---|---|---|---|---|---|---|
| obecny | 5 015 | 1 719 | 212 | 0,745 | 0,959 | 181 tys. m² (20% obecnej puli) |
| R5 (tylko lista wykluczeń) | 5 184 | 2 530 | 43 | 0,672 | 0,992 | 601 tys. m² |
| R5 bez pracy/amenity | 5 175 | 2 133 | 52 | 0,708 | 0,990 | 296 tys. m² |

Fałszywe dodatnie obecnego modelu to głównie `building=yes` w landuse=residential, które BDOT nazywa niemieszkalnym (garaże, budynki gospodarcze, usługowe). Dodatek R5 w gm. Kutno ma 160 budynków mieszkalnych wg BDOT (39 tys. m²) i 146 tys. m² niemieszkalnych lub bez odpowiednika (m.in. pozostałe niemieszkalne 86, rolnicze 99, magazynowe 48, biurowe 45, handlowe 37, przemysł 31, oświata/sport 28, szpitale 7). Czyli **lista wykluczeń R5 w Kutnie dodaje głównie obiekty niemieszkalne (79% dodanej powierzchni)**. Uwaga: lista R5 jest ratunkiem na brak tagów mieszkalnych w dużych miastach; w Kutnie 22 137 budynków to `yes`.

Kondygnacje BDOT to najsilniejsza korekta: OSM `apartments` w gm. Kutno ma 21% powierzchni obrysów obecnej puli, ale 43% po przemnożeniu przez kondygnacje. 90% budynków obecnej puli ma kondygnacje w BDOT; średnia kondygnacji ważona obrysem 2,2. W OSM `yes` mieszkalne wg BDOT: 1 piętro 1 593, 2 – 2 103, 3 – 226.

## 3. Wpływ przejścia na wykluczenia R5 (pkt 3)

Porównanie: obecna pula vs R5 bez pracy/amenity (wariant „r5p”; czysty R5 jest jeszcze szerszy, liczby w `g3_wyniki.json`).

- Gm. Kutno: powierzchnia puli 0,914 → 1,099 km² (+20%, +185 tys. m²), budynków 7 447 → 8 147.
- Obwody (233, wszystkie z geometrii BREC): zmiana powierzchni >20% w 34 obwodach, >50% w 22. Największy przyrost m²: 6511303 (+31 tys. m², +1109%), 6509026 (+18 tys.), 6511403 (+15 tys.), 6511001, 6511306, 6509025 (por. `mapa_wplyw_r5_obwody.png`). Ważony pracującymi udział „nowej” powierzchni w puli: 6,7% (czyli około 7% agentów-rezydentów miałoby szansę trafić do dodanych budynków).
- Obwody bez budynku mieszkalnego: **1 w obecnym i 1 w R5** (6509902, 57,84 pracujących, dostają losowy punkt). R5 tego nie naprawia, bo w obwodzie nie ma żadnego budynku kandydata. Czyli „ile obwodów przestaje potrzebować losowego punktu” = **0**.
- Gminy powiatu (przyrost puli m² / udział nowej powierzchni w puli): 1002045: +246% (71% puli), 1002092: +155% (61%), 1002082: +111% (53%), 1002102: +101% (50%), 1002044: +72%, 1002114: +54%, 1002022: +47%; pozostałe +12–21%. Pełna tabela `reports/etap2/g3_domy/wplyw_r5_per_gmina.csv`. Przyrost w powiecie to w 99% `building=yes` poza landuse=residential (6 772 budynków, 1,28 km²), reszta to remizy, bazyliki, plebanie.
- Wariant z kondygnacjami BDOT: zmienia rozkład budynków w obwodzie średnio o 12,1 punktu procentowego masy (całkowita wariacja, ważona pracującymi), współczynnik obrys→obrys×kond. 1,0–6,5 w obwodach (`g3_wyniki.json`, sekcja `kondygnacje`).

## 4. Domy agentów vs siatka GUS (pkt 4)

Agenci = 5 900 w próbce 25% (4 390 rezydentów z domem w Kutnie, 1 510 dojeżdżających z powiatu, 14 `random_point`). Mapy: `mapa_agenci_vs_gus_250m.png`, `scatter_powierzchnia_vs_gus_250m.png`, `mapa_wariantow_vs_gus_250m.png`; gpkg z komórkami `siatka250_kutno_porownanie.gpkg`. Siatka 250 m: 285 niepustych komórek w gm. Kutno, suma 42 052 (NSP 42 255 wg centroidów; GUS ma też komórki na granicy).

**Rzeczywiste domy agentów** (korelacja z ludnością komórki): 250 m r Pearson 0,972, Spearman 0,885; 1 km 0,998 / 0,975 (32 komórki). To przede wszystkim efekt tego, że liczba agentów w obwodzie jest wprost z NSP (pracujący ~ ludność obwodu), a nie dowód jakości wyboru budynków. Dlatego rozstrzyga porównanie **oczekiwanego** rozkładu rezydentów (liczba pracujących obwodu × udział wagi budynku w obwodzie, bez losowania) dla wariantów wag, 250 m, gm. Kutno:

| wariant wag | Pearson | Spearman | TV vs GUS [pp] (masa w złej komórce) |
|---|---|---|---|
| OSM obecny (obrys) | 0,977 | 0,918 | 10,3 |
| OSM jak R5 (bez pracy/amenity) | 0,973 | 0,901 | 11,6 |
| BDOT mieszkalne, obrys | 0,979 | 0,935 | 9,4 |
| **BDOT mieszkalne, obrys × kondygnacje** | **0,982** | **0,939** | **8,5** |
| BDOT mieszkalne, liczba budynków | 0,967 | 0,918 | 11,7 |

Surowa powierzchnia w komórce vs GUS (bez normalizacji do obwodów) rozróżnia mocniej: Pearson 250 m: OSM obecny 0,68, OSM R5 0,66, BDOT obrys 0,74, **BDOT × kondygnacje 0,93** (powiat 8 452 komórek: 0,69 / 0,63 / 0,75 / 0,92; 1 km gm. Kutno 0,89 / 0,88 / 0,88 / 0,98). Mapa różnic: agenci nadmiarowi (czerwony) w komórkach z małymi domami i niedomiar (niebieski) w sąsiednich blokowiskach, czyli brak kondygnacji spłaszcza centrum i osiedla bloków.

**Wniosek:** przejście na wykluczenia R5 **pogarsza** zgodność z GUS (TV 10,3 → 11,6 pp). Wagi z BDOT10k poprawiają (9,4 → 8,5 pp z kondygnacjami), ale zysk w obrębie obwodu jest umiarkowany, bo obwody spisowe (~180 pracujących) są już małe. Spearman dla całego powiatu (0,30–0,35) jest niski z powodu tysięcy komórek z kilkoma osobami (ochrona 1–4) i nie rozróżnia wariantów.

## Ograniczenia analizy

- Dopasowanie OSM–BDOT po punkcie reprezentatywnym; 14% budynków OSM w gm. Kutno bez odpowiednika. Wyniki per funkcja dotyczą dopasowanych.
- Dla powiatu (spoza gm. Kutno) nie mamy obwodów w użyciu: dojeżdżający z gmin powiatu są losowani w całej gminie (`gmina_geom`), więc tam wariant liczy się per gmina, a nie per obwód. Testowałem obwody tylko dla Kutna.
- Siatka GUS to ludność całkowita (nie pracujący). Pracujący mogą rozkładać się inaczej – nie mamy tego z siatki 250 m; siatka 1 km ma wiek (`RES_15_64`), nie użyta.
- Kondygnacje to proxy ludności; brak liczby mieszkań (zasób 18483 wymaga konta).
- 14 agentów (`random_point`) i obwód 6509902: pozostają niezależnie od wariantu.

## Wiersze do manifestu

Format `path,url,downloaded_utc,bytes,sha256` (pobrano 2026-10-17T11:34–11:35Z, godziny w UTC wg `date -u` z pobrania; manifestu nie edytowałem):

```
data/raw/g3/bdot10k/1002_GPKG.zip,https://opendata.geoportal.gov.pl/bdot10k/schemat2021/GPKG/10/1002_GPKG.zip,2026-10-17T11:34Z,25854403,0b948b601a8b497e815f100429f047b3aa4d17487eb0d324e88c4050c250766f
data/raw/g3/gus_grid/GRID_NSP2021_RES.zip,https://geo.stat.gov.pl/atom-web/download/?fileId=2795b7ed9098f86ab761352519ba1d85&name=GRID_NSP2021_RES.zip,2026-10-17T11:34Z,23527606,815deb0fb369df11de0ff150dd14ce87fd875acf3d542da8d2db1dafc0791680
data/raw/g3/gus_grid/NSP2021_TOT_grid250m_SHP.zip,https://geo.stat.gov.pl/atom-web/download/?fileId=7c7f83553d00ab22740e62fe5d323d70&name=NSP2021_TOT_grid250m_SHP.zip,2026-10-17T11:35Z,171905741,3b66b1188eac528723266fc3f56862905d6f9c0af93429443fb2f875bf1ead4c
data/raw/g3/gus_grid/NSP2021_TOT_grid500m_SHP.zip,https://geo.stat.gov.pl/atom-web/download/?fileId=f3d55d7726903dee59a1a7a5957a07f0&name=NSP2021_TOT_grid500m_SHP.zip,2026-10-17T11:35Z,38733220,4fec1b1eb6cf09f596a77ce3d120a8128d2e07a5c1521a190ee0fc4b146080df
```

Rozpakowane kopie leżą w `data/raw/g3/*/x`, `g250` (3,3 GB, można usunąć i rozpakować z zipa ponownie). Katalogi ATOM (`pd.xml`, `su.xml`, `grid.xml`) to tylko spisy plików, bez wartości.

## Rekomendacja dla G3

Rekomendowany wariant: **wagi budynków z BDOT10k: tylko „budynki mieszkalne”, waga = obrys × liczba kondygnacji** (zamiast listy OSM albo wykluczeń R5). Najlepsze dopasowanie do GUS 250 m (TV 8,5 pp, surowa powierzchnia r 0,93 vs 0,68 obecnie), działa w całym powiecie (kondygnacje wypełnione w 99,9%), jedno źródło urzędowe zamiast heurystyki landuse. Lista wykluczeń R5 odradzana w Kutnie: gorsza niż obecny model.

Decyzje dla użytkownika (zmiana wymaga wpisu w DECISIONS.md, D11 i zakres zamrożony):
1. **Czy odejść od zasady „waga = obrys” (świadoma decyzja 2026-09-10 w R5) na „obrys × kondygnacje”** w BDOT10k? Bez kondygnacji (sam BDOT, obrys): TV 9,4 pp, zysk mały; z kondygnacjami 8,5 pp i znacznie lepsza powierzchnia surowa.
2. **Które klasy BDOT uznać za dom:** tylko „budynki mieszkalne” (19 644 w powiecie) z wyłączeniem domów parafialnych, opieki, klasztorów, koszar (~120), czy wszystkie?
3. **OSM czy BDOT jako źródło geometrii domu** (BDOT 2025-12, 39% z ortofotomapy; OSM aktualniejszy w nowych osiedlach: 1 450 budynków OSM w gm. Kutno bez odpowiednika). Możliwy wariant hybrydowy: BDOT dla funkcji i kondygnacji, OSM jako uzupełnienie nowych budynków (do ustalenia osobno).
4. **Obwód 6509902** (57,8 pracujących, zero budynków mieszkalnych): zostawić losowy punkt czy przypisać do sąsiedniego obwodu?
5. Czy pobrać siatkę 1 km „budynki i mieszkania” przez konto w Menedżerze Zasobów (zasób 18483), żeby sprawdzić liczbę mieszkań na komórkę (kontrola kondygnacji)? Wymaga konta, więc po stronie użytkownika.

## Uzupełnienie (L-5): co zmieniłoby się w modelu, koszty, obwód 6509902

**Zmiana w kodzie (nie wykonana, do decyzji w DECISIONS.md):** w `pipeline/plans.py` warstwa kandydatów `homes_b` (dziś OSM: tagi mieszkalne + `yes` w landuse=residential) byłaby zastąpiona budynkami BDOT10k `OT_BUBD_A` z `KATEGORIAISTNIENIA=eksploatowany` i `FUNKCJAOGOLNABUDYNKU="budynki mieszkalne"`, a `pick_buildings` używałoby wagi `area_m2 × LICZBAKONDYGNACJI` (braki = 1). Reszta (przypięcie do linku, losowanie ze zwracaniem, seed) bez zmian. Efekt: w gm. Kutno ok. 7 450 → 5 250 budynków; zniknęłyby garaże i budynki gospodarcze z puli (181 tys. m², 20% obecnej puli), a udział bloków wzrósłby (OSM `apartments` 21% → 43% wagi). Zmiana zmieni `plans.xml` (nowy sha256, nowy wynik referencyjny) i przesunie część agentów z peryferii do centrum i osiedli, więc wymaga ponownych runów 25%.

**Koszty:**
- nowe źródło w repo (BDOT10k 26 MB, wpisy `docs/ZRODLA.md` i `data/manifest.csv`) i warstwa czytana w `plans.py` (pliki `data/raw/g3/...`);
- osobna logika dla powiatu: dojeżdżający z gmin powiatu też muszą brać budynki BDOT (kondygnacje są w całym powiecie, więc bez dodatkowych danych);
- BDOT ma 39% geometrii z ortofotomapy, a 1 450 budynków OSM w gm. Kutno nie ma w nim odpowiednika (nowe osiedla, aktualność OSM wyższa). To ryzyko niedoszacowania nowych dzielnic; łagodzi je wariant hybrydowy (BDOT dla funkcji i pięter, OSM `house/detached/apartments` jako uzupełnienie), droższy w utrzymaniu;
- zysk jest umiarkowany: oczekiwana masa w złej komórce 250 m spada z 10,3 do 8,5 pp. Wykluczenia R5 bez BDOT pogorszyłyby wynik (11,6 pp), więc ich nie warto.

**Obwód 6509902 nie jest realną luką danych.** To obwód 153 mieszkańców (57,84 pracujących) o powierzchni 0,25 ha, czyli jeden 5-kondygnacyjny blok wielorodzinny (BDOT: 1 014 m², OSM `apartments` 994 m²). Blok leży na granicy obwodu, a `plans.py` przypisuje budynek do obwodu po `representative_point().within(obwód)`; ten punkt wypada w sąsiednim obwodzie, więc kandydatów jest 0 i agenci dostają `random_point` w poligonie 0,25 ha (niedaleko bloku, błąd rzędu kilkudziesięciu metrów). To artefakt przypisania, nie brak budynku. Poprawka tania i niezależna od wariantu: przypisywać budynek do obwodu po największym pokryciu (albo przecięciu), a przy braku kandydatów brać najbliższy budynek mieszkalny. Różnica dla wyników praktycznie żadna (57,84 pracujących, 14 agentów w próbce 25%).

**Rekomendacja:** przyjąć BDOT10k (tylko „budynki mieszkalne”, obrys × kondygnacje) jako wagi domów w gm. Kutno i powiecie, bo jest najlepiej zgodny z GUS i jedyny uwzględnia bloki; hybrydę z OSM zostawić jako wariant, jeśli użytkownik uzna aktualność nowych osiedli za ważniejszą. Obwód 6509902 naprawić przypisaniem po przecięciu, bez osobnej decyzji. Przed wdrożeniem warto zrobić run 25% porównawczy (zgodnie z regułą skali) i zapisać decyzję w DECISIONS.md.
