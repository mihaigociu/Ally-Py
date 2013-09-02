'''
Created on Aug 28, 2013

@package: security - role based access control
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

API specifications for RBAC right.
'''

from ally.api.config import prototype, DELETE
from ally.api.option import SliceAndTotal # @UnusedImport
from ally.api.type import Iter
from ally.support.api.util_service import modelId
from security.api.right import QRight, Right
from security.api.right_type import RightType
from security.rbac.api.role import Role, QRole
import abc # @UnusedImport

# --------------------------------------------------------------------

class IRbacPrototype(metaclass=abc.ABCMeta):
    '''
    Rbac prototype service.
    '''
    
    @prototype
    def getRoles(self, identifier:lambda p:p.RBAC, q:QRole=None, **options:SliceAndTotal) -> Iter(Role.Name):
        '''
        Provides the roles for the provided identifier.
        
        @param identifier: object
            The RBAC object identifier to provide the roles for.
        @param q: QRole|None
            The query to apply on the roles.
        @param options: key arguments
            The result iteration options.
        @return: Iterable(Role.Name)
            An iterator containing the role names.
        '''
    
    @prototype
    def getRights(self, identifier:lambda p:p.RBAC, typeName:RightType.Name=None,
                  q:QRight=None, **options:SliceAndTotal) -> Iter(Right.Id):
        '''
        Provides the rights for the provided identifier.
        
        @param identifier: object
            The RBAC object identifier to provide the rights for.
        @param typeName: string|None
            The right type name to provide the rights for, if not provided all rights will be iterated.
        @param q: QRight|None
            The query to apply on the rights.
        @param options: key arguments
            The result iteration options.
        @return: Iterable(Right.Id)
            An iterator containing the rights ids.
        '''
        
    @prototype
    def addRole(self, identifier:lambda p:modelId(p.RBAC), roleName:Role.Name):
        '''
        Add to the RBAC object with identifier the role.
        
        @param identifier: object
            The RBAC object identifier to add the role to.
        @param roleName: string
            The role name to assign to identifier.
        @return: boolean
            True if the role has been added, False otherwise.
        '''
    
    @prototype(method=DELETE)
    def remRole(self, identifier:lambda p:modelId(p.RBAC), roleName:Role.Name) -> bool:
        '''
        Remove from the RBAC object with identifier the role. 
        
        @param identifier: object
            The RBAC object identifier to add remove the role from.
        @param roleName: string
            The role name to remove.
        @return: boolean
            True if a role has been removed, False otherwise.
        '''
        
    @prototype
    def addRight(self, identifier:lambda p:modelId(p.RBAC), rightId:Right.Id):
        '''
        Add to the RBAC object with identifier the right.
        
        @param identifier: object
            The RBAC object identifier to add the right to.
        @param rightId: integer
            The right id to assign to identifier.
        '''
    
    @prototype(method=DELETE)
    def remRight(self, identifier:lambda p:modelId(p.RBAC), rightId:Right.Id) -> bool:
        '''
        Remove from the RBAC object with identifier the right.
        
        @param identifier: object
            The RBAC object identifier to add remove the right from.
        @param rightId: integer
            The right id to remove.
        @return: boolean
            True if a right has been removed, False otherwise.
        '''
