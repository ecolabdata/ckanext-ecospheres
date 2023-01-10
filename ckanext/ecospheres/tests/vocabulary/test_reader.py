from builtins import object

from ckanext.ecospheres.vocabulary.reader import VocabularyReader

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
