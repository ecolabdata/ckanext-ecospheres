"""Easy loading of vocabulary data from distant registers.

Information about the parsing of the vocabulary should be provided
through the ``vocabularies.yaml`` file.

This module allows to retrieve vocabulary data from the
vocabulary name:

    >>> result = VocabularyIndex.load('ecospheres_theme')

Additional parameters are passed down to the :py:func:`request.get`
function used to fetch the data from the register. This allows
providing of proxy mapping, authentification info, etc.

    >>> result = VocabularyIndex.load(
    ...     'ecospheres_theme',
    ...     proxies={
    ...         'https': 'some.https.proxy',
    ...         'http': 'some.https.proxy'
    ...     }
    ... )

To quickly load and dump all vocabulary data as JSON:

    >>> results = VocabularyIndex.load_and_dump_all()

Or just one:

    >>> result = VocabularyIndex.load_and_dump('ecospheres_theme')

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
    def names(cls, available_only=True):
        """Générateur sur les noms de vocabulaires.

        Parameters
        ----------
        available_only : bool, default True
            If ``True``, vocabularies marked as unavailable
            are not considered.

        Yields
        ------
        str

        """
        VocabularyIndex()
        for name, unit in cls.VOCABULARY_INDEX.items():
            if unit.params.get('available') or not available_only:
                yield name

    @classmethod
    def get(cls, name, property):
        """Get property value for the given vocabulary.

        This method gives access to any property
        defined in the ``vocabularies.yaml`` file
        for the given vocabulary.

        Parameters
        ----------
        name : str
            Name of the vocabulary.
        property : str
            Name of the property.
        
        Returns
        -------
        str or int or bool or list or None
            The type of the returned value depends on the
            property. ``None`` if the property is not defined
            for the vocabulary.

        Raises
        ------
        ValueError
            If the vocabulary doesn't exist.

        """
        VocabularyIndex()
        if name in cls.VOCABULARY_INDEX:
            if property in ('name', 'parser'):
                return getattr(cls.VOCABULARY_INDEX[name], property, None)
            return cls.VOCABULARY_INDEX[name].params.get(property)
        else:
            raise ValueError(f"unknown vocabulary '{name}'")
    
    @classmethod
    def parser(cls, name):
        """Return the parser to use for the given vocabulary.

        Returns
        -------
        function

        Raises
        ------
        ValueError
            If the vocabulary doesn't exist.

        """
        VocabularyIndex()
        if name in cls.VOCABULARY_INDEX:
            return cls.VOCABULARY_INDEX[name].parser
        else:
            raise ValueError(f"unknown vocabulary '{name}'")

    @classmethod
    def params(cls, name):
        """Return the parsing parameters for the given vocabulary.

        Returns
        -------
        dict

        Raises
        ------
        ValueError
            If the vocabulary doesn't exist.

        """
        VocabularyIndex()
        if name in cls.VOCABULARY_INDEX:
            return cls.VOCABULARY_INDEX[name].params
        else:
            raise ValueError(f"unknown vocabulary '{name}'")

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

        Raises
        ------
        ValueError
            If the vocabulary doesn't exist.

        """
        VocabularyIndex(update)
        if name in VocabularyIndex.names():
            params = {'name': name, 'url': None}
            params.update(kwargs)
            params.update(VocabularyIndex.params(name))
            parser = VocabularyIndex.parser(name)
            return parser.__call__(**params)
        else:
            raise ValueError(f"unknown vocabulary '{name}'")

    @classmethod
    def load_and_dump(cls, name, update=False, permissive=False, **kwargs):
        """Load and dump data as JSON for the given vocabulary.

        Parameters
        ----------
        name : str
            Name of the vocabulary.
        update : bool, default False
            Force update of vocabulary properties from the
            ``vocabularies.yaml`` file. All vocabularies are
            update, not just the one targeted by this method.
        permissive : bool, default False
            If ``False`` the vocabulary data is only dumped when
            the parsing was fully successfull (ie there was no
            error at all).
            If ``True`` the vocabulary data is dumped as long
            as no critical error occurred.
        **kwargs : str
            Keyword parameters passed down to :py:func:`requests.get`,
            such as authentification info, proxy mapping, etc.

        Returns
        -------
        ckanext.ecospheres.vocabulary.parser.result.VocabularyParsingResult

        Raises
        ------
        ValueError
            If the vocabulary doesn't exist.

        """
        VocabularyIndex(update)
        res = VocabularyIndex.load(name, update=update, **kwargs)
        print(name, res.status_code)
        if res.status_code == 0 or permissive and res.status_code:
            res.data.dump()
        return res

    @classmethod
    def load_and_dump_all(cls, update=False, permissive=False, **kwargs):
        """Load and dump data as JSON for all available vocabularies.

        Parameters
        ----------
        update : bool, default False
            Force update of vocabulary properties from the
            ``vocabularies.yaml`` file.
        permissive : bool, default False
            If ``False`` the vocabulary data is only dumped when
            the parsing was fully successfull (ie there was no
            error at all).
            If ``True`` the vocabulary data is dumped as long
            as no critical error occurred.
        **kwargs : str
            Keyword parameters passed down to :py:func:`requests.get`,
            such as authentification info, proxy mapping, etc.

        Returns
        -------
        dict
            An dictionnary whose keys are vocabulary names and values are
            ckanext.ecospheres.vocabulary.parser.result.VocabularyParsingResult
            objects describing the parsing status of said vocabulary and holding
            parsing result.

        """
        VocabularyIndex(update)
        store = {}
        for name in VocabularyIndex.names():
            store[name] = VocabularyIndex.load_and_dump(
                name, update=update, permissive=permissive, **kwargs
            )
        return store

