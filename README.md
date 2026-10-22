# sigfox-antenna-sim

GitHub Pages + reproducible EM case matrix for **Yang Wang**’s Sigfox scaffold sensor (**WSSFM10R4AT**, **ZP_V06**, RC4 **920.8 MHz**): steel Hall pull-wire vs helical antenna.

**Live site:** [https://wy901015.github.io/sigfox-antenna-sim/](https://wy901015.github.io/sigfox-antenna-sim/)

## Model (v2 — more device-like)

| Element | Implementation |
|--------|----------------|
| **Helix** | PyNEC `helix()` — 22 mm × 10 mm OD, 4 mm pitch, 0.5 mm wire on PEC ground |
| **Steel cable** | 1.3 mm braided wire, dog-leg across ANT corner; span 170 mm (extended) or 75 mm (reeled) |
| **Spool** | 12-segment metal ring when reeled |
| **LiPo** | Wire-frame shell ~48 mm from ANT |
| **Plastic** | ε_eff ≈ 1.45 + shunt capacitance (not 3D dielectric mesh) |
| **Detuning** | Hybrid: NEC Z(f) + RLC + mutual L / near-field C vs clearance (0 at ≥32 mm baseline) |
| **Matching** | π-network optimized on **steel OUT 32 mm**, frozen for all cases |

**Reference only:** `monopole_reference.json` — legacy 75 mm monopole NEC sweep.

**Caveat:** Still approximate (not HFSS/CST). Use for keep-out trends; validate with VNA in closed housing.

## Cases (6)

1. Steel OUT ≥32 mm (baseline)  
2. Steel IN ~5 mm (crossing, extended)  
3. 15 mm / 25 mm clearance  
4. 5 mm + reeled spool  
5. 5 mm + cable segment parallel to helix axis  

Per-case JSON: `sim/results/cases/<case_id>.json`  
Table + curves: `sim/results/summary.json`, `coupled_s11.json`

## Re-run

```bash
python3 -m pip install -r requirements.txt
python3 sim/run_simulation.py
python3 sim/generate_sim_layout_svg.py   # optional SVG
```

## GitHub Pages

Settings → Pages → branch **`main`**, folder **`/`** (root `index.html`).
