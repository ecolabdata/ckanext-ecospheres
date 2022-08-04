from builtins import object

from ckanext.ecospheres.vocabulary.parser import VocabularyDataCluster, VocabularyDataTable

class TestVocabularyDataTable(object):
    
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

    def test_do_not_fail_if_no_field(self):
        """Vérifie qu'il est possible de ne spécifier aucun champ à la création de la table."""
        table = VocabularyDataTable(
            'somevoc', 'somevoc_my_table', None
        )
        assert table.fields == ()

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

    def test_create_table_with_not_null_constraint(self):
        """Contrôle la création d'une table avec contrainte de non nullité."""
        table = VocabularyDataTable(
            'somevoc', 'my_table', ('field_1', 'field_2'), not_null=['field_2']
        )
        assert table.constraints[0] == 'field_2'
        assert repr(table.constraints[0]) == 'field_2 IS NOT NULL'
    
    def test_not_null_constraints_on_unknown_fields_are_ignored(self):
        """Vérifie que les contraintes de non nullité qui ne portent pas sur des champs de la table sont ignorées."""
        table = VocabularyDataTable(
            'somevoc', 'my_table', ('field_1', 'field_2'),
            not_null=['field_2', 'field_3']
        )
        assert len(table.constraints) == 1
        assert repr(table.constraints[0]) == 'field_2 IS NOT NULL'

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

    def test_create_table_with_unique_constraint(self):
        """Contrôle la création d'une table avec contraintes d'unicité'."""
        table = VocabularyDataTable(
            'somevoc', 'my_table', ('field_1', 'field_2', 'field_3'),
            unique=['field_1', ('field_2', 'field_3')]
        )
        assert len(table.constraints) == 2
        assert table.constraints[0] == ('field_1',)
        assert repr(table.constraints[0]) == '(field_1) IS UNIQUE'
        assert table.constraints[1] == ('field_2', 'field_3')
        assert repr(table.constraints[1]) == '(field_2, field_3) IS UNIQUE'

    def test_unique_constraints_on_unknown_fields_are_ignored(self):
        """Vérifie que les contraintes d'unicité qui ne portent pas sur des champs de la table sont ignorées."""
        table = VocabularyDataTable(
            'somevoc', 'my_table', ('field_1', 'field_2'),
            unique=['field_1', ('field_2', 'field_3')]
        )
        assert len(table.constraints) == 1
        assert repr(table.constraints[0]) == '(field_1) IS UNIQUE'

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


class TestVocabularyDataCluster(object):

    def test_new_cluster_comes_with_label_and_altlabel_tables(self):
        """Vérifie qu'un nouveau cluster contient automatiquement les tables label et altlabel."""
        cluster = VocabularyDataCluster('somevoc')
        assert getattr(cluster, 'label', None) is not None
        assert getattr(cluster, 'somevoc_label', None) is not None
        assert getattr(cluster, 'altlabel', None) is not None
        assert getattr(cluster, 'somevoc_altlabel', None) is not None


class TestDataValidation(object):
    
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
        cluster.label.add('uri:2', language='en')
        cluster.label.add(language='en', label='label3')
        cluster.label.add('uri:4', 'en', 'label4')
        cluster.label.add() # 2 NOT NULL anomalies
        assert len(cluster.label) == 5
        response = cluster.label.validate()
        assert len(response) == 4
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
        cluster.label.add('uri:1', label='label1-b')
        cluster.label.add('uri:2', label='label2-en', language='en')
        cluster.label.add('uri:3', 'en', label='label3-en')
        cluster.label.add('uri:3', 'fr', label='label3-fr')
        cluster.label.add('uri:3', 'fr', 'label3-fr-b')
        cluster.label.add('uri:3', 'fr', 'label3-fr-c')
        cluster.label.add('uri:4', language='en')
        cluster.label.add()
        cluster_save = cluster.copy()
        assert len(cluster.label) == 9
        response = cluster.label.validate(delete=False)
        assert not response
        assert len(response) == 6
        assert len(cluster.label) == 9
        assert cluster == cluster_save

