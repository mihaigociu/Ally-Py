'''
Created on Aug 27, 2013

@package: gui core
@copyright: 2013 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Mihai Gociu

Populates the method rules for XML digester.
'''

from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.design.processor.attribute import defines, requires, attribute
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor, Handler
from ally.xml.digester import Node, Rule

# --------------------------------------------------------------------

class Create(Context):
    '''
    The create context.
    '''
    # ---------------------------------------------------------------- Required
    node = requires(Node)
    
class RepositoryMethod(Context):
    definer = attribute(Context, doc='''
    @rtype: Context
    The definer context for repository. 
    ''')
    methods = defines(list, doc='''
    @rtype: list[str]
    The list of methods.
    ''')

@injected
@setup(Handler, name='methodRule')
class MethodRuleHandler(HandlerProcessor):
    '''
    Implementation for a processor that populates the method rules for XML digester.
    '''

    xpath_method = 'Method'; wire.config('xpath_method', doc='''
    @rtype: string
    The method xpath to register with.
    ''') 
    
    def __init__(self):
        assert isinstance(self.xpath_method, str), 'Invalid method xpath %s' % self.xpath_method
        super().__init__()

    def process(self, chain, create:Create, Repository:RepositoryMethod, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Populate the root node.
        '''
        assert isinstance(create, Create), 'Invalid create %s' % create
        assert issubclass(Repository, RepositoryMethod), 'Invalid repository class %s' % Repository
        assert isinstance(create.node, Node), 'Invalid node %s' % create.node
        
        create.node.addRule(MethodRule(RepositoryMethod), self.xpath_method)

# --------------------------------------------------------------------
       
class MethodRule(Rule):
    def __init__(self, Repository):
        assert issubclass(Repository, RepositoryMethod), 'Invalid repository class %s' % Repository
        self.Repository = Repository
    
    def content(self, digester, content):
        '''
        @see: Rule.content
        '''
        assert digester.stack, 'Expected a repository on the digester stack'
        repository = digester.stack[-1]
        assert isinstance(repository, RepositoryMethod), 'Invalid repository class %s' % repository
        
        content = content.strip()
        if content:
            if repository.methods == None: repository.methods = []
            repository.methods.append(content)