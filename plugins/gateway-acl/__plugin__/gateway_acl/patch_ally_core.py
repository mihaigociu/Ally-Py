'''
Created on Aug 31, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the ally core setup patch.
'''

from ..sql_alchemy.processor import transaction
from ally.container import support, app, ioc
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

try:
    from __setup__ import ally_core  # @UnusedImport
except ImportError: log.info('No ally core component available, thus no need to register ACL assemblers to it')
else:
    from __setup__.ally_core.resources import assemblyAssembler, updateAssemblyAssembler, processMethod
    from acl.core.impl.processor import assembler

    # The assembler processors
    processFilter = indexFilter = indexAccess = support.notCreated  # Just to avoid errors
    support.createEntitySetup(assembler)
    
    # ----------------------------------------------------------------
    
    @ioc.after(updateAssemblyAssembler)
    def updateAssemblyAssemblerForFilter():
        assemblyAssembler().add(processFilter(), before=processMethod())
    
    @app.setup(app.CHANGED)
    def updateAssemblyAssemblerForAccess():
        assemblyAssembler().add(transaction(), indexFilter(), indexAccess())

