# -*- coding: utf-8 -*-
"""Generate batch.ini for k=2..12 targeted/random sweeps."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
critical = json.loads((ROOT / "configs" / "critical_nodes.json").read_text("utf-8"))
order = critical["adaptive_targeted_order"]

header = """[General]
network = IslNetwork
ned-path = ../src
sim-time-limit = 70s
cmdenv-express-mode = true
cmdenv-status-frequency = 10s
output-scalar-file = ../results/sweep/${configname}-${runnumber}.sca
**.vector-recording = false
**.scalar-recording = true
**.numSats = 24
**.sendInterval = 1s
**.startTime = 1s
**.stopTime = 60s
**.destId = -1
**.failureEnabled = true
**.failureTime = 40s
**.detectionDelay = 2s
**.recoveryEnabled = true
"""

lines = [header]
for k in range(2, 13):
    nodes = ",".join(str(x) for x in order[:k])
    lines.append(f"""
[Config TargetK{k}]
description = "targeted adaptive betweenness, k={k}"
**.failureMode = "list"
**.failureNodes = "{nodes}"
""")
    lines.append(f"""
[Config RandomK{k}]
description = "random failure, k={k}"
**.failureMode = "random"
**.failureK = {k}
**.failureNodes = ""
""")

out = ROOT / "project" / "simulations" / "batch.ini"
out.write_text("\n".join(lines), encoding="utf-8")
print(out)
print("configs:", 2 * 11)
