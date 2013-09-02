'''
Created on Jun 23, 2011

@package: support sqlalchemy
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

SQL alchemy implementation for the generic ided or named entities API.
'''

from ally.api.operator.type import TypeModel, TypeProperty, TypeQuery
from ally.api.type import typeFor
from ally.support.api.util_service import modelId
from inspect import isclass
from sql_alchemy.support.mapper import MappedSupport
from sql_alchemy.support.util_service import SessionSupport, buildQuery, \
    iterateCollection, insertModel, updateModel, deleteModel
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class EntitySupportAlchemy(SessionSupport):
    '''
    Provides support generic entity handling.
    '''

    def __init__(self, Mapped, QEntity=None, **mapping):
        '''
        Construct the entity support for the provided model class and query class.
        
        @param Mapped: class
            The mapped entity model class.
        @param QEntity: class|None
            The query mapped class if there is one.
        @param mapping: key arguments of columns
            The column mappings provided for criteria name in case they are needed, this is only used if a QEntity is
            provided.
        '''
        assert isclass(Mapped), 'Invalid class %s' % Mapped
        assert isinstance(Mapped, MappedSupport), 'Invalid mapped class %s' % Mapped
        model = typeFor(Mapped)
        assert isinstance(model, TypeModel), 'Invalid model class %s' % Mapped
        assert isinstance(model.propertyId, TypeProperty), 'Invalid model property id %s' % model.propertyId
        
        self.Entity = model.clazz
        self.Mapped = Mapped
        self.MappedId = modelId(Mapped)

        if QEntity is not None:
            assert isclass(QEntity), 'Invalid class %s' % QEntity
            assert isinstance(typeFor(QEntity), TypeQuery), 'Invalid query entity class %s' % QEntity
            if __debug__:
                for name in mapping:
                    assert name in typeFor(QEntity).properties, 'Invalid criteria name \'%s\' for %s' % (name, QEntity)
            self._mapping = mapping
        else: assert not mapping, 'Illegal mappings %s with no QEntity provided' % mapping
        self.QEntity = QEntity

# --------------------------------------------------------------------

class EntityGetServiceAlchemy(EntitySupportAlchemy):
    '''
    Generic implementation for @see: IEntityGetPrototype
    '''

    def getById(self, identifier):
        '''
        @see: IEntityGetPrototype.getById
        '''
        return self.session().query(self.Mapped).filter(self.MappedId == identifier).one()

class EntityFindServiceAlchemy(EntitySupportAlchemy):
    '''
    Generic implementation for @see: IEntityFindPrototype
    '''

    def getAll(self, **options):
        '''
        @see: IEntityFindPrototype.getAll
        '''
        return iterateCollection(self.session().query(self.MappedId), **options)

class EntityQueryServiceAlchemy(EntitySupportAlchemy):
    '''
    Generic implementation for @see: IEntityQueryPrototype
    '''

    def getAll(self, q=None, **options):
        '''
        @see: IEntityQueryPrototype.getAll
        '''
        assert self.QEntity is not None, 'No query available for this service'
        sql = self.session().query(self.MappedId)
        if q is not None:
            assert isinstance(q, self.QEntity), 'Invalid query %s' % q
            sql = buildQuery(sql, q, self.Mapped, **self._mapping)
        return iterateCollection(sql, **options)

class EntityCRUDServiceAlchemy(EntitySupportAlchemy):
    '''
    Generic implementation for @see: IEntityCRUDPrototype
    '''

    def insert(self, entity):
        '''
        @see: IEntityCRUDPrototype.insert
        '''
        return modelId(insertModel(self.Mapped, entity))

    def update(self, entity):
        '''
        @see: IEntityCRUDPrototype.update
        '''
        updateModel(self.Mapped, entity)

    def delete(self, identifier):
        '''
        @see: IEntityCRUDPrototype.delete
        '''
        return deleteModel(self.Mapped, identifier)

class EntityGetCRUDServiceAlchemy(EntityGetServiceAlchemy, EntityCRUDServiceAlchemy):
    '''
    Generic implementation for @see: IEntityGetCRUDPrototype
    '''

class EntityNQServiceAlchemy(EntityGetServiceAlchemy, EntityFindServiceAlchemy, EntityCRUDServiceAlchemy):
    '''
    Generic implementation for @see: IEntityNQPrototype
    '''

    def __init__(self, Entity):
        '''
        @see: EntitySupportAlchemy.__init__
        '''
        EntitySupportAlchemy.__init__(self, Entity)

class EntityServiceAlchemy(EntityGetServiceAlchemy, EntityQueryServiceAlchemy, EntityCRUDServiceAlchemy):
    '''
    Generic implementation for @see: IEntityPrototype
    '''

