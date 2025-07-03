"""mase_phi_hpc.aggregation.aggregation
====================================
High-level aggregation logic that combines PhyloWGS bootstrap results into a
single *tree_distribution* summary per patient.

The code is adapted from *3-aggregation/step3_aggregate.py* and supporting
helpers in *step3_analyze.py*. Only the functions required for the standard
bootstrap aggregation workflow are included. Tree utility helpers already live
in :pymod:`mase_phi_hpc.common.tree_utils`.
"""

from __future__ import annotations

import gzip
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, List, Tuple
from zipfile import ZipFile

import numpy as np
import pandas as pd

from mase_phi_hpc.common.tree_utils import render_tumor_tree  # optional – for visualisation

logger = logging.getLogger(__name__)

__all__ = [
    "process_phylowgs_output",
    "aggregate_bootstrap_replicates",
]

TreeStructure = Dict[int, List[int]]
NodeDict = Dict[int, List[int]]
FreqDict = Dict[int, List[List[float]]]


def process_phylowgs_output(
    summ_file: Path,
    muts_file: Path,
    mutass_file: Path,
) -> Tuple[
    TreeStructure,
    NodeDict,
    Dict[int, List[str]],
    Dict[Tuple[int, ...], int],
    Dict[Tuple[str, ...], Tuple[str, ...]],
    List[dict],
    FreqDict,
    FreqDict,
]:
    """Parse PhyloWGS *summ*, *muts* and *mutass* files for the **best** tree.

    The logic follows the original implementation but with clearer typing and
    comments.
    """

    with gzip.open(summ_file, "rt") as f:
        j_summ = json.load(f)

    # Identify the highest-likelihood tree index as a string key
    best_tree = max(j_summ["trees"].items(), key=lambda kv: kv[1]["llh"])[0]
    tree_struct_raw = j_summ["trees"][best_tree]["structure"]

    with ZipFile(mutass_file) as zf, zf.open(f"{best_tree}.json") as gz:
        tree_detail = json.load(gz)

    with gzip.open(muts_file, "rt") as mf:
        j_muts = json.load(mf)

    # Build structured outputs ------------------------------------------------
    tree_structure: TreeStructure = {int(p): [int(c) for c in ch] for p, ch in tree_struct_raw.items()}

    node_dict: NodeDict = {}
    node_dict_name: Dict[int, List[str]] = {}
    node_dict_re: Dict[Tuple[int, ...], int] = {}
    final_tree_cp: Dict[Tuple[str, ...], Tuple[str, ...]] = {}

    for p, mut_info in tree_detail["mut_assignments"].items():
        p_int = int(p)
        muts_idx = sorted(mut_info["ssms"])
        node_dict[p_int] = muts_idx
        node_dict_name[p_int] = [j_muts["ssms"][m]["name"] for m in muts_idx]
        node_dict_re[tuple(muts_idx)] = p_int

    for parent, children in tree_struct_raw.items():
        p_tuple = tuple(sorted([j_muts["ssms"][m]["name"] for m in tree_detail["mut_assignments"][parent]["ssms"]])) if parent != "0" else ("normal",)
        for child in children:
            c_tuple = tuple(sorted([j_muts["ssms"][m]["name"] for m in tree_detail["mut_assignments"][str(child)]["ssms"]]))
            final_tree_cp[c_tuple] = p_tuple

    population_dict = j_summ["trees"][best_tree]["populations"]
    clonal_freq: FreqDict = {}
    vaf_frac: FreqDict = {}
    prev_mat: List[dict] = []

    for node, pops in population_dict.items():
        node_i = int(node)
        clonal_freq[node_i] = []
        vaf_frac[node_i] = []
        for sample_idx, cp in enumerate(pops["cellular_prevalence"]):
            prev = cp - sum(population_dict[str(child)]["cellular_prevalence"][sample_idx] for child in tree_structure.get(node_i, []))
            clonal_freq[node_i].append(prev)
            vaf_frac[node_i].append(cp)
            prev_mat.append({"fraction": prev, "sample": sample_idx, "clone": node_i})
        clonal_freq[node_i] = [clonal_freq[node_i]]  # keep shape consistent with original
        vaf_frac[node_i] = [vaf_frac[node_i]]

    return (
        tree_structure,
        node_dict,
        node_dict_name,
        node_dict_re,
        final_tree_cp,
        prev_mat,
        clonal_freq,
        vaf_frac,
    )


# ---------------------------------------------------------------------------
# Aggregation driver
# ---------------------------------------------------------------------------

def aggregate_bootstrap_replicates(
    patient: str,
    bootstrap_dirs: List[Path],
    output_dir: Path,
    *,
    method: str = "phylowgs",
    generate_fig: bool = True,
) -> None:
    """Aggregate results from multiple bootstrap directories into a summary."""

    output_dir.mkdir(parents=True, exist_ok=True)

    tree_distribution = {
        "cp_tree": [],
        "node_dict": [],
        "node_dict_name": [],
        "node_dict_re": [],
        "tree_structure": [],
        "freq": [],
        "clonal_freq": [],
        "vaf_frac": [],
    }

    processed = 0
    for bs_dir in bootstrap_dirs:
        summ = bs_dir / "result.summ.json.gz"
        muts = bs_dir / "result.muts.json.gz"
        mutass = bs_dir / "result.mutass.zip"
        if not (summ.exists() and muts.exists() and mutass.exists()):
            logger.warning("Missing result files in %s – skipping", bs_dir)
            continue

        (
            tree_struct,
            node_dict,
            node_dict_name,
            node_dict_re,
            final_tree_cp,
            prev_mat,
            clonal_freq,
            vaf_frac,
        ) = process_phylowgs_output(summ, muts, mutass)

        # combine_tree logic simplified: treat each unique cp_tree as separate entry
        if final_tree_cp in tree_distribution["cp_tree"]:
            idx = tree_distribution["cp_tree"].index(final_tree_cp)
            tree_distribution["freq"][idx] += 1
            # append clonal freq / vaf – simplified (append lists)
            for k in clonal_freq:
                tree_distribution["clonal_freq"][idx][k] += clonal_freq[k]
                tree_distribution["vaf_frac"][idx][k] += vaf_frac[k]
        else:
            tree_distribution["cp_tree"].append(final_tree_cp)
            tree_distribution["node_dict"].append(node_dict)
            tree_distribution["node_dict_name"].append(node_dict_name)
            tree_distribution["node_dict_re"].append(node_dict_re)
            tree_distribution["tree_structure"].append(tree_struct)
            tree_distribution["freq"].append(1)
            tree_distribution["clonal_freq"].append(clonal_freq)
            tree_distribution["vaf_frac"].append(vaf_frac)

        processed += 1

    logger.info("Processed %s/%s bootstrap directories", processed, len(bootstrap_dirs))

    if not processed:
        logger.error("No bootstrap directories processed successfully.")
        return

    # Save pickle summaries ---------------------------------------------------
    with open(output_dir / f"{method}_bootstrap_summary.pkl", "wb") as fh:
        pickle.dump(tree_distribution, fh)

    # Simple text summary JSON of best tree (highest freq)
    best_idx = int(np.argmax(tree_distribution["freq"]))
    best_tree = {
        "node_dict_name": tree_distribution["node_dict_name"][best_idx],
        "tree_structure": tree_distribution["tree_structure"][best_idx],
    }
    with open(output_dir / f"{patient}_results_bootstrap_initial_best.json", "w") as js:
        json.dump(best_tree, js, indent=2)

    # Optional basic visualisation (Graphviz)
    if generate_fig:
        try:
            g = render_tumor_tree(
                tree_distribution["tree_structure"][best_idx],
                tree_distribution["node_dict_name"][best_idx],
            )
            g.render(filename=str(output_dir / f"{patient}_best_tree"), format="png", cleanup=True)
        except Exception as exc:
            logger.warning("Graphviz rendering failed: %s", exc)

    logger.info("Aggregation complete – results in %s", output_dir)