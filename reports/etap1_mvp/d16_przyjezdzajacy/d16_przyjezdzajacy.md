# D16: przyjeżdżający spoza powiatu (wjazd o godzinie z profilu, odcięcie > 100 km)

Data: 2026-10-17. Decyzja użytkownika D16 (`docs/projekt/DECISIONS.md`). Próbka 25%, 100 iteracji, seedy 4711, 1, 2 (`output/d16_25pct_s*`).
**Od teraz to są wyniki referencyjne** w miejsce `r3_ocena/wyniki_25pct/`.

## Zmiana

- **A.** Przyjeżdżający spoza powiatu pojawia się na linku wjazdowym o godzinie z profilu GBR (D14). Wcześniej (D15/1) doliczałem dojazd z gminy do granicy (odległość × 1,3 / 72 km/h). Mediana tego przesunięcia wynosiła 14 min, maksimum 5,9 h (Szczecin).
- **B.** Pomijamy gminy, których centroid leży dalej niż 100 km od najbliższego wjazdu (`max_border_km` w `config/kutno.toml`).
  - Odcięte: 12 gmin, 47 osób w 100% (0,2% popytu), m.in. Szczecin, Gdańsk, Kraków, Wrocław, Poznań.
  - Najdalsza zostawiona gmina leży 98,7 km od wjazdu. Warszawa (ok. 89 km, 27 osób) zostaje.
  - Mało, bo macierz GUS i tak pomija przepływy < 3 osób.

## Plany (`plans_10pct/25pct/100pct.json/png`)

- Liczba osób: 2 568, 6 421 i 25 685. Każda zgodna z oczekiwaną po odcięciu.
- Plany są deterministyczne (sha256 identyczny po ponownym wygenerowaniu). Start każdej osoby = godzina z profilu.
- Kontrola przed runem: top-10 miejsc pracy to hale `industrial` i `warehouse` (1,6–3,1 ha). Najpóźniejszy start to 23:52.

## Runy 25%

| | przed D16 (s4711 / s1) | po D16 (s4711 / s1) |
|---|---|---|
| nogi car, stuck | 12 866, 0 | 12 842, 0 (wszystkie 3 seedy) |
| mediana czasu podróży, mieszkańcy / przyjeżdżający [min] | 15,5 / 24,1 ; 15,2 / 24,2 | 15,2 / 24,3 ; 15,1 / 24,1 |
| p90 mieszkańcy [min] | 35,0 ; 33,3 | 34,1 ; 35,2 |
| opóźnienie razem [poj.-h próbki], 3 seedy | 1 014–1 130 | 1 076–1 091 |
| GEH < 5 w szczycie 7–8 między seedami | 98,9–99,5% | 97,8–99,6% |
| ostatni przyjazd w symulacji (s4711) | 32:34 | 32:22 |

- GEH < 5 między runem przed i po D16 (seed 4711) ma 96,1% linków w szczycie 7–8.
- Wpływ D16 na wskaźniki zbiorcze jest w granicach rozrzutu między seedami. To oczekiwane, bo zmiana dotyczy ok. 520 z 6 421 osób, a przesunięcie wynosiło zwykle kilkanaście minut.
- Przyjazdy po północy (78 nóg) nie znikają, bo pochodzą z wyjazdów wieczornych w profilu GBR (praca zmianowa), a nie z dalekich dojazdów.
- **Zysk z D16 jest metodyczny, nie liczbowy:** nie ma już agentów jadących codziennie z Gdańska ani startów przesuniętych o kilka godzin, a model ma dwa założenia mniej (72 km/h, krętość 1,3).

## Pliki

- `plans_*.json/png`: walidacja planów.
- `events_s*.json`: test eventów.
- `delay_s*.json/png`: opóźnienia.
- `convergence.json/png`: zbieżność i seedy.
- `przed_po_d16.json/png` i `geh_przed_po.json/png`: porównanie przed i po D16.
- `run_s4711.png`: mapa runu.
- `run_25pct_s*.log`: logi MATSim.
