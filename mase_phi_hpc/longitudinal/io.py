"""Input/Output helpers for longitudinal analysis."""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import pandas as pd

__all__ = ["load_ssm", "load_longitudinal_csv"]


def load_ssm(ssm_file: str | Path) -> pd.DataFrame:
    """Load an SSM file (tab-separated) into a DataFrame."""

    path = Path(ssm_file)
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path, sep="\t")


def load_longitudinal_csv(csv_file: str | Path) -> pd.DataFrame:
    """Load longitudinal ddPCR measurements CSV."""

    path = Path(csv_file)
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)