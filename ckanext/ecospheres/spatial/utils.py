
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


