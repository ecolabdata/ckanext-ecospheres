
import json, sqlalchemy
from pathlib import Path
import os
from ckanext import __path__ as ckanext_path
from sqlalchemy import create_engine

SQL_SCHEMA = 'vocabulary'
SQL_METADATA = sqlalchemy.MetaData(schema=SQL_SCHEMA)

try:
    DB=os.environ.get("CKAN_SQLALCHEMY_URL")
except:
    raise ValueError("CKAN_SQLALCHEMY_URL is missing")

engine=create_engine(DB)
SQL_METADATA.bind=engine


class DataConstraint:
    """Constraint.

    This is an abstract class.
    All table constraints and cross-table constraints are
    subclasses of this class.
    
    """

class TableConstraint(DataConstraint):
    """Table constraint.
    
    This is an abstract class.
    All table constraints are subclasses of this class.

    """

class TableUniqueConstraint(tuple, TableConstraint):
    """Unique constraint.

    :py:class:`TableUniqueConstraint`
    objects are tuples of table fields.

    Parameters
    ----------
    fields : tuple(str)
        A tuple of fields' names whose values should
        be unique in the context of the table.
    none_as_value : bool, default True
        ``False`` if a ``None``value should match any
        value  or ``True`` if it should only match
        ``None``.

    Attributes
    ----------
    none_as_value : bool
        ``False`` if a ``None``value matches any
        value  or ``True`` if it only matches
        ``None``.

    """
    def __init__(self, fields, none_as_value=False):
        self.none_as_value = none_as_value

    def __repr__(self):
        return '({}) IS UNIQUE'.format(', '.join(f for f in self))

class TableNotNullConstraint(str, TableConstraint):
    """Not null constraint.

    :py:class:`TableUniqueConstraint`
    objects are the names of the fields that should not
    be empty.

    """
    def __repr__(self):
        return f'{self} IS NOT NULL'

class ClusterConstraint(DataConstraint):
    """Cluster constraint.

    This is an abstract class.
    All constraints that may involve more than one
    table - and thus definied on the
    :py:class:`VocabularyDataCluster` object - are
    subclasses of this class.
    
    """

class ClusterReferenceConstraint(ClusterConstraint):
    """Reference constraint.
    
    This is a loose foreign key constraint, that will
    only check that values of the referenced fields are
    included in values of the referencing fields.

    Parameters
    ----------
    referenced_table : VocabularyDataTable
        The referenced table.
    referenced_fields : tuple(str)
        The names of the referenced fields, that should
        be existing fields of the referenced table.
    referencing_table : VocabularyDataTable
        The referencing table.
    referencing_fields : tuple(str)
        The names of the referencing fields, that should
        be existing fields of the referencing table.
    none_as_value : bool, default True
        ``False`` if a ``None``value in a referenced
        field should match any value  or ``True`` if it
        should only match ``None``.

    Attributes
    ----------
    referenced_table : VocabularyDataTable
        The referenced table.
    referenced_fields : tuple(str)
        The names of the referenced fields.
    referencing_table : VocabularyDataTable
        The referencing table.
    referencing_fields : tuple(str)
        The names of the referencing fields.
    none_as_value : bool, default True
        ``False`` if a ``None``value in a referenced
        field should match any value  or ``True`` if it
        should only match ``None``. A ``None`` value
        in a referencing field will only ever
        match a ``None`` value in the referenced
        field.
            
    """
    def __init__(
        self, referenced_table, referenced_fields,
        referencing_table, referencing_fields,
        none_as_value=True
    ):
        self.referenced_table = referenced_table
        if isinstance(referenced_fields, str):
            self.referenced_fields = (referenced_fields,)
        else:
            self.referenced_fields = tuple(referenced_fields)
        
        self.referencing_table = referencing_table
        if isinstance(referencing_fields, str):
            self.referencing_fields = (referencing_fields,)
        else:
            self.referencing_fields = tuple(referencing_fields)
        self.none_as_value = none_as_value

    def __repr__(self):
        return '({}) IS REFERENCED BY ({})'.format(
            ', '.join([
                f'{self.referenced_table.name}.{field}'
                for field in self.referenced_fields
            ]),
            ', '.join([
                f'{self.referencing_table.name}.{field}'
                for field in self.referencing_fields
            ])
        )

class InvalidConstraintError(Exception):
    """Exception raised when trying to set up an invalid constraint."""

class VocabularyDataRow(dict):
    """Row of a vocabulary data table.
    
    A :py:class:`VocabularyDataRow` object is a dictionnary
    whose keys are the names of the table fields and the values
    the data to store in said fields.

    """

class DataValidationAnomaly(VocabularyDataRow):
    """Anomaly detected during validation.

    The dictionnary is the invalid row itself.

    Attributes
    ----------
    table_name : str
        The name of the table the invalid row
        belongs to.
    constraint : TableConstraint
        The constraint that was not respected.
    
    Parameters
    ----------
    row : VocabularyDataRow
        The invalid row.
    table_name : str
        The name of the table the invalid row
        belongs to.
    constraint : DataConstraint
        The constraint that was not respected.

    """
    def __init__(self, row, table_name, constraint):
        self.update(row)
        self.constraint = constraint
        self.table_name = table_name

class DataValidationResponse(list):
    """Result of data validation.

    This is a list of the detected anomalies, if any.

    The boolean value of a :py:class:`DataValidationResponse`
    object is the global result of the validation : ``True``
    if all rows are valid (ie the list is empty), else
    ``False``.

    Attributes
    ----------
    anomalies : list(DataValidationAnomaly)
        List of invalid rows.

    """
    def __bool__(self):
        return len(self) == 0

    def __repr__(self):
        if self:
            return 'data is valid'
        else:
            s = {
                f'{i + 1} - {repr(self[i].constraint)}': self[i]
                for i in range(len(self))
            }
            return 'anomalies:\n{}'.format(
                json.dumps(s, ensure_ascii=False, indent=4)
            )

class VocabularyDataTable(list):
    """Pseudo table with vocabulary data.
    
    This class is meant to organise parsed vocabulary prior to
    database storage. A :py:class:`VocabularyDataTable` object
    contains the data meant for the database table with the same
    name as its attribute :py:attr:`VocabularyDataTable.name`.

    Each item of the list is a :py:class:`VocabularyDataRow`
    object representing a row of the table.

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
        that should be unique across the table. This way
        of setting up unique constraints doesn't allow
        to change the way ``None`` values are handled (they
        will be treated as any other values). If another
        behaviour is needed, the constraint should be set
        up after table creation with the
        :py:meth:`VocabularyDataTable.set_unique_constraint`
        method instead.
    not_null : list(str), optional
        List of fields names that should not be empty.

    Attributes
    ----------
    name : str
        The table name.
    fields : tuple(str)
        Names of the table fields.
    constraints : list(TableConstraint)
        List of the table constraints.
    sql : sqlalchemy.sql.schema.Table or None
        SQL commands to create the table in a database.
        This will be generated automatically for 
        subclasses, else it's ``None`` unless manually
        provided after initialization.

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
            self.set_not_null_constraint(field)

        for fields in unique or []:
            self.set_unique_constraint(fields)

        self.sql = None
        table_key = f'{SQL_SCHEMA}.{self.name}'
        if table_key in SQL_METADATA.tables:
            SQL_METADATA.remove(SQL_METADATA.tables[table_key])

    def set_not_null_constraint(self, field):
        """Declare a field that should not be empty.
        
        This method may be applied multiple times
        for different constraints. It will not have any
        effect if the same constraint is declared
        twice.

        Parameters
        ----------
        field : str
            Name of the field that should not be empty.

        Raises
        ------
        InvalidConstraintError
            If the field is not one of the table's fields.

        """
        if not field or not field in self.fields:
            raise InvalidConstraintError(
                f'Unknown field "{field}".'
            )
        constraint = TableNotNullConstraint(field)
        if not constraint in self.constraints:
            self.constraints.append(constraint)
    
    def set_unique_constraint(self, fields, none_as_value=True):
        """Declare one or more fields that should not contains the same set of values twice.
        
        This method may be applied multiple times
        for different constraints. It will not have any
        effect if the same constraint is declared
        twice.

        Parameters
        ----------
        fields : str or tuple(str)
            A field name or tuple of fields' names whose values
            should be unique in the context of the table.
        none_as_value : bool, default True
            ``False`` if a ``None``value should match any
            value  or ``True`` if it should only match
            ``None``.

        Raises
        ------
        InvalidConstraintError
            If one of the fields doesn't belong in the table.

        """
        if isinstance(fields, str):
            fields = (fields, )
        if not fields:
            raise InvalidConstraintError('Missing fields.')
        if not all(f in self.fields for f in fields):
            raise InvalidConstraintError(
                'At least one unknown field in "({})".'.format(
                    ', '.join(fields)
                )
            )
        constraint = TableUniqueConstraint(
            sorted(fields), none_as_value=none_as_value
            )
        if not constraint in self.constraints:
            self.constraints.append(constraint)

    def exists(self, row_part, start=None, stop=None):
        """Does the table contain a row with matching values for given fields ?
        
        Data is provided through keywords parameters.
        Keywords parameters should use the fields' names
        or the function will return ``False``.

        This method may be really slow on huge tables, since
        there's no indexation.

        This method treats ``None`` as any other value.

        Parameters
        ----------
        row_part : dict or VocabularyDataRow
            Row or part of a row. Keywords should be
            fields' names or the method will return ``False``.
        start : int, optional
            If provided, only rows whose index
            is superior or egal are considered.
        stop : int, optional
            If provided, only rows whose index
            is strictly inferior are considered.

        Returns
        -------
        bool

        Examples
        --------
        >>> table = VocabularyDataTable(
        ...     'somevoc', 'special', ('field_1', 'field_2', 'field_3')
        ... )
        >>> table.add('a', 'b', 'c')
        {'field_1': 'a', 'field_2': 'b', 'field_3': 'c'}
        >>> table.exists({'field_1': 'a', 'field_3': 'c'})
        True
        >>> table.add('b', 'b', 'b')
        {'field_1': 'b', 'field_2': 'b', 'field_3': 'b'}
        >>> table.exists({'field_1': 'b', 'field_3': 'b'}, stop=1)
        False

        """
        if not self or not all(field in self.fields for field in row_part):
            return False
        
        if start is None:
            start = 0
        if stop is None:
            stop = len(self)
        table = self[start:stop]

        return any(
            all(
                row_part[field] == row[field]
                for field in row_part
            ) 
            for row in table
        )

    def validate(self, delete=True):
        """Validate the table data.

        This method validate the table data against its
        not null and unique constraints, if any.

        By default, unvalid rows are deleted from
        the table. This may be prevented using the
        `delete` parameter.

        Invalid rows are returned through the response
        :py:attr:`DataValidationResponse.anomalies` attribute,
        so the parser can handle them.

        Parameters
        ----------
        delete : bool, default True
            If ``True``, unvalid rows will be deleted
            from the table.
        
        Returns
        -------
        DataValidationResponse

        Notes
        -----
        If the :py:attr:`TableUniqueConstraint.none_as_value` attribute
        of a unique constraint is set to ``False``, the validation will
        accept ``[{'field_a': None}, {'field_a': 'value_a'}]``
        but not ``[{'field_a': 'value_a'}, {'field_a': None}]``.
        Therefore the order values have been recorded in the table
        does matter in this case.

        If you wish ``{'field_a': None}`` to be detected as an
        anomaly in any case, you should run this method once,
        then reverse the order of the table and validate the data
        once again:

            >>> table = VocabularyDataTable(
            ...     'somevoc', 'special', ('field_a',)
            ... )
            >>> table.set_unique_constraint('field_a', none_as_value=False)
            >>> table.add(None)
            {'field_a': None}
            >>> table.add('a')
            {'field_a': 'a'}
            >>> table.validate()
            data is valid
            >>> table.reverse()
            >>> table.validate()
            anomalies: [{'field_a': None}]

        If the :py:attr:`TableUniqueConstraint.none_as_value` attribute
        is set to ``True``, both ``[{'field_a': None}, {'field_a': 'value_a'}]``
        and ``[{'field_a': 'value_a'}, {'field_a': None}]`` are valid.

        With unique constraints, only the second (or third, etc.)
        occurence of the set of values is considered an anomaly. The
        first row is not retroactively added to the response nor
        deleted from the table when the duplicate is met.

        """
        anomalies = DataValidationResponse()

        if not self.constraints:
            return anomalies

        for idx in range(len(self)):
            row = self[idx]
            for constraint in self.constraints:
                if isinstance(constraint, TableNotNullConstraint):
                    if row[constraint] in (None, ''):
                        anomalies.append(
                            DataValidationAnomaly(row, self.name, constraint)
                        )
                if isinstance(constraint, TableUniqueConstraint):
                    t = {
                        f: row[f] for f in constraint
                        if constraint.none_as_value
                        or not row[f] is None
                    }
                    if self.exists(t, stop=idx):
                        anomalies.append(
                            DataValidationAnomaly(row, self.name, constraint)
                        )

        if delete:
            for anomalie in anomalies:
                self.reverse()
                if anomalie in self:
                    # row might have been deleted already if more than
                    # one anomaly
                    self.remove(anomalie)
                    # for completely duplicated lines, this will leave only
                    # the last one of the reversed table
                self.reverse()

        return anomalies

    def validate_one(self, row):
        """Validate one data row in the context of the table.

        The provided row should not have been added to the
        table already or unique constraint tests will fail.
        
        Parameters
        ----------
        row : VocabularyDataRow
            The row to validate.

        Returns
        -------
        DataValidationResponse

        """
        anomalies = DataValidationResponse()

        if not self.constraints:
            return anomalies

        for constraint in self.constraints:
            if isinstance(constraint, TableNotNullConstraint):
                if row[constraint] in (None, ''):
                    anomalies.append(
                        DataValidationAnomaly(row, self.name, constraint)
                    )
            if isinstance(constraint, TableUniqueConstraint):
                t = {
                    f: row[f] for f in constraint
                    if constraint.none_as_value
                    or not row[f] is None
                    }
                if self.exists(t):
                    anomalies.append(
                        DataValidationAnomaly(row, self.name, constraint)
                    )

        return anomalies

    def build_row(self, *data, **kwdata):
        """Build a proper row from loose data.

        See :py:meth:`VocabularyDataTable.add` for more
        details about the parameters of this method.

        Returns
        -------
        VocabularyDataRow

        """
        row = {f: None for f in self.fields}
        if data:
            data = list(data)
            data.reverse()
            for field in self.fields:
                if not data:
                    break
                row[field] = data.pop()
        if kwdata:
            for field, value in kwdata.items():
                if field in row:
                    row[field] = value
        return row

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
        row = self.build_row(*data, **kwdata)
        self.append(row)
        return row


class VocabularyLabelTable(VocabularyDataTable):
    """Special table for labels.

    This table has three fields:

    * ``uri`` is the vocabulary item URI.
    * ``language`` is a ISO 639-1 language code
        (2 letter) if possible, else ISO 639-3.
    * ``label`` is the preferred label for the
        language.

    Three constraints are declared and used by data validation
    methods such as :py:meth:`VocabularyDataTable.validate`:

    * ``uri`` can't be empty.
    * ``label`` can't be empty.
    * two rows can't have the sames values for both ``uri``
      and ``language`` (only one label per language).

    Use :py:class:`VocabularyAltLabelTable` instead for
    alternative labels.
    
    Parameters
    ----------
    vocabulary : str
        Name of the vocabulary, ie its ``name``
        property in ``vocabularies.yaml``.

    Attributes
    ----------
    name : str
        The table name. It's always the vocabulary name
        with the suffix ``'_label'``.
    fields : tuple(str)
        Names of the table fields.
    constraints : list(TableConstraint)
        List of the table constraints.
    sql : sqlalchemy.sql.schema.Table or None
        SQL commands to create the table in a database.

    """

    def __init__(
        self, vocabulary
    ):
        super().__init__(
            vocabulary,
            name='label',
            fields=('uri', 'language', 'label'),
            not_null=['uri', 'label']
        )
        self.set_unique_constraint(
            ('uri', 'language'),
            none_as_value=False
        )
        self.sql = sqlalchemy.Table(
            self.name,
            SQL_METADATA,
            sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
            sqlalchemy.Column('uri', sqlalchemy.String, nullable=False, index=True),
            sqlalchemy.Column('language', sqlalchemy.String),
            sqlalchemy.Column('label', sqlalchemy.String, nullable=False, index=True),
            sqlalchemy.UniqueConstraint('uri', 'language')
        )

class VocabularyAltLabelTable(VocabularyDataTable):
    """Special table for alternative labels.
    
    This table has three fields:

    * ``uri`` is the vocabulary item URI.
    * ``language`` is a ISO 639-1 language code
        (2 letter) if possible, else ISO 639-3.
    * ``label`` is the preferred label for the
        language.

    Two constraints are declared and used by data validation
    methods such as :py:meth:`VocabularyDataTable.validate`:

    * ``uri`` can't be empty.
    * ``label`` can't be empty.

    Parameters
    ----------
    vocabulary : str
        Name of the vocabulary, ie its ``name``
        property in ``vocabularies.yaml``.

    Attributes
    ----------
    name : str
        The table name. It's always the vocabulary name
        with the suffix ``'_altlabel'``.
    fields : tuple(str)
        Names of the table fields.
    constraints : list(TableConstraint)
        List of the table constraints.
    sql : sqlalchemy.sql.schema.Table or None
        SQL commands to create the table in a database.

    """

    def __init__(
        self, vocabulary
    ):
        super().__init__(
            vocabulary,
            name='altlabel',
            fields=('uri', 'language', 'label'),
            not_null=['uri', 'label']
        )
        self.sql = sqlalchemy.Table(
            self.name,
            SQL_METADATA,
            sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
            sqlalchemy.Column('uri', sqlalchemy.String, nullable=False, index=True),
            sqlalchemy.Column('language', sqlalchemy.String),
            sqlalchemy.Column('label', sqlalchemy.String, nullable=False, index=True),
            sqlalchemy.Index(f'{self.name}_uri_language_idx', 'uri', 'language')
        )


class VocabularyHierarchyTable(VocabularyDataTable):
    """Special table for parent/child relationships.
    
    This table has two fields:

    * ``parent`` is the parent vocabulary item URI.
    * ``child`` is the child vocabulary item URI.

    Two constraints are declared and used by data validation
    methods such as :py:meth:`VocabularyDataTable.validate`:

    * ``parent`` can't be empty.
    * ``child`` can't be empty.

    Parameters
    ----------
    vocabulary : str
        Name of the vocabulary, ie its ``name``
        property in ``vocabularies.yaml``.

    Attributes
    ----------
    name : str
        The table name. It's always the vocabulary name
        with the suffix ``'_hierarchy'``.
    fields : tuple(str)
        Names of the table fields.
    constraints : list(TableConstraint)
        List of the table constraints.
    sql : sqlalchemy.sql.schema.Table or None
        SQL commands to create the table in a database.

    """

    def __init__(
        self, vocabulary
    ):
        super().__init__(
            vocabulary,
            name='hierarchy',
            fields=('parent', 'child'),
            not_null=['parent', 'child']
        )
        self.sql = sqlalchemy.Table(
            self.name,
            SQL_METADATA,
            sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
            sqlalchemy.Column('parent', sqlalchemy.String, nullable=False, index=True),
            sqlalchemy.Column('child', sqlalchemy.String, nullable=False, index=True)
        )


class VocabularySynonymTable(VocabularyDataTable):
    """Special table for equivalent URIs.
    
    This table has two fields:

    * ``uri`` is the vocabulary item URI.
    * ``synonym`` is the equivalent URI.

    Two constraints are declared and used by data validation
    methods such as :py:meth:`VocabularyDataTable.validate`:

    * ``uri`` can't be empty.
    * ``synonym`` can't be empty.

    Parameters
    ----------
    vocabulary : str
        Name of the vocabulary, ie its ``name``
        property in ``vocabularies.yaml``.

    Attributes
    ----------
    name : str
        The table name. It's always the vocabulary name
        with the suffix ``'_synonym'``.
    fields : tuple(str)
        Names of the table fields.
    constraints : list(TableConstraint)
        List of the table constraints.
    sql : sqlalchemy.sql.schema.Table or None
        SQL commands to create the table in a database.

    """

    def __init__(
        self, vocabulary
    ):
        super().__init__(
            vocabulary,
            name='synonym',
            fields=('uri', 'synonym'),
            not_null=['uri', 'synonym']
        )
        self.sql = sqlalchemy.Table(
            self.name,
            SQL_METADATA,
            sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
            sqlalchemy.Column('uri', sqlalchemy.String, nullable=False, index=True),
            sqlalchemy.Column('synonym', sqlalchemy.String, nullable=False, index=True)
        )


class VocabularyRegexpTable(VocabularyDataTable):
    """Special table for regular expressions (used for mapping).
    
    This table has two fields:

    * ``uri`` is the vocabulary item URI.
    * ``regexp`` is a regular expression that can be used to
      determine if a given text is related to the vocabulary item.

    Two constraints are declared and used by data validation
    methods such as :py:meth:`VocabularyDataTable.validate`:

    * ``uri`` can't be empty.
    * ``regexp`` can't be empty.

    Parameters
    ----------
    vocabulary : str
        Name of the vocabulary, ie its ``name``
        property in ``vocabularies.yaml``.

    Attributes
    ----------
    name : str
        The table name. It's always the vocabulary name
        with the suffix ``'_regexp'``.
    fields : tuple(str)
        Names of the table fields.
    constraints : list(TableConstraint)
        List of the table constraints.
    sql : sqlalchemy.sql.schema.Table or None
        SQL commands to create the table in a database.

    """

    def __init__(
        self, vocabulary
    ):
        super().__init__(
            vocabulary,
            name='regexp',
            fields=('uri', 'regexp'),
            not_null=['uri', 'regexp']
        )
        self.sql = sqlalchemy.Table(
            self.name,
            SQL_METADATA,
            sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
            sqlalchemy.Column('uri', sqlalchemy.String, nullable=False, index=True),
            sqlalchemy.Column('regexp', sqlalchemy.String, nullable=False)
        )


class VocabularySpatialTable(VocabularyDataTable):
    """Special table for bounding box coordinates.
    
    This table has five fields:

    * ``uri`` is the vocabulary item URI.
    * ``westlimit``, ``southlimit``, ``eastlimit``,
      and ``northlimit`` define the bounding box.

    Five constraints are declared and used by data validation
    methods such as :py:meth:`VocabularyDataTable.validate`:

    * ``uri`` can't be empty.
    * ``uri`` is unique.
    * ``westlimit`` can't be empty.
    * ``southlimit`` can't be empty.
    * ``eastlimit`` can't be empty.
    * ``northlimit`` can't be empty.

    Parameters
    ----------
    vocabulary : str
        Name of the vocabulary, ie its ``name``
        property in ``vocabularies.yaml``.

    Attributes
    ----------
    name : str
        The table name. It's always the vocabulary name
        with the suffix ``'_spatial'``.
    fields : tuple(str)
        Names of the table fields.
    constraints : list(TableConstraint)
        List of the table constraints.
    sql : sqlalchemy.sql.schema.Table or None
        SQL commands to create the table in a database.

    """

    def __init__(
        self, vocabulary
    ):
        super().__init__(
            vocabulary,
            name='spatial',
            fields=('uri', 'westlimit', 'southlimit', 'eastlimit', 'northlimit'),
            not_null=['uri', 'westlimit', 'southlimit', 'eastlimit', 'northlimit'],
            unique=['uri']
        )
        self.sql = sqlalchemy.Table(
            self.name,
            SQL_METADATA,
            sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
            sqlalchemy.Column('uri', sqlalchemy.String, nullable=False, unique=True),
            sqlalchemy.Column('westlimit', sqlalchemy.Numeric, nullable=False),
            sqlalchemy.Column('southlimit', sqlalchemy.Numeric, nullable=False),
            sqlalchemy.Column('eastlimit', sqlalchemy.Numeric, nullable=False),
            sqlalchemy.Column('northlimit', sqlalchemy.Numeric, nullable=False)
        )


class VocabularyDataCluster(dict):
    """Vocabulary data cluster.

    This class is meant to organise parsed vocabulary prior to
    database storage.

    A :py:class:`VocabularyDataCluster` is a dictionnary. Its keys are
    database table names. Its values are :py:class:`VocabularyDataTable`
    objects containing the data to be loaded into said tables.

    All tables (ie the :py:class:`VocabularyDataTable` objects) are
    also accessible through attributes named after the table.

    The labels' table and the alternative labels' table are
    created during initialization and can be accessed through
    the attributes :py:attr:`VocabularyDataCluster.label` and 
    :py:attr:`VocabularyDataCluster.altlabel`.

    The methods :py:meth:`VocabularyDataCluster.hierarchy_table`,
    :py:meth:`VocabularyDataCluster.synonym_table`,
    :py:meth:`VocabularyDataCluster.regexp_table` and
    :py:meth:`VocabularyDataCluster.spatial_table` can be used
    to add specific tables to the cluster if they are relevant
    for the vocabulary.

    Custom additionnal tables may be added with 
    :py:meth:`VocabularyDataCluster.table`.

    A cluster has a boolean value of ``False`` when none of its
    tables holds any data.

    Parameters
    ----------
    vocabulary : str
        Name of the vocabulary, ie its ``name``
        property in ``vocabularies.yaml``.

    Attributes
    ----------
    vocabulary : str
        Name of the vocabulary, ie its ``name``
        property in ``vocabularies.yaml``.
    label : VocabularyLabelTable
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
          label for a given language and URI. Alternative
          labels should be stored in the alternative
          labels table, ie
          :py:attr:`VocabularyDataCluster.altlabel`.
          The simplest way not to care about this
          issue would be to add labels in the cluster
          with the :py:meth:`VocabularyDataCluster.add_label`
          method.
    altlabel : VocabularyAltLabelTable
        The table containing the vocabulary alternative
        labels. Same structure as `label` whithout
        unicity constraint. If an entry is created
        in this table for some URI and language, there
        should already be a label for said URI and
        language in the labels table. This rule
        is validated through a reference contraint
        (:py:class:`ClusterReferenceConstraint`).
        The simplest way not to care about this
        issue would be to add labels in the cluster
        with the :py:meth:`VocabularyDataCluster.add_label`
        method.
        Alternative labels are used to find matching vocabulary
        items during harvest. Users will never see them.
    hierarchy : VocabularyHierarchyTable or None
        The table holding the relationships between 
        vocabulary items, if any. This table has to be created
        first with :py:meth:`VocabularyDataCluster.hierarchy_table`
        or this attribute's value will be ``None``.
    synonym : VocabularySynonymTable or None
        The table holding the synonyms for the vocabulary URIs,
        if any. This table has to be created first with
        :py:meth:`VocabularyDataCluster.synonym_table`
        or this attribute's value will be ``None``.
    regexp : VocabularyRegexpTable or None
        The table holding regular expressions to match
        data with the vocabulary URIs, if any. This table
        has to be created first with
        :py:meth:`VocabularyDataCluster.regexp_table`
        or this attribute's value will be ``None``.
    spatial : VocabularySpatialTable or None
        The table holding the coordinates of bounding boxes
        associated to the vocabulary URIs, if any. This
        table has to be created first with
        :py:meth:`VocabularyDataCluster.spatial_table`
        or this attribute's value will be ``None``.
    constraints : list(ClusterConstraint)
        List of cluster constraints, ie constraints
        that may involve more than one table. As for now,
        only reference constraints are implemented.
        Cluster constraints are not defined at the creation
        of the cluster but once all involved tables
        have been added to the cluster, through
        methods such as
        :py:meth`VocabularyDataCluster.set_reference_constraint`.

    """

    def __init__(self, vocabulary):
        self.vocabulary = vocabulary
        table = VocabularyLabelTable(
            self.vocabulary
        )
        self[table.name] = table
        self.label = table
        setattr(self, table.name, table)
        table = VocabularyAltLabelTable(
            self.vocabulary
        )
        self[table.name] = table
        self.altlabel = table
        setattr(self, table.name, table)
        self.constraints = []
        self.set_reference_constraint(
            referenced_table='altlabel',
            referenced_fields=('uri', 'language'),
            referencing_table='label',
            none_as_value=False
        )
        self.altlabel.sql.append_constraint(
            sqlalchemy.ForeignKeyConstraint(
                columns=['uri'],
                refcolumns=[f'{self.label.name}.uri'],
                ondelete='CASCADE',
                onupdate='CASCADE',
                initially=True
            )
        )
        self.hierarchy = None
        self.synonym = None
        self.regexp = None
        self.spatial = None

    def __bool__(self):
        return any(table for table in self.values())

    def table(self, name, fields):
        """Add a custom table and returns its name.

        Be aware that the name of the resulting
        table might differ from the intial one as
        a table name has to be prefixed by the 
        vocabulary name.

        Parameters
        ----------
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

    def hierarchy_table(self):
        """Return the name of the cluster table holding relationships, creating it if needed.

        A hierarchy table has two fields: one for
        the parent's URI, one for the child's. Both
        URIs should exist in the labels table.

        It is a :py:class:`VocabularyHierarchyTable`
        object that can be accessed via the
        :py:attribute:`VocabularyDataCluster.hierarchy`
        attribute of the cluster.

        Returns
        -------
        str
            The name of the hierarchy table.

        """
        if self.hierarchy:
            return self.hierarchy.name
        hierarchy_table = VocabularyHierarchyTable(
            self.vocabulary
        )
        self[hierarchy_table.name] = hierarchy_table
        self.hierarchy = hierarchy_table
        setattr(self, hierarchy_table.name, hierarchy_table)
        self.set_reference_constraint(
            referenced_table=hierarchy_table.name,
            referenced_fields=('parent',),
            referencing_table='label',
            referencing_fields=('uri',)
        )
        self.hierarchy.sql.append_constraint(
            sqlalchemy.ForeignKeyConstraint(
                columns=['parent'],
                refcolumns=[f'{self.label.name}.uri'],
                ondelete='CASCADE',
                onupdate='CASCADE',
                initially=True
            )
        )
        self.set_reference_constraint(
            referenced_table=hierarchy_table.name,
            referenced_fields=('child',),
            referencing_table='label',
            referencing_fields=('uri',)
        )
        self.hierarchy.sql.append_constraint(
            sqlalchemy.ForeignKeyConstraint(
                columns=['child'],
                refcolumns=[f'{self.label.name}.uri'],
                ondelete='CASCADE',
                onupdate='CASCADE',
                                initially=True

            )
        )
        return hierarchy_table.name

    def synonym_table(self):
        """Return the name of the cluster table holding synonyms for URIs (alias), creating it if needed.

        A synonym table has two fields: one for
        the URI, one for the synonym. The URI should
        exist in the labels table, synonym may exist
        but it's not mandatory.

        It is a :py:class:`VocabularySynonymTable`
        object that can be accessed via the
        :py:attribute:`VocabularyDataCluster.synonym`
        attribute of the cluster.

        Returns
        -------
        str
            The name of the synonym table.

        """
        if self.synonym:
            return self.synonym.name
        synonym_table = VocabularySynonymTable(
            self.vocabulary
        )
        self[synonym_table.name] = synonym_table
        self.synonym = synonym_table
        setattr(self, synonym_table.name, synonym_table)
        self.set_reference_constraint(
            referenced_table=synonym_table.name,
            referenced_fields=('uri',),
            referencing_table='label'
        )
        self.synonym.sql.append_constraint(
            sqlalchemy.ForeignKeyConstraint(
                columns=['uri'],
                refcolumns=[f'{self.label.name}.uri'],
                ondelete='CASCADE',
                onupdate='CASCADE',
                                initially=True

            )
        )
        return synonym_table.name

    def regexp_table(self):
        """Return the name of the cluster table holding the regular expressions associated with the vocabulary URIs, creating it if needed.

        A regexp table has two fields: one for
        the URI, one for the regular expression. The
        URI should exist in the labels table.

        It is a :py:class:`VocabularyRegexpTable`
        object that can be accessed via the
        :py:attribute:`VocabularyDataCluster.regexp`
        attribute of the cluster.

        Returns
        -------
        str
            The name of the regexp table.

        """
        if self.regexp:
            return self.regexp.name
        regexp_table = VocabularyRegexpTable(
            self.vocabulary
        )
        self[regexp_table.name] = regexp_table
        self.regexp = regexp_table
        setattr(self, regexp_table.name, regexp_table)
        self.set_reference_constraint(
            referenced_table=regexp_table.name,
            referenced_fields=('uri',),
            referencing_table='label'
        )
        self.regexp.sql.append_constraint(
            sqlalchemy.ForeignKeyConstraint(
                columns=['uri'],
                refcolumns=[f'{self.label.name}.uri'],
                ondelete='CASCADE',
                onupdate='CASCADE',
                                initially=True

            )
        )
        return regexp_table.name

    def spatial_table(self):
        """Return the name of the cluster table holding the coordinates of the bounding boxes associated with the vocabulary URIs, creating it if needed.

        A spatial table has five fields: one for
        the URI, four for the coordinates. The
        URI should exist in the labels table.

        It is a :py:class:`VocabularySpatialTable`
        object that can be accessed via the
        :py:attribute:`VocabularyDataCluster.spatial`
        attribute of the cluster.

        Returns
        -------
        str
            The name of the spatial table.

        """
        if self.spatial:
            return self.spatial.name
        spatial_table = VocabularySpatialTable(
            self.vocabulary
        )
        self[spatial_table.name] = spatial_table
        self.spatial = spatial_table
        setattr(self, spatial_table.name, spatial_table)
        self.set_reference_constraint(
            referenced_table=spatial_table.name,
            referenced_fields=('uri',),
            referencing_table='label'
        )
        self.spatial.sql.append_constraint(
            sqlalchemy.ForeignKeyConstraint(
                columns=['uri'],
                refcolumns=[f'{self.label.name}.uri'],
                ondelete='CASCADE',
                onupdate='CASCADE',
                                initially=True

            )
        )
        return spatial_table.name

    def validate(self, delete=True):
        """Validate the cluster data.

        This method validate the data against all constraints
        defined for the cluster and its tables.

        By default, unvalid rows are deleted from
        the tables. This may be prevented using the
        `delete` parameter.

        Invalid rows are returned through the response
        :py:attr:`DataValidationResponse.anomalies` attribute,
        so the parser can handle them.

        Parameters
        ----------
        delete : bool, default True
            If ``True``, unvalid rows will be deleted
            from the table.
        
        Returns
        -------
        DataValidationResponse

        """
        anomalies = DataValidationResponse()

        if not self.constraints:
            return anomalies
        
        for constraint in self.constraints:

            if isinstance(constraint, ClusterReferenceConstraint):

                fields_map = {
                    constraint.referenced_fields[idx]: constraint.referencing_fields[idx]
                        for idx in range(len(constraint.referenced_fields))
                }

                for row in constraint.referenced_table:
                    row_part = {
                        fields_map[field]: value
                        for field, value in row.items()
                        if field in fields_map and (
                            constraint.none_as_value
                            or value is not None
                        )
                    }
                    if row_part and not constraint.referencing_table.exists(row_part):
                        anomalies.append(
                            DataValidationAnomaly(
                                row,
                                constraint.referenced_table.name,
                                constraint
                            )
                        )

        if delete:
            for anomalie in anomalies:
                if anomalie in self[anomalie.table_name]:
                    # row might have been deleted already if more than
                    # one anomaly
                    self[anomalie.table_name].remove(anomalie)

        for table in self.values():
            anomalies += table.validate(delete=delete)

        return anomalies

    def set_reference_constraint(
        self, referenced_table, referenced_fields,
        referencing_table=None, referencing_fields=None,
        none_as_value=True
    ):
        """Declare table fields that should be referenced by other fields of the cluster.

        This method may be applied multiple times
        for different constraints.

        Parameters
        ----------
        referenced_table : VocabularyDataTable or str
            Either the name of the table containing the fields
            whose values should exist in other fields, or the
            table itself. Shorcuts ``'label'`` (labels table)
            and ``'altlabel'`` (alternative labels table)
            will work as well.
        referenced_fields : str or tuple(str)
            The name of one or several fields of the referenced
            table whose values should exist in other fields (for
            the same row).
        referencing_table : VocabularyDataTable or str, optional
            Either the name of the table containing the fields
            which should hold values of the referenced fields, or
            the table itself. Shorcuts ``'label'`` (labels table)
            and ``'altlabel'`` (alternative labels table)
            will work as well. By default, the referenced table
            is presumed to be the referencing table as well.
        referenced_fields : str or tuple(str), optional
            The name of one or several fields of the referencing
            table that should hold the values of the referenced
            fields. There should be exactly as much referencing
            fields as referenced fields, since each field of 
            `referenced_fields` will be compared with the field
            with the same index in `referencing_fields`.
            Be default, the names of the referencing fields are
            presumed to be the same as the names of the referenced
            fields.
        none_as_value : bool, default False
            ``False`` if a ``None``value in a referenced
            field should match any value  or ``True`` if it
            should only match ``None``.

        Raises
        ------
        InvalidConstraintError
            When some table or field name is unknown, or
            the number of referenced fields doesn't match
            the number of referencing fields.

        """

        if referenced_table == 'label':
            referenced_table = self.label
        elif referenced_table == 'altlabel':
            referenced_table = self.altlabel
        elif isinstance(referenced_table, VocabularyDataTable):
            if not referenced_table in list(self.values()):
                raise InvalidConstraintError(
                    f'Unknown referenced table "{referenced_table.name}".'
                )
        elif referenced_table in self:
            referenced_table = self[referenced_table]
        else:
            raise InvalidConstraintError(
                f'Unknown referenced table "{referenced_table}".'
            )
            
        if referencing_table is None:
            referencing_table = referenced_table
        elif referencing_table == 'label':
            referencing_table = self.label
        elif referencing_table == 'altlabel':
            referencing_table = self.altlabel
        elif isinstance(referencing_table, VocabularyDataTable):
            if not referencing_table in list(self.values()):
                raise InvalidConstraintError(
                    f'Unknown referencing table "{referencing_table.name}".'
                )
        elif referencing_table in self:
            referencing_table = self[referencing_table]
        else:
            raise InvalidConstraintError(
                f'Unknown referencing table "{referencing_table}".'
            )

        if not referenced_fields:
            raise InvalidConstraintError(
                    'Missing referenced fields in referenced table '
                    f'"{referenced_table.name}".'
                )
        if isinstance(referenced_fields, str):
            referenced_fields = (referenced_fields,)
        else:
            referenced_fields = tuple(referenced_fields)
        for field in referenced_fields:
            if not field in referenced_table.fields:
                raise InvalidConstraintError(
                    f'Referenced field "{field}" does not belong '
                    f'in referenced table "{referenced_table.name}".'
                )
        
        if not referencing_fields:
            referencing_fields = referenced_fields
        elif isinstance(referencing_fields, str):
            referencing_fields = (referencing_fields,)
        else:
            referencing_fields = tuple(referencing_fields)
        for field in referencing_fields:
            if not field in referencing_table.fields:
                raise InvalidConstraintError(
                    f'Referencing field "{field}" does not belong '
                    f'in referencing table "{referencing_table.name}".'
                )
        
        constraint = ClusterReferenceConstraint(
            referenced_table, referenced_fields,
            referencing_table, referencing_fields,
            none_as_value=none_as_value
        )
        self.constraints.append(constraint)  

    def add_label(self, *data, **kwdata):
        """Properly add a label in the cluster.
        
        This method will add the label to the labels table
        if there isn't one already for the URI and
        language, else to the alternative labels table.

        See :py:meth:`VocabularyDataTable.add` for
        more details on this method's parameters.

        Data is validated against the tables constraints and
        added only if valid. Cluster constraints are implicitely
        checked as well, since this method is meant to assure
        conformity on this end.

        Returns
        -------
        DataValidationResponse
            If the boolean value of this is ``False``, the
            label has not been added to the cluster.

        Notes
        -----
        Labels without a language tag are stored in the
        alternative labels' table as long as at least
        one other label with or without language tag
        already exists in the labels' table for the URI.
        Therefore, the order the labels are submitted
        matters: if you want the keep the untagged label
        in the labels' table, you should submit it first,
        else you should submit it last.

        """
        label_row = self.label.build_row(*data, **kwdata)
        response = self.label.validate_one(label_row)
        if response:
            self.label.add(*data, **kwdata)
        elif any(
            isinstance(anomaly.constraint, TableNotNullConstraint)
            for anomaly in response
        ):
            # invalid data, and not just because there's
            # already a value for the URI and language
            pass
        else:
            response = self.altlabel.validate_one(label_row)
            self.altlabel.add(*data, **kwdata)
        return response

    def dump(self, dirpath=None):
        """Dump the cluster data as JSON.
        
        Parameters
        ----------
        dirpath : str or pathlib.Path, optional
            Path of the directory were data should be
            stored. The file will be named after the
            vocabulary, with a ``'.json'`` extension.
            If not provided, the file is stored in
            a ``vocabularies`` subdirectory that will be
            created (if not existing already) in the
            parent directory of the extension, ie. the
            GIT root.
        
        """
        if dirpath:
            base_path = Path(dirpath)
        else:
            base_path = Path(ckanext_path[0]).parent / 'vocabularies'
            if not base_path.exists() or not base_path.is_dir():
                base_path.mkdir()
        path = base_path / f'{self.vocabulary}.json'
        with open(path, 'w', encoding='utf-8') as target:
            json.dump(self, target, ensure_ascii=False, indent=4)

