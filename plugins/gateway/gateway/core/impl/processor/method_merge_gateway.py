'''
Created on Aug 13, 2013

@package: gateway
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Processor that merges methods for Gateway objects.
'''

from ally.container.support import setup
from ally.design.processor.attribute import requires
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor, Handler
from ally.support.api.util_service import equalContainer, nameFor
from collections import Iterable
from gateway.api.gateway import Gateway

# --------------------------------------------------------------------

class Solicit(Context):
    '''
    The solicit context.
    '''
    # ---------------------------------------------------------------- Required
    gateways = requires(Iterable)

# --------------------------------------------------------------------

@setup(Handler, name='gatewayMethodMerge')
class GatewayMethodMerge(HandlerProcessor):
    '''
    Provides the merging for methods on Gateway objects.
    '''
    
    excluded = set([nameFor(Gateway.Methods)])
    # The excluded properties from the method merging.
    
    def process(self, chain, solicit:Solicit, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Adds the method override to gateways.
        '''
        assert isinstance(solicit, Solicit), 'Invalid reply %s' % solicit
        if solicit.gateways is None: return
        
        gateways, indexed = [], {}
        for gateway in solicit.gateways:
            assert isinstance(gateway, Gateway), 'Invalid gateway %s' % gateway
            
            add = True
            if gateway.Pattern is not None and gateway.Methods:
                byPattern = indexed.get(gateway.Pattern)
                if byPattern is None: byPattern = indexed[gateway.Pattern] = []
                for sgateway in byPattern:
                    assert isinstance(sgateway, Gateway), 'Invalid gateway %s' % sgateway
                    if equalContainer(gateway, sgateway, exclude=self.excluded):
                        methods = set(gateway.Methods)
                        methods.update(sgateway.Methods)
                        sgateway.Methods = sorted(methods)
                        add = False
                        break
                else: byPattern.append(gateway)
                    
            if add: gateways.append(gateway)
        
        solicit.gateways = gateways
