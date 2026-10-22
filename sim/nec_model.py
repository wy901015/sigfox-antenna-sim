"""Thin-wire NEC-2++ (PyNEC) model: monopole + optional steel pull-wire."""

from __future__ import annotations

import math
from typing import Iterable, List, Optional, Tuple

from PyNEC import nec_context

from geometry import GEO, SimGeometry


def _mhz(hz: float) -> float:
    return hz / 1e6


def run_nec_sweep(
    steel_clearance_mm: Optional[float],
    geo: SimGeometry = GEO,
    f_start_mhz: float = 880.0,
    f_stop_mhz: float = 960.0,
    n_points: int = 33,
) -> Tuple[List[float], List[complex], List[float]]:
    """
    Return (freq_mhz, z_antenna_ohm, gain_max_dbi) per frequency.

    steel_clearance_mm: lateral distance monopole ↔ steel wire; None = no steel.
    """
    if n_points < 2:
        raise ValueError("n_points must be >= 2")

    ctx = nec_context()
    g = ctx.get_geometry()

    g.wire(
        1,
        41,
        0.0,
        0.0,
        geo.monopole_base_z_m,
        0.0,
        0.0,
        geo.monopole_height_m,
        geo.monopole_radius_m,
        1,
        1,
    )

    if steel_clearance_mm is not None:
        y = steel_clearance_mm / 1000.0
        half = geo.steel_span_m / 2.0
        g.wire(
            2,
            41,
            -half,
            y,
            geo.steel_height_z_m,
            half,
            y,
            geo.steel_height_z_m,
            geo.steel_radius_m,
            1,
            1,
        )

    ctx.geometry_complete(0)
    ctx.gn_card(-1, 0, 0, 0, 0, 0, 0, 0)
    # Voltage source on tag 1, segment 1 (integers required by PyNEC bindings).
    ctx.ex_card(5, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0)

    df_hz = (f_stop_mhz - f_start_mhz) * 1e6 / (n_points - 1)
    f0_hz = f_start_mhz * 1e6
    ctx.fr_card(0, n_points, f0_hz, df_hz)
    ctx.rp_card(0, 37, 1, 0, 5, 0, 0, 0, 0, 5, 1, 1000, 0)

    freqs: List[float] = []
    zs: List[complex] = []
    gains: List[float] = []
    for i in range(n_points):
        f_hz = f0_hz + i * df_hz
        freqs.append(_mhz(f_hz))
        z = complex(ctx.get_impedance_real(i, 0), ctx.get_impedance_imag(i, 0))
        zs.append(z)
        gains.append(float(ctx.get_gain_max(i)))

    return freqs, zs, gains


def s11_db(z: complex, z0: float = 50.0) -> float:
    gamma = (z - z0) / (z + z0)
    mag = abs(gamma)
    if mag <= 0:
        return -120.0
    return 20.0 * math.log10(mag)


def resonant_frequency_mhz(freqs: Iterable[float], zs: Iterable[complex]) -> float:
    """Frequency where |Im{Z}| is minimum (series resonance proxy)."""
    f_list = list(freqs)
    z_list = list(zs)
    idx = min(range(len(z_list)), key=lambda i: abs(z_list[i].imag))
    return f_list[idx]
