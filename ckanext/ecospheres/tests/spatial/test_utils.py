from builtins import object

from ckanext.ecospheres.spatial.utils import (
    bbox_wkt_from_coordinates, 
    bbox_geojson_from_coordinates
)

class TestCoordinatesOperations(object):

    def test_bbox_wkt_from_coordinates(self):
        assert bbox_wkt_from_coordinates(
            2.223960161, 2.46962285, 48.815608978, 48.90165329
        ) == 'POLYGON((2.223960161 48.90165329,2.223960161 48.815608978,2.46962285 48.815608978,2.46962285 48.90165329,2.223960161 48.90165329))'

    def test_bbox_geojson_from_coordinates(self):
        assert bbox_geojson_from_coordinates(
            2.223960161, 2.46962285, 48.815608978, 48.90165329
        ) == '{"type": "Polygon", "coordinates": [[[2.223960161, 48.90165329], [2.223960161, 48.815608978], [2.46962285, 48.815608978], [2.46962285, 48.90165329], [2.223960161, 48.90165329]]]}'

