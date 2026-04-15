from __future__ import annotations

import math
from statistics import pstdev
from typing import Any

JsonDict = dict[str, Any]


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def target_curve(raw_value: float, preferred: float, tolerance: float, floor: float = 0.7,
                 decay: float = 0.02, min_score: float = 0.0) -> float:
    """
    Convert a 0..100 raw metric to a 0..1 score using a simple target/tolerance curve.
    """
    distance = abs(raw_value - preferred)
    if distance <= tolerance:
        return 1.0 - ((distance / max(tolerance, 1e-9)) * (1.0 - floor))
    extra = distance - tolerance
    return max(min_score, floor - (extra * decay))


def weighted_average(items: list[tuple[float, float]]) -> float:
    total_weight = sum(weight for _, weight in items)
    if total_weight <= 0:
        return 0.0
    return sum(score * weight for score, weight in items) / total_weight


def distinct_ratio(values: list[str]) -> float:
    if not values:
        return 0.0
    return len(set(values)) / len(values)


def normalize_to_100(value: float) -> float:
    return clamp(value * 100.0, 0.0, 100.0)


def stddev_score(values: list[float], ideal_stddev: float, max_stddev: float) -> float:
    if len(values) < 2:
        return 0.0
    current = pstdev(values)
    delta = abs(current - ideal_stddev)
    score = 1.0 - (delta / max(max_stddev, 1e-9))
    return clamp(score, 0.0, 1.0)


def safe_area(artwork: JsonDict) -> float:
    return float(artwork.get("width_ft", 0.0)) * float(artwork.get("height_ft", 0.0))


def orientation_of(artwork: JsonDict) -> str:
    width = float(artwork.get("width_ft", 0.0))
    height = float(artwork.get("height_ft", 0.0))
    if width > height:
        return "landscape"
    if height > width:
        return "portrait"
    return "square"


def visual_mass(artwork: JsonDict) -> float:
    intensity = float(artwork.get("visual_intensity", 0.5) or 0.5)
    return safe_area(artwork) * max(intensity, 0.5)
