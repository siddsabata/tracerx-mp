"""mase_phi_hpc.bootstrap.bootstrapping
====================================
Bootstrapping utilities that generate resampled *SSM* files for downstream
PhyloWGS analysis.

The implementation is adapted from the original *1-bootstrap/step1_bootstrap.py*
script with the following refinements:

*   Converted to a reusable function-based API (no top-level CLI side-effects)
*   Adopted :pymod:`pathlib.Path` for path handling
*   Added comprehensive type hints & docstrings
*   Leveraged :pymod:`pandas` / :pymod:`numpy` directly; no extra deps

Usage example
-------------
>>> from pathlib import Path
>>> from mase_phi_hpc.bootstrap.bootstrapping import generate_bootstraps
>>> generate_bootstraps(Path("ssm.txt"), Path("out/"), n_bootstraps=100)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)
__all__ = [
    "bootstrap_va_dt",
    "write_bootstrapped_ssm_file",
    "generate_bootstraps",
]

# ---------------------------------------------------------------------------
# Core algorithms
# ---------------------------------------------------------------------------

def bootstrap_va_dt(
    af_list: List[float],
    depth_list: List[int],
    n_bootstraps: int,
) -> Tuple[np.ndarray, np.ndarray]:
    """Bootstrap depths *and* allele frequencies for a single mutation.

    Parameters
    ----------
    af_list
        Variant allele frequencies for each sample of a mutation *(0-1 range)*.
    depth_list
        Corresponding read depths for each sample.
    n_bootstraps
        Number of bootstrap replicates.

    Returns
    -------
    (vaf_boot, depth_boot)
        Two arrays of shape *(n_samples, n_bootstraps)* – the bootstrapped VAFs
        and depths respectively.
    """

    af_arr = np.asarray(af_list, dtype=float)
    depth_arr = np.asarray(depth_list, dtype=int)

    total_depth = int(depth_arr.sum())
    if total_depth < 0:
        raise ValueError("Depth values must be non-negative.")

    # Probability vector for multinomial redistribution of reads
    pvals = depth_arr / total_depth if total_depth > 0 else np.zeros_like(depth_arr, dtype=float)

    # Sample new depths – ensure no sample gets zero depth (within 10 attempts)
    for attempt in range(10):
        if total_depth == 0:
            depth_samples = np.zeros((n_bootstraps, len(depth_arr)), dtype=int)
        else:
            depth_samples = np.random.multinomial(total_depth, pvals, size=n_bootstraps)
        if total_depth == 0 or not (depth_samples == 0).any():
            break
    else:
        # Replace zeros (where original depth > 0) with one to keep counts valid
        mask_original_nonzero = depth_arr > 0
        depth_samples[(depth_samples == 0) & mask_original_nonzero] = 1

    depth_samples = depth_samples.T  # shape → (n_samples, n_bootstraps)
    vaf_samples = np.zeros_like(depth_samples, dtype=float)

    for i, (orig_vaf, _) in enumerate(zip(af_arr, depth_arr)):
        for j in range(n_bootstraps):
            d_sample = int(depth_samples[i, j])
            if d_sample == 0:
                vaf_samples[i, j] = 0.0
            else:
                var_reads = np.random.binomial(d_sample, orig_vaf)
                vaf_samples[i, j] = var_reads / d_sample

    return vaf_samples, depth_samples


# ---------------------------------------------------------------------------
# File I/O helpers
# ---------------------------------------------------------------------------

def write_bootstrapped_ssm_file(
    mutations: List[dict],
    bootstrap_idx: int,
    out_dir: Path,
) -> None:
    """Write a single *ssm.txt* (and empty *cnv.txt*) for a bootstrap replicate."""

    bootstrap_dir = out_dir / f"bootstrap{bootstrap_idx}"
    bootstrap_dir.mkdir(parents=True, exist_ok=True)

    ssm_path = bootstrap_dir / "ssm.txt"
    df = pd.DataFrame(mutations)
    if not df.empty:
        df = df[["id", "gene", "a", "d", "mu_r", "mu_v"]]
    else:
        df = pd.DataFrame(columns=["id", "gene", "a", "d", "mu_r", "mu_v"])

    df.to_csv(ssm_path, sep="\t", index=False)

    # Touch empty CNV file (required by PhyloWGS)
    (bootstrap_dir / "cnv.txt").touch()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_bootstraps(
    ssm_path: Path,
    output_dir: Path,
    *,
    n_bootstraps: int = 100,
) -> None:
    """Generate *n_bootstraps* SSM replicates from *ssm_path* into *output_dir*."""

    if not ssm_path.exists():
        raise FileNotFoundError(ssm_path)

    output_dir.mkdir(parents=True, exist_ok=True)

    df_ssm = pd.read_csv(ssm_path, sep="\t")
    if df_ssm.empty:
        raise ValueError("Input SSM file is empty – nothing to bootstrap.")

    required_cols = {"id", "gene", "a", "d", "mu_r", "mu_v"}
    missing = required_cols - set(df_ssm.columns)
    if missing:
        raise ValueError(f"Input SSM missing required columns: {', '.join(sorted(missing))}")

    # Pre-allocate list for each bootstrap iteration
    bootstrap_data: List[List[dict]] = [[] for _ in range(n_bootstraps)]

    for _, row in df_ssm.iterrows():
        try:
            mutation_id = row["id"]
            gene = row["gene"]
            mu_r = row["mu_r"]
            mu_v = row["mu_v"]

            # Handle multi-sample comma-separated counts
            if isinstance(row["a"], str):
                ref_counts = [int(x) for x in str(row["a"]).split(",")]
                depths = [int(x) for x in str(row["d"]).split(",")]
            else:
                ref_counts = [int(row["a"])]
                depths = [int(row["d"])]

            if len(ref_counts) != len(depths):
                logger.warning("Mismatch in 'a'/'d' sample counts for mutation %s – skipping", mutation_id)
                continue

            vaf_list = []
            depth_list = []
            for r_cnt, d_cnt in zip(ref_counts, depths):
                if d_cnt <= 0 or r_cnt < 0 or r_cnt > d_cnt:
                    logger.warning("Invalid counts for mutation %s – skipping sample", mutation_id)
                    continue
                vaf_list.append((d_cnt - r_cnt) / d_cnt if d_cnt else 0.0)
                depth_list.append(d_cnt)

            if not depth_list:
                logger.warning("No valid samples for mutation %s – skipping", mutation_id)
                continue

            vaf_boot, depth_boot = bootstrap_va_dt(vaf_list, depth_list, n_bootstraps)

            for bs_idx in range(n_bootstraps):
                new_depths = depth_boot[:, bs_idx]
                new_refs = np.round(vaf_boot[:, bs_idx] * new_depths).astype(int)

                a_str = ",".join(map(str, new_refs))
                d_str = ",".join(map(str, new_depths))

                bootstrap_data[bs_idx].append(
                    {
                        "id": mutation_id,
                        "gene": gene,
                        "a": a_str,
                        "d": d_str,
                        "mu_r": mu_r,
                        "mu_v": mu_v,
                    }
                )
        except Exception as exc:  # broad catch to keep pipeline running
            logger.exception("Error processing mutation row – skipped. (%s)", exc)

    # Write outputs
    logger.info("Writing %s bootstrapped SSM files to %s", n_bootstraps, output_dir)
    for i in range(n_bootstraps):
        write_bootstrapped_ssm_file(bootstrap_data[i], i + 1, output_dir)

    logger.info("Bootstrap generation complete.")