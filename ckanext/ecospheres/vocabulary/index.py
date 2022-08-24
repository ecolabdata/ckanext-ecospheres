"""Easy loading of vocabulary data from distant registers.

Information about the parsing of the vocabulary should be provided
through the ``vocabularies.yaml`` file.

This module allows to retrieve vocabulary data from the
vocabulary name:

    >>> res = VocabularyIndex.load('ecospheres_theme')

Additional parameters are passed down to the :py:func:`request.get`
function used to fetch the data from the register. This allows
providing of proxy mapping, authentification info, etc.

    >>> res = VocabularyIndex.load(
    ...     'ecospheres_theme',
    ...     proxies={'https': 'some.proxy'}
    ... )

"""

import yaml
from pathlib import Path

from ckanext.ecospheres.vocabulary.parser import parsers
from ckanext.ecospheres.vocabulary import __path__ as vocabulary_path

class VocabularyUnit:
    """Single vocabulary metadata.
    
    Attributes
    ----------
    name : str
        Name of the vocabulary.
    parser : function
        Function to call in order to fetch and parse the
        vocabulary data.
    **kwargs
        Keywords parameters for the parser.    
    
    """

    def __init__(self, name=None, parser=None, **kwargs):
        self.name = name
        if parser:
            if parser in parsers.__dict__:
                self.parser = parsers.__dict__[parser]
            else:
                raise ValueError(f"unknown parser for vocabulary '{name}'")
        else:
            self.parser = parsers.basic_rdf
        self.params = kwargs

class VocabularyIndex:
    """Access to vocabularies metadata and data.
    
    To load the index:
        >>> VocabularyIndex()

    To force the update of the (modified) index:
        >>> VocabularyIndex(True)

    Parameters
    ----------
    update : bool, default False
        If ``True``, data will be fetched from the
        ``vocabularies.yaml`` rather than using
        memorized information.

    """

    VOCABULARY_INDEX = {}

    def __new__(cls, update=False):
        if update or not cls.VOCABULARY_INDEX:
            yaml_path = Path(vocabulary_path[0]) / 'vocabularies.yaml'
            if not yaml_path.exists() or not yaml_path.is_file():
                raise FileNotFoundError('missing vocabularies.yaml file')
            with open(yaml_path, encoding='utf-8') as src:
                data = yaml.load(src, yaml.Loader)
            for vocabulary_params in data:
                if 'name' in vocabulary_params:
                    cls.VOCABULARY_INDEX[
                        vocabulary_params['name']
                    ] = VocabularyUnit(**vocabulary_params)
            
    @classmethod
    def load(cls, name, update=False, **kwargs):
        """Return parsed vocabulary data from a vocabulary name.

        This function reads the parsing parameters stored for the
        vocabulary in the ``vocabularies.yaml`` file and provides
        them to the suitable parser.

        Parameters
        ----------
        name : str
            Name of the vocabulary.
        update : bool, default False
            Force update of vocabulary properties from the
            ``vocabularies.yaml`` file. All vocabularies are
            update, not just the one targeted by this method.
        **kwargs : str
            Keyword parameters passed down to :py:func:`requests.get`,
            such as authentification info, proxy mapping, etc.

        Returns
        -------
        ckanext.ecospheres.vocabulary.parser.result.VocabularyParsingResult

        """
        VocabularyIndex(update)
        if name in cls.VOCABULARY_INDEX:
            params = {'name': name, 'url': None}
            params.update(kwargs)
            params.update(cls.VOCABULARY_INDEX[name].params)
            return cls.VOCABULARY_INDEX[name].parser.__call__(**params)
        else:
            raise ValueError(f"unknown vocabulary '{name}'")
