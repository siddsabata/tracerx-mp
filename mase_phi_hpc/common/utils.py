"""mase_phi_hpc.common.utils
===========================
Generic helper utilities that do **not** rely on any pipeline-specific
invariants. These functions can be used throughout the package and in unit
tests.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List

import numpy as np

__all__ = [
    "calculate_tree_entropy",
    "get_dominant_tree_frequency",
    "count_significant_trees",
    "validate_timepoint_data",
    "safe_division",
    "format_gene_list_for_display",
    "extract_numeric_from_marker_id",
    "create_result_metadata",
    "log_analysis_progress",
    "summarize_marker_usage",
]

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Basic numerical helpers
# ---------------------------------------------------------------------------

def calculate_tree_entropy(tree_frequencies: List[float]) -> float:
    """Return Shannon entropy of a tree frequency distribution."""

    return float(-sum(f * np.log(f + 1e-10) for f in tree_frequencies if f > 0))


def get_dominant_tree_frequency(tree_frequencies: List[float]) -> float:
    """Return the frequency of the most dominant tree (max value)."""

    return max(tree_frequencies, default=0.0)


def count_significant_trees(tree_frequencies: List[float], *, threshold: float = 0.01) -> int:
    """Count how many trees have a frequency greater than *threshold*."""

    return sum(1 for f in tree_frequencies if f > threshold)


# ---------------------------------------------------------------------------
# Data-frame / content validation helpers
# ---------------------------------------------------------------------------

def validate_timepoint_data(timepoint_data, required_genes: List[str], *, timepoint: str, log: logging.Logger | None = None) -> bool:  # type: ignore[valid-type]
    """Return *True* when *timepoint_data* contains **all** *required_genes*.

    Parameters
    ----------
    timepoint_data:
        A *pandas.DataFrame* with gene names in the **index**. (Typed as
        `Any` to avoid a hard dependency on *pandas* for modules that do not
        need it.)
    required_genes:
        List of gene identifiers that must be present.
    timepoint:
        Identifier used only for logging messages.
    log:
        Optional logger, falls back to module-level ``logger``.
    """

    _logger = log or logger

    missing = [g for g in required_genes if g not in timepoint_data.index]
    if missing:
        _logger.warning("Missing genes in timepoint %s: %s", timepoint, missing)
        return False
    return True


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def safe_division(numerator: float, denominator: float, *, default: float = 0.0) -> float:
    """Return ``numerator / denominator`` guarding against division by zero."""

    return numerator / denominator if denominator != 0 else default


def format_gene_list_for_display(gene_list: List[str], *, max_display: int = 5) -> str:
    """Turn a list of genes into a human-readable string with truncation."""

    if len(gene_list) <= max_display:
        return ", ".join(gene_list)
    displayed = ", ".join(gene_list[:max_display])
    remaining = len(gene_list) - max_display
    return f"{displayed} (and {remaining} more)"


def extract_numeric_from_marker_id(marker_id: str) -> int:
    """Extract the integer part from marker IDs such as ``s5`` ⇒ ``5``."""

    if marker_id.startswith("s") and marker_id[1:].isdigit():
        return int(marker_id[1:])
    raise ValueError(f"Invalid marker ID format: {marker_id}")


def create_result_metadata(patient_id: str, analysis_mode: str, *, n_timepoints: int, **kwargs: Any) -> Dict[str, Any]:
    """Return a dictionary with standardized metadata for result files."""

    metadata: Dict[str, Any] = {
        "patient_id": patient_id,
        "analysis_mode": analysis_mode,
        "timestamp": datetime.now().isoformat(),
        "n_timepoints": n_timepoints,
        "pipeline_version": "2.0.0",
    }
    metadata.update(kwargs)
    return metadata


def log_analysis_progress(log: logging.Logger, current_step: int, *, total_steps: int, step_description: str) -> None:
    """Emit a progress message of the form *Step X/Y – description* to *log*."""

    progress_pct = (current_step / total_steps) * 100
    log.info("Progress: Step %s/%s (%.1f%%) – %s", current_step, total_steps, progress_pct, step_description)


def summarize_marker_usage(all_selections: List[Dict[str, Any]], log: logging.Logger | None = None) -> Dict[str, Any]:
    """Create summary statistics across all timepoints for dynamic analysis."""

    _logger = log or logger

    if not all_selections:
        return {"total_unique_markers": 0, "marker_frequency": {}, "usage_patterns": {}}

    marker_counts: Dict[str, int] = {}
    for selection in all_selections:
        for marker in selection.get("selected_markers", []):
            marker_counts[marker] = marker_counts.get(marker, 0) + 1

    total_unique = len(marker_counts)
    most_used_marker, max_usage = max(marker_counts.items(), key=lambda x: x[1]) if marker_counts else ("none", 0)

    usage_summary = {
        "total_unique_markers": total_unique,
        "marker_frequency": marker_counts,
        "most_used_marker": most_used_marker,
        "max_usage_count": max_usage,
        "avg_markers_per_timepoint": float(np.mean([len(sel.get("selected_markers", [])) for sel in all_selections])),
    }

    _logger.info("Marker usage summary: %s unique markers used", total_unique)
    _logger.info("Most frequently used: %s (%s times)", most_used_marker, max_usage)

    return usage_summary