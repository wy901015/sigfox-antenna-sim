"""Geometry for ZP_V06 scaffold sensor — documented from photos / floorplan."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

F_SIGFOX_RC4_MHZ = 920.8
C0 = 299_792_458.0

CableOrientation = Literal["perpendicular", "parallel"]
ReelState = Literal["extended", "reeled"]


@dataclass(frozen=True)
class HelixSpec:
    """
    PCB-mounted Sigfox helical (WSSFM10R4 ANT pad), photo scale on ZP_V06.

    ~10 mm OD, ~20 mm height, ~5–6 turns, 0.5 mm wire — electrical length
    targets λ/4 ≈ 81 mm along wire (vendor / silk notes).
    """

    wire_radius_m: float = 0.00025
    axial_height_m: float = 0.022
    turn_pitch_m: float = 0.004
    helix_segments: int = 35
    base_z_m: float = 0.0015
    # NEC helix API: axis along Z at origin (PCB corner keep-out).

    @property
    def outer_diameter_mm(self) -> float:
        return 10.0

    @property
    def approximate_wire_length_mm(self) -> float:
        turns = self.axial_height_m / self.turn_pitch_m
        r = self.outer_diameter_mm / 2000.0
        return turns * 2 * 3.14159 * r * 1000 + self.axial_height_m * 1000


@dataclass(frozen=True)
class SteelCableSpec:
    """Braided Hall pull-wire (steel), floorplan: crosses ANT zone."""

    braid_radius_m: float = 0.00065
    height_z_m: float = 0.017
    span_extended_m: float = 0.17
    span_reeled_m: float = 0.075
    corner_offset_x_m: float = 0.008


@dataclass(frozen=True)
class SpoolSpec:
    """Short metal reel / Hall spool near cable exit (simplified ring)."""

    center_x_m: float = 0.028
    center_y_m: float = 0.010
    center_z_m: float = 0.020
    ring_radius_m: float = 0.011
    wire_radius_m: float = 0.0008


@dataclass(frozen=True)
class BatterySpec:
    """LiPo 3000 mAh block to the right of PCB (~45 mm from ANT axis)."""

    center_x_m: float = 0.048
    center_y_m: float = 0.0
    width_y_m: float = 0.034
    height_z_m: float = 0.052
    base_z_m: float = 0.008
    shell_radius_m: float = 0.0004


@dataclass(frozen=True)
class EnclosureSpec:
    """
    Thin ABS/PC enclosure — not meshed in NEC; effective medium on helix.

    ε_eff ≈ 1.4–1.5 (thin shell + mostly air) lowers resonance slightly and
    adds shunt capacitance (~2–4 MHz in this model).
    """

    epsilon_eff: float = 1.45
    extra_shunt_cap_ff: float = 0.08


@dataclass(frozen=True)
class SimGeometry:
    helix: HelixSpec = HelixSpec()
    steel: SteelCableSpec = SteelCableSpec()
    spool: SpoolSpec = SpoolSpec()
    battery: BatterySpec = BatterySpec()
    enclosure: EnclosureSpec = EnclosureSpec()
    z0_ohm: float = 50.0
    baseline_clearance_mm: float = 32.0

    @property
    def wavelength_m(self) -> float:
        return C0 / (F_SIGFOX_RC4_MHZ * 1e6)

    @property
    def quarter_wave_mm(self) -> float:
        return self.wavelength_m * 0.25 * 1000.0

    @property
    def lambda_over_10_mm(self) -> float:
        return self.wavelength_m / 10.0 * 1000.0


GEO = SimGeometry()
