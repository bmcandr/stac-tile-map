import string
from datetime import date, datetime, timedelta
from typing import List, Union
from unittest.mock import Mock, mock_open, patch

import geojson
import geojson.utils
import hypothesis.strategies as st
import pystac
import pystac_client
import pytest
from hypothesis import given
from hypothesis.strategies import composite

from stac_tiler_map.create_map import (
    DATE_FMT,
    get_items,
    get_search_dates,
    read_geojson,
    sort_items,
)

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


@given(
    end_date=st.dates() | st.datetimes(), period=st.integers(min_value=1, max_value=90)
)
def test_get_search_dates(end_date: Union[date, datetime], period: int):
    date_range = get_search_dates(end_date=end_date, period=period)
    start_date = end_date - timedelta(days=period)

    assert date_range == f"{start_date:{DATE_FMT}}/{end_date:{DATE_FMT}}"


GeometryStrategy = st.builds(
    geojson.Polygon,
    coordinates=st.lists(
        st.lists(
            st.lists(
                st.floats(allow_nan=False, allow_infinity=False), min_size=2, max_size=2
            ),
            min_size=1,
        ),
        min_size=1,
    ),
    type=st.just("Polygon"),
)

BBoxStrategy = st.lists(
    st.integers() | st.floats(allow_nan=False, allow_infinity=False),
    min_size=4,
    max_size=4,
)


STACItemStrategy = st.builds(
    pystac.Item,
    id=st.text(alphabet=string.ascii_letters + "-", min_size=1),
    geometry=GeometryStrategy,
    bbox=BBoxStrategy,
    datetime=st.datetimes(),
    properties=st.dictionaries(
        keys=st.text(), values=st.text() | st.integers() | st.floats(allow_nan=False)
    ),
)

SpatialExtentStrategy = st.builds(
    pystac.SpatialExtent, bboxes=st.lists(BBoxStrategy, min_size=1)
)

TemporalExtentStrategy = st.builds(
    pystac.TemporalExtent,
    intervals=st.lists(
        st.lists(st.datetimes(), min_size=2, max_size=2), min_size=1, max_size=1
    ),
)

ExtentStrategy = st.builds(
    pystac.Extent, spatial=SpatialExtentStrategy, temporal=TemporalExtentStrategy
)

STACCollectionStrategy = st.builds(
    pystac.Collection, id=st.text(), description=st.text(), extent=ExtentStrategy
)


@pytest.fixture
def items():
    return [
        pystac.Item(
            id="item_1",
            geometry=generate_feature(feature_type="Polygon"),
            bbox=[-109.050293, 37.002553, -101.975098, 41.013066],
            datetime=datetime.now(),
            properties={"eo:cloud_cover": 50},
        ),
        pystac.Item(
            id="item_2",
            geometry=generate_feature(feature_type="Polygon"),
            bbox=[-109.050293, 37.002553, -101.975098, 41.013066],
            datetime=datetime.now(),
            properties={"eo:cloud_cover": 0},
        ),
    ]


@pytest.fixture
def item_collection(items: List[pystac.Item]):
    return pystac.ItemCollection(items=items)


@pytest.mark.parametrize("sort_on,ascending", [(["eo:cloud_cover"], True)])
def test_sort_items(
    item_collection: pystac.ItemCollection,
    sort_on: List[str],
    ascending: bool,
):
    sorted_items = sort_items(
        item_collection=item_collection, sort_on=sort_on, ascending=True
    )

    items = list(item_collection)

    if ascending:
        items.reverse()

    assert sorted_items == items


@given(
    collection=STACCollectionStrategy,
    items=st.lists(STACItemStrategy),
    end_date=st.datetimes(),
    search_period=st.integers(min_value=1, max_value=90),
    intersects=GeometryStrategy,
)
def test_get_items(
    collection: pystac.Collection,
    items: List[pystac.Item],
    end_date: datetime,
    search_period: int,
    intersects: geojson.Feature,
):
    collection.add_items(items=items)

    item_collection = (
        pystac.ItemCollection(items=list(collection.get_items())) if items else None
    )

    item_search_mock = Mock()
    item_search_mock.item_collection.return_value = item_collection

    stac_client_mock = Mock()
    stac_client_mock.search.return_value = item_search_mock

    result = get_items(
        stac_client=stac_client_mock,
        collection=collection.id,
        end_date=end_date,
        search_period=search_period,
        intersects=intersects,
    )

    if items:
        assert result == item_collection
    else:
        assert result is None
