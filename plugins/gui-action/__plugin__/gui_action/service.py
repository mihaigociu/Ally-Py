'''
Created on Feb 23, 2012

@package: ally actions gui 
@copyright: 2011 Sourcefabric o.p.s.
@license:  http://www.gnu.org/licenses/gpl-3.0.txt
@author: Mihai Balaceanu

Provides the services setup.
'''

from ..plugin.registry import registerService
from .database import binders
from ally.container import support, bind

# --------------------------------------------------------------------

SERVICES = 'gui.action.api.**.I*Service'

bind.bindToEntities('gui.action.impl.**.*Alchemy', binders=binders)
support.createEntitySetup('gui.action.impl.**.*')
support.listenToEntities(SERVICES, listeners=registerService, beforeBinding=False)
support.loadAllEntities(SERVICES)

# --------------------------------------------------------------------

