import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.ecospheres.validators as v
import ckanext.ecospheres.helpers as helpers
import collections
import json
import logging
from flask import Blueprint
from ckan.model import Session, meta
from sqlalchemy import Column, Date, Integer, Text, create_engine, inspect
from ckanext.ecospheres.vocabulary.reader import VocabularyReader

import ast



class DcatFrenchPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IFacets)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IBlueprint)



    # ------------- IConfigurer ---------------#
    
    def get_helpers(self):
        '''Register the functions above as a template
        helper functions.
        '''
        return {
                'fr_dcat_json_string_to_object_aggregated_ressources':helpers.json_string_to_object_aggregated_ressources,
                'fr_dcat_aggregated_package_name_to_title':helpers.aggregated_package_name_to_title,
                'get_localized_value_for_display':helpers.get_localized_value_for_display,
                'get_localized_date':helpers.get_localized_date,
                'get_territories_label':helpers.get_territories_label,
                'get_type_adminstration_label_by_acronym':helpers.get_type_adminstration_label_by_acronym,
                'get_vocabulary_label_by_uri':helpers.get_vocabulary_label_by_uri,
                }

    

   
    # ------------- IValidators ---------------#
    def get_validators(self):
        return {
            'timestamp_to_datetime': v.timestamp_to_datetime,
            'multilingual_text_output': v.multilingual_text_output,
        }

    # ------------- IFacets ---------------#

    def dataset_facets(self, facets_dict, package_type):
        """_summary_
        Cette fonction permet de specifier les filtres à appliquer aux jeux de données.
        Example:  facets_dict['category'] = plugins.toolkit._('Thématiques') -> permet d'ajouter un filtre sur le champ
        indexé "category"
        NB: On ne peut ajouter que des champ indexé par solr. Pour ajouter un filtre 

        """
        facets_dict = collections.OrderedDict()
        facets_dict['organization'] = plugins.toolkit._('Organisations')
        facets_dict['category'] = plugins.toolkit._('Thématiques')
        facets_dict['subcategory'] = plugins.toolkit._('Sous-Thématiques')
        facets_dict['territory'] = plugins.toolkit._('Territoires')
        facets_dict['res_format'] = plugins.toolkit._('Formats')
        
        return facets_dict


    def group_facets(self, facets_dict, group_type, package_type):
        # clear the dict instead and change the passed in argument
        facets_dict['organization'] = plugins.toolkit._('Organizations')
        facets_dict['political_level'] = plugins.toolkit._('Political levels')
        facets_dict['res_rights'] = plugins.toolkit._('Terms of use')
        facets_dict['res_format'] = plugins.toolkit._('Formats')
        return facets_dict

    def organization_facets(self, facets_dict, organization_type,
                            package_type):
        facets_dict['groups'] = plugins.toolkit._('Categories')
        facets_dict['keywords_' + lang_code] = plugins.toolkit._('Keywords')
        facets_dict['res_rights'] = plugins.toolkit._('Terms of use')
        facets_dict['res_format'] = plugins.toolkit._('Formats')
        return facets_dict


    def before_index(self, search_data):
        """_summary_
        Cette fonction est appelé avant qu"un jeux de données ne soit indexé.
        On peut choisir quels champs indexer en les ajoutant à search_data
        """
        validated_dict = json.loads(search_data['validated_data_dict'])
        if categories:=validated_dict.get("category",None):
            search_data["category"]=[categorie["theme"] for categorie in categories]
        
        if subcategories:=validated_dict.get("subcategory",None):
            search_data["subcategory"]=[subcategorie["subtheme"] for subcategorie in subcategories]
       
        if territory:=validated_dict.get("territory",None):
            search_data["territory"]=[ter['label'] for ter in territory]

        if modified:=validated_dict.get("modified",None):
            search_data["modified"]=modified.replace("+00:00",'')

        if restricted_access:=validated_dict.get("restricted_access",None):
            search_data["restricted_access"]=restricted_access

        if created:=validated_dict.get("created",None):
            search_data["created"]=created.replace("+00:00",'')

        if issued:=validated_dict.get("issued",None):
            search_data["issued"]=issued.replace("+00:00",'')

        return search_data


    
    def before_search(self, search_params):
        """_summary_
        Cette fonction permet d'intercepter la requete avant de faire une recherche pour enrichir les paramtres de recherche,
        dans ce cas ci, on extrait les dates de début et de fin pour les ajouter au champ fq qui sera interpreté par le moteur de recherche
        solr
        A noter, pour ajouter des paramtres extra à une requetes dans CKAN et les recuperer avec la clé "extras", il faut préfixer le nom du paramtres par "ext_"

        
        """
        # /dataset/?q=&ext_startdate=2022-07-20T11:48:38.540Z&ext_enddate=2023-07-20T11:48:38.540Z
        # /dataset/?q=&ext_startdate=2022-07-20T11:48:38.540Z
        # /dataset/?q=&ext_enddate=2022-07-20T11:48:38.540Z
        # ?q=&ext_startdate=2022-06-21T00:00:00Z&ext_enddate=NOW
        #/?q=&ext_restricted_access=true
        #/?q=&ext_restricted_access=false
        #/dataset/?q=&ext_startdate=2022-07-20T11:48:38.540Z&ext_restricted_access=false
        extras=search_params.get("extras",None)
        if not extras:
            return search_params
        
        restricted_access=extras.get("ext_restricted_access",None)
        include_subdivision=extras.get("ext_include_subdivision",None)
        start_date=extras.get("ext_startdate",None)
        end_date=extras.get("ext_enddate",None)


        if not start_date and not end_date and not restricted_access  and not include_subdivision:
            return search_params

        if not start_date :
            start_date="*"
        
        if not end_date:
            end_date="NOW"

        fq = search_params['fq']
        fq = '{fq} +modified:[{start_date} TO {end_date}]'.format(
                                 fq=fq, start_date=start_date, end_date=end_date)
        if restricted_access is not None:
            fq = '{fq} +extras_restricted_access:{restricted_access}'.format(
                                    fq=fq, restricted_access=restricted_access)


        if include_subdivision == True:
            raise Exception(include_subdivision)


        search_params['fq'] = fq
        return search_params
    


    def after_search(self,search_results, search_params):
        search_dicts = search_results.get('results', [])
        for _dict in search_dicts:
            _dict_resources = _dict.get('resources', None)
            for resource in _dict_resources:
                if resoueces_type:=resource["format"]:
                    label=helpers.get_vocabulary_label_by_uri("iana_media_type",resoueces_type)
                    resource["format"]=label
        return search_results




    # ------------- IBlueprint ---------------#
    def _get_territoires(self):
        return {
                "territoires": VocabularyReader.labels(vocabulary="ecospheres_territory")
               }
    def _get_themes(self):
        return VocabularyReader.themes()
    
    def _get_organizations(self):
        return VocabularyReader.get_organization_by_admin()
    

    def _get_territoires_hierarchy(self):
        return VocabularyReader._get_territories_by_hierarchy()

        
    def get_blueprint(self):
        """
        Exposition des APIs 

        """
        blueprint = Blueprint('dcatapfrench_custom_api', self.__module__)
        rules = [ 
            ('/api/territoires', 'get_territoires', self._get_territoires),
            ('/api/territoires_hierarchy', 'get_territoires_hierarchy', self._get_territoires_hierarchy),
            ('/api/themes', 'get_themes', self._get_themes),
            ('/api/organizations', 'get_organizations', self._get_organizations),
            ]
        for rule in rules:
            blueprint.add_url_rule(*rule)
        return blueprint

