import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.ecospheres.validators as v
import ckanext.ecospheres.helpers as helpers
import collections

import logging

class DcatFrenchPlugin(plugins.SingletonPlugin):
    # Declare that this class implements IConfigurer.
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IFacets)
    plugins.implements(plugins.IPackageController, inherit=True)

    # IConfigurer

    
    def get_helpers(self):
        '''Register the functions above as a template
        helper functions.
        '''
        return {
                'fr_dcat_json_string_to_object_aggregated_ressources':helpers.json_string_to_object_aggregated_ressources,
                'fr_dcat_aggregated_package_name_to_title':helpers.aggregated_package_name_to_title,
                'get_localized_value_for_display':helpers.get_localized_value_for_display,
                'get_localized_date':helpers.get_localized_date,
                }

    
    # IValidators
    def get_validators(self):
        return {
            'timestamp_to_datetime': v.timestamp_to_datetime,
            'multilingual_text_output': v.multilingual_text_output,
        }

    def dataset_facets(self, facets_dict, package_type):
        facets_dict = collections.OrderedDict()
        facets_dict['organization'] = plugins.toolkit._('Organisations')
        facets_dict['category'] = plugins.toolkit._('Thématiques')
        facets_dict['subcategory'] = plugins.toolkit._('Sous-Thématiques')
        facets_dict['territory'] = plugins.toolkit._('Territoires')
        facets_dict['res_format'] = plugins.toolkit._('Formats')
        
        return facets_dict


    def before_index(self, search_data):

        import json

        validated_dict = json.loads(search_data['validated_data_dict'])

        if categories:=validated_dict.get("category",None):
            search_data["category"]=[categorie["theme"] for categorie in categories]
        
        if subcategories:=validated_dict.get("subcategory",None):
            search_data["subcategory"]=[subcategorie["subtheme"] for subcategorie in subcategories]
       
        if territory:=validated_dict.get("territory",None):
            search_data["territory"]=territory

        if modified:=validated_dict.get("modified",None):
            search_data["modified"]=modified.replace("+00:00",'')

        if created:=validated_dict.get("created",None):
            search_data["created"]=created.replace("+00:00",'')

        if issued:=validated_dict.get("issued",None):
            search_data["issued"]=issued.replace("+00:00",'')

        return search_data


    def before_search(self, search_params):
        #d'une dateA à une dateB
        # /dataset/?q=&ext_startdate=2022-07-20T11:48:38.540Z&ext_enddate=2022-07-20T11:48:38.540Z
        
        #dateA à aujourd'hui
        # ?q=&ext_startdate=2022-06-21T00:00:00Z&ext_enddate=NOW

        extras=search_params.get("extras",None)

        if not extras:
            return search_params
        
        start_date=extras.get("ext_startdate",None)
        end_date=extras.get("ext_enddate",None)


        if not start_date and not end_date:
            return search_params


        fq = search_params['fq']
        fq = '{fq} +modified:[{start_date} TO {end_date}]'.format(
        fq=fq, start_date=start_date, end_date=end_date)
        search_params['fq'] = fq
        return search_params
    


    def after_search(self,search_results, search_params):
        print("------------------------------------------------------------------------------------------")
        print("------------------------------------------------------------------------------------------")
        print("------------------------------------------------------------------------------------------")
        print("------------------------------------------------------------------------------------------")
        print("------------------------------------------------------------------------------------------")
        print("search_results: ", search_results)




        return search_results