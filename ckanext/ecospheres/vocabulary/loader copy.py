


from ckanext.ecospheres.vocabulary.index import VocabularyIndex
from sqlalchemy import Table, Column, Integer, String, MetaData
from ckan.model import  meta
from ckan.model.meta import Session
from sqlalchemy import create_engine
import os
import re

from sqlalchemy.schema import DropTable, CreateTable
from sqlalchemy.orm import scoped_session, sessionmaker


from contextlib import contextmanager

SPECIAL_TABLES=("ecospheres_territory","ecospheres_theme")
REGEX_PATTERN_ECOSPHERE = r'^ecospheres.*$'
class LOADER:

    connection=Session.connection()
    engine = create_engine(os.environ.get("CKAN_SQLALCHEMY_URL"))
    metadata = MetaData()

    
    @classmethod
    def __create_label_schema_table(cls,table_name):
        try:
            _table = Table(table_name, cls.metadata,
                            Column('id', Integer, primary_key=True),
                            Column('uri', String, nullable=False),
                            Column('label', String ,nullable=False),
                            Column('language', String, nullable=True),
                            extend_existing=True,
                        )
            if not _table.exists():
                cls.metadata.create_all(engine)
            return _table
        except Exception as e:
            print(str(e))
            raise Exception(f"Erreur lors de la creation de la table {table_name}")



    @classmethod
    def __load_data_into_bdd(cls,vocab_data,table_name,_table):
        #Suppression des données
        print(f"Insertion des données dans la table:\t {table_name}") 
        cls.connection.execute(
                _table.delete()
                )
        stm=_table.insert().values(vocab_data[table_name])
        cls.connection.execute(stm)
        Session.commit()



    @classmethod
    def load_vocab(cls):
        for name in VocabularyIndex.names():
            
            try:
                vocab_data=VocabularyIndex.load_and_dump(name).data
                if not vocab_data:
                    raise Exception(f"Erreur lors du chargement du vocabulaire {name}")
                    continue


                for table_name in vocab_data.keys():

                    #creation de la table en bdd si elle n'existe pas 
                    if re.match(REGEX_PATTERN_ECOSPHERE,table_name):
                        
                        pass

                    else:
                        """ Vocabulaires génériques """    
                        _table=cls.__create_label_schema_table(table_name=table_name)
                        print("table: ",type(_table))
                        cls.__load_data_into_bdd(vocab_data,table_name,_table)
            except Exception as e:
                print("Erreur ",str(e))

        import os
        print(os.environ.get("CKAN_SQLALCHEMY_URL"))