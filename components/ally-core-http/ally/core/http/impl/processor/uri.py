'''
Created on Jun 28, 2011

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the URI request node handler.
'''

from ally.core.http.impl.processor.base import ErrorResponseHTTP
from ally.core.impl.processor.base import addError
from ally.design.processor.attribute import requires, defines, definesIf
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.http.spec.codes import PATH_FOUND, PATH_NOT_FOUND, MISSING_SLASH
from urllib.parse import unquote
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Required
    root = requires(Context)
    
class Node(Context):
    '''
    The node context.
    '''
    # ---------------------------------------------------------------- Required
    invokers = requires(dict)
    child = requires(Context)
    childByName = requires(dict)
    hasMandatorySlash = requires(bool)

class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Defined
    node = definesIf(Context, doc='''
    @rtype: Context
    The node corresponding to the request.
    ''')
    nodesValues = definesIf(dict, doc='''
    @rtype: dictionary{Context: string}
    A dictionary containing the path values indexed by the node.
    ''')
    extension = definesIf(str, doc='''
    @rtype: string
    The extension of the requested URI.
    ''')
    # ---------------------------------------------------------------- Required
    uri = requires(str)

class ResponseContent(Context):
    '''
    The response content context.
    '''
    # ---------------------------------------------------------------- Defined
    type = defines(str, doc='''
    @rtype: string
    The response content type.
    ''')

# --------------------------------------------------------------------

class URIHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the searches based on the request URI the resource node, also
    populates the arguments based on path and extension on the request.
    '''

    def __init__(self):
        super().__init__(Node=Node)

    def process(self, chain, register:Register, request:Request, response:ErrorResponseHTTP,
                responseCnt:ResponseContent, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Process the URI to a resource path.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        assert isinstance(request, Request), 'Invalid required request %s' % request
        assert isinstance(responseCnt, ResponseContent), 'Invalid response content %s' % responseCnt
        
        if response.isSuccess is False: return  # Skip in case the response is in error
        assert isinstance(request.uri, str), 'Invalid request URI %s' % request.uri
        
        paths = request.uri.split('/')
        i = paths[-1].rfind('.') if len(paths) > 0 else -1
        if i < 0:
            clearExtension = True
            extension = None
        else:
            clearExtension = i == 0
            extension = paths[-1][i + 1:].lower()
            paths[-1] = paths[-1][0:i]
        
        paths = [unquote(p) for p in paths]
        if not paths[-1]: paths.pop()

        if extension:
            if Request.extension in request: request.extension = extension
            responseCnt.type = request.extension
        
        node = register.root
        for k, path in enumerate(paths):
            assert isinstance(node, Node), 'Invalid node %s' % node
            
            if node.childByName:
                if path not in node.childByName:
                    PATH_NOT_FOUND.set(response)
                    addError(response, 'Instead of \'%(item)s\' or before it is expected, maybe you meant: %(paths)s',
                             item=path, paths=['%s/%s/%s' % ('/'.join(paths[:k]), item, '/'.join(paths[k:]))
                                               for item in sorted(node.childByName)])
                    return
                node = node.childByName[path]
                continue
            
            if node.child:
                if Request.nodesValues in request:
                    if request.nodesValues is None: request.nodesValues = {}
                    request.nodesValues[node] = path
                node = node.child
                continue
            
            PATH_NOT_FOUND.set(response)
            addError(response, 'No more path items expected after \'%(path)s\'', path='/'.join(paths[:k]))
            return
                
        if not node.invokers:
            PATH_NOT_FOUND.set(response)
            if node.childByName:
                addError(response, 'Expected additional path items, maybe you meant: %(paths)s',
                         paths=['%s/%s' % ('/'.join(paths), item) for item in sorted(node.childByName)])
            else: addError(response, 'Expected a value path item')
            return
        
        if not clearExtension and node.hasMandatorySlash:
            # We need to check if the last path element is not a string property ant there might be confusion
            # with the extension
            MISSING_SLASH.set(response)
            addError(response, 'Unclear extension, you need to add a trailing slash to URI')
            return
                
        assert log.debug('Found resource for URI %s', request.uri) or True
        PATH_FOUND.set(response)
        if Request.node in request: request.node = node
