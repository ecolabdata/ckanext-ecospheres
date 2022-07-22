

import rdflib
import rdflib.parser
from rdflib import URIRef, BNode, Literal
from rdflib.namespace import Namespace, RDFS, RDF,XSD, SKOS
from ckanext.dcat.utils import catalog_uri, dataset_uri, url_to_rdflib_format, DCAT_EXPOSE_SUBCATALOGS
import xml
from ckanext.dcat.exceptions import RDFProfileException, RDFParserException
from ckanext.dcat.profiles import RDFProfile
from os.path import exists
from pathlib import Path
import os 
import json


ECOSPHERES = Namespace('http://registre/ecospheres/')
THEMES = Namespace('http://registre/ecospheres/themes-ecospheres/')
ESPSYNTAX = Namespace('http://registre/ecospheres/syntax#')

PATH_THEMES="/srv/app/src_extensions"
FILENAME_THEME="ref_themes.json"
class RDFThemesCGDDparser(RDFProfile):
    def __init__(self):
        self.g = rdflib.ConjunctiveGraph()
    
    def parse(self, data, _format=None):
        _format = url_to_rdflib_format(_format)
        if not _format or _format == 'pretty-xml':
            _format = 'xml'

        try:
            self.g.parse(data=data, format=_format)
        except (SyntaxError, xml.sax.SAXParseException,
                rdflib.plugin.PluginException, TypeError) as e:

            raise RDFParserException(e)



    def _themes(self):
        for theme in self.g.subjects(RDF.type, SKOS.Concept):
            yield theme
    
    def _get_parent_theme_dict(self,theme):
        is_parent=self._object_value_list( theme, SKOS.narrower)
        if not is_parent:
            return
        return self._get_theme_as_dict(theme)

    def _get_themes_children(self,parent_themes):
        for _theme in parent_themes:
            if themes_child:=_theme.get("narrower",None):
                print(_theme)
                # for child in themes_child:

                    # print(self._get_theme_as_dict(child))




    def _get_theme_as_dict(self,theme):
        theme_dict={}
        if not self._object_value_list( theme, SKOS.narrower):
            return
        for key,_predicate in (
                ("prefLabel",SKOS.prefLabel) ,
                ("broader",SKOS.broader) ,
                # ("exactMatch",SKOS.exactMatch) ,
                ("narrower",SKOS.narrower ) ,
                ("altLabel",SKOS.altLabel ) ,
                ("regexp",ESPSYNTAX.regexp ) ,
                ("changeNote",SKOS.changeNote ) ,
                ("definition",SKOS.definition ) ,
            ):

            if key in ["narrower"]:
                theme_child_list=[]
                for child in self.g.objects(theme, _predicate):
                    theme_child_dict={}
                    for _key,__predicate in (
                        ("prefLabel",SKOS.prefLabel) ,
                        ("broader",SKOS.broader) ,
                        # ("exactMatch",SKOS.exactMatch) ,
                        ("altLabel",SKOS.altLabel ) ,
                        ("regexp",ESPSYNTAX.regexp ) ,
                        ("definition",SKOS.definition ) ,
                        ("changeNote",SKOS.changeNote ) ,
                    ):
                        if _key in ["regexp","altLabel"]:
                            _value=self._object_value_list( child, __predicate)
                            
                        else:
                            _value=self._object_value( child, __predicate)
                        if _value:
                            theme_child_dict[_key]=_value
                        theme_child_dict['uri']=str(child)

                    theme_child_list.append(theme_child_dict)


                theme_dict[key]=theme_child_list

            elif key =="altLabel":
                value=self._object_value_list( theme, _predicate)
            else:
                value=self._object_value( theme, _predicate)
            if value:
                theme_dict[key]=value
        theme_dict["uri"]=str(theme)
        return theme_dict

        
    def _get_themes_as_list(self):
        themes=list()
        for theme in self._themes():
            if th:=self._get_theme_as_dict(theme):
                themes.append(th)
        themes_dict={
            "themes":themes
        }
        p = Path(PATH_THEMES)
        q = p / FILENAME_THEME
        file_exists = exists(q)
        if not file_exists:
            q.touch(exist_ok=True)
        with open(q, "w") as write_file:
            json.dump(themes_dict, write_file,indent=4)
        return themes

            