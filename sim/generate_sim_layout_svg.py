#!/usr/bin/env python3
"""Export simulation geometry (helix + steel + battery) to assets/."""

from pathlib import Path

from geometry import GEO

OUT = Path(__file__).resolve().parents[1] / "assets"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    h = GEO.helix
    s = GEO.steel
    b = GEO.battery

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="960" height="560" viewBox="0 0 960 560">
  <style>
    .t {{ font: 700 18px sans-serif; fill:#0f172a; }}
    .l {{ font: 12px sans-serif; fill:#334155; }}
    .d {{ font: 11px sans-serif; fill:#64748b; }}
  </style>
  <rect width="960" height="560" fill="#f8fafc"/>
  <text x="28" y="34" class="t">Hybrid model geometry — ZP_V06 (side + top schematic)</text>
  <text x="28" y="54" class="d">Helix {h.axial_height_m*1000:.0f} mm × {h.outer_diameter_mm:.0f} mm OD · steel @ {s.height_z_m*1000:.0f} mm Z · LiPo @ {b.center_x_m*1000:.0f} mm</text>

  <text x="40" y="90" class="l">Side view (Y–Z)</text>
  <rect x="40" y="420" width="420" height="10" fill="#334155"/>
  <line x1="120" y1="420" x2="120" y2="{420 - h.axial_height_m*1000*3.2}" stroke="#16a34a" stroke-width="5"/>
  <text x="130" y="300" class="l">Helical ANT</text>
  <line x1="60" y1="{420 - s.height_z_m*1000*3.2}" x2="400" y2="{420 - s.height_z_m*1000*3.2}" stroke="#dc2626" stroke-width="4"/>
  <text x="410" y="{420 - s.height_z_m*1000*3.2}" class="l">Steel cable</text>
  <rect x="360" y="340" width="14" height="80" fill="#3b82f6" opacity="0.5" stroke="#1d4ed8"/>
  <text x="378" y="385" class="d">Battery</text>

  <text x="500" y="90" class="l">Top view (X–Y) — steel clearance d</text>
  <rect x="500" y="120" width="420" height="320" fill="#fff" stroke="#cbd5e1"/>
  <circle cx="560" cy="220" r="18" fill="none" stroke="#16a34a" stroke-width="2"/>
  <text x="545" y="225" class="d">ANT</text>
  <line x1="520" y1="160" x2="880" y2="160" stroke="#dc2626" stroke-width="3"/>
  <text x="620" y="150" class="l">Steel span (extended / reeled)</text>
  <line x1="560" y1="220" x2="560" y2="160" stroke="#0ea5e9" stroke-dasharray="4 3"/>
  <text x="568" y="190" class="d">d (5–32 mm)</text>
  <circle cx="720" cy="220" r="22" fill="none" stroke="#64748b" stroke-dasharray="5 4"/>
  <text x="700" y="260" class="d">Spool (reeled)</text>
</svg>
"""
    (OUT / "sim-geometry.svg").write_text(svg, encoding="utf-8")
    print("Wrote", OUT / "sim-geometry.svg")


if __name__ == "__main__":
    main()
