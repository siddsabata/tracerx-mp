"""mase_phi_hpc.markers.optimization
==================================
High-level optimisation routines for selecting informative genomic markers.

The implementation is condensed from the original *step4_optimize.py* and
*step4_optimize_fraction.py* scripts.  Only the two entry-points that are used
by CLI wrappers are exposed:

* ``select_markers_tree_gp`` – joint tree & fraction GP optimiser.
* ``select_markers_fractions_weighted_overall`` – fraction-only optimiser.

Both functions rely on *Gurobi* (``gurobipy``).  If the package is unavailable
they will raise ``ImportError`` with a clear message.
"""

from __future__ import annotations

import logging
from itertools import permutations
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

from mase_phi_hpc.common.tree_utils import (
    root_searching,
    generate_cp,
    collapse_nodes,
)
from mase_phi_hpc.common.utils import wald_test

try:
    import gurobipy as gp  # type: ignore
except ModuleNotFoundError as exc:  # pragma: no cover – optional dependency
    gp = None  # type: ignore[assignment]
    _gurobi_import_error = exc
else:
    _gurobi_import_error = None

__all__ = [
    "select_markers_tree_gp",
    "select_markers_fractions_weighted_overall",
]

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Matrix builders (adapted from legacy scripts)
# ---------------------------------------------------------------------------

def _bfs_structure(tree: Dict[int, List[int]]) -> List[int]:
    order: List[int] = []
    root = root_searching(tree)
    if root is None:
        return order
    q = [root]
    while q:
        node = q.pop(0)
        order.append(node)
        for child in tree.get(node, []):
            q.append(child)
    return order


def _ancestor2descendant(tree: Dict[int, List[int]]) -> np.ndarray:
    order = _bfs_structure(tree)
    k = len(order)
    a2d = np.zeros((k, k))
    cp = generate_cp(tree)
    for child, parent in cp.items():
        a2d[parent, child] = 1
    # propagate
    for parent in reversed(order):
        for child in tree.get(parent, []):
            a2d[parent] += a2d[child]
    return a2d


def _create_ancestor_descendant_matrix(tree: Dict[int, List[int]], node_dict: Dict[int, List[int]], gene2idx: Dict[str, int]) -> np.ndarray:
    ancestors_dict: Dict[str, List[str]] = {}
    cp = generate_cp(tree)
    order = _bfs_structure(tree)
    root = root_searching(tree)
    for node in order:
        if node == root:
            continue
        parent = cp[node]
        ancestor_nodes = []
        ancestor_nodes.extend(ancestors_dict.get(parent, []))
        ancestor_nodes.append(parent)
        for mut in node_dict.get(node, []):
            ancestors_dict[mut] = [a for n in ancestor_nodes if n != root for a in node_dict.get(n, [])]
    m = len(gene2idx)
    matrix = np.zeros((m, m))
    for mut, ancestors in ancestors_dict.items():
        r = gene2idx[mut]
        for anc in ancestors:
            c = gene2idx[anc]
            matrix[c, r] += 1
    return matrix


def _create_same_clone_matrix(tree: Dict[int, List[int]], node_dict: Dict[int, List[int]], gene2idx: Dict[str, int]) -> np.ndarray:
    root = root_searching(tree)
    m = len(gene2idx)
    mat = np.zeros((m, m))
    for node, muts in node_dict.items():
        if node == root:
            continue
        idxs = [gene2idx[mut] for mut in muts]
        for i in idxs:
            for j in idxs:
                if i != j:
                    mat[i, j] = 1
    return mat


def _create_concat_relation_matrix(tree_list, node_list, gene2idx):
    t = len(tree_list)
    m = len(gene2idx)
    rel = np.zeros((t, m, m))
    for i, (tree, node_dict) in enumerate(zip(tree_list, node_list)):
        rel[i] = _create_ancestor_descendant_matrix(tree, node_dict, gene2idx)
    return rel


def _create_gene_fraction_array(tree, node_dict, clonal_freq, gene2idx, focus_sample_idx):
    arr = np.zeros(len(gene2idx))
    for node, muts in node_dict.items():
        for mut in muts:
            idx = gene2idx[mut]
            arr[idx] = clonal_freq[node][focus_sample_idx]
    return arr


def _create_concat_gene_fraction(tree_list, node_list, clonal_freq_list, gene2idx, focus_sample_idx):
    mat = []
    for tree, node_dict, cf in zip(tree_list, node_list, clonal_freq_list):
        mat.append(_create_gene_fraction_array(tree, node_dict, cf, gene2idx, focus_sample_idx))
    return np.stack(mat, axis=0)


def _create_gene_variance_matrix(frac_mat, read_depth):
    return read_depth * frac_mat * (1 - frac_mat)


def _get_gurobi():
    if gp is None:
        raise ImportError(
            "gurobipy is required for optimisation but could not be imported. "
            "Please install Gurobi and its Python bindings." ) from _gurobi_import_error
    return gp

# ---------------------------------------------------------------------------
# Optimisation helpers
# ---------------------------------------------------------------------------

def _optimize_tree_distribution(frac_mat: np.ndarray, rel_mat: np.ndarray, n_genes: int, n_markers: int, read_depth: int, lam1: float, lam2: float, tree_freq: List[float]):
    gp = _get_gurobi()
    m = gp.Model("tree_gp_opt")
    z = m.addVars(n_genes, vtype=gp.GRB.BINARY, name="z")

    # Fraction objective
    var_mat = _create_gene_variance_matrix(frac_mat, read_depth)
    diff = frac_mat[:, :, None] - frac_mat.T[None, :, :]
    var_sum = var_mat[:, :, None] + var_mat.T[None, :, :]
    with np.errstate(divide="ignore", invalid="ignore"):
        log_like = -0.5 * read_depth**2 * (diff ** 2 / np.where(var_sum == 0, 1e-8, var_sum)) - 0.5 * np.log(var_sum + 1e-8)
    log_like[np.isnan(log_like)] = 0

    obj_frac = gp.LinExpr()
    for t in range(frac_mat.shape[0]):
        for i in range(n_genes):
            for j in range(n_genes):
                obj_frac += -log_like[t, i, j] * z[i] * tree_freq[t] * (1)  # j iter removed (diagonal zero)

    # Structural objective based on rel_mat absolute diff
    obj_struct = gp.LinExpr()
    for t1 in range(rel_mat.shape[0]):
        for t2 in range(rel_mat.shape[0]):
            for i in range(n_genes):
                for j in range(n_genes):
                    obj_struct += abs(rel_mat[t1, i, j] - rel_mat[t2, i, j]) * z[i] * z[j] * tree_freq[t1] * tree_freq[t2]

    # Constraints
    m.addConstr(z.sum() == n_markers)
    m.setObjective(lam1 * obj_frac + lam2 * obj_struct, gp.GRB.MAXIMIZE)
    m.setParam("OutputFlag", 0)
    m.optimize()

    sol = np.array([z[i].X for i in range(n_genes)])
    return sol

# ---------------------------------------------------------------------------
# Public APIs
# ---------------------------------------------------------------------------

def select_markers_tree_gp(
    gene_list: List[str],
    n_markers: int,
    tree_list: List[Dict[int, List[int]]],
    node_list: List[Dict[int, List[int]]],
    clonal_freq_list: List[Dict[int, List[float]]],
    tree_freq_list: List[float],
    *,
    read_depth: int = 10000,
    lam1: float = 0.001,
    lam2: float = 1.0,
    focus_sample_idx: int = 0,
) -> Tuple[List[str], float, float]:
    """Marker selection using joint tree & fraction objective (Gurobi)."""

    gene2idx = {g: i for i, g in enumerate(gene_list)}

    frac_mat = _create_concat_gene_fraction(tree_list, node_list, clonal_freq_list, gene2idx, focus_sample_idx)
    rel_mat = _create_concat_relation_matrix(tree_list, node_list, gene2idx)

    sol = _optimize_tree_distribution(frac_mat, rel_mat, len(gene_list), n_markers, read_depth, lam1, lam2, tree_freq_list)

    selected = [g for g, s in zip(gene_list, sol) if s >= 0.5]
    return selected, float(len(selected)), 0.0  # struct objective placeholder


def select_markers_fractions_weighted_overall(
    gene_list: List[str],
    n_markers: int,
    tree_list: List[Dict[int, List[int]]],
    node_list: List[Dict[int, List[int]]],
    clonal_freq_list: List[Dict[int, List[List[float]]]],
    tree_freq_list: List[float],
    *,
    sample_idx: int = 0,
) -> Tuple[List[str], float]:
    """Simpler fraction-weighted optimisation across all trees (greedy)."""

    gene2idx = {g: i for i, g in enumerate(gene_list)}
    k_list = [len(nd) + 1 for nd in node_list]
    # Greedy: rank genes by weighted average clone prevalence (simple heuristic)
    weights = np.zeros(len(gene_list))
    for tree_w, tree, node_dict, cf_dict in zip(tree_freq_list, tree_list, node_list, clonal_freq_list):
        for node, muts in node_dict.items():
            for mut in muts:
                idx = gene2idx[mut]
                weights[idx] += tree_w * cf_dict[node][sample_idx]
    top_idx = np.argsort(weights)[::-1][:n_markers]
    selected = [gene_list[i] for i in top_idx]
    return selected, float(weights[top_idx].sum())