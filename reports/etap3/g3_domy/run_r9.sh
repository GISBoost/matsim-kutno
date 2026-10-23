#!/bin/bash
# G3/R9 (D28), krok 4: 5 runów 25% x 50 it. (3 seedy MATSim na planach p0, 2 seedy planów p1, p2), sieć R8, plany plans_g3r9[p1|p2]_25pct.
J="/c/Program Files/java25/bin/java"; L=reports/etap3/g3_domy/r9
run() { # nazwa seed plany
  "$J" -Xmx3g -jar matsim/matsim-example-project-0.0.1-SNAPSHOT.jar run --config scenarios/kutno/config_25pct.xml \
    --output output/$1 --config:global.randomSeed=$2 --config:global.numberOfThreads=2 --config:qsim.numberOfThreads=2 --iterations 50 \
    --config:plans.inputPlansFile=plans_$3_25pct.xml.gz --config:qsim.vehiclesSource=fromVehiclesData --config:vehicles.vehiclesFile=plans_$3_25pct_vehicles.xml.gz \
    > $L/run_$1.log 2>&1 &
}
run g3r9_25pct_s4711 4711 g3r9; run g3r9_25pct_s1 1 g3r9; run g3r9_25pct_s2 2 g3r9
run g3r9p1_25pct_s4711 4711 g3r9p1; run g3r9p2_25pct_s4711 4711 g3r9p2; wait
echo done > $L/run_r9.done
