'''
Created on Jan 17, 2012

@package: support sqlalchemy
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the database settings for the application database.
'''

from ally.container import ioc, support
from sql_alchemy import database_config
from sql_alchemy.database_config import alchemySessionCreator, metas
from sql_alchemy.support.session import bindSession

# --------------------------------------------------------------------

support.include(database_config)

# --------------------------------------------------------------------

alchemySessionCreator = alchemySessionCreator
metas = metas

@ioc.replace(database_url)
def database_url():
    '''This database URL is used for the application tables'''
    return 'sqlite:///workspace/shared/application.db'

# --------------------------------------------------------------------

def bindApplicationSession(proxy): bindSession(proxy, alchemySessionCreator())
