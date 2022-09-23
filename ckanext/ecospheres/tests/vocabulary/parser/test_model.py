from builtins import object
import pytest

from ckanext.ecospheres.vocabulary.parser.model import (
    InvalidConstraintError, TableNotNullConstraint, VocabularyDataCluster, VocabularyDataTable
)

class TestVocabularyDataTable(object):
    """Ensemble de tests relatif à la création et la configuration des tables."""
    
    def test_vocabulary_added_as_table_name_prefix_when_missing(self):
        """Vérifie que le nom du vocabulaire est bien ajouté au début du nom de la table quand il n'y était pas."""
        table = VocabularyDataTable('somevoc', 'my_table', ('field_1', 'field_2'))
        assert table.name == 'somevoc_my_table'

    def test_vocabulary_not_added_as_table_name_prefix_when_already_there(self):
        """Vérifie que le nom du vocabulaire n'est pas ajouté au début du nom de la table quand il y est déjà."""
        table = VocabularyDataTable('somevoc', 'somevoc_my_table', ('field_1', 'field_2'))
        assert table.name == 'somevoc_my_table'
    
    def test_discard_repeated_fields(self):
        """Vérifie qu'un champ listé plusieurs fois n'est considéré que la première fois."""
        table = VocabularyDataTable(
            'somevoc', 'somevoc_my_table', ('field_1', 'field_2', 'field_1')
        )
        assert table.fields == ('field_1', 'field_2')

    def test_creation_do_not_fail_if_no_field(self):
        """Vérifie qu'il est possible de ne spécifier aucun champ à la création de la table."""
        table = VocabularyDataTable(
            'somevoc', 'somevoc_my_table', None
        )
        assert table.fields == ()

    def test_create_table_with_not_null_constraint(self):
        """Contrôle la création d'une table avec contrainte de non nullité."""
        table = VocabularyDataTable(
            'somevoc', 'my_table', ('field_1', 'field_2'), not_null=['field_2']
        )
        assert table.constraints[0] == 'field_2'
        assert repr(table.constraints[0]) == 'field_2 IS NOT NULL'
    
    def test_not_null_constraints_on_unknown_fields_raise_an_error(self):
        """Vérifie que les contraintes de non nullité qui ne portent pas sur des champs de la table provoquent des erreurs."""
        with pytest.raises(InvalidConstraintError):
            VocabularyDataTable(
                'somevoc', 'my_table', ('field_1', 'field_2'),
                not_null=['field_2', 'field_3']
            )

    def test_a_not_null_constraint_is_only_defined_once(self):
        """Vérifie que les contraintes de non nullité dupliquées sont ignorées à la création."""
        table = VocabularyDataTable(
            'somevoc', 'my_table', ('field_1', 'field_2'),
            not_null=[
                'field_2', 'field_2', 'field_1'
            ]
        )
        assert len(table.constraints) == 2
        assert repr(table.constraints[0]) == 'field_2 IS NOT NULL'
        assert repr(table.constraints[1]) == 'field_1 IS NOT NULL'

    def test_set_not_null_constraint_after_creation(self):
        """Vérifie que la méthode qui permet de définir une contrainte de non nullité a posteriori est opérationnelle."""
        table = VocabularyDataTable(
            'somevoc', 'my_table', ('field_1', 'field_2'),
            not_null=['field_2']
        )
        table.set_not_null_constraint('field_1')
        assert len(table.constraints) == 2
        assert repr(table.constraints[0]) == 'field_2 IS NOT NULL'
        assert repr(table.constraints[1]) == 'field_1 IS NOT NULL'

    def test_create_table_with_unique_constraint(self):
        """Contrôle la création d'une table avec contraintes d'unicité'."""
        table = VocabularyDataTable(
            'somevoc', 'my_table', ('field_1', 'field_2', 'field_3'),
            unique=['field_1', ('field_2', 'field_3')]
        )
        assert len(table.constraints) == 2
        assert table.constraints[0] == ('field_1',)
        assert repr(table.constraints[0]) == '(field_1) IS UNIQUE'
        assert table.constraints[0].none_as_value
        assert table.constraints[1] == ('field_2', 'field_3')
        assert repr(table.constraints[1]) == '(field_2, field_3) IS UNIQUE'

    def test_unique_constraints_on_unknown_fields_raise_an_error(self):
        """Vérifie que les contraintes d'unicité qui ne portent pas sur des champs de la table provoquent des erreurs."""
        with pytest.raises(InvalidConstraintError):
            VocabularyDataTable(
                'somevoc', 'my_table', ('field_1', 'field_2'),
                unique=['field_1', ('field_2', 'field_3')]
            )

    def test_a_unique_constraint_is_only_defined_once(self):
        """Vérifie que les contraintes d'unicités dupliquées sont ignorées à la création."""
        table = VocabularyDataTable(
            'somevoc', 'my_table', ('field_1', 'field_2', 'field_3'),
            unique=[
                'field_2', ('field_2', 'field_3'),
                ('field_3', 'field_2'), 'field_2'
            ]
        )
        assert len(table.constraints) == 2
        assert table.constraints[0] == ('field_2',)
        assert repr(table.constraints[0]) == '(field_2) IS UNIQUE'
        assert table.constraints[1] == ('field_2', 'field_3')
        assert repr(table.constraints[1]) == '(field_2, field_3) IS UNIQUE'

    def test_set_unique_constraint_after_creation(self):
        """Vérifie que la méthode qui permet de définir une contrainte d'unicité' a posteriori est opérationnelle."""
        table = VocabularyDataTable(
            'somevoc', 'my_table', ('field_1', 'field_2')
        )
        table.set_unique_constraint(('field_1',), none_as_value=False)
        assert len(table.constraints) == 1
        assert repr(table.constraints[0]) == '(field_1) IS UNIQUE'
        assert not table.constraints[0].none_as_value

class TestDataAddition(object):
    """Ensemble de tests contrôlant l'ajout de données à une table."""

    def test_add_empty_record(self):
        """Contrôle l'ajout d'un enregistrement sans données."""
        table = VocabularyDataTable('somevoc', 'my_table', ('field_1', 'field_2'))
        item = table.add()
        assert item == {'field_1': None, 'field_2': None}

    def test_add_data_with_keyword_arguments(self):
        """Contrôle l'ajout de données à une table via des paramètres nommés."""
        table = VocabularyDataTable('somevoc', 'my_table', ('field_1', 'field_2'))
        item = table.add(field_2='a', field_1='b')
        assert item == {'field_1': 'b', 'field_2': 'a'}

    def test_unknown_fields_are_ignored_when_adding_data(self):
        """Vérifie que les références à des champs non définis sont ignorées lors de l'ajout de données."""
        table = VocabularyDataTable('somevoc', 'my_table', ('field_1', 'field_2'))
        item = table.add(field_2='a', field_1='b', field_3='c')
        assert item == {'field_1': 'b', 'field_2': 'a'}

    def test_add_data_with_positional_arguments(self):
        """Contrôle l'ajout de données à une table avec des arguments positionnels."""
        table = VocabularyDataTable('somevoc', 'my_table', ('field_1', 'field_2'))
        item = table.add('a', 'b')
        assert item == {'field_1': 'a', 'field_2': 'b'}

    def test_surnumeral_arguments_are_ignored_when_adding_data(self):
        """Vérifie que, s'il y a plus de données que de champs, les données excédentaires sont ignorées."""
        table = VocabularyDataTable('somevoc', 'my_table', ('field_1', 'field_2'))
        item = table.add('a', 'b', 'c')
        assert item == {'field_1': 'a', 'field_2': 'b'}

    def test_add_data_with_keyword_and_positional_arguments(self):
        """Vérifie qu'il est possible d'ajouter des données en mêlant les arguments nommés et positionnels"""
        table = VocabularyDataTable('somevoc', 'my_table', ('field_1', 'field_2'))
        item = table.add('a', 'c', field_2='b')
        assert item == {'field_1': 'a', 'field_2': 'b'}

class TestVocabularyDataCluster(object):
    """Ensemble de tests relatifs à la création et manipulation d'un cluster."""

    def test_new_cluster_comes_with_label_and_altlabel_tables(self):
        """Vérifie qu'un nouveau cluster contient automatiquement les tables label et altlabel."""
        cluster = VocabularyDataCluster('somevoc')
        assert getattr(cluster, 'label', None) is not None
        assert getattr(cluster, 'somevoc_label', None) is not None
        assert getattr(cluster, 'altlabel', None) is not None
        assert getattr(cluster, 'somevoc_altlabel', None) is not None

    def test_add_a_custom_table_to_the_cluster(self):
        """Vérifie qu'il est possible d'ajouter une table au cluster."""
        cluster = VocabularyDataCluster('somevoc')
        table_name = cluster.table('custom', ('uri', 'geom'))
        assert table_name == 'somevoc_custom'
        assert cluster.somevoc_custom == []
        assert cluster.get('somevoc_custom') is cluster.somevoc_custom
        assert cluster.somevoc_custom.name == 'somevoc_custom'
        assert cluster.somevoc_custom.fields == ('uri', 'geom')
    
    def test_cluster_is_a_properly_structured_json_like_object(self):
        """Vérifie que la structure du cluster est conforme au modèle."""
        cluster = VocabularyDataCluster('somevoc')
        cluster.table('custom', ('uri', 'comment'))
        cluster.label.add('uri:1', 'en', 'label1-en')
        cluster.label.add('uri:1', 'fr', 'label1-fr')
        cluster.label.add('uri:2', 'en', 'label2-en')
        cluster.somevoc_custom.add('uri:2', 'something to say')
        assert cluster == {
            'somevoc_label': [
                {
                    'uri': 'uri:1',
                    'language': 'en',
                    'label': 'label1-en'
                },
                {
                    'uri': 'uri:1',
                    'language': 'fr',
                    'label': 'label1-fr'
                },
                {
                    'uri': 'uri:2',
                    'language': 'en',
                    'label': 'label2-en'
                }
            ],
            'somevoc_altlabel': [],
            'somevoc_custom': [
                {
                    'uri': 'uri:2',
                    'comment': 'something to say'
                }
            ]
        }

class TestDataExistence(object):
    """Ensemble de tests relatifs à la vérification de l'existence de données dans une table."""

    def test_when_said_row_exists_it_is_found(self):
        """Vérifie que la fonction exists trouve un enregistrement quand il y en a un."""
        table = VocabularyDataTable(
            'somevoc', 'my_table', ('field_1', 'field_2', 'field_3')
        )
        table.add('a', 'b', 'c')
        table.add('e', 'b', 'c')
        table.add('m', 'n')
        assert table.exists({'field_1': 'a', 'field_3': 'c'})
    
    def test_when_said_row_does_not_exist_it_is_not_found(self):
        """Vérifie que la fonction exists ne trouve rien quand il n'y a pas d'enregistrement correspondant aux conditions."""
        table = VocabularyDataTable(
            'somevoc', 'my_table', ('field_1', 'field_2', 'field_3')
        )
        table.add('a', 'b', 'c')
        table.add('e', 'b', 'c')
        table.add('m', 'n')
        assert not table.exists({'field_1': 'x', 'field_3': 'c'})

    def test_empty_row_always_exists_only_in_non_empty_table(self):
        """Vérifie que chercher une ligne vide dans la table équivaut à chercher si la table est vide."""
        table = VocabularyDataTable(
            'somevoc', 'my_table', ('field_1', 'field_2', 'field_3')
        )
        assert not table.exists({})
        table.add('a', 'b', 'c')
        assert table.exists({})

class TestDataValidation(object):
    """Ensemble de tests relatifs à la validation des données."""
    
    def test_response_is_true_when_all_data_is_valid(self):
        """Vérifie que la valeur booléenne du résultat de validation est True lorsque tout est valide."""
        cluster = VocabularyDataCluster('somevoc')
        cluster.label.add('uri:1', label='label1')
        cluster.label.add('uri:2', language='en', label='label2')
        response = cluster.label.validate()
        assert response
        assert len(response) == 0

    def test_not_null_infraction(self):
        """Vérifie que les enregistrements ne respectant pas les contraintes de non nullité sont correctement détectées à la validation."""
        cluster = VocabularyDataCluster('somevoc')
        cluster.label.add('uri:1', label='label1')
        cluster.label.add('uri:2', language='en')
        cluster.label.add('uri:3', language='en', label='label3')
        assert len(cluster.label) == 3
        response = cluster.label.validate()
        assert not response
        assert len(response) == 1
        assert response[0].get('uri') == 'uri:2'
        assert repr(response[0].constraint) == 'label IS NOT NULL'

    def test_not_null_anomalies_are_properly_deleted(self):
        """Contrôle la suppression des enregistrements ne respectant pas les contraintes de non nullité."""
        cluster = VocabularyDataCluster('somevoc')
        cluster.label.add('uri:1', label='label1')
        cluster.label.add('uri:2', language='en') # 1 NOT NULL anomaly
        cluster.label.add(language='en', label='label3') # 1 NOT NULL anomaly
        cluster.label.add('uri:4', 'en', 'label4')
        cluster.label.add() # 2 NOT NULL anomalies
        assert len(cluster.label) == 5
        response = cluster.label.validate()
        assert len([
            r for r in response
            if isinstance(r.constraint, TableNotNullConstraint)
        ]) == 4
        assert len(cluster.label) == 2
        assert {
            'uri': 'uri:4',
            'language': 'en',
            'label': 'label4'
        } in cluster.label
        assert {
            'uri': 'uri:1',
            'language': None,
            'label': 'label1'
        } in cluster.label
        response = cluster.label.validate()
        assert response

    def test_unique_infraction(self):
        """Vérifie que les enregistrements ne respectant pas les contraintes d'unicité sont correctement détectées à la validation."""
        cluster = VocabularyDataCluster('somevoc')
        cluster.label.add('uri:1', label='label1')
        cluster.label.add('uri:1', label='label1-b')
        cluster.label.add('uri:2', label='label2-en', language='en')
        cluster.label.add('uri:3', language='en', label='label3-en')
        cluster.label.add('uri:3', language='fr', label='label3-fr')
        cluster.label.add('uri:3', language='fr', label='label3-fr-b')
        cluster.label.add('uri:3', language='fr', label='label3-fr-c')
        assert len(cluster.label) == 7
        response = cluster.label.validate()
        assert not response
        assert len(response) == 3
        for anomalie in response:
            assert repr(anomalie.constraint) == '(language, uri) IS UNIQUE'
        assert {
            'uri': 'uri:1',
            'language': None,
            'label': 'label1-b'
        } in response
        assert {
            'uri': 'uri:3',
            'language': 'fr',
            'label': 'label3-fr-b'
        } in response
        assert {
            'uri': 'uri:3',
            'language': 'fr',
            'label': 'label3-fr-b'
        } in response

    def test_unique_anomalies_are_properly_deleted(self):
        """Contrôle la suppression des enregistrements ne respectant pas les contraintes d'unicité."""
        cluster = VocabularyDataCluster('somevoc')
        cluster.label.add('uri:1', label='label1')
        cluster.label.add('uri:1', label='label1-b')
        cluster.label.add('uri:2', label='label2-en', language='en')
        cluster.label.add('uri:3', 'en', label='label3-en')
        cluster.label.add('uri:3', 'fr', label='label3-fr')
        cluster.label.add('uri:3', 'fr', 'label3-fr-b')
        cluster.label.add('uri:3', 'fr', 'label3-fr-c')
        assert len(cluster.label) == 7
        response = cluster.label.validate()
        assert len(cluster.label) == 4
        assert {
            'uri': 'uri:1',
            'language': None,
            'label': 'label1'
        } in cluster.label
        assert {
            'uri': 'uri:2',
            'language': 'en',
            'label': 'label2-en'
        } in cluster.label
        assert {
            'uri': 'uri:3',
            'language': 'en',
            'label': 'label3-en'
        } in cluster.label
        assert {
            'uri': 'uri:3',
            'language': 'fr',
            'label': 'label3-fr'
        } in cluster.label
        response = cluster.label.validate()
        assert response

    def test_no_deletion_when_asked_so(self):
        """Vérifie que les anomalies ne sont pas supprimées quand delete vaut False."""
        cluster = VocabularyDataCluster('somevoc')
        cluster.label.add('uri:1', label='label1')
        cluster.label.add('uri:1', label='label1-b') # 1 UNIQUE anomaly
        cluster.label.add('uri:2', label='label2-en', language='en')
        cluster.label.add('uri:3', 'en', label='label3-en')
        cluster.label.add('uri:3', 'fr', label='label3-fr')
        cluster.label.add('uri:3', 'fr', 'label3-fr-b') # 1 UNIQUE anomaly
        cluster.label.add('uri:3', 'fr', 'label3-fr-c') # 1 UNIQUE anomaly
        cluster.label.add('uri:4', language='en') # 1 NOT NULL anomaly
        cluster.label.add() # 2 NOT NULL ANOMALY + 1 UNIQUE anomaly
        cluster_save = cluster.copy()
        assert len(cluster.label) == 9
        response = cluster.label.validate(delete=False)
        assert not response
        assert len(response) == 7
        assert len(cluster.label) == 9
        assert cluster == cluster_save

    def test_none_only_matches_itself_for_a_mono_field_unique_constraint_with_none_as_value(self):
        """Vérifie qu'une contrainte d'unicité portant sur un seul champ et avec none_as_value valant True ne fait jamais matcher None avec autre chose que lui-même."""
        table = VocabularyDataTable(
            'somevoc', 'my_table', ('f1', 'f2', 'f3')
        )
        table.set_unique_constraint(('f1',), none_as_value=True)
        table.add()
        table.add('v1-A', 'v2-A')
        response = table.validate()
        assert response
        assert len(table) == 2
        table.add(None, 'v2-B', 'v3-B')
        response = table.validate()
        assert not response
        assert table == [{'f1': None, 'f2': None, 'f3': None}, {'f1': 'v1-A', 'f2': 'v2-A', 'f3': None}]

    def test_none_only_matches_itself_for_a_multi_fields_unique_constraint_with_none_as_value(self):
        """Vérifie qu'une contrainte d'unicité portant sur plusieurs et avec none_as_value valant True ne fait jamais matcher None avec autre chose que lui-même."""
        table = VocabularyDataTable(
            'somevoc', 'my_table', ('f1', 'f2', 'f3')
        )
        table.set_unique_constraint(('f1', 'f2'), none_as_value=True)
        table.add()
        table.add('v1-A', 'v2-A')
        response = table.validate()
        assert response
        assert len(table) == 2
        table.add(None, 'v2-B', 'v3-B')
        response = table.validate()
        assert response
        assert len(table) == 3
        table.add(f3='v3-C')
        response = table.validate()
        assert not response
        assert table == [
            {'f1': None, 'f2': None, 'f3': None},
            {'f1': 'v1-A', 'f2': 'v2-A', 'f3': None},
            {'f1': None, 'f2': 'v2-B', 'f3': 'v3-B'}
        ]

    def test_a_mono_field_unique_constraint_without_none_as_value_doesnt_match_none_with_following_rows(self):
        """Vérifie qu'une contrainte d'unicité portant sur un seul champ et avec none_as_value valant False ne fait pas matcher None avec les valeurs des lignes suivantes."""
        table = VocabularyDataTable(
            'somevoc', 'my_table', ('f1', 'f2', 'f3')
        )
        table.set_unique_constraint(('f1',), none_as_value=False)
        table.add() # first value, so shouldn't match anything ever
        table.add('v1-A', 'v2-A')
        response = table.validate()
        assert response
        assert len(table) == 2

    def test_none_matches_anything_in_previous_rows_for_a_mono_field_unique_constraint_without_none_as_value(self):
        """Vérifie qu'une contrainte d'unicité portant sur un seul champ et avec none_as_value valant False fait matcher None avec n'importe quelle autre valeur des lignes précédentes."""
        table = VocabularyDataTable(
            'somevoc', 'my_table', ('f1', 'f2', 'f3')
        )
        table.set_unique_constraint(('f1',), none_as_value=False)
        table.add('v1-A', 'v2-A')
        table.add(None, 'v2-B', 'v3-B')
        response = table.validate()
        assert not response
        assert table == [{'f1': 'v1-A', 'f2': 'v2-A', 'f3': None}]

    def test_a_multi_fields_unique_constraint_without_none_as_value_doesnt_match_none_with_following_rows(self):
        """Vérifie qu'une contrainte d'unicité portant sur plusieurs champs et avec none_as_value valant False ne fait pas matcher None avec les valeurs des lignes suivantes."""
        table = VocabularyDataTable(
            'somevoc', 'my_table', ('f1', 'f2', 'f3')
        )
        table.set_unique_constraint(('f1', 'f2'), none_as_value=False)
        table.add() # first value, so shouldn't match anything ever
        table.add('v1-A', 'v2-A')
        response = table.validate()
        assert response
        assert len(table) == 2

    def test_none_matches_anything_in_previous_rows_for_a_multi_fields_unique_constraint_without_none_as_value(self):
        """Vérifie qu'une contrainte d'unicité portant sur plusieurs champs et avec none_as_value valant False fait matcher None avec n'importe quelle autre valeur des lignes précédentes."""
        table = VocabularyDataTable(
            'somevoc', 'my_table', ('f1', 'f2', 'f3')
        )
        table.set_unique_constraint(('f1', 'f2'), none_as_value=False)
        table.add('v1-A', 'v2-A')
        table.add(None, 'v2-B', 'v3-B')
        table.add(None, 'v2-A', 'v3-B')
        table.add()
        response = table.validate()
        assert not response
        assert table == [
            {'f1': 'v1-A', 'f2': 'v2-A', 'f3': None},
            {'f1': None, 'f2': 'v2-B', 'f3': 'v3-B'}
        ]
        assert response == [
            {'f1': None, 'f2': 'v2-A', 'f3': 'v3-B'},
            {'f1': None, 'f2': None, 'f3': None}
        ]

    def test_validate_one_row(self):
        """Contrôle le fonctionnement de l'utilitaire validation unitaire."""
        table = VocabularyDataTable(
            'somevoc', 'my_table', ('f1', 'f2', 'f3', 'f4'),
            not_null=('f3',),
            unique=('f3', 'f4')
        )
        table.set_unique_constraint(('f1', 'f2'), none_as_value=False)
        table.add('v1-A', 'v1-B', 'v1-C', 'v1-D')
        assert table.validate_one(table.build_row('v2-A', 'v2-B', 'v2-C', 'v2-D'))
        assert table.validate_one(table.build_row('v1-A', 'v2-B', 'v2-C', 'v2-D'))
        assert not table.validate_one(table.build_row('v1-A', 'v1-B', 'v2-C', 'v2-D'))
        assert table.validate_one(table.build_row(None, 'v2-B', 'v2-C', 'v2-D'))
        assert not table.validate_one(table.build_row(None, 'v1-B', 'v2-C', 'v2-D'))
        assert not table.validate_one(table.build_row('v2-A', 'v2-B', None, 'v2-D'))
        assert not table.validate_one(table.build_row('v2-A', 'v2-B', 'v1-C', 'v2-D'))
        assert table.validate_one(table.build_row('v2-A', 'v2-B', 'v2-C', None))
        assert not table.validate_one(table.build_row('v2-A', 'v2-B', 'v2-C', 'v1-D'))
        table.add('v2-A', 'v2-B', 'v2-C')
        assert table.validate_one(table.build_row('v3-A', 'v3-B', 'v3-C', 'v3-D'))
        assert not table.validate_one(table.build_row('v3-A', 'v3-B', 'v3-C', None))
        
    def test_validate_mono_field_reference_constraint_with_none_as_value(self):
        """Contrôle la validation des contraintes de référencement portant sur un champ unique lorsque None est considéré comme une valeur."""
        cluster = VocabularyDataCluster('voc')
        cluster.table('t1', ('f1',))
        cluster.table('t2', ('f2',))
        cluster.set_reference_constraint('voc_t2', 'f2', 'voc_t1', ('f1',), none_as_value=True)
        cluster.voc_t1.add('v1')
        cluster.voc_t2.add('v1')
        assert cluster.validate()
        cluster.voc_t2.add('v2')
        assert not cluster.validate()
        cluster.voc_t2.add(None)
        assert not cluster.validate()

    def test_validate_multi_fields_reference_constraint_with_none_as_value(self):
        """Contrôle la validation des contraintes de référencement portant sur plusieurs champs lorsque None est considéré comme une valeur."""
        cluster = VocabularyDataCluster('voc')
        cluster.table('t1', ('f1', 'f2'))
        cluster.table('t2', ('f1', 'f2'))
        cluster.set_reference_constraint('voc_t2', ('f1', 'f2'), 'voc_t1')
        cluster.voc_t1.add('v1a', 'v1b')
        cluster.voc_t1.add('v2a')
        cluster.voc_t2.add('v1a', 'v1b')
        assert cluster.validate()
        cluster.voc_t2.add('v2a')
        assert cluster.validate()
        cluster.voc_t2.add('v3a', 'v3b')
        assert not cluster.validate()
        cluster.voc_t2.add('v2a', 'v1b')
        assert not cluster.validate()
        cluster.voc_t2.add('v1a')
        assert not cluster.validate()

    def test_validate_mono_field_reference_constraint_without_none_as_value(self):
        """Contrôle la validation des contraintes de référencement portant sur un champ unique lorsque None est considéré comme un jocker."""
        cluster = VocabularyDataCluster('voc')
        cluster.table('t1', ('f1',))
        cluster.table('t2', ('f2',))
        cluster.set_reference_constraint('voc_t2', 'f2', 'voc_t1', ('f1',), none_as_value=False)
        cluster.voc_t1.add('v1')
        cluster.voc_t2.add('v1')
        assert cluster.validate()
        cluster.voc_t2.add('v2')
        assert not cluster.validate()
        cluster.voc_t2.add(None)
        assert cluster.validate()
    
    def test_validate_multi_fields_reference_constraint_without_none_as_value(self):
        """Contrôle la validation des contraintes de référencement portant sur plusieurs champs lorsque None est considéré comme un jocker."""
        cluster = VocabularyDataCluster('voc')
        cluster.table('t1', ('f1', 'f2'))
        cluster.table('t2', ('f1', 'f2'))
        cluster.set_reference_constraint('voc_t2', ('f1', 'f2'), 'voc_t1', none_as_value=False)
        cluster.voc_t1.add('v1a', 'v1b')
        cluster.voc_t1.add('v2a')
        cluster.voc_t2.add('v1a', 'v1b')
        assert cluster.validate()
        cluster.voc_t2.add('v2a')
        assert cluster.validate()
        cluster.voc_t2.add('v3a', 'v3b')
        assert not cluster.validate()
        cluster.voc_t2.add('v2a', 'v1b')
        assert not cluster.validate()
        cluster.voc_t2.add('v1a')
        assert cluster.validate()

    def test_hierarchy_table_can_be_accessed(self):
        """Vérifie que tout est en ordre avec la création de la table des relations."""
        cluster = VocabularyDataCluster('voc')
        assert cluster.hierarchy is None
        hierarchy_table = cluster.hierarchy_table()
        assert hierarchy_table == 'voc_hierarchy'
        assert isinstance(cluster.hierarchy, VocabularyDataTable)
        assert cluster.hierarchy == cluster['voc_hierarchy']



