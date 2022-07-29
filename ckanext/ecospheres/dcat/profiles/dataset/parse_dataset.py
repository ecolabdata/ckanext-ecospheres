try:
    import rdflib
    from ckan.plugins import toolkit
    from ckantoolkit import config
    from rdflib import URIRef, BNode
    import os
    import json,logging,re 
    from pathlib import Path
    from os.path import exists

    from rdflib.namespace import RDF, SKOS
    from ..constants import (
        _IS_PART_OF,
        _HAS_PART,
        FREQ_BASE_URI,
        REGEX_PATTERN_THEME,
        PROV
        
    )
    from ckanext.dcat.profiles import (
        ADMS,
        DCAT,
        DCT,
        FOAF,
        LOCN,
        OWL,
        SCHEMA,
        TIME,
        VCARD,
        RDFS,
        SPDX,

    )
    from ckan.lib.helpers import lang
    from ._functions import (_parse_agent,
                                    _contact_points,
                                    _get_frequency,
                                    _build_genealogie,
                                    _bbox_spatial,
                                    _get_documentation_dict,
                                    _get_temporal,
                                    add_tag,
                                    _object_value_multilang,
                                    _qualified_attribution,
                                    _is_primary_topic_of,
                                    _spatial_coverage,
                                    _access_rights,
                                    _conforms_to,
                                    _accrual_periodicity,
                                    _language,
                                    _provenance,
                                    _version_notes,
                                    _tags_keywords,
                                    _check_sous_theme
                            )
except Exception as e: 
    raise ValueError("Erreur lors de l'import de librairies: ",str(e))



PATH_THEMES="/srv/app/src_extensions"
FILENAME_THEME="ref_themes.json"



def _get_theme_registry_as_json():
    try:
        p = Path(PATH_THEMES)
        path = p / FILENAME_THEME
        file_exists = exists(path)
        if not file_exists:
            return None
        with open(path, 'r') as f:
            return json.loads(f.read())
    except Exception as e:
        print(e)
        raise Exception("Erreur lors de la lecture du fichier json des themes")


log = logging.getLogger(__name__)

def afficher(data):
        print(json.dumps(data, indent=4, sort_keys=True))





def parse_dataset(self, dataset_dict, dataset_ref):
    """------------------------------------------<Littéraux>------------------------------------------"""

    for key, predicate in (
                            ('uri', DCT.identifier), #uri du dataset
                            ('identifier', DCT.identifier), #idetifier
                            ):
        value = self._object_value(dataset_ref, predicate)
        if value:
            dataset_dict[key] = value
            
            
    """multilang fields"""
    for key, predicate in (
                            ("title",DCT.title),
                            ('notes', DCT.description), # description/notes du dataset
                            ('description', DCT.description), # description/notes du dataset
                            ):
        value = _object_value_multilang(self,dataset_ref, predicate,multilang=True)
        if value:
            dataset_dict[key] = value
            
    
    
    ############################################   Dates  ############################################

    """-------------------------------------------<Temporal>-------------------------------------------"""        
    """
    Couverture temporelle:
        -start_date
        -end_date
    """
    _get_temporal(self,dataset_ref, DCT.temporal,dataset_dict)



    """-------------------------------------------< created, modified, issued >-------------------------------------------"""        
    """ Dates:
        -created: date de creation
        -modified: date de modification
        -issued: date de publication
        """        
    for key, predicate in (
                            ("created",DCT.created),#date de creation
                            ("modified",DCT.modified),# date de modification
                            ("issued",DCT.issued), # date de publication
                            ):
        value = self._object_value(dataset_ref, predicate)
        if value:
            """On supprime la timezone"""
            dataset_dict[key] = value
    
    
    ############################################   Organisations  ############################################
    
    """-------------------------------------------<contact_point>-------------------------------------------"""        
    """ champs communs à [contact_point, publisher, creator, rights_holder] 
    - name: Nom
    - type: type
    - email: Courriel
    - phone: Téléphone
    - url: Site internet
    - acronym: Sigle
    - title: titre
    - comment: Commentaire
    """
    """Points de contact"""
    
    _contact_points(self,
        dataset_ref,
        DCAT.contactPoint,
        dataset_dict
    )

    """-------------------------------------------<publisher>-------------------------------------------"""        
    _parse_agent(self,
                dataset_ref, 
                DCT.publisher,
                dataset_dict,
                keybase="publisher")

    
    """-------------------------------------------<creator>-------------------------------------------"""        
    _parse_agent(self,
                dataset_ref, 
                DCT.creator,
                dataset_dict,
                keybase="creator")
    

    """-------------------------------------------<rights_holder>-------------------------------------------"""        
    _parse_agent(self,
                dataset_ref, 
                DCT.rights_holder,
                dataset_dict,
                keybase="rights_holder")
    
    

    """-------------------------------------------<qualified_attribution>-------------------------------------------"""        
    _qualified_attribution(self,
                            dataset_ref, 
                            PROV.qualifiedAttribution,
                            dataset_dict)

    
    ############################################   Relations  ############################################
    """-------------------------------------------<in_series>-------------------------------------------"""        
    """-------------------------------------------<serie_datasets>-------------------------------------------"""        
    """ 
        in_series: isPartOf (Inclus dans les séries de données)
        serie_datasets: hasPart (Jeux de données de la série)
    """
    for key, predicate in (	
                            (_IS_PART_OF, DCT.isPartOf),
                            (_HAS_PART, DCT.hasPart),
                          ):
        _build_genealogie(self,dataset_ref,key,predicate,dataset_dict)
    
    
    ############################################   Références  ############################################
    
    """-------------------------------------------<landing_page, attributes_page >-------------------------------------------"""        
    """
    landing_page: Accès à la fiche sur le catalogue source
    attributes_page: Lien de la page où sont décrits les champs du jeu de données.
    page: Documentation
        -> uri: URL
        -> title:Titre
        -> Description: Description
        -> modified: Date de modification
        -> created: Date de création
        -> issued: Date de publication
    """
    
    for key, predicate in (
                            ('landing_page', DCAT.landingPage), # landing_page: Accès à la fiche sur le catalogue source
                            ("attributes_page",FOAF.page),
                            ):
        if key =="attributes_page":
            value=self._object_value_list(dataset_ref, predicate)
        else:
            value = self._object_value(dataset_ref, predicate)
        if value:
            dataset_dict[key] = value
    
    
    """-------------------------------------------<page>-------------------------------------------"""        
    _get_documentation_dict(self,dataset_ref,dataset_dict,FOAF.page)
    




    ############################################   Thèmes et mots clés  ############################################
    # récuperation des listes des themes
    try:
        list_themes_ecosphere_as_dict=_get_theme_registry_as_json()
        list_themes_ecosphere_as_dict=list_themes_ecosphere_as_dict.get("themes",None)
    except Exception as e:
        print(str(e))



    #liste des mots clés du dataset
    list_keywords=list(self._object_value_list(dataset_ref,DCAT.keyword))

    title = self._object_value(dataset_ref, DCT.title)

    categories={}
    subcategories={}

    for theme_ecosphere in list_themes_ecosphere_as_dict:

        is_match,sous_theme,uri_sous_theme=_check_sous_theme(theme_ecosphere,list_keywords,title)

        if is_match:
            
            pref_label=theme_ecosphere.get("prefLabel",None)

            if not categories.get(pref_label,None):
                categories[pref_label]={
                                        "theme":pref_label,
                                        "uri": theme_ecosphere.get("uri",None)
                                       }


            if not subcategories.get(sous_theme,None):
                subcategories[sous_theme]={
                                            "subtheme":sous_theme,
                                            "uri": uri_sous_theme
                                          }



    if not subcategories and not categories:
        #TODO: Theme ecosphere non trouvé 
        pass

    """-------------------------------------------<category>-------------------------------------------"""        

    # CATEGORY []
    # > dcat:theme
    # - pour le premier niveau de thèmes de la nomenclature du guichet
    # - déduit de "theme", "subject" et "free_tag" lors du moissonnage
    # - stockage sous forme d'une liste d'URI (appartenant au registre
    #   du guichet)
    # - les étiquettes des URI seraient à mapper sur la propriété
    #   "tags" lors du moissonnage
    
    if categories:
        dataset_dict["category"]=list(categories.values())



    """-------------------------------------------<subcategory>-------------------------------------------"""        
    # SUBCATEGORY []
    # > dcat:theme
    # - pour le second niveau de thèmes de la nomenclature du guichet
    # - déduit de "theme", "subject" et "free_tag" lors du moissonnage
    # - stockage sous forme d'une liste d'URI (appartenant au registre
    #   du guichet)
    # - les étiquettes des URI seraient à mapper sur la propriété
    #   "tags" lors du moissonnage
    
    if subcategories:
        dataset_dict["subcategory"]=list(subcategories.values())


    """-------------------------------------------<theme>-------------------------------------------"""        
    # THEME []
    # > dcat:theme
    # - pour les nomemclatures externes, notamment celle de la commission
    #   européenne et la nomenclature INSPIRE
    # - mapper dct:subject vers cette propriété (utilisé dans GeoDCAT-AP v2
    #   pour les catégories ISO)
    # - stockage sous la forme d'une liste d'URI
    # - les étiquettes des URI seraient à mapper sur la propriété
    #   "tags" lors du moissonnage


    """-------------------------------------------<subject>-------------------------------------------"""        
    # > dct:subject
    # nomenclatures externes, notamment les thèmes ISO
    # stockage sous la forme d'une liste d'URI


    
    
    """-------------------------------------------<free_tags>-------------------------------------------"""        
    # tags=dataset_dict["tags"]
    # # TODO: juste pour tester
    # add_tag(tags,['un','deux'])
    # add_tag(tags,'trois')
    # dataset_dict["tags"]=tags
    # dataset_dict["free_tags"]=tags
    
    """-------------------------------------------<tags>-------------------------------------------"""        
    _tags_keywords(self,dataset_ref,
                            DCAT.keyword,
                            dataset_dict)
    
    ############################################   Métadonnées sur les métadonnées   ############################################
    """-------------------------------------------< is_primary_topic_of >-------------------------------------------"""        
    ## > foaf:isPrimaryTopicOf -> dcat:CatalogRecord
    _is_primary_topic_of(self,dataset_ref,
                            FOAF.isPrimaryTopicOf,
                            dataset_dict)


    
    ############################################   Couverture spatiale  ############################################
    """-------------------------------------------<bbox>-------------------------------------------"""        
    _bbox_spatial(self,dataset_ref, DCT.spatial,dataset_dict)

    
    """-------------------------------------------<spatial_coverage>-------------------------------------------"""        
    _spatial_coverage(self,dataset_ref, DCT.spatial,dataset_dict)

    """-------------------------------------------<TERRITORY>-------------------------------------------"""        
    # import random
    # mocked_territories=["paris","lyon","brest","lille"]
    # dataset_dict["territory"]=random.choice(mocked_territories)

    ############################################   Etc. ############################################

    """-------------------------------------------<access_rights>-------------------------------------------"""        
    _access_rights(self,dataset_ref, DCT.accessRights,dataset_dict)



    """-------------------------------------------<crs>-------------------------------------------"""   
    # TODO: 

    """-------------------------------------------<conforms_to>-------------------------------------------"""        
    _conforms_to(self,dataset_ref, DCT.conformsTo,dataset_dict)
    
    
    """-------------------------------------------<accrual_periodicity>-------------------------------------------"""        
    _accrual_periodicity(self,dataset_ref,DCT.accrualPeriodicity,dataset_dict)

    

    """-------------------------------------------<language>-------------------------------------------"""        
    _language(self,dataset_ref,DCT.language,dataset_dict)
    

    """-------------------------------------------<provenance>-------------------------------------------"""        
    _provenance(self,dataset_ref,DCT.provenance,dataset_dict)
    

    """-------------------------------------------<version>-------------------------------------------"""        
    for key, predicate in (
                            ("version",OWL.versionInfo),
                            ):
        value = self._object_value(dataset_ref, predicate)
        if value:
            dataset_dict[key] = value    


    """-------------------------------------------<version_notes>-------------------------------------------"""        
    _version_notes(self,dataset_ref,ADMS.versionNotes,dataset_dict)
    
    

    """-------------------------------------------<temporal_resolution>-------------------------------------------"""        
    for key, predicate in (
                            ("temporal_resolution",DCAT.temporalResolution),
                            ):
        value = self._object_value(dataset_ref, predicate)
        if value:
            dataset_dict[key] = value   


    """-------------------------------------------<spatial_resolution>-------------------------------------------"""        
    for key, predicate in (
                            ("spatial_resolution",DCAT.spatialResolutionInMeters),
                            ):
        value = self._object_value(dataset_ref, predicate)
        if value:
            dataset_dict[key] = value   
    
        
    
    dataset_dict["extras"]=[]
    dataset_dict["resources"]=[]    



    ############################################   RESSOURCES ############################################
    
    for distribution in self._distributions(dataset_ref):
        resource_dict = {}

        """-------------------------------------------<URI>-------------------------------------------"""        
        if uri:=(str(distribution)
                                if isinstance(distribution,
                                                rdflib.term.URIRef)
                                else ''):
            resource_dict['uri'] = uri
        
        
        """-------------------------------------------<URL>-------------------------------------------"""        
        
        if url:=self._object_value(distribution,
                                                    DCAT.accessURL):
            resource_dict['url'] = url
                

        """-------------------------------------------<url_download,>-------------------------------------------"""        
        if url_download:=self._object_value(distribution,
                                                    DCAT.downloadURL):
            resource_dict['url_download'] = url_download
        


        """-------------------------------------------<title, description: multilangue>-------------------------------------------"""        
        #  Simple values
        for key, predicate in (
                ('name', DCT.title),
                ('description', DCT.description),
                ):
            value = _object_value_multilang(self,distribution, predicate,multilang=True)
            if value:
                resource_dict[key] = value



        """-------------------------------------------<media_type_ressource>-------------------------------------------"""        
        _media_type_list=[]
        for format_node in self.g.objects(distribution,  DCAT.mediaType):
            _media_type_dict={}
            for key, predicate in (
                            ('label', RDFS.label),
                            ):
                        value = _object_value_multilang(self,format_node, predicate,multilang=True)
                        if value:
                            _media_type_dict[key]=value
            _media_type_dict['uri']=str(format_node)
            _media_type_list.append(_media_type_dict)
        resource_dict['media_type_ressource'] = _media_type_list
        

        """-------------------------------------------<other_format>-------------------------------------------"""        
        #TODO: corriger 
        for format_node in self.g.objects(distribution, DCT['format']):
            other_format_dict={}
            for key, predicate in (
                            ('label', RDFS.label),
                            ):
                        value = _object_value_multilang(self,format_node, predicate,multilang=True)
                        if value:
                            other_format_dict[key]=value
            other_format_dict["uri"]=str(format_node)
            if other_format_dict:
                resource_dict["other_format"]=other_format_dict
        
        """-------------------------------------------<format>-------------------------------------------"""        
        for key, predicate in (
                    ('format', DCAT.mediaType),
                    ):
                value = self._object_value(distribution, predicate)
                if value:
                    resource_dict[key]=value

        """-------------------------------------------<service_conforms_to>-------------------------------------------"""        
        for node in self.g.objects(distribution, DCAT.accessService):
            for key, predicate in (
                            ('service_conforms_to', DCT.conformsTo),
                            ):
                        value = _object_value_multilang(self,node, predicate,multilang=True)
                        if value:
                            resource_dict[key] = value

        """-------------------------------------------<rights>-------------------------------------------"""        

        _rights_dict=None
        for rights_node in self.g.objects(distribution,  DCT.rights):
            _rights_dict={}
            for key, predicate in (
                            ('label', RDFS.label),
                            ):
                        value = _object_value_multilang(self,rights_node, predicate,multilang=True)
                        if value:
                            _rights_dict[key]=value
        if _rights_dict:
            resource_dict['rights']=_rights_dict

        """-------------------------------------------<licenses>-------------------------------------------"""        
        licences=[]
        for node in self.g.objects(distribution, DCT.license):
            license={}
            for key, predicate in (
                            ('type', DCT.type),
                            ('label', RDFS.label),
                            ):
                        if key=="label":
                            value = _object_value_multilang(self,node, predicate,multilang=True)
                        else: 
                            value=self._object_value(node, predicate)
                        if value:
                            license[key] = value
                        license["uri"]=str(node)
            licences.append(license)
        if licences:
            resource_dict['licenses'] = licences
            
        """-------------------------------------------<resource_issued>-------------------------------------------"""        
        for key, predicate in (
                        ('resource_issued', DCT.issued),
                        ):
                    value = self._object_value(distribution, predicate)
                    if value:
                        resource_dict[key] = value
        dataset_dict['resources'].append(resource_dict)
    return dataset_dict
