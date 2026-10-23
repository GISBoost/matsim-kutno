#!/bin/bash
# G3/R9 (D28), krok 5: analiza 5 runów R9 (te same skrypty co w workflow G1b): check_events, GPR lekkie i ciężkie, opóźnienia, kolejki.
# Wyjście: output/<run>/analiza/. Zgodność liczby nóg z planami sprawdza g3_porownanie.py.
for r in g3r9_25pct_s4711 g3r9_25pct_s1 g3r9_25pct_s2 g3r9p1_25pct_s4711 g3r9p2_25pct_s4711; do
  O=output/$r; mkdir -p $O/analiza
  uv run python pipeline/check_events.py $O/output_events.xml.zst > $O/analiza/check_events.json 2>&1
  for c in lcv heavy; do uv run python -W ignore pipeline/g5_baseline.py $O/analiza/gpr_$c $O cls=$c > $O/analiza/gpr_$c.log 2>&1; done
  uv run python -W ignore pipeline/link_delay.py $O $O/analiza/delay > $O/analiza/delay.log 2>&1
  uv run python -W ignore pipeline/queues.py $O $O/analiza/queues > $O/analiza/queues.log 2>&1
done
echo done > reports/etap3/g3_domy/r9/run_analiza.done
