# sigfox-antenna-sim

GitHub Pages site and reproducible scripts for **Yang Wang**’s Sigfox scaffold-sensor study: how a nearby **steel Hall pull-wire** detunes the **RC4 helical / wire antenna** (~**920.8 MHz**, module **WSSFM10R4AT**, board **ZP_V06**).

**Live site:** [https://wy901015.github.io/sigfox-antenna-sim/](https://wy901015.github.io/sigfox-antenna-sim/)

## What’s inside

| Path | Description |
|------|-------------|
| `index.html` | Interactive Chart.js report (loads `sim/results/*.json`) |
| `sim/run_simulation.py` | Main pipeline — coupled model + NEC reference |
| `sim/results/` | Committed `summary.json`, `coupled_s11.json`, `nec_reference.json`, CSV |
| `assets/` | PCB floorplan + simulation geometry SVG/PNG |

## Re-run simulation

```bash
python3 -m pip install -r requirements.txt
python3 sim/run_simulation.py
python3 sim/generate_sim_layout_svg.py   # optional: refresh assets/sim-geometry.svg
```

Outputs are written under `sim/results/`.

## Method (short)

1. **PyNEC (NEC-2++)** thin-wire monopole (~75 mm) over perfect ground, optional horizontal steel wire (`sim/nec_model.py`). Useful reference; horizontal parasitic coupling is weak without enclosure mesh.
2. **Coupled resonator overlay** — antenna RLC + steel parasitic mode + mutual inductance ∝ (5 mm / *d*)³ (`sim/coupled_model.py`). Drives the published S11 curves.
3. **π-match** optimized with steel **OUT** (32 mm clearance), then frozen for the **IN** (5 mm) case.

Sweep: **880–960 MHz**. Targets: resonance shift, S11 @ 920.8 MHz, rough link penalty (dB).

**Caveat:** approximate model — not HFSS/CST. Validate on fully assembled hardware (plastic closed, cable min/mid/max).

## Enable GitHub Pages

1. Push `main` (must contain `index.html` at repo root).
2. GitHub → **Settings** → **Pages** → **Build and deployment** → Source: **Deploy from a branch**.
3. Branch: **`main`**, folder: **`/ (root)`**.
4. Save; site appears at `https://<user>.github.io/sigfox-antenna-sim/` after a minute.

CLI (requires `gh` auth with `repo` + `admin:repo_hook`):

```bash
gh api repos/wy901015/sigfox-antenna-sim/pages -X POST \
  -f build_type=legacy \
  -f source[branch]=main \
  -f source[path]=/
```

Or enable Pages in the repository settings UI if the API is restricted.

## License

Simulation code and docs in this repo are provided for engineering study on the scaffold sensor project. PyNEC / NEC-2++ are GPL — see upstream licenses if you redistribute binaries.
