


from ckanext.ecospheres.vocabulary.index import VocabularyIndex
from sqlalchemy import create_engine
import os
import re
from sqlalchemy import Table, Column, Integer, String, MetaData,select

from sqlalchemy.schema import DropTable, CreateTable
from sqlalchemy.orm import scoped_session, sessionmaker
from contextlib import contextmanager
import logging
from sqlalchemy.schema import MetaData
import ckan.plugins as p

SPECIAL_TABLES=("ecospheres_territory","ecospheres_theme")
REGEX_PATTERN_ECOSPHERE_SPATIAL = r'.*ecospheres_territory_spatial.*'
REGEX_PATTERN_ECOSPHERE_HIERARCHY = r'.*ecospheres_theme_hierarchy.*'
REGEX_PATTERN_ECOSPHERE_REGEX = r'.*ecospheres_theme_regexp.*'



logger = logging.getLogger(__name__)




engine = create_engine(os.environ.get("CKAN_SQLALCHEMY_URL"))
metadata = MetaData()
DB=os.environ.get("CKAN_SQLALCHEMY_URL")

@contextmanager
def Session(database):

    try:
        Session = scoped_session(sessionmaker(
            bind=create_engine(database)))
        session = Session()
        yield session
        session.commit()
    except Exception as e:
        print("Error sending session",str(e))
        session.rollback()
        raise
    finally:
        session.close()


def _get_generic_schema(table_name):
    return Table(table_name, metadata,
                        Column('id', Integer, primary_key=True),
                        Column('uri', String, nullable=True),
                        Column('label', String ,nullable=True),
                        Column('language', String, nullable=True),
                        extend_existing=True,
                    )

def _get_hierarchy_schema_table(table_name):
    return Table(table_name, metadata,
                        Column('parent', String),
                        Column('child', String),
                        extend_existing=True,
                    )
def _get_regex_schema_table(table_name):
    return Table(table_name, metadata,
                        Column('uri', String),
                        Column('regexp', String),
                        extend_existing=True,
                    )

def _get_spatial_schema_table(table_name):
    return Table(table_name, metadata,
                        Column('uri', String),
                        Column('westlimit', String),
                        Column('southlimit', String),
                        Column('eastlimit', String),
                        Column('northlimit', String),
                        extend_existing=True,
    )

def __create_generique_label_schema_table(table_name,table_schema,data):
    try:
        with Session(database=DB) as s:
            try:
                logger.info(f"purge de la table : {table_name}")
                s.execute('drop table if exists {}'.format(table_name))                

                logger.info(f"Création de la table : {table_name}")
                table_creation_sql = CreateTable(table_schema)
                s.execute(table_creation_sql)
                stm=table_schema.insert().values(data[table_name])
                logging.info(f"Insetion des données dans la table {table_name}")
                s.execute(stm)
            except Exception as e:
                logging.error(f"Erreur lors de la création du table {table_name}\t {str(e)}")

        return table_schema

    except Exception as e:
        print(e)
        raise Exception(f"Erreur lors de la creation de la table {table_name}")





def load_vocab():

    for name in VocabularyIndex.names():       
        try:
            vocab_data=VocabularyIndex.load_and_dump(name).data
            if not vocab_data:
                raise Exception(f"Erreur lors du chargement du vocabulaire {name}")
                continue
            for table_name in vocab_data.keys():
                
                if re.match(REGEX_PATTERN_ECOSPHERE_SPATIAL,table_name):
                    _table=_get_spatial_schema_table(table_name)
                elif re.match(REGEX_PATTERN_ECOSPHERE_HIERARCHY,table_name):
                    _table=_get_hierarchy_schema_table(table_name)
                elif re.match(REGEX_PATTERN_ECOSPHERE_REGEX,table_name):
                    _table=_get_regex_schema_table(table_name)
                else:
                    _table = _get_generic_schema(table_name)
                
                __create_generique_label_schema_table(table_name,table_schema=_table,data=vocab_data)    
    
        except Exception as e:
            print("Erreur pendant le chargement des vocabulaires",str(e))




