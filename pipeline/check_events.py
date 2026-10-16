"""Liczy eventy MATSim i sprawdza, czy podróże faktycznie się odbyły.

Użycie: uv run python pipeline/check_events.py <output_events.xml[.zst|.gz]> [--expect-car-legs N]
Kod wyjścia 1, gdy departure != arrival, są eventy stuck albo liczba nóg car != N.
Uwaga: MATSim 2026 dokleja do nóg car teleportowane nogi walk (dojście/odejście),
więc liczymy departure per legMode, a oczekiwanie dotyczy tylko car.
"""
import argparse
import collections
import gzip
import json
import sys

import zstandard
from lxml import etree


def open_events(path):
    if path.endswith(".zst"):
        return zstandard.ZstdDecompressor().stream_reader(open(path, "rb"))
    if path.endswith(".gz"):
        return gzip.open(path, "rb")
    return open(path, "rb")


def count(path):
    types = collections.Counter()
    dep, arr = collections.Counter(), collections.Counter()
    modes = collections.Counter()
    with open_events(path) as f:
        for _, el in etree.iterparse(f, tag="event"):
            t = el.get("type")
            types[t] += 1
            if t == "departure":
                dep[el.get("person")] += 1
                modes[el.get("legMode")] += 1
            elif t == "arrival":
                arr[el.get("person")] += 1
            el.clear()
    return types, dep, arr, modes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("events")
    ap.add_argument("--expect-car-legs", type=int)
    a = ap.parse_args()
    types, dep, arr, modes = count(a.events)
    stuck = sum(n for t, n in types.items() if "stuck" in t.lower())  # "stuck" i "stuckAndAbort" (MATSim 2026)
    result = {
        "events_file": a.events,
        "event_types": dict(types),
        "persons_departing": len(dep),
        "departures": sum(dep.values()),
        "departures_by_mode": dict(modes),
        "arrivals": sum(arr.values()),
        "stuck": stuck,
        "persons_dep_ne_arr": sorted(p for p in dep.keys() | arr.keys() if dep[p] != arr[p]),
    }
    ok = result["departures"] == result["arrivals"] and stuck == 0 and not result["persons_dep_ne_arr"]
    if a.expect_car_legs is not None:
        ok = ok and modes["car"] == a.expect_car_legs == types.get("vehicle enters traffic", 0)
    result["ok"] = ok
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
