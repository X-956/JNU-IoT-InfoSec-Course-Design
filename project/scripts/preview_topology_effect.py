# -*- coding: utf-8 -*-
"""拓扑层预分析：随机失效 vs 自适应介数定向攻击的最大连通分量。

注意：这是纯图论计算，不是 OMNeT++ 数据包级仿真，不能当作投递率结果。
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import generate_topology as gt  # noqa: E402

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

G = gt.build_graph()
N = G.number_of_nodes()
critical = json.loads((ROOT / "configs" / "critical_nodes.json").read_text("utf-8"))
order = critical["adaptive_targeted_order"]
SEEDS = 50
KS = list(range(0, 17))


def lcc_size(h: nx.Graph) -> int:
    if h.number_of_nodes() == 0:
        return 0
    return len(max(nx.connected_components(h), key=len))


targeted = []
for k in KS:
    h = G.copy()
    h.remove_nodes_from(order[:k])
    targeted.append(lcc_size(h))

random_mean, random_ci = [], []
for k in KS:
    vals = []
    for seed in range(SEEDS):
        h = G.copy()
        rnd = random.Random(seed)
        h.remove_nodes_from(rnd.sample(list(G.nodes), k))
        vals.append(lcc_size(h))
    arr = np.array(vals, dtype=float)
    random_mean.append(arr.mean())
    random_ci.append(1.96 * arr.std(ddof=1) / np.sqrt(len(arr)) if len(arr) > 1 else 0)

fig, ax = plt.subplots(figsize=(8.6, 4.8), dpi=200)
ax.errorbar(KS, random_mean, yerr=random_ci, fmt="o-", color="#2f6fb0",
            capsize=3, lw=1.8, ms=4, label="随机失效（均值 ±95% CI）")
ax.plot(KS, targeted, "s--", color="#c62828", lw=2.0, ms=4,
        label="自适应介数定向攻击")
ax.axhline(N, color="#999999", lw=0.8, ls=":")
ax.set_xlabel("失效节点数 k")
ax.set_ylabel("最大连通分量节点数")
ax.set_title("拓扑层预分析：最大连通分量随失效节点数变化\n（纯图论计算，不是数据包级仿真）",
             fontsize=11)
ax.set_xticks(KS)
ax.set_ylim(0, N + 1)
ax.grid(alpha=0.25)
ax.legend(fontsize=9, loc="lower left")
for k in (6, 8):
    ax.annotate(f"k={k}: 定向 {targeted[k]} / 随机 {random_mean[k]:.1f}",
                xy=(k, targeted[k]), xytext=(k + 1.0, targeted[k] + 3.5),
                fontsize=8, color="#333333",
                arrowprops=dict(arrowstyle="->", color="#666666", lw=0.8))
fig.tight_layout()
out = ROOT / "figures" / "topology_lcc_preview.png"
fig.savefig(out, bbox_inches="tight", facecolor="white")
print(out)
print("k, random_mean, random_ci, targeted")
for k in KS:
    print(f"{k},{random_mean[k]:.2f},{random_ci[k]:.2f},{targeted[k]}")
