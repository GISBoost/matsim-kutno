#!/bin/bash
# G1/R8 (D26): sieć R8 (R7b + DisallowedNextLinks) w scenarios/kutno/network.xml.gz, te same plany i macierze co R7b, 25% x 5 (ustawienia jak R7b). Z katalogu projektu.
J="/c/Program Files/java25/bin/java"; L=reports/etap3/g1_skrzyzowania
run() { # nazwa seed plany
  "$J" -Xmx3g -jar matsim/matsim-example-project-0.0.1-SNAPSHOT.jar run --config scenarios/kutno/config_25pct.xml \
    --output output/$1 --config:global.randomSeed=$2 --config:global.numberOfThreads=2 --config:qsim.numberOfThreads=2 --iterations 100 \
    --config:plans.inputPlansFile=plans_$3_25pct.xml.gz --config:qsim.vehiclesSource=fromVehiclesData --config:vehicles.vehiclesFile=plans_$3_25pct_vehicles.xml.gz \
    > $L/run_$1.log 2>&1 &
}
run g1r8_25pct_s4711 4711 g5r7b; run g1r8_25pct_s1 1 g5r7b; run g1r8_25pct_s2 2 g5r7b
run g1r8p1_25pct_s4711 4711 g5r7bp1; run g1r8p2_25pct_s4711 4711 g5r7bp2; wait
echo done > $L/run_g1.done
