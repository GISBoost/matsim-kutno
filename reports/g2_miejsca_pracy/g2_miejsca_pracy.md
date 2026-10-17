# G2 / D17: liczba miejsc pracy (B, C) i wyjeżdżający (O1)

Data: 2026-10-17. Decyzja D17 (`DECISIONS.md`), warianty opisane w `docs/research/G2_warianty.md`. Próbka **10%** (prośba użytkownika), 100 iteracji, seedy 4711, 1, 2 (`output/g2{b,c}_10pct_s*`). Wszystkie 6 runów liczone równolegle po 2 wątki, ok. 11 min.

## Co się zmieniło w popycie (skala 100%)

| | A (D16, dotychczas) | **B (baza)** | C (wrażliwość) |
|---|---|---|---|
| mieszkańcy pracujący w Kutnie | 17 546 (estymacja D5) | 14 586 (P4507 − 2 669) | 11 223 |
| przyjeżdżający (po odcięciu > 100 km) | 8 139 | 8 139 | 6 263 |
| **miejsca pracy w Kutnie** | 25 685 | **22 725** | **17 486** (= P4508) |
| wyjeżdżający w modelu (O1) | 0 | 2 481 | 2 481 |
| agenci w próbce 10% | 2 568 | 2 521 | 1 997 |

- Wyjeżdżający: 2 669 w macierzy NSP, z czego 188 (18 gmin) odcięte > 100 km od wyjazdu. W próbce 10% jest 248 osób: 80 pracuje w budynkach gmin powiatu, 168 kończy podróż na jednym z 11 linków wyjazdowych. Najczęściej używane wyjazdy to A1 w stronę Warszawy (58) i w stronę Łodzi (48).
- Dom wyjeżdżającego to budynek mieszkalny w Kutnie w obwodzie losowanym wagą pracujących (D5). Praca trwa 8 h na budynku albo na linku wyjazdowym. **ZAŁOŻENIE** (jak D16/A): poza siecią nie ma czasu dojazdu, więc wyjeżdżający wraca na granicę po 8 h, a nie po 8 h plus dwa dojazdy.
- Liczba agentów zgadza się z oczekiwaną co do osoby. Rodzaje agentów różnią się od proporcji o mniej niż 1% (zaokrąglanie metodą największych reszt na całości: B ma 1 465 mieszkańców zamiast 1 459 i 808 przyjeżdżających zamiast 814).

## Testy

- Plany (`B/`, `C/plans_10pct_plans.{json,png}`):
  - każda osoba ma łańcuch home–car–work–car–home, domy są w obszarze, praca mieszkańców i przyjeżdżających w gminie Kutno;
  - wyjeżdżający mają dom w gminie i pracę poza nią;
  - sha256 powtarzalny, id osób unikalne.
  - Pierwsza wersja nie przeszła walidacji: wyjeżdżający spoza powiatu trafili do gałęzi przyjeżdżających (ERRORS 14).
- Eventy (`events_s*.json`): B 5 042 i C 3 994 nóg car, czyli tyle, ile w planach. 0 stuck we wszystkich 6 runach.

## Wyniki (próbka 10%; opóźnienia w pojazdogodzinach próbki)

| | A: r3 10% (przed D16, bez wyjeżdżających) | **B** | C |
|---|---|---|---|
| opóźnienie razem, 3 seedy [poj.-h] | 540–567 | **370–405** | 146–166 |
| mediana czasu podróży: mieszkańcy / przyjeżdżający / wyjeżdżający [min] (s4711) | 16,8 / 25,0 / – | 16,2 / 24,2 / 25,1 | 13,9 / 22,9 / 23,4 |
| p90 mieszkańcy [min] | 36,8 | 32,3 | 22,5 |
| mediana prędkości car, wyjazd 7:00 / 16:00 [km/h] | 29,6 / 25,9 | 33,0 / 31,8 | 36,7 / 39,6 |
| GEH < 5 w szczycie 7–8 między seedami | 93–95% | 93,3–95,1% | 95,6–96,1% |

- **Wariant B** zmniejsza popyt o 2% (−11,5% miejsc pracy, +2 481 wyjeżdżających), a opóźnienia o ok. 28%.
- **Wariant C** zmniejsza popyt o 22%, a opóźnienia o ok. 71%. Kongestia rośnie nieliniowo z popytem, więc liczba miejsc pracy to najczulszy parametr modelu.
- Najbardziej obciążony link jest ten sam we wszystkich wariantach (primary `2001576790001r`): B 68 poj.-h, C 15 poj.-h w s4711.
- Wyjeżdżający jadą w szczycie porannym od centrum na wyloty, czyli przeciwnie niż przyjeżdżający. Prędkości w szczycie i tak rosną, bo spadek liczby mieszkańców jadących wewnątrz miasta przeważa.
- **Ograniczenia porównania z A:**
  - A to stare runy 10% sprzed D16. Wpływ D16 na 25% mieścił się w rozrzucie seedów (`reports/d16_przyjezdzajacy/`).
  - Bez pomiarów (G5) nie da się rozstrzygnąć, który wariant jest bliższy rzeczywistości. Różnica B/C pokazuje tylko, jak bardzo wynik zależy od niewyjaśnionej luki 30% między źródłami.

## Pliki

- `B/`, `C/`: plany (`plans_10pct_plans.*`), eventy (`events_s*.json`), opóźnienia (`delay_s*.{json,png}`), zbieżność i GEH między seedami (`convergence.*`), logi runów.
- `porownanie_A_B_C_s4711.{png,json}`: dystrybuanty czasów (także wyjeżdżających), prędkość wg godziny, score.
- Odtworzenie: `uv run python -W ignore pipeline/plans.py scenarios/kutno/plans_g2b_10pct.xml.gz 0.1` (C: dopisać `jobs_total=17486`), potem `TAG=g2b PLANS=plans_g2b_10pct.xml.gz THREADS=2 XMX=1500m LOGDIR=reports/g2_miejsca_pracy/B bash output/r3_runs.sh 10pct 4711 1 2`.
