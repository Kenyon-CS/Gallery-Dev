from __future__ import annotations

from typing import Any

from .scoring_utils import (
    clamp,
    distinct_ratio,
    normalize_to_100,
    orientation_of,
    safe_area,
    target_curve,
    visual_mass,
    weighted_average,
)

JsonDict = dict[str, Any]


class Catalog:
    def __init__(self, art_data: JsonDict):
        artworks = art_data.get("artworks", [])
        self.by_id = {item["id"]: item for item in artworks}

    def get(self, artwork_id: str) -> JsonDict:
        return self.by_id[artwork_id]


class LayoutEvaluator:
    def __init__(self, art_data: JsonDict, gallery_data: JsonDict, scoring_data: JsonDict):
        self.catalog = Catalog(art_data)
        self.gallery_data = gallery_data
        self.scoring_data = scoring_data
        self.criteria = scoring_data.get("scoring", {}).get("criteria", {})
        self.constraints = scoring_data.get("scoring", {}).get("hard_constraints", {})

    def evaluate_wall(self, wall: JsonDict) -> JsonDict:
        placements = sorted(wall.get("placements", []), key=lambda p: float(p.get("x_ft", 0.0)))
        wall_width = float(wall.get("width_ft", 0.0))

        constraint_failures: list[str] = []
        min_artworks = self.constraints.get("min_artworks", {})
        max_artworks = self.constraints.get("max_artworks", {})
        min_gap_cfg = self.constraints.get("min_gap_ft", {})
        max_gap_cfg = self.constraints.get("max_gap_ft", {})

        if min_artworks.get("enabled") and len(placements) < int(min_artworks.get("value", 0)):
            constraint_failures.append("min_artworks")
        if max_artworks.get("enabled") and len(placements) > int(max_artworks.get("value", 10**9)):
            constraint_failures.append("max_artworks")

        gaps: list[float] = []
        occupied_width = 0.0
        previous_end = None
        visual_masses_left = 0.0
        visual_masses_right = 0.0
        centerline = wall_width / 2.0 if wall_width else 0.0

        artists: list[str] = []
        theme_pairs: list[float] = []
        years: list[int] = []
        areas: list[float] = []
        orientations: list[str] = []

        for idx, placement in enumerate(placements):
            artwork = self.catalog.get(placement["artwork_id"])
            start = float(placement.get("x_ft", 0.0))
            width = float(artwork.get("width_ft", 0.0))
            end = start + width
            occupied_width += width

            if start < 0 or end > wall_width:
                constraint_failures.append("stay_within_wall")

            if previous_end is not None:
                gap = start - previous_end
                gaps.append(gap)
                if min_gap_cfg.get("enabled") and gap < float(min_gap_cfg.get("value", 0.0)):
                    constraint_failures.append("min_gap_ft")
                if max_gap_cfg.get("enabled") and gap > float(max_gap_cfg.get("value", 9999.0)):
                    constraint_failures.append("max_gap_ft")
                if gap < 0:
                    constraint_failures.append("no_overlap")

            center = start + width / 2.0
            vmass = visual_mass(artwork)
            if center <= centerline:
                visual_masses_left += vmass
            else:
                visual_masses_right += vmass

            artists.append(str(artwork.get("artist", "unknown")))
            years.append(int(artwork.get("year", 0) or 0))
            areas.append(safe_area(artwork))
            orientations.append(orientation_of(artwork))

            if idx > 0:
                prev = self.catalog.get(placements[idx - 1]["artwork_id"])
                theme_pairs.append(self._theme_similarity(prev, artwork))

            previous_end = end

        raw_metrics = {
            "wall_utilization": normalize_to_100(occupied_width / wall_width) if wall_width else 0.0,
            "artist_variety": normalize_to_100(distinct_ratio(artists)),
            "spacing_regularity": self._spacing_regularity(gaps),
            "thematic_cohesion": normalize_to_100(sum(theme_pairs) / len(theme_pairs)) if theme_pairs else 0.0,
            "period_adjacency": self._period_flow(years),
            "visual_balance": self._visual_balance(visual_masses_left, visual_masses_right),
            "size_variety": self._size_variety(areas, orientations),
            "focal_point": self._focal_point_score(placements, wall_width),
        }

        criterion_scores: dict[str, dict[str, float]] = {}
        weighted_items: list[tuple[float, float]] = []
        for criterion_name, criterion_cfg in self.criteria.items():
            raw = raw_metrics.get(criterion_name)
            if raw is None:
                continue
            curve = criterion_cfg.get("scoring_curve", {})
            score = target_curve(
                raw_value=raw,
                preferred=float(criterion_cfg.get("preferred_value", 50.0)),
                tolerance=float(criterion_cfg.get("tolerance", 15.0)),
                floor=float(curve.get("in_tolerance_floor", 0.7)),
                decay=float(curve.get("out_of_tolerance_decay", 0.02)),
                min_score=float(curve.get("min_score", 0.0)),
            )
            importance = float(criterion_cfg.get("importance", 1.0))
            criterion_scores[criterion_name] = {"raw": round(raw, 2), "score": round(score, 4), "importance": importance}
            weighted_items.append((score, importance))

        aggregate = weighted_average(weighted_items)
        if constraint_failures:
            aggregate = 0.0

        return {
            "scope": "wall",
            "wall_id": wall.get("wall_id"),
            "score": round(aggregate, 4),
            "failed_constraints": sorted(set(constraint_failures)),
            "criteria": criterion_scores,
        }

    def evaluate_room(self, room: JsonDict) -> JsonDict:
        wall_results = [self.evaluate_wall(wall) for wall in room.get("walls", [])]
        if not wall_results:
            return {"scope": "room", "room_id": room.get("room_id"), "score": 0.0, "walls": []}
        room_score = sum(result["score"] for result in wall_results) / len(wall_results)
        return {
            "scope": "room",
            "room_id": room.get("room_id"),
            "score": round(room_score, 4),
            "walls": wall_results,
        }

    def evaluate_gallery(self, show_data: JsonDict) -> JsonDict:
        room_results = [self.evaluate_room(room) for room in show_data.get("rooms", [])]
        if not room_results:
            return {"scope": "gallery", "score": 0.0, "rooms": []}
        gallery_score = sum(result["score"] for result in room_results) / len(room_results)
        return {
            "scope": "gallery",
            "score": round(gallery_score, 4),
            "rooms": room_results,
        }

    def _spacing_regularity(self, gaps: list[float]) -> float:
        if not gaps:
            return 0.0
        ideal_gap = float(
            self.criteria.get("spacing_regularity", {})
            .get("algorithm", {})
            .get("params", {})
            .get("ideal_gap_ft", 0.55)
        )
        avg_deviation = sum(abs(g - ideal_gap) for g in gaps) / len(gaps)
        raw = max(0.0, 100.0 - avg_deviation * 100.0)
        return clamp(raw, 0.0, 100.0)

    def _theme_similarity(self, a: JsonDict, b: JsonDict) -> float:
        table = (
            self.scoring_data.get("scoring", {})
            .get("pairwise_tables", {})
            .get("theme_similarity", {})
        )
        default = float(table.get("default_similarity", 0.1))
        pairs = table.get("pairs", {})
        key1 = f"{a.get('primary_theme', 'unknown')}|{b.get('primary_theme', 'unknown')}"
        key2 = f"{b.get('primary_theme', 'unknown')}|{a.get('primary_theme', 'unknown')}"
        return float(pairs.get(key1, pairs.get(key2, default)))

    def _period_flow(self, years: list[int]) -> float:
        if len(years) < 2:
            return 0.0
        bins = (
            self.criteria.get("period_adjacency", {})
            .get("algorithm", {})
            .get("params", {})
            .get("year_bins", [])
        )
        scores: list[float] = []
        for i in range(1, len(years)):
            delta = abs(years[i] - years[i - 1])
            for band in bins:
                if delta <= int(band.get("max_diff", 10000)):
                    scores.append(float(band.get("score", 0.05)))
                    break
        return normalize_to_100(sum(scores) / len(scores)) if scores else 0.0

    def _visual_balance(self, left: float, right: float) -> float:
        total = left + right
        if total <= 0:
            return 0.0
        imbalance = abs(left - right) / total
        return normalize_to_100(1.0 - imbalance)

    def _size_variety(self, areas: list[float], orientations: list[str]) -> float:
        if len(areas) < 2:
            return 0.0
        distinct_orientations = len(set(orientations)) / 3.0
        area_min = min(areas)
        area_max = max(areas)
        area_spread = 0.0 if area_max <= 0 else (area_max - area_min) / area_max
        combined = 0.7 * area_spread + 0.3 * distinct_orientations
        return normalize_to_100(combined)

    def _focal_point_score(self, placements: list[JsonDict], wall_width: float) -> float:
        if not placements or wall_width <= 0:
            return 0.0
        best = None
        best_weight = -1.0
        for placement in placements:
            artwork = self.catalog.get(placement["artwork_id"])
            weight = float(artwork.get("focal_weight", 0.0) or 0.0)
            if weight > best_weight:
                best = (placement, artwork)
                best_weight = weight
        if best is None:
            return 0.0
        placement, artwork = best
        center = float(placement.get("x_ft", 0.0)) + float(artwork.get("width_ft", 0.0)) / 2.0
        zone_half = float(
            self.criteria.get("focal_point", {})
            .get("algorithm", {})
            .get("params", {})
            .get("center_zone_half_width_ft", 1.25)
        )
        wall_center = wall_width / 2.0
        distance = abs(center - wall_center)
        raw = 100.0 if distance <= zone_half else max(0.0, 100.0 - (distance - zone_half) * 20.0)
        return clamp(raw, 0.0, 100.0)
