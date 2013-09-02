'''
Created on Jun 6, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the node invokers conflicts resolving or error reporting.
'''

from ally.container.ioc import injected
from ally.design.processor.attribute import requires, defines
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
    # ---------------------------------------------------------------- Required
    invokers = requires(list)
    exclude = requires(set)
    nodes = requires(list)
    hintsCall = requires(dict)

class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Defined
    node = defines(Context, doc='''
    @rtype: Context
    The invoker node.
    ''')
    # ---------------------------------------------------------------- Required
    path = requires(list)
    location = requires(str)

class Element(Context):
    '''
    The element context.
    '''
    # ---------------------------------------------------------------- Required
    name = requires(str)
       
class Node(Context):
    '''
    The node context.
    '''
    # ---------------------------------------------------------------- Defined
    invokers = defines(dict)
    # ---------------------------------------------------------------- Required
    conflicts = requires(dict)
    
# --------------------------------------------------------------------

@injected
class ConflictResolveHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the node invokers conflicts resolving or error reporting.
    '''
    
    def __init__(self):
        super().__init__(Invoker=Invoker, Element=Element, Node=Node)

    def process(self, chain, register:Register, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provides the conflict resolving.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        
        if not register.nodes: return
        
        reported, aborted = set(), []
        for node in register.nodes:
            assert isinstance(node, Node), 'Invalid node %s' % node
            if not node.conflicts: continue
            assert isinstance(node.conflicts, dict), 'Invalid conflicts %s' % node.conflicts
            
            for methodHTTP, invokers in node.conflicts.items():
                if not invokers: continue
                assert isinstance(invokers, list), 'Invalid invokers %s' % invokers
                if len(invokers) > 1:
                    locations, address = [], None
                    for invoker in invokers:
                        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
                        if address is None and invoker.path: address = '/'.join(el.name or '*' for el in invoker.path)
                        if invoker.location not in locations: locations.append(invoker.location)
                    aborted.extend(invokers)
                    
                    if reported.isdisjoint(locations):
                        log.error('Cannot use invokers because they have the same web address \'%s\', at:%s',
                                  address, ''.join(locations))
                        reported.update(locations)
                else:
                    if node.invokers is None: node.invokers = {}
                    node.invokers[methodHTTP] = invokers[0]
                    invokers[0].node = node
                    
        if aborted and register.hintsCall:
            available = []
            for hname in sorted(register.hintsCall):
                available.append('\t%s: %s' % (hname, register.hintsCall[hname]))
            log.error('In order to make the invokers available please use one of the call hints:\n%s', '\n'.join(available))
            raise Abort(*aborted)
        