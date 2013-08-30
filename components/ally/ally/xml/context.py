'''
Created on Aug 27, 2013

@package: ally base
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides XML digester extension to be used with contexts.
'''

from .digester import Digester, Node
from ally.support.util_context import IPrepare

# --------------------------------------------------------------------

class DigesterArg(Digester):
    '''
    Extension for @see: Digester that also provides the assembly arguments that the nodes have prepared for.
    '''
    
    def __init__(self, arg, root, **keyargs):
        '''
        Construct the digester arguments support.
        @see: Digester.__init__
        
        @param arg: object
            The chain arguments.
        '''
        assert arg is not None, 'Arguments are expected'
        super().__init__(root, **keyargs)

        self.arg = arg
    
# --------------------------------------------------------------------

def prepare(node, resolvers=None):
    '''
    @param resolvers: dictionary{string, IResolver}|None
        The resolvers to prepare, if not provided an empty dictionary will be used.
    @return: dictionary{string, IResolver}
    '''
    if resolvers is None: resolvers = {}
    assert isinstance(resolvers, dict), 'Invalid resolvers %s' % resolvers
    
    queue, visited = [node], set()
    while queue:
        node = queue.pop()
        assert isinstance(node, Node), 'Invalid node %s' % node
        visited.add(node)
        
        for rule in node.rules:
            if isinstance(rule, IPrepare):
                assert isinstance(rule, IPrepare)
                rule.prepare(resolvers)
                
        queue.extend(child for child in node.childrens.values() if child not in visited)
                
    return resolvers
        
        
    