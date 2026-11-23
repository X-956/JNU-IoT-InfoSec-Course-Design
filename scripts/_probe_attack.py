import random
import sys

import networkx as nx

sys.path.insert(0, r"U:\3-2\信息安全\课程设计\scripts")
import generate_topology as gt

g = gt.build_graph()
h = g.copy()
order = []
while h.number_of_nodes():
    b = nx.betweenness_centrality(h, normalized=True)
    n = max(h.nodes, key=lambda x: (b[x], h.degree(x), -x))
    order.append((n, round(b[n], 4), h.degree(n)))
    h.remove_node(n)
print("adaptive:", order[:12])

for k in [4, 6, 8, 10]:
    h = g.copy()
    h.remove_nodes_from([x[0] for x in order[:k]])
    lcc = max(nx.connected_components(h), key=len)
    print("k", k, "adaptive LCC", len(lcc), "components",
          nx.number_connected_components(h))
    vals = []
    for seed in range(20):
        hh = g.copy()
        rnd = random.Random(seed)
        hh.remove_nodes_from(rnd.sample(list(g.nodes), k))
        vals.append(len(max(nx.connected_components(hh), key=len)))
    print("   random mean LCC", sum(vals) / len(vals))
