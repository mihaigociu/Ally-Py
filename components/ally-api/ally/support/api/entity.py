'''
Created on May 26, 2011

@package: ally api
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

General specifications for the entities API that poses an integer Id identifier.
'''

from ally.api.config import prototype
from ally.api.option import SliceAndTotal # @UnusedImport
from ally.api.type import Iter
from ally.support.api.util_service import modelId
import abc # @UnusedImport

# --------------------------------------------------------------------

class IEntityGetPrototype(metaclass=abc.ABCMeta):
    '''
    Provides the basic entity prototype service. This means locate by id.
    '''

    @prototype
    def getById(self, identifier:lambda p:p.Entity) -> lambda p:p.Entity:
        '''
        Provides the entity based on the identifier.
        
        @param identifier: object
            The id of the entity to find.
        '''

class IEntityFindPrototype(metaclass=abc.ABCMeta):
    '''
    Provides the basic entity find prototype service.
    '''

    @prototype
    def getAll(self, **options:SliceAndTotal) -> lambda p:Iter(modelId(p.Entity)):
        '''
        Provides the entities identifiers.
        
        @param options: @see: SliceAndTotal
            The options to fetch the entities with.
        @return: Iterable(object)
            The iterable with the entities identifiers.
        '''

class IEntityQueryPrototype(metaclass=abc.ABCMeta):
    '''
    Provides the entity find prototype service based on a query.
    '''

    @prototype
    def getAll(self, q:lambda p:p.QEntity=None, **options:SliceAndTotal) -> lambda p:Iter(modelId(p.Entity)):
        '''
        Provides the entities identifiers searched by the provided query.
        
        @param q: Query|None
            The query to search by.
        @param options: @see: SliceAndTotal
            The options to fetch the entities with.
        @return: Iterable(object)
            The iterable with the entities identifiers.
        '''

class IEntityCRUDPrototype(metaclass=abc.ABCMeta):
    '''
    Provides the entity the CRUD prototype services.
    '''

    @prototype
    def insert(self, entity:lambda p:p.Entity) -> lambda p:modelId(p.Entity):
        '''
        Insert the entity.
        
        @param entity: Entity
            The entity to be inserted.
        @return: object
            The identifier of the entity
        '''

    @prototype
    def update(self, entity:lambda p:p.Entity):
        '''
        Update the entity.
        
        @param entity: Entity
            The entity to be updated.
        '''

    @prototype
    def delete(self, identifier:lambda p:p.Entity) -> bool:
        '''
        Delete the entity for the provided identifier.
        
        @param identifier: object
            The identifier of the entity to be deleted.
        @return: boolean
            True if the delete is successful, false otherwise.
        '''

class IEntityGetCRUDPrototype(IEntityGetPrototype, IEntityCRUDPrototype):
    '''
    Provides the get and CRUD prototype service.
    '''

class IEntityNQPrototype(IEntityGetPrototype, IEntityFindPrototype, IEntityCRUDPrototype):
    '''
    Provides the find without querying, CRUD and query entity prototype services.
    '''

class IEntityPrototype(IEntityGetPrototype, IEntityQueryPrototype, IEntityCRUDPrototype):
    '''
    Provides the find, CRUD and query entity prototype services.
    '''
