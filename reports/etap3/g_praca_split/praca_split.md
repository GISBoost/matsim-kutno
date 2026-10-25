# Krok 4A etapu 3: praca = przyjazd + odjazd (D31, wariant, domyślnie wyłączony)

Data: 2026-10-25. Decyzja: [D31](../../../docs/projekt/DECISIONS.md). Runy: GitHub Actions, run `40206095692` (10 jobów: r92 = z podziałem pracy, r91 = R9.2 bez podziału, ta sama platforma i te same macierze O-D, 25%, 50 iteracji; 3 seedy MATSim na planach p0 + 2 seedy planów p1, p2). Estymacja O-D: run `40204663784` (tag r92). Liczby: [praca_split_porownanie.json](praca_split_porownanie.json), wykres [praca_split_porownanie.png](praca_split_porownanie.png), skrypt `praca_split_porownanie.py`.

## 1. Co zrobiono
`plans.py`, `work_split = "on"`: praca to dwie aktywności `work` w tym samym punkcie, przyjazd (link wybrany do linku odjazdu z domu) i odjazd (link wybrany do linku powrotu do domu), z nogą `walk` o długości 0 m między nimi i aktywnością odjazdu trwającą 1 s. Podział dotyczy 95,5% agentów (tylko tam, gdzie oba linki się różnią). Wyjeżdżający odjeżdżają z linku wjazdowego tej samej drogi. `work_split = "off"` odtwarza plany R9.2 bajt w bajt (sha256 `d66d6d26…`).

## 2. Wyniki (mediana 5 runów; rozrzut referencyjny = seedy planów r91)
| | R9.2 (r91, bez podziału) | praca przyjazd+odjazd (r92) |
|---|---|---|
| podróże z zawrotką na starcie lub końcu | 12,4% | **1,1%** |
| dodatkowy czas w zawrotkach | 38,8 poj.-h (0,49% czasu) | 2,6 poj.-h (0,03%) |
| pracujący „tam”: start / koniec | 1,0 / 25,0% | 0,9 / 2,2% |
| pracujący „z powrotem”: start / koniec | 52,3 / 0,9% | 1,8 / 0,7% |
| nogi car = plany, stuck | 5/5, 0 | 5/5, 0 |
| GPR lekkie w ±15% | 14/15 (poza DW 10043) | 14/15 (DW 10043 +18,3%) |
| GPR ciężkie w ±15% | 13/15 | 13/15 (DK 10044 −16,3%, DK 91878 −21,3%) |
| zmiana natężenia na odcinku GPR | | mediana 0,0%, maks. 0,5% (rozrzut planów: lekkie 4,2%, ciężkie 6,5%), 0 odcinków ponad rozrzut |
| opóźnienie dobowe [poj.-h próbki] | 224,2 / 224,3 / 228,6 / 248,6 / 217,5, mediana 224,3 | 220,9 / 231,2 / 229,8 / 247,5 / 216,9, mediana 229,8 (rozrzut planów 31,1) |
| przyczyny opóźnienia (pojemność / węzeł / spillback) | 19 / 44 / 37% | 21 / 41 / 37% |
| podróż car pracujących | 17,11 min, 11,10 km | 16,87 min, 10,93 km (rozrzut planów 0,36 min) |
| macierze O-D (estymacja r92 vs r91) | lekkie 47 916, ciężkie 19 368 | −0,11% i −0,03% (szum platformy z kroku 0: −0,12% i −0,04%), `od_warnings` ok |

## 3. Wniosek
Podział usuwa zawrotki (12,4% → 1,1% podróży, koszt czasu z 0,49% do 0,03%), ale **ruch się nie zmienia ponad rozrzut seedów planów**: natężenia o najwyżej 0,5%, opóźnienie i czas podróży w granicach rozrzutu, macierze O-D bez zmian. Zysk jest poprawnością trajektorii, nie zmianą wyników. Koszt: dodatkowa aktywność i noga `walk` 0 m w 95,5% planów, podróże piesze „work → work” w analizach, dwa razy typ `work`.

**Decyzja użytkownika: `work_split = "off"` (baza zostaje R9.2); wariant `on` zostaje w kodzie jako opcja.** Zawrotki przy pracy (52% i 25% podróży, 12,4% łącznie) są znanym ograniczeniem R9.2.

## 4. Jak czytać wykres ([praca_split_porownanie.png](praca_split_porownanie.png))
- **Lewy panel:** słupki = odsetek podróży z zawrotką na starcie lub końcu trasy (suma „start + koniec”) wg rodzaju agenta: mieszk. = mieszkańcy pracujący w Kutnie, dojeżdż. = przyjeżdżający, wyjeżdż. = pracujący poza Kutnem, tło lekkie/ciężkie = ruch tła. Szary = R9.2 bez podziału, niebieski = z podziałem pracy.
- **Środkowy i prawy panel (lekkie, ciężkie):** oś X = numery odcinków GPR (liczniki GDDKiA), oś Y = zmiana natężenia dobowego modelu z podziałem względem bez podziału, w % (mediana 5 runów). Szare tło = rozrzut natężeń między seedami planów kontroli (max−min)/średnia na odcinku: zmiana mieszcząca się w szarym polu jest szumem, nie efektem podziału.
- Liczby: `praca_split_porownanie.json`.

## 5. Ograniczenia
- Test zawrotek na 2 iteracjach (lokalny) dał 0,5%, na 50 iteracjach GHA 1,1%.
- Odległość swobodna w wyborze kierunku pomija zakazy skrętu i opóźnienia (jak D29).
- Kontrola r91 ma plany bez atrybutów osób (symulacja identyczna z R9.2, atrybuty jej nie zmieniają, D30).
- Czas podróży z TomTom nie był liczony (D22).
