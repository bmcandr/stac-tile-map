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


def generate_feature(
    feature_type: str,
) -> Union[geojson.Point, geojson.LineString, geojson.Polygon, None]:
    return geojson.utils.generate_random(featureType=feature_type)


def generate_feature_collection(feature_type: str) -> geojson.FeatureCollection:
    return geojson.FeatureCollection(
        features=[generate_feature(feature_type=feature_type) for _ in range(0, 10)]
    )


@pytest.mark.parametrize("feature_type", GEOJSON_TYPES)
class TestReadGeoJSON:
    fake_file_path = "path/to/data.geojson"
    fake_file_url = "http://www.example.com/data.geojson"

    def test_read_local_geojson_feature_collection(self, feature_type):
        test_feature_collection = generate_feature_collection(feature_type=feature_type)
        with patch(
            "stac_tiler_map.create_map.open",
            new=mock_open(read_data=geojson.dumps(test_feature_collection)),
        ) as _file:
            feature_collection = read_geojson(self.fake_file_path)
            _file.assert_called_once_with(self.fake_file_path, "r")

        assert feature_collection == test_feature_collection

    def test_read_remote_geojson_feature_collection(self, requests_mock, feature_type):
        test_feature_collection = generate_feature_collection(feature_type=feature_type)
        requests_mock.get(self.fake_file_url, json=test_feature_collection)
        feature_collection = read_geojson(self.fake_file_url)

        assert feature_collection == test_feature_collection

    def test_read_local_geojson_geometry(self, feature_type):
        geojson_obj = generate_feature(feature_type)
        with patch(
            "stac_tiler_map.create_map.open",
            new=mock_open(read_data=geojson.dumps(geojson_obj)),
        ) as _file:
            feature_collection = read_geojson(self.fake_file_path)
            _file.assert_called_once_with(self.fake_file_path, "r")
            assert feature_collection == geojson.FeatureCollection(
                features=[geojson_obj]
            )


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
