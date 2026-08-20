# FM-Scheduling — a benchmark for technician-constrained building-maintenance work-order scheduling

Companion repository for the manuscript *"An Open CMMS-Derived Benchmark for
Building-Maintenance Work-Order Dispatching: Rules, Optimisation, and
Learning"* (under peer review).

Preprint (earlier version) can be accessed here: http://dx.doi.org/10.2139/ssrn.7095162

Preprint can be accessed here: http://dx.doi.org/10.2139/ssrn.7095162

It contains, for reuse and verification:

- **Benchmark instances** (`data/instances.tar.zst`): 3,186 real-data replay
  instances and 1,800 calibrated generator instances (4,986 total) built from
  the public FMUCD work-order database, in a documented JSON schema.
- **The instance generator** with per-campus fitted parameter packs
  (`src/fmwos/generator.py`, `results/p2_generator/`).
- **The independent feasibility validator** (`src/fmwos/validator.py`) that
  scores every method and shares no code with any scheduler.
- **All methods under test**: seven dispatching rules (EDD, pFIFO, WSPT, ATC,
  WMDD, LPT, and a random-order floor), exact and rolling CP-SAT, a genetic
  algorithm, and the PPO-trained dispatcher (MLP and attention variants),
  plus training code.
- **Scored results** for every experiment in the paper (`results/`): the
  development evaluations, the frozen final evaluation (`results/r4_final/`),
  the robustness suites (`results/r4_robustness/`), the preventive-visibility
  study (`results/r4_visibility/`), and the diagnostic re-simulations
  (travel, weight-vector, candidate-cap sweeps).
- **The pre-specified evaluation protocol** (`docs/protocol.md`): the two
  decision gates, their pass/fail criteria, and the dated amendment history.

## Data source and licences

Raw data: FMUCD (Facility Management Unified Classification Database),
Mendeley Data, DOI [10.17632/cb8d2nsjss.1](https://doi.org/10.17632/cb8d2nsjss.1),
CC BY 4.0. The exact distribution file used has SHA-256
`4464648252c4bdca2a6deba9d467e94aec7568d675f51e06d6d343b3c09f006a`.

- **Data and derived artefacts** (instances, fitted parameter packs, scored
  results): **CC BY 4.0** (`LICENSE`), inherited from FMUCD.
- **Code** (`src/`, `scripts/`, `tests/`): **MIT** (`LICENSE-CODE`).

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
# final evaluation, robustness suites, and the preventive-visibility study
# (order and gates in docs/protocol.md, section R4):
PYTHONPATH=src python scripts/r4_final_instances.py && \
    PYTHONPATH=src python scripts/r4_final_eval.py && \
    PYTHONPATH=src python scripts/r4_analysis.py
python scripts/p5_figures.py && \
    python scripts/p5_figures_extra.py && \
    PYTHONPATH=src python scripts/r4_figures.py  # paper figures
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
  diagnostics (travel, weights, candidate cap); `r4_*.py` are the final
  evaluation, robustness, visibility, and exhibit generators.
- `results/` — every number in the paper traces to a file here.
- `docs/` — pre-specified protocol and the public decision log.

## Citation

A citation entry will be added upon publication.
