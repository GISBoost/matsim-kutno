# F6 — skala 100% (2026-10-16)

**Status: ZALICZONA** (test jak w F5 + RAM). Ocena sensowności dla Kutna należy do człowieka.

## Plany 100%

Polecenie: `pipeline/plans.py scenarios/kutno/plans_100pct.xml.gz 1.0`, ten sam seed i config co F4.

| Test (`validate_plans.py … 1.0`) | Wynik |
|---|---|
| osoby | 25 732 = round(1,0 × 25 732) |
| łańcuch h-car-w-car-h, domy w obszarze, praca w gm. Kutno | 100% / 0 poza / 0 poza |
| sha256 powtarzalny | tak |
| domy w losowym punkcie (obwód bez budynków) | 58 (ten sam obwód `6509902`) |

Mediana odległości w linii prostej: mieszkańcy 3,7 km, przyjeżdżający 13,1 km (F4: 3,8 i 13,0). Wylosowano 833 budynki pracy, top 5 skupia 12,8%. Plany 10% są niezmienione (sha256 `525ed292…`).

## Run

```
java -Xmx10g -jar matsim/matsim-example-project-0.0.1-SNAPSHOT.jar run --config scenarios/kutno/config_100pct.xml
```

- `config_100pct.xml` różni się od `config_10pct.xml` tylko plikiem planów, katalogiem wyjściowym i factors 1,0.
- Wynik: kod 0, **4 min 9 s** dla 20 iteracji (11–17 s na iterację).
- RAM: maks. „used RAM” z MemoryObserver to **1 017 MB** (próbkowane co minutę) przy `-Xmx10g`, więc kryterium < 10 GB jest spełnione z dużym zapasem.
- Log: `reports/f6_run.log`. Jedyny wyjątek to nieszkodliwe ostrzeżenie Guice/ASM.

| Test | Wynik |
|---|---|
| departure car = arrival = 2N | 51 464 = 2 × 25 732 (`reports/f6_events.json`) |
| stuck | 0 |
| każda osoba: odjazdy = przyjazdy | tak |

## Porównanie z F5 (`pipeline/compare_runs.py` → `reports/f6_compare.png`, `.json`)

| | F5 10% | F6 100% |
|---|---|---|
| czas podróży, mediana: mieszkańcy / przyjeżdżający | 17,3 / 25,6 min | 16,8 / 25,3 min |
| p90: mieszkańcy / przyjeżdżający | 42,1 / 41,8 min | 45,1 / 41,7 min |
| prędkość car, mediana o 7:00 / 8:00 | 27,4 / 31,3 km/h | 33,9 / 33,9 km/h |
| prędkość car, mediana o 16:00 / 17:00 | 28,8 / 26,4 km/h | 31,2 / 22,8 km/h |
| opóźnienie łącznie | 624 poj.-h (7,3 min na nogę car) | 6 830 poj.-h (8,0 min na nogę car) |
| score avg executed: it. 0 → 20 | 114,2 → 134,7 | 110,2 → 134,4 |

- **Rozkłady czasu podróży są prawie identyczne.** Próbka 10% ze skalowaniem przepustowości dobrze odwzorowuje 100% na poziomie rozkładów.
- **Różnice widać na poziomie godzin i linków.** Przy 10% szczyt poranny jest głębszy, a popołudniowy płytszy niż przy 100%. Przyczyną jest dyskretyzacja (10% = mało pojazdów na link, przepustowość 0,1) i inny wynik wyboru tras. Wnioski o konkretnych odcinkach wyciągamy tylko ze 100% (D8).
- Przy 100% pojawiają się też odjazdy po 24:00. To powroty z pracy osób, które wyjechały wieczorem lub w nocy (rozkład GBR, przedział 20–24).

## Kongestia przy 100% (`reports/f6_delay.json`, `.png`)

Te same okolice co w F5: dojazd do wschodniej strefy pracy. Kolejność odcinków jest jednak inna.

| link | droga (OSM) | pojazdy | śr. opóźnienie |
|---|---|---|---|
| 383845230002r | ul. Metalowa (residential) | 2 839 | 286 s |
| 410250640002r | ul. Sklęczkowska, DK92 (primary) | 5 444 | 202 s |
| 2020517410007r | tertiary bez nazwy przy węźle A1 | 3 070 | 328 s |
| 2456705130015r | ul. Józefów (residential) | 3 160 | 268 s |
| 3176338800019r | ul. Wschodnia (tertiary) | 2 897 | 236 s |

- Przy 100% ReRoute rozkłada ruch z DK92 na równoległe ulice lokalne (Metalowa, Józefów, Wschodnia). Te ulice mają 600 poj./h na pas, więc tam też powstają kolejki.
- Te same zastrzeżenia co w F5:
  - D6: wszyscy autem.
  - D7: praca ważona powierzchnią hal.
  - Capacity domyślne Supersonic.
- Nie porównano z pomiarami (GPR) ani natężeniami. **To nie jest prognoza ruchu w Kutnie (D2, D6).**

## Wykresy

- `reports/f6_run.png`, `reports/f6_delay.png`, `reports/f6_compare.png`, `reports/f6_plans.png`.
- Wykresy MATSim w `output/f6_100pct/`: `scorestats.png`, `modestats.png`, `traveldistancestats*.png`, `stopwatch.png`.

## Korekta po recenzji R3 (2026-10-16)

Zob. `docs/research/R3_ocena_modelu.md`. Ten raport zawiera trzy nieuprawnione sformułowania:
- **„Score stabilizuje się”** to artefakt `fractionOfIterationsToDisableInnovation=0.8`, nie dowód zbieżności. 20 iteracji to za mało na równowagę.
- **„10% dobrze odwzorowuje 100%”** dotyczy wyłącznie zagregowanych rozkładów. Przy 10% `storageCapacityFactor` powinien wynosić ok. 0,18, a nie 0,1 (FAQ MATSim).
- **Ranking wąskich gardeł** wynika z niezbiegniętego runu i z założeń D6/D7. Nie jest to wynik o ulicach Kutna.
