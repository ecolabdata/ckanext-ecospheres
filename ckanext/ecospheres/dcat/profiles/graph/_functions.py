
try:
    from ..constants import (
                        DCT,
                        DCAT,
                        VCARD,
                        SCHEMA,
                        ADMS,
                        FOAF,
                        TIME,
                        LOCN,
                        GSP,
                        OWL,
                        XSD,
                        SPDX,
                        XML,
                        PROV,
                        namespaces,
                        RDFS,
                        RDF,
                        ORG,
                        SKOS,
                        _TYPE  ,
                        _NAME  ,
                        _AFFILIATION  ,
                        _PHONE  ,
                        _EMAIL ,
                        _URL ,
                        _TITLE ,
                        _DESCRIPTION ,
                        _MODIFIED ,
                        _CREATED ,
                        _ISSUED ,
                        _URI ,
                        URIRef,
                        BNode,
                        Literal
    )
except Exception as e:
    raise ValueError("Erreur lors de l'import de variables ou de fonctions")





########################################### Functions #########################################
# BBOX
# > dct:spatial [-> dct:Location] / dcat:bbox
def _set_bbox(self, graph, _dataset_dict, _dataset_ref):
    bbox = self._get_dataset_value(_dataset_dict, 'bbox')
    if not bbox:
        return 
    g=graph
    qa=BNode()
    g.add((qa, RDF.type, DCT.Location))
    g.add((_dataset_ref, DCT.spatial, qa))
    g.add((qa, DCT.bbox, Literal(bbox)))


# SPATIAL_COVERAGE [{}]
# > dct:spatial -> dct:Location
    
def _set_spatial_coverage(self, graph, _dataset_dict, _dataset_ref):
    spatial_coverage = self._get_dataset_value(_dataset_dict, 'spatial_coverage')
    if not spatial_coverage:
        return
    
    g=graph
    for s_c in spatial_coverage:
        
        uri=URIRef(s_c.get(_URI,None))
        if uri:
            sc_node=URIRef(uri.rstrip('/'))
        else:
            sc_node=BNode()
            
        g.add((sc_node, RDF.type, DCT.Location))
        g.add((_dataset_ref, DCT.spatial, sc_node))

        if in_scheme:=s_c.get("in_scheme",None):
            g.add((sc_node, SKOS.inScheme, Literal(in_scheme)))
            
        # IDENTIFIER
        # > dct:identifier
        if identifier:=s_c.get("identifier",None):
            g.add((sc_node, DCT.identifier, Literal(identifier)))
        
        # LABEL {*}
        # > skos:prefLabel
        # [+ GeoDCAT-AP]
        if labels:=s_c.get("label",None): # {*}
            for lang in labels:
                g.add((sc_node, SKOS.prefLabel, Literal(labels[lang],lang=lang)))
            

# PROVENANCE [{*}]
# > dct:provenance [-> dct:ProvenanceStatement] / rdfs:label
# [+ DCAT-AP]
def _set_provenance(self, graph, _dataset_dict, _dataset_ref):
    provenance_dict = self._get_dataset_value(_dataset_dict, 'provenance')
    if not provenance_dict:
        return
    g=graph
    _clean_lagacy_nodes(g,_dataset_ref,DCT.provenance)    
 
    for _provenance in provenance_dict:
        node=BNode()
        g.add((node, RDF.type, DCT.ProvenanceStatement))
        g.add((_dataset_ref, DCT.provenance, node))
        
        for lang in provenance_dict:
            g.add((node,  RDFS.label, Literal(provenance_dict[lang],lang=lang)))



def _set_category(self, graph, _dataset_dict, _dataset_ref):
    category_dict = self._get_dataset_value(_dataset_dict, 'category')
    if not category_dict:
        return
    g=graph
    for theme in category_dict:
        if uri:=theme.get("uri",None):
            qa=URIRef(uri)
            g.add((_dataset_ref, DCAT.theme, qa))

def _set_theme(self, graph, _dataset_dict, _dataset_ref):
    theme_dict = self._get_dataset_value(_dataset_dict, 'theme')
    if not theme_dict:
        return
    g=graph

    for theme in theme_dict:
        if uri:=theme.get("uri",None):
            qa=URIRef(uri.rstrip('/'))
            g.add((_dataset_ref, DCAT.theme, qa))



# > prov:qualifiedAttribution -> prov:Attribution
def _set_qualifiedAttribution(self, graph, _dataset_dict, _dataset_ref):
    qualified_attribution_dict = self._get_dataset_value(_dataset_dict, 'qualified_attribution')
    if not qualified_attribution_dict:
        return 
    g=graph
    for q_a in qualified_attribution_dict:
        uri=q_a.get(_URI,None)
        if uri:
            qa=URIRef(uri.rstrip('/'))
        else:
            qa=BNode()
            
        g.add((qa, RDF.type, PROV.Attribution))
        g.add((_dataset_ref, PROV.qualifiedAttribution, qa))

        for qualifiedAtt in qualified_attribution_dict:
            # HAD_ROLE [{}]
            # > dcat:hadRole
            if had_role:=qualifiedAtt.get("had_role",None):
                for role in had_role:
                    if uri:=role.get("uri",None):
                        g.add((qa, DCAT.hadRole, Literal(uri)))

            for agent_dict in qualifiedAtt.get("agent",[]):
                agent_node=BNode()
                # > prov:agent -> prov:Agent
                g.add((agent_node, RDF.type, PROV.Agent))
                g.add((qa, PROV.agent, agent_node))

                #foaf:givenName
                if names:=agent_dict.get("name",None):
                    for lang in names:
                        g.add((agent_node,  FOAF.givenName, Literal(names[lang],lang=lang)))

                #foaf:mbox 
                if mail:=agent_dict.get("mail",None):
                    g.add((agent_node, FOAF.mbox, Literal(mail)))
                
                #foaf:homePage
                if url:=agent_dict.get("url",None):
                    g.add((agent_node, FOAF.homePage, Literal(url)))


# > foaf:isPrimaryTopicOf -> dcat:CatalogRecord
def _set_primary_topic_of(self, graph, _dataset_dict, _dataset_ref):
    is_primary_topic_of_dict = self._get_dataset_value(_dataset_dict, 'is_primary_topic_of')
    if not is_primary_topic_of_dict:
        return 
    g=graph
    for primary_topic in is_primary_topic_of_dict:
        uri=primary_topic.get(_URI,None)
        if uri:
            topic=URIRef(uri.rstrip('/'))
        else:
            topic=BNode()
        
        g.add((topic, RDF.type, DCAT.CatalogRecord))
        g.add((_dataset_ref, FOAF.isPrimaryTopicOf, topic))
        
        if modified:=primary_topic.get("modified",None):
            
            g.add((topic, DCT.modified, Literal(modified,
                                                  datatype=XSD.dateTime)))

        if identifier:=primary_topic.get("identifier",None):
            g.add((topic, DCT.identifier, Literal(identifier)))
            
        if primary_topic.get("language",None):
            _set_language(self, g, primary_topic, topic)
            
        if primary_topic.get("contact_point",None):
            _set_contact_point(self, g, primary_topic, topic)

        if in_catalog_dict:=primary_topic.get("in_catalog",None):

            in_catalog_node=BNode()
            g.add((in_catalog_node, RDF.type, DCAT.Catalog))
            g.add((topic, DCAT.inCatalog, in_catalog_node))
            
            if title:=in_catalog_dict.get("title",None):
                for lang in title:
                    g.add((in_catalog_node, DCT.title, Literal(title[lang], lang=lang)))
            
            
            if homepage:=in_catalog_dict.get("homepage",None):
                g.add((in_catalog_node, FOAF.homepage, Literal(homepage)))


def _set_version_notes(self, graph, _dataset_dict, _dataset_ref):
    version_notes_list = self._get_dataset_value(_dataset_dict, 'version_notes')
    if not version_notes_list:
        return
    g=graph
    _clean_lagacy_nodes(g,_dataset_ref,ADMS.versionNotes)    
    for lang, notes in version_notes_list.items():
        g.add((_dataset_ref, ADMS.versionNotes, Literal(notes, lang=lang)))

def _set_language(self, graph, _dataset_dict, _dataset_ref):
    g=graph
    _clean_lagacy_nodes(g,_dataset_ref,DCT.language)    
    language_list = self._get_dataset_value(_dataset_dict, 'language')
    if not language_list:
        return
    for lang in language_list:
        if uri:=lang.get("uri",None):
            language=URIRef(uri.rstrip('/'))
            g.add((_dataset_ref, DCT.language, language))



# CONFORMS_TO
# > dct:conformsTo -> dct:Standard        
def _set_conforms_to(self, graph, _dataset_dict, _dataset_ref):
    conforms_to = self._get_dataset_value(_dataset_dict, 'conforms_to')
    if not conforms_to:
        return
    g=graph
    if not isinstance(conforms_to, list) or len (conforms_to) ==0:
        return
    for con_to in conforms_to:
        # URI
        uri=con_to.get(_URI,None)
        if uri:
            conforms_to=URIRef(uri.rstrip('/'))
        else:
            conforms_to=BNode()
        
        g.add((conforms_to, RDF.type, DCT.Standard))
        g.add((_dataset_ref, DCT.conformsTo, conforms_to))
        # TITLE {*}
        # > dct:title
        if title:=con_to.get("title",None):
            for lang in title:
                g.add((conforms_to, DCT.title, Literal(title[lang],lang=lang)))



def _set_crs(self, graph, _dataset_dict, _dataset_ref):
    # CRS []
    # > dct:conformsTo
    g=graph
    _clean_lagacy_nodes(g,_dataset_ref,DCT.conformsTo)    
    crs_list = self._get_dataset_value(_dataset_dict, 'crs')
    if not crs_list:
        return
    for _crs in crs_list:
        if uri:=_crs.get("uri",None):
            _crs_node=URIRef(uri.rstrip('/'))
            g.add((_dataset_ref, DCT.conformsTo, _crs_node))


# ACCESS_RIGHTS [{}]
# > dct:accessRights -> dct:RightsStatement
def _set_access_rights(self, graph, _dataset_dict, _dataset_ref):
    access_rights_dict = self._get_dataset_value(_dataset_dict, 'access_rights')

    if not access_rights_dict:
        return
    g=graph
    _clean_lagacy_nodes(g,_dataset_ref,FOAF.accessRights)    
    for access_right in access_rights_dict:
        uri=access_right.get(_URI)
        if uri:
            access_rights_node=URIRef(uri.rstrip('/'))
        else:
            access_rights_node=BNode()
        
        
        g.add((_dataset_ref, FOAF.accessRights, access_rights_node))
        
        g.add((access_rights_node, RDF.type, DCT.RightsStatement))
        
        if label:=access_right.get('label',None): # {*}
            g.add((access_rights_node, RDFS.label, Literal(label)))

    
def _set_documentation_page(self, graph, _dataset_dict, _dataset_ref):
    pages = self._get_dataset_value(_dataset_dict, "page")
    if not pages:
        return
    g = graph
    if isinstance(pages, list):
        for page in pages:
            uri=page.get(_URI,None)
            if uri:
                page_details=URIRef(uri.rstrip('/'))
            else:
                page_details=BNode()

            g.add((_dataset_ref, FOAF.page, page_details))
            g.add((page_details, RDF.type, FOAF.Document))
            
            if url:=page.get(_URL,None):
                g.add((page_details, DCT.url, Literal(url)))
                
            if title:=page.get(_TITLE,None): #  {*}
                for lang in title:
                    g.add((page_details, DCT.title, Literal(title[lang],lang=lang)))
                
            if description:=page.get(_DESCRIPTION,None): #  {*}
                for lang in description:
                    g.add((page_details, DCT.description, Literal(description[lang],lang=lang)))

            if modified:=page.get(_MODIFIED,None):
                g.add((page_details, DCT.modified, Literal(modified,
                                                  datatype=XSD.dateTime)))

            if created:=page.get(_CREATED,None):
                g.add((page_details, DCT.created,  Literal(created,
                                                  datatype=XSD.dateTime)))

            if issued:=page.get(_ISSUED,None):
                g.add((page_details, DCT.issued, Literal(issued,
                                                  datatype=XSD.dateTime)))
                
    
    
    
def _set_relations_in_series(self, graph, _dataset_dict, _dataset_ref):
    _set_relations(self, graph, _dataset_dict, _dataset_ref,'in_series',DCAT.inSeries)



def _set_relations_series_member(self, graph, _dataset_dict, _dataset_ref):
    _set_relations(self, graph, _dataset_dict, _dataset_ref,'dataset_series',DCAT.seriesMember)



def _set_relations(self, graph, _dataset_dict, _dataset_ref,key,predicate):
    in_series_dict = self._get_dataset_value(_dataset_dict, key)
    if not in_series_dict:
        return 
    g = graph
    for in_serie in in_series_dict:
        identifier=in_serie.get("identifier",None)
        if identifier:
            g.add((_dataset_ref, predicate, URIRef(identifier)))
    
        
def _set_contact_point(self, graph, _dataset_dict, _dataset_ref):
    _contact_point_dict = self._get_dataset_value(_dataset_dict, 'contact_point')
    if not _contact_point_dict:
        return
    g = graph
    #suppression des neouds crées, pour éviter la duplication    
    _clean_lagacy_nodes(g, _dataset_ref, DCAT.contactPoint)
    
    contact_point_details=BNode()
    _contact_point_dict=_contact_point_dict[0]
    g.add((contact_point_details, RDF.type, VCARD.Kind))
    g.add((_dataset_ref, DCAT.contactPoint, contact_point_details))
    
    if affiliation_dict:=_contact_point_dict.get(_AFFILIATION,None):
        try:
            for lang in affiliation_dict:
                g.add((contact_point_details, VCARD.organization, Literal(affiliation_dict[lang], lang=lang)))
        except:
            pass
        
    if name_list:=_contact_point_dict.get(_NAME,None):  
        for lang in name_list:
            g.add((contact_point_details,  VCARD.fn, Literal(name_list[lang], lang=lang)))
        
    if _contact_point_dict.get(_EMAIL,None):
        g.add((contact_point_details, VCARD.hasEmail, Literal(_contact_point_dict[_EMAIL])))

    if _contact_point_dict.get(_PHONE,None):
        g.add((contact_point_details, VCARD.hasTelephone, Literal(_contact_point_dict[_PHONE])))

    if _contact_point_dict.get(_URL,None):
        g.add((contact_point_details, VCARD.hasURL, Literal(_contact_point_dict[_URL])))
    
def _clean_lagacy_nodes(g,dataset_ref,predicate):
    for obj in g.objects(dataset_ref, predicate):
        g.remove((dataset_ref, predicate, obj,))
    
def _set_publisher(self, graph, dataset_dict, dataset_ref):
    """
     <dcat:publisher>
            <foaf:Organization rdf:nodeID="Nc6e19ba1b1ee4c91872d46bdf7dff5e4">
                <foaf:workplaceHomepage>Indisponible</foaf:workplaceHomepage>
                <foaf:phone>Indisponible</foaf:phone>
                <foaf:name>Indisponible</foaf:name>
                <dct:type>Indisponible</dct:type>
                <foaf:memberOf>
                    <foaf:Organization rdf:nodeID="N9877867b76d4471b841e33e5b3c9b460">
                        <foaf:name>Indisponible</foaf:name>
                    </foaf:Organization>
                </foaf:memberOf>
                <foaf:mbox>Indisponible</foaf:mbox>
            </foaf:Organization>
    </dcat:publisher>
    """
    g = graph
    #suppression des neouds crées, pour éviter la duplication    
    _clean_lagacy_nodes(g,dataset_ref,DCT.publisher)
    _add_agent(self,g,dataset_dict,dataset_ref,DCAT.publisher,FOAF.Organization,"publisher")
    
    
    
def _set_creator(self, graph, dataset_dict, dataset_ref):

    """
     <dcat:creator>
            <foaf:Organization rdf:nodeID="N5196aa4ffc0b4e28a4545f142abbe360">
                <foaf:name>Indisponible</foaf:name>
                <foaf:workplaceHomepage>Indisponible</foaf:workplaceHomepage>
                <dct:type>Indisponible</dct:type>
                <foaf:phone>Indisponible</foaf:phone>
                <foaf:memberOf>
                    <foaf:Organization rdf:nodeID="N812c58dad03c4116af8b6628449452c4">
                        <foaf:name>Indisponible</foaf:name>
                    </foaf:Organization>
                </foaf:memberOf>
                <foaf:mbox>Indisponible</foaf:mbox>
            </foaf:Organization>
    </dcat:creator>
    """
    
    g = graph
    #suppression des neouds crées, pour éviter la duplication    
    _clean_lagacy_nodes(g,dataset_ref,DCT.creator)
    _add_agent(self,g,dataset_dict,dataset_ref,DCAT.creator,FOAF.Organization,"creator")
              
                    
              
              
              
def _set_rights_holder(self, graph, dataset_dict, dataset_ref):
    """
    <dcat:rightsHolder>
        <foaf:Organization rdf:nodeID="Neba4f4ca22b44bf3a3fb9aa88f6bbd62">
            <foaf:workplaceHomepage>Indisponible</foaf:workplaceHomepage>
            <foaf:mbox>Indisponible</foaf:mbox>
            <foaf:name>Indisponible</foaf:name>
            <dct:type>Indisponible</dct:type>
            <foaf:memberOf>
                <foaf:Organization rdf:nodeID="N0dc31a8843774366824482011dc80681">
                    <foaf:name>Indisponible</foaf:name>
                </foaf:Organization>
            </foaf:memberOf>
            <foaf:phone>Indisponible</foaf:phone>
        </foaf:Organization>
    </dcat:rightsHolder>
    """
    g = graph
    #suppression des neouds crées, pour éviter la duplication    
    _clean_lagacy_nodes(g,dataset_ref,DCT.rightsHolder)
    _add_agent(self,g,dataset_dict,dataset_ref,DCAT.rightsHolder,FOAF.Organization,"rights_holder")
    
    
    
def _add_agent(self,g,_dataset_dict,_dataset_ref,predicate,node_type,key):
    _agent_dict = self._get_dataset_value(_dataset_dict, key)
    if not _agent_dict:
        return
    for publisher_dict in _agent_dict:
        publisher_details=BNode()
        g.add((publisher_details, RDF.type, node_type))
        g.add((_dataset_ref, predicate, publisher_details))
        
        if affiliation_dict:=publisher_dict.get(_AFFILIATION,None): 
            affiliation = BNode()
            g.add((affiliation, RDF.type, ORG.Organization))
            g.add((publisher_details, ORG.memberOf, affiliation))

            for lang in affiliation_dict:
                g.add((affiliation,  FOAF.name, Literal(affiliation_dict[lang], lang=lang)))
            
        if name:=publisher_dict.get(_NAME,None): 
            for lang in name:
                g.add((publisher_details,  FOAF.name, Literal(name[lang], lang=lang)))

        if publisher_dict.get(_EMAIL,None):
            g.add((publisher_details, FOAF.mbox, Literal(publisher_dict[_EMAIL]))) 
            
        if publisher_dict.get(_TYPE,None):
            g.add((publisher_details, DCT.type, Literal(publisher_dict[_TYPE]))) 
            
        if publisher_dict.get(_PHONE,None):
            g.add((publisher_details, FOAF.phone, Literal(publisher_dict[_PHONE]))) 
            
        if publisher_dict.get(_URL,None):
            g.add((publisher_details, FOAF.workplaceHomepage, Literal(publisher_dict[_URL])))
            
            
                
def _set_temporal_coverage(self, graph, dataset_dict, dataset_ref):
    """
    <dc:temporal>
      <dc:PeriodOfTime>
        <dc:endDate rdf:datatype="http://www.w3.org/2001/XMLSchema#date">2020-12-31T00:00:00.000Z</dc:endDate>
        <dc:startDate rdf:datatype="http://www.w3.org/2001/XMLSchema#date">2005-01-01T00:00:00.000Z</dc:startDate>
      </dc:PeriodOfTime>
    </dc:temporal>
    """
    
    g = graph
    _clean_lagacy_nodes(g,dataset_ref,DCT.temporal)

    temporals = self._get_dataset_value(dataset_dict, 'temporal')
    try:
        start = temporals[0].get('start_date')
        end = temporals[0].get('end_date')
    except (IndexError, KeyError, TypeError):
        # do not add temporals if there are none
        return
    
    temporal_extent = BNode()
    g.add((temporal_extent, RDF.type, DCT.PeriodOfTime))
    _added = False
    if start:
        _added = True
        self._add_date_triple(temporal_extent, DCAT.startDate, start)
    if end:
        _added = True
        self._add_date_triple(temporal_extent, DCAT.endDate, end)
    if _added:
        g.add((dataset_ref, DCT.temporal, temporal_extent))