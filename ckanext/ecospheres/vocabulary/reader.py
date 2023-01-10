"""
Read vocabulary data from the database.

"""
import json, re
import logging
from pathlib import Path
from sqlalchemy import select, exists, and_, func, literal

from ckanext import __path__ as ckanext_path
from ckanext.ecospheres.vocabulary.loader import Session
from ckanext.ecospheres.vocabulary.parser.model import (
    VocabularyLabelTable, VocabularyAltLabelTable, VocabularyRegexpTable,
    VocabularyHierarchyTable, VocabularySpatialTable, VocabularySynonymTable
)

logger = logging.getLogger(__name__)

DEFAULT_LANGUAGE = 'en'

def get_table_name(vocabulary, modelclass):
    """Return the name of the database table for given type and vocabulary.

    Parameters
    ----------
    vocabulary : str
        Name of the vocabulary, ie its ``name``
        property in ``vocabularies.yaml``.
    modelclass : type
        A subclass of :py:class:`VocabularyDataTable`.

    Returns
    -------
    str

    """
    table = modelclass.__call__(vocabulary)
    return f'{table.schema}.{table.name}'

def get_table_sql(vocabulary, modelclass):
    """Return the sqlalchemy table definition for given type and vocabulary.

    Parameters
    ----------
    vocabulary : str
        Name of the vocabulary, ie its ``name``
        property in ``vocabularies.yaml``.
    modelclass : type
        A subclass of :py:class:`VocabularyDataTable`.

    Returns
    -------
    sqlalchemy.sql.schema.Table

    """
    table = modelclass.__call__(vocabulary)
    return table.sql

class VocabularyReader:
    """Read vocabulary data from the database."""

    @classmethod
    def is_known_uri(cls, vocabulary, uri, database=None):
        """Is the URI registered in given vocabulary ?

        Parameters
        ----------
        vocabulary : str
            Name of the vocabulary, ie its ``name``
            property in ``vocabularies.yaml``.
        uri : str
            Some URI to test.
        database : str, optional
            URL of the database where the vocabulary is stored,
            ie ``dialect+driver://username:password@host:port/database``.
            If not provided, the main CKAN PostgreSQL database will be used.
        
        Returns
        -------
        bool
            ``True`` if the vocabulary exists, is available and
            contains the URI, else ``False``.
        
        """
        if not vocabulary or not uri:
            return False
        with Session(database=database) as s:
            try:
                table_sql = get_table_sql(vocabulary, VocabularyLabelTable)
                stmt = exists(table_sql.c.uri).where(table_sql.c.uri == uri).select()
                res = s.execute(stmt)
                return res.scalar()
            except Exception as e:
                logger.error(
                    'Failed to look up URI "{0}" in vocabulary "{1}". {2}'.format(
                        uri, vocabulary, str(e)
                    )
                )
                return False

    @classmethod
    def get_label(cls, vocabulary, uri, language=None, database=None):
        """Get the label of the given URI.

        Parameters
        ----------
        vocabulary : str
            Name of the vocabulary, ie its ``name``
            property in ``vocabularies.yaml``.
        uri : str
            URI of a vocabulary item.
        language : str, optional
            The language the label should be written in. If not
            provided, the methop will look up a label in the language
            :py:data:`DEFAULT_LANGUAGE`. If there is none, one of the
            label of the URI is arbitrarily returned, if any.
            Likewise, the method will try to find a label in 
            :py:data:`DEFAULT_LANGUAGE` if `language` has no match.
            If it doesn't work, any label of the URI may be returned.
        case_sensitive : bool, default False
            If ``True``, the case will be considered when
            testing the labels.
        database : str, optional
            URL of the database where the vocabulary is stored,
            ie ``dialect+driver://username:password@host:port/database``.
            If not provided, the main CKAN PostgreSQL database will be used.
        
        Returns
        -------
        str or None
            The first matching URI. ``None`` if the vocabulary
            doesn't exist, is not available or there was
            no match for the URI.

        """
        if not vocabulary or not uri:
            return
        
        with Session(database=database) as s:
            try:
                table_sql = get_table_sql(vocabulary, VocabularyLabelTable)

                # with the provided language
                if language:
                    stmt = select(table_sql.c.label).where(
                        and_(
                            table_sql.c.uri == uri,
                            table_sql.c.language == language
                        )
                    )
                    res = s.execute(stmt)
                    val = res.scalar()
                    if val:
                        return val
                
                # with the default language
                stmt = select(table_sql.c.label).where(
                    and_(
                        table_sql.c.uri == uri,
                        table_sql.c.language == DEFAULT_LANGUAGE
                    )
                )
                res = s.execute(stmt)
                val = res.scalar()
                if val:
                    return val
                
                # without any language
                stmt = select(table_sql.c.label).where(
                    table_sql.c.uri == uri
                )
                res = s.execute(stmt)
                val = res.scalar()
                if val:
                    return val
                
            except Exception as e:
                logger.error(
                    'Failed to look up a label for URI'
                    ' "{0}" and language "{1}" in vocabulary "{2}". {3}'.format(
                        uri, language, vocabulary, str(e)
                    )
                )

    @classmethod
    def get_uri_from_label(
        cls, vocabulary, label, language=None, case_sensitive=False,
        database=None
    ):
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
        database : str, optional
            URL of the database where the vocabulary is stored,
            ie ``dialect+driver://username:password@host:port/database``.
            If not provided, the main CKAN PostgreSQL database will be used.
        
        Returns
        -------
        str or None
            The first matching URI. ``None`` if the vocabulary
            doesn't exist, is not available or there was
            no match for the label.
        
        """
        if not vocabulary or not label:
            return
        
        with Session(database=database) as s:
            try:
                for table in (VocabularyLabelTable, VocabularyAltLabelTable):
                    table_sql = get_table_sql(vocabulary, table)
                    if case_sensitive:
                        where_stmt = (table_sql.c.label == label)
                    else:
                        where_stmt = (func.lower(table_sql.c.label) == label.lower())
                    if language:
                        where_stmt = and_(where_stmt, (table_sql.c.language == language))
                    stmt = select(table_sql.c.uri).where(where_stmt)
                    res = s.execute(stmt)
                    uri = res.scalar()
                    if uri:
                        return uri
            except Exception as e:
                logger.error(
                    'Failed to look up label "{0}" in vocabulary "{1}". {2}'.format(
                        label, vocabulary, str(e)
                    )
                )

    @classmethod
    def get_uris_from_regexp(cls, vocabulary, terms, database=None):
        """Get all URIs whose regular expression matches any of the given terms.

        Parameters
        ----------
        vocabulary : str
            Name of the vocabulary, ie its ``name``
            property in ``vocabularies.yaml``.
        terms : list or tuple
            Metadata values to test against the regular
            expressions associated with the concepts.
        database : str, optional
            URL of the database where the vocabulary is stored,
            ie ``dialect+driver://username:password@host:port/database``.
            If not provided, the main CKAN PostgreSQL database will be used.
        
        Returns
        -------
        list(str)
            List of matching URIs. Result will be an empty list if the
            vocabulary doesn't exist, is not available, doesn't have
            a ``regexp`` table or there was no match for any term.
        
        """
        reslist = []

        if not vocabulary or not terms:
            return reslist

        with Session(database=database) as s:
            for term in terms:
                try:
                    table_sql = get_table_sql(vocabulary, VocabularyRegexpTable)
                    stmt = select(func.array_agg(table_sql.c.uri.distinct())).where(
                        literal(term).regexp_match(table_sql.c.regexp)
                    )
                    res = s.execute(stmt)
                    reslist += res.scalar()
                except Exception as e:
                    logger.error(
                        'Failed to look up regular expression matches of '
                        'term "{0}" in vocabulary "{1}". {2}'.format(
                            term, vocabulary, str(e)
                        )
                    )
        
        return reslist
    
    @classmethod
    def get_parents(cls, vocabulary, uri, database=None):
        """Get the URIs of the parent items.

        Parameters
        ----------
        vocabulary : str
            Name of the vocabulary, ie its ``name``
            property in ``vocabularies.yaml``.
        uri : str
            URI of a vocabulary item.
        database : str, optional
            URL of the database where the vocabulary is stored,
            ie ``dialect+driver://username:password@host:port/database``.
            If not provided, the main CKAN PostgreSQL database will be used.
        
        Returns
        -------
        list(str)
            list of the URIs of the parent items. Result will be an
            empty list if the vocabulary doesn't exist, is not available,
            doesn't have a ``hierarchy`` table, if the URI didn't exist
            in the vocabulary or if the item didn't have any parent.
        
        """
        if not vocabulary or not uri:
            return []
        
        with Session(database=database) as s:
            try:
                table_sql = get_table_sql(vocabulary, VocabularyHierarchyTable)
                stmt = select(func.array_agg(table_sql.c.parent.distinct())).where(
                    table_sql.c.child == uri
                )
                res = s.execute(stmt)
                return res.scalar() or []
            except Exception as e:
                logger.error(
                    'Failed to look up parent items of the URI'
                    ' "{0}" in vocabulary "{1}". {2}'.format(
                        uri, vocabulary, str(e)
                    )
                )
        
        return []
    
    @classmethod
    def get_synonyms(cls, vocabulary, uri, database=None):
        """Get the synonyms for the given URI.

        Parameters
        ----------
        vocabulary : str
            Name of the vocabulary, ie its ``name``
            property in ``vocabularies.yaml``.
        uri : str
            URI of a vocabulary item.
        database : str, optional
            URL of the database where the vocabulary is stored,
            ie ``dialect+driver://username:password@host:port/database``.
            If not provided, the main CKAN PostgreSQL database will be used.
        
        Returns
        -------
        list(str)
            list of synonyms. Result will be an empty list if the vocabulary
            doesn't exist, is not available, doesn't have a ``synonym`` table,
            if the URI didn't exist in the vocabulary or if the item didn't have
            any synonym.
        
        """
        if not vocabulary or not uri:
            return []
        
        with Session(database=database) as s:
            try:
                table_sql = get_table_sql(vocabulary, VocabularySynonymTable)
                stmt = select(func.array_agg(table_sql.c.synonym.distinct())).where(
                    table_sql.c.uri == uri
                )
                res = s.execute(stmt)
                return res.scalar() or []
            except Exception as e:
                logger.error(
                    'Failed to look up synonyms of the URI'
                    ' "{0}" in vocabulary "{1}". {2}'.format(
                        uri, vocabulary, str(e)
                    )
                )
        
        return []
    
    @classmethod
    def get_uri_from_synonym(cls, vocabulary, synonym, database=None):
        """Get one URI with matching synonym in given vocabulary, if any.

        Parameters
        ----------
        vocabulary : str
            Name of the vocabulary, ie its ``name``
            property in ``vocabularies.yaml``.
        synonym : str
            Synonym URI.
        database : str, optional
            URL of the database where the vocabulary is stored,
            ie ``dialect+driver://username:password@host:port/database``.
            If not provided, the main CKAN PostgreSQL database will be used.
        
        Returns
        -------
        str or None
            The first matching URI. ``None`` if the vocabulary
            doesn't exist, is not available, doesn't have a synonym table,
            or there was no match for the synonym URI.
        
        """
        if not vocabulary or not synonym:
            return
        
        with Session(database=database) as s:
            try:
                table_sql = get_table_sql(vocabulary, VocabularySynonymTable)
                stmt = select(table_sql.c.uri).where(
                    table_sql.c.synonym == synonym
                )
                res = s.execute(stmt)
                return res.scalar()
            except Exception as e:
                logger.error(
                    'Failed to look up an URI with synonym'
                    ' "{0}" in vocabulary "{1}". {2}'.format(
                        synonym, vocabulary, str(e)
                    )
                )
    
    @classmethod
    def get_ecospheres_territory(cls, vocabulary, uri, database=None):
        """Return the territory from the ecospheres_territory vocabulary best suited to represent the given URI.

        Parameters
        ----------
        vocabulary : {'eu_administrative_territory_unit', 'insee_official_geographic_code'}
            Name of the spatial vocabulary the URI is coming
            from.
        uri : str
            URI of some kind of spatial area.
        database : str, optional
            URL of the database where the vocabulary is stored,
            ie ``dialect+driver://username:password@host:port/database``.
            If not provided, the main CKAN PostgreSQL database will be used.
        
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
        
        territory = cls.get_uri_from_synonym(
            vocabulary='ecospheres_territory', synonym=uri, database=database
        )
        if territory:
            return territory
        
        if vocabulary == 'insee_official_geographic_code':

            # using synonyms
            synonyms = cls.get_synonyms(
                vocabulary=vocabulary, uri=uri, database=database
            )
            for synonym in synonyms:
                territory = cls.get_uri_from_synonym(
                    vocabulary='ecospheres_territory', synonym=synonym, database=database
                )
                if territory:
                    return territory
            
            synonyms.append(uri)

            # using supra territories
            parents = []
            for synonym in synonyms:
                parents += cls.get_parents(
                    vocabulary=vocabulary, uri=synonym, database=database
                )

            for parent in parents:
                territory = cls.get_uri_from_synonym(
                    vocabulary='ecospheres_territory', synonym=parent, database=database
                )
                if territory:
                    return territory

            # using supra territories synonyms
            parent_synonyms = []
            for parent in parents:
                parent_synonyms += cls.get_synonyms(
                    vocabulary=vocabulary, uri=parent, database=database
                )
            
            for parent_synonym in parent_synonyms:
                territory = cls.get_uri_from_synonym(
                    vocabulary='ecospheres_territory', synonym=parent_synonym, database=database
                )
                if territory:
                    return territory


class VocabularyJSONReader:
    
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
        VocabularyJSONReader(vocabulary)
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
        VocabularyJSONReader(vocabulary)
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
        VocabularyJSONReader(vocabulary)
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
            
            synonyms.append(uri)

            # using supra territories
            ogc_hierarchy_table = cls.table(vocabulary, 'hierarchy')
            parents = [
                row['parent'] for row in ogc_hierarchy_table if row['child'] in synonyms
            ]
            for parent in parents.copy():
                parents += cls.get_synonyms(vocabulary, parent)

            for row in synonym_table:
                if row['synonym'] in parents:
                    return row['uri']

