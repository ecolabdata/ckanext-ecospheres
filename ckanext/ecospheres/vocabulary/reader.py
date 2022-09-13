"""

This module should be entirely rewritten to fetch vocabulary
data from the database rather than from JSON files.

"""

import json, re
from pathlib import Path
from ckanext import __path__ as ckanext_path

class VocabularyReader:
    
    VOCABULARY_DATABASE = {}

    def __new__(cls, vocabulary):
        if not vocabulary in cls.VOCABULARY_DATABASE:
            path = Path(ckanext_path[0]).parent / f'vocabularies/{vocabulary}.json'
            if not path.exists() or not path.is_file():
                raise FileNotFoundError(f"could not find vocabulary data for '{vocabulary}'")
            with open(path, 'r', encoding='utf-8') as src:
                data = json.load(src)
            cls.VOCABULARY_DATABASE.update(data)

    @classmethod
    def labels(cls, vocabulary):
        """Return labels' table for the given vocabulary
        
        Parameters
        ----------
        vocabulary : str
            Name of the vocabulary, ie its ``name``
            property in ``vocabularies.yaml``.
        
        Returns
        -------
        list

        """
        VocabularyReader(vocabulary)
        label_table = f'{vocabulary}_label'
        return cls.VOCABULARY_DATABASE[label_table]

    @classmethod
    def altlabels(cls, vocabulary):
        """Return alternative labels' table for the given vocabulary.
        
        Parameters
        ----------
        vocabulary : str
            Name of the vocabulary, ie its ``name``
            property in ``vocabularies.yaml``.
        
        Returns
        -------
        list

        """
        VocabularyReader(vocabulary)
        altlabel_table = f'{vocabulary}_altlabel'
        return cls.VOCABULARY_DATABASE[altlabel_table]

    @classmethod
    def table(cls, vocabulary, table_name):
        """Return the table with given name for the vocabulary, if any.

        Parameters
        ----------
        vocabulary : str
            Name of the vocabulary, ie its ``name``
            property in ``vocabularies.yaml``.
        table_name : str
            Table's name. If not prefixed with the vocabulary
            name, it will be added.
        
        Returns
        -------
        list
            The table or ``None`` if the vocabulary doesn't
            have a table with the given name.

        """
        VocabularyReader(vocabulary)
        if not table_name.startswith(f'{vocabulary}_'):
            table_name = f'{vocabulary}_{table_name}'
        return cls.VOCABULARY_DATABASE.get(table_name)

    @classmethod
    def is_known_uri(cls, vocabulary, uri):
        """Is the URI registered in given vocabulary ?

        Parameters
        ----------
        vocabulary : str
            Name of the vocabulary, ie its ``name``
            property in ``vocabularies.yaml``.
        uri : rdflib.term.URIRef or str
            Some URI to test.
        
        Returns
        -------
        bool
            ``True`` if the vocabulary exists, is available and
            contains the URI, else ``False``.
        
        """
        if not vocabulary or not uri:
            return False
        return any(row['uri'] == uri for row in cls.labels(vocabulary))

    @classmethod
    def get_uri_from_label(cls, vocabulary, label, language=None,
        case_sensitive=False):
        """Get one URI with matching label in given vocabulary, if any.

        This function will consider most RDF properties used for labels, 
        names, titles, notations, etc.

        Parameters
        ----------
        vocabulary : str
            Name of the vocabulary, ie its ``name``
            property in ``vocabularies.yaml``.
        label : str
            Some label to look up.
        language : str, optional
            If provided, a label will only be seen as
            matching if its language is `language`.
        case_sensitive : bool, default False
            If ``True``, the case will be considered when
            testing the labels.

        Returns
        -------
        str or None
            The first matching URI. ``None`` if the vocabulary
            doesn't exist, is not available or there was
            no match for the label.
        
        """
        if not vocabulary or not label:
            return
        
        for row in cls.labels(vocabulary):
            if (
                (not language or language == row['language']) and
                (
                    case_sensitive and label == row['label']
                    or not case_sensitive and label.lower() == row['label'].lower()
                )
            ):
                return row['uri']
        
        for row in cls.altlabels(vocabulary):
            if (
                (not language or language == row['language']) and
                (
                    case_sensitive and label == row['label']
                    or not case_sensitive and label.lower() == row['label'].lower()
                )
            ):
                return row['uri']

    @classmethod
    def get_uri_from_regexp(cls, vocabulary, terms):
        """Get one URI whose regular expression matches any of the given terms.

        Parameters
        ----------
        vocabulary : str
            Name of the vocabulary, ie its ``name``
            property in ``vocabularies.yaml``.
        terms : list or tuple
            Metadata values to test against the regular
            expressions associated with the concepts.
        
        Returns
        -------
        str or None
            The first matching URI. ``None`` if the vocabulary
            doesn't exist, is not available, doesn't have a ``regexp``
            table or there was no match for any term.
        
        """
        if not vocabulary or not terms:
            return
        
        table = cls.table(vocabulary, 'regexp')
        if not table:
            return

        for row in table:
            pattern = re.compile(row['regexp'], flags=re.I)
            if any(re.search(pattern, term) for term in terms):
                return row['uri']
        
