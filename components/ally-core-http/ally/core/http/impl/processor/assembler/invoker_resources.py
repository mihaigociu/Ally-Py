'''
Created on Mar 18, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the resource paths encoding.
'''
# TODO: Gabrile: Move to encoders when they are refactored
from ally.container.ioc import injected
from ally.core.http.impl.index import NAME_BLOCK_REST, ACTION_REFERENCE
from ally.core.spec.transform import ITransfrom, IRender
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.http.spec.server import HTTP_GET
from ally.support.util import firstOf
from ally.support.util_spec import IDo
from ally.support.util_sys import locationStack

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Defined
    invokers = defines(list)
    # ---------------------------------------------------------------- Required
    exclude = requires(set)

class Node(Context):
    '''
    The node context.
    '''
    # ---------------------------------------------------------------- Required
    invokersAccessible = requires(list)

class InvokerResources(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Defined
    id = defines(str)
    location = defines(str)
    methodHTTP = defines(str)
    path = defines(list)
    encoder = defines(ITransfrom, doc='''
    @rtype: ITransfrom
    The encoder to be used for rendering the response object.
    ''')
    # ---------------------------------------------------------------- Required
    node = requires(Context)
    doEncodePath = requires(IDo)
    
# --------------------------------------------------------------------

@injected
class InvokerResourcesHandler(HandlerProcessor):
    '''
    Implementation for a handler that provides the resources encoding.
    '''

    nameResources = 'Resources'
    # The name used for resources paths.
    nameRef = 'href'
    # The reference attribute name.
    
    def __init__(self):
        assert isinstance(self.nameResources, str), 'Invalid resources name %s' % self.nameResources
        assert isinstance(self.nameRef, str), 'Invalid reference name %s' % self.nameRef
        super().__init__(Node=Node)
        
    def process(self, chain, register:Register, Invoker:InvokerResources, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Create the collection encoder.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        assert issubclass(Invoker, InvokerResources), 'Invalid invoker class %s' % Invoker
        
        if self.nameResources in register.exclude: return
        if register.invokers is None: register.invokers = []
        
        invoker = Invoker()
        register.invokers.append(invoker)
        assert isinstance(invoker, InvokerResources), 'Invalid invoker %s' % invoker
        invoker.id = self.nameResources
        invoker.location = locationStack(self.__class__)
        invoker.methodHTTP = HTTP_GET
        invoker.path = []
        invoker.encoder = EncoderResources(self.nameResources, self.nameRef, invoker)

# --------------------------------------------------------------------

class EncoderResources(ITransfrom):
    '''
    Implementation for a @see: ITransfrom for resources.
    '''
    
    def __init__(self, nameResources, nameRef, invoker):
        '''
        Construct the resources encoder.
        '''
        assert isinstance(nameResources, str), 'Invalid resources name %s' % nameResources
        assert isinstance(nameRef, str), 'Invalid reference name %s' % nameRef
        assert isinstance(invoker, InvokerResources), 'Invalid invoker %s' % invoker
        
        self.nameResources = nameResources
        self.nameRef = nameRef
        self.invoker = invoker
        
    def transform(self, value, target, support):
        '''
        @see: ITransfrom.transform
        '''
        assert isinstance(target, IRender), 'Invalid target %s' % target
        
        target.beginCollection(self.nameResources)
        node = self.invoker.node
        if node:
            assert isinstance(node, Node), 'Invalid node %s' % node
            if node.invokersAccessible:
                indexes = dict(indexBlock=NAME_BLOCK_REST, indexAttributesCapture={self.nameRef: ACTION_REFERENCE})
                for name, invoker in sorted(node.invokersAccessible, key=firstOf):
                    assert isinstance(invoker, InvokerResources), 'Invalid invoker %s' % invoker
                    assert isinstance(invoker.doEncodePath, IDo), 'Invalid path encode %s' % invoker.doEncodePath
                    target.beginObject(name, attributes={self.nameRef: invoker.doEncodePath(support)}, **indexes).end()
        target.end()
