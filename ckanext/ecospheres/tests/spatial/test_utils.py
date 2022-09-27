from builtins import object

from ckanext.ecospheres.spatial.utils import (
    bbox_wkt_from_coordinates, 
    bbox_geojson_from_coordinates,
    build_attributes_page_url,
    build_catalog_page_url,
    is_valid_url,
    extract_scheme_and_identifier
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

class TestURLOperations(object):

    def test_valid_url_is_valid(self):
        assert is_valid_url(
            'https://www.wikipedia.org/'
        )

    def test_unvalid_url_is_not_valid(self):
        assert not is_valid_url('truc')
        assert not is_valid_url('https://truc')

    def test_build_geoide_attributes_page_url(self):
        assert build_attributes_page_url(
            'http://catalogue.geo-ide.developpement-durable.gouv.fr/catalogue/srv/fre/catalog.search#/metadata',
            'fr-120066022-jdd-192de12f-ee82-4abc-a2c0-42e30e2242a0'
        ) == 'http://catalogue.geo-ide.developpement-durable.gouv.fr/catalogue/srv/fre/catalog.search#/metadata/fr-120066022-ca-jdd-192de12f-ee82-4abc-a2c0-42e30e2242a0'

    def test_build_catalog_page_url(self):
        assert build_catalog_page_url(
            'http://catalogue.geo-ide.developpement-durable.gouv.fr/catalogue/srv/fre/catalog.search#/metadata',
            'fr-120066022-jdd-192de12f-ee82-4abc-a2c0-42e30e2242a0'
        ) == 'http://catalogue.geo-ide.developpement-durable.gouv.fr/catalogue/srv/fre/catalog.search#/metadata/fr-120066022-jdd-192de12f-ee82-4abc-a2c0-42e30e2242a0'

    def test_extract_scheme_and_identifier(self):
        assert extract_scheme_and_identifier('http://id.insee.fr/geo/pays/france') == (
            'http://id.insee.fr/geo/pays', 'france'
        )
        assert extract_scheme_and_identifier('urn:uuid:4d2865ab-7b71-4d0b-afd7-e95758a73be1') == (
            'urn:uuid', '4d2865ab-7b71-4d0b-afd7-e95758a73be1'
        )
        assert extract_scheme_and_identifier('autre chose') == (
            None, 'autre chose'
        )
        assert extract_scheme_and_identifier('scheme/autre chose') == (
            None, 'scheme/autre chose'
        )

