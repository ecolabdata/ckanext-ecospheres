import os
import logging
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.schema import CreateTable
from sqlalchemy.orm import scoped_session, sessionmaker

from ckanext.ecospheres.vocabulary.index import VocabularyIndex

logger = logging.getLogger(__name__)

try:
    from ckan.plugins.toolkit import config
    DB = config.get_value(
        'sqlalchemy.url'
    )
    logger.warning(f"Couldn't get sqlalchemy.url from ckan.ini")
except:
    DB = os.environ.get("CKAN_SQLALCHEMY_URL")

@contextmanager
def Session(database=DB):
    """Database session context manager.
        
    Parameters
    ----------
    database : str, optional
        URL of the database the vocabulary should be loaded into,
        ie ``dialect+driver://username:password@host:port/database``.
        If not provided, the main CKAN PostgreSQL database will be used.
    
    Yields
    ------
    sqlalchemy.orm.Session
    
    """
    if not database:
        raise ValueError(
            "Missing database URL. "
            "The CKAN_SQLALCHEMY_URL environment variable doesn't exist."
        )
    engine = create_engine(database)
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
    finally:
        session.close()

def __create_table_and_load_data(
    table_name, schema_name, table_schema, data, database=None
):
    """Create a table in the database and load its data.
        
    Parameters
    ----------
    table_name : str
        Table name. This has to be a proper PostgreSQL
        identifier or the table creation will fail.
    schema_name : str
        Schema name (namespace). This has to be a proper
        PostgreSQL identifier or the table creation will
        fail.
    table_schema : sqlalchemy.sql.schema.Table
        Table object.
    data : dict
        Vocabulary data.
    database : str, optional
        URL of the database the vocabulary should be loaded into,
        ie ``dialect+driver://username:password@host:port/database``.
        If not provided, the main CKAN PostgreSQL database will be used.
    
    Returns
    -------
    bool
        ``True`` if the operation was successful.
    
    """
    try:
        with Session(database=database) as s:
            try:
                logger.debug(
                    'Drop table "{0}.{1}"'.format(
                        schema_name, table_name
                    )
                )
                s.execute(
                    'DROP TABLE IF EXISTS {0}.{1} CASCADE'.format(
                        schema_name, table_name
                    )
                )
                logger.debug(
                    'Create table "{0}.{1}"'.format(
                        schema_name, table_name
                    )
                )
                table_creation_sql = CreateTable(table_schema)
                s.execute(table_creation_sql)
                if data:
                    stm = table_schema.insert().values(data)
                    logger.debug(
                        'Insert vocabulary data into "{0}.{1}"'.format(
                            schema_name, table_name
                        )
                    )
                    s.execute(stm)
                return True
            except Exception as e:
                logger.error(
                    'Failed to store table "{0}.{1}" into the database. {2}'.format(
                        schema_name, table_name, str(e)
                    )
                )
                raise # need to raise the exception for the rollback to happen
    except Exception as e:
        logger.error('Database session error. {0}'.format(str(e)))
    return False

def intersection(lst1, lst2):
    return list(set(lst1) & set(lst2))

def load_vocab(vocab_list=None, database=None, **kwargs):
    """ Create table schema and load data for given vocabularies from vocabularies.yaml.

    Parameters
    ----------
    vocab_list : list(str) or str, optional
        A vocabulary name or list of vocabulary names to load into
        the database, ie their ``name`` property in ``vocabularies.yaml``.
        If not provided, all available vocabularies are loaded.
    database : str, optional
        URL of the database the vocabulary should be loaded into,
        ie ``dialect+driver://username:password@host:port/database``.
        If not provided, the main CKAN PostgreSQL database will be used.
    **kwargs : str
        Keyword parameters passed down to :py:func:`requests.get`,
        such as authentification info, proxy mapping, etc.

    Returns
    -------
    list(str)
        List of the 

    """
    if vocab_list:
        if isinstance(vocab_list, str):
            vocab_list = [vocab_list]
        vocab_to_load = intersection(vocab_list, VocabularyIndex.names())
    else:   
        vocab_to_load = list(VocabularyIndex.names())

    report = []

    for name in vocab_to_load:
        logger.debug(f'Loading vocabulary "{name}"')
        result = VocabularyIndex.load(name, **kwargs)
        if not result: # erreur critique
            logger.critical(
                'Failed to load vocabulary "{0}". {1}'.format(
                    name, str(result.log[-1])
                )
            )
            continue
        if result.status_code !=0: # erreur non critique
            for e in result.log:
                logger.warning(
                    'Anomaly while loading vocabulary "{0}". {1}'.format(
                        name, str(e)
                    )
                )
        vocab_data = result.data

        success = False
        for table_name, table in vocab_data.items():
            if  table.sql is None:
                logging.info(
                    'No SQL definition available for ' f'table "{table_name}" .')
                continue
            success = __create_table_and_load_data(
                table_name=table_name,
                schema_name=table.schema,
                table_schema=table.sql,
                data=table,
                database=database
            )
            if not success:
                # do not try to load other tables when one
                # of them failed
                break
        
        if success:
            report.append(name)
    
    return report
