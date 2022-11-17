"""

This module should be entirely rewritten to fetch vocabulary
data from the database rather than from JSON files.

"""
from ckan.model import GroupExtra, Group,Session as Session_CKAN

from ckan.logic.action.get import organization_list

from sqlalchemy import Table, Column, Integer, String, MetaData,select,and_,func,join
import ckan.plugins as p

import json
from pathlib import Path
from ckanext import __path__ as ckanext_path
import logging
from ckanext.ecospheres.vocabulary.loader import (
                                            _get_generic_schema
                                            ,_get_hierarchy_schema_table
                                            ,_get_spatial_schema_table
                                            ,Session,DB,_get_regex_schema_table
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



    @classmethod
    def _resultset_to_dict(cls, resultset):
        return {
            "uri": resultset[0], 
            "label": resultset[1],
            "language": resultset[2]
        }
    


    @classmethod 
    def _select_labels_from_database(cls,_table):
        """Return labels' table for the given table
        
        Parameters
        ----------
        _table : Table
            sqlalchemy.Table object
        
        Returns
        -------
        list
                    [
                        {
                        "uri": "uri_", 
                        "label":"label_",
                        "language": "language_"
                         },
                    ...
                    ...
                    ]

        """


        with Session(database=DB) as s:
            try:    
                
                statement=select([_table.c.uri, _table.c.label,_table.c.language])
                return [cls._resultset_to_dict(resultset) for resultset in s.execute(statement).fetchall()]
            except Exception as e:
                logging.error("Erreur lors de la création du table")
                return {}



    @classmethod 
    def _select_labels_from_database_theme_regex(cls,_table):

        """Return regex' table for the given table
        
        Parameters
        ----------
        _table : Table
            sqlalchemy.Table object
        
        Returns
        -------
        list
            [
                {
                    "uri":"uri_",
                    "regex":"regex_"
                },
                ...
                ...
            ]

        """

        with Session(database=DB) as s:
            try:    
                statement=select([_table.c.uri, _table.c.regexp])
                return  s.execute(statement).fetchall()
            except Exception as e:
                logging.error(f"Erreur lors de la récuperation des regex thèmes de la table {_table}")
                return {}

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
                    [
                        {
                        "uri": "uri_", 
                        "label":"label_",
                        "language": "language_"
                         },
                    ...
                    ...
                    ]

        """
        if vocabulary == "ecospheres_theme": 
            return cls.themes()
        _table=_get_generic_schema(f"{vocabulary}_label")
        return cls._select_labels_from_database(_table)

    @classmethod
    def __get_themes_hierarchy_as_dict(cls):
        """Return themes hierarchy
        
        
        Returns
        -------
        dict
            {
            "uri_parent" : [
                            "uri_child_1",
                            "uri_child_2",
                            ],
            ...
            ...

            },

        """
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
                logging.error(f"Erreur lors de la création du table {_table}")
                return {}
        
    @classmethod
    def __get_themes_from_db(cls,_table,uri:str):
        """Return label from theme table for the given uri
        
            Parameters
            ----------
            _table : str
            uri: str
            
            Returns
            -------
            dict
                {
                    "uri":"uri",
                    "label":"label",
                    "language":"language"
                }

        """
        with Session(database=DB) as s:
            try:
                statement=select([_table.c.uri, _table.c.label,_table.c.language]).\
                                    where(_table.c.uri==uri)
                res=s.execute(statement).fetchone()
                if res:
                    return cls._resultset_to_dict(res)
                return None
            except Exception as e:
                logging.error(f"Erreur lors de la création du table {_table}")
                return {}


    @classmethod
    def __get_theme_labels_by_uri(cls,uri:str):
        """Return label theme  for the given uri
        
        Parameters
        ----------
        uri: str

        Returns
        -------
        dict
                {
                    "uri":"uri",
                    "label":"label",
                    "language":"language"
                }

        """

        return cls.__get_themes_from_db(
                                    _get_generic_schema("ecospheres_theme_label"),
                                        uri)


    @classmethod
    def __get_theme_altlabels_by_uri(cls,uri:str):
        """Return altlabel theme  for the given uri
        
        Parameters
        ----------
        uri: str

        Returns
        -------
        dict
                {
                    "uri":"uri",
                    "label":"label",
                    "language":"language"
                }

        """
        return cls.__get_themes_from_db(
                                        _get_generic_schema("ecospheres_theme_altlabel"),
                                        uri)



    @classmethod
    def themes(cls):
        """Return theme labels with hierarchy
        

        Returns
        -------
        dict
                { 

                "theme_uri": {

                            "altlabel": [
                                            "alt_label_1", 
                                            "alt_label_2", 
                                        ], 

                            "child": [
                                        "altlabel": [
                                                    "alt_label_1", 
                                                    "alt_label_2",
                                                ], 
                                        "count": -1, 
                                        "label": "label", 
                                        "language": "fr", 
                                        "regexp": [
                                                    "regex_1", 
                                                    "regex_2", 
                                                    ], 
                                        "uri": "uri_subtheme"
                                    ],

                            "count": -1, 
                            "label": "label", 
                            "language": "fr", 
                        }

        """
        try:
            all_themes={}   
            #Récuperation des labels
            labels=cls._select_labels_from_database(_get_generic_schema("ecospheres_theme_label"))
            #Récuperation des altlabels
            labels_dict=dict()
            for label in labels:
                labels_dict[label["uri"]] =label

            alt_label_map={}
            altlabels=cls._select_labels_from_database(_get_generic_schema("ecospheres_theme_altlabel"))
            for alt_label in altlabels:
                alt_label_map.setdefault(alt_label["uri"], [])
                alt_label_map[alt_label['uri']].append(alt_label["label"])

            _table_regex=cls._select_labels_from_database_theme_regex(_get_regex_schema_table("ecospheres_theme_regexp"))
            regexp_map={}
            for regexp in _table_regex:
                regexp_map.setdefault(regexp[0],[])
                regexp_map[regexp[0]].append(regexp[1])
                
            #Récuperation des infos sur la hierarchie des themes
            hierarchy_table=cls.__get_themes_hierarchy_as_dict()
            for parent_theme in hierarchy_table:
                
                #themes parents
                temp_theme=labels_dict[parent_theme].copy()
                temp_theme["child"]=list()
                temp_theme["count"]=-1
                temp_theme["altlabel"]=alt_label_map.get(parent_theme,[])
                all_themes[parent_theme]=temp_theme

                #sous-themes
                for sous_theme in hierarchy_table[parent_theme]:
                    temp_sous_theme=labels_dict[sous_theme].copy()
                    temp_sous_theme["count"]=-1
                    temp_sous_theme["regexp"]=regexp_map.get(sous_theme,None)
                    temp_sous_theme["altlabel"]=alt_label_map.get(sous_theme,[])
                    all_themes[parent_theme]["child"].append(temp_sous_theme)

            return all_themes
        except Exception as e:
            logging.error(f"Erreur lors du chargement des données {_table}")
            return {}

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
                    [
                        {
                        "uri": "uri_", 
                        "label":"label_",
                        "language": "language_"
                         },
                    ...
                    ...
                    ]
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
        uri : rdflib.term.URIRef or stris_known_uri
            Some URI to test.
        
        Returns
        -------
        dict : if the vocabulary exists
                    {
                        "uri": "uri_", 
                        "label":"label_",
                        "language": "language_"
                    }
            
        None:  if the vocabulary do not exists  
        
        """
        _table=_get_generic_schema(f"{vocabulary}_label")
    
        clause=( _table.c.uri==uri)

        if language:
            clause=and_(clause,_table.c.language == language)

        with Session(database=DB) as s:
            try:
                statement=select([_table.c.uri, _table.c.label,_table.c.language]).\
                                    where(clause)
                res=  s.execute(statement).fetchone()
                if res:
                    return cls._resultset_to_dict(res)
                return None
            except Exception as e:
                logging.error(f"Erreur lors du chargement de la table {_table}")
                return list()


    @classmethod
    def get_uri_from_label(cls, vocabulary, label, language=None,case_sensitive=False):
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
                logging.error(f"Erreur lors de la création du table {_table}")
                return list()





    @classmethod
    def get_organization_by_admin(cls):
        """Return organization by administration type

        Returns
        -------
        dict :
        {
            "administration_type_label":{
                                        "count": -1, 
                                        "orgs":[
                                                {
                                                    "Courriel": "ddtm@gard.gouv.fr", 
                                                    "Site internet": "homepage"
                                                    "Territoire": "Territory", 
                                                    "Type": "admin_type", 
                                                    "Téléphone": "04 66 62 62 00", 
                                                    "count": -1, 
                                                    "created": "Thu, 22 Sep 2022 13:34:17 GMT", 
                                                    "description": "description",
                                                    "image_url": "image_url", 
                                                    "name": "organisation_name", 
                                                    "title": "organisation_title"
                                                },
                                                ...
                                                ...                                           
                                               ]
                                        },
                                        ......
                                        ......
        }
        """

        try:
            list_of_organizations_as_dict=dict()
            organizations_as_dict=dict()
        

            groups=Session_CKAN.query(Group).filter_by(state='active').all()
            if not groups:
                return {"message":"Liste des organisations vide"} 
            for group in groups:
                organizations_as_dict.setdefault(group.id,{})
                organizations_as_dict[group.id]["name"] = group.name
                organizations_as_dict[group.id]["title"]=group.title
                organizations_as_dict[group.id]["description"]=group.description
                organizations_as_dict[group.id]["created"]=group.created
                organizations_as_dict[group.id]["image_url"]=group.image_url
                organizations_as_dict[group.id]["count"]=-1

            groups_details=Session_CKAN.query(GroupExtra).all()
            for group_details in groups_details:
                #verfier si l'organisation est bien présente dans les organisations actives
                # Quand on supprime une orgonisation, elle sera juste marquée comme inactive, elle reste toujours en base de données
                if group_details.group_id not in organizations_as_dict:
                    continue
                organizations_as_dict[group_details.group_id][group_details.key] = group_details.value


            for org in organizations_as_dict:
                list_of_organizations_as_dict.setdefault(cls.TYPE_ADMINISTRATION[organizations_as_dict[org]['Type']],{})
                list_of_organizations_as_dict[cls.TYPE_ADMINISTRATION[organizations_as_dict[org]['Type']]].setdefault("orgs",[])
                list_of_organizations_as_dict[cls.TYPE_ADMINISTRATION[organizations_as_dict[org]['Type']]]["orgs"].append(organizations_as_dict[org])
                list_of_organizations_as_dict[cls.TYPE_ADMINISTRATION[organizations_as_dict[org]['Type']]]["count"]=-1


            return list_of_organizations_as_dict
        except Exception as e:
            logging.error(f"Erreur lors du chargement de la liste des territoires")
            return {}





    @classmethod
    def get_territory_by_code_region(cls,code_region):
        """Return territory label for given code_region.
        
        Parameters
        ----------
        code_region : str
        
        Returns
        -------
        tuple : (uri,label,language)
                
        """
        _table=_get_generic_schema("ecospheres_territory_label")
        with Session(database=DB) as s:
            try:
                statement=select([_table.c.uri, _table.c.label,_table.c.language]).\
                                    where(_table.c.uri==code_region)
                res=  s.execute(statement).fetchone()
                if res:
                    return res
                return None
            except Exception as e:
                logging.error(f"Erreur lors du chargement de la table: {_table}")
                return {}


    @classmethod
    def get_territory_spatial_by_code_region(cls,code_region):
        """Return territory spatial data for  given code_region.
        
        Parameters
        ----------
        code_region : str
        
        Returns
        -------
        dict :  {
                    "uri": "_uri_",
                    "westlimit": "_westlimit_",
                    "southlimit": "_southlimit_",
                    "eastlimit": "_eastlimit_",
                    "northlimit": "_northlimit_"
                }
                
        """

        _table=_get_spatial_schema_table("ecospheres_territory_spatial")
        with Session(database=DB) as s:
            try:
                statement=select([_table.c.uri, _table.c.westlimit,_table.c.southlimit,_table.c.eastlimit,_table.c.northlimit]).\
                                    where(_table.c.uri==code_region)
                res=  s.execute(statement).fetchone()
                if res:
                    return {
                        "uri": res[0],
                        "westlimit": res[1],
                        "southlimit": res[2],
                        "eastlimit": res[3],
                        "northlimit": res[4]
                    }
                return None
            except Exception as e:
                logging.error(f"Erreur lors du chargement de la table: {_table}")
                return {}

    @classmethod
    def _get_territories_by_hierarchy(cls):
        
        """Return theme labels with hierarchy
        

        Returns
        -------
        dict
            {
                "départements-métropole":[
                    {
                        ......
                    },
                    ...
                ],
                "depts_by_region":[
                     {
                        ......
                    },
                    ...
                ],
                "outre-mer":[
                     {
                        ......
                    },
                    ...
                ],
                "régions-métrople":[],
                "zones-maritimes":[],
            }
        """
        
        try:
            vocabulary="territoires"
            import re
            for ckanext in ckanext_path:
                if re.match(r'.*ckanext-ecospheres.*', ckanext):
                    ckan_ecosphere_index=ckanext_path.index(ckanext)

            path = Path(ckanext_path[ckan_ecosphere_index]).parent / f'vocabularies/{vocabulary}.json'
            
            if not path.exists() or not path.is_file():
                raise FileNotFoundError(f"could not find vocabulary data for '{vocabulary}'")
            with open(path, 'r', encoding='utf-8') as src:
                data = json.load(src)

            res_territoires_dict=dict()
        
            type_region_keys=['régions-métrople', 'départements-métropole', 'outre-mer', 'zones-maritimes']
            depts_by_region=dict()
            for type_region_key in type_region_keys:
                res_territoires_dict.setdefault(type_region_key,{})
                if region_data:=data.get(type_region_key,None):
                    for key in region_data:
                        res_territoires_dict[type_region_key].setdefault(key,{})
                        if name:=region_data[key].get('name',None):
                            res_territoires_dict[type_region_key][key]['name']=name
                        if code_region:=region_data[key].get('codeRégion',None):
                            res_territoires_dict[type_region_key][key]['code_region']=code_region
            for dep in res_territoires_dict['départements-métropole']:
                depts_by_region.setdefault(res_territoires_dict['départements-métropole'][dep].get('code_region'),[])
                dept_info_as_dict=res_territoires_dict['départements-métropole'][dep].copy()
                dept_info_as_dict["code_dept"]=dep
                depts_by_region[res_territoires_dict['départements-métropole'][dep].get('code_region')].append(dept_info_as_dict)

            res_territoires_dict["depts_by_region"]=depts_by_region
            return res_territoires_dict
        except Exception as e:
            logger.error(f"erreur lors de la récuperation des territoires par hierarchy: {_table}")
            
            return {}