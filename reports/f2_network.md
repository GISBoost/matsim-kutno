# F2 — sieć OSM, powiat kutnowski + bufor 3 km (2026-10-16)

**Status: ZALICZONA** (prędkości wg D13)

Ścieżka: `pipeline/make_area.py` (BREC 2021 → gmina / powiat / obszar sieci / miasta w EPSG:2180) → `org.matsim.kutno.CreateKutnoNetwork` (SupersonicOsmNetworkReader 2026.0, WGS84 → EPSG:2180, filtr obszaru, tylko `car`, NetworkCleaner) → `pipeline/validate_network.py`.
Wejście: `data/raw/osm/lodzkie-261015.osm.pbf` (Geofabrik, dane do 2026-10-15T20:21Z, sha256 w `data/manifest.csv`). Konwersja trwa 7 s.

| Test | Wynik |
|---|---|
| Granica gminy z BREC | 41 rejonów, 33,55 km² (zgodne z oficjalną powierzchnią Kutna); centrum (E 524 805, N 485 023) leży w poligonie, osie E,N OK |
| Powiat | 117 rejonów, 13 kodów TERYT (Krośniewice i Żychlin rozbite na miasto i wieś), 885,6 km² |
| Sieć | 4 453 węzły, 10 296 linków, 4 426 km; cleaner usunął 116 węzłów i 127 linków |
| Spójność | największa silnie spójna składowa = **100%** węzłów |
| Trasy testowe | centrum, 4 skrajne węzły (N/S/E/W), 5 losowych (seed 42): **90/90 par osiągalnych** |
| Atrybuty | 0 linków z capacity/freespeed/length/lanes ≤ 0; 0 linków bez `car` |
| Węzły poza obszarem | 69, max 4,0 km (końce odcinków do najbliższego skrzyżowania; tolerancja 5 km) |

Mapa: `reports/f2_network.png` (kolor = freespeed).

## Prędkości: problem (pierwsza wersja) → decyzja D13

Linki bez tagu `maxspeed` dostają domyślne prędkości Supersonic (wartości VSP, kalibrowane na miasta niemieckie):

| typ | km | mediana freespeed |
|---|---|---|
| unclassified | 2 109 | 15 km/h |
| residential | 1 105 | 15 km/h |
| tertiary | 840 | 25 km/h |
| secondary | 117 | 45 km/h |
| primary | 204 | 60 km/h |
| motorway | 18 | 140 km/h |

Ok. 3 000 km dróg lokalnych, w większości wiejskich (limit ustawowy 90 km/h poza terenem zabudowanym), jedzie 15–25 km/h. Skutek: centrum → skraj powiatu 52–65 min. Bez korekty czasy dojazdu przyjeżdżających byłyby kilkukrotnie zawyżone.

**Po D13** (tag `maxspeed` > limit ustawowy × 0,8; `config/network_speeds.properties`):

| źródło prędkości | km |
|---|---|
| domyślne poza miastem (90 → 72 km/h) | 2 729 |
| residential (50 → 40) | 996 |
| tag OSM `maxspeed` | 632 |
| domyślne w mieście (50 → 40) | 44 |
| living_street / motorway | 21 / 4 |

Czas z centrum Kutna do skrajnych węzłów (N/S/E/W): **28 / 22 / 35 / 33 min** (wcześniej 63 / 54 / 65 / 52). Topologia bez zmian, 90/90 tras. Regresja smoke po przebudowie: ok.
Capacity: domyślne Supersonic (np. 600 poj./h/pas dla dróg lokalnych). Bez weryfikacji, istotne dopiero przy analizie kongestii.

## Ograniczenia
- PBF obejmuje tylko woj. łódzkie. Bufor 3 km po stronie mazowieckiej nie zawiera dróg spoza województwa, więc wjazdy kończą się na granicy województwa.
