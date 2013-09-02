'''
Created on Aug 30, 2013

@package: support sqlalchemy
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the configurations patch for the processors used in handling the request.
'''

from ally.container import ioc, app
from ally.design.processor.handler import Handler
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

try:
    from __setup__ import ally_core  # @UnusedImport
except ImportError: log.info('No ally core component available, thus no need to apply the transaction patch')
else:
    from __setup__.ally_core.processor import invoking
    from __setup__.ally_core_http.processor import assemblyResources, updateAssemblyResources
    from sql_alchemy.impl.processor import transaction_core
    
    @ioc.entity
    def transactionCore() -> Handler: return transaction_core.TransactionCoreHandler()

    # ----------------------------------------------------------------

    @ioc.after(updateAssemblyResources)
    def updateAssemblyResourcesForAlchemy():
        assemblyResources().add(transactionCore(), before=invoking())
    
    @app.deploy(app.DEVEL)
    def updateLoggingForSQLErrors():
        logging.getLogger(transaction_core.__name__).setLevel(logging.INFO)