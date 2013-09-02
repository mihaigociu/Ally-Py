'''
Created on Aug 6, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

API specifications for service access.
'''

from .domain_acl import modelACL
from ally.api.config import service, call, query
from ally.api.criteria import AsEqualOrdered, AsLikeOrdered
from ally.api.type import Iter, Dict
from ally.support.api.entity_ided import Entity, IEntityGetService, QEntity, \
    IEntityQueryService
from binascii import crc32
import hashlib

# --------------------------------------------------------------------

class Access(Entity):
    '''
    Contains data required for an ACL access.
        Id -         the id of the access.
        Path -       contains the path that the access maps to. The path contains beside the fixed string
                     names also markers '*' for where dynamic path elements are expected.
        Method -     the method name that this access maps to.
        Shadowing -  the access that this access is actually shadowing, this means that the access path is just a reroute
                     for the shadowing access.
        Shadowed -   the access that this access is shadowed, this means that this access is overridden by the shadow in
                     required cases.
        Priority -   the ACL priority when constructing gateways on it.
        Hash -       the hash that represents the full aspect of the access.
    '''
    Id = int
    Path = str
    Method = str
    Priority = int
    Hash = str

Access.Shadowing = Access
Access.Shadowed = Access
Access = modelACL(Access)

@modelACL(name=Access)
class AccessCreate(Access):
    '''
    Contains data required for creating an ACL access.
        Types -          the types dictionary needs to have entries as there are '*' in the access 'Path' except if access
                         is a shadow in that case the types from the shadowed type will be used, the dictionary
                         key is the position of the '*' starting from 1 for the first '*', and as a value the type name.
        TypesShadowing - the dictionary containing as a key the position of the '*' in the 'Path' and as a value the 
                         the position in the shadowing access type.
        TypesShadowed -  the dictionary containing as a key the position of the '*' in the 'Path' and as a value the 
                         the position in the shadowed access type.
        Properties -     the properties dictionary associated with the access, as a key the property name and as a value
                         the property type name.
                         
    '''
    Types = Dict(int, str)
    TypesShadowing = Dict(int, int)
    TypesShadowed = Dict(int, int)
    Properties = Dict(str, str)

@modelACL(id='Position')
class Entry:
    '''
    The path entry that corresponds to a '*' dynamic path input.
        Position -           the position of the entry in the access path.
        Type -               the type name associated with the path entry.
        Shadowing -          the position that this entry is shadowing.
        Shadowed -           the position of the shadowed entry, also it means that the values belonging to it 
                             will not be actually used by the access path request.
    '''
    Position = int
    Shadowing = int
    Shadowed = int
    Type = str

@modelACL(id='Name')
class Property:
    '''
    The input model property associated with an access.
        Name -            the property name.
        Type -            the type associated with the input model property.
    '''
    Name = str
    Type = str

# --------------------------------------------------------------------

@query(Access)
class QAccess(QEntity):
    '''
    Provides the query for access.
    '''
    path = AsLikeOrdered
    method = AsEqualOrdered
    
# --------------------------------------------------------------------

@service((Entity, Access), (QEntity, QAccess))
class IAccessService(IEntityGetService, IEntityQueryService):
    '''
    The ACL access service provides the means of setting up the access control layer for services.
    '''
    
    @call
    def getEntry(self, accessId:Access, position:Entry) -> Entry:
        '''
        Provides the path dynamic entry for access and position.
        '''
        
    @call
    def getEntries(self, accessId:Access) -> Iter(Entry.Position):
        '''
        Provides the path dynamic entries for access.
        '''
        
    @call
    def getProperty(self, accessId:Access, name:Property) -> Property:
        '''
        Provides the input property with the provided name and access.
        '''
        
    @call
    def getProperties(self, accessId:Access) -> Iter(Property.Name):
        '''
        Provides the input properties for access.
        '''
    
    @call
    def insert(self, access:AccessCreate) -> Access.Id:
        '''
        Insert the access.
        
        @param access: AccessCreate
            The access to be inserted.
        @return: integer
            The id assigned to the access
        '''
    
    @call
    def delete(self, accessId:Access) -> bool:
        '''
        Delete the access for the provided id.
        
        @param id: integer
            The id of the access to be deleted.
        @return: boolean
            True if the delete is successful, false otherwise.
        '''
        
# --------------------------------------------------------------------

def generateId(path, method):
    '''
    Generates a unique id for the provided path and method.
    
    @param path: string
        The path to generate the id for.
    @param method: string
        The method name.
    @return: integer
        The generated hash id.
    '''
    assert isinstance(path, str), 'Invalid path %s' % path
    assert isinstance(method, str), 'Invalid method %s' % method
    return crc32(method.strip().upper().encode(), crc32(path.strip().strip('/').encode(), 0))

def generateHash(access):
    '''
    Generates hash for the provided access create.
    
    @param access: AccessCreate
        The access to generate the has for.
    @return: string
        The generated hash.
    '''
    assert isinstance(access, AccessCreate), 'Invalid access %s' % access
    
    hashAcc = hashlib.md5()
    hashAcc.update(str(generateId(access.Path, access.Method)).encode())
    if access.Shadowing: hashAcc.update(str(access.Shadowing).encode())
    if access.Shadowed: hashAcc.update(str(access.Shadowed).encode())
    if access.Types:
        for position in sorted(access.Types):
            hashAcc.update(('%s:%s' % (position, access.Types[position])).encode())
    if access.TypesShadowing:
        for position in sorted(access.TypesShadowing):
            hashAcc.update(('%s:%s' % (position, access.TypesShadowing[position])).encode())
    if access.TypesShadowed:
        for position in sorted(access.TypesShadowed):
            hashAcc.update(('%s:%s' % (position, access.TypesShadowed[position])).encode())
    if access.Properties:
        for name in sorted(access.Properties):
            hashAcc.update(('%s:%s' % (name, access.Properties[name])).encode())
    
    return hashAcc.hexdigest().upper()
