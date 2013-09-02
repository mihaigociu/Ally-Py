'''
Created on Jan 28, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the SQL alchemy meta for ACL access.
'''

from ..api.access import Access, Entry, Property
from .acl_intern import WithMethod, WithPath, WithType
from .metadata_acl import Base
from sql_alchemy.support.mapper import validate
from sqlalchemy.dialects.mysql.base import INTEGER
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.schema import Column, ForeignKey, UniqueConstraint
from sqlalchemy.types import String

# --------------------------------------------------------------------

@validate
class AccessMapped(Base, WithPath, WithMethod, Access):
    '''
    Provides the ACL access mapping.
    '''
    __tablename__ = 'acl_access'
    __table_args__ = (UniqueConstraint('fk_path_id', 'fk_method_id', name='uix_acl_access'), dict(mysql_engine='InnoDB'))
    
    Id = Column('id', INTEGER(unsigned=True), autoincrement=False, primary_key=True)
    Priority = association_proxy('path', 'priority')
    Shadowing = Column('fk_shadowing_id', ForeignKey('acl_access.id', ondelete='CASCADE'))
    Shadowed = Column('fk_shadowed_id', ForeignKey('acl_access.id', ondelete='CASCADE'))
    Hash = Column('hash', String(50), nullable=False, unique=True)
    
@validate
class EntryMapped(Base, WithType, Entry):
    '''
    Provides the ACL access entry mapping.
    '''
    __tablename__ = 'acl_access_entry'
    __table_args__ = (UniqueConstraint('fk_access_id', 'position', name='uix_acl_access_entry'), dict(mysql_engine='InnoDB'))
    
    Position = Column('position', INTEGER(unsigned=True))
    Shadowing = Column('shadowing_position', INTEGER(unsigned=True))
    Shadowed = Column('shadowed_position', INTEGER(unsigned=True))
    # Non REST model attribute --------------------------------------
    id = Column('id', INTEGER(unsigned=True), primary_key=True)
    accessId = Column('fk_access_id', ForeignKey(AccessMapped.Id, ondelete='CASCADE'), nullable=False)
    
@validate
class PropertyMapped(Base, WithType, Property):
    '''
    Provides the ACL access property mapping.
    '''
    __tablename__ = 'acl_access_property'
    __table_args__ = (UniqueConstraint('fk_access_id', 'name', name='uix_acl_access_property'), dict(mysql_engine='InnoDB'))
    
    Name = Column('name', String(255))
    # Non REST model attribute --------------------------------------
    id = Column('id', INTEGER(unsigned=True), primary_key=True)
    accessId = Column('fk_access_id', ForeignKey(AccessMapped.Id, ondelete='CASCADE'), nullable=False)
    
