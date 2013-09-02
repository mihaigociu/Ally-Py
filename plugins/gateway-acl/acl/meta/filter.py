'''
Created on Aug 19, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the SQL alchemy meta for ACL filter.
'''

from ..api.filter import Filter
from .acl_intern import WithPath, WithType
from .metadata_acl import Base
from sql_alchemy.support.mapper import validate
from sqlalchemy.dialects.mysql.base import INTEGER
from sqlalchemy.schema import Column
from sqlalchemy.types import String

# --------------------------------------------------------------------

@validate
class FilterMapped(Base, WithPath, WithType, Filter):
    '''
    Provides the ACL filter mapping.
    '''
    __tablename__ = 'acl_filter'
    __table_args__ = dict(mysql_engine='InnoDB')
    
    Name = Column('name', String(255), nullable=False, unique=True)
    # Non REST model attribute --------------------------------------
    id = Column('id', INTEGER(unsigned=True), primary_key=True)
