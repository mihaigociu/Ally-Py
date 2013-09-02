'''
Created on Aug 13, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Processor that provides the root URI.
'''

from ally.container.ioc import injected
from ally.design.processor.attribute import defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor

# --------------------------------------------------------------------

class Solicit(Context):
    '''
    The solicit context.
    '''
    # ---------------------------------------------------------------- Defined
    rootURI = defines(str, doc='''
    @rtype: string
    The root URI path to use for generated paths.
    ''')
    
# --------------------------------------------------------------------

@injected
class RootURIHandler(HandlerProcessor):
    '''
    Provides the root URI items to be used for generated paths.
    '''
    
    rootURI = str
    # The root URI to use for generated paths.
    
    def __init__(self):
        assert isinstance(self.rootURI, str), 'Invalid root URI %s' % self.rootURI
        super().__init__()
    
    def process(self, chain, solicit:Solicit, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Populate the roor URI.
        '''
        assert isinstance(solicit, Solicit), 'Invalid solicit %s' % solicit
        solicit.rootURI = self.rootURI.strip('/')
