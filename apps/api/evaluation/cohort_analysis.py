"""Cohort-level analysis of an already materialised evaluation artifact."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

ACCURACY_METRICS = ("precision", "recall", "ndcg", "map")
BEYOND_USER_METRICS = ("intra_list_diversity", "novelty", "recommended_count")
RUN_LEVEL_ONLY_METRICS = (
    "catalogue_coverage",
    "concentration_hhi",
    "prediction_coverage",
)


def _mean(values: Sequence[float]) -> float | None:
    return round(math.fsum(values) / len(values), 8) if values else None


def _metric_values(
    rows: Sequence[Mapping[str, Any]], section: str, k: str, metric: str
) -> list[float]:
    values: list[float] = []
    for row in rows:
        section_value = row.get(section)
        value = section_value.get(k) if isinstance(section_value, Mapping) else None
        if isinstance(value, Mapping) and value.get(metric) is not None:
            values.append(float(value[metric]))
    return values


def _summarise_rows(rows: Sequence[Mapping[str, Any]], k: str) -> dict[str, Any]:
    metrics = {
        metric: _mean(_metric_values(rows, "metrics", k, metric))
        for metric in ACCURACY_METRICS
    }
    beyond: dict[str, Any] = {}
    for metric in BEYOND_USER_METRICS:
        values = _metric_values(rows, "beyond_accuracy", k, metric)
        beyond[metric] = {"value": _mean(values), "user_count": len(values)}
    return {
        "user_count": len(rows),
        "metrics": metrics,
        "beyond_accuracy": beyond,
        "k": int(k),
    }


def analyse_artifact(artifact: Mapping[str, Any], population_manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Join per-user results with the immutable synthetic-population manifest.

    The function intentionally does not query Django or recalculate rankings.
    It is therefore safe to run after the one-shot test evaluation has been
    consumed. Missing ranked lists are reported rather than reconstructed.
    """

    users = population_manifest.get("users", [])
    by_user = {
        str(user["account_id"]): user
        for user in users
        if isinstance(user, Mapping) and "account_id" in user
    }
    algorithms = artifact.get("algorithms", {})
    if not isinstance(algorithms, Mapping) or not algorithms:
        raise ValueError("evaluation artifact has no algorithm sections")

    algorithm_rows: dict[str, dict[str, Mapping[str, Any]]] = {}
    unknown_users: set[str] = set()
    for algorithm_id, algorithm in algorithms.items():
        rows = algorithm.get("per_user", [])
        indexed: dict[str, Mapping[str, Any]] = {}
        for row in rows:
            user_id = str(row["user_id"])
            indexed[user_id] = row
            if user_id not in by_user:
                unknown_users.add(user_id)
        algorithm_rows[str(algorithm_id)] = indexed
    if unknown_users:
        raise ValueError(
            "evaluation users missing from population manifest: "
            + ", ".join(sorted(unknown_users))
        )

    cohort_names = sorted({str(user.get("cohort", "unknown")) for user in users})
    cohorts: dict[str, Any] = {}
    for cohort in cohort_names:
        population_ids = {
            user_id for user_id, user in by_user.items() if str(user.get("cohort")) == cohort
        }
        cohort_algorithms: dict[str, Any] = {}
        for algorithm_id, rows_by_user in sorted(algorithm_rows.items()):
            rows = [rows_by_user[user_id] for user_id in sorted(population_ids) if user_id in rows_by_user]
            evaluated_ids = set(rows_by_user) & population_ids
            algorithm_value = algorithms[algorithm_id]
            cohort_algorithms[algorithm_id] = {
                "evaluated_user_count": len(evaluated_ids),
                "not_evaluable_user_count": len(population_ids) - len(evaluated_ids),
                "summary_by_k": {
                    k: _summarise_rows(
                        [row for row in rows if isinstance(row.get("metrics", {}).get(k), Mapping)],
                        k,
                    )
                    for k in ("5", "10", "20")
                },
                "run_level_only_metrics": {
                    k: {
                        metric: algorithm_value.get("beyond_accuracy", {}).get(k, {}).get(metric)
                        for metric in RUN_LEVEL_ONLY_METRICS
                    }
                    for k in ("5", "10", "20")
                },
            }
        cohorts[cohort] = {
            "population_user_count": len(population_ids),
            "evaluated_user_count": len(
                set().union(*(set(indexed) for indexed in algorithm_rows.values())) & population_ids
            ),
            "not_evaluable_reason": (
                "La cohorte no contiene positivos elegibles para este split; "
                "no se puede calcular ranking personalizado."
                if cohort == "no_history"
                else None
            ),
            "algorithms": cohort_algorithms,
        }

    return {
        "analysis": "evaluation-cohorts-v1",
        "artifact_protocol_version": artifact.get("protocol_version"),
        "artifact_protocol_sha256": artifact.get("protocol_sha256"),
        "corpus_version": artifact.get("corpus_version"),
        "split": artifact.get("split"),
        "population_manifest_sha256": population_manifest.get("manifest_sha256"),
        "population_count": len(by_user),
        "artifact_evaluated_user_count": artifact.get("evaluation_population", {}).get("evaluated_user_count"),
        "cohorts": cohorts,
        "limitations": {
            "run_level_only_metrics": list(RUN_LEVEL_ONLY_METRICS),
            "explanation": (
                "El artefacto v15 conserva agregados globales y filas por usuario, "
                "pero no las listas recomendadas completas. Por eso cobertura, HHI "
                "y cobertura de predicción se conservan como métricas globales del run "
                "y no se desagregan artificialmente por cohorte."
            ),
        },
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    """Render the cohort report as citable Spanish evidence."""

    lines = [
        "# Desglose por cohortes de la evaluación offline v15",
        "",
        f"- Protocolo: `{report.get('artifact_protocol_version')}`",
        f"- Corpus: `{report.get('corpus_version')}`",
        f"- Split: `{report.get('split')}`",
        f"- Usuarios del manifiesto: **{report.get('population_count')}**",
        f"- Usuarios evaluables registrados: **{report.get('artifact_evaluated_user_count')}**",
        "",
        "Este informe es una transformación determinista del artefacto JSON ya ejecutado y "
        "del manifiesto de población. No relanza algoritmos ni consulta datos vivos.",
        "",
    ]
    for cohort, cohort_data in report["cohorts"].items():
        lines.extend([
            f"## Cohorte `{cohort}`",
            "",
            f"Población: **{cohort_data['population_user_count']}**; "
            f"evaluables: **{cohort_data['evaluated_user_count']}**.",
        ])
        if cohort_data.get("not_evaluable_reason"):
            lines.extend(["", f"> {cohort_data['not_evaluable_reason']}"])
        lines.extend(["", "| Algoritmo | K | Usuarios | Precision | Recall | nDCG | MAP | ILD | Novedad |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"])
        for algorithm_id, algorithm in cohort_data["algorithms"].items():
            for k in ("5", "10", "20"):
                summary = algorithm["summary_by_k"][k]
                beyond = summary["beyond_accuracy"]
                def value(metric: str) -> str:
                    current = summary["metrics"].get(metric)
                    return "—" if current is None else f"{current:.6f}"
                ild = beyond["intra_list_diversity"]["value"]
                novelty = beyond["novelty"]["value"]
                lines.append(
                    f"| `{algorithm_id}` | {k} | {summary['user_count']} | "
                    f"{value('precision')} | {value('recall')} | {value('ndcg')} | {value('map')} | "
                    f"{'—' if ild is None else f'{ild:.6f}'} | "
                    f"{'—' if novelty is None else f'{novelty:.6f}'} |"
                )
        lines.append("")
    lines.extend([
        "## Métricas que permanecen globales",
        "",
        "El artefacto v15 no guarda el ranking completo de cada usuario. Por ello "
        "`catalogue_coverage`, `concentration_hhi` y `prediction_coverage` se mantienen "
        "como métricas globales por algoritmo y K; el informe no las asigna a cohortes "
        "por aproximación.",
        "",
        "## Lectura metodológica",
        "",
        "La cohorte `no_history` es una condición descriptiva de arranque en frío: no debe "
        "interpretarse como un algoritmo con rendimiento cero. Las cohortes con historial "
        "sí se comparan sobre las mismas listas de candidatos, el mismo split y el mismo "
        "artefacto, por lo que sus medias son comparables dentro de los límites del estudio "
        "sintético.",
        "",
    ])
    return "\n".join(lines)
