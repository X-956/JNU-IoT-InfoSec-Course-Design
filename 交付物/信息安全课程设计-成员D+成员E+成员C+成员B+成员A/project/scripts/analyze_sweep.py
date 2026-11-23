# -*- coding: utf-8 -*-
"""Aggregate and plot the k=2..12 targeted/random sweep."""
from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

SCALAR_RE = re.compile(r"^scalar\s+(\S+)\s+(\S+)\s+([-\d.eE+]+)\s*$")
NAME_RE = re.compile(r"^(Target|Random)K(\d+)-")


def parse(path: Path) -> dict:
    sent = received = 0
    pdr_after = lcc = None
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
        elif name == "pdrAfterFailure":
            pdr_after = v
        elif name == "lccAfterFailure":
            lcc = int(v)
    return {
        "sent": sent,
        "received": received,
        "pdr": 100.0 * received / sent if sent else 0.0,
        "pdr_after": pdr_after,
        "lcc": lcc,
    }


def agg(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return float("nan"), float("nan")
    return mean(vals), stdev(vals) if len(vals) > 1 else 0.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--csv", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    groups = defaultdict(list)
    for path in sorted(Path(args.dir).glob("*.sca")):
        m = NAME_RE.match(path.name)
        if not m:
            continue
        mode, k = m.group(1), int(m.group(2))
        groups[(mode, k)].append(parse(path))

    rows = []
    if not groups:
        ap.error("No sweep .sca files found in input directory")
    for (mode, k), rs in sorted(groups.items(), key=lambda x: (x[0][1], x[0][0])):
        pdr_m, pdr_s = agg([r["pdr"] for r in rs])
        after_m, after_s = agg([r["pdr_after"] for r in rs])
        lcc_m, lcc_s = agg([r["lcc"] for r in rs])
        rows.append({
            "mode": mode, "k": k, "n": len(rs),
            "pdr_mean": round(pdr_m, 4), "pdr_sd": round(pdr_s, 4),
            "pdr_after_mean": round(after_m, 4), "pdr_after_sd": round(after_s, 4),
            "lcc_mean": round(lcc_m, 4), "lcc_sd": round(lcc_s, 4),
        })

    with open(args.csv, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.2), dpi=200)
    colors = {"Random": "#2f6fb0", "Target": "#c62828"}
    labels = {"Random": "随机失效", "Target": "定向攻击（自适应介数）"}
    for ax, metric, title in [
        (axes[0], "pdr_mean", "全时段投递率"),
        (axes[1], "pdr_after_mean", "失效后投递率"),
        (axes[2], "lcc_mean", "失效后最大连通分量"),
    ]:
        for mode in ("Random", "Target"):
            sub = [r for r in rows if r["mode"] == mode]
            x = [r["k"] for r in sub]
            y = [r[metric] for r in sub]
            sd = [r[metric.replace("_mean", "_sd")] for r in sub]
            ci = [s for s in sd]
            ax.errorbar(x, y, yerr=ci, fmt="o-", capsize=3, lw=1.8, ms=4,
                        color=colors[mode], label=labels[mode])
        ax.set_xlabel("失效节点数 k")
        ax.set_title(title)
        ax.set_xticks(range(2, 13))
        ax.grid(alpha=0.25)
        if metric == "lcc_mean":
            ax.set_ylim(0, 25)
        else:
            ax.set_ylim(0, 105)
        ax.legend(fontsize=8)
    fig.suptitle("24 节点星间网络：k=2…12 失效扫描（每点 20 seeds，恢复开启）\n"
                 "OMNeT++ 6.4.0 数据包级仿真，误差棒为样本标准差 SD", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(args.out, bbox_inches="tight", facecolor="white")
    print(args.out)
    print(f"wrote {args.csv} ({len(rows)} groups)")


if __name__ == "__main__":
    main()
