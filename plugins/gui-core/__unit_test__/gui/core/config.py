'''
Created on Aug 22, 2013

@package: gui core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Mihai Gociu

GUI core configuration XML testing.
'''

# Required in order to register the package extender whenever the unit test is run.
if True:
    import package_extender
    package_extender.PACKAGE_EXTENDER.setForUnitTest(True)

# --------------------------------------------------------------------
from gui.core.config.impl.processor.xml.parser import ParserHandler
from ally.xml.digester import RuleRoot, Node

from ally.container.ioc import initialize
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import defines, requires
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing, FILL_ALL
from os.path import join, dirname
import logging
import unittest

from gui.core.config.impl.rules import URLRule, ActionRule, MethodRule, AccessRule

# --------------------------------------------------------------------

logging.basicConfig()
logging.getLogger('ally.design.processor').setLevel(logging.INFO)

# --------------------------------------------------------------------
    
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

# --------------------------------------------------------------------
    
class TestConfigurationParsing(unittest.TestCase):

    def testConfigurationParser(self):
        
        parser = ParserHandler()
        parser.rootNode = RuleRoot()
        
        anonymous = parser.rootNode.obtainNode('Config/Anonymous')
        allows = anonymous.addRule(AccessRule(), 'Access')
        #allows.addRule(MethodRule(fromAttributes=True))
        allows.addRule(URLRule(), 'URL')
        allows.addRule(MethodRule(), 'Method')
        
        action = Node('Action')
        action.addRule(ActionRule())
        action.childrens['Action'] = action
        
        actions = Node('Actions')
        actions.childrens['Action'] = action
        
        anonymous.childrens['Actions'] = actions
        anonymous.childrens['Action'] = action
        
        assemblyParsing = Assembly('Parsing XML')
        assemblyParsing.add(initialize(parser))
        
        # ------------------------------------------------------------
        
        proc = assemblyParsing.create(solicit=TestSolicit)
        assert isinstance(proc, Processing)
        
        solicit = proc.ctx.solicit(file=join(dirname(__file__), 'config_test.xml'))
        arg = proc.execute(FILL_ALL, solicit=solicit)
        assert isinstance(arg.solicit, TestSolicit)
        
        print('Actions: ')
        if arg.solicit.repository.actions:
            for action in arg.solicit.repository.actions:
                print('Action at line %s: ' % action.lineNumber, action.path, action.label, action.script, action.navBar)
            
        print("Accesses: ")
        if arg.solicit.repository.accesses:
            for access in arg.solicit.repository.accesses:
                print('Access at line %s: ' % access.lineNumber, access.filters, access.methods, access.urls)
        

# --------------------------------------------------------------------

if __name__ == '__main__': unittest.main()