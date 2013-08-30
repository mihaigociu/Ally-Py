
from ally.design.processor.attribute import attribute, defines
from ally.design.processor.context import Context
from ally.design.processor.resolvers import merge
from ally.support.util_context import IPrepare
from ally.xml.digester import Rule, Digester
from ally.xml.context import DigesterArg
from ally.core.error import DevelError

# --------------------------------------------------------------------

class WithTracking(Context):
    '''
    Context class with tracking info.
    '''
    lineNumber = attribute(int, doc='''
    @rtype: int
    The starting line number for this element in the configuration file. 
    ''')
    colNumber = attribute(int, doc='''
    @rtype: int
    The starting column number for this element in the configuration file. 
    ''')

def trackOn(digester, context):
    '''
    Will set the tracking attributes on context
    '''
    assert isinstance(digester, Digester), 'Invalid digester %s' % digester
    assert isinstance(context, WithTracking), 'Invalid context %s' % context
    
    context.lineNumber, context.colNumber = digester.getLineNumber(), digester.getColumnNumber()

# --------------------------------------------------------------------

class ActionRule(Rule, IPrepare):
    '''
    Digester rule for extracting actions from the xml configuration file.
    '''
    
    class Repository(Context):
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
        
    class Action(WithTracking):
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
    
    def prepare(self, resolvers):
        '''
        @see: IVerifier.prepare
        '''
        merge(resolvers, dict(Repository=ActionRule.Repository, Action=ActionRule.Action))
    
    def begin(self, digester, **attributes):
        '''
        @see: Rule.begin
        '''
        assert isinstance(digester, DigesterArg), 'Invalid digester %s' % digester
        assert issubclass(digester.arg.Repository, ActionRule.Repository), \
        'Invalid repository class %s' % digester.arg.Repository
        assert issubclass(digester.arg.Action, ActionRule.Action), \
        'Invalid repository class %s' % digester.arg.Repository
        
        assert digester.stack, 'Expected a repository on the digester stack'
        repository = digester.stack[-1]
        assert isinstance(repository, ActionRule.Repository), 'Invalid repository %s' % repository
        
        if 'path' not in attributes:
            raise DevelError('A path attribute is required at line %s and column for \'%s\'' % 
                             (digester.getLineNumber(), digester.getColumnNumber(), digester.currentName()))
        
        action = digester.arg.Action()
        assert isinstance(action, ActionRule.Action), 'Invalid action %s' % action
        action.path, action.label = attributes['path'], attributes.get('label')
        action.script, action.navBar = attributes.get('script'), attributes.get('navbar')
        if 'parent' in attributes: action.path = '%s.%s' % (attributes['parent'], action.path)
        
        trackOn(digester, action)
        
        if repository.actions is None: repository.actions = []
        repository.actions.append(action)
        
        digester.stack.append(digester.arg.Repository(definer=action))
        
    def end(self, node, digester):
        '''
        @see: Rule.end
        '''
        assert isinstance(digester, DigesterArg), 'Invalid digester %s' % digester
        arepository = digester.stack.pop()
        #the parent repository - will move all actions from arepository to parent repository
        prepository = digester.stack[-1]
        
        assert isinstance(arepository, ActionRule.Repository), 'Invalid repository %s' % arepository
        assert isinstance(arepository.definer, ActionRule.Action), \
        'Invalid repository definer %s' % arepository.definer
        if arepository.actions:
            for child in arepository.actions:
                assert isinstance(child, ActionRule.Action), 'Invalid action %s' % child
                if not child.path.startswith(arepository.definer.path):
                    child.path = '%s.%s' % (arepository.definer.path, child.path)
                prepository.actions.append(child)


class AccessRule(Rule, IPrepare):
    '''
    Digester rule for extracting Access nodes from the xml configuration file.
    '''
    
    class Repository(Context):
        '''
        The repository context.
        '''
        # ---------------------------------------------------------------- Defined
        accesses = defines(list, doc='''
        @rtype: list[Context]
        ''')
    
    class Access(WithTracking):
        '''
        The access context.
        '''
        # ---------------------------------------------------------------- Defined
        filters = defines(list, doc='''
        @rtype: list[str]
        The list of filters.
        ''')
        
    def prepare(self, resolvers):
        '''
        @see: IVerifier.prepare
        '''
        merge(resolvers, dict(Repository=AccessRule.Repository, Access=AccessRule.Access))
    
    def begin(self, digester, **attributes):
        '''
        @see: Rule.begin
        '''
        assert isinstance(digester, DigesterArg), 'Invalid digester %s' % digester
        assert digester.stack, 'Expected a repository on the digester stack'
        repository = digester.stack[-1]
        assert isinstance(repository, AccessRule.Repository), 'Invalid repository %s' % repository
        
        access = digester.arg.Access()
        if not access.filters: access.filters = []
        access.filters.extend([f.strip() for f in attributes.get('filter', '').split(',') if f])
        
        trackOn(digester, access)
        
        if repository.accesses is None: repository.accesses = []
        repository.accesses.append(access)
        digester.stack.append(access)
        
    def end(self, node, digester):
        '''
        @see: Rule.end
        '''
        assert isinstance(digester, DigesterArg), 'Invalid digester %s' % digester
        assert digester.stack, 'Invalid stack %s' % digester.stack
        digester.stack.pop()
        

class URLRule(Rule, IPrepare):
    '''
    Digester rule for extracting URLs from the xml configuration file.
    '''
    
    class Access(Context):
        '''
        The access context.
        '''
        # ---------------------------------------------------------------- Defined
        urls = defines(list, doc='''
        @rtype: list[string]
        The list of urls.
        ''')
    
    def prepare(self, resolvers):
        '''
        @see: IVerifier.prepare
        '''
        merge(resolvers, dict(Access=URLRule.Access))
    
    def content(self, digester, content):
        '''
        @see: Rule.content
        '''
        assert isinstance(digester, DigesterArg), 'Invalid digester %s' % digester
        assert digester.stack, 'Expected access repository on the digester stack'
        access = digester.stack[-1]
        assert isinstance(access, URLRule.Access), 'Invalid Access class %s' % access
        
        content = content.strip()
        if content:
            if access.urls is None: access.urls = []
            access.urls.append(content)
            
class MethodRule(Rule, IPrepare):
    '''
    Digester rule for extracting Methods from the xml configuration file.
    '''
    
    class Access(Context):
        '''
        The access context.
        '''
        # ---------------------------------------------------------------- Defined
        methods = defines(list, doc='''
        @rtype: list[str]
        The list of methods.
        ''')
    
    def __init__(self, fromAttributes=False):
        '''
        Construct the method rule
        
        @param fromAttributes: boolean
            The flag tells whether to parse methods from xml tags or xml attributes.
        '''
        assert isinstance(fromAttributes, bool), 'Invalid flag %s' % fromAttributes
        self.fromAttributes = fromAttributes
    
    def prepare(self, resolvers):
        '''
        @see: IVerifier.prepare
        '''
        merge(resolvers, dict(Access=MethodRule.Access))
    
    def begin(self, digester, **attributes):
        '''
        @see: Rule.begin
        '''
        if not self.fromAttributes: return
        
        assert isinstance(digester, DigesterArg), 'Invalid digester %s' % digester
        assert digester.stack, 'Expected a repository on the digester stack'
        access = digester.stack[-1]
        assert isinstance(access, MethodRule.Access), 'Invalid access class %s' % access
        
        if not access.methods: access.methods = []
        access.methods.extend([m.strip() for m in attributes.get('methods', '').split(',') if m])
        
    def content(self, digester, content):
        '''
        @see: Rule.content
        '''
        if self.fromAttributes: return
        
        assert isinstance(digester, DigesterArg), 'Invalid digester %s' % digester
        assert digester.stack, 'Expected a repository on the digester stack'
        access = digester.stack[-1]
        assert isinstance(access, MethodRule.Access), 'Invalid access class %s' % access
        
        content = content.strip()
        if content:
            if access.methods is None: access.methods = []
            access.methods.append(content)