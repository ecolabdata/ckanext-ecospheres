from pathlib import Path
from os.path import exists
import json
from ckanext.ecospheres.models.territories import Territories



def load_data_from_file_to_db():
    Territories.delete_all()

    json_file=__get_file_from_disk()
    types_regions=['régions-métrople', 'départements-métropole', 'outre-mer', 'zones-maritimes']
    for type_region in types_regions:
        for code_region in json_file[type_region].keys():
            region_dict=json_file[type_region][code_region]
            uriUE=region_dict.get("uriUE",None)
            name=region_dict.get("name",None)
            if spatial:=region_dict.get("spatial",None):
                westlimit=spatial.get("westlimit",None)
                southlimit=spatial.get("southlimit",None)
                eastlimit=spatial.get("eastlimit",None)
                northlimit=spatial.get("northlimit",None)
            Territories.from_data(type_region=type_region,
                    name=name or None,
                    codeRegion=code_region or None,
                    uriUE=uriUE or None,
                    westlimit=westlimit or None,
                    southlimit=southlimit or None,
                    eastlimit=eastlimit or None,
                    northlimit=northlimit or None) 

           




#######################################################Fonctions#################################

def __get_file_from_disk(filename=None):
    PATH_THEMES="/srv/app/src_extensions/ckanext-ecospheres/vocabularies/"
    PATH_JSON="territoires.json"
   
    try:
        p = Path(PATH_THEMES)
        path = p /PATH_JSON
        print("path: ",path)
        file_exists = exists(path)

        if not file_exists:
            return None

        with open(path, 'r') as f:
            return json.loads(f.read())

    except Exception as e:
        raise Exception("Erreur lors de la lecture du fichier json des themes")