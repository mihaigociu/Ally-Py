'''
Created on Aug 28, 2013

@package: security - role based access control
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

API specifications for Roles with Rbac.
'''

from .role import IRoleService, Role
from ally.api.config import service, hints
from security.rbac.core.api.rbac import IRbacPrototype


# --------------------------------------------------------------------

@service(('RBAC', Role))
class IRoleRbacService(IRoleService, IRbacPrototype):
    '''
    Role model and Rbac service API.
    '''
hints(IRoleRbacService.getRoles, IRoleRbacService.addRole, IRoleRbacService.remRole, webName='Sub')
