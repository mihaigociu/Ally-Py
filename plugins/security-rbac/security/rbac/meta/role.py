'''
Created on Dec 21, 2012

@package: security - role based access control
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Ioan v. Pocol

Contains the SQL alchemy meta for rbac APIs.
'''

from ..api.role import Role
from .rbac import WithRbac
from .rbac_intern import Rbac
from sql_alchemy.support.mapper import validate
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import String

# --------------------------------------------------------------------

@validate
class RoleMapped(Rbac, WithRbac, Role):
    '''
    Provides the mapping for Role rbac.
    '''
    __tablename__ = 'rbac_role'
    __table_args__ = dict(mysql_engine='InnoDB', mysql_charset='utf8')

    Name = Column('name', String(255), nullable=False, unique=True)
    Description = Column('description', String(255))
    # Non REST model attribute --------------------------------------
    rbacId = Column('fk_rbac_id', ForeignKey(Rbac.id), nullable=True, primary_key=True)
