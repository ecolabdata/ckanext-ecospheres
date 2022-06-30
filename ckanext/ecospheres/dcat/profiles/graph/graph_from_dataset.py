
try:
    import logging
    from ..constants import (
        namespaces,
        DCT,
        DCAT,
        OWL,
        RDF,
        FOAF,
        RDFS,
        XSD,

        Literal
    )
    from ckanext.dcat.utils import resource_uri
    from rdflib import URIRef, BNode, Literal
    from ._functions import (
        _set_qualifiedAttribution,
        _set_primary_topic_of,
        _set_version_notes,
        _set_language,
        _set_conforms_to,
        _set_crs,
        _set_access_rights,
        _set_documentation_page,
        _set_relations_in_series,
        _set_relations_series_member,
        _set_relations,
        _set_contact_point,
        _clean_lagacy_nodes,
        _set_publisher,
        _set_creator,
        _set_rights_holder,
        _set_temporal_coverage,
        _set_bbox,
        _set_spatial_coverage,
        _set_provenance,
        
    )
except Exception as e:
    raise ValueError("Erreur lors de l'import de variables ou de fonctions")


def _add_multilang_value(self, subject, predicate, dataset_key=None, dataset_dict=None, multilang_values=None):  # noqa
        if not multilang_values and dataset_dict and dataset_key:
            multilang_values = dataset_dict.get(dataset_key)
        if multilang_values:
            try:
                for key, values in multilang_values.iteritems():
                    if values:
                        # the values can be either a multilang-dict or they are
                        # nested in another iterable (e.g. keywords)
                        if not hasattr(values, '__iter__'):
                            values = [values]
                        for value in values:
                            self.g.add((subject, predicate, Literal(value, lang=key)))  # noqa
                    # add default for each language
                    else:
                        self.g.add((subject, predicate, Literal('', lang=key)))  # noqa
            # if multilang_values is not iterable, it is simply added as a non-
            # translated Literal
            except AttributeError:
                self.g.add((subject, predicate, Literal(multilang_values)))


def graph_from_dataset(self, dataset_dict, dataset_ref):
    
    logging.info("Create graph from dataset '%s'" % dataset_dict['name'])

    g=self.g
    for prefix, namespace in namespaces.items():
        g.bind(prefix, namespace)
        
    g.add((dataset_ref, RDF.type, DCAT.Dataset))
    
    
    ############################################   Littéraux  ############################################

    items = [
        # identifier
        ('identifier', DCT.identifier, ['guid', 'id'], Literal),
        # date de modification
        ('modified', DCT.modified, None, Literal),
        
        # date de creation 
        ('created', DCT.created, None, Literal),
        
        # date de publication
        ('issued', DCT.issued, None, Literal),
        
        # URL de la fiche sur le catalogue source
        ('landing_page', DCAT.landingPage, None, Literal),
        
        # frequence de mise à jour
        ('accrual_periodicity', DCT.accrualPeriodicity, None, Literal),
        
        # version
        ('version', OWL.versionInfo, None, Literal),
        
        # temporal_resolution
        ('temporal_resolution', DCAT.temporalResolution, None, Literal),
        
        # spatial_resolution
        ('spatial_resolution', DCAT.spatialResolutionInMeters, None, Literal),
        
        # subject
        ('subject', DCT.subject, None, Literal),
        
        # subject
        ('attributes_page', FOAF.page, None, Literal),
        
    ]
    

    
    self._add_triples_from_dict(dataset_dict, dataset_ref, items)
        
    items = [
        # date de modification
        ('modified', DCT.modified, None, Literal),
        
        # date de creation 
        ('created', DCT.created, None, Literal),
        
        # date de publication
        ('issued', DCT.issued, None, Literal),
        
        
    ]
    

    self._add_date_triples_from_dict(dataset_dict, dataset_ref, items)

        
    
    
    ############################################   LItteruw multilangue  ############################################
    # # description {*}
    # g.add((_dataset_ref, ADMS.versionNotes, Literal(notes, lang=lang)))
    for obj in g.objects(dataset_ref, DCT.description):
        g.remove((dataset_ref, DCT.description, obj,))
    
    notes_dict=dataset_dict.get("notes",None)
    for lang, notes in notes_dict.items():
        g.add((dataset_ref, DCT.description, Literal(notes, lang=lang)))


    for obj in g.objects(dataset_ref, DCT.title):
        g.remove((dataset_ref, DCT.title, obj,))
    
    notes_dict=dataset_dict.get("title",None)
    for lang, _title in notes_dict.items():
        g.add((dataset_ref, DCT.title, Literal(_title, lang=lang)))



    ############################################   Dates  ############################################
    
    """
        valeurs littérales : created, modified, issued -> Cf. Littéraux
    """

    """------------------------------------------<Temporal>------------------------------------------"""
    # > dct:temporal
    _set_temporal_coverage(self, g, dataset_dict, dataset_ref)
    
    
    
    ############################################   Organisations  ############################################

    
    """------------------------------------------<Contact_point>------------------------------------------"""
    # > dcat:contactPoint -> vcard:Kind
    _set_contact_point(self, g, dataset_dict, dataset_ref)
    

    """------------------------------------------<Publisher>------------------------------------------"""
    # > dct:publisher -> foaf:Organization
    _set_publisher(self, g, dataset_dict, dataset_ref)
    

    """------------------------------------------<Creator>------------------------------------------"""
    # > dct:creator -> foaf:Organization
    _set_creator(self, g, dataset_dict, dataset_ref)
    

    """------------------------------------------<rightsHolder>------------------------------------------"""
    # dct:rightsHolder -> foaf:Organization
    _set_rights_holder(self, g, dataset_dict, dataset_ref)

    
    """------------------------------------------<qualifiedAttribution>------------------------------------------"""
    # QUALIFIED_ATTRIBUTION [{}]
    # > prov:qualifiedAttribution -> prov:Attribution
    _set_qualifiedAttribution(self, g, dataset_dict, dataset_ref)
    

    ############################################   Relations  ############################################
    
    """------------------------------------------<in_series>------------------------------------------"""
    #in_series
    _set_relations_in_series(self, g, dataset_dict, dataset_ref)
    
    """------------------------------------------<series_dataset>------------------------------------------"""
    #series_dataset
    _set_relations_series_member(self, g, dataset_dict, dataset_ref)


    ############################################   Références  ############################################

    """------------------------------------------<attributes_page>------------------------------------------"""
    # ATTRIBUTE_PAGE
    # > foaf:page
    # [+ DCAT-AP]
    
    
    """------------------------------------------<page>------------------------------------------"""
    # # PAGE [{}]
    # > foaf:page -> foaf:Document
    
    _set_documentation_page(self, g , dataset_dict, dataset_ref)



    ############################################   Thèmes et mots clés   ############################################

    """------------------------------------------ category ------------------------------------------"""
    # CATEGORY []
    # > dcat:theme
    
    """------------------------------------------ subcategory ------------------------------------------"""
    # SUBCATEGORY []
    # > dcat:theme
    
    """------------------------------------------ theme ------------------------------------------"""
    # THEME []
    # > dcat:theme
    
    
    """------------------------------------------ subject ------------------------------------------"""
    # > dct:subject


    """------------------------------------------ free_tags ------------------------------------------"""
    # FREE_TAG [{*}]
    # > dcat:keyword
    
    #pas tres clair pour l'instant Cf. ecospheres_dataset_schema.yaml
    


    
    ############################################   Métadonnées sur les métadonnées   ############################################
    
    """------------------------------------------ is_primary_topic_of ------------------------------------------"""
    # IS_PRIMARY_TOPIC_OF [{}]
    # > foaf:isPrimaryTopicOf -> dcat:CatalogRecord
    # [- DCAT-AP v2]
    _set_primary_topic_of(self, g, dataset_dict, dataset_ref)

    
    ############################################   Couverture spatiale   ############################################
    
    """------------------------------------------ bbox ------------------------------------------"""
    # > dct:spatial [-> dct:Location] / dcat:bbox
    # BBOX
    _set_bbox(self, g, dataset_dict, dataset_ref)

    """------------------------------------------spatial_coverage ------------------------------------------"""
    # SPATIAL_COVERAGE [{}]
    # > dct:spatial -> dct:Location
    _set_spatial_coverage(self, g, dataset_dict, dataset_ref)


    ############################################   Etc   ############################################
    
    """------------------------------------------access_rights ------------------------------------------"""
    # ACCESS_RIGHTS [{}]
    # > dct:accessRights -> dct:RightsStatement
    _set_access_rights(self, g, dataset_dict, dataset_ref)
    
    
    """------------------------------------------crs ------------------------------------------"""
    # CRS []
    # > dct:conformsTo
    _set_crs(self, g, dataset_dict, dataset_ref)

    """------------------------------------------conforms_to ------------------------------------------"""
    # CONFORMS_TO
    # > dct:conformsTo -> dct:Standard
    #pas très clair
    _set_conforms_to(self, g, dataset_dict, dataset_ref)

    """------------------------------------------ accrualPeriodicity ------------------------------------------"""
    # ACCRUAL_PERIODICITY
    # > dct:accrualPeriodicity
    #voir littéraux


    """------------------------------------------language ------------------------------------------"""
    # LANGUAGE []
    # > dct:language    
    _set_language(self, g, dataset_dict, dataset_ref)

    
    """------------------------------------------ provenance ------------------------------------------"""
    # PROVENANCE [{*}]
    # > dct:provenance [-> dct:ProvenanceStatement] / rdfs:label
    # [+ DCAT-AP]
    _set_provenance(self, g, dataset_dict, dataset_ref)



    """------------------------------------------ version notes ------------------------------------------"""
    # VERSION_NOTES {*}
    # > adms:versionNotes
    _set_version_notes(self, g, dataset_dict, dataset_ref)


    """------------------------------------------ version ------------------------------------------"""
    # VERSION
    # > owl:versionInfo
    # voir littéraux
    
    
    """------------------------------------------  temporal_resolution ------------------------------------------"""
    # TEMPORAL_RESOLUTION
    # > dcat:temporalResolution
    # voir littéraux
    
    """------------------------------------------ spatial_resolution   ------------------------------------------"""
    # SPATIAL_RESOLUTION
    # > dcat:spatialResolutionInMeters
    # voir littéraux

    ############################################   RESSOURCES ############################################
    for obj in g.objects(dataset_ref, DCAT.distribution):
        g.remove((dataset_ref, DCAT.distribution, obj,))


    for resource_dict in dataset_dict.get('resources', []):
        distribution = URIRef(resource_uri(resource_dict))
        g.add((dataset_ref, DCAT.distribution, distribution))
        g.add((distribution, RDF.type, DCAT.Distribution))


        """------------------------------------------ title   ------------------------------------------"""
        # # TITLE {*}
        # # > dct:title
        if names:=resource_dict.get("name",None):
            for lang in names:
                g.add((distribution,  DCT.title, Literal(names[lang], lang=lang)))


        """------------------------------------------ description   ------------------------------------------"""
        # DESCRIPTION {*}
        # > dct:description
        if descriptions:=resource_dict.get("description",None):
            for lang in descriptions:
                g.add((distribution,  DCT.description, Literal(descriptions[lang], lang=lang)))


        """------------------------------------------ media_type_ressource   ------------------------------------------"""
        # MEDIA_TYPE [{}]
        # > dcat:mediaType -> dct:MediaType
        if media_type_ressource:=resource_dict.get("media_type_ressource",None):
            for media_type_element in media_type_ressource:

            if uri:=media_type_element.get("uri",None):
                media_type_ressource_node=URIRef(uri)
            else:
                media_type_ressource_node=BNode()
                
            g.add((media_type_ressource_node, RDF.type, DCT.MediaType))
            g.add((distribution, DCT.mediaType, media_type_ressource_node))

            if labels:=media_type_element.get("label",None):
                for lang in labels:
                    g.add((media_type_ressource_node, RDFS.label, Literal(labels[lang],lang=lang)))


        """------------------------------------------ other_format   ------------------------------------------"""
        # OTHER_FORMAT [{}]
        # > dct:format -> dct:MediaTypeOrExtent
        if other_format:=resource_dict.get("other_format",None):
            if uri:=other_format.get("uri",None):
                other_format_node=URIRef(uri)
            else:
                other_format_node=BNode()
                
            g.add((other_format_node, RDF.type, DCT.MediaTypeOrExtent))
            g.add((distribution, DCT["format"], other_format_node))

            if labels:=other_format.get("label",None):
                for lang in labels:
                    g.add((other_format_node, RDFS.label, Literal(labels[lang],lang=lang)))

        """------------------------------------------ service_conforms_to   ------------------------------------------"""
        # SERVICE_CONFORMS_TO [{}]
        # > dcat:accessService [-> dcat:DataService] / dct:conformsTo
        if service_conforms_to:=resource_dict.get("service_conforms_to",None):
            service_conforms_to_node=BNode()
            g.add((service_conforms_to_node, RDF.type, DCAT.DataService))
            g.add((distribution, DCT.accessService, service_conforms_to_node))
            
            for lang in service_conforms_to:
                g.add((service_conforms_to_node, DCT.conformsTo, Literal(service_conforms_to[lang],lang=lang)))


        """------------------------------------------ rights   ------------------------------------------"""
        # RIGHTS {*}
        # > dct:rights [-> dct:RightsStatement] / rdfs:label
        if access_rights:=resource_dict.get("rights",None):
            if labels:=access_rights.get("label",None):
                access_right_node=BNode()
                g.add((access_right_node, RDF.type, DCT.RightsStatement))
                g.add((distribution, DCT.rights, access_right_node))
                for lang in labels:
                    g.add((access_right_node, RDFS.label, Literal(labels[lang],lang=lang)))


        """------------------------------------------ licenses   ------------------------------------------"""
        # LICENSE [{}]
        # > dct:license -> dct:LicenseDocument
        if licenses:=resource_dict.get("licenses",None):
            for license in licenses:
                if uri:=license.get("uri",None):
                    license_node=URIRef(uri)
                else:
                    license_node=BNode()
                
                g.add((license_node, RDF.type, DCT.LicenseDocument))
                g.add((distribution, DCT.license, license_node))
                
                # TYPE []
                # > dct:type
                if _type:=license.get("type",None):
                    g.add((license_node, DCT.type, Literal(_type)))
                
                # LABEL {*}
                # > rdfs:label
                if labels:=license.get("label",None):
                    for lang in labels:
                        g.add((license_node, RDFS.label, Literal(labels[lang],lang=lang)))


        """------------------------------------------ resource_issued   ------------------------------------------"""
        # ISSUED
        # > dct:issued
        if issued:=resource_dict.get("resource_issued"):
            g.add((distribution, DCT.issued, Literal(issued,
                                                  datatype=XSD.dateTime)))