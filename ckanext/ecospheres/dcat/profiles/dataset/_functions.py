import json
from datetime import datetime
import requests as _requests
from rdflib.namespace import Namespace, RDFS, RDF, SKOS
from rdflib import URIRef, BNode
from ckan.lib.i18n import get_locales
from ckan.lib.munge import munge_tag
import re
import unidecode 

from ..constants import (
    ADMS,
    DCAT,
    DCT,
    FOAF,
    LOCN,
    OWL,
    SCHEMA,
    TIME,
    VCARD,
    RDFS,
    PROV,
    NS,
    FREQ_BASE_URI,
    REGEX_PATTERN_THEME,
    _IS_PART_OF,
    _HAS_PART,
    ORG
    )
from ckanext.dcat.profiles import (
    RDFProfile,
)



aggregation_mapping={
    _IS_PART_OF: "in_series",
    _HAS_PART: "serie_datasets",
}

def _strip_uri( value, base_uri):
        return value.replace(base_uri, '')


def get_langs():
    language_priorities = ['en','fr']
    return language_priorities
    
def _check_sous_theme(theme_ecosphere,list_keywords,title) -> (bool,str,str):

    for th_child in theme_ecosphere:

        alt_labels_sous_theme=th_child.get("alt_label",None)
        pref_label_sous_theme=th_child.get("pref_label",None)
        uri_sous_theme=th_child.get("uri",None)


        #on verifie si le pref_label_sous_theme correspend à un mot clé
        for kw in list_keywords:
            if kw.lower() == unidecode.unidecode(pref_label_sous_theme.lower()):
                return  True, pref_label_sous_theme, uri_sous_theme


        #on verifie si le alt_labels_sous_theme correspend à un mot clé 
        if alt_labels_sous_theme:
            for kw in list_keywords:
                for alt_lab in alt_labels_sous_theme:
                    if kw.lower() == unidecode.unidecode(alt_lab.lower()):
                        return  True, pref_label_sous_theme, uri_sous_theme  


        #on essaye de faire matcher les regex avec le titre du dataset 
        if regexp:=th_child.get("regexp",None):
            for _regexp_ in regexp:
                if re.search(_regexp_,title):
                    return  True, pref_label_sous_theme, uri_sous_theme  

    return None,None,None


def _tags_keywords(self, subject, predicate,dataset_dict):
    keywords = {}
    for lang in get_langs():
        keywords[lang] = []

    for keyword_node in self.g.objects(subject, predicate):
        lang = keyword_node.language
        keyword = munge_tag(str(keyword_node))
        keywords.setdefault(lang, []).append(keyword)
    if keywords:
        dataset_dict["keywords"] = keywords

def _object_value_multilang(self, subject, predicate, multilang=False):
    '''
    Given a subject and a predicate, returns the value of the object
    Both subject and predicate must be rdflib URIRef or BNode objects
    If found, the unicode representation is returned, else None
    '''
    default_lang = 'fr'
    lang_dict = {}
    for o in self.g.objects(subject, predicate):
        if multilang and o.language:
            lang_dict[o.language] = str(o)
            lang_dict[o.language] = str(o)
        elif multilang:
            lang_dict[default_lang] =str(o)
        else:
            return str(o)
    if multilang:
        # when translation does not exist, create an empty one
        for lang in get_langs():
            if lang not in lang_dict:
                # TODO: à adapter ( Développé sur DIDO pas de traduction disponible, données originales prises par défaut pour les autres langues)
                lang_dict[lang] = ''

    __values=sum([bool(lang_dict[key]) for key in lang_dict]) == 0
    return None if __values else lang_dict
    

def _version_notes(self, subject, predicate,dataset_dict):
    value=_object_value_multilang(self, subject, predicate, multilang=True)
    if value:
        dataset_dict["version_notes"]= value



def _provenance(self, subject, predicate,dataset_dict):
    for attr in self.g.objects(subject, predicate):
        value=_object_value_multilang(self, attr, RDFS.label, multilang=True)
        if value:
            dataset_dict["provenance"]= value


def _language(self, subject, predicate,dataset_dict):
    _language_list=[]
    for attr in self.g.objects(subject, predicate):
        #TODO: raffiner si possible

        _language_list.append(str(attr))
    if _language_list:
        dataset_dict["language"]= _language_list



def _accrual_periodicity(self, subject, predicate,dataset_dict):
    _accrual_periodicity_list=[]
    for attr in self.g.objects(subject, predicate):
        #TODO: raffiner si possible

        _accrual_periodicity_list.append(str(attr))
    if _accrual_periodicity_list:
        dataset_dict["accrual_periodicity"]= _accrual_periodicity_list


def _conforms_to(self, subject, predicate,dataset_dict):
    _conforms_to_list=[]
    for attr in self.g.objects(subject, predicate):
        _conforms_to_dict={}
        for key,_predicate in (
                        ("title",DCT.title) ,
                    ):
            value=_object_value_multilang(self, attr, _predicate, multilang=True)
            if value:
                _conforms_to_dict[key]=value
        _conforms_to_dict['uri']=str(attr)
        _conforms_to_list.append(_conforms_to_dict)

    if _conforms_to_list:
        dataset_dict['conforms_to']= _conforms_to_list




def _access_rights(self, subject, predicate,dataset_dict):
    access_rights_list=[]
    for attr in self.g.objects(subject, predicate):
        access_rights_dict={}
        for key,_predicate in (
                ("label",RDFS.label) ,
                
            ):
            value=_object_value_multilang(self, attr, _predicate, multilang=True)
            if value:
                access_rights_dict[key]=value
        access_rights_dict['uri']=str(attr)
        access_rights_list.append(access_rights_dict)

    if access_rights_list:
        dataset_dict['access_rights']= access_rights_list



def _spatial_coverage(self, subject, predicate,dataset_dict):
    spatial_coverage_list=[]
    for attr in self.g.objects(subject, predicate):
        spatial_coverage_dict={}
        for key,_predicate in (
                ("label",SKOS.prefLabel) ,
                ("identifier",DCT.identifier) ,
                ("prefLabel",SKOS.inScheme) ,
                
            ):
            if key == "label":
                value=_object_value_multilang(self, attr, _predicate, multilang=True)

            elif key == "prefLabel":
                #TODO: à clarifier
                for _attr in self.g.objects(attr, _predicate):
                    value=self._object_value(_attr, SKOS.prefLabel)
                    if value:
                        pass
            else:
                value=self._object_value(attr, _predicate)
            
            if value:
                spatial_coverage_dict[key]=value
        spatial_coverage_dict["uri"]=str(attr)
        if spatial_coverage_dict:
            spatial_coverage_list.append(spatial_coverage_dict)

    if spatial_coverage_list:
        dataset_dict['spatial_coverage']= spatial_coverage_list



def _is_primary_topic_of(self, subject, predicate,dataset_dict):
    is_primary_topic_of_dict={}
    is_primary_topic_of_list=[]
    for attr in self.g.objects(subject, predicate):
        for key,_predicate in (
                    ("modified",DCT.modified) ,# foaf:phone
                    ("language",DCT.language) ,# foaf:phone
                    ("identifier",DCT.identifier) ,# foaf:phone
                ):
                if key =="language":
                    value=self._object_value_list(attr, _predicate)
                else:
                    value=self._object_value(attr, _predicate)
    
                is_primary_topic_of_dict[key]=value
        is_primary_topic_of_dict["contact_point"]=_contact_points(self, attr, DCAT.contactPoint,dataset_dict,return_value=True)
        is_primary_topic_of_list.append(is_primary_topic_of_dict)

    dataset_dict["is_primary_topic_of"]= is_primary_topic_of_list



def _bbox_spatial(self, subject, predicate,dataset_dict):
    res=None
    for attr in self.g.objects(subject, predicate):
        for key,_predicate in (
                ("bbox",DCAT.bbox) ,# foaf:phone
            ):

            value=self._object_value(attr, _predicate)
            if value:
                res=value

    if res:
        dataset_dict['bbox']=res


def _qualified_attribution(self, subject, predicate,dataset_dict):
    qualified_attri_list=[]
    for attr in self.g.objects(subject, predicate):
        qualified_attri_dict={}
        for key,_predicate in (
                ("had_role",NS.hadRole) ,# foaf:phone
            ):
            value=self._object_value(attr, _predicate)
            if value:
                qualified_attri_dict[key]=value
            
            #agent
            agent_list=[]
            for agent in self.g.objects(attr, PROV.agent):
                agent_dict={}
                for key,__predicate in (
                            ("name",FOAF.givenName) ,# foaf:phone
                            ("mail",FOAF.mbox) ,# foaf:phone
                            ("url",FOAF.homePage) ,# foaf:phone
                            ):
                    value=self._object_value(agent,__predicate)
                    if value:
                        agent_dict[key]=value
                agent_list.append(agent_dict)
            qualified_attri_dict['agent']=agent_list
        qualified_attri_list.append(qualified_attri_dict)
    
    if qualified_attri_list:
        dataset_dict["qualified_attribution"]= qualified_attri_list




def _parse_agent(self, subject, predicate,dataset_dict,keybase=None):
    
        list_publisher=[]
        
        agent_dict ={}
        
        for agent in self.g.objects(subject, predicate):
            if agent is None:
                continue
            
            # non-multilangue
            #TODO: type à clarifier    
            for key,_predicate in (
                ("title",FOAF.title), #dido -> présent
                ("type",DCT.type), 
                ("email",FOAF.mbox) , #foaf:mbox 
                ("phone",FOAF.phone) ,# foaf:phone
                ("url",FOAF.workplaceHomepage), #foaf:workplaceHomepage
            ):
                value=self._object_value(agent, _predicate)
                if value:
                    agent_dict[key] = value
            
            # multilangue    
            for key,_predicate in (
                ("name",FOAF.name), #dido -> présent
                ("comment",RDFS.comment), #dido  -> présent
            ):
                _value=_object_value_multilang(self, agent, _predicate, multilang=True)
                if _value:
                    agent_dict[key] = _value
                    
            # multilangue    
            for key,__predicate in (
                ("affiliation",ORG.memberOf),
            ):
                for attr in self.g.objects(agent, __predicate):
                    value=self._object_value(attr, FOAF.name)
                    if value:
                        agent_dict[key] = value

            list_publisher.append(agent_dict)

        if list_publisher:
            dataset_dict[keybase] =list_publisher


def _contact_points(self, subject, predicate,dataset_dict,return_value=False):
        
        contact_points_dict = dict()
        contact_points_list = []
        for contact_node in self.g.objects(subject, predicate):
            
            for key,_predicate in (
                ("email",VCARD.hasEmail), 
                ("phone",VCARD.hasTelephone) ,
                ("url",VCARD.hasURL), 
            ):
            
                value=self._object_value(contact_node, _predicate)
                if value:
                    contact_points_dict[key] = value
                    
            #multilangue        
            for key,_predicate in (
                ("affiliation",VCARD.organization),
                ("name",VCARD.fn), 
            ):
                _value=_object_value_multilang(self, contact_node, _predicate, multilang=True)
                if _value:
                    contact_points_dict[key] = _value
                    
            
                    
            contact_points_list.append(contact_points_dict)
        if return_value:
            return contact_points_list
        dataset_dict["contact_point"]= contact_points_list
        
    
    
def _get_frequency(self,subject,predicate,dataset_dict,key):
    
    for predicate, key, base_uri in (
            (DCT.accrualPeriodicity, key, FREQ_BASE_URI),
        ):
        valueRef = self._object_value(subject, predicate)
        if valueRef:
            _valueRef = self._object_value(valueRef, SKOS.altLabel)
            value = _strip_uri(valueRef, base_uri)
            return {key:value}
        else:
            return {key:"Indisponible"}
        
        
def _build_genealogie(self,dataset_ref,key,predicate,dataset_dict):
        def __get_object_description(__node ):
            return {	
                "identifier":self._object_value(__node, DCT.identifier),
                "title": self._object_value(__node, DCT.title)
            }
        part_identifier_list=[]
        for node in self.g.objects(dataset_ref, predicate):
            if key ==_HAS_PART:
                dataset_dict[_HAS_PART]=True 
                part_identifier_list.append(__get_object_description(node))
            else:
                dataset_dict[_IS_PART_OF]=True
                part_identifier_list.append(__get_object_description(node))
    
        if part_identifier_list:
            dataset_dict[aggregation_mapping[key]]=part_identifier_list
            
        

def _get_documentation_dict(self,dataset_ref,dataset_dict,predicate):
    documentation_dict_list=[]
    for o in self.g.objects(dataset_ref,predicate):
        doc={}
        for key,_predicate in (
                ("created",DCT.created), 
                ("issued",DCT.issued) ,
                ("modified",DCT.modified), 
                ("title",DCT.title,), 
                ("description",DCT.description), 
                ("url",SCHEMA.url), 

            ):
            if key in ["title","description"]:
                value=_object_value_multilang(self, o,_predicate, multilang=True)
            else:
                value=self._object_value(o,_predicate) 
            
            if value:
                doc[key] = value
        
        doc["uri"]=str(o)
        documentation_dict_list.append(doc)
    if documentation_dict_list:
        dataset_dict["page"]= documentation_dict_list
    
    
def _get_temporal(self, subject, predicate,dataset_dict):
    temporals_list=[]
    
    for temporal_node in self.g.objects(subject, predicate):
        temporals_list.append({
            "end_date": self._object_value(temporal_node, DCT.startDate) or "",
            "start_date":  self._object_value(temporal_node, DCT.endDate) or "",
            })
    dataset_dict['temporal']= temporals_list


def add_tag(tags_list,tags):
    def add(tags_list,tg):
        tags_list.append({
                        "name":tg   
                         }
                        )
    if  isinstance(tags, list):
        for tag in tags:
            add(tags_list,tag)
    if  isinstance(tags, str):
        add(tags_list, tags)
    return tags_list
        