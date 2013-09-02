'''
Created on Aug 7, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

API specifications for service filters.
'''

from .domain_acl import modelACL
from ally.api.config import service, call, query
from ally.api.criteria import AsLikeOrdered
from ally.support.api.entity_named import Entity, IEntityGetService, QEntity, \
    IEntityQueryService

# --------------------------------------------------------------------

@modelACL
class Filter(Entity):
    '''
    Contains data required for an ACL filter.
        Path -       contains the path that the filter maps to. The path contains beside the fixed string
                     names also markers '*' for where the filtered values or injected values will be placed.
        Hash -       the hash that represents the full aspect of the filter.
        Type -       the type name associated with the target path entry.
    '''
    Path = str
    Type = str
    
# --------------------------------------------------------------------

@query(Filter)
class QFilter(QEntity):
    '''
    Provides the query for filter.
    '''
    path = AsLikeOrdered

# --------------------------------------------------------------------

@service((Entity, Filter), (QEntity, QFilter))
class IFilterService(IEntityGetService, IEntityQueryService):
    '''
    The ACL access filter service provides the means of accessing the available filters.
    '''
    
    @call
    def insert(self, filter:Filter) -> Filter.Name:
        '''
        Insert the filter.
        
        @param filter: Filter
            The filter to be inserted.
        @return: string
            The name of the filter.
        '''
    
    @call
    def delete(self, name:Filter) -> bool:
        '''
        Delete the filter for the provided name.
        
        @param name: string
            The name of the filter to be deleted.
        @return: boolean
            True if the delete is successful, false otherwise.
        '''
