try: 
    from ckantoolkit import config
    from ckanext.dcat.utils import catalog_uri, dataset_uri, resource_uri
    from rdflib import BNode

    from ..constants import (
            namespaces,
            DCT,
            DCAT,
            OWL,
            RDF,
            FOAF,
            RDFS,
            XSD,
            URIRef,
            Literal
        )
except Exception as e:
    print("Erreur lors de l'importation des librairies")
    
def graph_from_catalog(self, catalog_dict, catalog_ref):
    
    g = self.g
    for prefix, namespace in namespaces.items():
        g.bind(prefix, namespace)

    g.add((catalog_ref, RDF.type, DCAT.Catalog))


    # Replace homepage
    # Try to avoid to have the Catalog URIRef identical to the homepage URI
    g.remove((catalog_ref, FOAF.homepage, URIRef(config.get('ckan.site_url'))))
    g.add((catalog_ref, FOAF.homepage, URIRef(catalog_uri() + '/#')))


    # Basic fields
    items = [
        ('title', DCT.title, config.get('ckan.site_title'), Literal),
        ('description', DCT.description, config.get('ckan.site_description'), Literal),
        ('language', DCT.language, config.get('ckan.locale_default', 'en'), URIRef),
    ]
    for item in items:
        key, predicate, fallback, _type = item
        if catalog_dict:
            value = catalog_dict.get(key, fallback)
        else:
            value = fallback
        if value:
            g.add((catalog_ref, predicate, _type(value)))
    
    # issued date
    issued = config.get('ckanext.dcatfranch_config.catalog_issued', '2022-10-01')
    if issued:
        self._add_date_triple(catalog_ref, DCT.issued, issued)

    # modified date
    modified = self._last_catalog_modification()
    if modified:
        self._add_date_triple(catalog_ref, DCT.modified, modified)



    # publisher
    pub_agent_name = config.get('ckanext.dcatfrench_config.publisher_name', 'unknown')
    pub_agent_mail = config.get('ckanext.dcatfrench_config.publisher_mail', 'unknown')
    pub_agent_phone = config.get('ckanext.dcatfrench_config.publisher_phone', 'unknown')
    pub_agent_url = config.get('ckanext.dcatfrench_config.publisher_url', 'unknown')

    publisher_catalog_details=BNode()
    g.add((publisher_catalog_details, RDF.type, FOAF.Organization))
    g.add((catalog_ref, DCAT.publisher, publisher_catalog_details))
    g.add((publisher_catalog_details,  FOAF.name, Literal(pub_agent_name)))
    g.add((publisher_catalog_details, FOAF.mbox, Literal(pub_agent_mail)) )
    g.add((publisher_catalog_details, FOAF.phone, Literal(pub_agent_phone))) 
    g.add((publisher_catalog_details, FOAF.workplaceHomepage, Literal(pub_agent_url)))





