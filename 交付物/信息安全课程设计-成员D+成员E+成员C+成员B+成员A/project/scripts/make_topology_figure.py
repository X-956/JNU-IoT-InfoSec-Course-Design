# -*- coding: utf-8 -*-
"""生成 24 节点星间网络简化拓扑示意图（设计图，不是仿真截图）。"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures"
OUT.mkdir(exist_ok=True)

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

PLANES, SLOTS = 3, 8
G = nx.Graph()
pos = {}
node_plane = {}
for p in range(PLANES):
    for s in range(SLOTS):
        n = f"P{p}S{s}"
        G.add_node(n)
        pos[n] = (p * 3.2, -s * 1.0)
        node_plane[n] = p

for p in range(PLANES):
    for s in range(SLOTS):
        G.add_edge(f"P{p}S{s}", f"P{p}S{(s + 1) % SLOTS}", kind="intra")
for p in range(PLANES - 1):
    for s in range(SLOTS):
        G.add_edge(f"P{p}S{s}", f"P{p+1}S{s}", kind="inter")

original_ok = [("P0S0", "P0S1"), ("P0S3", "P0S4"),
               ("P0S4", "P1S4"), ("P1S4", "P2S4")]
broken = [("P0S1", "P0S2"), ("P0S2", "P0S3")]
alternative = [("P0S0", "P1S0"), ("P1S0", "P1S1"), ("P1S1", "P1S2"),
               ("P1S2", "P1S3"), ("P1S3", "P1S4"), ("P1S4", "P2S4")]

fig, ax = plt.subplots(figsize=(9.6, 8.2), dpi=200)
intra = [(u, v) for u, v, d in G.edges(data=True) if d["kind"] == "intra"]
inter = [(u, v) for u, v, d in G.edges(data=True) if d["kind"] == "inter"]
nx.draw_networkx_edges(G, pos, edgelist=intra, ax=ax, edge_color="#9db7d5",
                       width=1.4, alpha=0.9)
nx.draw_networkx_edges(G, pos, edgelist=inter, ax=ax, edge_color="#d9a45b",
                       width=1.1, alpha=0.75, style="dashed")

colors = ["#2f6fb0", "#2f9e6f", "#8a5fb0"]
nx.draw_networkx_nodes(G, pos, ax=ax, node_size=560,
                       node_color=[colors[node_plane[n]] for n in G.nodes],
                       edgecolors="white", linewidths=1.2)
nx.draw_networkx_labels(G, pos, ax=ax, font_size=7.2, font_color="white",
                        font_weight="bold")

nx.draw_networkx_edges(G, pos, edgelist=original_ok, ax=ax, edge_color="#1f9d55",
                       width=3.0, alpha=0.95)
nx.draw_networkx_edges(G, pos, edgelist=broken, ax=ax, edge_color="#c62828",
                       width=2.2, alpha=0.9, style=(0, (2, 2)))
nx.draw_networkx_edges(G, pos, edgelist=alternative, ax=ax, edge_color="#e07b00",
                       width=3.0, alpha=0.95, style=(0, (4, 2)))

ax.scatter([pos["P0S2"][0]], [pos["P0S2"][1]], s=760, facecolors="none",
           edgecolors="#c62828", linewidths=2.6, zorder=5)
ax.text(pos["P0S2"][0] + 0.18, pos["P0S2"][1] + 0.28, "P0S2 失效",
        color="#c62828", fontsize=9, fontweight="bold")
ax.text(pos["P0S0"][0] - 0.52, pos["P0S0"][1] + 0.30, "源",
        color="#1f9d55", fontsize=9, fontweight="bold")
ax.text(pos["P2S4"][0] + 0.22, pos["P2S4"][1] + 0.30, "目的",
        color="#1f9d55", fontsize=9, fontweight="bold")

ax.text(0.02, 0.985, "24 节点星间网络简化拓扑（3 轨道面 × 8 星）",
        transform=ax.transAxes, fontsize=15, fontweight="bold", va="top")
ax.text(0.02, 0.94,
        "实线：同轨道面链路；虚线：异轨道面链路；绿线：原路径；红点线：中断链路；橙虚线：备用路径",
        transform=ax.transAxes, fontsize=8.5, color="#444444", va="top")

handles = [
    plt.Line2D([], [], color="#1f9d55", lw=3, label="正常路径"),
    plt.Line2D([], [], color="#e07b00", lw=3, ls="--", label="恢复路径"),
    plt.Line2D([], [], color="#c62828", lw=2, ls=":", label="中断链路"),
    plt.Line2D([], [], color="#9db7d5", lw=2, label="同面链路"),
    plt.Line2D([], [], color="#d9a45b", lw=2, ls="--", label="异面链路"),
]
ax.legend(handles=handles, loc="lower right", fontsize=8, frameon=False, ncol=2)
ax.set_axis_off()
ax.set_xlim(-0.6, 7.4)
ax.set_ylim(-7.9, 1.3)
ax.set_aspect("equal")
fig.tight_layout()
out = OUT / "topology_design.png"
fig.savefig(out, bbox_inches="tight", facecolor="white")
print(out)
