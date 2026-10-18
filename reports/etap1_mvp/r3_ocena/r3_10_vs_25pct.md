# R3: próbka 10% vs 25% (100 iteracji, seedy 4711, 1, 2)

Data: 2026-10-17. Te same configi, różni się tylko próbka (`plans.xml.gz`: 2 573 osoby, `plans_25pct.xml.gz`: 6 433 osoby). To dwa niezależne losowania z tego samego seeda planów. Część różnic wynika więc z losowania popytu, a nie tylko ze skalowania przepustowości.

Wszystkie runy przeszły test: 0 stuck, nogi car 5 146 (10%) i 12 866 (25%). Pliki: `wyniki_10pct/`, `wyniki_25pct/`.

| miara | 10% | 25% |
|---|---|---|
| mediana czasu podróży, mieszkańcy / przyjeżdżający [min] (s4711, s1) | 16,8–16,9 / 25,0–25,2 | 15,2–15,5 / 24,1–24,2 |
| p90 mieszkańcy [min] | 36,8–36,9 | 33,3–35,0 |
| mediana prędkości, wyjazd 16:00 [km/h] | 25–26 | 30–31 |
| opóźnienie razem, przeliczone na 100% [poj.-h] (3 seedy) | 5 400–5 670 (× 10) | 4 050–4 520 (× 4) |
| GEH < 5 w szczycie 7–8 między seedami tej samej próbki | 92,7–94,9% | 98,9–99,5% |
| GEH < 5 w szczycie 7–8 między 10% a 25% | 82,5–84% | |

Natężenia przeskalowano do 100%; brano linki z ≥ 100 poj./dobę (`r3_10_vs_25pct_geh.json`, `wyniki_10pct/r3_10pct_convergence.json`).

## Wnioski (na poziomie, który pokazują dane)

- **10% daje więcej kongestii niż 25%:** o ok. 30% więcej opóźnień, a popołudniowy szczyt jest wolniejszy o ok. 5 km/h. Dobowe natężenia są zgodne (GEH < 5 na 100% linków).
- **10% jest mniej powtarzalne między seedami** (93–95% wobec 99% linków z GEH < 5 w szczycie).
- **Nie wiadomo, który wynik jest bliższy prawdy.** Brak runu 100% z tymi planami i 100 iteracjami oraz brak pomiarów. Do wniosków o kongestii w szczycie przyjmujemy 25%. 10% wystarcza do testów technicznych.
