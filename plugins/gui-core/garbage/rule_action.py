'''
Created on Aug 22, 2013

@package: gui core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Mihai Gociu

Populates the action rules for XML digester.
'''

from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.core.error import DevelError
from ally.design.processor.attribute import defines, requires, attribute, \
    definesIf
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

class RepositoryAction(Context):
    '''
    The repository context.
    '''
    # ---------------------------------------------------------------- Defined
    definer = attribute(Context, doc='''
    @rtype: Context
    The definer context for repository. 
    ''')
    actions = defines(list, doc='''
    @rtype: list[Context]
    The list of actions created.
    ''')
    children = definesIf(list, doc='''
    @rtype: list[Context]
    The list of children repositories.
    ''')
    
class ActionContainer(Context):
    '''
    The action container context.
    '''
    # ---------------------------------------------------------------- Defined
    path = defines(str, doc='''
    @rtype: string
    The action path.
    ''')
    label = defines(str, doc='''
    @rtype: string
    The action label.
    ''')
    script = defines(str, doc='''
    @rtype: string
    The action java script file path.
    ''')
    navBar = defines(str, doc='''
    @rtype: string
    The navigation bar update path.
    ''')
    
# --------------------------------------------------------------------

@injected
@setup(Handler, name='actionRule')
class ActionRuleHandler(HandlerProcessor):
    '''
    Implementation for a processor that populates the action rules for XML digester.
    '''

    xpath_action = 'Action'; wire.config('xpath_action', doc='''
    @rtype: string
    The action xpath to register with. 
    ''')
    
    def __init__(self):
        assert isinstance(self.xpath_action, str), 'Invalid action xpath %s' % self.xpath_action
        super().__init__()

    def process(self, chain, create:Create, Action:ActionContainer, Repository:RepositoryAction, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Populate the root node.
        '''
        assert isinstance(create, Create), 'Invalid create %s' % create
        assert issubclass(Action, ActionContainer), 'Invalid action class %s' % Action
        assert issubclass(Repository, RepositoryAction), 'Invalid repository class %s' % Repository
        assert isinstance(create.node, Node), 'Invalid node %s' % create.node
        
        action = create.node.addRule(ActionRule(Action, Repository), self.xpath_action)
        action.childrens[self.xpath_action] = action

# --------------------------------------------------------------------

class ActionRule(Rule):
    #TODO: add comments
    
    def __init__(self, Action, Repository):
        assert issubclass(Action, ActionContainer), 'Invalid action class %s' % Action
        assert issubclass(Repository, RepositoryAction), 'Invalid repository class %s' % Repository
        self.Action = Action
        self.Repository = Repository
    
    def begin(self, digester, **attributes):
        '''
        @see: Rule.begin
        '''
        assert isinstance(digester, Digester), 'Invalid digester %s' % digester
        assert digester.stack, 'Expected a repository on the digester stack'
        repository = digester.stack[-1]
        assert isinstance(repository, RepositoryAction), 'Invalid repository %s' % repository
        
        #import pdb;pdb.set_trace() 
        
        if 'path' not in attributes:
            raise DevelError('A path attribute is required at line %s and column for \'%s\'' % 
                             (digester.getLineNumber(), digester.getColumnNumber(), digester.currentName()))
        
        action = self.Action()
        assert isinstance(action, ActionContainer), 'Invalid action %s' % action
        action.path, action.label = attributes['path'], attributes.get('label')
        action.script, action.navBar = attributes.get('script'), attributes.get('navbar')
        if 'parent' in attributes: action.path = '%s.%s' % (attributes['parent'], action.path)
        
        if repository.actions is None: repository.actions = []
        repository.actions.append(action)
        
        arepository = self.Repository(definer=action)
        if RepositoryAction.children in repository:
            if repository.children is None: repository.children = []
            repository.children.append(arepository)
        
        digester.stack.append(arepository)
        
    def end(self, node, digester):
        '''
        @see: Rule.end
        '''
        arepository = digester.stack.pop()
        #the parent repository - will move all actions from arepository to parent repository
        prepository = digester.stack[-1]
        
        assert isinstance(arepository, RepositoryAction), 'Invalid repository %s' % arepository
        assert isinstance(arepository.definer, ActionContainer), \
        'Invalid repository definer %s' % arepository.definer
        if arepository.actions:
            for child in arepository.actions:
                assert isinstance(child, ActionContainer), 'Invalid action %s' % child
                if not child.path.startswith(arepository.definer.path):
                    child.path = '%s.%s' % (arepository.definer.path, child.path)
                prepository.actions.append(child)
                    
