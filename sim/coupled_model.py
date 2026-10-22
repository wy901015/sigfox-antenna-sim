"""
Coupled-resonator overlay for steel pull-wire near a quarter-wave helical.

PyNEC thin-wire runs often under-estimate horizontal parasitic coupling when the
enclosure, PCB ground, and helix pitch are omitted. This model adds a physically
motivated mutual impedance between:

  - Antenna mode: series RLC tuned near 920.8 MHz (helical over ground)
  - Steel cable mode: parasitic half-wave-ish wire (~120 mm) with loss

Mutual coupling scales ~ (1/d^3) in the reactive near field (d << λ).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np

from geometry import GEO, F_SIGFOX_RC4_MHZ


@dataclass
class CoupledParams:
    f0_mhz: float = F_SIGFOX_RC4_MHZ
    r_ant_ohm: float = 12.0
    q_ant: float = 45.0
    r_steel_ohm: float = 4.0
    q_steel: float = 28.0
    f_steel_mhz: float = 922.0
    # Mutual coupling at 5 mm lateral clearance (reactive near-field, ~1/d^3 scaling).
    m_mutual_nh_at_5mm: float = 3.0
    reference_clearance_mm: float = 5.0


def _series_rlc(f_hz: np.ndarray, f0_mhz: float, r_ohm: float, q: float) -> np.ndarray:
    """Series RLC with resonance Z = R at f0 (Q = ω0 L / R)."""
    w0 = 2 * math.pi * f0_mhz * 1e6
    w = 2 * math.pi * f_hz
    l = q * r_ohm / w0
    c = 1.0 / (w0 * q * r_ohm)
    return r_ohm + 1j * (w * l - 1.0 / (w * c))


def _antenna_impedance(f_hz: np.ndarray, p: CoupledParams) -> np.ndarray:
    return _series_rlc(f_hz, p.f0_mhz, p.r_ant_ohm, p.q_ant)


def _steel_impedance(f_hz: np.ndarray, p: CoupledParams) -> np.ndarray:
    return _series_rlc(f_hz, p.f_steel_mhz, p.r_steel_ohm, p.q_steel)


def mutual_inductance_h(clearance_mm: float, p: CoupledParams) -> float:
    d = max(clearance_mm, 1.0)
    d0 = p.reference_clearance_mm
    m_nh = p.m_mutual_nh_at_5mm * (d0 / d) ** 3
    return m_nh * 1e-9


def coupled_impedance(
    f_hz: np.ndarray, clearance_mm: float, p: CoupledParams = CoupledParams()
) -> np.ndarray:
    za = _antenna_impedance(f_hz, p)
    zs = _steel_impedance(f_hz, p)
    m = mutual_inductance_h(clearance_mm, p)
    w = 2 * math.pi * f_hz
    # Parasitic steel wire in short-circuit (thin wire): Z_ref = (ωM)^2 / Z_steel
    z_reflected = (w * m) ** 2 / zs
    return za + z_reflected


def optimize_pi_match(
    z_ant: np.ndarray, f_hz: np.ndarray, f_match_hz: float, z0: float = 50.0
) -> Tuple[float, float, float]:
    """Find shunt C (F), series L (H), shunt C2 (F) for match at f_match_hz."""
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
    res = differential_evolution(cost, bounds, seed=42, polish=True, maxiter=80)
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


def run_coupled_sweep(
    clearance_mm: float,
    f_start_mhz: float = 880.0,
    f_stop_mhz: float = 960.0,
    n_points: int = 81,
    p: CoupledParams = CoupledParams(),
) -> Tuple[List[float], np.ndarray]:
    f_hz = np.linspace(f_start_mhz, f_stop_mhz, n_points) * 1e6
    z = coupled_impedance(f_hz, clearance_mm, p)
    return [float(x) for x in f_hz / 1e6], z
