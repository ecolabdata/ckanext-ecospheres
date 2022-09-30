try:
    import rdflib
    from ckan.plugins import toolkit
    from ckantoolkit import config
    from rdflib import URIRef, BNode
    import os
    import json,logging,re 
    from pathlib import Path
    from os.path import exists
    from ckanext.ecospheres.vocabulary.reader import VocabularyReader


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
                                    _language,
                                    _provenance,
                                    _version_notes,
                                    _tags_keywords,
                                    _check_sous_theme,
                                    _crs_list
                            )
except Exception as e: 
    raise ValueError("Erreur lors de l'import de librairies: ",str(e))





import os
log = logging.getLogger(__name__)




def parse_dataset(self, dataset_dict, dataset_ref):
    '''
    Crée un jeu de données CKAN dict à partir du graphe RDF `dataset_ref`.
    
    Retourne un dict `dataset_dict` de données qui peut être passé à `package_create`.
        ou `package_update`.
    '''
    
    
    """------------------------------------------<Littéraux>------------------------------------------"""

    for key, predicate in (
                            ('uri', DCT.identifier), #uri du dataset
                            ('identifier', DCT.identifier), #idetifier
                            ('accrual_periodicity', DCT.accrualPeriodicity), #idetifier
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
    """-------------------------------------------<serie_datasets,in_series>-------------------------------------------"""        
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
    """
    
    for key, predicate in (
                            ('landing_page', DCAT.landingPage), # landing_page: Accès à la fiche sur le catalogue source
                            # ("attributes_page",FOAF.page), # conflit avec documentation 
                            ):
        # if key =="attributes_page":
        #     value=self._object_value_list(dataset_ref, predicate)
        # else:
        value = self._object_value(dataset_ref, predicate)
        if value:
            dataset_dict[key] = value
    
    
    """-------------------------------------------<page>-------------------------------------------"""        
    '''
    page: Documentation
        -> uri: URL
        -> title:Titre
        -> Description: Description
        -> modified: Date de modification
        -> created: Date de création
        -> issued: Date de publication

    '''
    _get_documentation_dict(self,dataset_ref,dataset_dict,FOAF.page)
    




    ############################################   Thèmes et mots clés  ############################################
    themes=VocabularyReader.themes()

    list_keywords=list(self._object_value_list(dataset_ref,DCAT.keyword))
    title = self._object_value(dataset_ref, DCT.title)
    categories=dict()
    
    for theme in themes:
        sous_theme,uri_sous_theme=_check_sous_theme(themes[theme]["child"],list_keywords,title)
        if sous_theme:
            theme_label=themes[theme].get("label")
            if not categories.get(theme_label,None):
                categories[theme_label]={
                                        "theme":theme_label,
                                        "uri": themes[theme].get("uri")
                                    }


            if not categories.get(sous_theme,None):
                categories[sous_theme]={
                                        "theme":sous_theme,
                                        "uri": uri_sous_theme
                                        }

    """-------------------------------------------<category>-------------------------------------------"""        

    # CATEGORY []
    if categories:
        dataset_dict["category"]=list(categories.values())



    """-------------------------------------------<theme>-------------------------------------------"""        
    themes=[]
    # THEME []
    # > dcat:theme
    themes_dataset=list(self._object_value_list(dataset_ref,DCAT.theme))
    if themes_dataset:
        for t in themes_dataset:
            themes.append({"uri":t})
    subject=self._object_value(dataset_ref,DCT.subject)
    if subject:
        themes.append(
            {
            "uri": subject
            })
    
    dataset_dict["theme"]=themes
    
    """-------------------------------------------< tags, free_tags >-------------------------------------------"""        
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

    ############################################   Etc. ############################################

    """-------------------------------------------<access_rights>-------------------------------------------"""        
    _access_rights(self,dataset_ref, DCT.accessRights,dataset_dict)

    """-------------------------------------------<restricted_access>-------------------------------------------"""   
    #TODO: 
    import random
    dataset_dict["restricted_access"]=random.choice([True,False])

    """-------------------------------------------<crs>-------------------------------------------"""   
    _crs_list(self,dataset_ref, DCT.conformsTo,dataset_dict)

    """-------------------------------------------<conforms_to>-------------------------------------------"""        
    _conforms_to(self,dataset_ref, DCT.conformsTo,dataset_dict)
    
    
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
        other_format_list=[]
        for format_node in self.g.objects(distribution, DCT['format']):
            other_format_dict={}
            for key, predicate in (
                            ('label', RDFS.label),
                            ):
                        value = _object_value_multilang(self,format_node, predicate,multilang=True)
                        if value:
                            other_format_dict[key]=value
            other_format_dict["uri"]=str(format_node)
            other_format_list.append(other_format_dict)
            if other_format_dict:
                resource_dict["other_format"]=other_format_list
        
        """-------------------------------------------<format>-------------------------------------------"""        
        if media_type:=resource_dict.get("media_type_ressource",None):
            try:
                resource_dict["format"]=media_type[0].get('uri')
            except:
                pass


        if not resource_dict.get("format",None):
            try:
                if other_format:=resource_dict.get("other_format",None):
                    resource_dict["format"]=other_format[0].get('uri')
            except:
                pass

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
    
    if not dataset_dict.get('modified',None):
        if creation_data:=dataset_dict.get('created',None):
            dataset_dict['modified']=creation_data
        elif issued_date:=dataset_dict.get('issued',None):
            dataset_dict['modified']=issued_date
        else:
            import datetime
            dataset_dict['modified'] = datetime.datetime.today().isoformat("T")

    return dataset_dict
