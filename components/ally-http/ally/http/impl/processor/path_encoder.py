'''
Created on Jan 31, 2013

@package: ally http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the path encoder.
'''

from ally.container.ioc import injected
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.http.spec.headers import HeadersRequire, HOST
from ally.support.util_spec import IDo
from urllib.parse import urlsplit, urlunsplit
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Request(HeadersRequire):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    scheme = requires(str)

class Response(Context):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Defined
    doEncodePath = defines(IDo, doc='''
    @rtype: callable(path:string) -> string
    The path encoder used for encoding paths that will be rendered in the response.
    ''')
    
# --------------------------------------------------------------------

@injected
class EncoderPathHandler(HandlerProcessor):
    '''
    Provides the path encoder for the response.
    '''
    
    def process(self, chain, request:Request, response:Response, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Overrides the request method based on a provided header.
        '''
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response

        host = HOST.fetch(request)
        if host: response.doEncodePath = self.createEncode(request.scheme, host)
        else: assert log.debug('No host header available for URI %s', request.uri) or True
        
    # ----------------------------------------------------------------
    
    def createEncode(self, scheme, host):
        '''
        Create the path encode.
        
        @param scheme: string
            The encoded path scheme.
        @param host: string
            The host string.
        '''
        assert isinstance(scheme, str), 'Invalid scheme %s' % scheme
        assert isinstance(host, str), 'Invalid host %s' % host
        def doEncodePath(path):
            '''
            Do encode the path.
            '''
            assert isinstance(path, str), 'Invalid path %s' % path
            url = urlsplit(path)
    
            if url.scheme or url.netloc: return urlunsplit((url.scheme, url.netloc, url.path, url.query, url.fragment))
            # Is a relative URI so we append the scheme and host.
            return urlunsplit((scheme, host, url.path, url.query, url.fragment))
        return doEncodePath

