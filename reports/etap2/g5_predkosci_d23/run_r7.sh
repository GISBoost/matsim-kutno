#!/bin/bash
# R7 (D23): 25% x 5, te same plany i macierze co R6, sieć network_d23.xml.gz. Uruchamiać z katalogu projektu (worktree d23).
J="/c/Program Files/java25/bin/java"; L=reports/etap2/g5_predkosci_d23
run() { # nazwa seed [plany]
  "$J" -Xmx3g -jar matsim/matsim-example-project-0.0.1-SNAPSHOT.jar run --config scenarios/kutno/config_25pct_r7.xml \
    --output output/$1 --config:global.randomSeed=$2 --config:global.numberOfThreads=2 --config:qsim.numberOfThreads=2 --iterations 100 \
    ${3:+--config:plans.inputPlansFile=plans_$3_25pct.xml.gz --config:qsim.vehiclesSource=fromVehiclesData --config:vehicles.vehiclesFile=plans_$3_25pct_vehicles.xml.gz} \
    > $L/run_$1.log 2>&1 &
}
run g5r7_25pct_s4711 4711; run g5r7_25pct_s1 1; run g5r7_25pct_s2 2
run g5r7p1_25pct_s4711 4711 g5r6p1; run g5r7p2_25pct_s4711 4711 g5r6p2; wait
echo done > $L/run_r7.done
