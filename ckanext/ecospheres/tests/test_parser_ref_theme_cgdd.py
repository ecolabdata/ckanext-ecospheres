from ..dcat.profiles.themes_parser.parse_themes import RDFThemesCGDDparser

from pathlib import Path
import json
import os 
def _get_file_contents( file_name):
        path = os.path.join(os.path.dirname(__file__),
                            'files',
                            file_name)
        with open(path, 'r') as f:
            return f.read()

def test_parse_themes():
        file=_get_file_contents("ref_themes.json")
        o=RDFThemesCGDDparser()
        o.parse(file,_format="jsonld")
        o._get_themes_as_list()