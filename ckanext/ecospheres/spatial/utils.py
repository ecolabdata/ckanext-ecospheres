
import json

import ckan.plugins.toolkit as toolkit

from ckanext.ecospheres.spatial.base import EcospheresDatasetDict


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

