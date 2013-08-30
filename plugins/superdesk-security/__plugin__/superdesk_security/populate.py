'''
Created on Sep 9, 2012

@package: superdesk user
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the default data for the user plugin.
'''

from ..security_rbac.populate import NAME_ROOT
from ally.container import support, app
from security.rbac.api.rbac import IRoleService
from superdesk.security.api.user_rbac import IUserRbacService
from superdesk.user.api.user import IUserService, User, QUser
import hashlib

# --------------------------------------------------------------------
     
@app.populate
def populateRootUser():
    userService = support.entityFor(IUserService)
    assert isinstance(userService, IUserService)
    userRbacService = support.entityFor(IUserRbacService)
    assert isinstance(userRbacService, IUserRbacService)
    roleService = support.entityFor(IRoleService)
    assert isinstance(roleService, IRoleService)
    
    users = userService.getAll(limit=1, q=QUser(name='root'))
    if not users:
        user = User()
        user.Name = 'root'
        user.Password = hashlib.sha512(b'root').hexdigest()
        user.Id = userService.insert(user)
    else: user = users[0]
    
    userRbacService.assignRole(user.Id, roleService.getByName(NAME_ROOT).Id)
