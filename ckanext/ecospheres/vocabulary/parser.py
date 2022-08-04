import requests, re
from lxml import etree
from rdflib import Graph, URIRef, Literal, SKOS, RDF
from io import BytesIO

EPSG_NAMESPACES = {
       'gml': 'http://www.opengis.net/gml/3.2',
       'epsg': 'urn:x-ogp:spec:schema-xsd:EPSG:2.2:dataset'
    }


class DataTableConstraint:
    """Table constraints.
    
    This is an abstract class.
    All table constraints are subclasses of this class.

    """

class DataTableUniqueConstraint(tuple, DataTableConstraint):
    """Unique constraint.

    :py:class:`DataTableUniqueConstraint` objects are
    tuples of table fields.

    """
    def __repr__(self):
        return '({}) IS UNIQUE'.format(', '.join(f for f in self))

class DataTableNotNullConstraint(str, DataTableConstraint):
    """Not null constraint.

    :py:class:`DataTableUniqueConstraint` objects are
    the names of the fields that should not be empty.

    """
    def __repr__(self):
        return f'{self} IS NOT NULL'

class DataValidationAnomaly(dict):
    """Anomaly detected during validation.

    The dictionnary is the invalid record itself.

    Attributes
    ----------
    constraint : DataTableConstraint
        The constraint that was not respected.

    """
    def __init__(self, record, constraint):
        self.update(record)
        self.constraint = constraint

class DataValidationResponse(list):
    """Result of data validation.

    This is a list of the detected anomalies, if any.

    The boolean value of a :py:class:`DataValidationResponse`
    object is the global result of the validation : ``True``
    if all records are valid (ie the list is empty), else
    ``False``.

    Attributes
    ----------
    anomalies : list(DataValidationAnomaly)
        List of invalid records.

    """
    def __bool__(self):
        return len(self) == 0

class VocabularyDataTable(list):
    """Pseudo table with vocabulary data.
    
    This class is meant to organise parsed vocabulary prior to
    database storage. A :py:class:`VocabularyDataTable` object
    contains the data meant for the database table with the same
    name as its attribute :py:attr:`VocabularyDataTable.name`.

    Each item of the list represents a database record. It is
    a dictionnary whose keys are the names of the table fields.
    Its values are the values of the fields (ie. some vocabulary
    data) or ``None`` if no data was provided.

    :py:class:`VocabularyDataTable` objects are usually created
    and filled through a :py:class:`VocabularyDataCluster` object.
    
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
    unique : list(str or tuple(str)), optional
        List of fields names or tuples of fields names
        that should be unique across the table.
    not_null : list(str), optional
        List of fields names that should not be empty.

    Attributes
    ----------
    name : str
        The table name.
    fields : tuple(str)
        Names of the table fields.
    constraints : list(DataTableConstraint)
        List of the table constraints.

    """

    def __init__(
        self, vocabulary, name, fields,
        not_null=None, unique=None
    ):
        no_duplicate_fields = []
        for f in fields or ():
            if not f in no_duplicate_fields:
                no_duplicate_fields.append(f)
        self.fields = tuple(no_duplicate_fields)

        if not name.startswith(f'{vocabulary}_'):
            name = f'{vocabulary}_{name}'
        self.name = name

        self.constraints = []

        for field in not_null or []:
            constraint = DataTableNotNullConstraint(field)
            if field in self.fields and not constraint in self.constraints:
                self.constraints.append(constraint)

        for u in unique or []:
            if isinstance(u, str):
                u = (u, )
            constraint = DataTableUniqueConstraint(sorted(u))
            if all(f in self.fields for f in u) \
                and not constraint in self.constraints:
                self.constraints.append(constraint)

    def validate(self, delete=True):
        """Validate the table data.

        This method validate the table data against its
        not null and unique constraints, if any.

        By default, unvalid records are deleted from
        the table. This may be prevented using the
        `delete` parameter.

        Invalid records are returned through the response
        :py:attr:`DataValidationResponse.anomalies` attribute,
        so the parser can handle them.

        Parameters
        ----------
        delete : bool, default True
            If ``True``, unvalid records will be deleted
            from the table.
        
        Returns
        -------
        DataValidationResponse

        """
        if not self.constraints:
            return DataValidationResponse()

        anomalies = []

        known = {
            c: [] for c in self.constraints
            if isinstance(c, DataTableUniqueConstraint)
        }
        for item in self:
            for constraint in self.constraints:
                if isinstance(constraint, DataTableNotNullConstraint):
                    if not item[constraint]:
                        anomalies.append(DataValidationAnomaly(item, constraint))
                if isinstance(constraint, DataTableUniqueConstraint):
                    t = tuple(item[f] for f in constraint)
                    if t in known[constraint]:
                        anomalies.append(DataValidationAnomaly(item, constraint))
                    else:
                        known[constraint].append(t)

        if delete:
            for anomalie in anomalies:
                if anomalie in self:
                    # item might have been deleted already if more than
                    # one anomaly
                    self.remove(anomalie)
                    # for completely duplicated lines, this will leave only
                    # the last one

        return DataValidationResponse(anomalies)

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
        >>> table = VocabularyDataTable(
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

class VocabularyDataCluster(dict):
    """Vocabulary data cluster.

    This class is meant to organise parsed vocabulary prior to
    database storage.

    A :py:class:`VocabularyDataCluster` is a dictionnary. Its keys are
    database table names. Its values :py:class:`VocabularyDataTable`
    are objects containing the data to be loaded into said
    tables.

    The labels' table and the alternative labels' table are
    created during initialization and can be accessed through
    the attributes :py:attr:`VocabularyDataCluster.label` and 
    :py:attr:`VocabularyDataCluster.altlabel`.

    Additionnal tables may be added with :py:meth:`VocabularyDataCluster.table`.

    All tables are accessible through an attribute named after the
    table.

    Parameters
    ----------
    vocabulary : str
        Name of the vocabulary, ie its ``name``
        property in ``vocabularies.yaml``.

    Attributes
    ----------
    label : VocabularyDataTable
        The table containing the vocabulary labels.
        This table has three fields:

        * ``uri`` is the vocabulary item URI.
        * ``language`` is a ISO 639-1 language code
          (2 letter) if possible, else ISO 639-3.
        * ``label`` is the preferred label for the
          language.
        
        Constraints:
        * ``uri`` and ``label`` fields are not empty.
        * the table never contains more than one
          label for a given language and vocabulary.
        
    altlabel : VocabularyDataTable
        The table containing the vocabulary alternative
        labels. Same structure as `label` whithout
        unicity constraint. Alternative labels are
        used to find matching vocabulary items during
        harvest. Users will never see them.
    
    """

    def __init__(self, vocabulary):
        self.vocabulary = vocabulary
        table = VocabularyDataTable(
            self.vocabulary,
            name='label',
            fields=('uri', 'language', 'label'),
            unique=[('uri', 'language')],
            not_null=['uri', 'label']
        )
        self[table.name] = table
        self.label = table
        setattr(self, table.name, table)
        table = VocabularyDataTable(
            self.vocabulary,
            name='altlabel',
            fields=('uri', 'language', 'label'),
            not_null=['uri', 'label']
        )
        self[table.name] = table
        self.altlabel = table
        setattr(self, table.name, table)

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
        >>> cluster = VocabularyDataCluster('somevoc')
        >>> cluster.table('special', ('field_1', 'field_2'))
        'somevoc_special'
        >>> cluster.table('somevoc_special', ('field_1', 'field_2')) is None
        True

        """
        if name in self:
            return
        table = VocabularyDataTable(self.vocabulary, name, fields)
        self[table.name] = table
        setattr(self, table.name, table)
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

