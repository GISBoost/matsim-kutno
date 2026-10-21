#!/bin/bash
# R7b: sieć R7 (network.xml.gz w worktree d23 = network_d23), macierze r7b, 25% x 5 (ustawienia jak R6: 2 wątki, 3 GB, równolegle)
J="/c/Program Files/java25/bin/java"; L=reports/etap2/g5_predkosci_d23/r7b
run() { # nazwa seed plany
  "$J" -Xmx3g -jar matsim/matsim-example-project-0.0.1-SNAPSHOT.jar run --config scenarios/kutno/config_25pct_r7.xml \
    --output output/$1 --config:global.randomSeed=$2 --config:global.numberOfThreads=2 --config:qsim.numberOfThreads=2 --iterations 100 \
    --config:plans.inputPlansFile=plans_$3_25pct.xml.gz --config:qsim.vehiclesSource=fromVehiclesData --config:vehicles.vehiclesFile=plans_$3_25pct_vehicles.xml.gz \
    > $L/run_$1.log 2>&1 &
}
run g5r7b_25pct_s4711 4711 g5r7b; run g5r7b_25pct_s1 1 g5r7b; run g5r7b_25pct_s2 2 g5r7b
run g5r7bp1_25pct_s4711 4711 g5r7bp1; run g5r7bp2_25pct_s4711 4711 g5r7bp2; wait
echo done > $L/run_r7b.done
