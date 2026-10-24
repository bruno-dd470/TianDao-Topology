#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dual graph of pentads (Merkabah)
Black & white publication version
Single circular labels
"""

import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from itertools import combinations
from matplotlib.lines import Line2D

# =========================
# Merkabah data
# =========================

merkabah_triplets = {
    'A': ('P1','P2','P4'), 'B': ('P1','P3','P5'), 'C': ('P2','P3','P6'),
    'D': ('P4','P5','N2'), 'E': ('P5','P6','N3'), 'F': ('P1','P6','N4'),
    'G': ('P2','P5','N6'), 'H': ('P3','P4','N6'), 'I': ('P1','N2','N6'),
    'J': ('P1','N3','N5'), 'K': ('P2','N3','N5'), 'L': ('P3','N2','N4'),
    'M': ('P4','N1','N3'), 'N': ('P4','N5','N6'), 'O': ('P5','N1','N4'),
    'P': ('P6','N1','N2'), 'Q': ('P2','N1','N4'), 'R': ('P3','N1','N5'),
    'S': ('P6','N5','N6'), 'T': ('N2','N3','N4')
}

# =========================
# Graph construction
# =========================

all_pentads = sorted({
    p for trip in merkabah_triplets.values()
    for p in trip
})

G = nx.Graph()
G.add_nodes_from(all_pentads)

for trip in merkabah_triplets.values():
    for u, v in combinations(trip, 2):
        G.add_edge(u, v)

# =========================
# Cycle detection
# =========================

cycles_5 = []

for cycle in nx.simple_cycles(G, length_bound=5):
    if len(cycle) == 5:
        s = frozenset(cycle)
        if s not in cycles_5:
            cycles_5.append(s)

cycles_P = [
    c for c in cycles_5
    if all(x.startswith('P') for x in c)
]

cycles_N = [
    c for c in cycles_5
    if all(x.startswith('N') for x in c)
]

good_pairs = []

for c1 in cycles_P:
    for c2 in cycles_N:
        if c1.isdisjoint(c2):
            remaining = set(all_pentads) - c1 - c2
            if remaining == {'P4', 'N4'}:
                good_pairs.append((c1, c2))

belt_P_set, belt_N_set = good_pairs[0]

# =========================
# Cycle ordering
# =========================

def get_cycle_order(subgraph, nodes_set):
    sub = subgraph.subgraph(nodes_set)
    for cycle in nx.simple_cycles(sub, length_bound=5):
        if len(cycle) == 5:
            return cycle
    return list(nodes_set)

order_P = get_cycle_order(G, belt_P_set)
order_N = get_cycle_order(G, belt_N_set)

# =========================
# Circular layout
# =========================

def layout_circle(order, center, radius):

    angles = np.linspace(
        0,
        2*np.pi,
        len(order),
        endpoint=False
    )

    return {
        n: (
            center[0] + radius*np.cos(a),
            center[1] + radius*np.sin(a)
        )
        for n, a in zip(order, angles)
    }

pos = {}

pos.update(
    layout_circle(
        order_P,
        center=(-2, 0),
        radius=1.5
    )
)

pos.update(
    layout_circle(
        order_N,
        center=(2, 0),
        radius=1.5
    )
)

pos['P4'] = (0, 0.7)
pos['N4'] = (0, -0.7)

# =========================
# Edge classification
# =========================

edges_P_cycle = set(
    (
        order_P[i],
        order_P[(i+1) % 5]
    )
    for i in range(5)
)

edges_N_cycle = set(
    (
        order_N[i],
        order_N[(i+1) % 5]
    )
    for i in range(5)
)

edges_P_internal = []
edges_N_internal = []
edges_cross = []

for u, v in G.edges():

    if (u, v) in edges_P_cycle or (v, u) in edges_P_cycle:
        continue

    if (u, v) in edges_N_cycle or (v, u) in edges_N_cycle:
        continue

    u_in_P = u in belt_P_set
    v_in_P = v in belt_P_set

    u_in_N = u in belt_N_set
    v_in_N = v in belt_N_set

    if u_in_P and v_in_P:
        edges_P_internal.append((u, v))

    elif u_in_N and v_in_N:
        edges_N_internal.append((u, v))

    else:
        edges_cross.append((u, v))

# =========================
# DRAW
# =========================

plt.figure(figsize=(12, 9))

# Main belts

nx.draw_networkx_edges(
    G,
    pos,
    edgelist=list(edges_P_cycle),
    edge_color='black',
    width=3,
    style='solid'
)

nx.draw_networkx_edges(
    G,
    pos,
    edgelist=list(edges_N_cycle),
    edge_color='black',
    width=3,
    style='dashed'
)

# Internal edges

nx.draw_networkx_edges(
    G,
    pos,
    edgelist=edges_P_internal,
    edge_color='black',
    width=1.5,
    style='dotted'
)

nx.draw_networkx_edges(
    G,
    pos,
    edgelist=edges_N_internal,
    edge_color='black',
    width=1.5,
    style='dashdot'
)

# Cross edges

nx.draw_networkx_edges(
    G,
    pos,
    edgelist=edges_cross,
    edge_color='black',
    width=1.0,
    alpha=0.35
)

# Labels

nx.draw_networkx_labels(
    G,
    pos,
    font_size=11,
    font_weight='bold',
    font_color='black',
    bbox=dict(
        boxstyle="circle,pad=0.28",
        facecolor="white",
        edgecolor="black",
        linewidth=1.5
    )
)

# Legend (English)

legend_elements = [

    Line2D(
        [0], [0],
        color='black',
        linewidth=3,
        linestyle='solid',
        label='P belt'
    ),

    Line2D(
        [0], [0],
        color='black',
        linewidth=3,
        linestyle='dashed',
        label='N belt'
    ),

    Line2D(
        [0], [0],
        color='black',
        linewidth=1.5,
        linestyle=':',
        label='Internal P edges'
    ),

    Line2D(
        [0], [0],
        color='black',
        linewidth=1.5,
        linestyle='-.',
        label='Internal N edges'
    ),

    Line2D(
        [0], [0],
        color='black',
        linewidth=1.0,
        alpha=0.35,
        label='Cross edges'
    )
]

plt.legend(
    handles=legend_elements,
    loc='upper left',
    fontsize=10,
    frameon=True
)

plt.title(
    "Dual Graph of Pentads (Merkabah)",
    fontsize=14
)

plt.axis('equal')
plt.tight_layout()

plt.show()
