
import ckan.plugins.toolkit as toolkit

from ckanext.ecospheres.spatial.base import EcospheresDatasetDict

def build_dataset_dict_from_schema(type='dataset'):
    """Construit un dictionnaire de jeu de données d'après le schéma YAML.
    
    Parameters
    ----------
    type : str, default 'dataset'
        Le type de jeu de données. Il s'agit de la valeur de la
        propriété ``dataset_type`` du fichier YAML.

    Returns
    -------
    ckanext.ecospheres.spatial.base.EcospheresDatasetDict
        Un dictionnaire de jeu de données vierge, qui
        peut notamment remplacer le ``package_dict`` par
        défaut produit par un moissonneur. 

    """
    dataset_schema = toolkit.get_action('scheming_dataset_schema_show')(None, {'type': type})
    return EcospheresDatasetDict(dataset_schema)




