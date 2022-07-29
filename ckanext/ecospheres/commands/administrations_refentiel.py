from pathlib import Path
from os.path import exists
import json
from ckanext.ecospheres.models.type_admins import Typeadmins
from  ckanext.ecospheres.commands.utils import _get_file_from_disk



FILENAME="adminstrations_type_referentiel_codage.json"
def _get_data_from_file(filename=None):
    return json.loads(_get_file_from_disk(filename))

def load_data_admin():
    Typeadmins.delete_all()
    
    type_admins=_get_data_from_file(FILENAME)

    for codage in type_admins:
        Typeadmins.from_data(
                            code=codage,
                            label=type_admins[codage]
                            )


