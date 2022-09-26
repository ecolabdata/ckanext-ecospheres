
from builtins import object
from yaml import load, Loader
from pathlib import Path
from ckanext.ecospheres.scheming.tab import get_fields_by_tab

def _get_schema(schema_name):
    path = Path(scheming_path[0]) / f'{schema_name}.yaml'
    with open(path, 'r') as src:
        return load(src.read(), Loader)



def test_get_schema_tab():
    assert get_fields_by_tab()
