# F0 — środowisko MATSim (2026-10-16)

**Status: ZALICZONA**

| Element | Wartość |
|---|---|
| Java | Temurin OpenJDK 25.0.1 (`C:\Program Files\java25`), `JAVA_HOME` ustawiany w poleceniu |
| Maven | wrapper 3.3.2 → Maven 3.9.8 (`matsim/mvnw.cmd`), bez instalacji globalnej |
| MATSim | 2026.0 (parent pom), `matsim-example-project` @ `74d23af` (2026-04-20), skopiowany bez historii upstream |
| Python | uv 0.11.29, `.venv` Py 3.12; zależności przypięte w `uv.lock` |
| Build | `mvnw.cmd -B package -DskipTests` → BUILD SUCCESS, 3:47 min (pierwszy build, z pobieraniem zależności) |
| Uber-jar | `matsim/matsim-example-project-0.0.1-SNAPSHOT.jar` (210 MB, w `.gitignore`) |

## Test: scenariusz `equil`, 1 iteracja

Polecenie: `java -Xmx10g -jar matsim-example-project-0.0.1-SNAPSHOT.jar run --config scenarios\equil\config-2026.xml --output ..\output\f0_equil --iterations 1`

- Kod wyjścia 0, czas 10 s, iteracje 0 i 1 zakończone (`reports/f0_equil_run.log`).
- `pipeline/check_events.py --expect-car-legs 201` → `ok: true` (`reports/f0_equil_events.json`): 201 nóg car, 402 walk, departure = arrival = 603, 0 stuck, liczba `vehicle enters traffic` = 201. Wartość 201 wynika z planów: 99 osób × 2 + 1 osoba × 3.

## Ustalenia (nowe gotchas)

1. **Outputy MATSim 2026 są w `.zst` (Zstandard), nie w `.xml.gz`.** Prompty z archiwum zakładały `.gz`. `check_events.py` obsługuje oba formaty.
2. **Do każdej nogi car doklejane są teleportowane nogi `walk`** (dojście/odejście). Liczba `departure` ≈ 3 × liczba podróży car, więc testy muszą liczyć per `legMode`.
3. **`java.lang.IllegalArgumentException: Unsupported class file major version 69`** w logu to **nieszkodliwe ostrzeżenie Guice** (stary ASM nie czyta numerów linii klas Java 25 i tylko gorzej formatuje komunikaty błędów). Run przebiega poprawnie, ale filtr „Exception w logu = porażka” trzeba stroić, nie ignorować w całości.
