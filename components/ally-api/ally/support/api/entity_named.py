'''
Created on May 2, 2012

@package: ally api
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

General specifications for the entities API that poses a string Name identifier.
'''

from .entity import IEntityCRUDPrototype, IEntityGetPrototype, \
    IEntityFindPrototype, IEntityQueryPrototype
from ally.api.config import model, query, service
    
# --------------------------------------------------------------------

@model(id='Name')
class Entity:
    '''
    Provides the basic container for an entity that has a Name as the identifier.
    '''
    Name = str

# --------------------------------------------------------------------

@query(Entity)
class QEntity:
    '''
    Provides the basic query for an entity.
    '''

# --------------------------------------------------------------------

@service(('Entity', Entity))
class IEntityGetService(IEntityGetPrototype):
    '''
    Entity Name identifier service for @see: IEntityGetPrototype
    '''

@service(('Entity', Entity))
class IEntityFindService(IEntityFindPrototype):
    '''
    Entity Name identifier service for @see: IEntityFindService
    '''

@service(('Entity', Entity), ('QEntity', QEntity))
class IEntityQueryService(IEntityQueryPrototype):
    '''
    Entity Name identifier service for @see: IEntityQueryService
    '''

@service(('Entity', Entity))
class IEntityCRUDService(IEntityCRUDPrototype):
    '''
    Entity Name identifier service for @see: IEntityCRUDService
    '''

@service
class IEntityGetCRUDService(IEntityGetService, IEntityCRUDService):
    '''
    Provides the get and CRUD.
    '''

@service
class IEntityNQService(IEntityGetService, IEntityFindService, IEntityCRUDService):
    '''
    Provides the find without querying and CRUD services.
    '''

@service
class IEntityService(IEntityGetService, IEntityQueryService, IEntityCRUDService):
    '''
    Provides the find, CRUD and query entity services.
    '''
