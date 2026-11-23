# -*- coding: utf-8 -*-
"""生成 24 节点星间网络拓扑、关键节点排名和 OMNeT++ NED 网络文件。

这是设计/配置脚本，不运行 OMNeT++ 仿真。输出：
  configs/nodes.csv
  configs/links.csv
  configs/critical_nodes.json
  configs/IslNetwork.ned
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs"
CONFIG.mkdir(exist_ok=True)

PLANES = 3
SLOTS = 8
N = PLANES * SLOTS
INTRA_DELAY_MS = 70.0
INTER_DELAY_MS = 120.0
BANDWIDTH_MBPS = 10.0


def node_id(plane: int, slot: int) -> int:
    return plane * SLOTS + slot


def build_graph() -> nx.Graph:
    g = nx.Graph()
    for p in range(PLANES):
        for s in range(SLOTS):
            g.add_node(node_id(p, s), plane=p, slot=s)
    for p in range(PLANES):
        for s in range(SLOTS):
            a, b = node_id(p, s), node_id(p, (s + 1) % SLOTS)
            g.add_edge(a, b, kind="intra", delay_ms=INTRA_DELAY_MS,
                       bandwidth_mbps=BANDWIDTH_MBPS)
    for p in range(PLANES - 1):
        for s in range(SLOTS):
            a, b = node_id(p, s), node_id(p + 1, s)
            g.add_edge(a, b, kind="inter", delay_ms=INTER_DELAY_MS,
                       bandwidth_mbps=BANDWIDTH_MBPS)
    return g


def write_nodes(g: nx.Graph) -> None:
    with open(CONFIG / "nodes.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["node_id", "name", "plane", "slot", "x", "y"])
        for n, d in sorted(g.nodes(data=True)):
            w.writerow([n, f"P{d['plane']}S{d['slot']}", d["plane"], d["slot"],
                        d["plane"] * 320 + 100, d["slot"] * 110 + 100])


def write_links(g: nx.Graph) -> None:
    with open(CONFIG / "links.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["src", "dst", "kind", "delay_ms", "bandwidth_mbps"])
        for u, v, d in sorted(g.edges(data=True)):
            w.writerow([u, v, d["kind"], d["delay_ms"], d["bandwidth_mbps"]])


def adaptive_targeted_order(g: nx.Graph) -> list[tuple[int, float, int]]:
    """顺序攻击：每次在剩余图上重算介数，移除当前介数最大的节点。

    返回 (node, betweenness_at_selection, degree_at_selection)。介数相同
    时优先高度数，再按节点编号，保证结果可复现。
    """
    h = g.copy()
    order: list[tuple[int, float, int]] = []
    while h.number_of_nodes():
        b = nx.betweenness_centrality(h, normalized=True, weight=None)
        n = max(h.nodes, key=lambda x: (b[x], h.degree(x), -x))
        order.append((n, round(b[n], 6), h.degree(n)))
        h.remove_node(n)
    return order


def write_critical(g: nx.Graph) -> dict:
    betweenness = nx.betweenness_centrality(g, normalized=True, weight=None)
    degree = dict(g.degree())
    ranking = sorted(g.nodes, key=lambda n: (-betweenness[n], -degree[n], n))
    adaptive = adaptive_targeted_order(g)
    data = {
        "n": g.number_of_nodes(),
        "edges": g.number_of_edges(),
        "average_degree": 2 * g.number_of_edges() / g.number_of_nodes(),
        "diameter_hops": nx.diameter(g),
        "average_shortest_path_hops": nx.average_shortest_path_length(g),
        "betweenness": {str(n): round(betweenness[n], 6) for n in g.nodes},
        "degree": {str(n): degree[n] for n in g.nodes},
        "targeted_order": ranking,
        "targeted_top": ranking[:12],
        "adaptive_targeted_order": [x[0] for x in adaptive],
        "adaptive_targeted_detail": [
            {"node": n, "betweenness_at_selection": b, "degree_at_selection": d}
            for n, b, d in adaptive
        ],
    }
    with open(CONFIG / "critical_nodes.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data


def write_ned(g: nx.Graph) -> None:
    lines = [
        "// 由 scripts/generate_topology.py 自动生成；不要手工改连接。",
        "package isl;",
        "",
        "network IslNetwork",
        "{",
        "    submodules:",
        f"        sat[{N}]: Satellite;",
        "    connections:",
    ]
    seen = set()
    for u, v, d in sorted(g.edges(data=True)):
        key = (min(u, v), max(u, v))
        if key in seen:
            continue
        seen.add(key)
        delay = "70ms" if d["kind"] == "intra" else "120ms"
        lines.append(
            f"        sat[{u}].isl++ <--> IdealChannel {{ delay = {delay}; }} "
            f"<--> sat[{v}].isl++;"
        )
    lines += ["}", ""]
    (CONFIG / "IslNetwork.ned").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    g = build_graph()
    write_nodes(g)
    write_links(g)
    data = write_critical(g)
    write_ned(g)
    print(f"nodes={data['n']} edges={data['edges']} "
          f"avg_degree={data['average_degree']:.2f} "
          f"diameter={data['diameter_hops']} "
          f"avg_hops={data['average_shortest_path_hops']:.3f}")
    print("static betweenness top 8:")
    for n in data["targeted_top"][:8]:
        print(f"  node {n:2d}  betweenness={data['betweenness'][str(n)]:.4f}  "
              f"degree={data['degree'][str(n)]}")
    print("adaptive targeted order (first 12):",
          data["adaptive_targeted_order"][:12])
    print(f"wrote {CONFIG}")


if __name__ == "__main__":
    main()
