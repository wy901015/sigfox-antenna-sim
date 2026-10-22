# Simulation pipeline (v2)

## Files

- `geometry.py` — documented dimensions (helix, steel, spool, battery, enclosure)
- `cases.py` — case matrix IDs
- `nec_model.py` — PyNEC scene builder
- `coupled_model.py` — hybrid Z(f) + π-match helpers
- `run_simulation.py` — writes `results/` and `results/cases/*.json`

## Outputs

- `results/summary.json` — geometry docs + comparison table
- `results/coupled_s11.json` — all S11(f) curves
- `results/cases_comparison.csv`
- `results/nec_reference.json` — helix+battery raw NEC
- `results/monopole_reference.json` — optional monopole reference
