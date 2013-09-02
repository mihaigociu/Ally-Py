'''
Created on Aug 19, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Implementation for the ACL filter.
'''

from ..api.filter import IFilterService, QFilter
from ..meta.acl_intern import Path
from ..meta.filter import FilterMapped
from ally.container.ioc import injected
from ally.container.support import setup
from sql_alchemy.impl.entity import EntityGetServiceAlchemy, \
    EntityQueryServiceAlchemy, EntitySupportAlchemy
from sql_alchemy.support.util_service import deleteModel, insertModel
    
# --------------------------------------------------------------------

@injected
@setup(IFilterService, name='filterService')
class FilterServiceAlchemy(EntityGetServiceAlchemy, EntityQueryServiceAlchemy, IFilterService):
    '''
    Implementation for @see: IFilterService that provides the ACL filters.
    '''
    
    def __init__(self):
        EntitySupportAlchemy.__init__(self, FilterMapped, QFilter, path=Path.path)
        
    def insert(self, filtre):
        '''
        @see: IFilterService.insert
        '''
        return insertModel(FilterMapped, filtre).Name
        
    def delete(self, name):
        '''
        @see: IFilterService.delete
        '''
        return deleteModel(FilterMapped, name)
    
