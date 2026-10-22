"""
Hybrid model: NEC helical Z(f) + coupling overlays (steel, spool, battery, enclosure).

Steel near-field mutual inductance ~ (5 mm / d)^3. Longer cable span raises parasitic
mode coupling. Reeled spool adds a second mutual path. Plastic enclosure modeled as
ε_eff and extra shunt capacitance on the helix resonance.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

from cases import SimCase
from geometry import F_SIGFOX_RC4_MHZ, GEO, SimGeometry


@dataclass
class CoupledParams:
    # Helix resonance overlay (NEC helix is electrically short; augment to ~920 MHz).
    r_ant_ohm: float = 13.0
    q_ant: float = 52.0
    f_ant_mhz: float = 917.5
    r_steel_ohm: float = 4.5
    q_steel: float = 26.0
    m_mutual_nh_at_5mm: float = 8.5
    cap_ff_at_5mm: float = 0.38
    reference_clearance_mm: float = 5.0
    parallel_axis_factor: float = 1.85
    reeled_spool_extra_nh: float = 1.45
    battery_mutual_nh: float = 0.0
    span_reference_m: float = 0.17
    span_coupling_exponent: float = 0.62
    nec_blend: float = 0.18


def _series_rlc(f_hz: np.ndarray, f0_mhz: float, r_ohm: float, q: float) -> np.ndarray:
    w0 = 2 * math.pi * f0_mhz * 1e6
    w = 2 * math.pi * f_hz
    l = q * r_ohm / w0
    c = 1.0 / (w0 * q * r_ohm)
    return r_ohm + 1j * (w * l - 1.0 / (w * c))


def _steel_resonance_mhz(span_m: float) -> float:
    """Longer exposed steel → lower parasitic resonance (order ~ half-wave / span)."""
    half_wave_mhz = 128.0
    return half_wave_mhz * (GEO.steel.span_extended_m / max(span_m, 0.05))


def clearance_detune_mhz(case: SimCase, baseline_clearance_mm: float = 32.0) -> float:
    """Resonance pull-down vs baseline keep-out (0 at ≥32 mm)."""
    d = case.clearance_mm
    if d >= baseline_clearance_mm - 0.5:
        base = 0.0
    else:
        frac = (baseline_clearance_mm - d) / baseline_clearance_mm
        base = -17.0 * frac ** 1.12
    if case.reel == "reeled":
        base -= 3.0
    if case.orientation == "parallel":
        base -= 2.0
    return base


def coupling_capacitance_f(case: SimCase, p: CoupledParams) -> float:
    d = max(case.clearance_mm, 1.0)
    d0 = p.reference_clearance_mm
    c_ff = p.cap_ff_at_5mm * (d0 / d) ** 2
    if case.orientation == "parallel":
        c_ff *= 1.4
    if case.reel == "reeled":
        c_ff *= 1.25
    return c_ff * 1e-15


def mutual_inductance_h(case: SimCase, p: CoupledParams) -> float:
    d = max(case.clearance_mm, 1.0)
    d0 = p.reference_clearance_mm
    m = p.m_mutual_nh_at_5mm * (d0 / d) ** 3
    if case.orientation == "parallel":
        m *= p.parallel_axis_factor
    span = GEO.steel.span_extended_m if case.reel == "extended" else GEO.steel.span_reeled_m
    m *= (span / p.span_reference_m) ** p.span_coupling_exponent
    if case.reel == "reeled":
        m += p.reeled_spool_extra_nh
    m += p.battery_mutual_nh
    return m * 1e-9


def apply_enclosure_loading(z: np.ndarray, f_hz: np.ndarray, geo: SimGeometry) -> np.ndarray:
    """Shunt capacitance from thin plastic shell (effective ε_r)."""
    enc = geo.enclosure
    w = 2 * math.pi * f_hz
    c_shunt = enc.extra_shunt_cap_ff * 1e-15 * math.sqrt(enc.epsilon_eff)
    z_par = 1.0 / (1.0 / z + 1j * w * c_shunt)
    scale = 1.0 / math.sqrt(enc.epsilon_eff)
    return z_par * (0.92 + 0.08 * scale)


def scene_impedance_from_nec(
    z_nec: np.ndarray,
    f_hz: np.ndarray,
    case: SimCase,
    geo: SimGeometry = GEO,
    p: CoupledParams = CoupledParams(),
) -> np.ndarray:
    """Blend NEC helix Z with tuned RLC + steel parasitic overlay."""
    f_ant = p.f_ant_mhz + clearance_detune_mhz(case)
    z_rlc = _series_rlc(f_hz, f_ant, p.r_ant_ohm, p.q_ant)
    z_base = apply_enclosure_loading(
        (1.0 - p.nec_blend) * z_rlc + p.nec_blend * z_nec, f_hz, geo
    )

    span = geo.steel.span_extended_m if case.reel == "extended" else geo.steel.span_reeled_m
    f_steel = _steel_resonance_mhz(span)
    zs = _series_rlc(f_hz, f_steel, p.r_steel_ohm, p.q_steel)
    m = mutual_inductance_h(case, p)
    w = 2 * math.pi * f_hz
    z_reflected = (w * m) ** 2 / zs
    c_near = coupling_capacitance_f(case, p)
    z_cap = 1.0 / (1.0 / (z_base + z_reflected) + 1j * w * c_near)
    return z_cap


def optimize_pi_match(
    z_ant: np.ndarray, f_hz: np.ndarray, f_match_hz: float, z0: float = 50.0
) -> Tuple[float, float, float]:
    from scipy.optimize import differential_evolution

    w_match = 2 * math.pi * f_match_hz
    idx = int(np.argmin(np.abs(f_hz - f_match_hz)))
    z_load = z_ant[idx]

    def z_matched(c1: float, ls: float, c2: float) -> complex:
        z = 1j / (w_match * c1) + z_load + 1j * w_match * ls
        return 1.0 / (1.0 / z + 1j * w_match * c2)

    def cost(x: np.ndarray) -> float:
        c1, ls, c2 = x
        if c1 <= 0 or c2 <= 0 or ls <= 0:
            return 1e6
        zin = z_matched(c1, ls, c2)
        gamma = (zin - z0) / (zin + z0)
        return float(abs(gamma) ** 2)

    bounds = [(0.3e-12, 6e-12), (2e-9, 25e-9), (0.3e-12, 6e-12)]
    res = differential_evolution(cost, bounds, seed=42, polish=True, maxiter=100)
    return float(res.x[0]), float(res.x[1]), float(res.x[2])


def apply_pi_match(
    z_ant: np.ndarray, f_hz: np.ndarray, c1: float, ls: float, c2: float
) -> np.ndarray:
    zin = np.zeros(len(f_hz), dtype=complex)
    for i, w in enumerate(2 * math.pi * f_hz):
        zl = z_ant[i]
        z = 1j / (w * c1) + zl + 1j * w * ls
        zin[i] = 1.0 / (1.0 / z + 1j * w * c2)
    return zin


def s11_curve(zin: np.ndarray, z0: float = 50.0) -> np.ndarray:
    gamma = (zin - z0) / (zin + z0)
    mag = np.clip(np.abs(gamma), 1e-6, 1.0)
    return 20.0 * np.log10(mag)


def find_f_res_mhz(freqs_mhz: List[float], s11_db: np.ndarray) -> float:
    idx = int(np.argmin(s11_db))
    return float(freqs_mhz[idx])
