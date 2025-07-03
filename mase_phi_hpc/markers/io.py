"""mase_phi_hpc.markers.io
========================
Utilities for reading **SSM** files and converting them into a multi-sample
:pymod:`pandas.DataFrame` suitable for marker-selection algorithms.

Derived from *4-markers/step4_convert_ssm.py*.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd

__all__ = [
    "convert_ssm_to_dataframe_multi",
]

# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _parse_gene_string(gene_string: str | float | None) -> Dict[str, Any]:
    if gene_string is None or (isinstance(gene_string, float) and pd.isna(gene_string)):
        return {"symbol": "Unknown", "chromosome": "N/A", "position": "N/A", "ref": "N", "alt": "N"}

    parts = str(gene_string).split("_")
    if len(parts) >= 4 and ">" in parts[3]:
        sym, chrom, pos, mut_part = parts[:4]
        ref, alt = mut_part.split(">", 1)
    elif len(parts) == 1:
        sym, chrom, pos, ref, alt = parts[0], "N/A", "N/A", "N", "N"
    else:
        sym, chrom, pos, ref, alt = gene_string, "N/A", "N/A", "N", "N"

    return {"symbol": sym, "chromosome": chrom, "position": pos, "ref": ref, "alt": alt}


def _parse_counts(count_string: Any) -> List[int]:
    if count_string is None:
        return []
    try:
        return [int(x.strip()) for x in str(count_string).split(",") if x.strip()]
    except ValueError:
        return []


def _calculate_vaf(ref: int, depth: int) -> float:
    return 0.0 if depth == 0 else (depth - ref) / depth

# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------

def _apply_vaf_filter(
    df: pd.DataFrame,
    *,
    strategy: str = "any_high",
    threshold: float = 0.9,
    specific_samples: List[int] | None = None,
) -> pd.DataFrame:
    vaf_cols = [c for c in df.columns if c.startswith("VAF_sample_")]
    if not vaf_cols:
        return df.copy()

    if strategy == "any_high":
        mask = (df[vaf_cols] >= threshold).any(axis=1)
    elif strategy == "all_high":
        mask = (df[vaf_cols] >= threshold).all(axis=1)
    elif strategy == "majority_high":
        mask = (df[vaf_cols] >= threshold).sum(axis=1) > len(vaf_cols) / 2
    elif strategy == "specific_samples":
        specific_samples = specific_samples or [0]
        cols = [f"VAF_sample_{i}" for i in specific_samples if f"VAF_sample_{i}" in df.columns]
        mask = (df[cols] >= threshold).any(axis=1) if cols else pd.Series(False, index=df.index)
    else:
        mask = pd.Series(False, index=df.index)
    return df[~mask].reset_index(drop=True)

# ---------------------------------------------------------------------------
# Public converter
# ---------------------------------------------------------------------------

def convert_ssm_to_dataframe_multi(
    ssm_file: Path | str,
    *,
    filter_strategy: str = "any_high",
    filter_threshold: float = 0.9,
    specific_samples: List[int] | None = None,
) -> pd.DataFrame:
    """Convert an *SSM* file (multi-sample) into a tidy DataFrame.

    Parameters
    ----------
    ssm_file
        Path to the *ssm.txt* file.
    filter_strategy / filter_threshold / specific_samples
        Parameters forwarded to the VAF filter.

    Returns
    -------
    pandas.DataFrame
        One row per mutation with columns:
        * gene metadata (symbol, chromosome, position, ref, alt)
        * VAF_sample_i for i in range(n_samples)
    """

    ssm_path = Path(ssm_file)
    if not ssm_path.exists():
        raise FileNotFoundError(ssm_path)

    ssm_df = pd.read_csv(ssm_path, sep="\t")
    required_cols = {"id", "gene", "a", "d", "mu_r", "mu_v"}
    if not required_cols.issubset(ssm_df.columns):
        missing = required_cols - set(ssm_df.columns)
        raise ValueError(f"SSM missing required columns: {', '.join(sorted(missing))}")

    output_rows: List[dict] = []

    for _, row in ssm_df.iterrows():
        gene_meta = _parse_gene_string(row["gene"])
        ref_counts = _parse_counts(row["a"])
        depths = _parse_counts(row["d"])
        if len(ref_counts) != len(depths) or not depths:
            continue

        vafs = [_calculate_vaf(r, d) if 0 <= r <= d else 0.0 for r, d in zip(ref_counts, depths)]
        out = {
            "Hugo_Symbol": gene_meta["symbol"],
            "Reference_Allele": gene_meta["ref"],
            "Allele": gene_meta["alt"],
            "Chromosome": gene_meta["chromosome"],
            "Start_Position": gene_meta["position"],
        }
        out.update({f"VAF_sample_{i}": v for i, v in enumerate(vafs)})
        output_rows.append(out)

    df_out = pd.DataFrame(output_rows)
    return _apply_vaf_filter(df_out, strategy=filter_strategy, threshold=filter_threshold, specific_samples=specific_samples)