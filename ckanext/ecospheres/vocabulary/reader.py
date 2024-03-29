"""
Read vocabulary data from the database.

"""
import logging, re
from sqlalchemy import select, exists, and_, func, literal

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
    def fetch_data(cls, vocabulary, modelclass, add_count=False, database=None):
        """Fetch all data from a vocabulary table.

        Parameters
        ----------
        vocabulary : str
            Name of the vocabulary, ie its ``name``
            property in ``vocabularies.yaml``.
        modelclass : type
            A subclass of :py:class:`VocabularyDataTable`.
        add_count : bool, default False
            If this is ``True``, the method will add a 
            ``count`` attribute with value ``-1`` to all records.
        database : str, optional
            URL of the database where the vocabulary is stored,
            ie ``dialect+driver://username:password@host:port/database``.
            If not provided, the main CKAN PostgreSQL database will be used.

        Returns
        -------
        list(dict)
            A list of dictionnaries containing the attributes
            of each item of the table. The keys of the
            dictionnary are the names of the table's columns.
        
        """
        # TODO: If the 'count' key has no use, it shouldn't exist. [LL-2023.01.23]
        if not vocabulary:
            return []

        table_sql = get_table_sql(vocabulary, modelclass)

        try:
            with Session(database=database) as s:
                try:
                    if add_count:
                        stmt = f'''
                            WITH data_with_count AS (
                            SELECT *, -1 AS "count"
                                FROM {table_sql.schema}.{table_sql.name}
                            )
                            SELECT json_agg(to_json(data_with_count.*))
                                FROM data_with_count
                        '''
                    else:
                        stmt = f'''
                            SELECT json_agg(to_json({table_sql.name}.*))
                                FROM {table_sql.schema}.{table_sql.name}
                        '''
                        # much cleaner way to do this with SQLAlchemy 1.4.0b2+:
                        # stmt = select([
                        #     func.json_agg(func.to_json(table_sql.table_valued()))
                        # ])
                    res = s.execute(stmt)
                    return res.scalar() or []
                except Exception as e:
                    logger.error(
                        "Couldn't fetch data from the {0} table "
                        'of vocabulary "{1}". {2}'.format(
                            modelclass, vocabulary, str(e)
                        )
                    )
        except Exception as e:
            logger.error('Database session error. {0}'.format(str(e)))
        return []

    @classmethod
    def fetch_labels(cls, vocabulary, add_count=False, database=None):
        """Fetch all data from the label table of the given vocabulary.

        Parameters
        ----------
        vocabulary : str
            Name of the vocabulary, ie its ``name``
            property in ``vocabularies.yaml``.
        add_count : bool, default False
            If this is ``True``, the method will add a 
            ``count`` attribute with value ``-1`` to all records.
        database : str, optional
            URL of the database where the vocabulary is stored,
            ie ``dialect+driver://username:password@host:port/database``.
            If not provided, the main CKAN PostgreSQL database will be used.
        
        Returns
        -------
        list(dict)
            A list of dictionnaries. Each dictionnary represents one
            label through 4 keys:

            * ``id`` - integer, primary key of the label table.
            * ``uri`` - URI of the vocabulary item.
            * ``language`` - language of the label.
            * ``label`` - label of the vocabulary item.

            If `add_count` is set to ``True``, the dictionnary has
            an additional key ``count`` with value ``-1``.

        """
        return cls.fetch_data(
            vocabulary=vocabulary,
            modelclass=VocabularyLabelTable,
            add_count=add_count,
            database=database
        )

    @classmethod
    def fetch_hierarchized_data(cls, vocabulary, children_alias=None, database=None):
        """Fetch all data from the label and hierachy tables of the given vocabulary.

        Returns an empty list if the vocabulary
        doesn't have a hierarchy table in the database.

        Parameters
        ----------
        vocabulary : str
            Name of the vocabulary, ie its ``name``
            property in ``vocabularies.yaml``.
        children_alias : str, optional
            Alternative name for the key listing all
            children of the given vocabulary item. By default,
            the key is called ``'children'``.
        database : str, optional
            URL of the database where the vocabulary is stored,
            ie ``dialect+driver://username:password@host:port/database``.
            If not provided, the main CKAN PostgreSQL database will be used.

        Returns
        -------
        list(dict)
            A list of dictionnaries. Each dictionnary represents one
            label through 4 keys:

            * ``id`` - integer, primary key of the label table.
            * ``uri`` - URI of the vocabulary item.
            * ``language`` - language of the label.
            * ``label`` - label of the vocabulary item.
            * ``count`` - vaut toujours -1
            * ``children`` (name of the key may be changed through the
              `children_alias` parameter) - list of children labels,
              which are similar dictionnaries without the ``children``
              key.
        
        """
        #TODO: [LL-2023.01.23]
        # - This won't work properly if the vocabulary items have labels
        # in multiple languages. The method should either have a language
        # argument to specify one preferred language and return only one
        # label for each vocabulary item, or it should have a 'labels' key
        # listing dictionnaries with 'language' and 'label' keys...
        # - Not sure how this should work if there's more than two levels in
        # the hierarchy, but that's most likely not it either.
        # - If the 'count' key has no use, it shouldn't exist.

        if not vocabulary:
            return []

        label_sql = get_table_sql(vocabulary, VocabularyLabelTable)
        hierarchy_sql = get_table_sql(vocabulary, VocabularyHierarchyTable)
        if not cls.table_exists(hierarchy_sql, database=database):
            return []

        children_alias = children_alias or 'children'

        try:
            with Session(database=database) as s:
                try:
                    stmt = f'''
                        WITH label_data AS (
                        SELECT
                            *, -1 AS "count"
                            FROM {label_sql.schema}.{label_sql.name}
                        ),
                        by_parent AS (
                        SELECT
                            hierarchy.parent,
                            json_agg(
                                to_json(child_data.*) ORDER BY child_data.label
                            ) AS {children_alias}
                            FROM {hierarchy_sql.schema}.{hierarchy_sql.name} AS hierarchy
                                LEFT JOIN label_data AS child_data
                                    ON child_data.uri = hierarchy.child
                            GROUP BY hierarchy.parent
                        ),
                        by_parent_with_labels AS (
                        SELECT
                            parent_data.*,
                            by_parent.{children_alias}
                            FROM by_parent
                                LEFT JOIN label_data AS parent_data
                                    ON parent_data.uri = by_parent.parent
                        )
                        SELECT
                            json_object_agg(
                                by_parent_with_labels.uri,
                                to_json(by_parent_with_labels.*)
                                ORDER BY by_parent_with_labels.label
                            )
                            FROM by_parent_with_labels
                    '''
                    res = s.execute(stmt)
                    return res.scalar() or []
                except Exception as e:
                    logger.error(
                        "Couldn't fetch hierarchized data "
                        'of vocabulary "{1}". {2}'.format(
                            vocabulary, str(e)
                        )
                    )
        except Exception as e:
            logger.error('Database session error. {0}'.format(str(e)))
        return []

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
        
        table_sql = get_table_sql(vocabulary, VocabularyLabelTable)

        try:
            with Session(database=database) as s:
                try:
                    stmt = exists([table_sql.c.uri]).where(table_sql.c.uri == uri).select()
                    res = s.execute(stmt)
                    return res.scalar()
                except Exception as e:
                    logger.error(
                        'Failed to look up URI "{0}" in vocabulary "{1}". {2}'.format(
                            uri, vocabulary, str(e)
                        )
                    )
        except Exception as e:
            logger.error('Database session error. {0}'.format(str(e)))
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
        database : str, optional
            URL of the database where the vocabulary is stored,
            ie ``dialect+driver://username:password@host:port/database``.
            If not provided, the main CKAN PostgreSQL database will be used.
        
        Returns
        -------
        str or None
            A label for the URI. ``None`` if the vocabulary
            doesn't exist, is not available or there was
            no match for the URI.

        """
        if not vocabulary or not uri:
            return
        
        table_sql = get_table_sql(vocabulary, VocabularyLabelTable)

        try:
            with Session(database=database) as s:
                try:
                    # with the provided language
                    if language:
                        stmt = select([table_sql.c.label]).where(
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
                    stmt = select([table_sql.c.label]).where(
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
                    stmt = select([table_sql.c.label]).where(
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
        except Exception as e:
            logger.error('Database session error. {0}'.format(str(e)))

    @classmethod
    def get_uri_from_label(
        cls, vocabulary, label, language=None, case_sensitive=False,
        use_altlabel=True, database=None
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
        use_altlabel : bool, default True
            Should the method search for a matching alternative
            label if there's no match with the preferred labels?
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
        
        if use_altlabel:
            tables = (VocabularyLabelTable, VocabularyAltLabelTable)
        else:
            tables = (VocabularyLabelTable,)

        try:
            with Session(database=database) as s:
                try:
                    for table in tables:
                        table_sql = get_table_sql(vocabulary, table)
                        if case_sensitive:
                            where_stmt = (table_sql.c.label == label)
                        else:
                            where_stmt = (func.lower(table_sql.c.label) == label.lower())
                        if language:
                            where_stmt = and_(where_stmt, (table_sql.c.language == language))
                        stmt = select([table_sql.c.uri]).where(where_stmt)
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
        except Exception as e:
            logger.error('Database session error. {0}'.format(str(e)))

    @classmethod
    def get_uris_from_regexp(cls, vocabulary, terms, database=None):
        """Get all URIs whose regular expression matches any of the given terms.

        Parameters
        ----------
        vocabulary : str
            Name of the vocabulary, ie its ``name``
            property in ``vocabularies.yaml``.
        terms : str or list(str) or tuple(str)
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

        table_sql = get_table_sql(vocabulary, VocabularyRegexpTable)
        if not cls.table_exists(table_sql, database=database):
            return reslist

        if isinstance(terms, str):
            terms = [terms]

        try:
            with Session(database=database) as s:
                for term in terms:
                    try:
                        stmt = select([func.array_agg(table_sql.c.uri.distinct())]).where(
                            literal(term).op('~')(table_sql.c.regexp)
                        )
                        res = s.execute(stmt)
                        uris = res.scalar()
                        if uris:
                            reslist += uris
                    except Exception as e:
                        logger.error(
                            'Failed to look up regular expression matches of '
                            'term "{0}" in vocabulary "{1}". {2}'.format(
                                term, vocabulary, str(e)
                            )
                        )
        except Exception as e:
            logger.error('Database session error. {0}'.format(str(e)))
        
        return reslist
    
    @classmethod
    def get_parents(cls, vocabulary, uri, database=None):
        """Get the URIs of the parent items.

        Parameters
        ----------
        vocabulary : str
            Name of the vocabulary, ie its ``name``
            property in ``vocabularies.yaml``.
        uri : str or list(str)
            URI of a vocabulary item or a list of such URIs.
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
        
        table_sql = get_table_sql(vocabulary, VocabularyHierarchyTable)
        if not cls.table_exists(table_sql, database=database):
            return []

        try:
            with Session(database=database) as s:
                try:
                    if isinstance(uri, list):
                        cdt = (table_sql.c.child._in(uri))
                    else:
                        cdt = (table_sql.c.child == uri)
                    stmt = select([func.array_agg(table_sql.c.parent.distinct())]).where(cdt)
                    res = s.execute(stmt)
                    return res.scalar() or []
                except Exception as e:
                    logger.error(
                        'Failed to look up parent items of the URI'
                        ' "{0}" in vocabulary "{1}". {2}'.format(
                            uri, vocabulary, str(e)
                        )
                    )
        except Exception as e:
            logger.error('Database session error. {0}'.format(str(e)))
        
        return []
    
    @classmethod
    def get_children(cls, vocabulary, uri, database=None):
        """Get the URIs of the children items.

        Parameters
        ----------
        vocabulary : str
            Name of the vocabulary, ie its ``name``
            property in ``vocabularies.yaml``.
        uri : str or list(str)
            URI of a vocabulary item or a list of such URIs.
        database : str, optional
            URL of the database where the vocabulary is stored,
            ie ``dialect+driver://username:password@host:port/database``.
            If not provided, the main CKAN PostgreSQL database will be used.
        
        Returns
        -------
        list(str)
            List of the URIs of the children items. Result will be an
            empty list if the vocabulary doesn't exist, is not available,
            doesn't have a ``hierarchy`` table, if the URI didn't exist
            in the vocabulary or if the item didn't have any children.
        
        """
        if not vocabulary or not uri:
            return []
        
        table_sql = get_table_sql(vocabulary, VocabularyHierarchyTable)
        if not cls.table_exists(table_sql, database=database):
            return []
        
        try:
            with Session(database=database) as s:
                try:
                    if isinstance(uri, list):
                        cdt = (table_sql.c.parent._in(uri))
                    else:
                        cdt = (table_sql.c.parent == uri)
                    stmt = select([func.array_agg(table_sql.c.child.distinct())]).where(cdt)
                    res = s.execute(stmt)
                    return res.scalar() or []
                except Exception as e:
                    logger.error(
                        'Failed to look up children items of the URI'
                        ' "{0}" in vocabulary "{1}". {2}'.format(
                            uri, vocabulary, str(e)
                        )
                    )
        except Exception as e:
            logger.error('Database session error. {0}'.format(str(e)))
        
        return []

    @classmethod
    def get_children_labels_from_label(
        cls, vocabulary, label, language=None, database=None
    ):
        """Get the labels of the children items.

        Labels may not be unique in some vocabularies. In that case, the
        method will return all the children from the multiple vocabulary
        items sharing the same label.

        Alternative labels are not considered.

        Parameters
        ----------
        vocabulary : str
            Name of the vocabulary, ie its ``name``
            property in ``vocabularies.yaml``.
        label : str
            Label of a vocabulary item.
        language : str, optional
            If provided, a label will only be seen as
            matching if its language is `language`.
        database : str, optional
            URL of the database where the vocabulary is stored,
            ie ``dialect+driver://username:password@host:port/database``.
            If not provided, the main CKAN PostgreSQL database will be used.
        
        Returns
        -------
        list(str)
            List of the labels of the children items. Result will be an
            empty list if the vocabulary doesn't exist, is not available,
            doesn't have a ``hierarchy`` table, if the label didn't exist
            in the vocabulary or if the item didn't have any children.
        
        """
        if not vocabulary or not label:
            return []
        
        uri = cls.get_uri_from_label(
            vocabulary=vocabulary, label=label, language=language,
            use_altlabel=False, database=database
        )

        label_table_sql = get_table_sql(vocabulary, VocabularyLabelTable)
        hierarchy_table_sql = get_table_sql(vocabulary, VocabularyHierarchyTable)
        if not cls.table_exists(hierarchy_table_sql, database=database):
            return []
        
        try:
            with Session(database=database) as s:
                try:
                    stmt = select([func.array_agg(label_table_sql.c.label.distinct())]).select_from(
                        hierarchy_table_sql
                    ).join(label_table_sql, hierarchy_table_sql.c.child == label_table_sql.c.uri).where(
                        hierarchy_table_sql.c.parent == uri
                    )
                    res = s.execute(stmt)
                    return res.scalar() or []
                except Exception as e:
                    logger.error(
                        'Failed to look up children items of the URI'
                        ' "{0}" in vocabulary "{1}". {2}'.format(
                            uri, vocabulary, str(e)
                        )
                    )
        except Exception as e:
            logger.error('Database session error. {0}'.format(str(e)))
        
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
        
        table_sql = get_table_sql(vocabulary, VocabularySynonymTable)
        if not cls.table_exists(table_sql, database=database):
            return []
        
        try:
            with Session(database=database) as s:
                try:
                    stmt = select([func.array_agg(table_sql.c.synonym.distinct())]).where(
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
        except Exception as e:
            logger.error('Database session error. {0}'.format(str(e)))
        
        return []
    
    @classmethod
    def get_uri_from_id_fragment(cls, vocabulary, fragment, database=None):
        """Get one URI with the given identifying part.

        Parameters
        ----------
        vocabulary : str
            Name of the vocabulary, ie its ``name``
            property in ``vocabularies.yaml``.
        fragment : str
            A string that might be the identifying fragment of
            an URI. For now, only basic alpha-numeric characters,
            ``'-'`` and ``'_'`` are allowed.
        database : str, optional
            URL of the database where the vocabulary is stored,
            ie ``dialect+driver://username:password@host:port/database``.
            If not provided, the main CKAN PostgreSQL database will be used.
        
        Returns
        -------
        str or None
            The first matching URI. ``None`` if the vocabulary
            doesn't exist, is not available, the identifier had no
            match or contained forbidden characters.
        
        """
        if (
            not vocabulary or not fragment or
            not re.match('^[a-zA-Z0-9_-]+$', fragment)
        ):
            return
        fragment = fragment.lower().replace('-', '[-]')
        
        table_sql = get_table_sql(vocabulary, VocabularyLabelTable)

        try:
            with Session(database=database) as s:
                try:
                    stmt = select([table_sql.c.uri]).where(
                        func.lower(table_sql.c.uri).op('~')(f'[/#]{fragment}$')
                    )
                    res = s.execute(stmt)
                    return res.scalar()
                except Exception as e:
                    logger.error(
                        'Failed to look up an URI whose identifying part is'
                        ' "{0}" in vocabulary "{1}". {2}'.format(
                            fragment, vocabulary, str(e)
                        )
                    )
        except Exception as e:
            logger.error('Database session error. {0}'.format(str(e)))

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
        
        table_sql = get_table_sql(vocabulary, VocabularySynonymTable)
        if not cls.table_exists(table_sql, database=database):
            return

        try:
            with Session(database=database) as s:
                try:
                    stmt = select([table_sql.c.uri]).where(
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
        except Exception as e:
            logger.error('Database session error. {0}'.format(str(e)))

    @classmethod
    def get_bbox(cls, vocabulary, uri, database=None):
        """Get the coordinates of the boundary box for the given URI, if any.

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
        dict or None
            A dictionnary with five keys: ``uri`` is the given URI, 
            ``westlimit``, ``southlimit``, ``eastlimit``, and ``northlimit``
            are the coordinates of the bounding box.
            Result will be ``None`` if the vocabulary doesn't exist, is not
            available, doesn't have a ``spatial`` table, if the URI didn't
            exist in the vocabulary or if the item didn't have a bbox.
        
        """
        if not vocabulary or not uri:
            return
        
        table_sql = get_table_sql(vocabulary, VocabularySpatialTable)
        if not cls.table_exists(table_sql, database=database):
            return
        
        try:
            with Session(database=database) as s:
                try:
                    stmt = f'''
                        SELECT to_json(spatial_table.*)
                            FROM {table_sql.schema}.{table_sql.name} AS spatial_table
                            WHERE spatial_table.uri = :uri
                    '''
                    res = s.execute(stmt, params={'uri': uri})
                    bbox = res.scalar()
                    if bbox and 'id' in bbox:
                        del bbox['id']
                    return bbox or None
                except Exception as e:
                    logger.error(
                        'Failed to get the bbox of the URI'
                        ' "{0}" in vocabulary "{1}". {2}'.format(
                            uri, vocabulary, str(e)
                        )
                    )
        except Exception as e:
            logger.error('Database session error. {0}'.format(str(e)))

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

    @classmethod
    def list_vocabularies(cls, database=None):
        """List all vocabularies in the database.

        A vocabulary ``voc`` is assumed to exist as long as the 
        database contains a table named ``voc_label``.

        Parameters
        ----------
        database : str, optional
            URL of the database where the vocabulary is stored,
            ie ``dialect+driver://username:password@host:port/database``.
            If not provided, the main CKAN PostgreSQL database will be used.
        
        Returns
        -------
        list
            A list of vocabulary names.
        
        """
        try:
            with Session(database=database) as s:
                try:
                    res = s.execute("""
                        SELECT array_agg(
                                DISTINCT substring(relname, '^(.*)_label$')
                                ORDER BY substring(relname, '^(.*)_label$')
                            )
                            FROM pg_catalog.pg_class
                            WHERE relname ~ '^(.*)_label$'
                        """)
                    return res.scalar()
                except Exception as e:
                    logger.error('Failed to list vocabularies. {0}'.format(str(e)))
        except Exception as e:
            logger.error('Database session error. {0}'.format(str(e)))

    @classmethod
    def table_exists(cls, table_sql, database=None):
        """Check if a table exists in the database.

        Parameters
        ----------
        table_sql : sqlalchemy.sql.schema.Table
            Definition of the table.
        database : str, optional
            URL of the database where the vocabulary is stored,
            ie ``dialect+driver://username:password@host:port/database``.
            If not provided, the main CKAN PostgreSQL database will be used.
        
        Returns
        -------
        bool or ``None``
            ``None`` if the test failed for some reason.
        
        """
        try:
            with Session(database=database) as s:
                try:
                    res = s.execute(
                        """
                        SELECT to_regclass(:relfullname) IS NOT NULL
                        """,
                        {
                            'relfullname': f'{table_sql.schema}.{table_sql.name}'
                        }
                    )
                    return res.scalar()
                except Exception as e:
                    logger.error(
                        'Failed to check if "{0}"."{1}" exists. {2}'.format(
                            table_sql.schema, table_sql.name, str(e)
                        )
                    )
        except Exception as e:
            logger.error('Database session error. {0}'.format(str(e)))
