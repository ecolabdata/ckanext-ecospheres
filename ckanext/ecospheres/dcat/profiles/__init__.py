
import logging
import datetime
import re

from rdflib import Literal, BNode
from rdflib.util import from_n3
from rdflib.namespace import Namespace

import ckan.plugins.toolkit as toolkit
from ckanext.dcat.profiles import RDFProfile, CleanedURIRef

from ckanext.ecospheres.helpers import ecospheres_get_package_uri

from .dataset.parse_dataset import parse_dataset as _parse_dataset
from .graph.graph_from_catalog import graph_from_catalog as _graph_from_catalog

logger = logging.getLogger(__name__)

ADMS = Namespace('http://www.w3.org/ns/adms#')
CNT = Namespace('http://www.w3.org/2011/content#')
DCAT = Namespace('http://www.w3.org/ns/dcat#')
DCATAP = Namespace('http://data.europa.eu/r5r/')
DCT = Namespace('http://purl.org/dc/terms/')
DCTYPE = Namespace('http://purl.org/dc/dcmitype/')
DQV = Namespace('http://www.w3.org/ns/dqv#')
FOAF = Namespace('http://xmlns.com/foaf/0.1/')
GEODCAT = Namespace('http://data.europa.eu/930/')
GSP = Namespace('http://www.opengis.net/ont/geosparql#')
LOCN = Namespace('http://www.w3.org/ns/locn#')
ORG = Namespace('http://www.w3.org/ns/org#')
OWL = Namespace('http://www.w3.org/2002/07/owl#')
PROV = Namespace('http://www.w3.org/ns/prov#')
RDF = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
RDFS = Namespace('http://www.w3.org/2000/01/rdf-schema#')
SDO = Namespace('http://schema.org/')
SH = Namespace('http://www.w3.org/ns/shacl#')
SKOS = Namespace('http://www.w3.org/2004/02/skos/core#')
VCARD = Namespace('http://www.w3.org/2006/vcard/ns#')
XSD = Namespace('http://www.w3.org/2001/XMLSchema#')

NAMESPACES = {
    'adms': ADMS,
    'cnt': CNT,
    'dcat': DCAT,
    'dcatap': DCATAP,
    'dct': DCT,
    'dctype': DCTYPE,
    'dqv': DQV,
    'foaf': FOAF,
    'geodcat': GEODCAT,
    'gsp': GSP,
    'locn': LOCN,
    'org': ORG,
    'owl': OWL,
    'prov': PROV,
    'rdf': RDF,
    'rdfs': RDFS,
    'sdo': SDO,
    'sh': SH,
    'skos': SKOS,
    'vcard': VCARD,
    'xsd': XSD
    }

def dataset_schema():
    '''Return the schema for datasets' metadata.'''
    return toolkit.get_action('scheming_dataset_schema_show')(
        None, {'type': 'dataset'}
    )

def clean_empty_data(data):
    '''Recursively delete all keys without meaningful value.'''
    if isinstance(data, str):
        return not bool(data)
    elif isinstance(data, dict):
        to_delete = []
        for key, value in data.copy().items():
            if clean_empty_data(value):
                to_delete.append(key) 
        for key in to_delete:
            del data[key]
        return not bool(data)
    elif isinstance(data, list):
        to_delete = []
        for elem in data:
            if clean_empty_data(elem):
                to_delete.append(elem)
        for elem in to_delete:
            data.remove(elem)
        return not bool(data)
    else:
        return data is None

class WiserLiteral(Literal):
    '''Extend Literal to choose wisely the datatype argument.
    
    At this point, the constructor simply allow switching between
    the types of literal values ``xsd:date`` and ``xsd:dateTime``,
    and between ``gsp:wktLiteral`` and ``gsp:gmlLiteral``.

    '''
    def __new__(cls, value, datatype=None, lang=None):
        # TODO: ajouter de la validation selon le type. [LL-2023.03.31]

        if datatype in (XSD.date, XSD.dateTime):
            if isinstance(value, datetime.date):
                return super().__new__(cls, value, datatype=XSD.date)
            if isinstance(value, datetime.datetime):
                return super().__new__(cls, value, datatype=XSD.dateTime)
            if isinstance(value, str):
                if re.match(
                    '^(?:[1-9][0-9]{3}|0[0-9]{3})'
                    '[-](?:0[1-9]|1[0-2])'
                    '[-](?:0[1-9]|[12][0-9]|3[01])$',
                    value
                ):
                    return super().__new__(cls, value, datatype=XSD.date)
                if re.match(
                    '^(?:[1-9][0-9]{3}|0[0-9]{3})'
                    '[-](?:0[1-9]|1[0-2])'
                    '[-](?:0[1-9]|[12][0-9]|3[01])'
                    r'(?:[T\s](([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]|(24:00:00)))?',
                    value
                ):
                    return super().__new__(cls, value, datatype=XSD.dateTime)
        
        if datatype in (GSP.wktLiteral, GSP.gmlLiteral):
            # very basic way to recognize GML formatting
            if '<gml' in value:
                return super().__new__(cls, value, datatype=GSP.gmlLiteral)
            else:
                return super().__new__(cls, value, datatype=GSP.wktLiteral)

        return super().__new__(cls, value, datatype=datatype, lang=lang)

class EcospheresDCATAPProfile(RDFProfile):

    def parse_dataset(self, dataset_dict, dataset_ref):
        return _parse_dataset(self, dataset_dict, dataset_ref)
        # TODO: à réécrire [LL-2023-03-03]
    
    def graph_from_catalog(self, catalog_dict, catalog_ref):
        return  _graph_from_catalog(self, catalog_dict, catalog_ref)
        # TODO: à réécrire [LL-2023-03-03]

    def graph_from_dataset(self, dataset_dict, dataset_ref):

        dataset_dict = dataset_dict.copy()
        if clean_empty_data(dataset_dict):
            return

        for prefix, namespace in NAMESPACES.items():
            self.g.namespace_manager.bind(
                prefix, namespace, override=True, replace=True
            )
        
        schema = dataset_schema()
        if dataset_ref_str := dataset_dict.get('uri'):
            dataset_ref = CleanedURIRef(dataset_ref_str)
        else:
            logger.debug('< {dataset_ref} > Skipped dataset without URI')
            return
        self.g.add((dataset_ref, RDF.type, DCAT.Dataset))

        # champs décrivant le jeu de données
        self._graph_from_dataset_and_schema(
            dataset_dict,
            schema.get('dataset_fields'),
            dataset_ref,
            dataset_ref
        )

        # champs décrivant les ressources
        resources = dataset_dict.get('resources')
        if resources:
            for resource_dict in resources:
                node = BNode()

                # récupération de l'URI de la ressource,
                # s'il y en avait un
                if resource_uri_str := resource_dict.get('uri'):
                    node = CleanedURIRef(resource_uri_str)
                
                self._graph_from_dataset_and_schema(
                    resource_dict,
                    schema.get('resource_fields'),
                    node,
                    dataset_ref
                )
                if (node, None, None) in self.g:
                    self.g.add((dataset_ref, DCAT.distribution, node))
                    self.g.add((node, RDF.type, DCAT.Distribution))
    
    def _read_rdf_path(self, rdf_path, subject):
        if len(rdf_path) == 2:
            return (
                subject,
                from_n3(rdf_path[0], nsm=self.g.namespace_manager),
                from_n3(rdf_path[1], nsm=self.g.namespace_manager)
            )
        else:
            node = BNode()
            property = from_n3(rdf_path[0], nsm=self.g.namespace_manager)
            self.g.add((subject, property, node))
            rdftype = from_n3(rdf_path[1], nsm=self.g.namespace_manager)
            self.g.add((node, RDF.type, rdftype))
            return self._read_rdf_path(rdf_path[2:], node)

    def _graph_from_dataset_and_schema(
        self, fields_data, fields_schema, subject, dataset_ref
    ):
        if not fields_data:
            logger.debug(
                f'< {dataset_ref} > Missing data for < {subject} >'
            )
            return
        if not fields_schema:
            logger.debug(
                f'< {dataset_ref} > Missing schema fragment for < {subject} >'
            )
            return
        if not isinstance(fields_data, dict):
            logger.debug(
                f'< {dataset_ref} > Ill-formed data '
                'skipped during serialization'
                )
            return
        if not isinstance(fields_schema, list):
            logger.debug(
                f'< {dataset_ref} > Data for ill-formed '
                'schema skipped during serialization'
                )
            return

        for field, value in fields_data.items():

            field_subject = subject

            if (
                field in ('uri', 'resources')
                or value in (None, '', [], {})
            ):
                continue

            # recherche de la description du champ
            for field_dict in fields_schema:
                if field_dict.get('field_name') == field:
                    field_schema = field_dict
                    break
            else:
                logger.debug(
                    f'< {dataset_ref} > Unknown field "{field}" '
                    'skipped during serialization'
                )
                continue
            
            value_type = field_schema.get('value_type')

            # création des parents implicites
            rdf_path = field_schema.get('rdf_path')
            if not rdf_path:
                continue
            field_subject, property, rdftype = self._read_rdf_path(
                rdf_path, field_subject
            )

            # cas particuliers
            if property == DCAT.inSeries and isinstance(value, list):
                for parent in value:
                    parent_uri = ecospheres_get_package_uri(parent)
                    if parent_uri:
                        self.g.add((field_subject, property, CleanedURIRef(parent_uri)))
            elif property == DCAT.seriesMember and value and isinstance(value, list):
                for child in value:
                    child_uri = ecospheres_get_package_uri(child)
                    if child_uri:
                        self.g.add((field_subject, property, CleanedURIRef(child_uri)))
                self.g.add((field_subject, RDF.type, DCAT.DatasetSeries))

            # noeud anonyme et noeud anonyme/URI
            elif (
                value_type in ('node or uri', 'node')
                and isinstance(value, list)
                and value
                and isinstance(value[0], dict)
            ):
                subfields_schema = field_schema.get('repeating_subfields')
                if not subfields_schema:
                    continue
                for subfields_data in value:
                    node = BNode()
                    for subkey, subvalue in subfields_data.items():
                        if subkey == 'uri' and subvalue:
                            node = CleanedURIRef(subvalue)
                    self.g.add((field_subject, property, node))
                    if rdftype != SKOS.Concept:
                        l_before = len(self.g)
                        self._graph_from_dataset_and_schema(
                            subfields_data, subfields_schema, node, dataset_ref
                        )
                        if len(self.g) > l_before:
                            self.g.add((node, RDF.type, rdftype))

            # URI
            elif value_type == 'uri':
                if isinstance(value, str):
                    self.g.add((field_subject, property, CleanedURIRef(value)))
                elif isinstance(value, list):
                    for v in value:
                        if isinstance(v, str):
                            self.g.add((field_subject, property, CleanedURIRef(v)))
                        elif isinstance(v, dict):
                            uri = v.get('uri')
                            if uri and isinstance(uri, str):
                                self.g.add((field_subject, property, CleanedURIRef(uri)))
            
            # valeur littérale
            elif value_type == 'literal':
                if field_schema.get('translatable_values'):
                    if not isinstance(value, dict):
                        return
                    for language, e in value.items():
                        if not isinstance(e, list):
                            e = [e]
                    for v in e:
                        if v:
                            self.g.add(
                                (field_subject, property, WiserLiteral(v, lang=language))
                            )
                elif isinstance(value, list):
                    for v in value:
                        lit = WiserLiteral(v, datatype=rdftype)
                        # # RDFLib 6.3.2
                        # if lit.ill_typed:
                        #     continue
                        self.g.add((field_subject, property, lit))
                else:
                    lit = WiserLiteral(value, datatype=rdftype)
                    # # RDFLib 6.3.2
                    # if lit.ill_typed:
                    #     continue
                    self.g.add((field_subject, property, lit))

