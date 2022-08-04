

import rdflib
import rdflib.parser
from rdflib import URIRef, BNode, Literal
from rdflib.namespace import Namespace, RDFS, RDF,XSD, SKOS
from ckanext.dcat.utils import catalog_uri, dataset_uri, url_to_rdflib_format, DCAT_EXPOSE_SUBCATALOGS
from  ckanext.ecospheres.commands.utils import _get_file_from_disk
from  ckanext.ecospheres.models.themes import Themes,Subthemes


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

PATH_THEMES="/srv/app/src_extensions/ckanext-ecospheres/vocabularies/"
FILENAME_THEME="themes_jsonld.json"





def load_themes_from_file_to_db(filename=None):
    if not filename:
        filename="themes_jsonld.json"
    file=_get_file_from_disk(filename)
    parser=RDFThemesCGDDparser()
    parser.parse(file,_format="jsonld")
    themes_parsed=parser._get_themes_as_list()
    Themes.delete_all()


    #TODO
    #conversion des coordonnées en GeoJSON et WKT (et/ou GML pour les exports DCAT)

    for theme in themes_parsed:
        prefLabel=theme.get("prefLabel",None)
        uri=theme.get("uri",None)
        Themes.from_data(
            uri=theme.get("uri",None),
            pref_label=theme.get("prefLabel",None),
            alt_label=theme.get("altLabel",None),
            change_note=theme.get("changeNote",None),
            definition=theme.get("definition",None),
        )
        
        if subthemes_list:=theme.get("narrower",None):
            for subtheme in subthemes_list:
                Subthemes.from_data(
                    pref_label=subtheme.get("prefLabel",None),
                    uri=subtheme.get("uri",None),
                    broader=subtheme.get("broader",None),
                    definition=subtheme.get("definition",None),
                    alt_label=subtheme.get("altLabel",None),
                    regexp=subtheme.get("regexp",None),
                    theme_id=theme.get("prefLabel",None)
                )



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
       
        return themes

            