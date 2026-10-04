"""Generates the structural diagrams for the SavePoint TFG memoria (architecture,
domain model, use cases, deployment flow, GSD cycle). Outputs .pdf for LaTeX
\\includegraphics into this same directory. Pure matplotlib, no external
diagramming tool needed: run `python generate_diagrams.py` from anywhere,
dependencies are just `matplotlib` (`pip install matplotlib`).
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
from matplotlib.path import Path
import matplotlib.patches as mpatches
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

INK = "#1c1f26"
BOX_EDGE = "#2b3140"
BOX_FILL = "#f4f6fa"
ACCENT_FILL = "#e4e9f5"
MUTED = "#5c6270"

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["text.color"] = INK


def box(ax, xy, w, h, text, fontsize=10, fill=BOX_FILL, edge=BOX_EDGE, lw=1.4, boxstyle="round,pad=0.02,rounding_size=0.08"):
    x, y = xy
    patch = FancyBboxPatch((x, y), w, h, boxstyle=boxstyle, linewidth=lw,
                            edgecolor=edge, facecolor=fill, zorder=2)
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
             fontsize=fontsize, color=INK, zorder=3, linespacing=1.4)
    return (x, y, w, h)


def arrow(ax, p1, p2, style="-|>", lw=1.3, color=BOX_EDGE, connectionstyle="arc3,rad=0.0", dashed=False):
    fa = FancyArrowPatch(p1, p2, arrowstyle=style, mutation_scale=14,
                          linewidth=lw, color=color, zorder=2.5,
                          connectionstyle=connectionstyle,
                          linestyle="dashed" if dashed else "solid")
    ax.add_patch(fa)


def top(b):
    x, y, w, h = b
    return (x + w / 2, y + h)


def bottom(b):
    x, y, w, h = b
    return (x + w / 2, y)


def left(b):
    x, y, w, h = b
    return (x, y + h / 2)


def right(b):
    x, y, w, h = b
    return (x + w, y + h / 2)


def save(fig, name):
    fig.savefig(os.path.join(OUT_DIR, name + ".pdf"), bbox_inches="tight", pad_inches=0.12)
    fig.savefig(os.path.join(OUT_DIR, name + ".png"), bbox_inches="tight", pad_inches=0.12, dpi=200)
    plt.close(fig)


# ---------------------------------------------------------------------------
# 1. Architecture diagram
# ---------------------------------------------------------------------------
def diagram_arquitectura():
    fig, ax = plt.subplots(figsize=(7.2, 6.4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 11)
    ax.axis("off")

    b_browser = box(ax, (1.2, 9.1), 4.4, 1.0, "Navegador", fontsize=11)
    b_next = box(ax, (0.6, 7.0), 5.6, 1.4,
                 "Next.js\nApp Router · renderizado en servidor\nreescritura same-origin hacia la API",
                 fontsize=9.5)
    b_django = box(ax, (0.6, 3.9), 5.6, 2.2, "", fontsize=9.5, fill=ACCENT_FILL)
    ax.text(3.4, 5.75, "Django + Django REST Framework", ha="center", va="center",
            fontsize=10, fontweight="bold")
    mods = ["catalogue", "library", "accounts", "recommendations"]
    mod_widths = [1.0, 0.9, 1.0, 1.55]
    mx = 0.8
    for m, mw in zip(mods, mod_widths):
        box(ax, (mx, 4.2), mw, 0.85, m, fontsize=7.2, fill="#ffffff")
        mx += mw + 0.08
    b_db = box(ax, (1.2, 1.6), 4.4, 1.1, "PostgreSQL", fontsize=11)

    b_ingest = box(ax, (7.0, 3.9), 2.7, 2.2,
                    "Comandos de gestión\n(ingesta offline)\n\nIGDB · Wikidata",
                    fontsize=9.5, fill="#fff3e0")
    b_eval = box(ax, (7.0, 1.6), 2.7, 1.6,
                  "Runner de evaluación\n(offline, fuera de la\npetición HTTP)",
                  fontsize=9, fill="#fff3e0")

    arrow(ax, bottom(b_browser), top(b_next))
    arrow(ax, bottom(b_next), top(b_django))
    arrow(ax, bottom(b_django), top(b_db))
    arrow(ax, left(b_ingest), right(b_django), connectionstyle="arc3,rad=0.0")
    arrow(ax, left(b_eval), right(b_db), connectionstyle="arc3,rad=-0.15")

    save(fig, "arquitectura")


# ---------------------------------------------------------------------------
# 2. Domain model (simplified ER diagram)
# ---------------------------------------------------------------------------
def diagram_modelo_dominio():
    fig, ax = plt.subplots(figsize=(9.6, 7.0))
    ax.set_xlim(0, 14.3)
    ax.set_ylim(0.6, 10.8)
    ax.axis("off")

    def cluster(xy, w, h, title, title_xy):
        ax.add_patch(mpatches.FancyBboxPatch(xy, w, h, boxstyle="round,pad=0.05,rounding_size=0.15",
                                              linewidth=1.0, edgecolor="#9aa3b8", facecolor="#f7f8fb", zorder=0))
        ax.text(title_xy[0], title_xy[1], title, fontsize=10.5, fontweight="bold", color=MUTED)

    cluster((0.25, 6.1), 4.5, 4.5, "Cuentas y amistades", (0.5, 10.2))
    cluster((0.25, 0.8), 4.5, 4.5, "Biblioteca personal", (0.5, 0.95))
    cluster((5.0, 4.7), 9.1, 5.9, "Catálogo", (5.25, 10.2))
    cluster((6.9, 0.8), 7.2, 3.5, "Evaluación (laboratorio)", (7.15, 0.95))

    fs = 8.3
    # Cuentas
    b_friend = box(ax, (0.45, 9.0), 1.95, 0.75, "Friendship", fontsize=fs - 0.8)
    b_request = box(ax, (0.45, 7.95), 1.95, 0.75, "FriendshipRequest", fontsize=fs - 1.6)
    b_block = box(ax, (0.45, 6.9), 1.95, 0.75, "Block", fontsize=fs - 0.8)
    b_user = box(ax, (3.1, 7.45), 1.45, 0.9, "User", fontsize=fs, fill=ACCENT_FILL)
    # Biblioteca personal
    b_entry = box(ax, (0.45, 3.2), 1.9, 0.9, "LibraryEntry", fontsize=fs, fill=ACCENT_FILL)
    b_status = box(ax, (0.5, 1.5), 2.1, 0.8, "StatusTransition", fontsize=fs - 0.5)
    b_copy = box(ax, (2.75, 3.2), 1.85, 0.9, "OwnedCopy", fontsize=fs)
    # Catalogo
    b_alias = box(ax, (5.2, 8.9), 2.2, 0.9, "GameAlias", fontsize=fs)
    b_genre = box(ax, (7.7, 8.9), 2.0, 0.9, "Genre", fontsize=fs)
    b_related = box(ax, (10.0, 8.9), 1.9, 0.9, "RelatedContent", fontsize=fs - 0.8)
    b_platform = box(ax, (12.1, 8.9), 1.8, 0.9, "Platform", fontsize=fs)
    b_source = box(ax, (5.2, 7.0), 2.1, 1.0, "SourceRecord", fontsize=fs)
    b_work = box(ax, (7.7, 7.0), 2.2, 1.0, "GameWork", fontsize=fs, fill=ACCENT_FILL)
    b_release = box(ax, (11.8, 7.0), 2.0, 1.0, "GameRelease", fontsize=fs)
    b_edition = box(ax, (11.8, 5.1), 2.0, 0.8, "Edition", fontsize=fs)
    # Evaluacion
    b_feature = box(ax, (7.3, 2.5), 2.9, 0.9, "WorkFeatureVector", fontsize=fs - 0.3, fill="#fff3e0")
    b_snapshot = box(ax, (10.7, 2.5), 3.1, 0.9, "CorpusRatingSnapshot", fontsize=fs - 0.5, fill="#fff3e0")

    # Convention: every arrow leaves the entity that holds the foreign key and
    # points at the entity it references; the double-headed arrow is many-to-many.
    arrow(ax, right(b_friend), (3.1, 8.2))
    arrow(ax, right(b_request), (3.1, 7.9))
    arrow(ax, right(b_block), (3.1, 7.6))
    arrow(ax, (1.2, 4.1), (3.4, 7.45))
    arrow(ax, (3.7, 4.1), (4.1, 7.45))
    arrow(ax, top(b_status), bottom(b_entry))
    arrow(ax, (2.0, 4.1), (7.95, 7.0))

    arrow(ax, bottom(b_alias), (8.0, 8.0))
    arrow(ax, right(b_source), left(b_work))
    arrow(ax, (8.8, 8.0), (8.7, 8.9), style="<|-|>")
    arrow(ax, bottom(b_related), (9.6, 8.0))
    arrow(ax, left(b_release), right(b_work))
    arrow(ax, top(b_release), bottom(b_platform))
    arrow(ax, top(b_edition), bottom(b_release))

    arrow(ax, (4.6, 3.85), (12.2, 7.0), connectionstyle="arc3,rad=0.0")
    arrow(ax, (4.6, 3.5), left(b_edition), dashed=True)

    arrow(ax, top(b_feature), (8.2, 7.0))
    arrow(ax, top(b_snapshot), (9.4, 7.0))

    save(fig, "modelo-dominio")


# ---------------------------------------------------------------------------
# 3. Use case diagram
# ---------------------------------------------------------------------------
def stick_actor(ax, x, y, label, scale=1.0):
    head = Circle((x, y + 0.9 * scale), 0.22 * scale, facecolor=BOX_FILL, edgecolor=BOX_EDGE, linewidth=1.4, zorder=3)
    ax.add_patch(head)
    ax.plot([x, x], [y + 0.68 * scale, y + 0.1 * scale], color=BOX_EDGE, linewidth=1.6, zorder=3)
    ax.plot([x - 0.32 * scale, x + 0.32 * scale], [y + 0.5 * scale, y + 0.5 * scale], color=BOX_EDGE, linewidth=1.6, zorder=3)
    ax.plot([x, x - 0.28 * scale], [y + 0.1 * scale, y - 0.35 * scale], color=BOX_EDGE, linewidth=1.6, zorder=3)
    ax.plot([x, x + 0.28 * scale], [y + 0.1 * scale, y - 0.35 * scale], color=BOX_EDGE, linewidth=1.6, zorder=3)
    ax.text(x, y - 0.62 * scale, label, ha="center", va="top", fontsize=9.5, fontweight="bold")


def ellipse_uc(ax, xy, w, h, text, fontsize=8.3):
    x, y = xy
    e = mpatches.Ellipse((x, y), w, h, facecolor=BOX_FILL, edgecolor=BOX_EDGE, linewidth=1.3, zorder=2)
    ax.add_patch(e)
    ax.text(x, y, text, ha="center", va="center", fontsize=fontsize, zorder=3, linespacing=1.3)
    return (x, y, w, h)


def _ellipse_edge(uc, toward):
    """Point on the boundary of the use-case ellipse `uc` facing `toward`."""
    cx, cy, w, h = uc
    dx, dy = toward[0] - cx, toward[1] - cy
    t = 1.0 / (((dx / (w / 2)) ** 2 + (dy / (h / 2)) ** 2) ** 0.5)
    return (cx + dx * t, cy + dy * t)


def _association(ax, actor_xy, uc):
    p = _ellipse_edge(uc, actor_xy)
    ax.plot([actor_xy[0], p[0]], [actor_xy[1], p[1]], color=BOX_EDGE, linewidth=1.2, zorder=1.5)


def diagram_casos_uso():
    fig, ax = plt.subplots(figsize=(9.8, 6.4))
    ax.set_xlim(0, 14.8)
    ax.set_ylim(0, 9.5)
    ax.axis("off")

    boundary = mpatches.FancyBboxPatch((2.1, 0.35), 10.7, 8.8, boxstyle="round,pad=0.02,rounding_size=0.12",
                                        linewidth=1.4, edgecolor=BOX_EDGE, facecolor="none", zorder=1)
    ax.add_patch(boundary)
    ax.text(7.45, 8.75, "SavePoint", ha="center", fontsize=10.5, fontweight="bold", color=MUTED)

    # Actors: the visitor on the left, the registered user on the right.
    visitor = (1.0, 4.6)
    user = (13.8, 5.3)
    stick_actor(ax, visitor[0], visitor[1] - 0.2, "Visitante")
    stick_actor(ax, user[0], user[1] - 0.2, "Persona\nusuaria")

    w, h, radius = 3.1, 0.86, 4.9
    fs = 7.5

    def on_arc(actor, dy, side):
        """x so that the use case sits on a circle around the actor: every association
        line is then radial and never crosses a neighbouring use case."""
        dx = (radius ** 2 - dy ** 2) ** 0.5
        return actor[0] + side * dx

    visitor_ucs = [
        ("CU-1 Buscar un juego\npor título", 7.9),
        ("CU-2 Consultar ficha\ny procedencia", 6.35),
        ("CU-3 Filtrar y ordenar\nel catálogo", 4.8),
        ("CU-4 Ver recomendación\npor popularidad", 3.25),
        ("CU-5 Registrarse como\npersona usuaria", 1.7),
    ]
    for text, y in visitor_ucs:
        x = on_arc((visitor[0], visitor[1]), y - visitor[1], +1)
        uc = ellipse_uc(ax, (x, y), w, h, text, fontsize=fs)
        _association(ax, (visitor[0] + 0.3, visitor[1] + 0.3), uc)

    user_ucs = [
        ("CU-6 Iniciar y cerrar\nsesión", 8.4),
        ("CU-7 Cambiar estado\nde biblioteca", 7.4),
        ("CU-8 Valorar un juego", 6.4),
        ("CU-9 Registrar copias\nen propiedad", 5.4),
        ("CU-10 Ver recomendación\npor afinidad", 4.4),
        ("CU-11 Gestionar amistades\ny bloqueos", 3.4),
        ("CU-12 Ver la colección\nde un amigo", 2.4),
        ("CU-13 Comentar un juego\n(visible para amigos)", 1.4),
    ]
    for text, y in user_ucs:
        x = on_arc((user[0], user[1]), y - user[1], -1)
        uc = ellipse_uc(ax, (x, y), w, h, text, fontsize=fs)
        _association(ax, (user[0] - 0.3, user[1] + 0.3), uc)

    save(fig, "casos-uso")


# ---------------------------------------------------------------------------
# 4b. Deployment topology and boot-chain flow
# ---------------------------------------------------------------------------
def diagram_despliegue_flujo():
    fig, ax = plt.subplots(figsize=(9.6, 5.8))
    ax.set_xlim(0, 14.8)
    ax.set_ylim(0, 8.9)
    ax.axis("off")

    # Row 1: the public topology, left to right.
    y1, h1 = 6.9, 1.5
    b_browser = box(ax, (0.3, y1), 2.4, h1, "Navegador\n(HTTPS)", fontsize=9.5)
    b_vercel = box(ax, (3.6, y1), 3.3, h1,
                   "Vercel Hobby\nbuild nativo de Next.js\nreescritura same-origin", fontsize=8.6)
    b_render = box(ax, (7.8, y1), 3.3, h1,
                   "Render Free\nimagen de la API\n(Django + DRF)", fontsize=8.6, fill=ACCENT_FILL)
    b_neon = box(ax, (12.0, y1), 2.5, h1, "Neon Free\nPostgreSQL\ngestionado", fontsize=8.6)
    arrow(ax, right(b_browser), left(b_vercel))
    arrow(ax, right(b_vercel), left(b_render))
    arrow(ax, right(b_render), left(b_neon))

    # Row 2: the boot chain of the API on Render, inside its own group.
    ax.add_patch(mpatches.FancyBboxPatch((0.3, 2.5), 14.2, 3.4, boxstyle="round,pad=0.05,rounding_size=0.15",
                                          linewidth=1.0, edgecolor="#9aa3b8", facecolor="#f7f8fb", zorder=0))
    ax.text(0.6, 5.45, "Cadena de arranque de la API en Render",
            fontsize=8.6, fontweight="bold", color=MUTED)
    steps = ["migrate", "import\ncatalogue", "gunicorn\n(health OK)"]
    sx, sw, gap = 1.6, 3.2, 1.3
    boxes = []
    for st in steps:
        boxes.append(box(ax, (sx, 3.1), sw, 1.4, st, fontsize=8.6, fill="#fff3e0"))
        sx += sw + gap
    for i in range(len(boxes) - 1):
        arrow(ax, right(boxes[i]), left(boxes[i + 1]))
    arrow(ax, bottom(b_render), (b_render[0] + b_render[2] / 2, 5.9))

    b_health = box(ax, (10.5, 0.3), 3.4, 1.1, "/health/ devuelve\nel commit desplegado", fontsize=8.6)
    arrow(ax, bottom(boxes[-1]), top(b_health))

    save(fig, "despliegue-flujo")


# ---------------------------------------------------------------------------
# 4. GSD cycle diagram
# ---------------------------------------------------------------------------
def diagram_ciclo_gsd():
    import math
    fig, ax = plt.subplots(figsize=(8.2, 8.2))
    ax.set_xlim(-7.2, 7.2)
    ax.set_ylim(-7.2, 7.2)
    ax.set_aspect("equal")
    ax.axis("off")

    steps = [
        ("Idea", "propuesta inicial"),
        ("Hoja de ruta", "ROADMAP.md"),
        ("Discutir", "decisiones fijadas"),
        ("Contrato de\ninterfaz", "UI-SPEC (si aplica)"),
        ("Planificar", "PLAN.md"),
        ("Ejecutar", "commits + SUMMARY.md"),
        ("Verificar", "VERIFICATION.md"),
        ("Revisar", "informe de revisión"),
    ]
    n = len(steps)
    r = 4.6
    w, h = 2.0, 1.05
    label_r = r + (w / 2) + 1.15
    for i, (title, artefact) in enumerate(steps):
        ang = math.pi / 2 - i * (2 * math.pi / n)
        x, y = r * math.cos(ang), r * math.sin(ang)
        b = box(ax, (x - w / 2, y - h / 2), w, h, title, fontsize=9.3)
        lx, ly = label_r * math.cos(ang), label_r * math.sin(ang)
        ax.text(lx, ly, artefact, ha="center", va="center", fontsize=7.3, color=MUTED, style="italic")

    for i in range(n):
        ang1 = math.pi / 2 - i * (2 * math.pi / n)
        ang2 = math.pi / 2 - (i + 1) * (2 * math.pi / n)
        x1, y1 = r * math.cos(ang1), r * math.sin(ang1)
        x2, y2 = r * math.cos(ang2), r * math.sin(ang2)
        d1 = (x2 - x1, y2 - y1)
        norm = (d1[0] ** 2 + d1[1] ** 2) ** 0.5
        ux, uy = d1[0] / norm, d1[1] / norm
        p1 = (x1 + ux * 1.05, y1 + uy * 1.05)
        p2 = (x2 - ux * 1.05, y2 - uy * 1.05)
        arrow(ax, p1, p2, connectionstyle=f"arc3,rad=-0.28")

    ax.text(0, 0, "Ciclo GSD\npor incremento", ha="center", va="center", fontsize=11, fontweight="bold")
    ax.text(0, -1.0, "cada paso deja un\nartefacto escrito en\n.planning/", ha="center", va="center",
            fontsize=8, color=MUTED, style="italic")

    save(fig, "ciclo-gsd")


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    diagram_arquitectura()
    diagram_modelo_dominio()
    diagram_casos_uso()
    diagram_despliegue_flujo()
    diagram_ciclo_gsd()
    print("done")
