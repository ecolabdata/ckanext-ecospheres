from builtins import object

from rdflib import URIRef, Literal

from ckanext.ecospheres.vocabulary import reader

class TestIsKnownURI(object):
    
    def test_find_recorded_vocabulary_item_from_uriref_uri(self):
        """Vérifie que is_known_uri détecte bien comme telles les URI référencées (avec URI de type URIRef)."""
        assert reader.is_known_uri(
            'eu_language', 
            URIRef('http://publications.europa.eu/resource/authority/language/FRA')
        )
    
    def test_find_recorded_vocabulary_item_from_str_uri(self):
        """Vérifie que is_known_uri détecte bien comme telles les URI référencées (avec URI de type str)."""
        assert reader.is_known_uri(
            'eu_language', 
            'http://publications.europa.eu/resource/authority/language/FRA'
        )
    
    def test_dont_find_unrecorded_vocabulary_item_from_uriref_uri(self):
        """Vérifie que is_known_uri détecte bien comme inconnues les URI non référencées (avec URI de type URIRef)."""
        assert reader.is_known_uri(
            'eu_language', 
            URIRef('http://THING')
        )
    
    def test_find_recorded_vocabulary_item_from_str_uri(self):
        """Vérifie que is_known_uri détecte bien comme inconnues les URI non référencées (avec URI de type str)."""
        assert reader.is_known_uri(
            'eu_language', 
            'http://THING'
        )

class TestGetURIFromLabel(object):

    def test_get_uri_from_literal_skos_preflabel(self):
        """Vérifie qu'il est possible de trouver un item à partir d'un label de type Literal."""