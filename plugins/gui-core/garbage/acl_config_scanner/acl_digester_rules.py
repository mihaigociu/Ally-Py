from .acl_auxiliary_classes import StackNode, ActionContainer, FilterContainer, \
    RightContainer
from acl.api.access import generateId
from acl.api.group import IGroupService
from ally.api.error import InputError
from ally.container import wire
from ally.xml.digester import Rule, Node
from sqlalchemy.exc import IntegrityError

class ActionRule(Rule):
    
    def begin(self, digester, **attributes):
        #action nodes can be nested; if this is the case, concat parent path and child path
        parent = None
        if digester.stack[-1].type == 'Action': parent = digester.stack[-1].aclContainer

        path = attributes.get('path')
        if parent and not path.startswith(parent.getPath()):
            path = str.format('{0}.{1}', parent.getPath(), path)
        
        actionContainer = ActionContainer(path, attributes.get('label'), \
                             attributes.get('script'), attributes.get('navbar'), \
                             attributes.get('parent'))
        digester.stack.append(StackNode('Action', actionContainer))
                
    def content(self, digester, content):
        pass
        
    def end(self, node, digester):
        actionNode = digester.stack.pop()
        if digester.stack[-1].type == 'Right':
            digester.stack[-1].aclContainer.addActions([actionNode.aclContainer])
            #also add the children of the Action to the Right
            digester.stack[-1].aclContainer.addActions([child.aclContainer for child in actionNode.children])
        else:
            #we have some nested Actions here; we will attach the action to its Action parent (in Children list), which will then pass all the Children to its own parent or to a Right object 
            assert digester.stack[-1].type in ('Action', 'Actions')
            digester.stack[-1].children.append(actionNode)
            

class ActionsRule(Rule):
    def begin(self, digester, **attributes):
        digester.stack.append(StackNode('Actions'))
        pass
    
    def content(self, digester, content):
        pass
        
    def end(self, node, digester):
        #add all the actions in this node to the Right node that contains it
        actionsNode = digester.stack.pop()
        assert digester.stack[-1].type == 'Right'
        digester.stack[-1].aclContainer.addActions([child.aclContainer for child in actionsNode.children])
        

class RightsRule(Rule):
    def begin(self, digester, **attributes):
        digester.stack.append(StackNode('Rights'))
                
    def content(self, digester, content):
        pass
        
    def end(self, node, digester):
        pass

class RightRule(Rule):
    groupService = IGroupService; wire.entity('groupService')
    
    def begin(self, digester, **attributes):
        node = digester._nodes[-1]
        assert isinstance(node, Node)
        rightContainer = RightContainer(attributes.get('name', node.name), attributes.get('description'))
        digester.stack.append(StackNode('Right', rightContainer))

    def content(self, digester, content):
        pass
        
    def end(self, node, digester):
        rightNode = digester.stack.pop()
        digester.stack[-1].children.append(rightNode)
        
        #add Filters to the database
        for fContainer in rightNode.aclContainer.filters:
            for path in fContainer.urls:
                for method in fContainer.methods:
                    accessId = generateId(path, method)
                    try:
                        #TODO: remove
                        if __debug__:
                            print(path, method, accessId)
                            
                        self.groupService.addGroup(accessId, rightNode.aclContainer.name)
                        self.groupService.addFilter(accessId, rightNode.aclContainer.name, fContainer.name)
                        
                    #errors caused by the invalid access id - 
                    #TODO handle properly
                    except IntegrityError:
                        print("invalid access id (integrity)")
                        #raise
                    except InputError:
                        print("invalid access id (input)")
                        print()
                        #raise
        
        
class FilterRule(Rule):
    def begin(self, digester, **attributes):
        filterContainer = FilterContainer(attributes.get('filter'))
        filterContainer.addMethods([m.strip() for m in attributes.get('methods', '').split(',') if m != ''])
        digester.stack.append(StackNode('Allows', filterContainer))
                
    def content(self, digester, content):
        pass
        
    def end(self, node, digester):
        filterNode = digester.stack.pop()
        assert digester.stack[-1].type == 'Right'
        digester.stack[-1].aclContainer.addFilter(filterNode.aclContainer)
        
        
class URLRule(Rule):
    def begin(self, digester, **attributes):
        pass
                
    def content(self, digester, content):
        assert isinstance(content, str)
        assert digester.stack[-1].type == 'Allows'
        digester.stack[-1].aclContainer.addUrl(content)
        
    def end(self, node, digester):
        pass

class DescriptionRule(Rule):
    def begin(self, digester, **attributes):
        pass
                
    def content(self, digester, content):
        assert isinstance(content, str)
        assert digester.stack[-1].type == 'Right'
        digester.stack[-1].aclContainer.addToDescription(content)
        
    def end(self, node, digester):
        pass
