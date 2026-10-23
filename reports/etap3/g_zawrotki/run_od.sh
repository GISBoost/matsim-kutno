#!/bin/bash
# R9.1 (D29), krok 2: estymacja O-D tła na runach pracujących z nowymi domami (3 seedy MATSim, jak R7b). p1/p2 = seed punktów 1/2 (jak R7b).
# Uruchamiać z katalogu projektu po run_r1.sh. Wyjście: scenarios/kutno/demand/background_od_r91[_p1|_p2]_{lcv,heavy}_gpr.csv
L=reports/etap3/g_zawrotki/r91; R="output/g3r91r1_25pct_s4711 output/g3r91r1_25pct_s1 output/g3r91r1_25pct_s2"
est() { # cls tag [seed=N]
  uv run python -W ignore pipeline/background_od.py 30 $2 $R cls=$1 drop=10045,91892,91119 $3 > $L/od_$2.log 2>&1
}
for c in lcv heavy; do
  est $c r91_${c}_gpr & est $c r91_p1_${c}_gpr seed=1 & est $c r91_p2_${c}_gpr seed=2 &
  wait
done
echo done > $L/run_od.done
