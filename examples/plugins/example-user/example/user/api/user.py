'''
Created on Jun 12, 2013

@package: example user
@copyright: 2013 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Martin Saturka

The API descriptions for user example.
'''

from ally.api.config import service, query
from ally.api.criteria import AsLike
from example.api.domain_example import modelExample
from ally.support.api.entity import Entity, QEntity, IEntityService

# --------------------------------------------------------------------

@modelExample
class User(Entity):
    '''
    The user model.
    '''
    Name = str

# --------------------------------------------------------------------

@query(User)
class QUser(QEntity):
    '''
    The user model query object.
    '''
    name = AsLike

# --------------------------------------------------------------------

@service((Entity, User), (QEntity, QUser))
class IUserService(IEntityService):
    '''
    The user service.
    '''
