"""Runtime and process-resource metadata for reproducible evaluations."""

from __future__ import annotations

import os
import platform
import sys
import time
from importlib import metadata
from typing import Any


def _package_version(distribution: str) -> str | None:
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return None


def runtime_environment() -> dict[str, Any]:
    """Return non-sensitive environment facts needed to reproduce a run.

    Deliberately excludes hostnames, paths, environment-variable values and
    credentials. The manifest describes the execution environment without
    turning an evidence artifact into an accidental machine inventory.
    """

    packages = {
        name: version
        for name, version in {
            "Django": _package_version("Django"),
            "numpy": _package_version("numpy"),
            "scipy": _package_version("scipy"),
            "scikit-learn": _package_version("scikit-learn"),
            "pandas": _package_version("pandas"),
        }.items()
        if version is not None
    }
    return {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "machine": platform.machine(),
        "cpu_count": os.cpu_count(),
        "packages": packages,
    }


def process_resource_usage() -> dict[str, float | int | None]:
    """Capture process CPU time and peak RSS when the platform exposes it."""

    try:
        import resource

        usage = resource.getrusage(resource.RUSAGE_SELF)
        # Linux reports KiB; macOS reports bytes. Keep the unit explicit and
        # convert macOS so the artifact has one portable interpretation.
        max_rss_kib = int(usage.ru_maxrss)
        if sys.platform == "darwin":
            max_rss_kib = round(max_rss_kib / 1024)
        return {
            "max_rss_kib": max_rss_kib,
            "user_cpu_seconds": round(float(usage.ru_utime), 6),
            "system_cpu_seconds": round(float(usage.ru_stime), 6),
        }
    except (ImportError, AttributeError, OSError):
        return {
            "max_rss_kib": None,
            "user_cpu_seconds": round(time.process_time(), 6),
            "system_cpu_seconds": None,
        }
