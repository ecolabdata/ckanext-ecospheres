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
        VocabularyReader.themes()



class TestReadTypeOrganization(object):

    def test_get_organizations(self):
        list_organizations= VocabularyReader.get_organization_by_admin()
        assert list_organizations
        assert len(list_organizations) > 0

class TestGetEcosphereTerritory(object):

    def test_get_territory_by_code_region(self):
        region_label=VocabularyReader.get_territory_by_code_region(code_region='D21')
        assert region_label
        assert not VocabularyReader.get_territory_by_code_region(code_region='D233')
    def test_get_territory_spatial_by_code_region(self):
        region_spatial=VocabularyReader.get_territory_spatial_by_code_region(code_region='D21')
        assert region_spatial
    def test_get_territory_spatial_by_code_region(self):
        territoies_hierarchy=VocabularyReader._get_territories_by_hierarchy()
        assert territoies_hierarchy
    
    def test_get_territory_(self):
        label_dict=VocabularyReader.is_known_uri(vocabulary="eu_licence",uri="https://www.etalab.gouv.fr/licence-ouverte-open-licence")
        print(label_dict)


# ------------------------------------------------------------
# tests issus de la branche spatial

class TestSpatialIsKnownURI(object):
    
    def test_find_recorded_vocabulary_item(self):
        """Vérifie que is_known_uri détecte bien comme telles les URI référencées (avec URI de type str)."""
        assert VocabularyReader.is_known_uri(
            'eu_language', 
            'http://publications.europa.eu/resource/authority/language/FRA'
        )
    
    def test_dont_find_unrecorded_vocabulary_item(self):
        """Vérifie que is_known_uri détecte bien comme inconnues les URI non référencées (avec URI de type str)."""
        assert not VocabularyReader.is_known_uri(
            'eu_language', 
            'http://THING'
        )

class TestSpatialGetURI(object):

    def test_get_uri_from_label(self):
        """Vérifie qu'il est possible de trouver un item à partir de son label."""
        assert VocabularyReader.get_uri_from_label(
            'ecospheres_theme',
            "Réseaux d'énergie et de communication"
        ) == 'http://registre.data.developpement-durable.gouv.fr/ecospheres/themes-ecospheres/reseaux-d-energie-et-de-communication'

    def test_get_uri_from_label_with_known_lang_tag(self):
        """Vérifie qu'il est possible de trouver un item à partir de son label, en spécifiant une langue connue."""
        assert VocabularyReader.get_uri_from_label(
            'ecospheres_theme',
            "Réseaux d'énergie et de communication",
            language='fr'
        ) == 'http://registre.data.developpement-durable.gouv.fr/ecospheres/themes-ecospheres/reseaux-d-energie-et-de-communication'

    def test_get_uri_from_label_with_unknown_lang_tag(self):
        """Vérifie que l'URI ne sort pas lorsque le label correspond mais pas la langue."""
        assert VocabularyReader.get_uri_from_label(
            'ecospheres_theme',
            "Réseaux d'énergie et de communication",
            language='en'
        ) is None

    def test_get_uri_from_altlabel(self):
        """Vérifie qu'il est possible de trouver un item à partir d'un label alternatif."""
        assert VocabularyReader.get_uri_from_label(
            'ecospheres_theme',
            'Habitat Politique de la ville/Construction'
        ) == 'http://registre.data.developpement-durable.gouv.fr/ecospheres/themes-ecospheres/construction'

    def test_get_uri_from_regexp(self):
        """Vérifie qu'il est possible de trouver un item à partir d'une expression régulière."""
        assert VocabularyReader.get_uris_from_regexp(
            'ecospheres_theme',
            ('VERCORS', 'Parc Naturel Régional du Vercors')
        ) == ['http://registre.data.developpement-durable.gouv.fr/ecospheres/themes-ecospheres/zonages-d-amenagement']

    def test_get_parent(self):
        """Vérifie qu'il est possible récupérer le parent d'un item."""
        assert VocabularyReader.get_parents(
            'ecospheres_theme',
            'http://registre.data.developpement-durable.gouv.fr/ecospheres/themes-ecospheres/infrastructure-portuaire'
        ) == [
            'http://registre.data.developpement-durable.gouv.fr/ecospheres/themes-ecospheres/infrastructures-de-transport'
        ]

    def test_get_unregistered_parent(self):
        """Vérifie que tenter de récupérer le parent d'un item sans parent renvoie une liste vide."""
        assert VocabularyReader.get_parents(
            'ecospheres_theme',
            'http://registre.data.developpement-durable.gouv.fr/ecospheres/themes-ecospheres/infrastructures-de-transport'
        ) == []

class TestSpatialGetTerritory(object):

    def test_get_territory_from_eu_uri(self):
        """Récupération du territoire d'Ecosphères correspondant à un URI du vocabulaire eu_administrative_territory_unit."""
        assert VocabularyReader.get_ecospheres_territory(
            'eu_administrative_territory_unit',
            'http://publications.europa.eu/resource/authority/country/SPM'
        ) == 'SPM'
    
    def test_unknown_territory_from_eu_uri(self):
        """Vérifie que rien n'est renvoyé avec un URI non reconnu du vocabulaire eu_administrative_territory_unit."""
        assert VocabularyReader.get_ecospheres_territory(
            'eu_administrative_territory_unit',
            'http://publications.europa.eu/resource/authority/atu/BGR_OBL_VTT'
        ) is None
    
    def test_get_territory_from_ogc_uri(self):
        """Récupération du territoire d'Ecosphères correspondant à un URI du vocabulaire insee_official_geographic_code."""
        assert VocabularyReader.get_ecospheres_territory(
            'insee_official_geographic_code',
            'http://id.insee.fr/geo/region/02'
        ) == 'MTQ'

    def test_get_territory_from_uuid_ogc_uri(self):
        """Récupération du territoire d'Ecosphères correspondant à un URI du vocabulaire insee_official_geographic_code basé sur un UUID."""
        assert VocabularyReader.get_ecospheres_territory(
            'insee_official_geographic_code',
            'http://id.insee.fr/geo/departement/d423d69b-3557-41f6-9469-9ed0f3db412a'
        ) == 'MTQ'

    def test_get_supra_territory_from_ogc_uri(self):
        """Récupération du territoire d'Ecosphères incluant le territoire identifié par un URI du vocabulaire insee_official_geographic_code."""
        assert VocabularyReader.get_ecospheres_territory(
            'insee_official_geographic_code',
            'http://id.insee.fr/geo/commune/9ca7148d-1d9f-4cf0-8fd6-db5ed497d8ed'
        ) == 'D29'

    def test_get_supra_territory_from_ogc_uri_synonym(self):
        """Récupération du territoire d'Ecosphères incluant le territoire identifié par un URI synonyme du vocabulaire insee_official_geographic_code."""
        assert VocabularyReader.get_ecospheres_territory(
            'insee_official_geographic_code',
            'http://id.insee.fr/geo/commune/29019'
        ) == 'D29'
