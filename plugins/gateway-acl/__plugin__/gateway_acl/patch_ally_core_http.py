'''
Created on Feb 19, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the ally core http setup patch.
'''

from .service import root_uri_acl
from ally.container import ioc
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

try:
    from __setup__ import ally_core_http  # @UnusedImport
except ImportError: log.info('No ally core http component available, thus no need to register root URI for ACL Gateways')
else:
    from __setup__.ally_core_http.server import root_uri_resources
    
    # ----------------------------------------------------------------
    
    @ioc.replace(root_uri_acl)
    def root_uri_acl_resources(): return root_uri_resources()
