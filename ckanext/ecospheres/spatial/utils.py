
import re, json, requests

import ckan.plugins.toolkit as toolkit

from ckanext.ecospheres.spatial.base import EcospheresDatasetDict

ISO_NAMESPACES = {
           "gts": "http://www.isotc211.org/2005/gts",
           "gml": "http://www.opengis.net/gml",
           "gml32": "http://www.opengis.net/gml/3.2",
           "gmx": "http://www.isotc211.org/2005/gmx",
           "gsr": "http://www.isotc211.org/2005/gsr",
           "gss": "http://www.isotc211.org/2005/gss",
           "gco": "http://www.isotc211.org/2005/gco",
           "gmd": "http://www.isotc211.org/2005/gmd",
           "srv": "http://www.isotc211.org/2005/srv",
           "xlink": "http://www.w3.org/1999/xlink",
           "xsi": "http://www.w3.org/2001/XMLSchema-instance",
        }

def build_dataset_dict_from_schema(type='dataset', main_language=None):
    """Construit un dictionnaire de jeu de données d'après le schéma YAML.
    
    Parameters
    ----------
    type : str, default 'dataset'
        Le type de jeu de données. Il s'agit de la valeur de la
        propriété ``dataset_type`` du fichier YAML.
    main_language : str, optional
        S'il y a lieu, une langue dans laquelle seront supposées
        être rédigées toutes les valeurs traduisibles dont la
        langue n'est pas explicitement spécifiée. On utilisera
        autant que possible un code ISO 639 sur deux caractères,
        et plus généralement le code approprié pour désigner la
        langue en RDF.

    Returns
    -------
    ckanext.ecospheres.spatial.base.EcospheresDatasetDict
        Un dictionnaire de jeu de données vierge, qui
        peut notamment remplacer le ``package_dict`` par
        défaut produit par un moissonneur. 

    """
    dataset_schema = toolkit.get_action('scheming_dataset_schema_show')(None, {'type': type})
    return EcospheresDatasetDict(dataset_schema, main_language=main_language)

def bbox_geojson_from_coordinates(west, east, south, north):
    """Serialize bounding box coordinates as a GeoJSON geometry.

    Coordinates are assumed to use World Geodetic System 1984 as
    geographic coordinate reference system and units of decimal degrees.

    Parameters
    ----------
    west : numeric
        West-bound longitude.
    east : numeric
        East-bound longitude.
    south : numeric
        South-bound latitude.
    north : numeric
        North-bound latitude.
    
    Returns
    -------
    str
        A GeoJSON dump.

    """
    west = float(west)
    east = float(east)
    north = float(north)
    south = float(south)
    geodict = {
        'type': 'Polygon',
        'coordinates': [
            [
                [west, north],
                [west, south],
                [east, south],
                [east, north],
                [west, north]
            ]
        ] 
    }
    return json.dumps(geodict)

def bbox_wkt_from_coordinates(west, east, south, north):
    """Serialize bounding box coordinates as a WKT geometry.

    Coordinates are assumed to use the OGC:CRS84 reference system.

    Parameters
    ----------
    west : numeric
        West-bound longitude.
    east : numeric
        East-bound longitude.
    south : numeric
        South-bound latitude.
    north : numeric
        North-bound latitude.
    
    Returns
    -------
    str
        A WKT literal.

    """
    return (
        'POLYGON(('
        f'{west} {north},'
        f'{west} {south},'
        f'{east} {south},'
        f'{east} {north},'
        f'{west} {north}))'
    )

def is_valid_url(url):
    """Send a get request to the URL and check the response.

    Parameters
    ----------
    url : str
        Some URL.
    
    Returns
    -------
    bool
        ``False`` if the status code of the response
        indicates that some error occurred, else ``True``.

    """
    try:
        response = requests.get(url)
        return response.status_code == requests.codes.ok
    except:
        return False

def build_catalog_page_url(
    catalog_base_url, ids
):
    """Try to generate an URL for the dataset page on source catalog.

    Parameters
    ----------
    catalog_base_url : str
        Base URL for the catalog pages.
    ids : str or list(str) or tuple(str)
        One or more identifiers for the dataset or
        the catalog record.

    Returns
    -------
    str or None
        A valid URL that should be the URL of the 
        dataset page. Generated URLs are tested and will
        only be returned if the GET request didn't fail.

    """
    if isinstance(ids, str):
        ids = [ids]
    if not ids or not catalog_base_url:
        return
    if not any(
        catalog_base_url.endswith(suffix) for suffix in ('/', '#', '=')
    ):
        catalog_base_url = catalog_base_url + '/'
    
    for id in ids:        
        url = catalog_base_url + id
        if is_valid_url(url):
            return url

def build_attributes_page_url(
    attributes_base_url, ids
):
    """Try to generate an URL for the attributes page.

    Parameters
    ----------
    attributes_base_url : str
        Base URL for every attributes pages of the
        catalog.
    ids : str or list(str) or tuple(str)
        One or more identifiers for the dataset or
        the catalog record.
    
    Returns
    -------
    str or None
        A valid URL that should be the URL of the page
        describing the attributes of the dataset.
        Generated URLs are tested and will only be returned
        if the GET request didn't fail.

    """
    if isinstance(ids, str):
        ids = [ids]
    if not ids or not attributes_base_url:
        return
    if not any(
        attributes_base_url.endswith(suffix) for suffix in ('/', '#', '=')
    ):
        attributes_base_url = attributes_base_url + '/'
    
    for id in ids:
        
        if '-jdd-' in id:
            # this is meant for Géo-IDE
            url = attributes_base_url + id.replace('-jdd-', '-ca-jdd-')
            if is_valid_url(url):
                return url
            else:
                return
        
        url = attributes_base_url + id
        if is_valid_url(url):
            return url

def extract_scheme_and_identifier(uri_or_label):
    """Extract the scheme and the significant part of a concept URI.

    The identifier is assumed to be the last part of the
    URI, separated from the scheme by one of ``'#'``, ``':'``
    or ``'/'``. It should be made of word characters, digits,
    underscores and/or ``'-'`` or the function won't recognize
    it.

    Parameters
    ----------
    uri_or_label : str
        Maybe a concept URI, anyway some kind of string.

    Returns
    -------
    tuple
        A two elements tuple. The first one is
        the scheme, the second the identifier.
        If the provided string wasn't an URL or any
        basic kind of URI (separator ``'#'``, ``':'`` or
        ``'/'``), it is return unchanged as an identifier,
        while the scheme element will be ``None``.

    """
    r = re.search(
        r'^(.*)[/#:]([\w-]+?)$', uri_or_label
    )
    if r:
        return (r[1], r[2])
    return (None, uri_or_label)

def getrecordbyid_request(url_csw, record_id):
    """Crée une requête GetRecordById pour envoi en HTTP GET.
    
    Parameters
    ----------
    url_csw : str
        L'URL de base du service CSW du catalogue, sans aucun paramètre.
    record_id : str
        L'identifiant de la fiche de métadonnées sur le catalogue.
        Correspond à la valeur de la balise ``gmd:fileIdentifier``
        des fiches ISO 19139.
    
    Returns
    -------
    str
    
    Notes
    -----
    La requête n'est pas en encodage-pourcent.
    
    """
    url_csw = url_csw.rstrip('?/')
    config = {
        'service' : 'CSW',
        'REQUEST': 'GetRecordById',
        'version': '2.0.2',
        'namespace': 'xmlns:csw=http://www.opengis.net/cat/csw',
        'outputFormat': 'application/xml',
        'outputSchema': 'http://www.isotc211.org/2005/gmd',
        'ElementSetName': 'full',
        'Id': record_id
        }
    data = '&'.join('{}={}'.format(k, v) for k, v in config.items())
    return '{}?{}'.format(url_csw, data)


