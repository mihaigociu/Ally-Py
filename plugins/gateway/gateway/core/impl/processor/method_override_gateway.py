'''
Created on Feb 21, 2013

@package: gateway
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Processor that adds method override to Gateway objects, basically support for @see: MethodOverrideHandler.
'''

from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.design.processor.attribute import requires
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor, Handler
from ally.http.spec.server import HTTP_DELETE, HTTP_POST, HTTP_GET, HTTP_PUT
from ally.support.api.util_service import copyContainer, nameFor
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

@injected
@setup(Handler, name='registerMethodOverride')
class RegisterMethodOverride(HandlerProcessor):
    '''
    Provides the method override gateways, basically support for @see: MethodOverrideHandler.
    '''
    pattern_xmethod_override = 'X\-HTTP\-Method\-Override\\:\s*%s\s*$(?i)'; wire.config('pattern_xmethod_override', doc='''
    The header pattern for the method override, needs to contain '%s' where the value will be placed.
    ''')
    methods_override = {
                        HTTP_DELETE: [HTTP_GET],
                        HTTP_PUT: [HTTP_POST],
                        }; wire.config('methods_override', doc='''
    A dictionary containing as a key the overrided method and as a value the methods that are overriden.
    ''')
                        
    excluded = set([nameFor(Gateway.Methods)])
    # The excluded properties from the method override copy.
    
    def __init__(self):
        '''
        Construct the populate method override filter.
        '''
        assert isinstance(self.pattern_xmethod_override, str), \
        'Invalid method override pattern %s' % self.pattern_xmethod_override
        assert isinstance(self.methods_override, dict), 'Invalid methods override %s' % self.methods_override
        super().__init__()
    
    def process(self, chain, solicit:Solicit, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Adds the method override to gateways.
        '''
        assert isinstance(solicit, Solicit), 'Invalid solicit %s' % solicit
        if solicit.gateways is None: return
        
        gateways, indexed = [], {}
        for gateway in solicit.gateways:
            assert isinstance(gateway, Gateway), 'Invalid gateway %s' % gateway
            gateways.append(gateway)
            if not gateway.Methods: continue
            
            methods, overrides = set(), set()
            for method in gateway.Methods:
                override = self.methods_override.get(method)
                if override:
                    methods.add(method)
                    overrides.update(override)
            
            # If the override methods are already declared as methods we don't need to declare them anymore
            if methods.union(overrides).issubset(gateway.Methods): continue
                
            ogateway = Gateway()
            copyContainer(gateway, ogateway, exclude=self.excluded)
            ogateway.Methods = sorted(overrides)
            if ogateway.Headers is None: ogateway.Headers = []
            for method in methods:
                ogateway.Headers.append(self.pattern_xmethod_override % method)
            
            byPattern = indexed.get(ogateway.Pattern)
            if byPattern is None: byPattern = indexed[ogateway.Pattern] = []
            byPattern.append((overrides, ogateway))
        
        if indexed: solicit.gateways = self.iterOverrides(gateways, indexed)
        else: solicit.gateways = gateways
            
    # ----------------------------------------------------------------
            
    def iterOverrides(self, gateways, indexed):
        '''
        Iterates the gateways and overrides.
        '''
        assert isinstance(gateways, Iterable), 'Invalid gateways %s' % gateways
        assert isinstance(indexed, dict), 'Invalid indexed %s' % indexed
        for gateway in gateways:
            assert isinstance(gateway, Gateway), 'Invalid gateway %s' % gateway
            if gateway.Methods:
                byPattern = indexed.get(gateway.Pattern)
                if byPattern:
                    assert isinstance(byPattern, list), 'Invalid by pattern %s' % byPattern
                    k = 0
                    while k < len(byPattern):
                        overrides, ogateway = byPattern[k]
                        k += 1
                        assert isinstance(overrides, set), 'Invalid overrides %s' % overrides
                        if not overrides.isdisjoint(gateway.Methods):
                            yield ogateway
                            k -= 1
                            del byPattern[k]
                    if not byPattern: indexed.pop(gateway.Pattern)
            
            yield gateway
            
        for byPattern in indexed.values():
            for _overrides, ogateway in byPattern: yield ogateway
