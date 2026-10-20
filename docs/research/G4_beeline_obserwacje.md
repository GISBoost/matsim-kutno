# Dziennik obserwacji — eksperyment `beelineDistanceFactor` (2026-10-17)

Chronologicznie, także pomyłki. Wynik końcowy: `docs/research/G4_beeline.md`.

1. **Wyjściowa hipoteza użytkownika:** f ≈ 1,6, bo „pole koła / pole izochrony ≈ 1,6”. Zauważyłem, że stosunek pól to f² (przy jednorodnym objeździe), a π/2 = 1,57 to stosunek pola koła do rombu normy L1 w idealnej siatce, czyli f ≈ 1,25–1,27. Hipotezę sprawdziłem empirycznie na dwa sposoby (pary dom–praca, izochrony).
2. **QGIS przez MCP:** `ping` działa, gdy QGIS nie liczy. Długi `execute_code` (> kilkadziesiąt sekund) kończy się błędem MCP po stronie klienta, ale **skrypt działa w QGIS dalej**; gdy QGIS liczy, ping też wygasa. Auto (110 celów, 10 394 par) liczyło 1135 s, rower ok. 3 min, pieszo ok. 5 min. Błąd „Error executing tool” nie oznaczał zawieszenia. Użyłem pliku-znacznika (`car_done.txt`) do wykrycia końca.
3. **Błąd w pierwszym podejściu:** część startów zwracała null geometrię (punkt bez trasy) → wyjątek. Naprawione przez pominięcie (pieszo 46, rower 121, auto 114 z 10 394).
4. **Koszt algorytmu:** `shortestpathlayertopoint` buduje graf na każde wywołanie (~1,7 s), więc czas zależy od liczby *różnych celów*, nie par. Zredukowałem do 110 celów (losowanych z wagą = liczba pracowników).
5. **Obciążenie próbki:** wylosowane cele dają dłuższe dystanse niż pełna populacja (średnio 4,2 vs 3,7 km, KS = 0,146). Skorygowałem przez przeważenie binów w `fit_factor.py`.
6. **Dojścia do sieci:** ścieżka QGIS zaczyna się na najbliższym punkcie sieci, nie w punkcie startowym; `cost` ≈ długość geometrii + ok. 4 m. Dojścia dom→sieć (śr. 21 m) i sieć→praca (śr. 90 m, bo duże zakłady) dodałem jako linię prostą. Bez nich f niższe o 0,02–0,04.
7. **Rower > pieszo:** wynik f_rower (1,35) > f_pieszo (1,25) wydaje się nieintuicyjny, ale wynika z założenia filtra: rower nie używa chodników (`footway` bez `bicycle=yes`), których pieszy ma ~165 km. Wrażliwość nie była testowana.
8. **Korelacja f między trybami:** rower–auto 0,94, pieszo–auto 0,80, pieszo–rower 0,82. Rower i auto mają prawie tę samą sieć drogową; pieszych różnią skróty przez chodniki i ścieżki.
9. **Offset b:** OLS `trasa = a·linia + b` daje a = 1,11–1,19 i b = 0,55–0,75 km. To znaczy, że stałe dojścia i lokalne obejścia dają dużą część objazdu na krótkich trasach.
10. **Błąd w `isochrones.csv`:** kolumny `mean_end_euclid`, `max_end_euclid` liczą odległość do niewłaściwego końca linii (f ≈ 10), więc `f_meanend` i `f_max` są śmieciowe. Używam tylko pól obwiedni. Do poprawy, jeśli metoda zostanie powtórzona.
11. **Wrażliwość izochron:** obwiednia wklęsła (0,25) daje wyższe f niż wypukła o 0,1–0,4; to metoda gorsza niż bezpośredni pomiar po parach.
12. **MUM 2026:** w przeczytanych slajdach (Wu/Eskilstuna, Metzler/DLR, Leong) nie ma teleportacji ani `beelineDistanceFactor`; rower jest tam trybem sieciowym. Wcześniejszych lat nie przeanalizowałem (strony indeksowe 403/404 przy pobieraniu).
13. **Czego nie sprawdzono:** brak testu configu MATSim z nowymi współczynnikami (zasady projektu pkt 9 wymaga 2 iteracji, ale G4 jest poza zakresem MVP); brak porównania z siecią MATSim `network.xml.gz` (auto liczone z OSM); brak danych obserwowanych o dojazdach.
