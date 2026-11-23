# -*- coding: utf-8 -*-
"""Aggregate OMNeT++ .sca scalars into a per-run CSV summary.

Usage:
  python analyze_results.py --results D:\\work\\isl-sim\\results --out summary.csv
"""
from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev

SCALAR_RE = re.compile(r"^scalar\s+(\S+)\s+(\S+)\s+([-\d.eE+]+)\s*$")
RUN_RE = re.compile(r"^run\s+(\S+)")


def parse_sca(path: Path) -> dict:
    sent = received = dropped = 0
    lcc = components = failed = None
    pdr_after = recovery = None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = SCALAR_RE.match(line)
        if not m:
            continue
        module, name, value = m.group(1), m.group(2), m.group(3)
        try:
            v = float(value)
        except ValueError:
            continue
        if name == "sent" and ".sat[" in module:
            sent += int(v)
        elif name == "received" and ".sat[" in module:
            received += int(v)
        elif name == "dropped" and ".sat[" in module:
            dropped += int(v)
        elif name == "lccAfterFailure":
            lcc = int(v)
        elif name == "componentsAfterFailure":
            components = int(v)
        elif name == "failedCount":
            failed = int(v)
        elif name == "pdrAfterFailure":
            pdr_after = v
        elif name == "recoveryTime":
            recovery = v

    pdr = 100.0 * received / sent if sent else 0.0
    return {
        "file": path.name,
        "config": path.name.split("-")[0],
        "sent": sent,
        "received": received,
        "dropped": dropped,
        "pdr": round(pdr, 4),
        "lcc": lcc,
        "components": components,
        "failed": failed,
        "pdr_after": round(pdr_after, 4) if pdr_after is not None else None,
        "recovery_time": recovery,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    rows = [parse_sca(p) for p in sorted(Path(args.results).glob("*.sca"))]
    rows = [r for r in rows if r["sent"] > 0]
    fields = ["file", "config", "sent", "received", "dropped", "pdr",
              "lcc", "components", "failed", "pdr_after", "recovery_time"]
    with open(args.out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    groups = defaultdict(list)
    for r in rows:
        groups[r["config"]].append(r)

    print(f"{'config':24s} {'n':>3s} {'PDR mean':>9s} {'PDR sd':>8s} "
          f"{'after mean':>10s} {'LCC mean':>9s} {'LCC sd':>7s}")
    for cfg, rs in sorted(groups.items()):
        pdrs = [r["pdr"] for r in rs]
        lccs = [r["lcc"] for r in rs if r["lcc"] is not None]
        after = [r["pdr_after"] for r in rs if r["pdr_after"] is not None]
        print(f"{cfg:24s} {len(rs):3d} {mean(pdrs):9.2f} "
              f"{(stdev(pdrs) if len(pdrs) > 1 else 0):8.2f} "
              f"{(mean(after) if after else float('nan')):10.2f} "
              f"{(mean(lccs) if lccs else float('nan')):9.2f} "
              f"{(stdev(lccs) if len(lccs) > 1 else 0):7.2f}")
    print(f"wrote {args.out} ({len(rows)} runs)")


if __name__ == "__main__":
    main()
