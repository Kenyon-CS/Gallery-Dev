# Gallery Algorithm Starter Project

A complete Python starter project for developing and testing gallery-layout algorithms locally before plugging them into a React upload-and-run system.

The design goal is simple:

- students write a Python function that receives **three plain Python dictionaries**:
  - `art_data`
  - `gallery_data`
  - `scoring_data`
- their function returns a **show structure** as a dictionary
- the test bed can read YAML locally, convert it to dictionaries/lists, call student code, and write the resulting show back out as YAML or JSON

This mirrors the eventual React-side workflow, where uploaded YAML files can be parsed to JSON and sent into a Python runtime or service.

The project already includes a very basic working algorithm split into the six layers you wanted:

1. wall generator
2. wall evaluator
3. room generator
4. room evaluator
5. gallery generator
6. gallery evaluator

The included baseline uses only a few simple scoring ideas as placeholders:

- spacing regularity
- artist variety
- wall utilization
- visual balance
- thematic cohesion
- focal point placement

It is intentionally modest. It works, it is readable, and it gives students something concrete to replace.

---
```
                          ┌──────────────────────────────┐
                          │        YAML INPUT FILES      │
                          │                              │
                          │  art.yaml                    │
                          │  gallery.yaml                │
                          │  scoring.yaml                │
                          └─────────────┬────────────────┘
                                        │
                                        ▼
                          ┌──────────────────────────────┐
                          │        YAML LOADER           │
                          │   (utils/yaml_loader.py)     │
                          │                              │
                          │ Converts YAML → Python dicts │
                          └─────────────┬────────────────┘
                                        │
                                        ▼
                          ┌──────────────────────────────┐
                          │      TEST HARNESS / CLI      │
                          │        (main.py)             │
                          │                              │
                          │  - Loads data                │
                          │  - Calls algorithm           │
                          │  - Handles debug/output      │
                          └─────────────┬────────────────┘
                                        │
                                        ▼
                ┌────────────────────────────────────────────────┐
                │        STUDENT ALGORITHM ENTRY POINT           │
                │                                                │
                │  build_gallery_show(art, gallery, scoring)     │
                │                                                │
                └─────────────┬──────────────────────────────────┘
                              │
                              ▼
        ┌────────────────────────────────────────────────────────────┐
        │                  ALGORITHM PIPELINE                        │
        │                                                            │
        │   ┌────────────────────────────────────────────────────┐   │
        │   │              Gallery Generator                     │   │
        │   │   (splits work across rooms)                       │   │
        │   └─────────────┬──────────────────────────────────────┘   │
        │                 │                                          │
        │                 ▼                                          │
        │   ┌────────────────────────────────────────────────────┐   │
        │   │               Room Generator                       │   │
        │   │   (assigns artworks to walls)                      │   │
        │   └─────────────┬──────────────────────────────────────┘   │
        │                 │                                          │
        │                 ▼                                          │
        │   ┌────────────────────────────────────────────────────┐   │
        │   │               Wall Generator                       │   │
        │   │   (places artworks with x_ft positions)            │   │
        │   └─────────────┬──────────────────────────────────────┘   │
        │                 │                                          │
        │                 ▼                                          │
        │   ┌────────────────────────────────────────────────────┐   │
        │   │               Wall Evaluator                       │   │
        │   │   (spacing, overlap, constraints, etc.)            │   │
        │   └─────────────┬──────────────────────────────────────┘   │
        │                 │                                          │
        │                 ▼                                          │
        │   ┌────────────────────────────────────────────────────┐   │
        │   │               Room Evaluator                       │   │
        │   │   (aggregation across walls)                       │   │
        │   └─────────────┬──────────────────────────────────────┘   │
        │                 │                                          │
        │                 ▼                                          │
        │   ┌────────────────────────────────────────────────────┐   │
        │   │             Gallery Evaluator                      │   │
        │   │   (final scoring using scoring.yaml)               │   │
        │   └────────────────────────────────────────────────────┘   │
        │                                                            │
        └─────────────┬──────────────────────────────────────────────┘
                      │
                      ▼
        ┌────────────────────────────────────────────────────────────┐
        │                  SHOW OUTPUT (DICT)                        │
        │                                                            │
        │  rooms → walls → placements                               │
        │                                                            │
        └─────────────┬──────────────────────────────────────────────┘
                      │
                      ▼
        ┌────────────────────────────────────────────────────────────┐
        │                YAML WRITER / JSON OUTPUT                   │
        │                                                            │
        │  show.yaml (for inspection)                               │
        │  OR JSON (for React system)                               │
        └────────────────────────────────────────────────────────────┘
```

## Folder structure

```text
gallery_algo_starter/
├── README.md
├── pyproject.toml
├── requirements.txt
├── data/
│   ├── art.yaml
│   ├── gallery.yaml
│   └── scoring.yaml
├── examples/
│   └── student_algorithm.py
├── src/
│   └── gallerylab/
│       ├── __init__.py
│       ├── algorithm_api.py
│       ├── baseline_algorithm.py
│       ├── bridge.py
│       ├── cli.py
│       ├── evaluators.py
│       ├── io_utils.py
│       └── scoring_utils.py
└── tests/
    └── smoke_test.py
```

---

## Quick start

### 1. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### 2. Run the baseline algorithm

```bash
python -m gallerylab.cli \
  --art data/art.yaml \
  --gallery data/gallery.yaml \
  --scoring data/scoring.yaml \
  --output output_show.yaml
```

This will:

- load the three YAML inputs
- convert them to Python dictionaries/lists
- run the baseline `build_gallery_show(...)`
- write the generated show to `output_show.yaml`

### 3. Run a student algorithm instead

```bash
python -m gallerylab.cli \
  --art data/art.yaml \
  --gallery data/gallery.yaml \
  --scoring data/scoring.yaml \
  --algorithm examples/student_algorithm.py \
  --output student_show.yaml
```

---

## The algorithm API

This is the core contract between the test bed and student code.

### Input contract

Student code must define a function:

```python
def build_gallery_show(art_data, gallery_data, scoring_data):
    ...
```

Each argument is a plain Python structure made only from:

- `dict`
- `list`
- `str`
- `int`
- `float`
- `bool`
- `None`

That means students do **not** need custom classes to get started.

INPUT CONTRACT
```

art_data:
  { "artworks": [ { id, width_ft, height_ft, artist, ... }, ... ] }

gallery_data:
  { "rooms": [ { id, walls: [ { id, width_ft }, ... ] }, ... ] }

scoring_data:
  (see scoring.yaml)

OUTPUT CONTRACT (your function must return):

{
  "rooms": [
    {
      "room_id": "...",
      "walls": [
        {
          "wall_id": "...",
          "placements": [
            {
              "artwork_id": "...",
              "x_ft": float
            }
          ]
        }
      ]
    }
  ]
}
```

### Output contract

The function must return a dictionary like this:

```python
{
    "schema_version": "1.0",
    "show_id": "generated_show",
    "title": "My generated show",
    "rooms": [
        {
            "room_id": "R1",
            "walls": [
                {
                    "wall_id": "R1-N",
                    "width_ft": 18.0,
                    "placements": [
                        {
                            "artwork_id": "ART001",
                            "x_ft": 0.0,
                            "y_ft": 0.0,
                            "locked": False
                        }
                    ]
                }
            ]
        }
    ]
}
```

At minimum, each placement should include:

- `artwork_id`
- `x_ft`

The starter code also uses:

- `y_ft`
- `locked`

---

## How this maps to the React upload system

Later, in the React-based system, the flow can be:

1. user uploads `art.yaml`, `gallery.yaml`, and `scoring.yaml`
2. frontend or backend parses YAML into JSON
3. JSON is handed to the Python algorithm runner
4. algorithm returns a JSON-compatible show dictionary
5. React visualizer renders the generated show

Because JSON maps naturally to Python dicts/lists, the same student function can work in both environments.

Conceptually:

```python
show = build_gallery_show(art_data, gallery_data, scoring_data)
```

where `art_data`, `gallery_data`, and `scoring_data` may have originated either from:

- local YAML files during development, or
- JSON sent from the React app

---
## Pipeline
```
Gallery Generator
    ↓
Room Generator
    ↓
Wall Generator
    ↓
Wall Evaluator
    ↑
Room Evaluator
    ↑
Gallery Evaluator
```

## The six algorithm layers

The starter project is intentionally decomposed into six pieces.

### 1. Wall generator

File: `baseline_algorithm.py`

Class: `BaselineWallGenerator`

Purpose:

- choose artworks for one wall
- place them left-to-right
- respect any locked placements already present in a partial show

Baseline behavior:

- sorts candidates by focal weight, then width
- uses one preferred gap value
- stops when the wall fills up or the max artwork count is reached

### 2. Wall evaluator

Class: `BaselineWallEvaluator`

Purpose:

- evaluate a single wall layout using the scoring profile

Baseline checks include:

- minimum and maximum number of artworks
- overlap
- within-wall bounds
- minimum and maximum gap
- artist variety
- thematic cohesion
- spacing regularity
- visual balance
- wall utilization
- period adjacency
- focal point placement

### 3. Room generator

Class: `BaselineRoomGenerator`

Purpose:

- iterate over the room’s walls
- call the wall generator for each wall
- remove already-used artworks so the same work is not reused repeatedly

### 4. Room evaluator

Class: `BaselineRoomEvaluator`

Purpose:

- aggregate wall scores for one room

### 5. Gallery generator

Class: `BaselineGalleryGenerator`

Purpose:

- iterate through all rooms
- call the room generator
- preserve any curator-specified locked placements from `partial_show`

### 6. Gallery evaluator

Class: `BaselineGalleryEvaluator`

Purpose:

- aggregate all room scores into a final gallery score

---

## Partial shows and locked placements

This starter supports the idea of a curator specifying a **partial show** that the algorithm must complete.

In `gallery.yaml`, there is a section like this:

```yaml
partial_show:
  rooms:
    - room_id: R1
      walls:
        - wall_id: R1-N
          placements:
            - artwork_id: ART001
              x_ft: 6.0
              y_ft: 0.0
              locked: true
```

The baseline generator preserves these locked placements and then fills the rest of the wall.

That gives students a clean place to start thinking about:

- required works
- required rooms
- required walls
- fixed x-locations
- curator overrides

---

## Sample input files

### `data/art.yaml`

Contains the artwork catalog. Each artwork can include fields such as:

- `id`
- `title`
- `artist`
- `year`
- `width_ft`
- `height_ft`
- `primary_theme`
- `theme_tags`
- `visual_intensity`
- `focal_weight`

### `data/gallery.yaml`

Contains the gallery structure:

- rooms
- walls
- wall widths
- optional `partial_show`

### `data/scoring.yaml`

Contains the scoring profile.

This project uses the target-based scoring style from your uploaded scoring YAML, including criteria such as thematic cohesion, artist variety, spacing regularity, visual balance, wall utilization, period adjacency, size variety, and focal point placement.

---

## What students are expected to replace

The baseline algorithm is deliberately simple. Students should replace pieces of it step by step.

Examples of improvements they might make:

- choose artworks by theme, period, or medium instead of just focal weight
- search many possible wall layouts instead of building one greedily
- rebalance a room after scoring it
- compare multiple candidate rooms before choosing one
- optimize globally across the whole gallery
- incorporate more scoring criteria from `scoring.yaml`
- use hill climbing, beam search, simulated annealing, genetic algorithms, or custom heuristics

The decomposition into wall/room/gallery generators and evaluators is there so they do not have to rewrite the whole system at once.

---

## Student algorithm template

There is a starter student file here:

```text
examples/student_algorithm.py
```

It currently just calls the baseline:

```python
from gallerylab.baseline_algorithm import build_gallery_show as baseline_build_gallery_show


def build_gallery_show(art_data, gallery_data, scoring_data):
    return baseline_build_gallery_show(art_data, gallery_data, scoring_data)
```

Students can gradually replace that with their own logic.

---

## Example: using the library directly in Python

```python
from gallerylab.io_utils import load_yaml
from gallerylab.baseline_algorithm import build_gallery_show

art_data = load_yaml("data/art.yaml")
gallery_data = load_yaml("data/gallery.yaml")
scoring_data = load_yaml("data/scoring.yaml")

show = build_gallery_show(art_data, gallery_data, scoring_data)
print(show["evaluation"]["score"])
```

---

## Example: how the React backend could call student code later

A Python service or worker could do something like this:

```python
from gallerylab.bridge import load_algorithm_from_python_file, run_algorithm_from_data

algorithm = load_algorithm_from_python_file("uploads/student_algorithm.py")
show = run_algorithm_from_data(algorithm, art_data, gallery_data, scoring_data)
```

That is the same contract used by the local CLI, just without the YAML-loading step.

---

## Notes on the baseline scoring

The evaluator currently does **not** implement every possible detail from the scoring YAML. It uses the scoring file as a structured profile and demonstrates how a scoring-driven system can work, but it only implements a starter subset in a simplified way.

That is intentional.

This gives students room to:

- add more faithful implementations of criteria
- compare simplified versus richer scoring models
- explore how local and global scoring interact

---

## Suggested student workflow

A good progression is:

1. run the baseline unchanged
2. inspect the output show
3. modify only the wall generator
4. improve wall scoring
5. improve room generation
6. add whole-gallery search or repair passes
7. compare scores and visual outcomes

This keeps the project manageable.

---

## Testing

A simple smoke test is included:

```bash
pytest
```

If you do not want to add pytest yet, you can simply run the CLI and inspect the output show.

---

## Future extensions

This starter is designed to grow into a fuller system. Natural next steps include:

- support for mediums, color palettes, or controlled vocabularies
- room adjacency and doorway-aware flow
- forbidden walls or preferred walls
- wall building or subdivision during search
- human-in-the-loop curation and re-scoring
- comparison dashboards for multiple algorithms
- strict schema validation for student submissions
- integration with the React visualizer and upload pipeline

---

## Summary of the core API

Input:

```python
build_gallery_show(art_data, gallery_data, scoring_data)
```

Output:

- a JSON-compatible dictionary describing the generated show

This is the one thing students need to know.

Everything else in the starter project exists to help them test, iterate, and improve that function.
