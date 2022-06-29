import json
import logging
import ckan.plugins as p
from ckanext.dcat.interfaces import IDCATRDFHarvester
from ckanext.dcat.harvesters.rdf import DCATRDFHarvester
from ckanext.harvest.harvesters.base import HarvesterBase


def afficher(data):
    print(json.dumps(data, indent=4, sort_keys=True))

###############Constantes & Variables ######################
log = logging.getLogger(__name__)
TITLE='title'
URL='url'
IDENTIFIER="identifier"
DATA="data"
_IS_PART_OF='isPartOf'
_HAS_PART='hasPart'
aggregation_mapping={
	_IS_PART_OF: "in_series",
	_HAS_PART: "serie_datasets",
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
        
        # if "documentation" in dataset_dict:
        import re
        identifier=dataset_dict["identifier"]
        if re.match(r'^(https://).*$',identifier):
            res=re.match(r'^.*\/(.*)$',dataset_dict["identifier"])
            if res:
                print(f'groups:\t{res.group(1)}')
        else:
            print("identifier is not an url")
        pass

    def after_update(self, harvest_object, dataset_dict, temp_dict):
        return None

        
        
    def before_create(self, harvest_object, dataset_dict, temp_dict):
        
       
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
  
    