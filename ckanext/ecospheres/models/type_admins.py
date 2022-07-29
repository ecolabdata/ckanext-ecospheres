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

__all__ = ['Typeadmins']

class Typeadmins(DeclarativeBase,DomainObject):
    __tablename__ = 'type_admins'
    code = Column(types.Unicode, primary_key=True) 
    label = Column(types.Unicode, nullable=True) 
        
    @classmethod
    def delete_all(cls):
        cls.Session.query(cls).delete()
        cls.Session.flush()

    
    @classmethod
    def from_data(cls,
                code,
                label,
                  ):
        inst = cls(
                code=code,
                label=label,
                   )
        inst.add()
        cls.Session.commit()
        return inst

    @classmethod
    def _get_data(cls):
        return cls.Session.query(cls).all()