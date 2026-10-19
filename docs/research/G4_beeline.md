# G4 — współczynnik objazdu (`beelineDistanceFactor`) dla Kutna: eksperyment empiryczny

Stan: 2026-10-17. Pomiar na sieci OSM Kutna w QGIS 3.40.5 (algorytmy natywne), EPSG:2180. **Model MATSim nie został zmieniony.**
Skrypty: `docs/research/G4_beeline/` (`prep_networks.py`, `analyze_od.py`, `analyze_iso.py`, `fit_factor.py`). Dane pośrednie: `output/g4_beeline/` (gitignored). Wykres: `reports/etap2/g4_beeline/f_vs_dist.png`. Dziennik obserwacji: `docs/research/G4_beeline_obserwacje.md`.

## 1. Wynik w skrócie

| Tryb | f średnie na parę | f = Σtrasa/Σlinia | f (OLS: trasa = a·linia + b) | f minimalizujący błąd bezwzględny | Domyślne MATSim 1,3 |
|---|---|---|---|---|---|
| pieszo | 1,28 | **1,24–1,26** | a = 1,11, b = 545 m | 1,22 | błąd bezwzględny 425 m |
| rower | 1,38 | **1,34–1,35** | a = 1,17, b = 711 m | 1,30 | 503 m |
| auto | 1,42 | **1,36–1,38** | a = 1,19, b = 746 m | 1,32 | 536 m |

(Ważone rozkładem odległości wszystkich 17 546 par dom–praca w gm. Kutno; n ≈ 10,3 tys. par na tryb.)

1. **Hipoteza 1,6 nie potwierdza się jako współczynnik objazdu dla Kutna.** Dla większości par (2–7 km) f mieści się w 1,2–1,45. Wartości ≥ 1,6 pojawiają się tylko dla podróży krótszych niż ~2 km.
2. **Domyślne 1,3 jest blisko prawdy dla roweru** (1,30–1,35), nieco za wysokie dla pieszych (1,22–1,26).
3. **f silnie zależy od odległości**: krótkie trasy są bardziej „okrężne” (patrz sekcja 3). Jeden mnożnik zawsze będzie błędny na jednym z końców rozkładu. Wyraźniej: trasa ≈ a·linia + b, gdzie b ≈ 0,5–0,75 km to w dużej mierze dojścia do sieci i obejścia lokalne. MATSim nie ma stałej addytywnej w trasie teleportowanej (sama formuła to `dist × factor / speed`).

## 2. Skąd się wzięło „1,6” — pole izochrony a współczynnik

Intuicja: „stosunek pola koła (odległość w linii prostej = d) do pola izochrony (odległość po sieci = d)” daje liczbę ~1,6. Matematycznie to jest **stosunek pól, czyli f²**, nie f:
- Dla idealnej siatki ulic zasięg po sieci to romb (norma L1), a stosunek pól koła do rombu to π/2 ≈ **1,57**. Stąd „1,6”. Ale odpowiada to średniemu współczynnikowi objazdu ok. **1,25–1,27** (4/π dla losowego kierunku w siatce), nie 1,6. Literatura: dla siatki idealnej obszar dojścia stanowi 63,7% = 2/π pola koła (Planitmetro, link niżej).
- Eksperyment (30 losowych adresów mieszkańców, `native:serviceareafromlayer`, odległości 500/1000/2000/3000 m; obwiednia = otoczka wypukła i wklęsła wierzchołków osiągalnej sieci):

| tryb | d [m] | A_koło / A_izochrony (wypukła) | A_koło / A_izochrony (wklęsła 0,25) | f = √(A_koło/A) wypukła | f wklęsła |
|---|---|---|---|---|---|
| pieszo | 3000 | 1,54 | 1,88 | 1,24 | 1,39 |
| pieszo | 1000 | 1,89 | 2,42 | 1,40 | 1,64 |
| pieszo | 500 | 2,13 | 2,98 | 1,50 | 1,81 |
| rower | 3000 | 1,68 | 2,04 | 1,31 | 1,46 |
| rower | 1000 | 2,01 | 2,64 | 1,45 | 1,72 |
| auto | 3000 | 1,88 | 2,35 | 1,39 | 1,57 |
| auto | 1000 | 2,37 | 3,29 | 1,62 | 2,01 |

Wnioski: stosunek pól 1,5–2,6 (wypukła), czyli „liczba około 1,6” rzeczywiście się pojawia dla pieszych ok. 3 km, ale **jako stosunek pól**. Po pierwiastku daje f 1,24–1,8, **zgodnie z f z par dom–praca przy tych samych odległościach** (np. pieszo 3–4 km: 1,28; rower: 1,41; auto: 1,43). Wynik zależy od sposobu wyznaczenia obwiedni (wypukła vs wklęsła różnią się o ok. 0,1–0,3 w f), więc jako estymator f metoda izochron jest **mniej odporna** niż bezpośredni pomiar po parach.

## 3. Zależność od odległości (pary dom–praca z `plans_100pct.xml.gz`)

f = Σ(trasa po sieci + dojścia do sieci) / Σ(odległość euklidesowa):

| linia prosta [m] | pieszo | rower | auto | liczba par (pieszo) |
|---|---|---|---|---|
| 0–1000 | 1,70 | 1,87 | 2,03 | 396 |
| 1000–2000 | 1,44 | 1,53 | 1,59 | 1021 |
| 2000–3000 | 1,31 | 1,41 | 1,45 | 1112 |
| 3000–4000 | 1,28 | 1,41 | 1,43 | 1790 |
| 4000–5000 | 1,25 | 1,35 | 1,37 | 2390 |
| 5000–7000 | 1,21 | 1,29 | 1,32 | 3165 |
| 7000–12 000 | 1,16 | 1,20 | 1,23 | 474 |

Zgodnie z literaturą: krótkie podróże są bardziej okrężne, a stały współczynnik 1,25–1,41 to od lat uproszczenie (źródła w sekcji 6).

## 4. Metoda i założenia (wszystkie do zmiany w razie potrzeby)

- **Sieci** z `data/raw/osm/lodzkie-261015.osm.pbf`, przycięte do gm. Kutno + 3 km, cięte w węzłach współdzielonych (topologia OSM): pieszo 876 km, rower 697 km, auto 565 km (`prep.log`).
  - *pieszo*: wszystkie drogi z wyjątkiem motorway/trunk, plus `footway`, `path`, `pedestrian`, `steps`, `track`, `cycleway`; wykluczone `foot=no`, `access=no/private`. Jednokierunkowość ignorowana.
  - *rower*: drogi oprócz motorway/trunk, `cycleway`, `track`, `path` bez zakazu; `footway`/`pedestrian` tylko z `bicycle=yes/designated/permissive`; wykluczone `bicycle=no/dismount`. **ZAŁOŻENIE: jednokierunkowość ignorowana** (kontrapas zwykle dozwolony, ale to nie jest zweryfikowane dla Kutna).
  - *auto*: drogi samochodowe z `oneway` (kierunki w polu `dir`), bez `access=no/private`. To odtworzenie z OSM, **nie** sieć `network.xml.gz` MATSim (prędkości nie grają roli, bo kryterium to dystans).
- **Pary**: mieszkańcy z `plans_100pct.xml.gz`, oba końce w granicach gm. Kutno (17 546 z 25 685 agentów). **To są pary wygenerowane przez nasz model popytu (D17), nie obserwacje**; ich rozkład odległości (mediana 3,7 km, max 10,6 km) zależy od modelu pracy.
- **Próbka**: 110 celów (losowanie ważone liczbą pracowników, seed 42) → 10 394 par. Rozkład odległości próbki różni się od pełnego (KS = 0,146, p ≈ 0): próbka jest o ok. 0,5 km dłuższa. Dlatego liczby w tabelach 1 i fit są **przeważone binami odległości** do pełnego rozkładu.
- **Trasa**: `native:shortestpathlayertopoint` (strategia „najkrótsza”), pomijając punkty bez trasy (pieszo 46, rower 121, auto 114 z 10 394).
- **Dojścia**: punkty (budynki/zakłady) leżą od sieci średnio 21 m (dom) i 90 m (praca, duże zakłady), bo ścieżka zaczyna się na najbliższym punkcie sieci. Dodałem do trasy proste dojścia dom→sieć i sieć→praca. Bez nich f jest niższe o ~0,02–0,04.
- **Izochrony**: 30 losowych domów (seed 7), `native:serviceareafromlayer` z kosztem w metrach; obwiednie jak w sekcji 2. Kolumna `mean_end_euclid`/`f_meanend` w `isochrones.csv` jest **błędna** (liczy dystans do początku linii) i nie jest używana.

## 5. Ograniczenia (czego ten pomiar nie rozstrzyga)

1. Pary dom–praca są syntetyczne; faktyczne dojazdy w Kutnie mogą mieć inny rozkład odległości (potrzebna walidacja na danych obserwowanych, jeśli się pojawią).
2. Rower: ignoruję jednokierunkowość, chodniki traktuję jako niedostępne (poza `bicycle=yes`), nawierzchnię i wzniesienia pomijam. Praktycznie rowerzysta w Polsce często jedzie chodnikiem, co obniżyłoby f w stronę wartości „pieszo”. Wrażliwość nie była testowana.
3. Pomiar dotyczy tras dom–praca, nie wszystkich celów (zakupy, szkoła) — te w MVP nie istnieją.
4. Auto: odtworzenie sieci z OSM, bez zawrotek granicznych i bez czyszczenia (NetworkCleaner) z F2. Może zawyżać f względem sieci MATSim.
5. Nie testowano żadnego configu MATSim z tymi wartościami.

## 6. Literatura i źródła, do których zajrzałem

- MATSim Wiki, *Mixed car/motorcycle/bicycle simulation*: teleportacja a sieciowe tryby (https://matsim.atlassian.net/wiki/spaces/MATPUB/pages/84246572).
- Lista wątków MATSim (SourceForge) z wzorem `beelineDistanceFactor` / `teleportedModeSpeed`: https://sourceforge.net/p/matsim/mailman/message/32795125/ (tylko wzór, bez wartości dla Polski).
- Boeing G., *The Relative Circuity of Walkable and Drivable Urban Street Networks* (40 miast USA, OSM): sieć piesza jest zwykle bardziej bezpośrednia niż drogowa, zgodnie z naszym wynikiem, że f_pieszo < f_auto. https://geoffboeing.com/?p=2796 (wartości liczbowe nie zostały odczytane).
- Lisbon, ISPRS IJGI 2021, 10(7):453 — porównanie circuity dla sieci drogowej, rowerowej i pieszej (https://www.mdpi.com/2220-9964/10/7/453); pełna treść nieczytana.
- Transportation Research Part C — modele zakładają od ok. 50 lat stały współczynnik 1,25–1,41, ale średni wskaźnik objazdu maleje z odległością (wg streszczenia wyszukiwarki); artykuł nieczytany.
- Pole dojścia w siatce idealnej = 63,7% koła (2/π): https://planitmetro.com/?p=9257 (blog; odczyt z wyników wyszukiwania).
- Równanie `teleportedModeParameters` i domyślne 1,3: sekcja 4d w `docs/research/G4_tryby.md` (WebFetch z kodu 2026.0).

## 7. MATSim User Meeting: co mówią o rowerze

Przeszukałem listę 43 prezentacji MUM 2026 (https://www.matsim.org/conferences/mum2026/) i przeczytałem slajdy wybrane po tytułach (lokalnie w `data/raw/g4/mum/`). Starsze lata (2021–2025): strony indeksowe zwróciły 403/404 przy pobieraniu skryptem; w wyszukiwarce znalazłem tylko stronę MUM 2025 (https://matsim.org/news/2025/matsim-user-meeting-2025/) bez listy prezentacji. **Starszych lat nie przeanalizowałem.**

| Prezentacja | Co dotyczy roweru | Dla nas |
|---|---|---|
| **105-15 Wu, Sharmeen, Jonsson — Eskilstuna (Szwecja, miasto średniej wielkości, 55 775 agentów, próbka 30%)** | Rower jako **tryb sieciowy** (bicycle contrib), sieć z NetAScore (bikeability), DEM, kalibracja udziału trybów do krajowej ankiety podróży. Parametry scoringu: stała roweru +1,5, auta -2, transit -1; czas -6 util/h dla wszystkich; dystans rower -1·10⁻⁴, walk -5·10⁻⁴, auto -2,5·10⁻⁴ util/m (tabela slajd 10). Na rowerze jeździ 5,37% linków. | Najbliższy wzór dla miasta wielkości Kutna: kalibracja stałych (ASC) do ankiety. Zakres (bikeability, scenariusze polityk) jest szerszy niż nasz. |
| **105-14 Metzler, Ziemke (DLR) — sieć rowerowa** | Generowanie sieci rowerowej z OSM: 27 kategorii infrastruktury, ścieżki/chodniki otwarte dla rowerów, elevacja z LiDAR; sieć Berlina ma 173 tys. linków (84 tys. wcześniej). Jeszcze draft PR #5168. | Pokazuje, że **rower sieciowy wymaga osobnego pipeline'u**; dla Kutna (23 km dedykowanej infrastruktury) zysk niewielki. |
| 107-10 Leong et al. — CitySim | Piesi (bezpieczeństwo, tłumy), nie dojazdy. | Nie dotyczy. |

W żadnym z przeczytanych slajdów **nie ma `beelineDistanceFactor` ani teleportacji** (przeszukałem tekst po: teleport, beeline, detour, crow, euclid, straight, speed). Czyli nie wiem z MUM 2026, jak inni liczą współczynnik; podejście Wu to sieć rowerowa, nie teleportacja. Abstraktów nie czytałem (tylko slajdy).

## 8. Rekomendacja i decyzje (do ustalenia przez użytkownika)

1. Zamiast 1,6 przyjąć **wartości z pomiaru** jako ZAŁOŻENIA w configu (źródło: ten dokument): **pieszo 1,25, rower 1,35, (auto 1,37 jako kontrola, bo auto idzie siecią)**. Zaokrąglić do 1,3 dla obu to też akceptowalne (błąd w skali ±0,05 przy medianowej odległości).
2. Czy akceptujemy błąd systematyczny dla krótkich tras (< 2 km, f 1,5–2)? Alternatywa: osobne `beelineDistanceFactor` per tryb to maksimum, które da MATSim; zależność od odległości wymaga własnego routera lub trybu sieciowego.
3. Czy testować wrażliwość roweru (kontrapas, chodniki jako dozwolone) przed zamrożeniem 1,35? Moja rekomendacja: tak, jednym dodatkowym przebiegiem, skoro rower jest najmniej pewny.
4. Czy dla pieszych i rowerzystów dodać limit odległości (żeby 10 km pieszo nie było trybem możliwym)? To osobna decyzja z `G4_tryby.md`.
5. Walidacja na danych obserwowanych: jeśli powstanie jakikolwiek pomiar (GPS, ankieta), porównać z tabelą w sekcji 3.
