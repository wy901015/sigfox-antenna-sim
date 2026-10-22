#!/usr/bin/env python3
"""Run multi-case helical + steel scene study; write sim/results/."""

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

from cases import all_cases, baseline_case  # noqa: E402
from coupled_model import (  # noqa: E402
    apply_pi_match,
    find_f_res_mhz,
    optimize_pi_match,
    scene_impedance_from_nec,
    s11_curve,
)
from geometry import F_SIGFOX_RC4_MHZ, GEO  # noqa: E402
from nec_model import (  # noqa: E402
    resonant_frequency_mhz,
    run_monopole_reference_sweep,
    run_nec_helix_battery_sweep,
    run_nec_scene_sweep,
    s11_db,
)

RESULTS = ROOT / "results"
CASES_DIR = RESULTS / "cases"


def _index_sigfox(freqs_mhz: list[float]) -> int:
    return int(np.argmin(np.abs(np.array(freqs_mhz) - F_SIGFOX_RC4_MHZ)))


def main() -> None:
    f_start, f_stop, n = 880.0, 960.0, 81
    cases = all_cases()
    baseline = baseline_case()
    CASES_DIR.mkdir(parents=True, exist_ok=True)

    nec_freq, z_helix_nec, _ = run_nec_helix_battery_sweep(n_points=n)
    f_hz = np.array(nec_freq) * 1e6
    z_nec_arr = np.array(z_helix_nec)

    case_results = []
    s11_by_case: dict[str, list[float]] = {}
    z_store: dict[str, list] = {}

    z_baseline = scene_impedance_from_nec(z_nec_arr, f_hz, baseline)
    c1, ls, c2 = optimize_pi_match(z_baseline, f_hz, F_SIGFOX_RC4_MHZ * 1e6, GEO.z0_ohm)

    zin_base = apply_pi_match(z_baseline, f_hz, c1, ls, c2)
    s11_base = s11_curve(zin_base, GEO.z0_ohm)
    i_sig = _index_sigfox(nec_freq)
    base_f_res = find_f_res_mhz(nec_freq, s11_base)
    base_s11_sig = float(s11_base[i_sig])
    gamma_base = abs((zin_base[i_sig] - GEO.z0_ohm) / (zin_base[i_sig] + GEO.z0_ohm))
    power_base = 1.0 - gamma_base**2

    for case in cases:
        nf, nz, gains = run_nec_scene_sweep(case, n_points=n)
        z_scene = scene_impedance_from_nec(z_nec_arr, f_hz, case)
        zin = apply_pi_match(z_scene, f_hz, c1, ls, c2)
        s11 = s11_curve(zin, GEO.z0_ohm)
        f_res = find_f_res_mhz(nf, s11)
        s11_sig = float(s11[i_sig])
        gamma = abs((zin[i_sig] - GEO.z0_ohm) / (zin[i_sig] + GEO.z0_ohm))
        power = 1.0 - gamma**2
        penalty = 10.0 * math.log10(max(power_base, 1e-12) / max(power, 1e-12))

        row = {
            "case_id": case.case_id,
            "label_zh": case.label_zh,
            "label_en": case.label_en,
            "clearance_mm": case.clearance_mm,
            "orientation": case.orientation,
            "reel": case.reel,
            "f_res_mhz": f_res,
            "s11_db_at_920_8": s11_sig,
            "delta_f_res_mhz_vs_baseline": f_res - base_f_res,
            "delta_s11_db_at_920_8_vs_baseline": s11_sig - base_s11_sig,
            "estimated_link_penalty_db_vs_baseline": penalty,
            "nec_f_res_mhz_raw": resonant_frequency_mhz(nf, nz),
        }
        case_results.append(row)
        s11_by_case[case.case_id] = [float(x) for x in s11]
        z_store[case.case_id] = [{"r": float(z.real), "x": float(z.imag)} for z in z_scene]

        (CASES_DIR / f"{case.case_id}.json").write_text(
            json.dumps(
                {
                    "case": row,
                    "freq_mhz": nf,
                    "s11_matched_db": s11_by_case[case.case_id],
                    "z_scene_ohm": z_store[case.case_id],
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    # Monopole NEC reference (legacy)
    mono_f, mono_z = run_monopole_reference_sweep(n_points=33)

    helix = GEO.helix
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model_version": 2,
        "device": {
            "module": "WSSFM10R4AT / SFM10R4",
            "pcb": "ZP_V06",
            "tx_mhz": F_SIGFOX_RC4_MHZ,
            "band": "Sigfox RC4",
        },
        "geometry_documentation": {
            "helix_outer_diameter_mm": helix.outer_diameter_mm,
            "helix_axial_height_mm": helix.axial_height_m * 1000,
            "helix_pitch_mm": helix.turn_pitch_m * 1000,
            "helix_wire_diameter_mm": helix.wire_radius_m * 2000,
            "helix_approx_wire_length_mm": helix.approximate_wire_length_mm,
            "steel_braid_diameter_mm": GEO.steel.braid_radius_m * 2000,
            "steel_height_mm": GEO.steel.height_z_m * 1000,
            "steel_span_extended_mm": GEO.steel.span_extended_m * 1000,
            "steel_span_reeled_mm": GEO.steel.span_reeled_m * 1000,
            "spool_ring_radius_mm": GEO.spool.ring_radius_m * 1000,
            "battery_center_x_mm": GEO.battery.center_x_m * 1000,
            "enclosure_epsilon_eff": GEO.enclosure.epsilon_eff,
            "quarter_wave_mm": GEO.quarter_wave_mm,
            "lambda_over_10_mm": GEO.lambda_over_10_mm,
        },
        "baseline_case_id": baseline.case_id,
        "pi_match_optimized_on": baseline.case_id,
        "pi_match": {"c1_pf": c1 * 1e12, "l_nh": ls * 1e9, "c2_pf": c2 * 1e12},
        "cases": case_results,
        "assumptions": [
            "Primary radiator: PyNEC helix (22 mm × 10 mm OD, 4 mm pitch) on PEC ground.",
            "Steel: 1.3 mm braided cable, dog-leg across ANT corner; optional vertical segment (parallel case).",
            "Reeled: 12-segment metal ring spool + shorter 75 mm span.",
            "Battery: LiPo shell wires at 48 mm from ANT; fixed in all cases.",
            f"Plastic: ε_eff={GEO.enclosure.epsilon_eff}, extra shunt C — not full 3D dielectric mesh.",
            "π-match optimized on baseline (steel OUT 32 mm), frozen for all cases.",
            "Still approximate — confirm with VNA in closed plastic housing.",
        ],
    }

    coupled_payload = {
        "freq_mhz": nec_freq,
        "baseline_case_id": baseline.case_id,
        "cases": [
            {
                "case_id": c.case_id,
                "label_zh": c.label_zh,
                "label_en": c.label_en,
                "s11_matched_db": s11_by_case[c.case_id],
            }
            for c in cases
        ],
    }

    nec_payload = {
        "freq_mhz": nec_freq,
        "helix_battery_raw_s11_db": [s11_db(z) for z in z_helix_nec],
        "note": "Raw 50 Ω S11 from NEC helix + battery (no steel, no pi-match).",
    }

    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (RESULTS / "coupled_s11.json").write_text(
        json.dumps(coupled_payload, indent=2), encoding="utf-8"
    )
    (RESULTS / "nec_reference.json").write_text(
        json.dumps(nec_payload, indent=2), encoding="utf-8"
    )
    (RESULTS / "monopole_reference.json").write_text(
        json.dumps(
            {
                "freq_mhz": mono_f,
                "z_ohm": [{"r": float(z.real), "x": float(z.imag)} for z in mono_z],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    with (RESULTS / "cases_comparison.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=list(case_results[0].keys()),
        )
        w.writeheader()
        w.writerows(case_results)

    with (RESULTS / "coupled_s11.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        header = ["freq_mhz"] + [c.case_id for c in cases]
        w.writerow(header)
        for i, f in enumerate(nec_freq):
            w.writerow([f] + [s11_by_case[c.case_id][i] for c in cases])

    print("Wrote", RESULTS, f"({len(cases)} cases)")
    worst = max(
        (r for r in case_results if r["case_id"] != baseline.case_id),
        key=lambda r: r["delta_s11_db_at_920_8_vs_baseline"],
    )
    print("Worst ΔS11:", worst["case_id"], worst["delta_s11_db_at_920_8_vs_baseline"])


if __name__ == "__main__":
    main()
