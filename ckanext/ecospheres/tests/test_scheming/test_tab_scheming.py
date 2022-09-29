
from builtins import object
from yaml import load, Loader
from pathlib import Path
from ckanext.ecospheres.scheming.tab import get_fields_by_tab

def _get_schema(schema_name):
    path = Path(scheming_path[0]) / f'{schema_name}.yaml'
    with open(path, 'r') as src:
        return load(src.read(), Loader)



def get_vocabulairies_for_given_repeating_subfields(data,subfield):

    if repeating_subfields_dict:=data.get("repeating_subfields",None):
        

        subfields_as_dict={
            item["field_name"]: item for item in repeating_subfields_dict
        }

        if field_dict:=subfields_as_dict.get(subfield,None):
            return field_dict.get("vocabularies",None)
    return None

def get_vocabulairies_for_given_fields(data):

    if vocabularies:=data.get("vocabularies",None):
        return vocabularies

        
    return None
def test_get_schema_tab():
    data={
                "field_name":"licenses",
                "vocabularies":[
                            "adms_licence_tdddype"
                        ],
                "label":{
                    "fr":"Licence",
                    "en":"Licence"
                },
                "help_text":"Conditions d'utilisation de la ressource.",
                "value_type":"node or uri",
                "display_snippet":"licence_fr.html",
                "repeating_subfields":[
                    {
                        "field_name":"uri",
                        "label":{
                            "fr":"URL",
                            "en":"URL"
                        },
                        "value_type":"uri",
                        "known_values":"require",
                        "vocabularies":[
                            "eu_licence",
                            "spdx_license"
                        ]
                    },
                    {
                        "field_name":"type",
                        "label":{
                            "fr":"Type",
                            "en":"Type"
                        },
                        "help_text":"Caractéristiques de la licence.",
                        "multiple_values":True,
                        "value_type":"uri",
                        "known_values":"require",
                        "vocabularies":[
                            "adms_licence_type"
                        ]
                    },
                    {
                        "form_snippet":"fluent_text.html",
                        "display_snippet":"fluent_text.html",
                        "error_snippet":"fluent_text.html",
                        "validators":"fluent_text",
                        "output_validators":"fluent_text_output",
                        "field_name":"label",
                        "label":{
                            "fr":"Termes",
                            "en":"Terms"
                        },
                        "help_text":"Termes de la licence.",
                        "preset":"fluent_text",
                        "value_type":"literal",
                        "translatable_values":True
                    }
                ]
                }
    res=get_vocabulairies_for_given_repeating_subfields(data=data,subfield="type")
    print("res: ",res)
    res=get_vocabulairies_for_given_fields(data=data)
    print("res: ",res)