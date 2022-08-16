
from builtins import object
from yaml import load, Loader
from pathlib import Path
from ckanext.ecospheres.vocabulary import __path__ as vocabulary_path

def _load_vocabularies():
    path = Path(vocabulary_path[0]) / 'vocabularies.yaml'
    with open(path, 'r') as src:
        return load(src.read(), Loader)

class TestEcospheresVocabularyIndex(object):

    def test_load_vocabularies(self):
        """Vérifie que le YAML contenant la liste des vocabulaires est dé-sérialisable."""
        vocabularies = _load_vocabularies()
        assert isinstance(vocabularies, list)
        assert len(vocabularies) > 1

    def test_each_vocabulary_has_a_name(self):
        """Vérifie que tous les vocabulaire ont une propriété name."""
        vocabularies = _load_vocabularies()
        for vocabulary in vocabularies:
            assert vocabulary.get('name')

