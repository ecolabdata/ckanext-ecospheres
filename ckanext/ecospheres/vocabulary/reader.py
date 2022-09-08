"""

This module should be entirely rewritten to fetch vocabulary
data from the database rather than from JSON files.

"""
from ckan.model import GroupExtra, Group,Session as Session_CKAN

from ckan.logic.action.get import organization_list

from sqlalchemy import Table, Column, Integer, String, MetaData,select,and_,func
import ckan.plugins as p

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
    TYPE_ADMINISTRATION={
                            "AC" : "Administration centrale",
                            "DR" : "Directions régionales",
                            "DIRID" : "Directions interrégionales et interdépartementales",
                            "DD" : "Directions départementales",
                            "SOM" : "Services d'OutreMer",
                            "Op" : "Opérateurs"
                        }
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
        if vocabulary == "ecospheres_theme": 
            return cls.themes()
        _table=_get_generic_schema(f"{vocabulary}_label")
        return cls._select_labels_from_database(_table)

    @classmethod
    def __get_themes_hierarchy_as_dict(cls):
        _table=_get_hierarchy_schema_table("ecospheres_theme_hierarchy")
        uri_themes_with_hierarchy={}
        with Session(database=DB) as s:
            try:
                statement=select([_table.c.parent, _table.c.child])
                for uri_parent, uri_child in s.execute(statement).fetchall():
                    uri_themes_with_hierarchy.setdefault(uri_parent, [])
                    uri_themes_with_hierarchy[uri_parent].append(uri_child)
                return uri_themes_with_hierarchy
            except Exception as e:
                logging.error(f"Erreur lors de la création du table {_table}\t {str(e)}")
                return list()
        
    @classmethod
    def __get_themes_from_db(cls,_table,uri:str):
        with Session(database=DB) as s:
            try:
                statement=select([_table.c.uri, _table.c.label,_table.c.language]).\
                                    where(_table.c.uri==uri)
                res=s.execute(statement).fetchone()
                if res:
                    return cls._resultset_to_dict(res)
                return None
            except Exception as e:
                logging.error(f"Erreur lors de la création du table {_table}\t {str(e)}")
                return list()

    @classmethod
    def __get_theme_labels_by_uri(cls,uri:str):
        return cls.__get_themes_from_db(
                                    _get_generic_schema("ecospheres_theme_label"),
                                        uri)


    @classmethod
    def __get_theme_altlabels_by_uri(cls,uri:str):
        return cls.__get_themes_from_db(
                                        _get_generic_schema("ecospheres_theme_altlabel"),
                                        uri)

    @classmethod
    def themes(cls):
        themes_hierarchy_as_dict=cls.__get_themes_hierarchy_as_dict()
        all_themes_subtheme_hierarchy_as_dict=dict()
        for uri_parent in themes_hierarchy_as_dict:

            theme_parent_child=cls.__get_theme_labels_by_uri(uri_parent)
            theme_parent_child.setdefault("child", [])
            theme_parent_child.setdefault("altlabel", [])
            
            #Récuperation des altlabels pour le theme parent
            if label:=cls.__get_theme_altlabels_by_uri(uri_parent):
                theme_parent_child["altlabel"].append(label["label"])
            
            
            for uri_child in themes_hierarchy_as_dict[uri_parent]:
                if child_label:=cls.__get_theme_labels_by_uri(uri_child):
                    if label:=cls.__get_theme_altlabels_by_uri(uri_child):
                        child_label.setdefault("altlabel", [])
                        child_label["altlabel"].append(label["label"])
                        # print(theme_parent_child["label"]," : ",label["label"])

                    theme_parent_child["child"].append(child_label)
            all_themes_subtheme_hierarchy_as_dict[theme_parent_child["label"]]=theme_parent_child
        return all_themes_subtheme_hierarchy_as_dict

    @classmethod
    def altlabels(cls, vocabulary:str):
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
        if vocabulary == "ecospheres_theme": 
            return cls.themes()
        _table=_get_generic_schema(f"{vocabulary}_altlabel")
        return cls._select_labels_from_database(_table)


    @classmethod
    def is_known_uri(cls, vocabulary:str, uri:str,language:str=None):
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

    @classmethod            
    def _get_user_name(context):
        context['defer_commit'] = True  # See ckan/ckan#1714
        _site_user = p.toolkit.get_action('get_site_user')(context, {})
        return  _site_user['name']

    @classmethod
    def _get_user_name(self):
        user = p.toolkit.get_action('get_site_user')(
            {'ignore_auth': True, 'defer_commit': True},
            {})
        print("user: ",user["name"])
        return user['name']


    @classmethod
    def get_organization_by_admin(cls):
        list_of_organizations_as_dict=dict()
        organizations_as_dict=dict()
        ctx = {'ignore_auth': True,
                'user': cls._get_user_name()}

        groups=Session_CKAN.query(Group).filter_by(state='active').all()
        for group in groups:
            organizations_as_dict.setdefault(group.id,{})
            organizations_as_dict[group.id]["name"] = group.name
            organizations_as_dict[group.id]["title"]=group.title
            organizations_as_dict[group.id]["description"]=group.description
            organizations_as_dict[group.id]["created"]=group.created
            organizations_as_dict[group.id]["image_url"]=group.image_url

        groups_details=Session_CKAN.query(GroupExtra).all()
        for group_details in groups_details:
            #verfier si l'organisation est bien présente dans les organisations actives
            # Quand on supprime une orgonisation, elle sera juste marquée comme inactive, elle reste toujours en base de données
            if group_details.group_id not in organizations_as_dict:
                continue
            organizations_as_dict[group_details.group_id][group_details.key] = group_details.value


        for org in organizations_as_dict:
            list_of_organizations_as_dict.setdefault(cls.TYPE_ADMINISTRATION[organizations_as_dict[org]['Type']],[])
            list_of_organizations_as_dict[cls.TYPE_ADMINISTRATION[organizations_as_dict[org]['Type']]].append(organizations_as_dict[org])

        return list_of_organizations_as_dict