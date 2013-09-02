'''
Created on Jun 6, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the node invokers conflicts resolving based on replace for call hint.
'''

from ally.api.operator.type import TypeService, TypeCall
from ally.api.type import typeFor
from ally.container.ioc import injected
from ally.design.processor.attribute import requires, definesIf
from ally.design.processor.context import Context
from ally.design.processor.execution import Abort
from ally.design.processor.handler import HandlerProcessor
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Defined
    hintsCall = definesIf(dict)
    # ---------------------------------------------------------------- Required
    nodes = requires(list)

class Node(Context):
    '''
    The node context.
    '''
    # ---------------------------------------------------------------- Required
    conflicts = requires(dict)

class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Required
    service = requires(TypeService)
    call = requires(TypeCall)
    location = requires(str)
    
# --------------------------------------------------------------------

@injected
class ConflictReplaceHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the node invokers conflicts resolving based on replace for call hint.
    '''
    
    hintName = 'replaceFor'
    # The hint name for the replace for name.
    hintDescription = '(service API class| tuple(service API class)) Used whenever a service call has the same signature with '\
    'another service call and thus require to use the same web address, this allows to explicitly dictate what'\
    'call has priority over another call(s) by providing the class to which the call should be replaced.'
    # The hint description.
    
    def __init__(self):
        assert isinstance(self.hintName, str), 'Invalid hint name %s' % self.hintName
        assert isinstance(self.hintDescription, str), 'Invalid hint description %s' % self.hintDescription
        super().__init__(Node=Node, Invoker=Invoker)

    def process(self, chain, register:Register, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provides the conflict resolving.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register

        if Register.hintsCall in register:
            if register.hintsCall is None: register.hintsCall = {}
            register.hintsCall[self.hintName] = self.hintDescription
            
        if not register.nodes: return
        
        reported, aborted = set(), []
        for node in register.nodes:
            assert isinstance(node, Node), 'Invalid node %s' % node
            if not node.conflicts: continue
            assert isinstance(node.conflicts, dict), 'Invalid conflicts %s' % node.conflicts
            
            for invokers in node.conflicts.values():
                assert  isinstance(invokers, list), 'Invalid invokers %s' % invokers
                byService, solving = {}, []
                for invoker in invokers:
                    assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
                    if not invoker.service or not invoker.call: continue
                    if invoker.service in byService: continue
                    replaces = invoker.call.hints.get(self.hintName)
                    if not replaces: continue
                    if not isinstance(replaces, tuple): replaces = (replaces,)
                    
                    byService[invoker.service] = invoker
                    solving.append((invoker, replaces))
                
                if byService:
                    locations = []
                    for invoker, replaces in solving:
                        locations.append(invoker.location)
                        for clazz in replaces:
                            service = typeFor(clazz)
                            if not isinstance(service, TypeService):
                                log.error('Cannot use invoker because the replace hints are invalid, at:%s, '
                                          'it should be:\n%s', invoker.location, self.hintDescription)
                                aborted.append(invoker)
                                break
                            assert isinstance(service, TypeService), 'Invalid service class %s' % clazz
                            byService.pop(service, None)
                    
                    if not byService:
                        if reported.isdisjoint(locations):
                            log.error('Cannot use invokers because the replace hints are circular among them, at:%s',
                                      ''.join(locations))
                            reported.update(locations)
                        aborted.extend(invokers)
                    else:
                        solved = set(byService)
                        for invoker, replaces in solving:
                            if invoker not in solved: aborted.append(invoker)

        if aborted: raise Abort(*aborted)
