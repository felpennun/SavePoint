r"""Entity diagrams of the SavePoint data model for the memoria (chapter "Diseño y arquitectura").

Every attribute drawn is read from the real Django models (names, types, nullability,
uniqueness, foreign keys), so a field that does not exist makes the script fail instead of
appearing in the figure. Only the most relevant attributes of each entity are shown.

Two steps, because the project environment has Django but not matplotlib:

    # 1) extract the model metadata (project environment, from apps/api)
    cd apps/api
    DJANGO_SETTINGS_MODULE=config.settings DJANGO_SECRET_KEY=doc-only DATABASE_URL=postgresql://u:p@localhost/x \
        ../../.venv/Scripts/python.exe ../../scripts/thesis-figures/generate_modelo_datos.py --dump

    # 2) draw the figures (any Python with matplotlib): PDFs into thesis/figures (add --png <folder> for previews)
    python scripts/thesis-figures/generate_modelo_datos.py

Pure matplotlib (no Graphviz).
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.normpath(os.path.join(HERE, "..", "..", "thesis", "figures"))
META_PATH = os.path.join(HERE, "models_meta.json")

TYPES = {
    "UUIDField": "uuid", "BigAutoField": "bigint", "AutoField": "int", "CharField": "varchar",
    "SlugField": "varchar", "TextField": "text", "FloatField": "float", "PositiveIntegerField": "int",
    "PositiveSmallIntegerField": "int", "PositiveBigIntegerField": "bigint", "IntegerField": "int",
    "BigIntegerField": "bigint", "BooleanField": "bool", "DateField": "date", "DateTimeField": "timestamp",
    "JSONField": "json", "BinaryField": "bytea", "DecimalField": "numeric",
}


def dump_meta() -> None:
    """Step 1 (needs Django): write name, type, key tag and nullability of every model field."""
    import django

    sys.path.insert(0, os.getcwd())  # run from apps/api so that `config` is importable
    django.setup()
    from django.apps import apps
    from django.contrib.auth import get_user_model

    meta = {}
    models = [("User", get_user_model())]
    for app in ("catalogue", "library", "accounts", "social", "recommendations"):
        models += [(f"{app}.{m.__name__}", m) for m in apps.get_app_config(app).get_models()]
    for label, m in models:
        fields = {}
        for f in m._meta.get_fields():
            if (f.auto_created and not f.concrete) or f.many_to_many:
                continue
            tag = "PK" if f.primary_key else ("FK" if f.is_relation else ("UQ" if f.unique else ""))
            type_ = TYPES[(f.related_model._meta.pk if f.is_relation else f).get_internal_type()]
            fields[f.name] = {
                "name": f.attname if f.is_relation else f.name,
                "type": type_,
                "tag": tag,
                "null": bool(getattr(f, "null", False)) and not f.primary_key,
                "one_to_one": bool(getattr(f, "one_to_one", False)),
                "target": f"{f.related_model._meta.app_label}.{f.related_model.__name__}" if f.is_relation else None,
            }
        meta[label] = fields
    with open(META_PATH, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=1, sort_keys=True)
    print("model metadata written to", META_PATH, f"({len(meta)} models)")


if "--dump" in sys.argv:
    dump_meta()
    sys.exit(0)

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

with open(META_PATH, encoding="utf-8") as fh:
    META = json.load(fh)

INK = "#1c1f26"
EDGE = "#2b3140"
HEAD = "#e4e9f5"
HEAD_REF = "#eef0f4"
BODY = "#fbfcfe"
MUTED = "#5c6270"
TAG = "#3b4a7a"
FS = 7.7  # attribute font size (pt); the axes fill the figure, so one data unit is one inch
FS_HEAD = 8.9
CH = 0.6 * FS / 72  # width of one monospace character (in)
LH = 0.148  # line height (in)
HEAD_H = 0.24
PAD = 0.06
PAGE_W = 6.3  # text width of the memoria in inches: figures are drawn at 1:1 so the fonts keep their size

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["text.color"] = INK


def describe(label: str, field_name: str):
    """(display name, type, tag) for one attribute of a real model (read from the extracted metadata)."""
    f = META[label][field_name]
    return f["name"] + ("?" if f["null"] else ""), f["type"], f["tag"]


class Entity:
    def __init__(self, key, title, label, x, y, fields=(), w=1.9, ref=False, subtitle=(), extra=None, min_h=0.0):
        self.key, self.title, self.ref, self.subtitle = key, title, ref, list(subtitle)
        self.label = label
        self.x, self.y_top, self.w = x, y, w
        self.rows = [describe(label, f) for f in fields] if label else []
        self.rows += list(extra or [])
        self.h = max(min_h, HEAD_H + PAD * 1.4 + LH * len(self.rows) + 0.115 * len(self.subtitle) + (0.03 if self.subtitle else 0))

    left = property(lambda self: self.x)
    right = property(lambda self: self.x + self.w)
    top = property(lambda self: self.y_top)
    bottom = property(lambda self: self.y_top - self.h)
    cx = property(lambda self: self.x + self.w / 2)
    cy = property(lambda self: self.y_top - self.h / 2)

    def draw(self, ax):
        ax.add_patch(mpatches.Rectangle((self.x, self.bottom), self.w, self.h, fc=BODY, ec=EDGE, lw=0.9, zorder=2))
        ax.add_patch(mpatches.Rectangle((self.x, self.top - HEAD_H), self.w, HEAD_H,
                                        fc=HEAD_REF if self.ref else HEAD, ec=EDGE, lw=0.9, zorder=3))
        head_fs = min(FS_HEAD, (self.w - 0.12) * 72 / (len(self.title) * 0.80))
        ax.text(self.cx, self.top - HEAD_H / 2, self.title, ha="center", va="center", fontsize=head_fs,
                fontweight="bold", zorder=4)
        y = self.top - HEAD_H - PAD * 0.6
        for line in self.subtitle:
            ax.text(self.cx, y - 0.01, line, ha="center", va="top", fontsize=FS - 0.9, color=MUTED, style="italic", zorder=4)
            y -= 0.115
        if self.subtitle:
            y -= 0.03
        for name, type_, tag in self.rows:
            yy = y - LH / 2
            ax.text(self.x + 0.05, yy, tag, ha="left", va="center", fontsize=FS - 0.6, color=TAG,
                    fontweight="bold", family="DejaVu Sans Mono", zorder=4)
            # a long attribute name shrinks a little instead of running into its type
            room = self.w - 0.24 - 3 * CH - len(type_) * 0.6 * (FS - 1.0) / 72
            name_fs = min(FS, room * 72 / (len(name) * 0.6))
            ax.text(self.x + 0.05 + 3 * CH, yy, name, ha="left", va="center", fontsize=name_fs,
                    family="DejaVu Sans Mono", zorder=4)
            ax.text(self.right - 0.05, yy, type_, ha="right", va="center", fontsize=FS - 1.0, color=MUTED,
                    family="DejaVu Sans Mono", zorder=4)
            y -= LH


class Diagram:
    """Entities plus connectors. Connection points on the same side of a box are spread automatically."""

    def __init__(self, name, height, w=1.9, lane_margin=0.2):
        self.name, self.H, self.w, self.lane_margin = name, height, w, lane_margin
        self.xs = [0.0, (PAGE_W - w) / 2, PAGE_W - w]  # three columns, equal gaps
        self.ents: dict[str, Entity] = {}
        self.edges = []

    def column(self, x, spec, y=None, gap=0.27):
        y = self.H - 0.05 if y is None else y
        for s in spec:
            e = Entity(x=x, y=y, **{"w": self.w, **s})
            self.ents[e.key] = e
            y = e.bottom - gap

    def link(self, a, b, a_side, b_side, a_card="N", b_card="1", dashed=False, note=None):
        self.edges.append(dict(a=a, b=b, sa=a_side, sb=b_side, ca=a_card, cb=b_card, dashed=dashed, note=note))

    def assign_ports(self):
        groups = {}
        for i, ed in enumerate(self.edges):
            for end, other in (("a", "b"), ("b", "a")):
                e, side = self.ents[ed[end]], ed["s" + end]
                o = self.ents[ed[other]]
                groups.setdefault((e.key, side), []).append((i, end, o.cy if side in "lr" else o.cx))
        for (key, side), items in groups.items():
            e = self.ents[key]
            items.sort(key=lambda t: -t[2] if side in "lr" else t[2])
            n = len(items)
            span = min((e.h if side in "lr" else e.w) * 0.72, 0.3 * (n - 1))
            for k, (i, end, _) in enumerate(items):
                self.edges[i]["off_" + end] = 0.0 if n == 1 else span / 2 - span * k / (n - 1)

    def draw(self, ax):
        self.assign_ports()
        gaps = {}
        for ed in self.edges:
            a, b = self.ents[ed["a"]], self.ents[ed["b"]]
            if ed["sa"] in "rl" and ed["sb"] in "rl":
                if ed["sa"] != ed["sb"]:
                    key = (round(min(a.right, b.right), 2), round(max(a.left, b.left), 2))
                else:  # both ends on the same side: the lane is the gap next to that side of the column
                    c = min(range(3), key=lambda i: abs(self.xs[i] - a.x))
                    key = (round(self.xs[c - 1] + self.w, 2), round(self.xs[c], 2)) if ed["sa"] == "l"                         else (round(self.xs[c] + self.w, 2), round(self.xs[c + 1], 2))
                gaps.setdefault(key, []).append(ed)
        for (x0, x1), eds in gaps.items():
            self._order_trunks(x0, x1, eds)
        for ed in self.edges:
            self._route(ax, ed)
        for e in self.ents.values():
            e.draw(ax)

    def _ends(self, ed):
        def port(e, side, off):
            return {"r": (e.right, e.cy + off), "l": (e.left, e.cy + off),
                    "t": (e.cx + off, e.top), "b": (e.cx + off, e.bottom)}[side]

        a, b = self.ents[ed["a"]], self.ents[ed["b"]]
        return port(a, ed["sa"], ed.get("off_a", 0)), port(b, ed["sb"], ed.get("off_b", 0))

    def _order_trunks(self, x0, x1, eds):
        """Give every connector of one gap its own vertical lane, choosing the order with the fewest crossings."""
        n = len(eds)
        lo, hi = x0 + self.lane_margin, x1 - self.lane_margin
        if hi <= lo:
            lo, hi = x0 + (x1 - x0) * 0.35, x1 - (x1 - x0) * 0.35
        lanes = [(lo + hi) / 2] if n == 1 else [lo + (hi - lo) * k / (n - 1) for k in range(n)]
        ends = [self._ends(ed) for ed in eds]

        def segments(i, tx):
            (ax_, ay), (bx, by) = ends[i]
            return [((ax_, ay), (tx, ay)), ((tx, ay), (tx, by)), ((tx, by), (bx, by))]

        def crosses(s, t):
            (p, q), (r, u) = s, t
            for (h1, h2), (v1, v2) in (((p, q), (r, u)), ((r, u), (p, q))):
                if h1[1] == h2[1] and v1[0] == v2[0]:
                    if min(h1[0], h2[0]) < v1[0] < max(h1[0], h2[0]) and min(v1[1], v2[1]) < h1[1] < max(v1[1], v2[1]):
                        return True
            return False

        def cost(order):
            segs = [segments(i, lanes[order[i]]) for i in range(n)]
            return sum(crosses(s, t) for i in range(n) for j in range(i + 1, n) for s in segs[i] for t in segs[j])

        import itertools

        base = sorted(range(n), key=lambda i: -ends[i][0][1])
        if n <= 8:
            best = min(itertools.permutations(range(n)), key=cost)
        else:
            best = base
        for i, ed in enumerate(eds):
            ed["trunk"] = lanes[best[i]]

    def _route(self, ax, ed):
        p1, p2 = self._ends(ed)
        pts = [p1]
        if ed["sa"] in "rl" and ed["sb"] in "rl":
            tx = ed.get("trunk", (p1[0] + p2[0]) / 2)
            pts += [(tx, p1[1]), (tx, p2[1])]
        elif ed["sa"] in "tb" and ed["sb"] in "tb":
            ty = (p1[1] + p2[1]) / 2
            pts += [(p1[0], ty), (p2[0], ty)]
        pts.append(p2)
        xs, ys = zip(*pts)
        ax.plot(xs, ys, color=EDGE, lw=0.75, zorder=1, solid_capstyle="butt", ls="--" if ed["dashed"] else "-")
        for p, side, text in ((p1, ed["sa"], ed["ca"]), (p2, ed["sb"], ed["cb"])):
            dx, dy = {"r": (0.035, 0.03), "l": (-0.035, 0.03), "t": (0.045, 0.045), "b": (0.045, -0.045)}[side]
            ax.text(p[0] + dx, p[1] + dy, text, fontsize=FS - 0.8, fontweight="bold", zorder=6,
                    ha="left" if dx > 0 else "right", va="bottom" if dy > 0 else "top",
                    bbox=dict(boxstyle="square,pad=0.06", fc="white", ec="none"))
        if ed["note"]:
            mx = pts[1][0] if len(pts) > 3 else (p1[0] + p2[0]) / 2
            my = (pts[1][1] + pts[2][1]) / 2 if len(pts) > 3 else (p1[1] + p2[1]) / 2
            ax.text(mx + 0.04, my, ed["note"], fontsize=FS - 1.0, color=MUTED, style="italic", va="center", zorder=5)

    def save(self):
        low = min(e.bottom for e in self.ents.values()) - 0.08
        fig, ax = plt.subplots(figsize=(PAGE_W, self.H - low))
        fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
        self.draw(ax)
        ax.set_xlim(0, PAGE_W)
        ax.set_ylim(low, self.H)
        ax.axis("off")
        # only the PDF goes into thesis/figures (it is all LaTeX needs); pass `--png <folder>` for a preview image
        fig.savefig(os.path.join(OUT_DIR, f"{self.name}.pdf"), bbox_inches="tight", pad_inches=0.04)
        if "--png" in sys.argv:
            folder = sys.argv[sys.argv.index("--png") + 1]
            os.makedirs(folder, exist_ok=True)
            fig.savefig(os.path.join(folder, f"{self.name}.png"), bbox_inches="tight", pad_inches=0.04, dpi=200)
        plt.close(fig)


# --------------------------------------------------------------------------- catalogue
def catalogue():
    d = Diagram("modelo-datos-catalogo", 8.7, w=1.7, lane_margin=0.15)
    d.column(d.xs[0], [
        dict(key="alias", title="GameAlias", label="catalogue.GameAlias", fields=["id", "work", "locale", "value", "normalized_value"]),
        dict(key="source", title="SourceRecord", label="catalogue.SourceRecord", fields=["id", "work", "source", "source_id", "licence", "snapshot_sha256"]),
        dict(key="asset", title="AssetAttribution", label="catalogue.AssetAttribution", fields=["id", "work", "file_url", "creator", "licence", "display_allowed"]),
        dict(key="related", title="RelatedContent", label="catalogue.RelatedContent", fields=["id", "parent_work", "child_work", "relation"]),
        dict(key="vector", title="WorkFeatureVector", label="recommendations.WorkFeatureVector", fields=["id", "work", "feature_set_version", "vector_json"]),
    ])
    d.column(d.xs[1], [
        dict(key="work", title="GameWork", label="catalogue.GameWork", subtitle=["obra: identidad canónica del título"],
             fields=["id", "canonical_slug", "original_title", "title_en", "title_es", "summary", "first_release_date",
                     "total_rating", "total_rating_count", "is_dlc", "in_corpus", "corpus_version"]),
        dict(key="pop", title="CorpusPopularityScore", label="catalogue.CorpusPopularityScore", fields=["id", "work", "corpus_version", "score", "formula_version"]),
        dict(key="rating", title="CorpusRatingSnapshot", label="catalogue.CorpusRatingSnapshot", fields=["id", "work", "corpus_version", "rating", "rating_count"]),
    ], gap=0.3)
    d.column(d.xs[2], [
        dict(key="platform", title="Platform", label="catalogue.Platform", fields=["id", "name", "slug"]),
        dict(key="release", title="GameRelease", label="catalogue.GameRelease", fields=["id", "work", "platform", "release_name", "release_date"]),
        dict(key="edition", title="Edition", label="catalogue.Edition", fields=["id", "release", "name"]),
        dict(key="dims", title="Dimensiones", label=None, ref=True,
             subtitle=["Genre · Theme · Franchise", "Developer · Publisher · Keyword", "GameMode · PlayerPerspective", "(atributos comunes)"],
             extra=[("id", "uuid", "PK"), ("igdb_id", "int", "UQ"), ("name", "varchar", ""), ("slug", "varchar", "UQ")]),
        dict(key="evidence", title="GameWorkCuratedLabel", label="catalogue.GameWorkCuratedLabel", fields=["id", "work", "label", "source_kind", "source_value"]),
        dict(key="label", title="CuratedLabel", label="catalogue.CuratedLabel", fields=["id", "name", "slug", "kind", "curation_version"]),
    ], gap=0.34)
    for k in ("alias", "source", "asset", "related", "vector"):
        d.link(k, "work", "r", "l")
    d.link("pop", "work", "t", "b")
    d.link("rating", "work", "l", "l")
    d.link("release", "work", "l", "r")
    d.link("release", "platform", "t", "b", b_card="0..1")
    d.link("edition", "release", "t", "b")
    d.link("work", "dims", "r", "l", "N", "N")
    d.link("evidence", "work", "l", "r")
    d.link("evidence", "label", "b", "t", "N", "1")
    d.save()


# --------------------------------------------------------------------------- library and accounts
def biblioteca():
    d = Diagram("modelo-datos-biblioteca", 8.4, w=1.62, lane_margin=0.23)
    d.column(d.xs[0], [
        dict(key="profile", title="AccountProfile", label="accounts.AccountProfile",
             fields=["id", "user", "display_name", "bio", "avatar_preset", "is_anonymized"]),
        dict(key="fav", title="FavoriteSlot", label="accounts.FavoriteSlot", fields=["id", "user", "slot", "work"]),
        dict(key="comment", title="GameComment", label="library.GameComment", fields=["id", "user", "work", "text", "visibility"]),
    ], gap=0.4)
    d.column(d.xs[1], [
        dict(key="user", title="User (auth_user)", label="User", ref=True,
             fields=["id", "username", "email", "is_active", "date_joined"], min_h=2.2),
        dict(key="work", title="GameWork", label="catalogue.GameWork", ref=True,
             fields=["id", "canonical_slug"], subtitle=["(catálogo)"], min_h=1.55),
        dict(key="release", title="GameRelease", label="catalogue.GameRelease", ref=True,
             fields=["id", "work"], subtitle=["(catálogo)"]),
        dict(key="edition", title="Edition", label="catalogue.Edition", ref=True,
             fields=["id", "release"], subtitle=["(catálogo)"]),
    ], gap=0.4)
    d.column(d.xs[2], [
        dict(key="entry", title="LibraryEntry", label="library.LibraryEntry",
             fields=["id", "user", "work", "current_status", "rating_half_steps", "is_platinum"]),
        dict(key="transition", title="StatusTransition", label="library.StatusTransition",
             fields=["id", "entry", "from_status", "to_status", "changed_at"]),
        dict(key="copy", title="OwnedCopy", label="library.OwnedCopy",
             fields=["id", "user", "work", "release", "edition", "format", "idempotency_key", "price"]),
        dict(key="list", title="CustomList", label="library.CustomList",
             fields=["id", "user", "name", "public_slug", "visibility", "version"]),
        dict(key="item", title="CustomListItem", label="library.CustomListItem",
             fields=["id", "list", "work", "position"]),
    ], gap=0.3)
    d.link("profile", "user", "r", "l", "1", "1")
    d.link("fav", "user", "r", "l")
    d.link("comment", "user", "r", "l")
    d.link("fav", "work", "r", "l")
    d.link("comment", "work", "r", "l")
    d.link("entry", "user", "l", "r")
    d.link("copy", "user", "l", "r")
    d.link("list", "user", "l", "r")
    d.link("entry", "work", "l", "r")
    d.link("copy", "work", "l", "r")
    d.link("item", "work", "l", "r")
    d.link("copy", "release", "l", "r")
    d.link("copy", "edition", "l", "r", b_card="0..1")
    d.link("transition", "entry", "t", "b")
    d.link("item", "list", "t", "b")
    d.save()


# --------------------------------------------------------------------------- friendships and recommendations
def social():
    d = Diagram("modelo-datos-social", 7.6, w=1.62, lane_margin=0.23)
    d.column(d.xs[0], [
        dict(key="request", title="FriendshipRequest", label="social.FriendshipRequest",
             fields=["id", "sender", "receiver", "status", "responded_at"]),
        dict(key="block", title="Block", label="social.Block", fields=["id", "blocker", "blocked", "is_active"]),
        dict(key="message", title="SocialMessage", label="social.SocialMessage",
             fields=["id", "sender", "receiver", "work", "message", "read_at"]),
        dict(key="notice", title="SocialNotice", label="social.SocialNotice",
             fields=["id", "recipient", "actor", "kind", "work", "read_at"]),
    ], gap=0.32)
    d.column(d.xs[1], [
        dict(key="user", title="User (auth_user)", label="User", ref=True, fields=["id", "username"], min_h=3.1),
        dict(key="pair", title="RelationshipPair", label="social.RelationshipPair", fields=["id", "low_user", "high_user"]),
        dict(key="friendship", title="Friendship", label="social.Friendship", fields=["id", "pair", "accepted_at"]),
        dict(key="work", title="GameWork", label="catalogue.GameWork", ref=True, fields=["id"], subtitle=["(catálogo)"]),
    ], gap=0.45)
    d.column(d.xs[2], [
        dict(key="state", title="RecommendationState", label="recommendations.RecommendationState",
             fields=["id", "user", "collection_revision", "active_snapshot"]),
        dict(key="snapshot", title="RecommendationSnapshot", label="recommendations.RecommendationSnapshot",
             fields=["id", "user", "corpus_version", "payload", "generated_at"]),
        dict(key="job", title="RecommendationRefreshJob", label="recommendations.RecommendationRefreshJob",
             fields=["id", "user", "algorithm_id", "status", "attempts", "available_at"]),
        dict(key="signal", title="RecommendationSignalCache", label="recommendations.RecommendationSignalCache",
             fields=["id", "user", "corpus_version", "similarity_json", "created_at"]),
    ], gap=0.32)
    for k in ("request", "block", "message", "notice"):
        d.link(k, "user", "r", "l")  # drawn once although there are two foreign keys (sender and receiver, ...)
    d.link("message", "work", "r", "l", b_card="0..1")
    d.link("notice", "work", "r", "l", b_card="0..1")
    d.link("pair", "user", "t", "b")
    d.link("friendship", "pair", "t", "b", "1", "1")
    d.link("state", "user", "l", "r", "1", "1")
    d.link("state", "snapshot", "b", "t", "N", "0..1")
    d.link("snapshot", "user", "l", "r")
    d.link("job", "user", "l", "r")
    d.link("signal", "user", "l", "r")
    d.save()


if __name__ == "__main__":
    catalogue()
    biblioteca()
    social()
    print("written to", OUT_DIR)
