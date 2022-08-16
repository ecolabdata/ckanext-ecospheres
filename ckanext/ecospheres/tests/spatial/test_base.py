
from builtins import object

from ckanext.ecospheres.spatial.base import (
    EcospheresDatasetDict, EcospheresSubfieldsList,
    EcospheresSimpleTranslationDict, EcospheresMultiTranslationsDict,
    EcospheresMultiValuesList, EcospheresObjectDict
)


SIMPLE_DATASET_SCHEMA = {
    'dataset_fields': [
        {
            # une seule valeur littérale et traduisible
            'field_name': 'title',
            'translatable_values': True
        },
        {
            # plusieurs valeurs littérales traduisibles
            'field_name': 'free_tag',
            'translatable_values': True,
            'multiple_values': True
        },
        {
            # une seule valeur littérale non traduisible
            'field_name': 'version'
        },
        {
            # plusieurs valeurs littérales non traduisibles
            'field_name': 'category',
            'multiple_values': True
        },
        {
            # métadonnées imbriquées
            'field_name': 'creator',
            'repeating_subfields': [
                {
                    'field_name': 'name',
                    'translatable_values': True
                },
                {
                    'field_name': 'email'
                }
            ]
        }
    ],
    'resource_fields': [
        {
            'field_name': 'url'
        }
    ]
}
"""Schéma basique représentatif des différentes formes de structuration des métadonnées."""


class TestEcospheresDatasetDict(object):

    def test_init_dataset_dict_from_schema(self):
        """Vérifie qu'un dictionnaire de jeu de données construit selon un schéma est cohérent avec ce schéma."""

        dataset_dict = EcospheresDatasetDict(SIMPLE_DATASET_SCHEMA)

        for field in ('title', 'free_tag', 'version', 'category', 'creator',
            'resources', 'extras', 'owner_org'):
            assert field in dataset_dict
        
        assert type(dataset_dict['title']) == EcospheresSimpleTranslationDict
        assert type(dataset_dict['free_tag']) == EcospheresMultiTranslationsDict
        assert type(dataset_dict['category']) == EcospheresMultiValuesList
        assert type(dataset_dict['creator']) == EcospheresSubfieldsList
        assert dataset_dict['version'] is None

        creator_dict = dataset_dict.new_item('creator')

        for field in ('name', 'email'):
            assert field in creator_dict

        assert type(creator_dict) == EcospheresObjectDict
        assert creator_dict in dataset_dict['creator']
        assert type(creator_dict['name']) == EcospheresSimpleTranslationDict
        assert creator_dict['email'] is None

    def test_add_resource_to_dataset_dict(self):
        """Contrôle le dictionnaire obtenu en ajoutant une ressource dans un dictionnaire de jeu de données."""

        dataset_dict = EcospheresDatasetDict(SIMPLE_DATASET_SCHEMA)

        resource_dict_1 = dataset_dict.new_resource()
        assert resource_dict_1 in dataset_dict['resources']
        assert type(resource_dict_1) == EcospheresObjectDict
        assert 'url' in resource_dict_1

        resource_dict_1.set_value('url', 'https://data.developpement-durable.gouv.fr')
        assert resource_dict_1['url'] == 'https://data.developpement-durable.gouv.fr'

        resource_dict_2 = dataset_dict.new_resource()
        assert len(dataset_dict['resources']) == 2
        assert resource_dict_2 in dataset_dict['resources']
        
        resource_dict_2.set_value('url', 'https://dev.data.developpement-durable.gouv.fr')
        assert resource_dict_1['url'] == 'https://data.developpement-durable.gouv.fr'
        assert resource_dict_2['url'] == 'https://dev.data.developpement-durable.gouv.fr'

    def test_set_not_translatable_unique_value_of_dict_field(self):
        """Contrôle le dictionnaire résultant lorsqu'on définit la valeur d'un champ admettant une unique valeur non traduisible."""

        dataset_dict = EcospheresDatasetDict(SIMPLE_DATASET_SCHEMA)

        # sur un champ à la racine du dictionnaire de jeu de données
        dataset_dict.set_value('version', 'v1')
        assert dataset_dict['version'] == 'v1'

        # idem, avec une liste
        dataset_dict.set_value('version', ['v2', 'v3'])
        assert dataset_dict['version'] == 'v3'

        # sur un sous-dictionnaire + en spécifiant inutilement
        # la langue
        creator_dict = dataset_dict.new_item('creator')
        creator_dict.set_value('email', 'mailto:name@something.org', 'it')
        assert creator_dict['email'] == 'mailto:name@something.org'

    def test_add_not_translatable_values_to_dict_field(self):
        """Contrôle le dictionnaire résultant lorsqu'on ajoute des valeurs à un champ admettant plusieurs valeurs non traduisibles."""

        dataset_dict = EcospheresDatasetDict(SIMPLE_DATASET_SCHEMA)

        dataset_dict.set_value('category', 'namespace:theme1')
        dataset_dict.set_value('category', 'namespace:theme2', 'en')
        dataset_dict.set_value('category', ['namespace:theme3', 'namespace:theme4'])
        assert [v for v in dataset_dict['category']] == ['namespace:theme1',
            'namespace:theme2', 'namespace:theme3', 'namespace:theme4']

    def test_add_translation_to_dict_field(self):
        """Contrôle le dictionnaire résultant lorsqu'on ajoute une traduction pour un champ admettant une unique valeur traduisible."""

        dataset_dict = EcospheresDatasetDict(SIMPLE_DATASET_SCHEMA, main_language='en')

        dataset_dict.set_value('title', 'Titre', 'fr')
        dataset_dict.set_value('title', '???', 'en')
        dataset_dict.set_value('title', ['Thing', 'Title'])
        assert {k: v for k, v in dataset_dict['title'].items()} == {'fr': 'Titre', 'en': 'Title'}

        # sur un sous-dictionnaire
        creator_dict = dataset_dict.new_item('creator')
        creator_dict.set_value('name', '???', 'en')
        creator_dict.set_value('name', 'Name', 'en')
        creator_dict.set_value('name', ['Nom'], 'fr')
        assert {k: v for k, v in creator_dict['name'].items()} == {'en': 'Name', 'fr': 'Nom'}

    def test_add_translatable_values_to_dict_field(self):
        """Contrôle le dictionnaire résultant lorsqu'on ajoute des valeurs à un champ admettant plusieurs valeurs traduisibles."""

        dataset_dict = EcospheresDatasetDict(SIMPLE_DATASET_SCHEMA, main_language='en')

        dataset_dict.set_value('free_tag', 'keyword 1', 'en')
        dataset_dict.set_value('free_tag', 'keyword 2')
        dataset_dict.set_value('free_tag', ['mot-clé 3', 'mot-clé 4'], 'fr')
        dataset_dict.set_value('free_tag', [], 'it')

        assert {k: [v for v in l] for k, l in dataset_dict['free_tag'].items()} == {
            'en': ['keyword 1', 'keyword 2'],
            'fr': ['mot-clé 3', 'mot-clé 4']
        }

    def test_do_not_set_empty_values_to_dict_field(self):
        """Vérifie que les tentatives d'ajout d'une valeur vide à un champ sont ignorées sauf s'il n'admet qu'une valeur non traduisible."""

        dataset_dict = EcospheresDatasetDict(SIMPLE_DATASET_SCHEMA)

        # champ n'admettant qu'une valeur non traduisible
        dataset_dict.set_value('version', 'v1')
        assert dataset_dict['version'] == 'v1'
        dataset_dict.set_value('version', None)
        assert dataset_dict['version'] is None

        # idem avec une valeur "vide" autre que None
        dataset_dict.set_value('version', 'v1')
        assert dataset_dict['version'] == 'v1'
        dataset_dict.set_value('version', '   \n')
        assert dataset_dict['version'] is None

        # champ admettant plusieurs valeurs non traduisibles
        dataset_dict.set_value('category', 'namespace:theme')
        dataset_dict.set_value('category', None)
        assert [v for v in dataset_dict['category']] == ['namespace:theme']

        # idem + valeur "vide" autre que None parmi les valeurs d'une liste
        dataset_dict.set_value('category', ['\r', 'namespace:theme2'])
        assert [v for v in dataset_dict['category']] == ['namespace:theme', 'namespace:theme2']

        # champ admettant une unique valeur traduisible
        dataset_dict.set_value('title', 'Nom', 'fr')
        dataset_dict.set_value('title', None, 'fr')
        assert {k: v for k, v in dataset_dict['title'].items()} == {'fr': 'Nom'}

        # champ admettant plusieurs valeurs traduisibles
        dataset_dict.set_value('free_tag', 'keyword 1', 'en')
        dataset_dict.set_value('free_tag', None, 'en')
        assert {k: [v for v in l] for k, l in dataset_dict['free_tag'].items()} == {'en': ['keyword 1']}

    def test_remove_values_from_dict_field(self):
        """Vérifie que la suppression des valeurs des champs fonctionne correctement."""

        dataset_dict = EcospheresDatasetDict(SIMPLE_DATASET_SCHEMA)

        # champ n'admettant qu'une valeur non traduisible
        dataset_dict.set_value('version', 'v1')
        dataset_dict.delete_values('version')
        assert dataset_dict['version'] is None

        # champ admettant plusieurs valeurs non traduisibles
        dataset_dict.set_value('category', ['namespace:theme1', 'namespace:theme2'])
        assert len(dataset_dict['category']) == 2
        dataset_dict.delete_values('category')
        assert len(dataset_dict['category']) == 0

        # champ admettant une unique valeur traduisible
        dataset_dict.set_value('title', 'Titre', 'fr')
        dataset_dict.set_value('title', 'Title', 'en')
        dataset_dict.set_value('title', 'Titolo', 'it')
        assert len(dataset_dict['title']) == 3

        # ... en spécifiant une langue non référencée
        dataset_dict.delete_values('title', language='es')
        assert len(dataset_dict['title']) == 3

        # ... en spécifiant une langue référencée
        dataset_dict.delete_values('title', language='en')
        assert {k: v for k, v in dataset_dict['title'].items()} == {'fr': 'Titre', 'it': 'Titolo'}

        # ... sans spécifier de langue
        dataset_dict.delete_values('title')
        assert len(dataset_dict['title']) == 0

        # champ admettant plusieurs valeurs traduisibles
        dataset_dict.set_value('free_tag', ['keyword 1', 'keyword 2'], 'en')
        dataset_dict.set_value('free_tag', ['mot-clé 3'], 'fr')
        assert len(dataset_dict['free_tag']) == 2

        # ... en spécifiant une langue non référencée
        dataset_dict.delete_values('free_tag', language='es')
        assert len(dataset_dict['free_tag']) == 2

        # ... en spécifiant une langue référencée
        dataset_dict.delete_values('free_tag', language='fr')
        assert {k: [v for v in l] for k, l in dataset_dict['free_tag'].items()} == {
            'en': ['keyword 1', 'keyword 2']
        }

        # ... sans spécifier de langue
        dataset_dict.delete_values('free_tag')
        assert len(dataset_dict['free_tag']) == 0        

    def test_remove_all_resources_from_dataset_dict(self):
        """Contrôle le bon déroulement de la suppression des ressources."""

        dataset_dict = EcospheresDatasetDict(SIMPLE_DATASET_SCHEMA)
        
        for i in range(3):
            dataset_dict.new_resource()
        assert len(dataset_dict['resources']) == 3

        dataset_dict.delete_resources()
        assert len(dataset_dict['resources']) == 0

    def test_add_extra_field_to_dataset_dict(self):
        """Teste l'ajout d'une valeur pour un champ non prévu par le schéma."""

        dataset_dict = EcospheresDatasetDict(SIMPLE_DATASET_SCHEMA)

        dataset_dict.set_value('truc', 'bidule')
        dataset_dict.set_value('autre', 'chose')
        dataset_dict.set_value('autre', 'machin', 'fr')
        dataset_dict.set_value('vide', '     ')

        assert dataset_dict['extras'] == [
            {
                'key': 'truc',
                'value': 'bidule'
            },
            {
                'key': 'autre',
                'value': 'machin'
            },
            {
                'key': 'vide',
                'value': None
            }
        ]

    def test_remove_extra_field_from_dataset_dict(self):
        """Teste l'ajout d'une valeur pour un champ non prévu par le schéma."""

        dataset_dict = EcospheresDatasetDict(SIMPLE_DATASET_SCHEMA)

        dataset_dict.set_value('truc', 'bidule')
        dataset_dict.set_value('autre', 'chose')
        dataset_dict.delete_values('truc')
        dataset_dict.delete_values('inconnu')

        assert dataset_dict['extras'] == [
            {
                'key': 'autre',
                'value': 'chose'
            }
        ]

