from pathlib import Path
from unittest.mock import mock_open, patch

import geojson
import geojson.utils
import pytest

from stac_tiler_map.create_map import (
    _get_random_feature,
    _get_scene,
    _get_search_dates,
    read_geojson,
)

GEOJSON_TYPES = [
    "Point",
    "LineString",
    "Polygon",
]


@pytest.fixture
def feature_collection(request):
    return {
        "type": "FeatureCollection",
        "features": [
            geojson.utils.generate_random(request.param) for _ in range(0, 10)
        ],
    }


@pytest.mark.parametrize(
    "feature_collection",
    GEOJSON_TYPES,
    indirect=True,
)
class TestReadGeoJSON:
    def test_read_local_geojson(self, feature_collection):
        fake_file_path = "path/to/data.geojson"

        with patch(
            "stac_tiler_map.create_map.open",
            new=mock_open(read_data=geojson.dumps(feature_collection)),
        ) as _file:
            geojson_obj = read_geojson(fake_file_path)
            _file.assert_called_once_with(fake_file_path, "r")

        assert geojson_obj == feature_collection

    def test_read_remote_geojson(self, requests_mock, feature_collection):
        fake_file_url = "http://www.example.com/data.geojson"

        requests_mock.get(fake_file_url, json=feature_collection)
        geojson_obj = read_geojson(fake_file_url)

        assert geojson_obj == feature_collection
