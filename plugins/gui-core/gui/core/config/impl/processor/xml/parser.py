'''
Created on Aug 22, 2013

@package: gui core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Mihai Gociu

Parses XML files based on digester rules.
'''

from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.xml.context import DigesterArg, prepare
from ally.container.ioc import injected
from ally.design.processor.execution import Chain
from ally.xml.digester import Node, DigesterError
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Solicit(Context):
    '''
    The solicit context.
    '''
    # ---------------------------------------------------------------- Defined
    repository = defines(Context, doc='''
    @rtype: Context
    The parsed repository.
    ''')
    # ---------------------------------------------------------------- Required
    file = requires(str)

# --------------------------------------------------------------------

@injected
class ParserHandler(HandlerProcessor):
    '''
    Implementation for a processor that parses XML files based on digester rules.
    '''
    
    rootNode = Node
    # The root node to use for parsing.
    
    def __init__(self):
        assert isinstance(self.rootNode, Node), 'Invalid node %s' % self.rootNode
        super().__init__(**prepare(self.rootNode))
        
        self._inError = False

    def process(self, chain, solicit:Solicit, Repository:Context, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Parse the solicited files.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(solicit, Solicit), 'Invalid solicit %s' % solicit
        
        digester = DigesterArg(chain.arg, self.rootNode)
        digester.stack.append(Repository())
        try:
            digester.parse('utf8', open(solicit.file, 'rb'))
            if self._inError: log.warning('XML parsing OK')
            self._inError = False
        except DigesterError as e:
            if not self._inError: log.error(e)
            self._inError = True
            chain.cancel()
            
        solicit.repository = digester.stack.pop()