# FM-Scheduling — a benchmark for technician-constrained building-maintenance work-order scheduling

Preprint can be accessed here: http://dx.doi.org/10.2139/ssrn.7095162
Companion repository for the manuscript *"When Does Learned Dispatching Beat
Priority Rules? An Open Benchmark for Technician-Constrained
Maintenance Work-Order Scheduling in Building Portfolios"* (under peer review).

It contains, for reuse and verification:

- **Benchmark instances** (`data/instances.tar.zst`): 3,186 real-data replay
  instances and 1,800 calibrated generator instances (4,986 total) built from
  the public FMUCD work-order database, in a documented JSON schema.
- **The instance generator** with per-campus fitted parameter packs
  (`src/fmwos/generator.py`, `results/p2_generator/`).
- **The independent feasibility validator** (`src/fmwos/validator.py`) that
  scores every method and shares no code with any scheduler.
- **All methods under test**: six dispatching rules, exact and rolling CP-SAT,
  a genetic algorithm, and the PPO-trained dispatcher (MLP and attention
  variants), plus training code.
- **Scored results** for every experiment in the paper (`results/`), and the
  diagnostic re-simulations (travel, weight-vector, candidate-cap sweeps).
- **The pre-specified evaluation protocol** (`docs/protocol.md`): the two
  decision gates, their pass/fail criteria, and the dated amendment history.

## Data source and licence

Raw data: FMUCD (Facility Management Unified Classification Database),
Mendeley Data, DOI [10.17632/cb8d2nsjss.1](https://doi.org/10.17632/cb8d2nsjss.1),
CC BY-NC 4.0. The exact distribution file used has SHA-256
`4464648252c4bdca2a6deba9d467e94aec7568d675f51e06d6d343b3c09f006a`.
Everything in this repository is released under **CC BY-NC 4.0**, inherited
from FMUCD; commercial users must license FMUCD independently.

## Reproduce

```bash
conda env create -f environment.yml && conda activate fmwos
# 1. download FMUCD to data/raw/FMUCD.csv (SHA-256 above must match)
python scripts/p0_profile.py                    # cleaning audit + profiling
python scripts/p1_instances.py                  # calibration + replay track
python scripts/p2_generator.py                  # generator track
PYTHONPATH=src python scripts/p2_e1.py          # E1 static (sharded, resumable)
PYTHONPATH=src python -m fmwos.train --seed 301 --curriculum v2  # PPO
PYTHONPATH=src python scripts/p4_dyneval.py --with-pmmix --with-storm2 \
    --storm-arrivals 1.25,1.5,2.0,3.0           # dynamic evaluation
PYTHONPATH=src python scripts/p4_analysis.py    # Gate-B tables
python scripts/p5_figures.py                    # paper figures
```

Unpack the released instances instead of rebuilding them:

```bash
mkdir -p data/processed && tar -C data/processed --zstd -xf data/instances.tar.zst
```

Tests (plain python): `PYTHONPATH=src python tests/<file>.py`.

## Layout

- `src/fmwos/` — io/cleaning, calibration, instances, generator, validator,
  dispatching rules, CP-SAT (static + rolling), GA, environment, lower
  bound, policies (MLP + attention), PPO training.
- `scripts/` — one entry point per experiment; `r2_*.py` are the revision
  diagnostics (travel, weights, candidate cap).
- `results/` — every number in the paper traces to a file here.
- `docs/` — pre-specified protocol and the public decision log.

## Citation

Citation entry will be added upon publication.
