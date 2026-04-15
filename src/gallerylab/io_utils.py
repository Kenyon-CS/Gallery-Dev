from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


JsonDict = dict[str, Any]


def load_yaml(path: str | Path) -> JsonDict:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


def write_yaml(path: str | Path, data: JsonDict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)


def load_json(path: str | Path) -> JsonDict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str | Path, data: JsonDict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
