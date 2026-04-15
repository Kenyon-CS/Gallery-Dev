from __future__ import annotations

import argparse
from pathlib import Path

from .baseline_algorithm import build_gallery_show
from .bridge import load_algorithm_from_python_file, run_algorithm_from_files
from .io_utils import write_json, write_yaml



def main() -> None:
    parser = argparse.ArgumentParser(description="Run a gallery layout algorithm on YAML inputs.")
    parser.add_argument("--art", required=True, help="Path to art.yaml")
    parser.add_argument("--gallery", required=True, help="Path to gallery.yaml")
    parser.add_argument("--scoring", required=True, help="Path to scoring.yaml")
    parser.add_argument("--output", required=True, help="Path to output show file (.yaml or .json)")
    parser.add_argument("--algorithm", help="Optional Python file containing build_gallery_show(...)")
    args = parser.parse_args()

    algorithm = build_gallery_show
    if args.algorithm:
        algorithm = load_algorithm_from_python_file(args.algorithm)

    show_data = run_algorithm_from_files(algorithm, args.art, args.gallery, args.scoring)
    output_path = Path(args.output)
    if output_path.suffix.lower() == ".json":
        write_json(output_path, show_data)
    else:
        write_yaml(output_path, show_data)

    print(f"Wrote show to {output_path}")
    if "evaluation" in show_data:
        print(f"Gallery score: {show_data['evaluation'].get('score', 0.0)}")


if __name__ == "__main__":
    main()
