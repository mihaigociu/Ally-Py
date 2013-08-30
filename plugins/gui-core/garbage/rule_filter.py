'''
Created on Aug 22, 2013

@package: gui core
@copyright: 2013 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Mihai Gociu

Populates the filter rules for XML digester.
'''

from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.core.error import DevelError
from ally.design.processor.attribute import defines, requires, attribute
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor, Handler
from ally.xml.digester import Node, Rule, Digester

# --------------------------------------------------------------------

class Create(Context):
    '''
    The create context.
    '''
    # ---------------------------------------------------------------- Required
    node = requires(Node)

class RepositoryFilter(Context):
    '''
    The repository context.
    '''
    # ---------------------------------------------------------------- Defined
    definer = attribute(Context, doc='''
    @rtype: Context
    The definer context for repository. 
    ''')
    filters = defines(list, doc='''
    @rtype: list[str]
    The list of filters.
    ''')
    methods = defines(list, doc='''
    @rtype: list[str]
    The list of methods.
    ''')
    urls = defines(list, doc='''
    @rtype: list[str]
    The list of urls.
    ''')

# --------------------------------------------------------------------

@injected
@setup(Handler, name='filterRule')
class FilterRuleHandler(HandlerProcessor):
    '''
    Implementation for a processor that populates the filter rules for XML digester.
    '''

    xpath_filter = 'Allows'; wire.config('xpath_filter', doc='''
    @rtype: string
    The filter xpath to register with. 
    ''')
    
    def __init__(self):
        assert isinstance(self.xpath_filter, str), 'Invalid filter xpath %s' % self.xpath_filter
        super().__init__()

    def process(self, chain, create:Create, Repository:RepositoryFilter, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Populate the root node.
        '''
        assert isinstance(create, Create), 'Invalid create %s' % create
        assert issubclass(Repository, RepositoryFilter), 'Invalid repository class %s' % Repository
        assert isinstance(create.node, Node), 'Invalid node %s' % create.node
        
        create.node = create.node.addRule(FilterRule(RepositoryFilter), self.xpath_filter)

# --------------------------------------------------------------------

class FilterRule(Rule):
    #TODO: add comments
    
    def __init__(self, Repository):
        assert issubclass(Repository, RepositoryFilter), 'Invalid repository class %s' % Repository
        self.Repository = Repository
        
    def begin(self, digester, **attributes):
        '''
        @see: Rule.begin
        '''
        assert isinstance(digester, Digester), 'Invalid digester %s' % digester
        assert digester.stack, 'Expected a repository on the digester stack'
        repository = digester.stack[-1]
        assert isinstance(repository, RepositoryFilter), 'Invalid repository %s' % repository
        
        if 'filter' not in attributes:
            raise DevelError('A filter attribute is required at line %s and column for \'%s\'' % 
                             (digester.getLineNumber(), digester.getColumnNumber(), digester.currentName()))
        
        if not repository.filters: repository.filters = []
        repository.filters.extend([f.strip() for f in attributes.get('filter', '').split(',') if f])
        
        if repository.methods == None: repository.methods = []
        repository.methods.extend([m.strip() for m in attributes.get('methods', '').split(',') if m])
        
    def end(self, node, digester):
        '''
        @see: Rule.end
        '''
        assert digester.stack, 'Invalid stack %s' % digester.stack
        repository = digester.stack[-1]
        assert isinstance(repository, RepositoryFilter)
        print(repository.filters, repository.methods, repository.urls)
        repository.filters, repository.methods, repository.urls = [], [], []
        

