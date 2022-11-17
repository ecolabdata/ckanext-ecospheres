
from rdflib.namespace import Namespace, RDFS, RDF,XSD, SKOS
from rdflib import URIRef, BNode, Literal


_IS_PART_OF='isPartOf'
_HAS_PART='series_member'
FREQ_BASE_URI = 'http://publications.europa.eu/resource/authority/frequency/'
REGEX_PATTERN_THEME=r'.*data\.statistiques\.developpement\-durable\.gouv.*'



DCT = Namespace("http://purl.org/dc/terms/")
DCAT = Namespace("http://www.w3.org/ns/dcat#")
VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")
SCHEMA = Namespace('http://schema.org/')
ADMS = Namespace("http://www.w3.org/ns/adms#")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
TIME = Namespace('http://www.w3.org/2006/time')
LOCN = Namespace('http://www.w3.org/ns/locn#')
GSP = Namespace('http://www.opengis.net/ont/geosparql#')
OWL = Namespace('http://www.w3.org/2002/07/owl#')
SPDX = Namespace('http://spdx.org/rdf/terms#')
XML = Namespace('http://www.w3.org/2001/XMLSchema')
PROV = Namespace("http://www.w3.org/ns/prov#")
NS = Namespace("http://example.com/vocab#")
ORG=Namespace("http://www.w3.org/ns/org#")
namespaces = {
    'dct': DCT,
    'dcat': DCAT,
    'adms': ADMS,
    'vcard': VCARD,
    'foaf': FOAF,
    'schema': SCHEMA,
    'time': TIME,
    'skos': SKOS,
    'locn': LOCN,
    'gsp': GSP,
    'owl': OWL,
    'xml': XML,
    'prov':PROV,
    'org':ORG
}


FREQ_BASE_URI = 'http://publications.europa.eu/resource/authority/frequency/'
REGEX_PATTERN_THEME=r'.*data\.statistiques\.developpement\-durable\.gouv.*'
_TYPE="type"
_NAME="name"
_AFFILIATION="affiliation"
_PHONE="phone"
_EMAIL="email"
_URL="url"
_TITLE="title"
_DESCRIPTION="description"
_MODIFIED="modified"
_CREATED="created"
_ISSUED="issued"
_URI="uri"

_IS_PART_OF='isPartOf'
_HAS_PART='hasPart'
