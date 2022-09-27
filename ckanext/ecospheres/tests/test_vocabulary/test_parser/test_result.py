from builtins import object

from ckanext.ecospheres.vocabulary.parser import exceptions
from ckanext.ecospheres.vocabulary.parser.result import (
    VocabularyParsingCompletedWithErrors,
    VocabularyParsingResult
)

class TestAddAndValidateLabel(object):
    """Ensemble de tests relatifs à l'ajout de labels au cluster de données et la validation subséquente."""
    
    def test_add_valid_label(self):
        """Vérifie que l'ajout de labels valides est accepté."""
        res = VocabularyParsingResult('voc')
        assert res.add_label(uri='domain:uri_1', label='label_1', language='en')
        assert res.add_label(uri='domain:uri_2', label='label_2', language='en')
        assert res.data.label
        assert res.data == {
            'voc_label': [
                {'uri': 'domain:uri_1', 'language': 'en', 'label': 'label_1'},
                {'uri': 'domain:uri_2', 'language': 'en', 'label': 'label_2'}
            ],
            'voc_altlabel': []
        }
        assert res.status_code == 0
        assert bool(res.status_code)
        assert not res.log
        assert res.data.validate()

    def test_add_label_without_uri(self):
        """Vérifie qu'il n'est pas permis d'ajouter un label sans URI."""
        res = VocabularyParsingResult('voc')
        assert not res.add_label(label='label_1', language='en')
        assert not res.data.label
        assert isinstance(res.status_code, VocabularyParsingCompletedWithErrors)
        assert res.status_code == 2
        assert bool(res.status_code)
        assert len(res.log) == 1
        assert isinstance(res.log[0], exceptions.InvalidDataError)
        assert repr(res.log[0].anomaly.constraint) == 'uri IS NOT NULL'
        assert str(res.log[0]) == (
            'row {"uri": null, "language": "en", "label": "label_1"} '
            'infringes the constraint "uri IS NOT NULL"'
        )
        assert res.data.validate()

    def test_add_label_without_label(self):
        """Vérifie qu'il n'est pas permis d'ajouter un label sans libellé."""
        res = VocabularyParsingResult('voc')
        assert not res.add_label(uri='domain:uri_1', language='en')
        assert not res.data.label
        assert isinstance(res.status_code, VocabularyParsingCompletedWithErrors)
        assert res.status_code == 2
        assert bool(res.status_code)
        assert len(res.log) == 1
        assert isinstance(res.log[0], exceptions.InvalidDataError)
        assert repr(res.log[0].anomaly.constraint) == 'label IS NOT NULL'
        assert str(res.log[0]) == (
            'row {"uri": "domain:uri_1", "language": "en", "label": null} '
            'infringes the constraint "label IS NOT NULL"'
        )
        assert res.data.validate()

    def test_add_alternative_label_with_language(self):
        """Vérifie que le second label fourni pour un language est stocké dans la table des labels alternatifs."""
        res = VocabularyParsingResult('voc')
        assert res.add_label(uri='domain:uri_1', label='label_1', language='en')
        assert res.add_label(uri='domain:uri_1', label='label_2', language='en')
        assert res.data.label
        assert res.data == {
            'voc_label': [
                {'uri': 'domain:uri_1', 'language': 'en', 'label': 'label_1'}
            ],
            'voc_altlabel': [
                {'uri': 'domain:uri_1', 'language': 'en', 'label': 'label_2'}
            ]
        }
        assert res.status_code == 0
        assert bool(res.status_code)
        assert not res.log
        assert res.data.validate()

    def test_add_label_without_language(self):
        """Vérifie que l'ajout de labels sans langue est toléré."""
        res = VocabularyParsingResult('voc')
        assert res.add_label(uri='domain:uri_1', label='label_1')
        assert res.add_label(uri='domain:uri_1', label='label_1b', language='en')
        assert res.add_label(uri='domain:uri_2', label='label_2')
        assert res.data.label
        assert res.data == {
            'voc_label': [
                {'uri': 'domain:uri_1', 'language': None, 'label': 'label_1'},
                {'uri': 'domain:uri_1', 'language': 'en', 'label': 'label_1b'},
                {'uri': 'domain:uri_2', 'language': None, 'label': 'label_2'}
            ],
            'voc_altlabel': []
        }
        assert res.status_code == 0
        assert bool(res.status_code)
        assert not res.log
        assert res.data.validate()

    def test_add_alternative_label_without_language(self):
        """Vérifie qu'un label sans langue est stocké dans la table des labels alternatifs s'il existe déjà un label pour l'URI."""
        res = VocabularyParsingResult('voc')
        assert res.add_label(uri='domain:uri_1', label='label_1', language='en')
        assert res.add_label(uri='domain:uri_1', label='label_2')
        assert res.data.label
        assert res.data == {
            'voc_label': [
                {'uri': 'domain:uri_1', 'language': 'en', 'label': 'label_1'}
            ],
            'voc_altlabel': [
                {'uri': 'domain:uri_1', 'language': None, 'label': 'label_2'}
            ]
        }
        assert res.status_code == 0
        assert bool(res.status_code)
        assert not res.log
        assert res.data.validate()

    def test_add_multiple_labels_without_language(self):
        """Vérifie que lorsqu'on ajoute un premier label sans langue, puis d'autres labels sans langues, ceux-ci sont considérés comme labels alternatifs."""
        res = VocabularyParsingResult('voc')
        assert res.add_label(uri='domain:uri_1', label='label_1')
        assert res.add_label(uri='domain:uri_1', label='label_2')
        assert res.data.label
        assert res.data == {
            'voc_label': [
                {'uri': 'domain:uri_1', 'language': None, 'label': 'label_1'}
            ],
            'voc_altlabel': [
                {'uri': 'domain:uri_1', 'language': None, 'label': 'label_2'}
            ]
        }
        assert res.status_code == 0
        assert bool(res.status_code)
        assert not res.log
        assert res.data.validate()
