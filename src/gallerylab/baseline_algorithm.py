from __future__ import annotations

from collections import defaultdict
from typing import Any

from .evaluators import LayoutEvaluator

JsonDict = dict[str, Any]


class BaselineWallGenerator:
    """
    Very simple baseline wall generator:
    - filters artworks that can fit
    - sorts by focal weight descending, then by width descending
    - lays them left to right using a fixed preferred gap
    """

    def __init__(self, preferred_gap_ft: float = 0.55, max_artworks: int = 8):
        self.preferred_gap_ft = preferred_gap_ft
        self.max_artworks = max_artworks

    def generate(self, wall: JsonDict, artworks: list[JsonDict], locked: list[JsonDict] | None = None) -> JsonDict:
        wall_width = float(wall.get("width_ft", 0.0))
        placements = [] if not locked else [dict(item) for item in locked]
        used_ids = {p["artwork_id"] for p in placements}

        x = 0.0
        if placements:
            placements = sorted(placements, key=lambda p: float(p.get("x_ft", 0.0)))
            last = placements[-1]
            last_width = next((float(a.get("width_ft", 0.0)) for a in artworks if a["id"] == last["artwork_id"]), 0.0)
            x = float(last.get("x_ft", 0.0)) + last_width + self.preferred_gap_ft

        candidates = [a for a in artworks if a["id"] not in used_ids and float(a.get("width_ft", 0.0)) <= wall_width]
        candidates.sort(key=lambda a: (-float(a.get("focal_weight", 0.0) or 0.0), -float(a.get("width_ft", 0.0)), a["id"]))

        for artwork in candidates:
            if len(placements) >= self.max_artworks:
                break
            width = float(artwork.get("width_ft", 0.0))
            if x + width > wall_width:
                continue
            placements.append({
                "artwork_id": artwork["id"],
                "x_ft": round(x, 2),
                "y_ft": 0.0,
                "locked": False,
            })
            x += width + self.preferred_gap_ft

        return {
            "wall_id": wall["id"],
            "width_ft": wall_width,
            "placements": sorted(placements, key=lambda p: float(p.get("x_ft", 0.0))),
        }


class BaselineWallEvaluator:
    def __init__(self, evaluator: LayoutEvaluator):
        self.evaluator = evaluator

    def evaluate(self, wall_layout: JsonDict) -> JsonDict:
        return self.evaluator.evaluate_wall(wall_layout)


class BaselineRoomGenerator:
    def __init__(self, wall_generator: BaselineWallGenerator, wall_evaluator: BaselineWallEvaluator):
        self.wall_generator = wall_generator
        self.wall_evaluator = wall_evaluator

    def generate(self, room: JsonDict, artworks: list[JsonDict], locked_by_wall: dict[str, list[JsonDict]]) -> JsonDict:
        remaining = artworks[:]
        walls_out: list[JsonDict] = []
        for wall in room.get("walls", []):
            locked = locked_by_wall.get(wall["id"], [])
            wall_layout = self.wall_generator.generate(wall, remaining, locked=locked)
            walls_out.append(wall_layout)
            used_ids = {p["artwork_id"] for p in wall_layout.get("placements", [])}
            remaining = [a for a in remaining if a["id"] not in used_ids]
        return {"room_id": room["id"], "walls": walls_out}


class BaselineRoomEvaluator:
    def __init__(self, evaluator: LayoutEvaluator):
        self.evaluator = evaluator

    def evaluate(self, room_layout: JsonDict) -> JsonDict:
        return self.evaluator.evaluate_room(room_layout)


class BaselineGalleryGenerator:
    def __init__(self, room_generator: BaselineRoomGenerator, room_evaluator: BaselineRoomEvaluator):
        self.room_generator = room_generator
        self.room_evaluator = room_evaluator

    def generate(self, art_data: JsonDict, gallery_data: JsonDict, scoring_data: JsonDict) -> JsonDict:
        artworks = art_data.get("artworks", [])[:]
        locked_by_wall = _collect_locked_positions(gallery_data)
        rooms_out: list[JsonDict] = []

        for room in gallery_data.get("rooms", []):
            room_layout = self.room_generator.generate(room, artworks, locked_by_wall)
            rooms_out.append(room_layout)
            used_ids = {p["artwork_id"] for wall in room_layout["walls"] for p in wall["placements"]}
            artworks = [a for a in artworks if a["id"] not in used_ids]

        return {
            "schema_version": "1.0",
            "show_id": gallery_data.get("show_id", "generated_show"),
            "title": f"Generated show for {gallery_data.get('gallery_name', 'gallery')}",
            "rooms": rooms_out,
        }


class BaselineGalleryEvaluator:
    def __init__(self, evaluator: LayoutEvaluator):
        self.evaluator = evaluator

    def evaluate(self, show_data: JsonDict) -> JsonDict:
        return self.evaluator.evaluate_gallery(show_data)



def _collect_locked_positions(gallery_data: JsonDict) -> dict[str, list[JsonDict]]:
    locked_by_wall: dict[str, list[JsonDict]] = defaultdict(list)
    partial_show = gallery_data.get("partial_show", {})
    for room in partial_show.get("rooms", []):
        for wall in room.get("walls", []):
            for placement in wall.get("placements", []):
                if placement.get("locked"):
                    locked_by_wall[wall["wall_id"]].append(placement)
    return locked_by_wall



def build_gallery_show(art_data: JsonDict, gallery_data: JsonDict, scoring_data: JsonDict) -> JsonDict:
    evaluator = LayoutEvaluator(art_data, gallery_data, scoring_data)
    wall_generator = BaselineWallGenerator(
        preferred_gap_ft=float(
            scoring_data.get("scoring", {})
            .get("criteria", {})
            .get("spacing_regularity", {})
            .get("algorithm", {})
            .get("params", {})
            .get("ideal_gap_ft", 0.55)
        )
    )
    wall_evaluator = BaselineWallEvaluator(evaluator)
    room_generator = BaselineRoomGenerator(wall_generator, wall_evaluator)
    room_evaluator = BaselineRoomEvaluator(evaluator)
    gallery_generator = BaselineGalleryGenerator(room_generator, room_evaluator)
    gallery_evaluator = BaselineGalleryEvaluator(evaluator)

    show_data = gallery_generator.generate(art_data, gallery_data, scoring_data)
    show_data["evaluation"] = gallery_evaluator.evaluate(show_data)
    return show_data
