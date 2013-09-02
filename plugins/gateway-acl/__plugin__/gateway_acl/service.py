'''
Created on Jan 9, 2012

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the services for ACL.
'''
    
from ..gateway.service import updateAssemblyAnonymousGateways, \
    assemblyAnonymousGateways, gatewayMethodMerge, registerMethodOverride
from ..plugin.registry import registerService
from .database import binders
from acl.api.group import IGroupService
from acl.core.impl.processor.gateway.acl_permission import \
    RegisterAclPermissionHandler
from acl.core.impl.processor.gateway.root_uri import RootURIHandler
from ally.container import ioc, support, bind
from ally.container.support import entityFor
from ally.design.processor.assembly import Assembly
from ally.design.processor.handler import Handler

# --------------------------------------------------------------------

# The gateway processors
anonymousGroup = registerPermissionGateway = support.notCreated  # Just to avoid errors

SERVICES = 'acl.api.**.I*Service'

bind.bindToEntities('acl.impl.**.*Alchemy', 'acl.core.impl.processor.gateway.**.*Alchemy', binders=binders)
support.createEntitySetup('acl.impl.**.*', 'acl.core.impl.processor.gateway.**.*')
support.listenToEntities(SERVICES, listeners=registerService)
support.loadAllEntities(SERVICES)

# --------------------------------------------------------------------

@ioc.config
def root_uri_acl():
    '''
    The prefix used for appending to the Gateway paths.
    '''
    return 'resources'

# --------------------------------------------------------------------

@ioc.entity
def assemblyGroupGateways() -> Assembly:
    ''' The assembly used for generating the group gateways'''
    return Assembly('Group gateways')

# --------------------------------------------------------------------

@ioc.entity
def rootURI() -> Handler:
    b = RootURIHandler()
    b.rootURI = root_uri_acl()
    return b

@ioc.entity
def registerAclPermission() -> Handler:
    b = RegisterAclPermissionHandler()
    b.aclPermissionProvider = entityFor(IGroupService)
    return b

# --------------------------------------------------------------------

@ioc.after(updateAssemblyAnonymousGateways)
def updateAssemblyAnonymousGatewaysForAcl():
    assemblyAnonymousGateways().add(anonymousGroup(), rootURI(), registerAclPermission(), registerPermissionGateway(),
                                    before=gatewayMethodMerge())

@ioc.after(assemblyGroupGateways)
def updateAssemblyGroupGateways():
    assemblyGroupGateways().add(registerAclPermission(), rootURI(), registerPermissionGateway(), gatewayMethodMerge(),
                                registerMethodOverride())
