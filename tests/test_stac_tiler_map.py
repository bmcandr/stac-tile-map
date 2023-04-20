from datetime import date, datetime, timedelta
from typing import Union
from unittest.mock import mock_open, patch

import geojson
import geojson.utils
import pytest

from stac_tiler_map.create_map import _get_scene, _get_search_dates, read_geojson

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


@pytest.fixture
def geometry(request):
    return geojson.utils.generate_random(request.param)


class TestReadGeoJSON:
    fake_file_path = "path/to/data.geojson"
    fake_file_url = "http://www.example.com/data.geojson"

    feature_collection_args = (
        "feature_collection",
        GEOJSON_TYPES,
    )

    @pytest.mark.parametrize(*feature_collection_args, indirect=True)
    def test_read_local_geojson_feature_collection(self, feature_collection):
        with patch(
            "stac_tiler_map.create_map.open",
            new=mock_open(read_data=geojson.dumps(feature_collection)),
        ) as _file:
            geojson_obj = read_geojson(self.fake_file_path)
            _file.assert_called_once_with(self.fake_file_path, "r")

        assert geojson_obj == feature_collection

    @pytest.mark.parametrize(*feature_collection_args, indirect=True)
    def test_read_remote_geojson_feature_collection(
        self, requests_mock, feature_collection
    ):
        requests_mock.get(self.fake_file_url, json=feature_collection)
        geojson_obj = read_geojson(self.fake_file_url)

        assert geojson_obj == feature_collection

    @pytest.mark.parametrize("geometry", GEOJSON_TYPES, indirect=True)
    def test_read_local_geojson_geometry(self, geometry):
        with pytest.raises(AssertionError):
            with patch(
                "stac_tiler_map.create_map.open",
                new=mock_open(read_data=geojson.dumps(geometry)),
            ) as _file:
                _ = read_geojson(self.fake_file_path)
                _file.assert_called_once_with(self.fake_file_path, "r")


@pytest.mark.parametrize(
    "end_date,period,expected",
    [
        (date(2023, 1, 1), 1, "2022-12-31/2023-01-01"),
        (datetime(2023, 1, 1), 1, "2022-12-31/2023-01-01"),
        (date(2023, 1, 31), 30, "2023-01-01/2023-01-31"),
        (datetime(2023, 1, 31), 30, "2023-01-01/2023-01-31"),
    ],
)
def test_get_search_dates(end_date: Union[date, datetime], period: int, expected: str):
    date_range = _get_search_dates(end_date=end_date, period=period)

    assert date_range == expected
