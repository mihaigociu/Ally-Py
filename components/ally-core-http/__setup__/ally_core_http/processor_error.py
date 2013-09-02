'''
Created on Feb 7, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the processors used in presenting REST errors.
'''

from ..ally_core.processor import converterContent, rendering
from ..ally_core.resources import injectorAssembly
from ..ally_http.processor import acceptRequestDecode, contentLengthEncode, \
    allowEncode, methodOverride, contentTypeResponseEncode, internalError
from .processor import allow_method_override, uri, errorExplain, \
    read_from_params, headerParameter
from ally.container import ioc
from ally.core.http.impl.processor.error_populator import ErrorPopulator
from ally.design.processor.assembly import Assembly
from ally.design.processor.handler import Handler
from ally.http.spec.codes import METHOD_NOT_AVAILABLE

# --------------------------------------------------------------------

@ioc.entity
def statusToCode():
    return {
            METHOD_NOT_AVAILABLE.status: METHOD_NOT_AVAILABLE
            }

@ioc.entity
def errorPopulator() -> Handler:
    b = ErrorPopulator()
    b.statusToCode = statusToCode()
    return b

# --------------------------------------------------------------------

@ioc.entity
def assemblyErrorDelivery() -> Assembly:
    '''
    The assembly containing the handlers that will be used in delivery for the error responses.
    '''
    return Assembly('Error delivery')

# --------------------------------------------------------------------
    
@ioc.before(assemblyErrorDelivery)
def updateAssemblyErrorDelivery():
    assemblyErrorDelivery().add(internalError(), injectorAssembly(), uri(), acceptRequestDecode(), converterContent(),
                                rendering(), errorPopulator(), errorExplain(), contentTypeResponseEncode(), 
                                contentLengthEncode(), allowEncode())
    if allow_method_override(): assemblyErrorDelivery().add(methodOverride(), before=acceptRequestDecode())
    if read_from_params(): assemblyErrorDelivery().add(headerParameter(), after=injectorAssembly())
