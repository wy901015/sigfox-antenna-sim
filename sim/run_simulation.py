#!/usr/bin/env python3
"""Run NEC + coupled-resonator study and write sim/results/*.json and CSV."""

from __future__ import annotations

import csv
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from coupled_model import (  # noqa: E402
    CoupledParams,
    apply_pi_match,
    optimize_pi_match,
    run_coupled_sweep,
    s11_curve,
)
from geometry import F_SIGFOX_RC4_MHZ, GEO  # noqa: E402
from nec_model import resonant_frequency_mhz, run_nec_sweep, s11_db  # noqa: E402

RESULTS = ROOT / "results"
RESULTS.mkdir(parents=True, exist_ok=True)


def _find_resonance_mhz(freqs_mhz: list[float], s11: np.ndarray) -> float:
    idx = int(np.argmin(s11))
    return float(freqs_mhz[idx])


def main() -> None:
    f0 = 880.0
    f1 = 960.0
    n = 81

    # --- Coupled model (primary curves for the site) ---
    p = CoupledParams()
    f_out, z_out = run_coupled_sweep(GEO.steel_clearance_out_mm, f0, f1, n, p)
    f_in, z_in = run_coupled_sweep(GEO.steel_clearance_in_mm, f0, f1, n, p)
    f_hz = np.array(f_out) * 1e6

    c1, ls, c2 = optimize_pi_match(z_out, f_hz, F_SIGFOX_RC4_MHZ * 1e6, GEO.z0_ohm)
    zin_out = apply_pi_match(z_out, f_hz, c1, ls, c2)
    zin_in = apply_pi_match(z_in, f_hz, c1, ls, c2)
    s11_out = s11_curve(zin_out, GEO.z0_ohm)
    s11_in = s11_curve(zin_in, GEO.z0_ohm)

    i_sig = int(np.argmin(np.abs(np.array(f_out) - F_SIGFOX_RC4_MHZ)))
    fres_out = _find_resonance_mhz(f_out, s11_out)
    fres_in = _find_resonance_mhz(f_in, s11_in)

    # Relative gain penalty: use coupled Im{Z} peak + empirical 0.15 dB per MHz shift
    delta_f = fres_in - fres_out
    s11_delta = float(s11_in[i_sig] - s11_out[i_sig])
    # Conductance ratio at Sigfox channel (proxy for radiated power with fixed match)
    g_out = np.real(1.0 / zin_out[i_sig])
    g_in = np.real(1.0 / zin_in[i_sig])
    gain_penalty_db = float(10.0 * math.log10(max(g_in, 1e-9) / max(g_out, 1e-9)))

    # --- NEC reference (raw 50 Ω S11, documents limit of wire-only model) ---
    nec_freq_out, nec_z_out, nec_g_out = run_nec_sweep(GEO.steel_clearance_out_mm)
    nec_freq_in, nec_z_in, nec_g_in = run_nec_sweep(GEO.steel_clearance_in_mm)
    nec_s11_out = [s11_db(z, GEO.z0_ohm) for z in nec_z_out]
    nec_s11_in = [s11_db(z, GEO.z0_ohm) for z in nec_z_in]

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "device": {
            "module": "WSSFM10R4AT / SFM10R4",
            "pcb": "ZP_V06",
            "tx_mhz": F_SIGFOX_RC4_MHZ,
            "band": "Sigfox RC4",
        },
        "geometry": {
            "monopole_height_mm": GEO.monopole_height_m * 1000,
            "steel_span_mm": GEO.steel_span_m * 1000,
            "steel_clearance_in_mm": GEO.steel_clearance_in_mm,
            "steel_clearance_out_mm": GEO.steel_clearance_out_mm,
            "quarter_wave_mm": GEO.quarter_wave_mm,
        },
        "pi_match_optimized_on": "steel_out",
        "pi_match": {"c1_pf": c1 * 1e12, "l_nh": ls * 1e9, "c2_pf": c2 * 1e12},
        "metrics": {
            "f_res_out_mhz": fres_out,
            "f_res_in_mhz": fres_in,
            "delta_f_res_mhz": delta_f,
            "s11_out_db_at_920_8": float(s11_out[i_sig]),
            "s11_in_db_at_920_8": float(s11_in[i_sig]),
            "delta_s11_db_at_920_8": s11_delta,
            "estimated_link_penalty_db": gain_penalty_db,
        },
        "assumptions": [
            "Helical modeled as 75 mm monopole over perfect ground (NEC) plus coupled parasitic mode.",
            "Steel pull-wire: 1.2 mm × 120 mm horizontal segment at 35 mm height.",
            "Pi-match components optimized with steel OUT (≥30 mm keep-out), then frozen for IN case.",
            "Plastic enclosure, PCB copper keep-out, and helix pitch not fully meshed (not HFSS).",
            "Hypothesis: metal within ~λ/10 (~33 mm @ 920 MHz) dominates detuning — IN case uses 5 mm.",
        ],
        "nec_note": (
            "PyNEC thin-wire runs show weak direct coupling for horizontal parasitic wire; "
            "coupled-resonator overlay calibrated for near-field steel interaction."
        ),
    }

    coupled_payload = {
        "freq_mhz": f_out,
        "s11_steel_out_db": [float(x) for x in s11_out],
        "s11_steel_in_db": [float(x) for x in s11_in],
        "z_steel_out_ohm": [{"r": float(z.real), "x": float(z.imag)} for z in z_out],
        "z_steel_in_ohm": [{"r": float(z.real), "x": float(z.imag)} for z in z_in],
    }

    nec_payload = {
        "freq_mhz": nec_freq_out,
        "s11_steel_out_db": nec_s11_out,
        "s11_steel_in_db": nec_s11_in,
        "f_res_out_mhz": resonant_frequency_mhz(nec_freq_out, nec_z_out),
        "f_res_in_mhz": resonant_frequency_mhz(nec_freq_in, nec_z_in),
    }

    (RESULTS / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (RESULTS / "coupled_s11.json").write_text(
        json.dumps(coupled_payload, indent=2), encoding="utf-8"
    )
    (RESULTS / "nec_reference.json").write_text(
        json.dumps(nec_payload, indent=2), encoding="utf-8"
    )

    with (RESULTS / "coupled_s11.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["freq_mhz", "s11_steel_out_db", "s11_steel_in_db"])
        for i, f in enumerate(f_out):
            w.writerow([f, float(s11_out[i]), float(s11_in[i])])

    print("Wrote", RESULTS)
    print("Δf_res (MHz):", round(delta_f, 2))
    print("ΔS11 @ 920.8 MHz (dB):", round(s11_delta, 2))
    print("Link penalty (dB):", round(gain_penalty_db, 2))


if __name__ == "__main__":
    main()
