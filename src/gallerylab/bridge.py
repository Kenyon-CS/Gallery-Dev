from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any, Callable

from .io_utils import load_json, load_yaml, write_json, write_yaml

JsonDict = dict[str, Any]



def run_algorithm_from_data(algorithm: Callable[[JsonDict, JsonDict, JsonDict], JsonDict],
                            art_data: JsonDict,
                            gallery_data: JsonDict,
                            scoring_data: JsonDict) -> JsonDict:
    return algorithm(art_data, gallery_data, scoring_data)



def run_algorithm_from_files(algorithm: Callable[[JsonDict, JsonDict, JsonDict], JsonDict],
                             art_path: str | Path,
                             gallery_path: str | Path,
                             scoring_path: str | Path) -> JsonDict:
    art_data = load_yaml(art_path)
    gallery_data = load_yaml(gallery_path)
    scoring_data = load_yaml(scoring_path)
    return algorithm(art_data, gallery_data, scoring_data)



def load_algorithm_from_python_file(path: str | Path, function_name: str = "build_gallery_show"):
    path = Path(path)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not import algorithm module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        return getattr(module, function_name)
    except AttributeError as exc:
        raise AttributeError(f"{path} does not define {function_name}(...)") from exc
