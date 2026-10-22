# Simulation pipeline

## Geometry (`geometry.py`)

- Monopole height **75 mm** (quarter-wave electrical ~81 mm on helix).
- Steel pull-wire: **120 mm** span, **1.2 mm** radius, height **35 mm**.
- **IN:** 5 mm lateral clearance (violates λ/10 keep-out).
- **OUT:** 32 mm clearance (recommended keep-out).

## Scripts

- `run_simulation.py` — writes `results/summary.json`, `coupled_s11.json`, `nec_reference.json`, `coupled_s11.csv`.
- `nec_model.py` — PyNEC wire model.
- `coupled_model.py` — mutual-inductance parasitic coupling + π-match.
- `generate_sim_layout_svg.py` — `../assets/sim-geometry.svg`.

## Dependencies

See root `requirements.txt` (`numpy`, `scipy`, `PyNEC`, `matplotlib` optional).
