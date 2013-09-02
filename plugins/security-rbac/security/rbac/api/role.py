'''
Created on Aug 28, 2013

@package: security - role based access control
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

API specifications for Roles.
'''

from .domain_rbac import modelRbac
from ally.api.config import query, service
from ally.api.criteria import AsLikeOrdered
from ally.support.api.entity_named import Entity, QEntity, IEntityService

# --------------------------------------------------------------------

@modelRbac
class Role(Entity):
    '''
    The role model.
    '''
    Description = str

# --------------------------------------------------------------------

@query(Role)
class QRole(QEntity):
    '''
    Query for role model
    '''
    description = AsLikeOrdered

# --------------------------------------------------------------------

@service((Entity, Role), (QEntity, QRole))
class IRoleService(IEntityService):
    '''
    Role model service API.
    '''