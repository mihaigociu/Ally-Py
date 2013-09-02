'''
Created on Aug 13, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Implementation for the ACL group based gateways.
'''

from ..api.gateway_acl import IGatewayACLService
from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import defines, requires
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing, FILL_CLASSES
from collections import Iterable

# --------------------------------------------------------------------

class Solicit(Context):
    '''
    The solicit context.
    '''
    # ---------------------------------------------------------------- Defined
    acl = defines(object, doc='''
    @rtype: Iterable(string)
    The groups names to create gateways for.
    ''')
    # ---------------------------------------------------------------- Required
    gateways = requires(Iterable)
    
# --------------------------------------------------------------------

@injected
@setup(IGatewayACLService, name='gatewayACLService')
class GatewayACLService(IGatewayACLService):
    '''
    Implementation for @see: IGatewayACLService that provides the ACL gateways.
    '''
    
    assemblyGroupGateways = Assembly; wire.entity('assemblyGroupGateways')
    # The assembly to be used for generating gateways
    
    def __init__(self):
        assert isinstance(self.assemblyGroupGateways, Assembly), \
        'Invalid assembly gateways %s' % self.assemblyGroupGateways
        
        self._processing = self.assemblyGroupGateways.create(solicit=Solicit)
    
    def getGateways(self, group):
        '''
        @see: IGatewayACLService.getGateways
        '''
        assert isinstance(group, str), 'Invalid group name %s' % group
        
        proc = self._processing
        assert isinstance(proc, Processing), 'Invalid processing %s' % proc
        
        solicit = proc.execute(FILL_CLASSES, solicit=proc.ctx.solicit(acl={group})).solicit
        assert isinstance(solicit, Solicit), 'Invalid solicit %s' % solicit
        return solicit.gateways or ()
