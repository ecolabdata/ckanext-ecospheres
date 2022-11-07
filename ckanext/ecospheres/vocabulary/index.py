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

The result is a :py:class:`ckanext.ecospheres.vocabulary.parser.result.VocabularyParsingResult`
object holding the parsed vocabulary in its 
:py:attr:`ckanext.ecospheres.vocabulary.parser.result.VocabularyParsingResult.data`
attribute.

The boolean value of the object can be checked to
know if a critical error occured during the parsing. In this
case, no data will be available.

The :py:attr:`ckanext.ecospheres.vocabulary.parser.result.VocabularyParsingResult.status_code`
tells if other non critical errors occured. To check the complete absence
of error:

    >>> if result.status_code == 0:
    ...    pass

Whether critical or not, errors are stored in the 
:py:attr:`ckanext.ecospheres.vocabulary.parser.result.VocabularyParsingResult.log`
attribute, as a list of :py:class:`Exception` objects.

The vocabulary data is stored in a
:py:class:`ckanext.ecospheres.vocabulary.parser.model.VocabularyDataCluster`
object. The simplest way to work with a cluster would be to
handle it as a list of tables. Tables are list of dictionaries. Each item is a
table row, the dictionary provides the values for each field (field names are
the keys, all fields are present for every item though they might be empty).

The structure of the table can be infered from its type.

Some types are mandatory in a cluster:

* :py:class:`ckanext.ecospheres.vocabulary.parser.model.VocabularyLabelTable`
* :py:class:`ckanext.ecospheres.vocabulary.parser.model.VocabularyAltLabelTable`

Others are optional:

* :py:class:`ckanext.ecospheres.vocabulary.parser.model.VocabularyHierarchyTable`
* :py:class:`ckanext.ecospheres.vocabulary.parser.model.VocabularySynonymTable`
* :py:class:`ckanext.ecospheres.vocabulary.parser.model.VocabularyRegexpTable`
* :py:class:`ckanext.ecospheres.vocabulary.parser.model.VocabularySpatialTable`

To quickly load and dump all vocabulary data as JSON:

    >>> results = VocabularyIndex.load_and_dump_all()

Or just one:

    >>> result = VocabularyIndex.load_and_dump('ecospheres_theme')

To save as RDF all vocabulary data previously stored as JSON:

    >>> graph = VocabularyIndex.to_rdf()

Or just one:

    >>> graph = VocabularyIndex.to_rdf('ecospheres_theme')

"""

import yaml, json
from pathlib import Path
from rdflib import (
    Graph, URIRef, Literal, SKOS, RDF
)

from ckanext.ecospheres.vocabulary.parser import parsers
from ckanext.ecospheres.vocabulary import __path__ as vocabulary_path
from ckanext import __path__ as ckanext_path

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

    @classmethod
    def to_rdf(
        cls, name=None, dirpath=None, all_in_one=False,
        do_not_save=False, update=False, languages=None
    ):
        """Build a RDF graph from a vocabulary serialized as JSON.

        Graphs are stored as turtle files - either one graph
        for all vocabularies or one graph per vocabulary
        according to the value of `all_in_one`.

        This method can only be used if the vocabulary
        is available as JSON data in the ``vocabularies`` 
        directory, else it does nothing and returns an
        empty graph.

        Only standard tables will be managed: labels,
        hierarchy and synonyms. Alternative labels are not
        supported for now, because it's not possible to
        determine the right property to use. ``skos:altLabel``
        wouldn't be appropriate for an identifiers, for instance.

        Schemes are not stored in the vocabulary data, and
        often didn't exist to begin with. The method will
        use the scheme referenced in the ``vocabularies.yaml``
        file. If there is none, the function does nothing and
        returns an empty graph.

        Parameters
        ----------
        name : str or list(str), optional
            Name of the vocabulary or vocabularies. If not
            provided, all available vocabularies in
            the ``vocabularies`` directory will be considered.
        dirpath : str or pathlib.Path, optional
            Path of the directory were RDF data should be
            stored. The function will try to create it
            if it doesn't already exists. If this isn't provided,
            the files will be stored in the ``vocabularies/rdf`` 
            subdirectory (created if needed).
        all_in_one : bool, default False
            If this is ``True``, all vocabularies are stored
            in one unique file named ``vocabularies.ttl``.
            Else the files will be named after the
            vocabulary, with a ``'.ttl'`` extension.
        do_not_save : bool, default False
            If this is ``True``, no data will be saved.
        update : bool, default False
            Force update of vocabulary properties from the
            ``vocabularies.yaml`` file.
        languages : list(str), optional
            If provided, only translatable values in the listed
            languages will be added to the vocabulary (especially
            for labels).
        
        Returns
        -------
        rdflib.graph.Graph

        """
        VocabularyIndex(update)
        vocabularies_path = Path(ckanext_path[0]).parent / 'vocabularies'
        if not vocabularies_path.exists() or not vocabularies_path.is_dir():
            raise FileNotFoundError('no "vocabularies" directory')

        dirpath = Path(dirpath) if dirpath else vocabularies_path / 'rdf'
        if not dirpath.exists() or not dirpath.is_dir():
            dirpath.mkdir()

        if isinstance(name, str):
            name = [name]

        main_graph = Graph()

        for file in vocabularies_path.iterdir():

            if not file.suffix == '.json' or (
                name and not file.stem in name
            ) or not file.stem in cls.VOCABULARY_INDEX:
                continue

            raw_data = file.read_text(encoding='utf-8')
            data = json.loads(raw_data)
            graph = Graph()

            # ----- Concept Scheme ------
            scheme_uri = cls.get(file.stem, 'eco_uri')
            scheme_labels = cls.get(file.stem, 'eco_label')
            if not scheme_uri:
                continue
            scheme_uri = URIRef(scheme_uri)
            graph.add(
                (
                    scheme_uri,
                    RDF.type,
                    SKOS.ConceptScheme
                )
            )
            for language, scheme_label in scheme_labels.items():
                if not languages or language in languages:
                    graph.add(
                        (
                            scheme_uri,
                            SKOS.prefLabel,
                            Literal(scheme_label, lang=language)
                        )
                    )

            # ------ Concepts ------
            for table in data:
                if table.endswith('_label'):
                    for item in data[table]:
                        graph.add(
                            (
                                URIRef(item['uri']),
                                RDF.type,
                                SKOS.Concept
                            )
                        )
                        graph.add(
                            (
                                URIRef(item['uri']),
                                SKOS.inScheme,
                                scheme_uri
                            )
                        )
                        if not languages or item['language'] in languages:
                            graph.add(
                                (
                                    URIRef(item['uri']),
                                    SKOS.prefLabel,
                                    Literal(item['label'], lang=item['language'])
                                )
                            )

            for table in data:
                # new iteration, because concepts
                # should be added first
                if table.endswith('_synonym'):
                    for item in data[table]:
                        graph.add(
                            (
                                URIRef(item['uri']),
                                RDF.type,
                                SKOS.Concept
                            )
                        )
                        graph.add(
                            (
                                URIRef(item['uri']),
                                SKOS.exactMatch,
                                URIRef(item['synonym'])
                            )
                        )

                if table.endswith('_hierarchy'):
                    for item in data[table]:
                        if (
                            (URIRef(item['parent']), RDF.type, SKOS.Concept) in graph
                            and (URIRef(item['child']), RDF.type, SKOS.Concept)
                        ):
                            graph.add(
                                (
                                    URIRef(item['parent']),
                                    SKOS.narrower,
                                    URIRef(item['child'])
                                )
                            )
            
            # ------ Individual storage ------
            if graph and not do_not_save and not all_in_one:
                graph.serialize(
                    destination=dirpath / f'{file.stem}.ttl',
                    encoding='utf-8'
                    )
            
            main_graph += graph

        # ------ Global storage ------
        if main_graph and not do_not_save and all_in_one:
            main_graph.serialize(
                destination=dirpath / f'vocabularies.ttl',
                encoding='utf-8'
                )

        return main_graph
