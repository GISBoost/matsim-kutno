# Audyt G5, poprawka K1: strefy graniczne na ślepych końcach DK92 (zach.) i DK60 (płn.)

Data: 2026-10-18. Ustalenie: `reports/etap2/audyt_g5/audyt_g5.md` K1. Decyzja: D21 (pkt K1).

## Diagnoza (potwierdzona)

- PBF obejmuje tylko łódzkie. Skan sieci (węzły z jednym sąsiadem dla typów `entry_road_types`) znalazł 9 ślepych końców dróg primary/secondary:
  - 7 leży ≤ 703 m od krawędzi obszaru, więc reguła pasa 1 km już robiła z nich wjazdy i wyjazdy;
  - 2 leżą dalej i nie były strefami:
    - DK60 płn. (Gostynin): węzeł 2970197424 (528 777 E, 498 796 N), 1 900 m od krawędzi;
    - DK92 zach. (Kłodawa): węzeł 3063418575 (504 407 E, 487 296 N), 2 316 m od krawędzi.
- Ślepe końce dróg lokalnych (residential/unclassified) przy granicy województwa też istnieją, ale te klasy nie są wjazdami (`entry_road_types`), tak samo jak na krawędzi obszaru.

## Poprawka (`pipeline/plans.py`)

Link drogi wjazdowej, którego zewnętrzny węzeł jest ślepym końcem, traktujemy jak link w pasie granicznym. Reguła jest ogólna, nie wpisuje węzłów ręcznie.
- `border_links.csv`: 31 → 33 wjazdy i 31 → 33 wyjazdy. Nowe linki: `2934227590000f/r` (DK60 N) i `3021014880009f/r` (DK92 W).
- Przyjeżdżający i wyjeżdżający: 105 osób próbki 25% (Gostynin 1404011/1404022, Kłodawa 3009032 i inne gminy z zachodu i z północy) zmienia link wjazdu na najbliższy. Lista odciętych gmin > 100 km się nie zmienia (30 gmin).
- Walidator planów (`validate_k1.log`, plany `plans_k1_25pct` z macierzami R4): ok, sha256 powtarzalny.

## Test diagnostyczny: estymacja O-D z nowymi strefami (bez runu MATSim)

Ta sama metoda i cel co R4 (`background_od.py 30 … cls=lcv|heavy`, model pracujących z R1). **Cel GPR ma jeszcze błąd K2, więc to nie jest nowa baza**, tylko sprawdzenie, czy fantom znika.

| | R4 lekkie | K1 lekkie | R4 ciężkie | K1 ciężkie |
|---|---|---|---|---|
| podróże na dobę | 85 203 | 66 841 | 25 312 | 17 680 |
| pary Dąbrowice / Krośniewice-m. / Krośniewice-w. między sobą | 24 041 | **54** | 9 523 | **27** |
| gmina–gmina | 29 954 | 6 682 | 10 730 | 1 250 |
| tranzyt granica–granica | 21 594 | 25 858 | 6 290 | 7 461 |
| nowe strefy DK60 N + DK92 W (wjazd + wyjazd) | – | 9 495 | – | 2 757 |
| odcinki dopasowania (trasy swobodne) | 100% | 100% | 100% | 100% |
| Objazdowa 91124 (kontrolny) | 130% | 137% | 68% | 75% |
| Bitwy pod Kutnem 91866 (kontrolny) | 91% | 92% | 72% | 72% |
| DK91d 91892 / 91119 (lokalne) | 24 / 37% | 38 / 39% | 20 / 40% | 27 / 41% |

## Wnioski

1. Fantomowa para znika (−99,8%). Liczniki DK92 91121/91122 wypełnia teraz ruch z zachodu, a łączny ruch tła spada o 22% (lekkie) i 30% (ciężkie), przy tym samym dopasowaniu.
2. Objazdowa rośnie offline o 7 pp (lekkie). Ruch z DK60 N jedzie przez Kutno. To nadal problem K5 i wag a priori (I4), więc wraca przy poprawce I4.
3. Nowe strefy nie mają własnego licznika na granicy. Ich natężenie wyznaczają 91121 (DK92) i 91878 (DK60 Sójki). SCPR 30025 i dane DK60 N (Lisica 14005) jako dodatkowe cele: do sprawdzenia przy K2.
4. Wariant pełny (sieć z PBF wielkopolskie + mazowieckie) nie jest potrzebny do tej poprawki. Zostaje w planie, gdyby ruch lokalny przy granicy województwa okazał się ważny.
