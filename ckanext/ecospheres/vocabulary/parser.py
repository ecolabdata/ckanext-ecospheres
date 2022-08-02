import requests, re
from lxml import etree
from rdflib import Graph, URIRef, Literal, SKOS, RDF
from io import BytesIO

EPSG_NAMESPACES = {
       'gml': 'http://www.opengis.net/gml/3.2',
       'epsg': 'urn:x-ogp:spec:schema-xsd:EPSG:2.2:dataset'
    }

def spdx_license_to_skos(url, strict=False):
    """Build a RDF graph using simple SKOS vocabulary from SPDX license register.

    Parameters
    ----------
    url : str
        Base URL of the SPDX register. Should return
        a JSON document listing all licenses, with keys
        ``reference``, ``licenseId`` and ``name``.
    strict : bool, default False
        If ``True``, an exception will be raised if
        necessary information is missing for a license.
        If ``False``, the execution will continue with the
        next license. 

    Returns
    -------
    rdflib.graph.Graph

    """
    response = requests.get(url)
    if response.status_code != requests.codes.ok:
        response.raise_for_status()
    
    json_result = response.json()
    if not 'licenses' in json_result:
        raise ValueError('No licenses list ? Key "licenses" was not found.')
    
    license_graph = Graph()

    for license in json_result['licenses']:
        x_uri = license.get('reference')
        if not x_uri:
            if strict:
                raise ValueError(f'Missing reference for license.')
            else:
                continue
                # TODO: log error
        license_uri = re.sub('[.]html$', '', x_uri)

        x_name = license.get('name')
        if not x_name:
            if strict:
                raise ValueError(f'Missing name for license <{license_uri}>.')
            else:
                continue
                # TODO: log error

        x_identifier = license.get('licenseId')
        if not x_identifier:
            if strict:
                raise ValueError(f'Missing identifier for license <{license_uri}>.')
            else:
                continue
                # TODO: log error

        license_graph.add((URIRef(license_uri), RDF.type, SKOS.Concept))
        license_graph.add((URIRef(license_uri), SKOS.inScheme, URIRef('https://spdx.org/licenses')))
        license_graph.add((URIRef(license_uri), SKOS.prefLabel, Literal(f'{x_identifier} : {x_name}', lang='en')))
    
    return license_graph


def ogc_epsg_to_skos(url, strict=False):
    """Build a RDF graph using simple SKOS vocabulary from OGC's EPSG coordinates reference systems register.

    Execution takes approximatively 2 hours, with around
    7k HTTP requests and parsing of each XML response.

    Parameters
    ----------
    url : str
        Base URL of the EPSG register. Should return
        a XML document listing all coordinates reference
        systems (CRS) URIs.
    strict : bool, default False
        If ``True``, an exception will be raised if the
        XML describing the CRS can't be fetched or parsed
        for any CRS. If ``False``, the execution will
        continue with the next CRS. 

    Returns
    -------
    rdflib.graph.Graph

    """
    response = requests.get(url)
    if response.status_code != requests.codes.ok:
        response.raise_for_status()
    
    main_tree = etree.parse(BytesIO(response.content))
    main_root = main_tree.getroot()

    epsg_graph = Graph()

    for elem in main_root:

        crs_url = elem.text
        response = requests.get(crs_url)
    
        if response.status_code != requests.codes.ok:
            if strict:
                response.raise_for_status()
            else:
                continue
                # TODO: log error

        try:
            crs_tree = etree.parse(BytesIO(response.content))
        except Exception as err:
            if strict:
                raise err
            else:
                continue
                # TODO: log error
        
        crs_root = crs_tree.getroot()
        
        x_name = crs_root.xpath('gml:name/text()', namespaces=EPSG_NAMESPACES)
        if not x_name:
            if strict:
                raise ValueError(f'Missing name for CRS <{crs_url}>.')
            else:
                continue
                # TODO: log error

        x_identifier = crs_root.xpath('gml:identifier/text()', namespaces=EPSG_NAMESPACES)
        if not x_identifier:
            if strict:
                raise ValueError(f'Missing identifier for CRS <{crs_url}>.')
            else:
                continue
                # TODO: log error
        
        x_code_space = crs_root.xpath('gml:identifier/@codeSpace', namespaces=EPSG_NAMESPACES) or 'EPSG'
        # since code space is always EPSG for now, it's assumed to be
        # EPSG as well if missing in the future

        epsg_graph.add((URIRef(crs_url), RDF.type, SKOS.Concept))
        epsg_graph.add((URIRef(crs_url), SKOS.inScheme, URIRef(url)))
        epsg_graph.add((URIRef(crs_url), SKOS.prefLabel, Literal(f'{x_code_space[0]} {x_identifier[0]} : {x_name[0]}')))
        print(crs_url)

    return epsg_graph

