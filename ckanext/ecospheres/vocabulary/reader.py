"""

This module should be entirely rewritten to fetch vocabulary
data from the database rather than from JSON files.

"""
from sqlalchemy import Table, Column, Integer, String, MetaData,select,and_,func

import json
from pathlib import Path
from ckanext import __path__ as ckanext_path
import logging
from ckanext.ecospheres.vocabulary.loader import (
                                            _get_generic_schema
                                            ,_get_hierarchy_schema_table
                                            ,_get_spatial_schema_table
                                            ,Session,DB
                                    )


logger = logging.getLogger(__name__)



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
    def _resultset_to_dict(cls, resultset):
        return {
            "uri": resultset[0], 
            "label": resultset[1],
            "language": resultset[2]
        }
    
    @classmethod 
    def _select_labels_from_database(cls,_table):
        with Session(database=DB) as s:
            try:
                statement=select([_table.c.uri, _table.c.label,_table.c.language])
                return [cls._resultset_to_dict(resultset) for resultset in s.execute(statement).fetchall()]
            except Exception as e:
                logging.error(f"Erreur lors de la création du table {_table}\t {str(e)}")
                return list()

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
    
        _table=_get_generic_schema(f"{vocabulary}_label")
        return cls._select_labels_from_database(_table)


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
        
        _table=_get_generic_schema(f"{vocabulary}_altlabel")
        return cls._select_labels_from_database(_table)


    @classmethod
    def is_known_uri(cls, vocabulary, uri,language=None):
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
    
        _table=_get_generic_schema(f"{vocabulary}_label")


        if not language:
            language="fr"

        with Session(database=DB) as s:
            try:
                statement=select([_table.c.uri, _table.c.label,_table.c.language]).\
                                    where(and_(_table.c.uri==uri,_table.c.language==language))
                res=  s.execute(statement).fetchone()
                print(res)
                if res:
                    return cls._resultset_to_dict(res)
                return None
            except Exception as e:
                logging.error(f"Erreur lors de la création du table {_table}\t {str(e)}")
                return list()

        # if not vocabulary or not uri:
        #     return False
        # return any(row['uri'] == uri for row in cls.labels(vocabulary))


        print("test vocabulary")
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
        _table=_get_generic_schema(f"{vocabulary}_label")
        logger.info(f"fetching results from {_table} table")
        if res:=  cls._get_result_from_db(label, language,
                                         case_sensitive,_table):
            logger.info(f"Result found in {_table} table")
            return res
        logger.info(f"Not Result found in {_table} table")


        _table=_get_generic_schema(f"{vocabulary}_altlabel")
        logger.info(f"fetching results from {_table} table")
        return cls._get_result_from_db(label, language,
                                         case_sensitive,_table)

    @classmethod
    def _get_result_from_db(cls,label, language,case_sensitive,_table):
        if case_sensitive:
            clause=( func.lower(_table.c.label) ==  func.lower(label))
        else:
            clause=(_table.c.label == label)


        if language:
            clause=and_(clause,_table.c.language == language)
        with Session(database=DB) as s:
            try:
                statement=select([_table.c.uri, _table.c.label,_table.c.language]).\
                                    where(clause)
                res=  s.execute(statement).fetchone()
                if res:
                    return res[0]
                return None
            except Exception as e:
                logging.error(f"Erreur lors de la création du table {_table}\t {str(e)}")
                return list()
