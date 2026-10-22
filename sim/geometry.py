"""Geometry constants for Sigfox ZP_V06 scaffold sensor (meters, SI)."""

from __future__ import annotations

from dataclasses import dataclass

F_SIGFOX_RC4_MHZ = 920.8
C0 = 299_792_458.0


@dataclass(frozen=True)
class SimGeometry:
    """NEC / coupled-model geometry (top-down + heights)."""

    # Helical approximated as 75 mm monopole over PCB ground (λ/4 ~ 81 mm electrical).
    monopole_height_m: float = 0.075
    monopole_radius_m: float = 0.0005
    monopole_base_z_m: float = 0.001

    # Steel Hall pull-wire: 1.2 mm Ø, ~120 mm span, passes antenna zone.
    steel_span_m: float = 0.12
    steel_radius_m: float = 0.0006
    steel_height_z_m: float = 0.035

    # Lateral clearance from monopole axis (y) to wire centerline.
    steel_clearance_in_mm: float = 5.0
    steel_clearance_out_mm: float = 32.0

    # Pi-match reference (module sees ~50 Ω after matching network).
    z0_ohm: float = 50.0

    @property
    def wavelength_m(self) -> float:
        return C0 / (F_SIGFOX_RC4_MHZ * 1e6)

    @property
    def quarter_wave_mm(self) -> float:
        return self.wavelength_m * 0.25 * 1000.0


GEO = SimGeometry()
