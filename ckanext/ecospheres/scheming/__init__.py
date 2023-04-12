
# import ckan.plugins.toolkit as toolkit
import yaml
from pathlib import Path

from ckanext.ecospheres.scheming import __path__ as scheming_path

def dataset_schema():
    '''Return the schema for datasets' metadata.'''
    # return toolkit.get_action('scheming_dataset_schema_show')(
    #     None, {'type': 'dataset'}
    # )
    yaml_path = Path(scheming_path[0]) / 'ecospheres_dataset_schema.yaml'
    if not yaml_path.exists() or not yaml_path.is_file():
        raise FileNotFoundError('missing ecospheres_dataset_schema.yaml file')
    with open(yaml_path, encoding='utf-8') as src:
        return yaml.load(src, yaml.Loader)

DATASET_SCHEMA = dataset_schema()
