# Mase-phi HPC Pipeline

Welcome to **Mase-phi HPC**, a modular, high-performance pipeline for phylogenetic analysis and longitudinal cancer evolution studies.

## Repository Layout
```
configs/          # YAML configuration files
data/             # Example datasets (unchanged)
docs/             # Technical documentation (work-in-progress)
environments/     # Conda environment definitions
scripts/          # CLI entry-point scripts
mase_phi_hpc/     # Core Python package
└── ...           # (bootstrap, aggregation, markers, phylowgs, longitudinal)
tests/            # Unit & integration tests
```

## Quick Start
1.  Install the Conda environments (requires Miniconda/Anaconda):
    ```bash
    ./scripts/install_environments.sh
    ```
2.  Activate the desired environment and run a pipeline step, e.g.:
    ```bash
    conda activate aggregation_env
    python -m mase_phi_hpc.aggregation <args>
    ```

*Detailed usage instructions and full documentation will be added during Phase 2–5.*