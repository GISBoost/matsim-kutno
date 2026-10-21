#!/bin/bash
# R7b krok 1: model pracujących (plany R1 bez tła i ciężkich, plans_g5r1k1_25pct) na sieci R7 = wejście estymacji O-D (jak output/g5r1k1_* dla R6b)
J="/c/Program Files/java25/bin/java"; L=reports/etap2/g5_predkosci_d23/r7b
for s in 4711 1 2; do
  "$J" -Xmx3g -jar matsim/matsim-example-project-0.0.1-SNAPSHOT.jar run --config scenarios/kutno/config_25pct_r7.xml --output output/g5r7r1_25pct_s$s \
    --config:global.randomSeed=$s --config:global.numberOfThreads=2 --config:qsim.numberOfThreads=2 --iterations 100 \
    --config:plans.inputPlansFile=plans_g5r1k1_25pct.xml.gz --config:qsim.vehiclesSource=defaultVehicle > $L/run_r1_s$s.log 2>&1 &
done
wait; echo done > $L/run_r1.done
