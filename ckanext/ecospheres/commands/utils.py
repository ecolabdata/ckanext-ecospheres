from os.path import exists
from pathlib import Path
import json


def _get_file_from_disk(filename=None):
    PATH_THEMES="/srv/app/src_extensions/ckanext-ecospheres/vocabularies/"
    try:
        p = Path(PATH_THEMES)
        path = p / filename
        file_exists = exists(path)
        if not file_exists:
            return None
        with open(path, 'r') as f:
            return f.read()
    except Exception as e:
        print(e)
        raise Exception("Erreur lors de la lecture du fichier json des themes")



