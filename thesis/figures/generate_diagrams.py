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

    ax.text(5.0, 0.55,
            "Flecha continua: ruta de una petición HTTP. Flechas hacia la izquierda: procesos\n"
            "fuera de la petición HTTP (importación y evaluación offline).",
            ha="center", va="center", fontsize=8, color=MUTED)

    save(fig, "arquitectura")


# ---------------------------------------------------------------------------
# 2. Domain model (simplified ER diagram)
# ---------------------------------------------------------------------------
def diagram_modelo_dominio():
    fig, ax = plt.subplots(figsize=(8.6, 6.8))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 10.5)
    ax.axis("off")

    # Cluster backgrounds
    ax.add_patch(mpatches.FancyBboxPatch((0.25, 5.1), 8.6, 5.0, boxstyle="round,pad=0.05,rounding_size=0.15",
                                          linewidth=1.0, edgecolor="#9aa3b8", facecolor="#f7f8fb", zorder=0))
    ax.text(0.55, 9.75, "Catálogo", fontsize=10.5, fontweight="bold", color=MUTED)

    ax.add_patch(mpatches.FancyBboxPatch((0.25, 2.3), 5.6, 2.5, boxstyle="round,pad=0.05,rounding_size=0.15",
                                          linewidth=1.0, edgecolor="#9aa3b8", facecolor="#f7f8fb", zorder=0))
    ax.text(0.55, 4.55, "Biblioteca personal", fontsize=10.5, fontweight="bold", color=MUTED)

    ax.add_patch(mpatches.FancyBboxPatch((9.15, 5.1), 3.6, 5.0, boxstyle="round,pad=0.05,rounding_size=0.15",
                                          linewidth=1.0, edgecolor="#9aa3b8", facecolor="#f7f8fb", zorder=0))
    ax.text(9.4, 9.75, "Cuentas", fontsize=10.5, fontweight="bold", color=MUTED)

    ax.add_patch(mpatches.FancyBboxPatch((6.15, 2.3), 6.6, 2.5, boxstyle="round,pad=0.05,rounding_size=0.15",
                                          linewidth=1.0, edgecolor="#9aa3b8", facecolor="#f7f8fb", zorder=0))
    ax.text(6.4, 4.55, "Investigación (laboratorio)", fontsize=10.5, fontweight="bold", color=MUTED)

    fs = 8.3
    b_work = box(ax, (2.7, 8.1), 2.0, 0.95, "GameWork", fontsize=fs, fill=ACCENT_FILL)
    b_genre = box(ax, (5.4, 8.1), 1.9, 0.95, "Genre", fontsize=fs)
    b_alias = box(ax, (0.55, 8.1), 1.9, 0.95, "GameAlias", fontsize=fs)
    b_source = box(ax, (0.55, 6.6), 2.0, 0.95, "SourceRecord", fontsize=fs)
    b_related = box(ax, (5.35, 6.6), 2.1, 0.95, "RelatedContent\n(DLC)", fontsize=fs - 0.3)
    b_release = box(ax, (2.7, 6.6), 2.0, 0.95, "GameRelease", fontsize=fs)
    b_edition = box(ax, (2.7, 5.3), 1.7, 0.8, "Edition", fontsize=fs)
    b_platform = box(ax, (4.7, 5.3), 1.7, 0.8, "Platform", fontsize=fs)

    b_entry = box(ax, (0.55, 3.5), 2.2, 0.95, "LibraryEntry", fontsize=fs, fill=ACCENT_FILL)
    b_status = box(ax, (0.55, 2.5), 2.2, 0.75, "StatusTransition", fontsize=fs - 0.5)
    b_copy = box(ax, (3.1, 3.5), 2.4, 0.95, "OwnedCopy", fontsize=fs)

    b_user = box(ax, (9.5, 8.1), 2.8, 0.95, "User", fontsize=fs, fill=ACCENT_FILL)
    b_anchor = box(ax, (9.5, 6.7), 2.8, 0.85, "DemoAccountAnchor", fontsize=fs - 0.5)
    b_identity = box(ax, (9.5, 5.5), 2.8, 0.85, "DemoAccountIdentity", fontsize=fs - 0.5)

    b_snapshot = box(ax, (6.4, 3.5), 2.7, 0.95, "CorpusRatingSnapshot", fontsize=fs - 0.5, fill="#fff3e0")
    b_feature = box(ax, (9.4, 3.5), 3.0, 0.95, "WorkFeatureVector", fontsize=fs, fill="#fff3e0")

    arrow(ax, right(b_work), left(b_genre), connectionstyle="arc3,rad=0.0")
    arrow(ax, left(b_work), right(b_alias))
    arrow(ax, bottom(b_work), top(b_release))
    arrow(ax, right(b_release), left(b_related))
    arrow(ax, left(b_release), right(b_source))
    arrow(ax, bottom(b_release), top(b_edition))
    arrow(ax, (b_release[0] + b_release[2], b_release[1]), top(b_platform), connectionstyle="arc3,rad=-0.1")

    arrow(ax, left(b_entry), left(b_work), connectionstyle="arc3,rad=0.55")
    arrow(ax, bottom(b_entry), top(b_status))
    arrow(ax, right(b_entry), left(b_copy))
    arrow(ax, (b_entry[0], b_entry[1] + b_entry[3] / 2), (b_user[0], b_user[1]), connectionstyle="arc3,rad=-0.2")

    arrow(ax, bottom(b_anchor), top(b_identity), connectionstyle="arc3,rad=0.0")
    arrow(ax, bottom(b_user), top(b_anchor), connectionstyle="arc3,rad=0.0")

    arrow(ax, right(b_copy), left(b_snapshot), connectionstyle="arc3,rad=0.0")
    arrow(ax, right(b_snapshot), left(b_feature))

    ax.text(6.5, 0.7,
            "IgdbImportRun y AssetAttribution (procedencia por importación y por portada) se omiten de la\n"
            "figura por espacio; ambas cuelgan de GameWork y se describen en el texto.",
            ha="center", va="center", fontsize=8, color=MUTED)

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


def diagram_casos_uso():
    fig, ax = plt.subplots(figsize=(8.8, 6.4))
    ax.set_xlim(0, 13.5)
    ax.set_ylim(0, 9.5)
    ax.axis("off")

    boundary = mpatches.FancyBboxPatch((2.6, 0.5), 10.4, 8.5, boxstyle="round,pad=0.02,rounding_size=0.12",
                                        linewidth=1.4, edgecolor=BOX_EDGE, facecolor="none", zorder=1)
    ax.add_patch(boundary)
    ax.text(7.8, 8.75, "SavePoint", fontsize=10.5, fontweight="bold", color=MUTED)

    stick_actor(ax, 1.1, 6.0, "Visitante")
    stick_actor(ax, 1.1, 2.2, "Persona\nusuaria")

    uc_visitor = [
        ("Buscar un juego\npor título", (4.6, 8.0)),
        ("Consultar ficha\ny procedencia", (7.6, 8.0)),
        ("Filtrar y ordenar\nel catálogo", (10.6, 8.0)),
        ("Ver perfil\npúblico", (4.6, 6.5)),
        ("Ver recomendación\npor popularidad", (7.6, 6.5)),
        ("Registrarse en la\nfrontera de demo", (10.6, 6.5)),
    ]
    uc_user = [
        ("Iniciar y cerrar\nsesión", (4.6, 4.3)),
        ("Cambiar estado\nde biblioteca", (7.6, 4.3)),
        ("Valorar un\njuego", (10.6, 4.3)),
        ("Registrar copias\nen propiedad", (4.6, 2.0)),
        ("Ver recomendaciones\npor afinidad", (7.6, 2.0)),
    ]

    for text, pos in uc_visitor:
        u = ellipse_uc(ax, pos, 2.55, 1.15, text)
        arrow(ax, (1.35, 6.0), (u[0] - u[2] / 2, u[1]), connectionstyle="arc3,rad=0.05")

    for text, pos in uc_user:
        u = ellipse_uc(ax, pos, 2.55, 1.15, text)
        arrow(ax, (1.35, 2.2), (u[0] - u[2] / 2, u[1]), connectionstyle="arc3,rad=-0.05")

    save(fig, "casos-uso")


# ---------------------------------------------------------------------------
# 4b. Deployment topology and boot-chain flow
# ---------------------------------------------------------------------------
def diagram_despliegue_flujo():
    fig, ax = plt.subplots(figsize=(8.4, 6.2))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 9.7)
    ax.axis("off")

    b_browser = box(ax, (5.1, 8.5), 2.8, 0.95, "Navegador (HTTPS)", fontsize=9.5)
    b_vercel = box(ax, (0.6, 6.7), 4.1, 1.5,
                    "Vercel Hobby\nbuild nativo de Next.js\nreescritura same-origin", fontsize=8.6)
    b_render = box(ax, (5.05, 6.7), 4.1, 1.5,
                    "Render Free\nimagen de la API\n(Django + DRF)",
                    fontsize=8.6, fill=ACCENT_FILL)
    b_neon = box(ax, (9.7, 6.7), 2.7, 1.5, "Neon Free\nPostgreSQL\ngestionado", fontsize=8.6)

    arrow(ax, bottom(b_browser), (b_vercel[0] + b_vercel[2] * 0.7, b_vercel[1] + b_vercel[3]),
          connectionstyle="arc3,rad=0.15")
    arrow(ax, right(b_vercel), left(b_render))
    arrow(ax, right(b_render), left(b_neon))

    chain_title_y = 5.85
    ax.text(7.1, chain_title_y, "Cadena de arranque en Render (cada paso idempotente; uno fallido detiene el arranque)",
            ha="center", va="center", fontsize=8.3, color=MUTED, style="italic")

    steps = ["migrate", "import\ncatalogue", "bootstrap\ndemo accounts", "seed\ndemo", "gunicorn\n(health OK)"]
    sx = 0.7
    sw = 2.28
    boxes = []
    for s in steps:
        b = box(ax, (sx, 4.1), sw, 1.15, s, fontsize=8.3, fill="#fff3e0")
        boxes.append(b)
        sx += sw + 0.18
    for i in range(len(boxes) - 1):
        arrow(ax, right(boxes[i]), left(boxes[i + 1]))
    arrow(ax, bottom(b_render), top(boxes[0]), connectionstyle="arc3,rad=0.0")
    arrow(ax, bottom(boxes[-1]), (boxes[-1][0] + boxes[-1][2] / 2, 2.9), connectionstyle="arc3,rad=0.0")

    b_health = box(ax, (3.6, 1.55), 5.8, 1.0, "/health/ devuelve el commit desplegado", fontsize=8.6)

    ax.text(6.5, 0.55,
            "Compose local (db + api + web) construye las mismas imágenes de api y de datos, sin depender de estos tres servicios.",
            ha="center", va="center", fontsize=8, color=MUTED)

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
