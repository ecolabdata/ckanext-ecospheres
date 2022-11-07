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

import re, json, zipfile
from lxml import etree
from rdflib import URIRef, Literal, Dataset, RDF
from io import BytesIO

from ckanext.ecospheres.vocabulary.parser import utils, exceptions
from ckanext.ecospheres.vocabulary.parser.utils import VocabularyGraph
from ckanext.ecospheres.vocabulary.parser.result import VocabularyParsingResult


EPSG_NAMESPACES = {
    'gml': 'http://www.opengis.net/gml/3.2',
    'epsg': 'urn:x-ogp:spec:schema-xsd:EPSG:2.2:dataset'
}

IGN_NAMESPACES = {
    'xmlns': 'http://www.isotc211.org/2005/gmx',
    'gml': 'http://www.opengis.net/gml'
}

def basic_rdf(
    name, url, format='xml', schemes=None, 
    languages=None, rdf_types=None, recursive=False,
    hierarchy=False, uri_property=None, regexp_property=None,
    translation_scheme=None, _result=None, **kwargs
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
    uri_property : str, default None
        URI of a property that holds the URIs of vocabulary
        items, to use instead of the original URIs of source
        graph.
    regexp_property : str, default None
        URI of a property providing regular expressions to
        use for mapping free text to the vocabulary concepts.
    translation_scheme : str, default None
        URI of a scheme from Ecospheres' register that might
        provide additionnal translations for the vocabulary
        labels.
    
    Returns
    -------
    VocabularyParsingResult

    """

    result = _result if _result is not None else VocabularyParsingResult(name)
    
    pile = [url]
    uris = []
    labels = []
    relationships = []
    regexp = []
    if uri_property:
        map_uris = {}

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

            if uri_property:
                res_uri = graph.value(URIRef(new_uri), URIRef(uri_property))
                if res_uri and (
                    isinstance(res_uri, URIRef) or
                    isinstance(res_uri, Literal) 
                    and res_uri.datatype == URIRef('http://purl.org/dc/terms/URI')
                ):
                    map_uris[new_uri] = str(res_uri)

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
            
            if regexp_property:
                new_regexp = graph.objects(URIRef(new_uri), URIRef(regexp_property))
                for exp in new_regexp:
                    exp = str(exp)
                    if not (new_uri, exp) in regexp:
                        regexp.append((new_uri, exp))

    if uri_property:
        new_labels = []
        new_relationships = []
        new_uris = []
        for uri, language, label in labels:
            if uri in map_uris:
                new_labels.append((map_uris[uri], language, label))
        for parent, child in relationships:
            if child in map_uris and parent in map_uris:
                new_relationships((map_uris[child], map_uris[parent]))
        for uri in uris:
            if uri in map_uris:
                new_uris.append(map_uris[uri])
        labels = new_labels
        relationships = new_relationships
        uris = new_uris

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
        result.data.hierarchy_table()
        table = result.data.hierarchy
        for relationship in relationships:
            table.add(*relationship)
        if not regexp_property:
            response = result.data.validate()
            if not response:
                for anomaly in response:
                    result.log_error(exceptions.InvalidDataError(anomaly))

    if regexp_property:
        result.data.regexp_table()
        table = result.data.regexp
        for exp in regexp:
            table.add(*exp)
        response = result.data.validate()
        if not response:
            for anomaly in response:
                result.log_error(exceptions.InvalidDataError(anomaly))

    if not result.data:
        result.exit(exceptions.NoVocabularyDataError())

    if result and translation_scheme:
        if not translation_scheme.endswith('.json'):
            translation_scheme = f'{translation_scheme}.json'
        result = basic_rdf(
            name=name, url=translation_scheme, format='json-ld',
            languages=languages, recursive=True,
            uri_property='http://www.w3.org/2004/02/skos/core#exactMatch',
            _result=result, **kwargs
        )

    return result

def spdx_license(name, url, translation_scheme, **kwargs):
    """Build a vocabulary cluster from the SPDX license register's data.

    Parameters
    ----------
    name : str
        Name of the vocabulary.
    url : str
        Base URL of the SPDX register. Should return
        a JSON document listing all licenses, with keys
        ``reference``, ``licenseId`` and ``name``.
    translation_scheme : str, default None
        URI of a scheme from Ecospheres' register that might
        provide additionnal translations for the vocabulary
        labels.

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

    if result and translation_scheme:
        if not translation_scheme.endswith('.json'):
            translation_scheme = f'{translation_scheme}.json'
        result = basic_rdf(
            name=name, url=translation_scheme, format='json-ld',
            recursive=True, uri_property='http://www.w3.org/2004/02/skos/core#exactMatch',
            _result=result, **kwargs
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
    all territories, a ``[name]_hierarchy (parent, child)``
    table where a child is a subdivision of the parent, and
    a ``[name]_synonym (uri, synonym)`` table storing 
    corresponding URIs from the ``eu_administrative_territory_unit``
    and ``insee_official_geographic_code`` vocabularies.

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
        'zones-maritimes', 'régions-métropole', 'outre-mer',
        'départements-métropole'
    )
    # the order matters: included territories should be handled
    # after including territories.

    result.data.hierarchy_table()
    result.data.synonym_table()
    result.data.spatial_table()

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

            depcode = re.match('^D([0-9]{2}|2[AB])$', id)
            if depcode:
                label = f'{depcode[1]} {label}'

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
            result.data.spatial.add(
                id, westlimit, southlimit, eastlimit, northlimit
            )
    
            if 'codeRégion' in territory:
                result.data.hierarchy.add(
                    territory['codeRégion'], id
                )
            
            uri_ue = territory.get('uriUE')
            if uri_ue:
                result.data.synonym.add(
                    id, uri_ue
                )

            uri_cog = territory.get('uriCOG')
            if uri_cog:
                result.data.synonym.add(
                    id, uri_cog
                )

    if not result.data:
        result.exit(exceptions.NoVocabularyDataError())

    return result


def insee_official_geographic_code(name, url, rdf_types=None, **kwargs):
    """Build a vocabulary cluster with Insee's official geographic code data.

    This vocabulary is HUGE, loading it takes a lot
    of time (around 1h45).

    The cluster build by this parser contains an additional
    ``[name]_hierarchy (parent, child)`` table where a child
    is a subdivision of the parent, and a
    ``[name]_synonym (uri, synonym)`` table storing the
    information that two URIs identify the same object.
    If the A-B couple appears in this table, B-A will be there
    as well, and both A and B would have been registered in the
    labels table. Only one of them will carry the alternative
    labels and hierarchy information.

    Parameters
    ----------
    name : str
        Name of the vocabulary.
    url : str
        Download URL of the ZIP file containing the data.
        That archive should contain one file holding
        trig-encoded RDF data. The parser will look for
        a graph whose identifier is
        ``'http://rdf.insee.fr/graphes/geo/cog'``.
    rdf_types : list(str), optional
        Liste d'URI de classes d'objets à considérer. Si
        non fourni, tout est conservé.

    Returns
    -------
    VocabularyParsingResult

    Notes
    -----
    Terrorial entities will be registered more than once 
    if they have multiple URIs (usually one with an UUID
    and one with a geographic code). Labels for all available
    languages are provided for both, alternative labels
    are carried by the UUID-based URI.

    """
    result = VocabularyParsingResult(name)

    try:
        content = utils.fetch_data(url, format='bytes', **kwargs)
        zip_data = zipfile.ZipFile(BytesIO(content))
        dataset = Dataset()
        with zip_data.open(zip_data.namelist()[0]) as src:
            # assuming there is only one file in the archive
            dataset.parse(file=src, format='trig')
        graph = dataset.graph('http://rdf.insee.fr/graphes/geo/cog')
    except Exception as error:
        result.exit(error)
        return result

    result.data.hierarchy_table()
    result.data.synonym_table()

    relationships = []
    uris = []

    for uuid, label in graph.subject_objects(URIRef('http://rdf.insee.fr/def/geo#nom')):
        if not rdf_types or str(graph.value(uuid, RDF.type)) in rdf_types:
            result.add_label(str(uuid), language='fr', label=str(label))
            uris.append(uuid)

    for item in result.data.label:
        uri = item['uri']
        label = item['label']

        for altlabel in graph.objects(
            URIRef(uri), URIRef('http://rdf.insee.fr/def/geo#nomSansArticle')
        ):
            if str(altlabel) != label:
                result.add_label(uri, language='fr', label=str(altlabel))

        for altlabel in graph.objects(
            URIRef(uri), URIRef('http://rdf.insee.fr/def/geo#nomEntier')
        ):
            if str(altlabel) != label:
                result.add_label(uri, language='fr', label=str(altlabel))
        
        for insee_code in graph.objects(
            URIRef(uri), URIRef('http://rdf.insee.fr/def/geo#codeINSEE')
        ):
            result.add_label(uri, language='fr', label=str(insee_code))

        for parent in graph.objects(
                URIRef(uri), URIRef('http://rdf.insee.fr/def/geo#subdivisionDirecteDe')
        ):
            if parent in uris and not (str(parent), uri) in relationships:
                relationships.append((str(parent), uri))

        for code_uri in graph.objects(
            URIRef(uri), URIRef('http://www.w3.org/2002/07/owl#sameAs')
        ):
            if not code_uri in uris:
                result.add_label(str(code_uri), language='fr', label=label)
                uris.append(code_uri)
                result.data.synonym.add(str(code_uri), uri)
                result.data.synonym.add(uri, str(code_uri))

    for relationship in relationships:
        result.data.hierarchy.add(*relationship)

    # skipping validation as it's already quite long
    # response = result.data.validate()
    # if not response:
    #     for anomaly in response:
    #         result.log_error(exceptions.InvalidDataError(anomaly))

    if not result.data:
        result.exit(exceptions.NoVocabularyDataError())

    return result


def ign_crs(name, url, **kwargs):
    """Build a vocabulary cluster from IGN's coordinates reference systems register.

    The cluster build by this parser contains an additional
    ``[name]_synonym (uri, synonym)`` table storing 
    corresponding URIs from the EPSG register and such.

    Parameters
    ----------
    name : str
        Name of the vocabulary.
    url : str
        Base URL of the register. Should return a XML document
        listing all coordinates reference systems (CRS) as
        ``crs`` elements.

    Returns
    -------
    VocabularyParsingResult

    """
    result = VocabularyParsingResult(name)

    result.data.synonym_table()

    try:
        raw_data = utils.fetch_data(url, format='bytes', **kwargs)
        tree = etree.parse(BytesIO(raw_data))
        root = tree.getroot()
    except Exception as error:
        result.exit(error)
        return result

    for elem in root.iter(tag='{*}crs'):

        valid = True

        identifiers = elem.xpath('./*/gml:identifier/text()', namespaces=IGN_NAMESPACES)
        if not identifiers:
            result.log_error(
                exceptions.UnexpectedDataError('missing crs identifier'),
            )
            valid = False
        
        synonyms = []
        labels = []
        for value in elem.xpath('./*/gml:name', namespaces=IGN_NAMESPACES):
            if value.get('codeSpace'):
                synonyms.append(value.text)
            elif value.text:
                labels.append(value.text)
        if not labels:
            result.log_error(
                exceptions.UnexpectedDataError('missing crs name'),
            )
            valid = False

        if valid:
            identifier = identifiers[0]

            for label in labels:
                result.add_label(
                    uri=identifier,
                    language='fr',
                    label=label
                    )
            
            for synonym in synonyms:
                result.data.synonym.add(identifier, synonym)

    if not result.data:
        result.exit(exceptions.NoVocabularyDataError())

    return result

