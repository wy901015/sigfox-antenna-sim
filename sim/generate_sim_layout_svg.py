#!/usr/bin/env python3
"""Export NEC/coupled-model geometry side view to assets/."""

from pathlib import Path

from geometry import GEO

OUT = Path(__file__).resolve().parents[1] / "assets"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    h_mm = GEO.monopole_height_m * 1000
    span_mm = GEO.steel_span_m * 1000
    z_mm = GEO.steel_height_z_m * 1000
    d_in = GEO.steel_clearance_in_mm
    d_out = GEO.steel_clearance_out_mm

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="900" height="520" viewBox="0 0 900 520">
  <style>
    .t {{ font: 700 18px sans-serif; fill:#0f172a; }}
    .l {{ font: 12px sans-serif; fill:#334155; }}
    .d {{ font: 11px sans-serif; fill:#64748b; }}
  </style>
  <rect width="900" height="520" fill="#f8fafc"/>
  <text x="28" y="36" class="t">EM simulation geometry (side view, Y–Z plane)</text>
  <text x="28" y="56" class="d">Monopole/helical axis at Y=0 · steel pull-wire horizontal · perfect ground (NEC)</text>

  <!-- ground -->
  <rect x="40" y="400" width="820" height="12" fill="#334155"/>
  <text x="48" y="430" class="l">PCB ground / enclosure floor (PEC in NEC)</text>

  <!-- monopole -->
  <line x1="200" y1="400" x2="200" y2="{400 - h_mm * 4}" stroke="#16a34a" stroke-width="4"/>
  <text x="210" y="{400 - h_mm * 2}" class="l">Helical / monopole ({h_mm:.0f} mm)</text>

  <!-- steel IN -->
  <line x1="120" y1="{400 - z_mm * 4}" x2="520" y2="{400 - z_mm * 4}" stroke="#dc2626" stroke-width="5"/>
  <text x="530" y="{400 - z_mm * 4 + 4}" class="l">Steel IN (d={d_in:.0f} mm)</text>

  <!-- steel OUT -->
  <line x1="120" y1="{400 - z_mm * 4 - 50}" x2="520" y2="{400 - z_mm * 4 - 50}" stroke="#94a3b8" stroke-width="4" stroke-dasharray="8 6"/>
  <text x="530" y="{400 - z_mm * 4 - 46}" class="l">Steel OUT (d={d_out:.0f} mm)</text>

  <!-- dimensions -->
  <line x1="200" y1="400" x2="200" y2="{400 - z_mm * 4}" stroke="#0ea5e9" stroke-width="1" marker-end="url(#a)"/>
  <text x="208" y="{400 - z_mm * 2}" class="d">z={z_mm:.0f} mm</text>
  <text x="48" y="480" class="d">Span {span_mm:.0f} mm · RC4 {920.8} MHz · λ/4≈{GEO.quarter_wave_mm:.0f} mm</text>
  <defs>
    <marker id="a" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#0ea5e9"/>
    </marker>
  </defs>
</svg>
"""
    (OUT / "sim-geometry.svg").write_text(svg, encoding="utf-8")
    print("Wrote", OUT / "sim-geometry.svg")


if __name__ == "__main__":
    main()
