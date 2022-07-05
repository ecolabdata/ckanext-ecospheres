
from ckantoolkit import config
from ckanext.dcat.utils import catalog_uri, dataset_uri, resource_uri

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

def graph_from_catalog(self, catalog_dict, catalog_ref):
    
    g = self.g
    print(catalog_dict)
    print("----------------------------------------------------------------------------------------------------------")
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

    # Dates
    modified = self._last_catalog_modification()
    if modified:
        self._add_date_triple(catalog_ref, DCT.modified, modified)