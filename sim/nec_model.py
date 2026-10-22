"""PyNEC scene: helical ANT, steel cable path, spool, battery shell wires."""

from __future__ import annotations

import math
from typing import Iterable, List, Optional, Tuple

from PyNEC import nec_context

from cases import SimCase
from geometry import GEO, SimGeometry


def _add_helix(g, geo: SimGeometry) -> None:
    h = geo.helix
    g.helix(
        1,
        h.helix_segments,
        h.turn_pitch_m,
        h.axial_height_m,
        0.0,
        0.0,
        0.0,
        0.0,
        h.wire_radius_m,
    )


def _add_steel_cable(g, case: SimCase, geo: SimGeometry) -> None:
    s = geo.steel
    y = case.clearance_mm / 1000.0
    span = s.span_extended_m if case.reel == "extended" else s.span_reeled_m
    z = s.height_z_m
    r = s.braid_radius_m
    ox = s.corner_offset_x_m

    if case.orientation == "perpendicular":
        # Crosses antenna corner: dog-leg in X–Y (photo: wire sweeps across ANT zone).
        g.wire(2, 15, -span * 0.35, y, z, ox, y * 0.6, z, r, 1, 1)
        g.wire(2, 21, ox, y * 0.6, z, span * 0.45, y, z, r, 1, 1)
    else:
        # Short vertical braid segment beside helix (parallel to helix axis Z).
        g.wire(2, 17, ox, y, z, ox, y, z + 0.028, r, 1, 1)


def _add_spool(g, case: SimCase, geo: SimGeometry) -> None:
    if case.reel != "reeled":
        return
    sp = geo.spool
    n = 12
    for i in range(n):
        a0 = 2 * math.pi * i / n
        a1 = 2 * math.pi * (i + 1) / n
        x0 = sp.center_x_m + sp.ring_radius_m * math.cos(a0)
        y0 = sp.center_y_m + sp.ring_radius_m * math.sin(a0)
        x1 = sp.center_x_m + sp.ring_radius_m * math.cos(a1)
        y1 = sp.center_y_m + sp.ring_radius_m * math.sin(a1)
        g.wire(3, 1, x0, y0, sp.center_z_m, x1, y1, sp.center_z_m, sp.wire_radius_m, 1, 1)


def _add_battery(g, geo: SimGeometry) -> None:
    b = geo.battery
    x = b.center_x_m
    y0 = -b.width_y_m / 2
    y1 = b.width_y_m / 2
    z0 = b.base_z_m
    z1 = b.base_z_m + b.height_z_m
    rad = b.shell_radius_m
    g.wire(4, 7, x, y0, z0, x, y0, z1, rad, 1, 1)
    g.wire(4, 7, x, y1, z0, x, y1, z1, rad, 1, 1)
    g.wire(5, 7, x, y0, z1, x, y1, z1, rad, 1, 1)
    g.wire(5, 7, x, y0, z0, x, y1, z0, rad, 1, 1)


def run_nec_helix_battery_sweep(
    geo: SimGeometry = GEO,
    f_start_mhz: float = 880.0,
    f_stop_mhz: float = 960.0,
    n_points: int = 41,
) -> Tuple[List[float], List[complex], List[float]]:
    """Helix + LiPo shell only (no steel) — base Z(f) for hybrid model."""
    ctx = nec_context()
    g = ctx.get_geometry()
    _add_helix(g, geo)
    _add_battery(g, geo)
    return _finish_nec_sweep(ctx, f_start_mhz, f_stop_mhz, n_points)


def run_nec_scene_sweep(
    case: SimCase,
    geo: SimGeometry = GEO,
    f_start_mhz: float = 880.0,
    f_stop_mhz: float = 960.0,
    n_points: int = 41,
    include_battery: bool = True,
) -> Tuple[List[float], List[complex], List[float]]:
    ctx = nec_context()
    g = ctx.get_geometry()
    _add_helix(g, geo)
    _add_steel_cable(g, case, geo)
    _add_spool(g, case, geo)
    if include_battery:
        _add_battery(g, geo)
    return _finish_nec_sweep(ctx, f_start_mhz, f_stop_mhz, n_points)


def _finish_nec_sweep(
    ctx: nec_context,
    f_start_mhz: float,
    f_stop_mhz: float,
    n_points: int,
) -> Tuple[List[float], List[complex], List[float]]:

    ctx.geometry_complete(0)
    ctx.gn_card(-1, 0, 0, 0, 0, 0, 0, 0)
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
        freqs.append(f_hz / 1e6)
        zs.append(complex(ctx.get_impedance_real(i, 0), ctx.get_impedance_imag(i, 0)))
        gains.append(float(ctx.get_gain_max(i)))

    return freqs, zs, gains


def run_monopole_reference_sweep(
    geo: SimGeometry = GEO,
    f_start_mhz: float = 880.0,
    f_stop_mhz: float = 960.0,
    n_points: int = 33,
) -> Tuple[List[float], List[complex]]:
    """75 mm monopole reference only (legacy comparison)."""
    ctx = nec_context()
    g = ctx.get_geometry()
    g.wire(1, 41, 0, 0, 0.001, 0, 0, 0.075, 0.0005, 1, 1)
    ctx.geometry_complete(0)
    ctx.gn_card(-1, 0, 0, 0, 0, 0, 0, 0)
    ctx.ex_card(5, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0)
    df_hz = (f_stop_mhz - f_start_mhz) * 1e6 / (n_points - 1)
    f0_hz = f_start_mhz * 1e6
    ctx.fr_card(0, n_points, f0_hz, df_hz)
    ctx.rp_card(0, 1, 1, 0, 5, 0, 0, 0, 0, 1, 1, 1000, 0)
    freqs = []
    zs = []
    for i in range(n_points):
        freqs.append((f0_hz + i * df_hz) / 1e6)
        zs.append(complex(ctx.get_impedance_real(i, 0), ctx.get_impedance_imag(i, 0)))
    return freqs, zs


def s11_db(z: complex, z0: float = 50.0) -> float:
    gamma = (z - z0) / (z + z0)
    mag = abs(gamma)
    if mag <= 0:
        return -120.0
    return 20.0 * math.log10(mag)


def resonant_frequency_mhz(freqs: Iterable[float], zs: Iterable[complex]) -> float:
    f_list = list(freqs)
    z_list = list(zs)
    idx = min(range(len(z_list)), key=lambda i: abs(z_list[i].imag))
    return f_list[idx]
