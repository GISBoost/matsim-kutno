#!/bin/bash
# G3/R9 (D28), krok 1: model pracujących na nowych domach (plans_g3r9k1_25pct, bez tła i ciężkich), 3 seedy, 25%, 50 it.
# Uruchamiać z katalogu projektu. Wejście do background_od.py.
J="/c/Program Files/java25/bin/java"; L=reports/etap3/g3_domy/r9
for s in 4711 1 2; do
  "$J" -Xmx3g -jar matsim/matsim-example-project-0.0.1-SNAPSHOT.jar run --config scenarios/kutno/config_25pct.xml \
    --output output/g3r9r1_25pct_s$s --config:global.randomSeed=$s --config:global.numberOfThreads=2 --config:qsim.numberOfThreads=2 --iterations 50 \
    --config:plans.inputPlansFile=plans_g3r9k1_25pct.xml.gz --config:qsim.vehiclesSource=defaultVehicle \
    > $L/run_r1_s$s.log 2>&1 &
done
wait
echo done > $L/run_r1.done
