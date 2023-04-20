from pathlib import Path

import pytest

from stac_tiler_map.create_map import (
    _get_random_feature,
    _get_scene,
    _get_search_dates,
    read_local_geojson,
    read_remote_geojson,
)

TEST_DIR = Path(__file__).parent
ROOT_DIR = TEST_DIR.parent
DATA_DIR = ROOT_DIR / "data"


def test_read_local_geojson():
    geojson = read_local_geojson(Path(DATA_DIR, "national-parks.geojson"))

    assert isinstance(geojson, dict)
