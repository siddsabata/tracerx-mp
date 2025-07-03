"""Configuration models and loader for longitudinal analysis.

This is a *first pass* migration of the original `5-long/config_handler.py`.
Long-term this should be replaced with Pydantic `BaseModel`s but for now we
keep the same dictionary structure while validating required sections.
"""

from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any, Dict, List

__all__ = ["load_config"]

_REQUIRED_SECTIONS = ["patient_id", "analysis_mode", "input_files", "output"]
_REQUIRED_INPUT_KEYS = [
    "aggregation_dir",
    "ssm_file",
    "longitudinal_data",
    "code_dir",
]


def load_config(config_path: str | Path) -> Dict[str, Any]:
    """Load and minimally validate a YAML config for longitudinal analysis."""

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(path)

    with path.open("r") as fh:
        cfg: Dict[str, Any] = yaml.safe_load(fh)

    # Required top-level sections
    missing = [sec for sec in _REQUIRED_SECTIONS if sec not in cfg]
    if missing:
        raise ValueError(f"Config missing required sections: {', '.join(missing)}")

    # Required input keys
    inputs = cfg["input_files"]
    missing_inputs = [k for k in _REQUIRED_INPUT_KEYS if k not in inputs]
    if missing_inputs:
        raise ValueError(f"Config missing required input_files fields: {', '.join(missing_inputs)}")

    # Fill optional defaults
    cfg.setdefault("parameters", {})
    cfg.setdefault("fixed_markers", [])
    cfg.setdefault("filtering", {"timepoints": []})
    cfg.setdefault("visualization", {"generate_plots": True, "plot_format": "png", "save_intermediate": False})
    cfg.setdefault("validation", {"validate_inputs": True, "debug_mode": False})

    return cfg