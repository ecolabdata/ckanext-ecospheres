import json
import logging
import ckan.plugins as p
from ckanext.dcat.interfaces import IDCATRDFHarvester
from ckanext.dcat.harvesters.rdf import DCATRDFHarvester
from ckanext.harvest.harvesters.base import HarvesterBase
from sqlalchemy import  inspect
import ckan.model as model
from ckanext.ecospheres.models.territories import Territories
import re
from ckanext.ecospheres.vocabulary.reader import VocabularyReader

def afficher(data):
    print(json.dumps(data, indent=4, sort_keys=True))


###############Constantes & Variables ######################
log = logging.getLogger(__name__)
TITLE='title'
URL='url'
IDENTIFIER="identifier"
DATA="data"
_IS_PART_OF='in_series'
_HAS_PART='series_member'
aggregation_mapping={
	_IS_PART_OF: "in_series",
	_HAS_PART: "series_member",
}

identifier_name_map={}


############################################################

class DCATfrRDFHarvester(DCATRDFHarvester):

    p.implements(IDCATRDFHarvester, inherit=True)
    def before_download(self, url, harvest_job):
        return url, []

    def update_session(self, session):
        return session

    def after_download(self, content, harvest_job):
        return content, []

    def after_parsing(self, rdf_parser, harvest_job):
        return rdf_parser, []

    def before_update(self, harvest_object, dataset_dict, temp_dict):
        pass
        
    def after_update(self, harvest_object, dataset_dict, temp_dict):
        return None
    
    
    def after_create(self, harvest_object, dataset_dict, temp_dict):

        # afficher(dataset_dict)
        return None
    
    def __get_organization_infos(self,harvest_object):
        org_owner_id=None
        try:
            source_dataset = model.Package.get(harvest_object.source.id)
            org_owner_id=source_dataset.owner_org
        except Exception as e:
            pass
        user = p.toolkit.get_action('get_site_user')(
                {'ignore_auth': True, 'defer_commit': True},
                {}) 
        _user_name = user['name']
        ctx = {'ignore_auth': True,
                'user': _user_name}
        org_dict = {'id': org_owner_id}
        act = p.toolkit.get_action('organization_show')
        org = act(context=ctx, data_dict=org_dict)
        return org

    def _get_territory(self,org):
        extras=org["extras"]
        for extra_element in extras:
            if extra_element["key"]=="Territoire":
                return extra_element["value"]

    

    def before_create(self, harvest_object, dataset_dict, temp_dict):
        
        spatial=dataset_dict.get("spatial",None)
        if not spatial:
            org=self.__get_organization_infos(harvest_object)
            territories_codes=self._get_territory(org)
            res=re.match(r'{(.*)}',territories_codes)
            resultats=res.group(1)
            #liste des territoires de competence de l'organisation
            departements=resultats.split(',')
            # print(departements)
            territories=[]
            if departements:
                for code_dep in departements:
                    uri,label_territory,_= VocabularyReader.get_territory_by_code_region(code_region=code_dep)
                    if uri:

                        territories.append({
                                            "label":label_territory.strip(), 
                                            "uri": uri})
                        #TODO: ajouter algo calculate GeoJSON
                        # spatial=VocabularyReader.get_territory_spatial_by_code_region(code_region=code_dep)
            dataset_dict["territory"]=territories

        self.__before_create(harvest_object,dataset_dict)
        
    
    def __aggregate(self,dataset_dict,key):
        urls_aggregated_list=list()
     
        if dataset_dict.get(key):
            
            data=dataset_dict[aggregation_mapping[key]]
            for object in data:
                id=self.__generate_name(object[IDENTIFIER],object[TITLE])
                
                urls_aggregated_list.append(
                    {
                        TITLE:object[TITLE],
                        URL: id,
                        IDENTIFIER:object[IDENTIFIER],
                    }
                )
                
            dataset_dict[aggregation_mapping[key]]=urls_aggregated_list
    
    def __before_create(self,harvest_object, dataset_dict):
        
        KEYS=[_IS_PART_OF,_HAS_PART]
        for key in KEYS:
            self.__aggregate(dataset_dict,key)
        dataset_dict["name"]=self.__generate_name(dataset_dict["identifier"],dataset_dict["title"])
             


    def _gen_new_name(self, title):
        try:
            return super(DCATfrRDFHarvester, self)._gen_new_name(title['fr'])  # noqa
        except TypeError:
            return super(DCATfrRDFHarvester, self)._gen_new_name(title)  # noqa



    def __generate_name(self,identifier,title):
        name=None
        #if dataset_dict[name] déja généré
        if identifier in identifier_name_map:
            return identifier_name_map[identifier]
        #génération du dataset_dict[name] 
        import re
        if re.match(r'^(https://).*$',identifier):
            res=re.match(r'^.*\/(.*)$',identifier)
            if res:
                id=res.group(1)
        else:
            id=title

        name = HarvesterBase._gen_new_name(id)
        if not name:
                raise Exception('Could not generate a unique name '
                            'from the title or the GUID. Please '
                            'choose a more unique title.')
        identifier_name_map[identifier]=name
        return name




    def after_create(self, harvest_object, dataset_dict, temp_dict):
        return None

    def update_package_schema_for_create(self, package_schema):
        return package_schema

    def update_package_schema_for_update(self, package_schema):
        return package_schema
  
    