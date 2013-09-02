'''
Created on Dec 21, 2012

@package: security - role based access control
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Ioan v. Pocol

Contains the SQL alchemy meta for rbac APIs.
'''

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.schema import Column, ForeignKey
from security.meta.metadata_security import Base
from sqlalchemy.dialects.mysql.base import INTEGER

# --------------------------------------------------------------------

class Rbac(Base):
    '''
    Provides the mapping for base Rbac.
    '''
    __tablename__ = 'rbac'
    __table_args__ = dict(mysql_engine='InnoDB')

    id = Column('id', INTEGER(unsigned=True), primary_key=True)

class WithRbac:
    '''
    Provides the with Rbac definition.
    '''
    __table_args__ = dict(mysql_engine='InnoDB')

    rbacId = declared_attr(lambda cls: Column('fk_rbac_id', ForeignKey(Rbac.id), nullable=True))
