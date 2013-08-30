'''
Created on Aug 27, 2013

@package: gui core
@copyright: 2013 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Mihai Gociu

Populates the url rules for XML digester.
'''

from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.design.processor.attribute import defines, requires, attribute
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor, Handler
from ally.xml.digester import Node, Rule
from ally.support.util_context import IPrepare
from ally.design.processor.resolvers import merge

# --------------------------------------------------------------------

class Create(Context):
    '''
    The create context.
    '''
    # ---------------------------------------------------------------- Required
    node = requires(Node)
    
class RepositoryUrl(Context):
    definer = attribute(Context, doc='''
    @rtype: Context
    The definer context for repository. 
    ''')
    urls = defines(list, doc='''
    @rtype: list[str]
    The list of urls.
    ''')

@injected
@setup(Handler, name='urlRule')
class URLRuleHandler(HandlerProcessor):
    '''
    Implementation for a processor that populates the url rules for XML digester.
    '''

    xpath_url = 'URL'; wire.config('xpath_url', doc='''
    @rtype: string
    The url xpath to register with.
    ''') 
    
    def __init__(self):
        assert isinstance(self.xpath_url, str), 'Invalid url xpath %s' % self.xpath_url
        super().__init__()

    def process(self, chain, create:Create, Repository:RepositoryUrl, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Populate the root node.
        '''
        assert isinstance(create, Create), 'Invalid create %s' % create
        assert issubclass(Repository, RepositoryUrl), 'Invalid repository class %s' % Repository
        assert isinstance(create.node, Node), 'Invalid node %s' % create.node
        
        create.node.addRule(URLRule(RepositoryUrl), self.xpath_url)

# --------------------------------------------------------------------
       
class URLRule(Rule, IPrepare):
    #TODO: add comment
    
    class Repository(Context):
        #TODO: add comment
        
        definer = attribute(Context, doc='''
        @rtype: Context
        The definer context for repository. 
        ''')
        urls = defines(list, doc='''
        @rtype: list[string]
        The list of urls.
        ''')
        
    def __init__(self, Repository):
        assert issubclass(Repository, RepositoryUrl), 'Invalid repository class %s' % Repository
        self.Repository = Repository
    
    def prepare(self, resolvers):
        '''
        @see: IVerifier.prepare
        '''
        merge(resolvers, dict(Repository=URLRule.Repository))
    
    def content(self, digester, content):
        '''
        @see: Rule.content
        '''
        assert digester.stack, 'Expected a repository on the digester stack'
        repository = digester.stack[-1]
        assert isinstance(repository, RepositoryUrl), 'Invalid repository class %s' % repository
        
        content = content.strip()
        if content:
            if repository.urls == None: repository.urls = []
            repository.urls.append(content)