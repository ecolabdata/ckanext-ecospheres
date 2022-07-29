import logging
from ckan.lib.base import config
from ckan.model import Tag, Vocabulary, meta, DomainObject
from sqlalchemy import Column, ForeignKey, Index, and_, or_, orm, types,String
from sqlalchemy.exc import SQLAlchemyError as SAError, IntegrityError
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship

log = logging.getLogger(__name__)


DeclarativeBase = declarative_base(metadata=meta.metadata)

__all__ = ['Themes','Subthemes']

class Themes(DeclarativeBase,DomainObject):
    __tablename__ = 'themes'
    uri = Column(types.Unicode, nullable=True) 
    pref_label = Column(types.Unicode, nullable=True,primary_key=True) 
    broader = Column(types.Unicode, nullable=True) 
    change_note = Column(types.Unicode, nullable=True) 
    definition = Column(types.Unicode, nullable=True) 
    alt_label = Column(postgresql.ARRAY(String), nullable=True) 
    total = Column(types.Numeric, nullable=True,default=0) 
    
    subtheme = relationship("Subthemes",lazy='joined')
    
    
    @classmethod
    def delete_all(cls):
        cls.Session.query(cls).delete()
        cls.Session.flush()

    
    @classmethod
    def from_data(cls,
                uri,
                pref_label,
                alt_label,
                change_note,
                definition,
                  ):
        inst = cls(
                uri=uri,
                pref_label=pref_label,
                change_note=change_note,
                definition=definition,
                alt_label=alt_label,
                   )
        inst.add()
        cls.Session.commit()
        return inst


    @classmethod
    def get_themes(cls):
        return cls.Session.query(cls,Subthemes)\
                   .join(Subthemes,
                         Subthemes.theme_id == cls.pref_label).all()



class Subthemes(DeclarativeBase,DomainObject):
    __tablename__ = 'subthemes'
    id = Column(types.Integer, primary_key=True)
    pref_label = Column(types.Unicode, nullable=True) 
    broader = Column(types.Unicode, nullable=True)  
    uri = Column(types.Unicode, nullable=True)  
    definition = Column(types.Unicode, nullable=True)  
    change_note = Column(types.Unicode, nullable=True)  
    alt_label = Column(postgresql.ARRAY(String), nullable=True)  
    regexp = Column(postgresql.ARRAY(String), nullable=True)  
    total = Column(types.Numeric, nullable=True,default=0) 
    theme_id = Column(types.Unicode, ForeignKey("themes.pref_label"))
    
    
    
    @classmethod
    def from_data(cls,
                  pref_label,
                  broader,
                  definition,
                  alt_label,
                  regexp,
                  theme_id,
                  uri=uri
                  ):
        inst = cls(
                pref_label=pref_label,
                uri=uri,
                broader=broader,
                definition=definition,
                alt_label=alt_label,
                regexp=regexp,
                theme_id=theme_id,
                   )
        inst.add()
        cls.Session.commit()
        return inst
  
    @classmethod
    def delete_all(cls):
        cls.Session.query(cls).delete()
        cls.Session.flush()