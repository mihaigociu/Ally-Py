'''
The following classes will be used as containers in the Digester stack
'''

class StackNode:
    '''
    Base container class to be used in the digester stack
    '''
    def __init__(self, typeName, aclContainer=None):
        assert isinstance(typeName, str), 'Invalid node type name %s' % typeName
        self.type = typeName
        self.children = []
        self.aclContainer = aclContainer

    def __repr__(self):
        return str(self.__dict__)

class ActionContainer:
    '''
    Container class for Acl Action 
    '''
    def __init__(self, path, label=None, script=None, navbar=None, parent=None):
        self.path = path
        self.label = label
        self.script = script
        self.navBar = navbar
        if parent != None:
            self.path = '{0}.{1}'.format(self.path, parent)
        
    def getPath(self):
        return self.path

    def __repr__(self):
        return str(self.__dict__)

class RightContainer:
    '''
    Container class for Acl Right 
    '''
    def __init__(self, name, description=''):
        self.name = name
        self.description = description
        self.actions = []
        self.filters = []
        
    def addActions(self, actions):
        self.actions.extend(actions)
    
    def addFilter(self, filter):
        self.filters.append(filter)
    
    def addToDescription(self, description):
        if self.description == None: self.setDescription('')
        if description: self.description += description
    
    def setDescription(self, description):
        self.description = description
    
    def __repr__(self):
        return str(self.__dict__)

class FilterContainer:
    '''
    Container class for Acl Filter 
    '''
    def __init__(self, name):
        self.name = name
        self.urls = []
        self.methods = []
    
    def addMethods(self, methods):
        self.methods.extend(methods)
    
    def addUrl(self, url):
        self.urls.append(url)

    def __repr__(self):
        return str(self.__dict__)