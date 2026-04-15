"""
Student algorithm template.

The React system can eventually upload a file like this, import build_gallery_show,
and pass art/gallery/scoring as JSON objects. For local testing, the CLI can run it
against YAML files.
"""

from typing import Any

from gallerylab.baseline_algorithm import build_gallery_show as baseline_build_gallery_show

JsonDict = dict[str, Any]



def build_gallery_show(art_data: JsonDict, gallery_data: JsonDict, scoring_data: JsonDict) -> JsonDict:
    """
    Replace this body with your own algorithm.

    Contract:
      - Inputs are plain dict/list structures parsed from YAML or JSON.
      - Return a show dict with rooms -> walls -> placements.
      - Each placement must contain at least: artwork_id, x_ft.
    """
    return baseline_build_gallery_show(art_data, gallery_data, scoring_data)
