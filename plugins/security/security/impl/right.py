'''
Created on Mar 6, 2012

@package: security
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the implementation for right.
'''

from ..api.right import IRightService, QRight
from ..meta.right import RightMapped, RightAccess
from acl.core.impl.acl import AclServiceAlchemy
from ally.container.ioc import injected
from ally.container.support import setup
from sql_alchemy.impl.entity import EntityGetServiceAlchemy, \
    EntityCRUDServiceAlchemy, EntitySupportAlchemy
from sql_alchemy.support.util_service import buildQuery, iterateCollection

# --------------------------------------------------------------------

@injected
@setup(IRightService, name='rightService')
class RightServiceAlchemy(EntityGetServiceAlchemy, EntityCRUDServiceAlchemy, AclServiceAlchemy, IRightService):
    '''
    Implementation for @see: IRightService
    '''
    
    def __init__(self):
        EntitySupportAlchemy.__init__(self, RightMapped, QRight)
        AclServiceAlchemy.__init__(self, RightMapped, RightAccess)
        
    def getAll(self, typeName=None, q=None, **options):
        '''
        @see: IRightService.getAll
        '''
        sql = self.session().query(RightMapped.Id)
        if typeName: sql = sql.filter(RightMapped.Type == typeName)
        if q is not None:
            assert isinstance(q, QRight), 'Invalid query %s' % q
            sql = buildQuery(sql, q, RightMapped)
        return iterateCollection(sql, **options)
    