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
raw data, notably the :py:func:`ckanext.ecospheres.vocabulary.parser.utils.fetch_data`
function.

Arbitrary keywords parameters should be passed down
any time the parser calls :py:func:`ckanext.ecospheres.vocabulary.parser.utils.fetch_data`.
:py:func:`ckanext.ecospheres.vocabulary.parser.utils.fetch_data` will
then pass down any relevant parameter (ie. any parameter with an expected name)
to :py:func:`requests.get`, such as proxy mapping, etc.

    >>> data = utils.fetch_data(url, format=format, **kwargs)

Any error met during execution should be logged by the parser, either
as a "critical failure" or as a "simple error".

To declare a critical failure with the
:py:meth:`VocabularyParsingResult.exit` method:

    >>> res.exit(exception_object)
    >>> return res

As in the exemple above, the (failed) parsing result should
immediately be returned after declaring a critical failure.

To log a simple error with the
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
from ckanext.ecospheres.vocabulary.parser.utils import VocabularyGraph
from ckanext.ecospheres.vocabulary.parser.result import VocabularyParsingResult


EPSG_NAMESPACES = {
       'gml': 'http://www.opengis.net/gml/3.2',
       'epsg': 'urn:x-ogp:spec:schema-xsd:EPSG:2.2:dataset'
    }

def basic_rdf(
    name, url, format='xml', schemes=None, 
    languages=None, rdf_types=None, recursive=False,
    hierarchy=False, **kwargs
):
    """Build a vocabulary cluster from RDF data using simple SKOS vocabulary.

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
    schemes : list(str or rdflib.term.URIRef), optional
        A list of schemes' URIs. If provided, only the
        concepts from the listed schemes are considered.
    languages : list(str or None), optional
        A list of allowed languages for labels. If 
        provided, only labels explicitely tagged with one
        of the languages from the list will be considered.
        To accept labels without a language tag, ``None``
        should be added to the list.
    rdf_types : list(str or rdflib.term.URIRef), optional
        A list of RDF classes URIs. If provided, items
        typed as an object of one of those classes will
        be considered as vocabulary items and only them.
    recursive : bool, default False
        If ``True``, the function will try and get additional
        data by sending a request to every vocabulary URI.
        Do not change the value of this parameter if not
        necessary to retrieve the labels or any relevant
        information as it will make the parsing much slower.
    hierarchy : bool, default False
        If ``True``, an additional ``[name]_hierarchy``
        table will be added to the cluster and populated with
        relationships provided by ``skos:broader`` and
        ``skos:narrower`` properties.
    
    Returns
    -------
    VocabularyParsingResult

    """

    result = VocabularyParsingResult(name)
    
    pile = [url]
    uris = []
    labels = []
    relationships = []

    while pile:
        uri = pile.pop()

        try:
            rdf_data = utils.fetch_data(uri, format='text', **kwargs)
            graph = VocabularyGraph()
            graph.parse(data=rdf_data, format=format)
        except Exception as error:
            if uri == url:
                result.exit(error)
                return result
            result.log_error(error)
            continue
        
        new_uris = graph.find_vocabulary_items(
            schemes=schemes, rdf_types=rdf_types
        ) # uri should be one of those if it's a concept
        
        for new_uri in new_uris:
            new_uri = str(new_uri)
            if not new_uri in uris:
                uris.append(new_uri)
                if recursive and not new_uri == url:
                    pile.append(new_uri)
                    # this means that if a label is
                    # found from the current URI, any
                    # label returned when the function will
                    # interrogate the new URI will be seen as
                    # an alternative label, even if a "better"
                    # property is holding the label
            
            new_labels = graph.find_labels(new_uri, languages=languages)
            for new_label in new_labels:
                label_row = (new_uri, new_label.language, str(new_label))
                if not label_row in labels:
                    labels.append(label_row)

            if hierarchy:
                children = graph.find_children(new_uri)
                for child in children:
                    child = str(child)
                    if not (new_uri, child) in relationships:
                        relationships.append((new_uri, child))
    
    for label in labels:
        result.add_label(*label)
        if label[0] in uris:
            uris.remove(label[0])

    for uri in uris:
        result.log_error(
            exceptions.UnexpectedDataError(
                'missing label', detail=uri
            )
        )

    if hierarchy:
        table_name = result.data.table('hierarchy', ('parent', 'child'))
        table = result.data[table_name]
        table.set_not_null_constraint('parent')
        table.set_not_null_constraint('child')
        result.data.set_reference_constraint(
            referenced_table=table_name,
            referenced_fields=('parent',),
            referencing_table='label',
            referencing_fields=('uri',)
        )
        result.data.set_reference_constraint(
            referenced_table=table_name,
            referenced_fields=('child',),
            referencing_table='label',
            referencing_fields=('uri',)
        )
        for relationship in relationships:
            table.add(*relationship)
        response = result.data.validate()
        if not response:
            for anomaly in response:
                result.log_error(exceptions.InvalidDataError(anomaly))

    if not result.data:
        result.exit(exceptions.NoVocabularyDataError())

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
        json_data = utils.fetch_data(url, **kwargs)
    except Exception as error:
        result.exit(error)
        return result
    
    if not 'licenses' in json_data:
        result.exit(
            exceptions.UnexpectedDataError(
                'missing key "licenses" in the JSON data'
            )
        )
        return result
    
    for license in json_data['licenses']:
        valid = True

        uri = license.get('reference')
        if not uri:
            result.log_error(
                exceptions.UnexpectedDataError(
                    'missing key "reference" for the license',
                    detail=json.dumps(license, ensure_ascii=False)
                )
            )
            valid = False
        else:
            uri = re.sub('[.]html$', '', uri)

        label = license.get('name')
        if not label:
            result.log_error(
                exceptions.UnexpectedDataError(
                    'missing key "name" for the license',
                    detail=json.dumps(license, ensure_ascii=False)
                )
            )
            valid = False

        identifier = license.get('licenseId')
        if not identifier:
            result.log_error(
                exceptions.UnexpectedDataError(
                    'missing key "licenseId" for the license',
                    detail=json.dumps(license, ensure_ascii=False)
                )
            )
            valid = False

        if valid:
            result.add_label(
                uri=uri,
                language='en',
                label=f'{identifier} : {label}'
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
                label=label
            )

    if not result.data:
        result.exit(exceptions.NoVocabularyDataError())

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
        json_data = utils.fetch_data(url, **kwargs)
    except Exception as error:
        result.exit(error)
        return result
    
    if not 'TotalResults' in json_data:
        result.exit(
            exceptions.UnexpectedDataError(
                'missing key "TotalResults" in the JSON data'
            )
        )
        return result
    
    # second request to fetch them
    try:
        json_data = utils.fetch_data(
            url, params={'pageSize': json_data['TotalResults']}, **kwargs
            )
    except Exception as error:
        result.exit(error)
        return result
    
    if not 'Results' in json_data:
        result.exit(
            exceptions.UnexpectedDataError(
                'missing key "Results" in the JSON data'
            )
        )
        return result

    for crs_data in json_data['Results']:
        valid = True

        label = crs_data['Name']
        if not label:
            result.log_error(
                exceptions.UnexpectedDataError('missing name', detail=crs_data),
            )
            valid = False

        identifier = crs_data['Code']
        if not identifier:
            result.log_error(
                exceptions.UnexpectedDataError('missing identifier', detail=crs_data),
            )
            valid = False
        
        code_space = crs_data['DataSource']
        if not code_space == 'EPSG':
            result.log_error(
                exceptions.UnexpectedDataError('code space is not EPSG', detail=crs_data),
            )
            valid = False
        # any code space other than EPSG (ie nothing for now) is
        # discarded, since it won't be possible to build the OGC URI

        if valid:
            uri = f'http://www.opengis.net/def/crs/EPSG/0/{identifier}'
            result.add_label(
                uri=uri,
                label=f'{code_space} {identifier} : {label}'
            )
            # alternative labels: 'code:identifier', label
            # alone and identifier alone
            result.add_label(
                uri=uri,
                label=f'{code_space}:{identifier}'
            )
            result.add_label(
                uri=uri,
                label=f'{label}'
            )
            result.add_label(
                uri=uri,
                label=f'{identifier}'
            )

    if not result.data:
        result.exit(exceptions.NoVocabularyDataError())

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
        raw_data = utils.fetch_data(url, format='bytes', **kwargs)
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
            raw_crs_data = utils.fetch_data(crs_url, format='bytes', **kwargs)
            crs_tree = etree.parse(BytesIO(raw_crs_data))
            crs_root = crs_tree.getroot()
        except Exception as error:
            result.log_error(error)
            continue
        
        valid = True

        label = crs_root.xpath('gml:name/text()', namespaces=EPSG_NAMESPACES)
        if not label:
            result.log_error(
                exceptions.UnexpectedDataError('missing name', detail=crs_url),
            )
            valid = False

        identifier = crs_root.xpath('gml:identifier/text()', namespaces=EPSG_NAMESPACES)
        if not identifier:
            result.log_error(
                exceptions.UnexpectedDataError('missing identifier', detail=crs_url),
            )
            valid = False
        
        code_space = crs_root.xpath('gml:identifier/@codeSpace',
            namespaces=EPSG_NAMESPACES) or 'EPSG'
        # since code space is always EPSG for now, it's assumed to be
        # EPSG as well if missing in the future

        if valid:
            result.add_label(
                uri=crs_url,
                label=f'{code_space[0]} {identifier[0]} : {label[0]}'
            )
            # alternative labels: 'code:identifier', name
            # alone and identifier alone
            result.add_label(
                uri=crs_url,
                label=f'{code_space[0]}:{identifier[0]}'
            )
            result.add_label(
                uri=crs_url,
                label=f'{label[0]}'
            )
            result.add_label(
                uri=crs_url,
                label=f'{identifier[0]}'
            )

    if not result.data:
        result.exit(exceptions.NoVocabularyDataError())

    return result

def ecospheres_territory(name, url, **kwargs):
    """Build a vocabulary cluster with Ecospheres' territories.

    The cluster build by this parser contains an additional
    ``[name]_spatial (uri, westlimit, southlimit, eastlimit,
    northlimit)`` table storing extend coordinates for
    all territories.

    Parameters
    ----------
    name : str
        Name of the vocabulary.
    url : str
        URL of the territories' data.

    Returns
    -------
    VocabularyParsingResult

    Notes
    -----
    Since territories are not included in DCAT exports, this
    parser doesn't bother to look for real URIs and uses
    instead some identifiers without namespace.

    """
    result = VocabularyParsingResult(name)

    try:
        json_data = utils.fetch_data(url, **kwargs)
    except Exception as error:
        result.exit(error)
        return result
    
    territory_types = (
        'zones-maritimes', 'outre-mer', 'départements-métropole',
        'régions-métropole'
    )

    table_name = result.data.table(
        'spatial', ('uri', 'westlimit', 'southlimit', 'eastlimit', 'northlimit')
        )
    table = result.data[table_name]
    table.set_not_null_constraint('uri')
    table.set_unique_constraint('uri')
    table.set_not_null_constraint('westlimit')
    table.set_not_null_constraint('southlimit')
    table.set_not_null_constraint('eastlimit')
    table.set_not_null_constraint('northlimit')
    result.data.set_reference_constraint(
        referenced_table=table_name,
        referenced_fields=('uri',),
        referencing_table='label'
    )

    for territory_type in territory_types:
        if not territory_type in json_data:
            result.log_error(
                exceptions.UnexpectedDataError(
                    f"no registerded territory of type '{territory_type}'"
                )
            )
            continue

        for id, territory in json_data[territory_type].items():
            label = territory.get('name')
            if not label:
                result.log_error(
                    exceptions.UnexpectedDataError(
                        f"missing name for territory '{id}'"
                    )
                )
                continue

            if not 'spatial' in territory:
                result.log_error(
                    exceptions.UnexpectedDataError(
                        f"missing coordinates for territory '{id}'"
                    )
                )
                continue
            westlimit = territory['spatial'].get('westlimit')
            southlimit = territory['spatial'].get('southlimit')
            eastlimit = territory['spatial'].get('eastlimit')
            northlimit = territory['spatial'].get('northlimit')
            if (
                westlimit is None or southlimit is None or
                eastlimit is None or northlimit is None
            ):
                result.log_error(
                    exceptions.UnexpectedDataError(
                        f"missing coordinates for territory '{id}'"
                    )
                )
                continue
            
            result.add_label(id, language='fr', label=label)
            result.data[table_name].add(id, westlimit, southlimit, eastlimit, northlimit)
    
    if not result.data:
        result.exit(exceptions.NoVocabularyDataError())

    return result

