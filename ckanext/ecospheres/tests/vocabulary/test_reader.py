from builtins import object

from rdflib import URIRef, Literal

from ckanext.ecospheres.vocabulary.reader import VocabularyReader

class TestIsKnownURI(object):
    
    def test_find_recorded_vocabulary_item_from_uriref_uri(self):
        """Vérifie que is_known_uri détecte bien comme telles les URI référencées (avec URI de type URIRef)."""
        # assert VocabularyReader.is_known_uri(
        #     'eu_language', 
        #     URIRef('http://publications.europa.eu/resource/authority/language/FRA')
        # )
    
    def test_find_recorded_vocabulary_item_from_str_uri(self):
        """Vérifie que is_known_uri détecte bien comme telles les URI référencées (avec URI de type str)."""
        assert VocabularyReader.is_known_uri(
            'eu_language', 
            'http://publications.europa.eu/resource/authority/language/FRA'
        ) == {'uri': 'http://publications.europa.eu/resource/authority/language/FRA', 'label': 'français', 'language': 'fr'}
        
        
        assert  VocabularyReader.is_known_uri(
            'eu_language', 
            'http://publications.europa.eu/resource/authority/language/FRA',
            'en'
        ) == {'uri': 'http://publications.europa.eu/resource/authority/language/FRA', 'label': 'French', 'language': 'en'}

    # def test_dont_find_unrecorded_vocabulary_item_from_uriref_uri(self):
    #     """Vérifie que is_known_uri détecte bien comme inconnues les URI non référencées (avec URI de type URIRef)."""
    #     assert not VocabularyReader.is_known_uri(
    #         'eu_language', 
    #         URIRef('http://THING')
    #     )
    
    def test_find_recorded_vocabulary_item_from_str_uri(self):
        """Vérifie que is_known_uri détecte bien comme inconnues les URI non référencées (avec URI de type str)."""
        assert not VocabularyReader.is_known_uri(
            'eu_language', 
            'http://THING'
        )

class TestGetURIFromLabel(object):

    def test_get_uri_from_literal_skos_preflabel_without_language_and_sensitivity(self):
        """Vérifie qu'il est possible de trouver un item à partir d'un label de type Literal."""
        uri=VocabularyReader.get_uri_from_label(
                                            vocabulary="eu_file_type",
                                            label="Tihendatud ISO pilt",
                                            language=None,
                                            case_sensitive=False)
        assert uri
        assert uri == "http://publications.europa.eu/resource/authority/file-type/ISO_ZIP"
        
        uri=VocabularyReader.get_uri_from_label(
                                            vocabulary="eu_file_type",
                                            label="Tihendatud ISO not existe",
                                            language=None,
                                            case_sensitive=False)
        assert not  uri



    def test_get_uri_from_literal_skos_preflabel_without_language_with_sensitivity(self):
        """Vérifie qu'il est possible de trouver un item à partir d'un label de type Literal."""
        uri=VocabularyReader.get_uri_from_label(
                                            vocabulary="eu_file_type",
                                            label="Tihendatud iso pilt",
                                            language=None,
                                            case_sensitive=False)
        assert not  uri
        
        uri=VocabularyReader.get_uri_from_label(
                                            vocabulary="eu_file_type",
                                            label="Tihendatud iso pilt",
                                            language=None,
                                            case_sensitive=True)
        assert   uri
        assert uri == "http://publications.europa.eu/resource/authority/file-type/ISO_ZIP"
     
        uri=VocabularyReader.get_uri_from_label(
                                            vocabulary="eu_file_type",
                                            label="esri file geodatabase",
                                            language=None,
                                            case_sensitive=False)
        assert not  uri
        
        uri=VocabularyReader.get_uri_from_label(
                                            vocabulary="eu_file_type",
                                            label="Esri File Geodatabase",
                                            language=None,
                                            case_sensitive=True)
        assert   uri
        assert uri == "http://publications.europa.eu/resource/authority/file-type/GDB"
     
    def test_get_uri_from_literal_skos_preflabel_with_language_with_sensitivity(self):
        """Vérifie qu'il est possible de trouver un item à partir d'un label de type Literal."""
        uri=VocabularyReader.get_uri_from_label(
                                            vocabulary="eu_file_type",
                                            label="Tihendatud iso pilt",
                                            language='fr',
                                            case_sensitive=False)
        assert not  uri
        
        uri=VocabularyReader.get_uri_from_label(
                                            vocabulary="eu_file_type",
                                            label="Tihendatud iso pilt",
                                            language='en',
                                            case_sensitive=True)
        assert  not uri

        uri=VocabularyReader.get_uri_from_label(
                                            vocabulary="eu_file_type",
                                            label="Tihendatud iso pilt",
                                            language='et',
                                            case_sensitive=True)
        assert   uri
        assert uri == "http://publications.europa.eu/resource/authority/file-type/ISO_ZIP"
     
        
     
     


    def test_get_uri_from_literal_skos_preflabel_with_language_without_sensitivity(self):
        uri=VocabularyReader.get_uri_from_label(
                                            vocabulary="eu_file_type",
                                            label="Tihendatud ISO pilt",
                                            language='et',
                                            case_sensitive=False)
                        
        assert uri
        assert uri == "http://publications.europa.eu/resource/authority/file-type/ISO_ZIP"

        uri=VocabularyReader.get_uri_from_label(
                                            vocabulary="eu_file_type",
                                            label="Tihendatud ISO pilt",
                                            language='fr',
                                            case_sensitive=False)
        
        assert not uri
    def test_get_uri_from_literal_skos_preflabel_with_language_without_sensitivity_from_altlabels_table(self):
        uri=VocabularyReader.get_uri_from_label(
                                            vocabulary="eu_file_type",
                                            label="Internet Archive ARC file format",
                                            language=None,
                                            case_sensitive=False)
                        
        assert uri
        assert uri == "http://publications.europa.eu/resource/authority/file-type/ARC"

    

class TestGetLabels(object):

    def test_get_label_by_vocabulary(self):
        """Vérifie la récuperation des labels d'un vocabulaire"""
        ecospheres_territory_labels=VocabularyReader.labels("ecospheres_territory")
        assert ecospheres_territory_labels
        assert len(ecospheres_territory_labels) > 0


        eu_access_right_labels=VocabularyReader.labels("eu_access_right")
        assert eu_access_right_labels
        assert len(eu_access_right_labels) > 0

class TestGetAltLabels(object):

    def test_get_altlabel_by_vocabulary(self):
        """Vérifie la récuperation des labels d'un vocabulaire"""
        eu_frequency_altlabels=VocabularyReader.altlabels("eu_frequency")
        assert eu_frequency_altlabels
        assert len(eu_frequency_altlabels) > 0


        eu_file_type_labels=VocabularyReader.labels("eu_file_type")
        assert eu_file_type_labels
        assert len(eu_file_type_labels) > 0
        
        eu_file_type_altlabels=VocabularyReader.altlabels("eu_file_type")
        assert eu_file_type_altlabels
        assert len(eu_file_type_altlabels) > 0



class TestGetThemes(object):
    def test_get_themes(self):
        print("getting themes")
        # VocabularyReader.themes()



class TestReadTypeOrganization(object):

    def test_get_organizations(self):
        list_organizations= VocabularyReader.get_organization_by_admin()
        assert list_organizations
        assert len(list_organizations) > 0
