"""Renders the real link graph of the SavePoint Obsidian vault (ideas-vault/),
in the visual style of Obsidian's own graph view, as a figure for the TFG
memoria. Parses actual [[wikilinks]] between actual notes: no fabricated data.
Run from anywhere; deps are `matplotlib` and `networkx`
(`pip install matplotlib networkx`). Re-run after the vault changes to refresh
figures/obsidian-vault-graph.pdf.
"""
import os
import re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT = os.path.normpath(os.path.join(OUT_DIR, "..", "..", "ideas-vault"))

LINK_RE = re.compile(r"\[\[([^\]|#]+)")

FOLDER_COLOR = {
    "ADR": "#e07a5f",
    "Conceptos": "#81a4cd",
    "Fases": "#8fbf8f",
    "Requisitos": "#d4b86a",
    "Mapas": "#b98fd0",
    "root": "#9aa3b8",
}
FOLDER_LABEL = {
    "ADR": "ADR",
    "Conceptos": "Conceptos",
    "Fases": "Fases",
    "Requisitos": "Requisitos",
    "Mapas": "Mapas",
    "root": "Índice",
}

notes = {}  # name -> folder
for dirpath, dirnames, filenames in os.walk(VAULT):
    dirnames[:] = [d for d in dirnames if not d.startswith(".")]
    for fn in filenames:
        if not fn.endswith(".md"):
            continue
        name = fn[:-3]
        rel = os.path.relpath(dirpath, VAULT)
        folder = "root" if rel == "." else rel.split(os.sep)[0]
        notes[name] = folder

G = nx.Graph()
for name, folder in notes.items():
    G.add_node(name, folder=folder)

name_lower = {n.lower(): n for n in notes}

for dirpath, dirnames, filenames in os.walk(VAULT):
    dirnames[:] = [d for d in dirnames if not d.startswith(".")]
    for fn in filenames:
        if not fn.endswith(".md"):
            continue
        src = fn[:-3]
        with open(os.path.join(dirpath, fn), encoding="utf-8") as f:
            text = f.read()
        for m in LINK_RE.finditer(text):
            target = m.group(1).strip()
            tgt_key = target.lower()
            if tgt_key in name_lower:
                tgt = name_lower[tgt_key]
                if tgt != src:
                    G.add_edge(src, tgt)

# Keep only the main connected component: a handful of phase notes link only
# among themselves and would otherwise stretch the layout into mostly empty
# space, the same reason Obsidian lets you filter orphans out of the view.
components = sorted(nx.connected_components(G), key=len, reverse=True)
main_component = components[0]
dropped = G.number_of_nodes() - len(main_component)
G = G.subgraph(main_component).copy()

print(f"notes: {len(notes)}, in main component: {G.number_of_nodes()}, edges: {G.number_of_edges()}, dropped: {dropped}")

pos = nx.spring_layout(G, k=2.6 / (G.number_of_nodes() ** 0.5), iterations=300, seed=7)

degrees = dict(G.degree())
max_deg = max(degrees.values()) if degrees else 1

fig, ax = plt.subplots(figsize=(9.5, 8.6))
fig.patch.set_facecolor("#1b1d21")
ax.set_facecolor("#1b1d21")

for u, v in G.edges():
    x1, y1 = pos[u]
    x2, y2 = pos[v]
    ax.plot([x1, x2], [y1, y2], color="#4a4d55", linewidth=0.6, alpha=0.55, zorder=1)

for folder in FOLDER_COLOR:
    xs, ys, sizes = [], [], []
    for n in G.nodes():
        if G.nodes[n]["folder"] == folder:
            xs.append(pos[n][0])
            ys.append(pos[n][1])
            sizes.append(18 + 55 * (degrees[n] / max_deg))
    if xs:
        ax.scatter(xs, ys, s=sizes, color=FOLDER_COLOR[folder], zorder=2,
                   edgecolors="#1b1d21", linewidths=0.4, label=FOLDER_LABEL[folder])

# No inline text labels: Obsidian's own graph view is label-free by default
# at this density too, and 130 candidate labels would just collide. The top
# hub notes are named in the figure caption instead.
top_hubs = sorted(degrees.items(), key=lambda kv: kv[1], reverse=True)[:6]

ax.set_xticks([])
ax.set_yticks([])
for spine in ax.spines.values():
    spine.set_visible(False)

legend = ax.legend(loc="lower center", fontsize=8.5, frameon=False, labelcolor="#d8dae0",
                    markerscale=1.2, ncol=6, bbox_to_anchor=(0.5, -0.06))

fig.savefig(os.path.join(OUT_DIR, "obsidian-vault-graph.pdf"), bbox_inches="tight",
            pad_inches=0.15, facecolor=fig.get_facecolor())
fig.savefig(os.path.join(OUT_DIR, "obsidian-vault-graph.png"), bbox_inches="tight",
            pad_inches=0.15, dpi=200, facecolor=fig.get_facecolor())
print("saved")
print("top hubs:", ", ".join(n for n, d in top_hubs))
