'''
Created on Jan 9, 2012

@package: gui core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the services for the gui core.
'''

from ally.container import ioc, app, support
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import defines, requires
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing, FILL_ALL
from ally.design.processor.handler import Handler
from ally.xml.digester import Node, RuleRoot
from gui.core.config.impl.processor.xml.parser import ParserHandler
from gui.core.config.impl.rules import AccessRule, MethodRule, URLRule, \
    ActionRule, DescriptionRule, GroupRule
from sched import scheduler
from threading import Thread
import time

# --------------------------------------------------------------------

# The synchronization processors
synchronizeAction = support.notCreated  # Just to avoid errors
support.createEntitySetup('gui.core.config.impl.processor.synchronize.**.*')

# --------------------------------------------------------------------

@ioc.config
def names_for_group_access():
    '''
    Contains the names of the access groups that are expected in the configuration file. Expected properties are name and
    optionally a flag indicating if actions are allowed.
    '''
    return [dict(name='Anonymous', hasActions=True, hasDescription=False), \
            dict(name='Captcha', hasActions=False, hasDescription=False), \
            dict(name='Right', hasActions=True, hasDescription=True)]

# --------------------------------------------------------------------

@ioc.entity
def assemblyConfiguration() -> Assembly:
    return Assembly('GUI Configurations')

@ioc.entity
def nodeRootXML() -> Node: return RuleRoot()

@ioc.entity
def parserXML() -> Handler:
    b = ParserHandler()
    b.rootNode = nodeRootXML()
    return b

# --------------------------------------------------------------------

@ioc.before(nodeRootXML)
def updateRootNodeXMLForGroups():
    for spec in names_for_group_access():
        assert isinstance(spec, dict), 'Invalid specifications %s' % spec
        assert 'name' in spec, 'A group name is required in %s' % (spec,)
        node = nodeRootXML().addRule(GroupRule(), 'Config/%s' % spec['name'])
        addNodeAccess(node)
        if spec.get('hasActions', False): addNodeAction(node)
        if spec.get('hasDescription', False): addNodeDescription(node)

@ioc.before(assemblyConfiguration)
def updateAssemblyConfiguration():
    assemblyConfiguration().add(parserXML(), synchronizeAction())

@app.deploy
def cleanup():
    ''' Start the cleanup process for authentications/sessions'''
    
    class TestSolicit(Context):
        '''
        The solicit context.
        '''
        # ---------------------------------------------------------------- Defined
        file = defines(str, doc='''
        @rtype: string
        The file to be parsed.
        ''')
        # ---------------------------------------------------------------- Required
        repository = requires(Context)
        
    proc = assemblyConfiguration().create(solicit=TestSolicit)
    assert isinstance(proc, Processing)
    solicit = proc.ctx.solicit(file='acl_right_2.xml')
    
    schedule = scheduler(time.time, time.sleep)
    def executeCleanup():
        arg = proc.execute(FILL_ALL, solicit=solicit)
        assert isinstance(arg.solicit, TestSolicit)
        
        if arg.solicit.repository.groups:
            for group in arg.solicit.repository.groups:
                print('Group: %s' % group.name)
                if group.description: print('Description: %s' % group.description)
                
                print('Actions: ')
                if group.actions:
                    for action in group.actions:
                        print('Action at line %s: ' % action.lineNumber, action.path, action.label, action.script, action.navBar)
                     
                print("Accesses: ")
                if group.accesses:
                    for access in group.accesses:
                        print('Access at line %s: ' % access.lineNumber, access.filters, access.methods, access.urls)        
                print()
    
        schedule.enter(3, 1, executeCleanup, ())

    schedule.enter(3, 1, executeCleanup, ())
    scheduleRunner = Thread(name='Configuration scanner', target=schedule.run)
    scheduleRunner.daemon = True
    scheduleRunner.start()
    
# --------------------------------------------------------------------

def addNodeDescription(node):
    assert isinstance(node, Node), 'Invalid node %s' % node
    node.addRule(DescriptionRule(), 'Description')

def addNodeAccess(node):
    assert isinstance(node, Node), 'Invalid node %s' % node
    
    access = node.addRule(AccessRule(), 'Allows')
    access.addRule(MethodRule(fromAttributes=True))
    access.addRule(URLRule(), 'URL')
    access.addRule(MethodRule(), 'Method')

def addNodeAction(node):
    assert isinstance(node, Node), 'Invalid node %s' % node
    
    action = Node('Action')
    action.addRule(ActionRule())
    action.childrens['Action'] = action
    
    actions = Node('Actions')
    actions.childrens['Action'] = action
    
    node.childrens['Actions'] = actions
    node.childrens['Action'] = action
