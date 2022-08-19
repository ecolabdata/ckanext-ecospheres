"""Vocabulary parsers.

All functions of this module are vocabulary parsers
that may be referenced as such in the ``vocabularies.yaml``
file.

A parser should take two positional arguments:

* The name of the vocabulary for which the
  parser is being used, ie the value of its
  ``name`` property in ``vocabularies.yaml``.
* The URL provided by the ``vocabularies.yaml``
  file, ie the ``url`` property for the vocabulary.
  This is the location to fetch the data from.

Parsers may use optional arguments and they should
allow arbitrary keywords parameters. If the values
for the optional arguments are expected to be provided
by the ``vocabularies.yaml`` file, then their names
and types should match some properties of this file.
If not, then they should not match the name of
any property used in the ``vocabularies.yaml`` file.

All vocabulary parsers should return a
:py:class:`VocabularyParsingResult` object.

Initializating the result should be one of the first
steps for the parser:

    >>> res = VocabularyParsingResult(name)

The :py:mod:`ckanext.ecospheres.vocabulary.parser.utils`
module provides some convenient tools to fetch and parse
raw data.

Any error met during execution should be logged, either
as a "critical failure" or as a "simple error".

Declare a critical failure with the
:py:meth:`VocabularyParsingResult.exit` method:

    >>> res.exit(exception_object)
    >>> return res

As in the exemple above, the (failed) parsing result should
immediately be returned after declaring a critical failure.

Log a simple error with the
:py:meth:`VocabularyParsingResult.log_error` method:

    >>> res.log_error(exception_object)

While critical failures interrupt the parsing and
won't let the receiver access any data, a simple error
will let the receiver access the parsed data and decide
for themselves if it can be used. For exemple, if
required information is missing for one vocabulary item,
this item will be skipped and a simple error is logged
to inform the receiver.

If the error is not captured, the
`ckanext.ecospheres.vocabulary.parser.exceptions` module
provides some :py:class:`Exception` subclasses to build
the needed error objects.

In most case, the main purpose of the parser is to get
URIs and labels for all vocabulary items. They should
be registered in the :py:class:`VocabularyParsingResult`
object using the :py:meth:`VocabularyParsingResult.add_label`
method:

    >>> res.add_label(
    ...     uri='http://spdx.org/licenses/etalab-2.0',
    ...     language='en',
    ...     label='etalab-2.0 : Etalab Open License 2.0'
    ...     )

This method includes some basic validation of the
provided data (and return the validation result as a
:py:class:`ckanext.ecospheres.vocabulary.parser.model.DataValidationResponse`
object). If any anomaly is detected, the row is skipped and a
:py:class:`exceptions.InvalidDataError` is logged.

When alternative labels are available for the vocabulary
items, the should be stored using the same method:

    >>> res.add_label(
    ...     uri='http://spdx.org/licenses/etalab-2.0',
    ...     label='etalab-2.0'
    ...     )

Data is parsed in a normalized database-like structure,
to make sure it can be easily loaded in a database.
This vocabulary cluster is a 
:py:class:`ckanext.ecospheres.vocabulary.parser.model.VocabularyDataCluster`
object that can be accessed through the :py:attr:`VocabularyParsingResult.data`
property of the parsing result. The cluster contains table-like
objects (including the labels' table and the alternative labels' table
mentionned above) and these tables contain row-like objects.

If needed, the parser may add its own custom tables
to the cluster, define contraints on these tables,
validate the data againts this constraints, etc.

Once the parsing is done, the receiver will know if it was
successfull through the :py:attr:`VocabularyParsingResult.status_code`
property.

To re-raise critical parsing failure:

    >>> if not res.status_code:
    ...     raise res.log.pop()

The :py:attr:`VocabularyParsingResult.data` property
gives access to the parsed data. It can be used as a JSON-like
object:

* root keys are the name of the tables. If they do not exist
  in the database, they should be created.
* their values are lists. Each item of the list is a row of the
  table.
* a row is a dictionnary. Keys are the fields' names. All fields
  are present for every row, whether there is a value or not.

"""

import re, json
from lxml import etree
from rdflib import (
    Graph, URIRef, Literal, SKOS, RDF, RDFS,
    DCTERMS as DCT, FOAF
)
from io import BytesIO

from ckanext.ecospheres.vocabulary.parser import utils, exceptions
from ckanext.ecospheres.vocabulary.parser.result import VocabularyParsingResult


EPSG_NAMESPACES = {
       'gml': 'http://www.opengis.net/gml/3.2',
       'epsg': 'urn:x-ogp:spec:schema-xsd:EPSG:2.2:dataset'
    }

RDF_LABELS = [
    SKOS.prefLabel, DCT.title, RDFS.label, FOAF.name,
    SKOS.altLabel, DCT.identifier, SKOS.notation
]
"""Ordered list of RDF properties that might provide a label.

The order of the list is the order the properties
will be considered when the vocabulary is parsed. Once one
of these was found, the value is used as label, any other
would provide an alternative label. 

"""

def basic_rdf(
    name, url, format='xml', schemes=None, 
    languages=None, rdf_types=None, **kwargs
):
    """Build a vocabulary cluster from RDF data using simple SKOS vocabulary.

    This parser will register as a vocabulary item any URI 
    typed as ``skos:Concept`` and/or having a ``skos:inScheme``
    property.

    Parameters
    ----------
    name : str
        Name of the vocabulary.
    url : str
        Base URL of the SPDX register. Should return
        a JSON document listing all licenses, with keys
        ``reference``, ``licenseId`` and ``name``.
    format : {'xml', 'turtle', 'n3', 'json-ld', 'nt', 'trig'}, optional
        Encoding format of the RDF data. Parsing will
        fail if this parameter isn't properly set.
    schemes : list(str or URIRef), optional
        A list of schemes' URIs. If provided, only the
        concepts from the listed schemes are considered.
    languages : list(str or None), optional
        A list of allowed languages for labels. If 
        provided, only labels explicitely tagged with one
        of the languages from the list will be considered.
        To accept labels without a language tag, ``None``
        should be added to the list.
    rdf_types : list(str or URIRef), optional
        A list of RDF classes URIs. If provided, items
        typed as an object of one of those classes will
        be considered as vocabulary items and only them.
    
    Returns
    -------
    VocabularyParsingResult

    """

    result = VocabularyParsingResult(name)

    try:
        rdf_data = utils.fetch_data(url, format='text')
        graph = Graph()
        graph.parse(data=rdf_data, format=format)
    except Exception as error:
        result.exit(error)
        return result

    uris = []
    for uri, p, o in graph:
        if isinstance(uri, URIRef) and not uri in uris and (
            schemes and any(
                (uri, SKOS.inScheme, URIRef(scheme)) in graph
                for scheme in schemes
            ) and (
                not rdf_types or any(
                    (uri, RDF.type, URIRef(rdf_type)) in graph
                    for rdf_type in rdf_types
                )
            )
            or not schemes and (
                not rdf_types and (
                    (uri, RDF.type, SKOS.Concept) in graph
                    or (uri, SKOS.inScheme, None) in graph
                )
                or rdf_types and any(
                    (uri, RDF.type, URIRef(rdf_type)) in graph
                    for rdf_type in rdf_types
                )
            ) 
        ):
            uris.append(uri)

    for uri in uris:
        for property in RDF_LABELS:
            for label in graph.objects(uri, property):
                if isinstance(label, Literal) and (
                    not languages or label.language in languages 
                ):
                    result.add_label(uri, label.language, str(label))

    return result

def spdx_license(name, url, **kwargs):
    """Build a vocabulary cluster from the SPDX license register's data.

    Parameters
    ----------
    name : str
        Name of the vocabulary.
    url : str
        Base URL of the SPDX register. Should return
        a JSON document listing all licenses, with keys
        ``reference``, ``licenseId`` and ``name``.

    Returns
    -------
    VocabularyParsingResult

    """

    result = VocabularyParsingResult(name)

    try:
        json_data = utils.fetch_data(url)
    except Exception as error:
        result.exit(error)
        return result
    
    if not 'licenses' in json_data:
        result.exit(
            exceptions.UnexpectedDataError(
                'Missing key "licenses" in the JSON data.'
            )
        )
        return result
    
    for license in json_data['licenses']:
        valid = True

        uri = license.get('reference')
        if not uri:
            result.log_error(
                exceptions.UnexpectedDataError(
                    'Missing key "reference" for the license.',
                    detail=json.dumps(license, ensure_ascii=False)
                )
            )
            valid = False
        else:
            uri = re.sub('[.]html$', '', uri)

        name = license.get('name')
        if not name:
            result.log_error(
                exceptions.UnexpectedDataError(
                    'Missing key "name" for the license.',
                    detail=json.dumps(license, ensure_ascii=False)
                )
            )
            valid = False

        identifier = license.get('licenseId')
        if not identifier:
            result.log_error(
                exceptions.UnexpectedDataError(
                    'Missing key "licenseId" for the license.',
                    detail=json.dumps(license, ensure_ascii=False)
                )
            )
            valid = False

        if valid:
            result.add_label(
                uri=uri,
                language='en',
                label=f'{identifier} : {name}'
            )
            # the identifier and name alone are stored
            # as alternative labels
            result.add_label(
                uri=uri,
                label=identifier
            )
            result.add_label(
                uri=uri,
                language='en',
                label=name
            )

    return result

def iogp_epsg(name, url, **kwargs):
    """Build a vocabulary cluster from the OGC's EPSG coordinates reference systems register's data.

    Parameters
    ----------
    name : str
        Name of the vocabulary.
    url : str
        Base URL of the EPSG register. Should return
        a XML document listing all coordinates reference
        systems (CRS) URIs.

    Returns
    -------
    VocabularyParsingResult

    """
    result = VocabularyParsingResult(name)

    # first request to know the number of entries
    try:
        json_data = utils.fetch_data(url)
    except Exception as error:
        result.exit(error)
        return result
    
    if not 'TotalResults' in json_data:
        result.exit(
            exceptions.UnexpectedDataError(
                'Missing key "TotalResults" in the JSON data.'
            )
        )
        return result
    
    # second request to fetch them
    try:
        json_data = utils.fetch_data(
            url, params={'pageSize': json_data['TotalResults']}
            )
    except Exception as error:
        result.exit(error)
        return result
    
    if not 'Results' in json_data:
        result.exit(
            exceptions.UnexpectedDataError(
                'Missing key "Results" in the JSON data.'
            )
        )
        return result

    for crs_data in json_data['Results']:
        valid = True

        name = crs_data['Name']
        if not name:
            result.log_error(
                exceptions.UnexpectedDataError('Missing name.', detail=crs_data),
            )
            valid = False

        identifier = crs_data['Code']
        if not identifier:
            result.log_error(
                exceptions.UnexpectedDataError('Missing identifier.', detail=crs_data),
            )
            valid = False
        
        code_space = crs_data['DataSource']
        if not code_space == 'EPSG':
            result.log_error(
                exceptions.UnexpectedDataError('Code space is not EPSG.', detail=crs_data),
            )
            valid = False
        # any code space other than EPSG (ie nothing for now) is
        # discarded, since it won't be possible to build the OGC URI

        if valid:
            uri = f'http://www.opengis.net/def/crs/EPSG/0/{identifier}'
            result.add_label(
                uri=uri,
                label=f'{code_space} {identifier} : {name}'
            )
            # alternative labels: 'code:identifier', name
            # alone and identifier alone
            result.add_label(
                uri=uri,
                label=f'{code_space}:{identifier}'
            )
            result.add_label(
                uri=uri,
                label=f'{name}'
            )
            result.add_label(
                uri=uri,
                label=f'{identifier}'
            )

    return result

def ogc_epsg(name, url, limit=None, **kwargs):
    """Build a vocabulary cluster from the OGC's EPSG coordinates reference systems register's data.

    Parameters
    ----------
    vocabulary : str
        Name of the vocabulary.
    url : str
        Base URL of the EPSG register. Should return
        a XML document listing all coordinates reference
        systems (CRS) URIs.
    limit : int, optional
        Maximum number of CRS whose data should be fetched
        (one query by CRS). If ``None``, all listed CRS
        URIs are queried. In that case, execution takes
        approximatively 2 hours, with around 7k HTTP requests
        and parsing of each XML response.

    Returns
    -------
    VocabularyParsingResult

    """
    result = VocabularyParsingResult(name)

    runs = 0

    try:
        raw_data = utils.fetch_data(url, format='bytes')
        main_tree = etree.parse(BytesIO(raw_data))
        main_root = main_tree.getroot()
    except Exception as error:
        result.exit(error)
        return result

    for elem in main_root:

        runs += 1
        if limit and runs > limit:
            break

        crs_url = elem.text

        try:
            raw_crs_data = utils.fetch_data(crs_url, format='bytes')
            crs_tree = etree.parse(BytesIO(raw_crs_data))
            crs_root = crs_tree.getroot()
        except Exception as error:
            result.log_error(error)
            continue
        
        valid = True

        name = crs_root.xpath('gml:name/text()', namespaces=EPSG_NAMESPACES)
        if not name:
            result.log_error(
                exceptions.UnexpectedDataError('Missing name.', detail=crs_url),
            )
            valid = False

        identifier = crs_root.xpath('gml:identifier/text()', namespaces=EPSG_NAMESPACES)
        if not identifier:
            result.log_error(
                exceptions.UnexpectedDataError('Missing identifier.', detail=crs_url),
            )
            valid = False
        
        code_space = crs_root.xpath('gml:identifier/@codeSpace',
            namespaces=EPSG_NAMESPACES) or 'EPSG'
        # since code space is always EPSG for now, it's assumed to be
        # EPSG as well if missing in the future

        if valid:
            result.add_label(
                uri=crs_url,
                label=f'{code_space[0]} {identifier[0]} : {name[0]}'
            )
            # alternative labels: 'code:identifier', name
            # alone and identifier alone
            result.add_label(
                uri=crs_url,
                label=f'{code_space[0]}:{identifier[0]}'
            )
            result.add_label(
                uri=crs_url,
                label=f'{name[0]}'
            )
            result.add_label(
                uri=crs_url,
                label=f'{identifier[0]}'
            )

    return result
