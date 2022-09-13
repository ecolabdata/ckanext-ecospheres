from builtins import object

from ckanext.ecospheres.vocabulary.reader import VocabularyReader

class TestIsKnownURI(object):
    
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

class TestGetURI(object):

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
        assert VocabularyReader.get_uri_from_regexp(
            'ecospheres_theme',
            ('VERCORS', 'Parc Naturel Régional du Vercors')
        ) == 'http://registre.data.developpement-durable.gouv.fr/ecospheres/themes-ecospheres/zonages-d-amenagement'


