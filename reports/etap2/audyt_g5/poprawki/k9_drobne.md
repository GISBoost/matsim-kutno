# Krok 9: drobne ustalenia audytu D1–D9

Data: 2026-10-18. Ustalenia: `audyt_g5.md` §2 „DROBNE”. Decyzja: D21 (pkt D1–D9).

## D1/D2: kierunki A1 i udziały kierunkowe DK (wdrożone przed referencją)

- **Konwencja ustalona źródłem.** GDDKiA, *Wytyczne GPR 2020, cz. 3: Instrukcja o sposobie przeprowadzenia GPR*: „L – kierunek ruchu pojazdów zgodnie z malejącym pikietażem, P – kierunek ruchu pojazdów zgodnie z rosnącym pikietażem”. Opis odcinka „od – do” biegnie według narastającego pikietażu. Plik `data/raw/g5/gpr2025/instrukcja_gpr2020_cz3.pdf` (5,5 MB, manifest, ZRODLA). ZAŁOŻENIE: GPR 2025 używa tej samej konwencji (te same kolumny „Kierunek Lewy / Prawy”).
- **Kierunek linku względem pikietażu.** Linie odcinków w `dk_odcpom_web.zip` biegną zgodnie z pikietażem: koniec odcinka = początek następnego, z tymi samymi pikietażami (71410 → 91820 → 91821 na 244,500 i 253,570 km; DK60 i DK92 tak samo). Dla linku licznika: kierunek stycznej do linii odcinka w rzucie środka linku vs kierunek linku (|cos| 0,61–1,00 na wszystkich 30 linkach DK).
- **Wynik.** Na wszystkich trzech odcinkach A1 jezdnia „najbliższa”, która dostawała udział „prawy”, jedzie w kierunku malejącego pikietażu (na północ). **Audyt D1 potwierdzony:** kierunki były zamienione (o 1,7–2,6 pp). Na DK udział 0,5 zastąpiony udziałami GPR: odchylenie do ±5,2 pp na odcinkach dopasowania (91122), ±4,7 pp na Bitwy pod Kutnem, ±3,8 pp na 91119.
- **Kontrola.** Niezależny skrypt w scratchpadzie (to samo kryterium, ale liczone na `gpr_linki.csv` przed zmianą) dał identyczne udziały (różnica 0,0). Udziały na każdym odcinku sumują się do 1. Pozostałe kolumny `gpr_linki.csv` są bez zmian. Kod: `g5_gpr.py share()`.
- **Wpływ na estymację** (R6a → R6, ten sam R1): lekkie 65 905 → 65 755 podróży/dobę (−0,2%), ciężkie 22 990 → 22 972. Sumy odcinków bez zmian (poza 91119 lokalny: 42% → 41%). Na kierunkach zmiana do ±5%, czyli więcej niż mediana rozrzutu seedów R3 (0,6%) i porównywalnie z rozrzutem seedów planów (krok 8). Dlatego nowa baza R6 i referencja (krok 8) używają już D1/D2 (`background_od_r6b_*`). Run kroku 6 to R6a (sprzed D1/D2), opisany w `g5_r6.md`.

## D3: R3 na 3 seedach to 13/14

`g5_r3.md`: 10044 = 2 772 / 3 261 = 0,85004, czyli w ±15%. Dopisana adnotacja „audyt D3”.

## D4: GEH w godzinie szczytu (K5)

GEH ze średniej godziny doby (K5: Objazdowa 4,8) zaniża wartość. W godzinie szczytu (8% doby; Lisica, lekkie, 15–16: 8,3%) R3 daje: Objazdowa **6,7** (6,9 przy 8,3%), Bitwy pod Kutnem 4,0. Objazdowa przekracza więc próg 5. Adnotacja w `k5/k5_objazdowa.md`. Wariant A (decyzja użytkownika) zostaje jako znana rozbieżność, ale argument „GEH < 5” odpada. R6a: Objazdowa 127%, GEH w szczycie ok. 6,6.

## D5: tabela PCE ze skryptu

Sprawdzone: `g5_pce.py` (K2) odtwarza `pce_wrd13_gpr.csv` i `pce_wrd13_gpr_sdrr.csv` bit w bit (cmp). Tabela zależy od `gpr_punkty.csv`, a ten po D1/D2 jest bez zmian.

## D6: config zapisuje bazę

Zrobione w kroku 6. `config_{10,25,100}pct.xml` wskazują `plans_g5r6_*pct.xml.gz`, `qsim.vehiclesSource=fromVehiclesData` i `vehicles.vehiclesFile=plans_g5r6_*pct_vehicles.xml.gz`. Run bazy wynika z samego configu (`r3_runs.sh` bez PLANS/VEH).

## D7: okno 6–9 w `queues.py` opisane przy liczbach

Przy liczbach udziału opóźnień w czasie jazdy w `g5_r4.md` (5,6%) i `g5_r5.md` (4,7%) dopisane „okno 6–9, przejazdy pośrednie (`queues.py`)”; `g5_r2.md` i `g5_r3.md` podawały okno już wcześniej. Nowe raporty (k6, R6) podają okno jawnie.

## D8: archiwizacja źródła prędkości ORS

`data/raw/g5/ors/VehicleFlagEncoder_main_2026-10-18.java` (stan z audytu) i `VehicleFlagEncoder_v6.6.0.java` (tag v6.6.0, 2021-06-08, rok macierzy GUS) są w manifeście i w ZRODLA. Prędkości domyślne (motorway 100, trunk 85, primary 65, secondary 60, tertiary 50, unclassified 30, residential 30) i 0,9 × maxspeed są w obu wersjach identyczne. Wniosek z `g5_czasy_pce.md` (0,76 → 0,84) nie zależy więc od wersji. Nie wiemy, której wersji GUS faktycznie użył.

## D9: typ `ciezki`

- **Ciągniki rolnicze.** Ustawowo 40 km/h, w modelu 80 km/h. W celu ciężkich SDRDR to 232 z 54 961 poj./dobę na 20 odcinkach (**0,42%**), najwięcej na DW (4–6% ciężkich na DW573/581/583/702, 0–1% na DK). Wpływ pomijalny, osobnego typu pojazdu nie dodaję (ZAŁOŻENIE).
- **Długość 15 m, szerokość 2,5 m.** W strukturze ciężkich GPR (SDRDR) dominują ciężarowe z przyczepą lub naczepą: na odcinkach DK 42–93% (ważone 86%), na DW 54–68% (60%). Limity dla zespołów pojazdów to 16,5 m (ciągnik z naczepą) i 18,75 m (z przyczepą), szerokość 2,55 m (dyrektywa 96/53/WE, zał. I). Pliku dyrektywy nie pobierałem; to ZAŁOŻENIE z podaną podstawą. 15 m to średnia ważona zespołów (ok. 16,5 m) i solówek (ok. 10–12 m).
- **Czy QSim używa długości.** Test: R6 25%, iteracja 0 (te same trasy), typ `ciezki` 15 m vs 30 m (`k9_len/`, `output/k9_len{15,15b,30}`). Opóźnienie 1 799,2 poj.-h w obu i w powtórce 15 m, `vol_car` identyczne na 10 383/10 383 linkach. **QSim 2026 nie używa długości pojazdu** (pojemność składowania liczy z pce), więc 15 m i 2,5 m to tylko opis. Pliki eventów różnią się kolejnością zapisu także między dwoma runami z tym samym configiem (4 wątki), dlatego porównanie robię po wynikach, nie po sha256.
- **Końce ciężkich w budynkach mieszkalnych i gospodarczych:** poprawione w kroku 4 (`heavy_ends = "work"`): 50,6% → 0,1%.

## Czy D1–D9 wymagają powtórzenia estymacji i runu

Tylko D1/D2 zmieniają cel GPR (kierunki). Estymację powtórzyłem (`r6b`), a referencja z kroku 8 jest już na nowej bazie. Pozostałe punkty nie zmieniają wejść modelu.
