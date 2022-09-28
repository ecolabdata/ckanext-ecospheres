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
        uri : str
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
    def get_uris_from_regexp(cls, vocabulary, terms):
        """Get all URIs whose regular expression matches any of the given terms.

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
        list(str) or None
            List of matching URIs. Result will be an empty list if the
            vocabulary doesn't exist, is not available, doesn't have
            a ``regexp`` table or there was no match for any term.
        
        """
        res = []

        if not vocabulary or not terms:
            return res
        
        table = cls.table(vocabulary, 'regexp')
        if not table:
            return res

        for row in table:
            pattern = re.compile(row['regexp'], flags=re.I)
            if any(re.search(pattern, term) for term in terms):
                res.append(row['uri'])
        return res

    @classmethod
    def get_parents(cls, vocabulary, uri):
        """Get the URIs of the parent items.

        Parameters
        ----------
        vocabulary : str
            Name of the vocabulary, ie its ``name``
            property in ``vocabularies.yaml``.
        uri : str
            URI of a vocabulary item.
        
        Returns
        -------
        list(str)
            list of the URIs of the parent items. Result will be an
            empty list if the vocabulary doesn't exist, is not available,
            doesn't have a ``hierarchy`` table, if the URI didn't exist
            in the vocabulary or if the item didn't have any parent.

        """
        res = []

        if not vocabulary or not uri:
            return res
        
        table = cls.table(vocabulary, 'hierarchy')
        if not table:
            return res
        
        for row in table:
            if row.get('child') == uri:
                res.append(row.get('parent'))
        
        return res
    
    @classmethod
    def get_synonyms(cls, vocabulary, uri):
        """Get the synonyms for the given URI.

        Parameters
        ----------
        vocabulary : str
            Name of the vocabulary, ie its ``name``
            property in ``vocabularies.yaml``.
        uri : str
            URI of a vocabulary item.
        
        Returns
        -------
        list(str)
            list of synonyms. Result will be an empty list if the vocabulary
            doesn't exist, is not available, doesn't have a ``synonym`` table,
            if the URI didn't exist in the vocabulary or if the item didn't have
            any synonym.

        """
        res = []

        if not vocabulary or not uri:
            return res
        
        table = cls.table(vocabulary, 'synonym')
        if not table:
            return res
        
        for row in table:
            if row.get('uri') == uri:
                res.append(row.get('synonym'))
        
        return res

    @classmethod
    def get_ecospheres_territory(cls, vocabulary, uri):
        """Return the territory from the ecospheres_territory vocabulary best suited to represent the given URI.

        Parameters
        ----------
        vocabulary : str
            Name of the vocabulary the URI is coming
            from.
        uri : str
            URI of some kind of spatial area.
        
        Returns
        -------
        str
            The identifier of a territory from the ecospheres_territory
            vocabulary.

        """
        if not uri or not vocabulary in (
            'eu_administrative_territory_unit', 'insee_official_geographic_code'
        ):
            return

        synonym_table = cls.table('ecospheres_territory', 'synonym')
        for row in synonym_table:
            if row['synonym'] == uri:
                return row['uri']
        
        if vocabulary == 'insee_official_geographic_code':

            # using synonyms
            synonyms = cls.get_synonyms(vocabulary, uri)
            for synonym in synonyms:
                for row in synonym_table:
                    if row['synonym'] == synonym:
                        return row['uri']

            # using supra territories
            ogc_hierarchy_table = cls.table(vocabulary, 'hierarchy')
            parents = [
                row['parent'] for row in ogc_hierarchy_table if row['child'] == uri
            ]
            for parent in parents:
                parents += cls.get_synonyms(vocabulary, parent)

            for row in synonym_table:
                if row['synonym'] in parents:
                    return row['uri']
        

        

