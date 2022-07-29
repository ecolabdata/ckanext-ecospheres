#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from ckan.lib.base import config
from ckan.model import Tag, Vocabulary, meta, DomainObject
from sqlalchemy import Column, ForeignKey, Index, and_, or_, orm, types
from sqlalchemy.exc import SQLAlchemyError as SAError, IntegrityError
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from ckan.model import Session, meta

log = logging.getLogger(__name__)


DeclarativeBase = declarative_base(metadata=meta.metadata)

__all__ = ['Territories']

class Territories(DeclarativeBase, DomainObject):
    __tablename__ = 'territories'
    id = Column(types.Integer, primary_key=True)
    type_region = Column(types.Unicode, nullable=True) #
    name = Column(types.Unicode, nullable=True) #le nom officiel en français
    codeRegion = Column(types.Unicode, nullable=True, unique=True) #code à 3 caractères de la région à laquelle le département appartient
    uriUE = Column(types.Unicode, nullable=True) #URI de l'Union Européenne"
    westlimit = Column(types.Numeric, nullable=True) #longitude minimum en degrés décimaux en WGS84
    southlimit = Column(types.Numeric,nullable=True) #latitude minimum en degrés décimaux en WGS84
    eastlimit = Column(types.Numeric, nullable=True) #longitude maximum en degrés décimaux en WGS84
    northlimit = Column(types.Numeric, nullable=True) #latitude maximum en degrés décimaux en WGS84



    @classmethod
    def from_data(cls,
                  type_region,
                  name,
                  codeRegion,
                  uriUE,
                  westlimit,
                  southlimit,
                  eastlimit,
                  northlimit):
        inst = cls(type_region=type_region,
                   name=name,
                   codeRegion=codeRegion,
                   uriUE=uriUE,
                   westlimit=westlimit,
                   southlimit=southlimit,
                   eastlimit=eastlimit,
                   northlimit=northlimit)
        inst.add()
        cls.Session.commit()
        return inst

        
    @classmethod
    def by_code_region(cls, code_region):
        query = meta.Session.query(cls)\
            .filter(cls.codeRegion == code_region)\
            .autoflush(True)

        return query.first()

    @classmethod
    def delete_all(cls):
        cls.Session.query(cls).delete()
        cls.Session.flush()
