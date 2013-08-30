'''
Created on Feb 27, 2012

@package: gui action
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Mihai Balaceanu

Action Manager Implementation
'''

from ally.container.ioc import injected
from ally.container.support import setup
from gui.action.api.action import Action, IActionManagerService
from sql_alchemy.impl.entity import EntityNQServiceAlchemy, EntitySupportAlchemy
from sqlalchemy.exc import SQLAlchemyError
from ally.support.sqlalchemy.util_service import iterateCollection, insertModel
from gui.action.meta.action import ActionMapped

# --------------------------------------------------------------------

@injected
@setup(IActionManagerService, name='actionManager')
class ActionManagerServiceAlchemy(EntityNQServiceAlchemy, IActionManagerService):
    '''
    @see: IActionManagerService
    '''

    def __init__(self):
        EntitySupportAlchemy.__init__(self, ActionMapped)

    def getChildren(self, path, **options):
        '''
        @see: IActionManagerService.getChildren
        '''
        assert isinstance(path, str), 'Invalid path %s' % path
        sql = self.session().query(ActionMapped.Path).filter(ActionMapped.Path.like('%s.%' % path))
        return iterateCollection(sql, **options)
    
    def insert(self, action):
        '''
        @see IActionManagerService.insert
        '''
        assert isinstance(action, Action), 'Invalid action %s' % action
        insertModel(ActionMapped, action)
        
        path = action.Path
        while '.' in path:
            path = path[:path.rfind('.')]
            if self.session().query(ActionMapped.Path).filter(ActionMapped.Path == path).count(): break
            insertModel(ActionMapped, Action(Path=path))
                
        return action.Path
        
    def delete(self, path):
        '''
        @see IActionManagerService.delete
        '''
        assert isinstance(path, str), 'Invalid path %s' % path
        
        sql = self.session().query(ActionMapped)
        sql = sql.filter(ActionMapped.Path.like('{0}.%'.format(path)) | (ActionMapped.Path == path))
        hasDeleted = False
        for action in sql.all():
            self.session().delete(action)
            hasDeleted = True
        return hasDeleted
    
