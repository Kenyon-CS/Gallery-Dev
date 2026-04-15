from gallerylab.baseline_algorithm import build_gallery_show
from gallerylab.io_utils import load_yaml


def test_smoke() -> None:
    art = load_yaml("data/art.yaml")
    gallery = load_yaml("data/gallery.yaml")
    scoring = load_yaml("data/scoring.yaml")
    show = build_gallery_show(art, gallery, scoring)
    assert "rooms" in show
    assert len(show["rooms"]) > 0
