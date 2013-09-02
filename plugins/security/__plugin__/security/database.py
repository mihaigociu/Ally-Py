'''
Created on Jan 17, 2012

@package: security
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the database settings.
'''

from ..gateway_acl.database import updateMetasForACL
from ..sql_alchemy.db_application import metas, bindApplicationSession
from ally.container import ioc
from security.meta.metadata_security import meta

# --------------------------------------------------------------------

@ioc.entity
def binders(): return [bindApplicationSession]

# --------------------------------------------------------------------

@ioc.after(updateMetasForACL)
def updateMetasForSecurity(): metas().append(meta)
