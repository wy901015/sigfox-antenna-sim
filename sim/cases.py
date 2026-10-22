"""Simulation case matrix for steel pull-wire vs helical antenna."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from geometry import CableOrientation, ReelState


@dataclass(frozen=True)
class SimCase:
    case_id: str
    label_zh: str
    label_en: str
    clearance_mm: float
    orientation: CableOrientation = "perpendicular"
    reel: ReelState = "extended"
    is_baseline: bool = False


def all_cases() -> List[SimCase]:
    return [
        SimCase(
            "steel_out_32",
            "钢缆移出 ≥32 mm（基线）",
            "Steel OUT ≥32 mm (baseline)",
            32.0,
            is_baseline=True,
        ),
        SimCase(
            "steel_in_5",
            "钢缆靠近 ~5 mm（横穿·全伸出）",
            "Steel IN ~5 mm, crossing, extended",
            5.0,
        ),
        SimCase(
            "steel_15",
            "钢缆间距 15 mm",
            "Steel clearance 15 mm",
            15.0,
        ),
        SimCase(
            "steel_25",
            "钢缆间距 25 mm（近 λ/10）",
            "Steel clearance 25 mm (~λ/10)",
            25.0,
        ),
        SimCase(
            "steel_in_5_reeled",
            "5 mm + 收卷（线盘靠近）",
            "5 mm + cable reeled (spool near ANT)",
            5.0,
            reel="reeled",
        ),
        SimCase(
            "steel_in_5_parallel",
            "5 mm + 钢缆段 ∥ 螺旋轴",
            "5 mm + cable parallel to helix axis",
            5.0,
            orientation="parallel",
        ),
    ]


def baseline_case() -> SimCase:
    for c in all_cases():
        if c.is_baseline:
            return c
    raise RuntimeError("no baseline case")
