"""Additional figures for the SavePoint TFG memoria: evaluation pipeline, catalogue data
flow, iteration calendar and nDCG@10 chart. Reuses the drawing helpers of
generate_diagrams.py. Run `python generate_extra.py` from this directory."""
import datetime as dt

import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from generate_diagrams import (ACCENT_FILL, BOX_EDGE, BOX_FILL, INK, MUTED, arrow, bottom, box, left, right,
                               save, top)

WARM = "#fff3e0"


# ---------------------------------------------------------------------------
# Evaluation pipeline
# ---------------------------------------------------------------------------
def diagram_pipeline_evaluacion():
    fig, ax = plt.subplots(figsize=(9.8, 4.6))
    ax.set_xlim(0, 15.4)
    ax.set_ylim(0, 7.4)
    ax.axis("off")

    w, h, gap = 3.2, 1.7, 0.7
    xs = [0.3 + i * (w + gap) for i in range(4)]
    y_a, y_b = 4.9, 1.2

    a1 = box(ax, (xs[0], y_a), w, h, "Corpus gobernado\ny snapshots congelados", fontsize=9)
    a2 = box(ax, (xs[1], y_a), w, h, "Usuarios sintéticos\ny sus bibliotecas", fontsize=9)
    a3 = box(ax, (xs[2], y_a), w, h, "Partición de usuarios\ntrain, validación y test", fontsize=9)
    a4 = box(ax, (xs[3], y_a), w, h, "Retención de positivos\npor usuario", fontsize=9)
    for p, q in ((a1, a2), (a2, a3), (a3, a4)):
        arrow(ax, right(p), left(q))

    # Second row flows right to left so that the whole pipeline reads as a snake.
    b1 = box(ax, (xs[3], y_b), w, h, "Conjunto de candidatas\ncomún a todos", fontsize=9, fill=ACCENT_FILL)
    b2 = box(ax, (xs[2], y_b), w, h, "Dieciséis algoritmos\n(un proceso cada uno)", fontsize=9, fill=WARM)
    b3 = box(ax, (xs[1], y_b), w, h, "Métricas y contrastes\nestadísticos", fontsize=9, fill=WARM)
    b4 = box(ax, (xs[0], y_b), w, h, "Artefacto versionado\n(huellas y semillas)", fontsize=9, fill=ACCENT_FILL)
    arrow(ax, bottom(a4), top(b1))
    for p, q in ((b1, b2), (b2, b3), (b3, b4)):
        arrow(ax, left(p), right(q))

    save(fig, "pipeline-evaluacion")


# ---------------------------------------------------------------------------
# Catalogue data flow
# ---------------------------------------------------------------------------
def diagram_flujo_catalogo():
    fig, ax = plt.subplots(figsize=(9.8, 4.9))
    ax.set_xlim(0, 15.4)
    ax.set_ylim(0, 8.6)
    ax.axis("off")

    sw, sh = 4.2, 1.5
    s1 = box(ax, (0.6, 6.6), sw, sh, "Wikidata\n150 juegos, CC0", fontsize=9)
    s2 = box(ax, (5.6, 6.6), sw, sh, "IGDB, API v4\ncatálogo a escala real", fontsize=9)
    s3 = box(ax, (10.6, 6.6), sw, sh, "RAWG (opcional)\nratings de contraste", fontsize=9)

    imp = box(ax, (0.4, 4.3), 14.7, 1.4,
              "Importación mediante comandos de gestión, fuera de línea e idempotentes", fontsize=9, fill=WARM)
    for s in (s1, s2, s3):
        arrow(ax, bottom(s), (s[0] + s[2] / 2, 5.7))

    w, h, gap = 2.5, 1.7, 0.55
    xs = [0.4 + i * (w + gap) for i in range(5)]
    c = [box(ax, (xs[0], 1.4), w, h, "Catálogo en\nPostgreSQL\ny procedencia", fontsize=8.8),
         box(ax, (xs[1], 1.4), w, h, "Gobierno del\ncorpus (versión\ny plataformas)", fontsize=8.8, fill=ACCENT_FILL),
         box(ax, (xs[2], 1.4), w, h, "Snapshots de\nvaloraciones\n(solo inserción)", fontsize=8.8, fill=ACCENT_FILL),
         box(ax, (xs[3], 1.4), w, h, "Vectores de\nrasgos (caché\nversionada)", fontsize=8.8, fill=ACCENT_FILL),
         box(ax, (xs[4], 1.4), w, h, "Laboratorio de\nevaluación", fontsize=8.8, fill=WARM)]
    arrow(ax, (xs[0] + w / 2, 4.3), (xs[0] + w / 2, 3.1))
    for p, q in zip(c, c[1:]):
        arrow(ax, right(p), left(q))

    save(fig, "flujo-catalogo")


# ---------------------------------------------------------------------------
# Iteration calendar
# ---------------------------------------------------------------------------
def diagram_calendario():
    d = dt.date
    # Real dates from 4 September (repository evidence); the preliminary study
    # starts in early August (approximate).
    iters = [
        ("Iteración 1", "Estudio previo y pruebas (inicio aprox.)", d(2026, 8, 4), d(2026, 9, 3)),
        ("Iteración 2", "Demostración y catálogo a escala real", d(2026, 9, 4), d(2026, 9, 6)),
        ("Iteración 3", "Contrato de evaluación", d(2026, 9, 7), d(2026, 9, 8)),
        ("Iteración 4", "Recomendadores y resultados", d(2026, 9, 9), d(2026, 9, 12)),
        ("Iteración 5", "Flujos, amistades y endurecimiento", d(2026, 9, 13), d(2026, 9, 14)),
        ("Iteración 6", "Memoria y despliegue final", d(2026, 9, 15), d(2026, 10, 4)),
    ]
    # (label, day, vertical stagger of the label)
    miles = [("H0", d(2026, 8, 4), 0.0), ("H1", d(2026, 9, 5), 0.0), ("H2", d(2026, 9, 6), 0.3),
             ("H3", d(2026, 9, 8), 0.0), ("H4 y H5", d(2026, 9, 12), 0.3), ("H6", d(2026, 9, 14), 0.0),
             ("H7", d(2026, 10, 4), 0.0)]

    fig, ax = plt.subplots(figsize=(9.8, 4.2))
    n = len(iters)
    for i, (name, what, a, b) in enumerate(iters):
        y = n - i
        ax.barh(y, (b - a).days + 1, left=mdates.date2num(a), height=0.55, color=ACCENT_FILL,
                edgecolor=BOX_EDGE, linewidth=1.2, zorder=2)
        if i == n - 1:
            ax.text(mdates.date2num(a) - 1.0, y, what, va="center", ha="right", fontsize=8, color=INK, zorder=3)
        else:
            ax.text(mdates.date2num(b) + 1.5, y, what, va="center", ha="left", fontsize=8, color=INK, zorder=3)
    ax.set_yticks(range(1, n + 1))
    ax.set_yticklabels([it[0] for it in reversed(iters)], fontsize=9)
    ym = n + 0.95
    for lab, day, stagger in miles:
        x = mdates.date2num(day)
        ax.plot([x], [ym], marker="D", color=BOX_EDGE, markersize=6, zorder=3, clip_on=False)
        ax.text(x, ym + 0.32 + stagger, lab, ha="center", va="bottom", fontsize=8.2,
                fontweight="bold", color=MUTED)
    ax.set_ylim(0.4, n + 1.0)
    ax.set_xlim(mdates.date2num(d(2026, 8, 1)), mdates.date2num(d(2026, 10, 7)))
    ax.xaxis_date()
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    months = {8: "ago", 9: "sep", 10: "oct"}
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: months.get(mdates.num2date(v).month, "")))
    ax.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=0))
    ax.grid(axis="x", which="major", color="#c9ced9", linewidth=0.8, zorder=0)
    ax.tick_params(axis="x", labelsize=9)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(axis="y", length=0)
    save(fig, "calendario-iteraciones")


# ---------------------------------------------------------------------------
# nDCG@10 per algorithm
# ---------------------------------------------------------------------------
def chart_ndcg():
    data = [
        ("random-v1", 0.00000, "Baseline"),
        ("popularity-v1", 0.00340, "Baseline"),
        ("content-cbf-weighted-v1", 0.17245, "Contenido"),
        ("content-cbf-multiplicative-v1", 0.08558, "Contenido"),
        ("content-cbf-twostage-v1", 0.11724, "Contenido"),
        ("content-cbf-neg-v1", 0.11778, "Contenido"),
        ("content-cbf-weighted-pop-v1", 0.15181, "Contenido y popularidad"),
        ("content-cbf-multiplicative-pop-v1", 0.08517, "Contenido y popularidad"),
        ("content-cbf-twostage-pop-v1", 0.11410, "Contenido y popularidad"),
        ("content-cbf-neg-pop-v1", 0.09936, "Contenido y popularidad"),
        ("recency-v1", 0.00594, "Contenido y novedad"),
        ("content-cbf-mmr-v1", 0.13888, "Contenido y diversidad"),
        ("content-cbf-mmr-pop-v1", 0.13824, "Contenido y diversidad"),
        ("cf-user-knn-v1", 0.02098, "Colaborativo"),
        ("hybrid-weighted-cf-v1", 0.16989, "Híbrido"),
        ("hybrid-mmr-v1", 0.15913, "Híbrido"),
    ]
    colors = {"Baseline": "#9aa3b8", "Contenido": "#4c6fbf", "Contenido y popularidad": "#8fb0e6",
              "Contenido y novedad": "#e0963a", "Contenido y diversidad": "#8b5fbf",
              "Colaborativo": "#c4553f", "Híbrido": "#4a9a6a"}
    published = {"content-cbf-weighted-v1", "content-cbf-mmr-pop-v1", "recency-v1"}
    data = sorted(data, key=lambda r: r[1])

    fig, ax = plt.subplots(figsize=(9.0, 5.6))
    for i, (name, v, fam) in enumerate(data):
        ax.barh(i, v, color=colors[fam], edgecolor=INK if name in published else "none",
                linewidth=1.8 if name in published else 0, height=0.72, zorder=2)
        ax.text(v + 0.003, i, f"{v:.3f}".replace(".", ","), va="center", fontsize=8, color=INK)
    ax.set_yticks(range(len(data)))
    ax.set_yticklabels([r[0] for r in data], fontsize=8, family="monospace")
    ax.set_xlim(0, 0.20)
    ax.set_xlabel("nDCG@10", fontsize=9)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.3f}".replace(".", ",")))
    ax.grid(axis="x", color="#d7dbe4", linewidth=0.8, zorder=0)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    handles = [mpatches.Patch(color=c, label=f) for f, c in colors.items()]
    handles.append(mpatches.Patch(facecolor="white", edgecolor=INK, linewidth=1.8, label="Publicada en la aplicación"))
    ax.legend(handles=handles, loc="lower right", fontsize=8, frameon=False)
    save(fig, "ndcg-algoritmos")


if __name__ == "__main__":
    diagram_calendario()
    print("done")
