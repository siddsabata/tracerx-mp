"""mase_phi_hpc.common.tree_utils
================================
Shared helper functions and classes for manipulating and visualising
phylogenetic trees.

This module is an amalgamation of the original utilities defined in:

* `3-aggregation/tree_operations.py`
* `3-aggregation/tree_rendering.py`
* (selected generic helpers from other modules)

Keeping them in a single place avoids code duplication and facilitates
unit-testing. All functions are imported using fully-qualified names so
legacy scripts can be progressively refactored to depend on this module
instead of re-implementing similar logic in multiple locations.
"""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple, Optional

import numpy as np

# ``graphviz`` is an optional dependency – only required for rendering. We
# import it lazily to avoid hard failures in non-GUI environments.
try:
    from graphviz import Digraph  # type: ignore
except ModuleNotFoundError:  # pragma: no cover – doc build / minimal env
    Digraph = None  # type: ignore[misc,assignment]

__all__ = [
    "ModifyTree",
    "collapse_nodes",
    "render_tumor_tree",
    "add_prefix_tree",
    "df2dict",
    "W2node_dict",
    "generate_tree",
    "generate_cp",
    "root_searching",
    "E2tree",
    "validate_sample_consistency",
]


# ---------------------------------------------------------------------------
# Core tree manipulation helpers
# ---------------------------------------------------------------------------

class ModifyTree:
    """Utility class for modifying tree structures expressed as an *edge* matrix.

    The original implementation came from *tree_operations.py* and is preserved
    with minor stylistic updates and type annotations.

    Parameters
    ----------
    E:
        Square *edge* matrix where ``E[parent, child] == 1`` indicates an edge
        from *parent* → *child*.
    """

    def __init__(self, E: np.ndarray):
        self.E = np.asarray(E, dtype=int)
        self.N: int = self.E.shape[0]
        self.cp_tree: Dict[int, int] = {}
        self.tree: Dict[int, List[int]] = {}

        # Build child-parent and parent-children mappings.
        for parent in range(self.N - 1, -1, -1):
            for child in range(self.N - 1, -1, -1):
                if int(self.E[parent, child]) == 1:
                    self.cp_tree[child] = parent
                    self.tree.setdefault(parent, []).append(child)

    # ------------------------------------------------------------------
    # Convenience predicates
    # ------------------------------------------------------------------

    def is_leaf(self, idx: int) -> bool:
        """Return *True* if *idx* has no children."""

        return idx not in self.tree

    def is_root(self, idx: int) -> bool:
        """Return *True* if *idx* has no parent (i.e. root node)."""

        return idx in self.tree and idx not in self.cp_tree

    def num_children(self, idx: int) -> int:
        """Return the number of children for *idx*."""

        return 0 if self.is_leaf(idx) else len(self.tree[idx])

    # ------------------------------------------------------------------
    # Structural modification
    # ------------------------------------------------------------------

    def delete_node(self, idx: int) -> None:
        """Remove a node from the tree whilst keeping the structure valid.

        The removal rules mirror the original script – root deletion is only
        allowed when it has a single child; internal nodes have their children
        re-attached to the parent.
        """

        if self.is_root(idx):
            if self.num_children(idx) > 1:
                raise ValueError("Cannot delete root node with more than one child!")
            child = self.tree[idx][0]
            self.tree.pop(idx)
            self.cp_tree.pop(child, None)
        elif self.is_leaf(idx):
            parent = self.cp_tree.pop(idx)
            if self.num_children(parent) == 1:
                self.tree.pop(parent)
            else:
                self.tree[parent].remove(idx)
        else:  # internal node
            parent = self.cp_tree.pop(idx)
            children = self.tree.pop(idx)
            self.tree[parent].remove(idx)
            for child in children:
                self.cp_tree[child] = parent
                self.tree[parent].append(child)
                self.E[parent, child] = 1  # maintain edge matrix


# ---------------------------------------------------------------------------
# Collapsing helpers
# ---------------------------------------------------------------------------

def collapse_nodes(
    U: np.ndarray,
    C: np.ndarray,
    E: np.ndarray,
    A: np.ndarray,
    W: np.ndarray,
    *,
    threshold: float = 0.0,
    only_leaf: bool = False,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Collapse low-information nodes (branch length 0 or low frequency).

    Parameters
    ----------
    U, C, E, A, W
        Matrices describing the tree (identical semantics to the original
        implementation).
    threshold
        Frequency threshold below which nodes are considered for removal.
    only_leaf
        If *True* a conservative strategy that only deletes leaves is applied.

    Returns
    -------
    Updated ``(U, C, E, A, W)`` tuple with the specified nodes removed.
    """

    tree = ModifyTree(E)

    branch_remove_idx: List[int] = []
    freq_remove_idx: List[int] = []
    freq_leaf_remove_idx: List[int] = []

    def _collapse_branch(node: int) -> None:
        target = tree.cp_tree[node]
        U[:, target] += U[:, node]
        tree.delete_node(node)
        branch_remove_idx.append(node)

    # ------------------------------------------------------------------
    # 1. Zero-length branch removal
    # ------------------------------------------------------------------
    for parent in range(tree.N - 1, -1, -1):
        for child in range(tree.N - 1, -1, -1):
            if int(E[parent, child]) == 1 and W[child, :].sum() == 0:
                _collapse_branch(child)

    # ------------------------------------------------------------------
    # 2. Frequency-based pruning
    # ------------------------------------------------------------------
    for node in range(tree.N - 1, -1, -1):
        if node in branch_remove_idx or tree.is_root(node):
            continue
        mean_freq = float(np.mean(U[:, node]))
        if mean_freq <= threshold:
            if tree.num_children(node) == 1:
                freq_remove_idx.append(node)
            elif tree.is_leaf(node):
                freq_leaf_remove_idx.append(node)

    for node in freq_remove_idx:
        target = tree.tree[node][0]
        tree.delete_node(node)
        W[target, :] += W[node, :]

    for node in freq_leaf_remove_idx:
        tree.delete_node(node)

    # Combine and rebuild matrices
    remove_idx: List[int] = branch_remove_idx + freq_remove_idx + freq_leaf_remove_idx
    if remove_idx:
        U = np.delete(U, remove_idx, axis=1)
        C = np.delete(C, remove_idx, axis=0)
        A = np.delete(A, remove_idx, axis=0)
        A = np.delete(A, remove_idx, axis=1)
        E = np.delete(tree.E, remove_idx, axis=0)
        E = np.delete(E, remove_idx, axis=1)
        W = np.delete(W, remove_idx, axis=0)
    return U, C, E, A, W


# ---------------------------------------------------------------------------
# Rendering utilities
# ---------------------------------------------------------------------------

def render_tumor_tree(tree_structure: Dict[int, List[int]], node_dict: Dict[int, List[str]]):
    """Render a tumour phylogeny with Graphviz.

    The function mirrors the original implementation but guards against a
    missing *graphviz* installation (returns *None* in that case).
    """

    if Digraph is None:
        raise ImportError("graphviz is not installed – install via `pip install graphviz` or skip rendering.")

    graph = Digraph(format="png")
    edge_idx = 0
    root = root_searching(tree_structure)

    for parent, children in tree_structure.items():
        parent_label_elements = ["normal"] if parent == root else node_dict[parent]
        parent_label = _format_node_label(parent, parent_label_elements)

        for child in children:
            edge_idx += 1
            child_elements = node_dict.get(child, [str(child)])
            child_label = _format_node_label(child, child_elements)
            graph.edge(parent_label, child_label, f"b{edge_idx}")

    return graph


def _format_node_label(node_idx: int, mutations: Sequence[str]) -> str:
    """Create a multi-line label if the mutation list is long."""

    prefix = f"{node_idx} "
    if len(mutations) < 10:
        return prefix + " ".join(str(m) for m in mutations)

    # Split into thirds for readability
    third = len(mutations) // 3
    lines = [" ".join(str(m) for m in mutations[i : i + third]) for i in range(0, len(mutations), third)]
    return prefix + "\n".join(lines)


# ---------------------------------------------------------------------------
# Convenience helpers originally from tree_rendering.py
# ---------------------------------------------------------------------------

def add_prefix_tree(mutation: Dict[int, List[str]]) -> Dict[int, List[str]]:
    """Prepend ``mut_`` to each mutation identifier (purely cosmetic)."""

    return {node: [f"mut_{m}" for m in mut_list] for node, mut_list in mutation.items()}


def df2dict(df) -> Dict[int, str]:  # type: ignore[valid-type]
    """Convert a *pandas* DataFrame to an *index → mutation name* mapping."""

    import pandas as pd  # local import to avoid hard dependency

    if not isinstance(df, pd.DataFrame):  # defensive
        raise TypeError("df must be a pandas DataFrame")

    idx2name: Dict[int, str] = {}
    for i in range(len(df)):
        gene_val = df.loc[i, "Gene"]
        if isinstance(gene_val, str):
            name = gene_val
        else:
            name = f"{df.loc[i, 'Chromosome']}_{df.loc[i, 'Genomic Position']}"
        idx2name[i] = name
    return idx2name


def W2node_dict(W_node: np.ndarray, idx2name: Optional[Dict[int, str]] = None) -> Dict[int, List[str]]:
    """Transform a binary *W* matrix (nodes × mutations) to a dict mapping."""

    node_dict: Dict[int, List[str]] = {}
    N, m = W_node.shape
    for i in range(N):
        node_dict.setdefault(i, [])
        for j in range(m):
            if W_node[i, j] == 1:
                name = idx2name[j] if idx2name is not None else j  # type: ignore[arg-type]
                node_dict[i].append(name)  # type: ignore[list-item]
    return node_dict


def generate_tree(cp_tree: Dict[int, int]) -> Dict[int, List[int]]:
    """Convert *child → parent* mapping to *parent → children* mapping."""

    tree: Dict[int, List[int]] = {}
    for child, parent in cp_tree.items():
        tree.setdefault(parent, []).append(child)
    return tree


def generate_cp(tree: Dict[int, List[int]]) -> Dict[int, int]:
    """Convert *parent → children* mapping to *child → parent* mapping."""

    return {c: p for p, children in tree.items() for c in children}


def root_searching(tree: Dict[int, List[int]]) -> Optional[int]:
    """Return the root node of *tree* or *None* if it cannot be determined."""

    tree_cp = generate_cp(tree)
    if not tree_cp:
        return None

    current = next(iter(tree_cp))
    visited = set()
    for _ in range(len(tree_cp) + 1):  # safe upper bound
        if current in visited:
            # Cycle detected – not a valid tree
            return None
        visited.add(current)
        if current not in tree_cp:
            break
        current = tree_cp[current]
    return current


def E2tree(E: np.ndarray) -> Dict[int, List[int]]:
    """Convert an edge matrix to *parent → children* dictionary representation."""

    tree: Dict[int, List[int]] = {}
    N = int(E.shape[0])
    for i in range(N):
        for j in range(N):
            if E[i, j] == 1:
                tree.setdefault(i, []).append(j)
    return tree


def validate_sample_consistency(clonal_freq_data: Dict[int, List[List[float]]]) -> int:
    """Return the sample count if all nodes share the same number of samples.

    If counts differ *-1* is returned as a sentinel value.
    """

    sample_counts: List[int] = [len(freq_sample) for freqs in clonal_freq_data.values() for freq_sample in freqs]
    unique_counts = set(sample_counts)
    if len(unique_counts) > 1:
        print(f"Warning: Inconsistent sample counts across nodes: {unique_counts}")
        return -1
    return next(iter(unique_counts)) if unique_counts else 0