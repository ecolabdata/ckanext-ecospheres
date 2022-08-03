import requests, re
from lxml import etree
from rdflib import Graph, URIRef, Literal, SKOS, RDF
from io import BytesIO

EPSG_NAMESPACES = {
       'gml': 'http://www.opengis.net/gml/3.2',
       'epsg': 'urn:x-ogp:spec:schema-xsd:EPSG:2.2:dataset'
    }

class VocabularyTable(list):
    """Pseudo table with vocabulary data.
    
    This class is meant to organise parsed vocabulary prior to
    database storage. A :py:class:`VocabularyTable` object
    contains the data meant for the database table with the same
    name as its attribute :py:attr:`VocabularyTable.name`.

    Each item of the list represents a database record. It is
    a dictionnary whose keys are the names of the table fields.
    Its values are the values of the fields (ie. some vocabulary
    data) or ``None`` if no data was provided.

    :py:class:`VocabularyTable` objects are usually created
    and filled through a :py:class:`VocabularyData` object.
    
    Parameters
    ----------
    vocabulary : str
        Name of the vocabulary, ie its ``name``
        property in ``vocabularies.yaml``.
    name : str
        The table name. If not prefixed by the vocabulary
        name, such prefixed will be added.
    fields : tuple(str)
        Names of the table fields.

    Attributes
    ----------
    name : str
        The table name.
    fields : tuple(str)
        Names of the table fields.

    """

    def __init__(self, vocabulary, name, fields):
        self.fields = tuple(fields or ())
        if not name.startswith(f'{vocabulary}_'):
            name = f'{vocabulary}_{name}'
        self.name = name
        
    def add(self, *data, **kwdata):
        """Add some data to the table.
        
        Data is provided through positional and/or
        keywords parameters.

        Keywords parameters should use the fields' names
        or will be ignored. Positional parameters are handled
        first and therefor might be overwriten by keywords
        parameters. If the number of positional parameters exceeds
        the number of fields, extra parameters are ignored.
        
        Examples
        --------
        >>> table = VocabularyTable(
        ...     'somevoc', 'special', ('field_1', 'field_2')
        ... )
        >>> table.add()
        {'field_1': None, 'field_2': None}
        >>> table.add('a', 'b', 'c')
        {'field_1': 'a', 'field_2': 'b'}
        >>> table.add(field_2='a', field_1='b', field_3='c')
        {'field_1': 'b', 'field_2': 'a'}
        >>> table.add('a', 'c', field_2='b')
        {'field_1': 'a', 'field_2': 'b'}

        """
        item = {f: None for f in self.fields}
        self.append(item)
        if data:
            data = list(data)
            data.reverse()
            for field in self.fields:
                if not data:
                    break
                item[field] = data.pop()
        if kwdata:
            for field, value in kwdata.items():
                if field in item:
                    item[field] = value
        return item

class VocabularyData(dict):
    """Vocabulary data.

    This class is meant to organise parsed vocabulary prior to
    database storage.

    A :py:class:`VocabularyData` is a dictionnary. Its keys are
    database table names. Its values :py:class:`VocabularyTable`
    are objects containing the data to be loaded into said
    tables.

    The labels' table and the alternative labels' table are
    created during initialization and can be accessed through
    the attributes :py:attr:`VocabularyData.label` and 
    :py:attr:`VocabularyData.altlabel`.

    Additionnal tables may be added with :py:meth:`VocabularyData.table`
    and will be accessible through an attribute named after the
    table.

    Parameters
    ----------
    vocabulary : str
        Name of the vocabulary, ie its ``name``
        property in ``vocabularies.yaml``.
    label : VocabularyTable
        The table containing the vocabulary labels.
        This table has three fields :

        * ``uri`` is the vocabulary item URI.
        * ``language`` is a ISO 639-1 language code
          (2 letter) if possible, else ISO 639-3.
        * ``label`` is the preferred label for the
          language.
        
        ``uri, language`` should be unique.
    altlabel : VocabularyTable
        The table containing the vocabulary alternative
        labels. Same structure as `label` whithout
        unicity consideration. Alternative labels are
        used to find matching vocabulary items during
        harvest. Users will never see them.

    Attributes
    ----------
    name : str
        The table name.
    fields : tuple(str)
        Names of the table fields.

    """

    def __init__(self, vocabulary):
        self.vocabulary = vocabulary
        table = VocabularyTable(
            self.vocabulary,
            name='label',
            fields=('uri', 'language', 'label')
        )
        self[table.name] = table
        self.labels = table
        table = VocabularyTable(
            self.vocabulary,
            name='altlabel',
            fields=('uri', 'language', 'label')
        )
        self[table.name] = table
        self.altlabels = table

    def table(self, name, fields):
        """Add a custom table and returns its name.

        Be aware that the name of the resulting
        table might differ from the intial one as
        a table name has to be prefixed by the 
        vocabulary name.

        Parameters
        ----------
        vocabulary : str
            Name of the vocabulary, ie its ``name``
            property in ``vocabularies.yaml``.
        name : str
            The table name. If not prefixed by the vocabulary
            name, such prefixed will be added.
        fields : tuple(str)
            Names of the table fields.

        Returns
        -------
        str or None
            The name of the newly created table, or
            ``None`` if the table existed already.

        Examples
        --------
        >>> somevoc = VocabularyData('somevoc')
        >>> somevoc.table('special', ('field_1', 'field_2'))
        'somevoc_special'
        >>> somevoc.table('somevoc_special', ('field_1', 'field_2')) is None
        True

        """
        if name in self:
            return
        table = VocabularyTable(self.vocabulary, name, fields)
        self[table.name] = table
        self.__setattr__(table.name, table)
        return table.name

def spdx_license_to_skos(url, strict=False):
    """Build a RDF graph using simple SKOS vocabulary from SPDX license register.

    Parameters
    ----------
    url : str
        Base URL of the SPDX register. Should return
        a JSON document listing all licenses, with keys
        ``reference``, ``licenseId`` and ``name``.
    strict : bool, default False
        If ``True``, an exception will be raised if
        necessary information is missing for a license.
        If ``False``, the execution will continue with the
        next license. 

    Returns
    -------
    rdflib.graph.Graph

    """
    response = requests.get(url)
    if response.status_code != requests.codes.ok:
        response.raise_for_status()
    
    json_result = response.json()
    if not 'licenses' in json_result:
        raise ValueError('No licenses list ? Key "licenses" was not found.')
    
    license_graph = Graph()

    for license in json_result['licenses']:
        x_uri = license.get('reference')
        if not x_uri:
            if strict:
                raise ValueError(f'Missing reference for license.')
            else:
                continue
                # TODO: log error
        license_uri = re.sub('[.]html$', '', x_uri)

        x_name = license.get('name')
        if not x_name:
            if strict:
                raise ValueError(f'Missing name for license <{license_uri}>.')
            else:
                continue
                # TODO: log error

        x_identifier = license.get('licenseId')
        if not x_identifier:
            if strict:
                raise ValueError(f'Missing identifier for license <{license_uri}>.')
            else:
                continue
                # TODO: log error

        license_graph.add((URIRef(license_uri), RDF.type, SKOS.Concept))
        license_graph.add((URIRef(license_uri), SKOS.inScheme, URIRef('https://spdx.org/licenses')))
        license_graph.add((URIRef(license_uri), SKOS.prefLabel, Literal(f'{x_identifier} : {x_name}', lang='en')))
    
    return license_graph


def ogc_epsg_to_skos(url, strict=False):
    """Build a RDF graph using simple SKOS vocabulary from OGC's EPSG coordinates reference systems register.

    Execution takes approximatively 2 hours, with around
    7k HTTP requests and parsing of each XML response.

    Parameters
    ----------
    url : str
        Base URL of the EPSG register. Should return
        a XML document listing all coordinates reference
        systems (CRS) URIs.
    strict : bool, default False
        If ``True``, an exception will be raised if the
        XML describing the CRS can't be fetched or parsed
        for any CRS. If ``False``, the execution will
        continue with the next CRS. 

    Returns
    -------
    rdflib.graph.Graph

    """
    response = requests.get(url)
    if response.status_code != requests.codes.ok:
        response.raise_for_status()
    
    main_tree = etree.parse(BytesIO(response.content))
    main_root = main_tree.getroot()

    epsg_graph = Graph()

    for elem in main_root:

        crs_url = elem.text
        response = requests.get(crs_url)
    
        if response.status_code != requests.codes.ok:
            if strict:
                response.raise_for_status()
            else:
                continue
                # TODO: log error

        try:
            crs_tree = etree.parse(BytesIO(response.content))
        except Exception as err:
            if strict:
                raise err
            else:
                continue
                # TODO: log error
        
        crs_root = crs_tree.getroot()
        
        x_name = crs_root.xpath('gml:name/text()', namespaces=EPSG_NAMESPACES)
        if not x_name:
            if strict:
                raise ValueError(f'Missing name for CRS <{crs_url}>.')
            else:
                continue
                # TODO: log error

        x_identifier = crs_root.xpath('gml:identifier/text()', namespaces=EPSG_NAMESPACES)
        if not x_identifier:
            if strict:
                raise ValueError(f'Missing identifier for CRS <{crs_url}>.')
            else:
                continue
                # TODO: log error
        
        x_code_space = crs_root.xpath('gml:identifier/@codeSpace', namespaces=EPSG_NAMESPACES) or 'EPSG'
        # since code space is always EPSG for now, it's assumed to be
        # EPSG as well if missing in the future

        epsg_graph.add((URIRef(crs_url), RDF.type, SKOS.Concept))
        epsg_graph.add((URIRef(crs_url), SKOS.inScheme, URIRef(url)))
        epsg_graph.add((URIRef(crs_url), SKOS.prefLabel, Literal(f'{x_code_space[0]} {x_identifier[0]} : {x_name[0]}')))
        print(crs_url)

    return epsg_graph

