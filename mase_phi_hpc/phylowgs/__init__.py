"""PhyloWGS orchestration helpers.

The original implementation used *2-phylowgs/phylowgs.sh* – a SLURM-aware bash
script – to execute PhyloWGS (Python 2) across bootstrap samples.  This package
now provides a thin Python wrapper (`run_bootstrap_sample`) that offers the
same functionality programmatically.

Running PhyloWGS still relies on the external PhyloWGS repository and a Python
2 environment.  Ensure the `phylowgs_env` Conda environment is activated or
accessible before calling the helper.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

__all__ = ["run_bootstrap_sample"]


def run_bootstrap_sample(
    bootstrap_dir: Path,
    phylowgs_repo: Path,
    *,
    num_chains: int = 5,
    python_exe: str = "python2",
    extra_args: Optional[List[str]] = None,
) -> None:
    """Execute *multievolve.py* and *write_results.py* for one bootstrap folder.

    Parameters
    ----------
    bootstrap_dir
        Directory containing `ssm.txt` and `cnv.txt` for a single bootstrap.
    phylowgs_repo
        Path to the cloned PhyloWGS repository (where *multievolve.py* lives).
    num_chains
        Number of MCMC chains. Defaults to 5 to mirror the original script.
    python_exe
        Python executable that can run PhyloWGS (Python 2).
    extra_args
        Additional flags to pass directly to *multievolve.py*.
    """

    bootstrap_dir = bootstrap_dir.resolve()
    phylowgs_repo = phylowgs_repo.resolve()

    ssm_file = bootstrap_dir / "ssm.txt"
    cnv_file = bootstrap_dir / "cnv.txt"
    chains_dir = bootstrap_dir / "chains"

    for f in (ssm_file, cnv_file):
        if not f.exists():
            raise FileNotFoundError(f)

    multievolve = phylowgs_repo / "multievolve.py"
    write_results = phylowgs_repo / "write_results.py"

    if not multievolve.exists() or not write_results.exists():
        raise FileNotFoundError("Cannot locate PhyloWGS scripts in repository path")

    chains_dir.mkdir(exist_ok=True)

    cmd_multievolve = [
        python_exe,
        str(multievolve),
        "--num-chains",
        str(num_chains),
        "--ssms",
        str(ssm_file),
        "--cnvs",
        str(cnv_file),
        "--output-dir",
        str(chains_dir),
    ] + (extra_args or [])

    logger.info("Running multievolve: %s", " ".join(cmd_multievolve))
    subprocess.run(cmd_multievolve, check=True)

    cmd_write_results = [
        python_exe,
        str(write_results),
        "--include-ssm-names",
        "result",
        str(chains_dir / "trees.zip"),
        str(bootstrap_dir / "result.summ.json.gz"),
        str(bootstrap_dir / "result.muts.json.gz"),
        str(bootstrap_dir / "result.mutass.zip"),
    ]

    logger.info("Running write_results: %s", " ".join(cmd_write_results))
    subprocess.run(cmd_write_results, check=True)

    logger.info("Finished PhyloWGS run for %s", bootstrap_dir)