from __future__ import annotations

from typing import Any, Protocol

JsonDict = dict[str, Any]


class GalleryAlgorithm(Protocol):
    def __call__(self, art_data: JsonDict, gallery_data: JsonDict, scoring_data: JsonDict) -> JsonDict:
        """Return a show structure as a plain Python dictionary."""
