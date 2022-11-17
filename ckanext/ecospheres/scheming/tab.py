
from builtins import object
from yaml import load, Loader
from pathlib import Path
from ckanext.ecospheres.scheming import __path__ as scheming_path
import logging

def _get_schema(schema_name):
    path = Path(scheming_path[0]) / f'{schema_name}.yaml'
    with open(path, 'r') as src:
        return load(src.read(), Loader)


def get_fields_by_tab():
    try:
        tab_dict={}
        schema = _get_schema('ecospheres_dataset_schema')
        if dataset_fields:=schema.get('dataset_fields',None):
            for field_dict in dataset_fields:
                if tab:=field_dict.get('tab',None):
                    for lang in tab.keys():
                        tab_dict.setdefault(lang,{})
                        tab_dict[lang].setdefault(tab.get(lang),[])
                        tab_dict[lang][tab.get(lang)].append(field_dict.get('field_name',None))
        return tab_dict
    except Exception as e:
        logging.error(f"Erreur lors du parsing du schema",str(e))        
        return {}