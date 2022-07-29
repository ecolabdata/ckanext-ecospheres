import logging
import json
from pathlib import Path
from os.path import exists
from ckanext.ecospheres.models.territories import Territories
from ckanext.ecospheres.models.themes import Themes,Subthemes
from ckanext.ecospheres.models.type_admins import Typeadmins

log = logging.getLogger(__name__)



def setup_db():
    created=setup_territories_models()
    created= setup_themes_models() or created
    created= setup_admin_types_models() or created
    return created

def setup_territories_models():
    created = False
    for t in (Territories.__table__,
              ):
        if not t.exists():
            log.info(f'EcospheresDb: creating table {t.name}')
            t.create()
            created = True
        else:
            log.debug(f'EcospheresDb: table {t.name} already exists')

    return created
    
def setup_themes_models():
    created = False
    for t in (
        Themes.__table__,
        Subthemes.__table__
              ):
        if not t.exists():
            log.info(f'EcospheresDb: creating table {t.name}')
            t.create()
            created = True
        else:
            log.debug(f'EcospheresDb: table {t.name} already exists')

    return created

def setup_admin_types_models():
    created = False
    for t in (
        Typeadmins.__table__,
              ):
        if not t.exists():
            log.info(f'EcospheresDb: creating table {t.name}')
            t.create()
            created = True
        else:
            log.debug(f'EcospheresDb: table {t.name} already exists')

    return created
    






