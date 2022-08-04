from ckanext.ecospheres.registre_loader.loader import Loader
from ckanext.ecospheres.models.territories import Territories
from ckanext.ecospheres.models.themes import Themes



def test_load():
    loader=Loader()
    territoires= loader.territoires
    assert territoires
    code_region="D91"
    territoire_91=loader.get_territorie_by_code_region(code_region)
    assert territoire_91
    themes= loader.themes

