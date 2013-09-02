'''
Created on May 28, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the paths adjustments based on target models.
'''

from ally.api.operator.type import TypeModel
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.http.spec.server import HTTP_POST, HTTP_GET, HTTP_PUT

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Required
    invokers = requires(list)
    
class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Defined
    path = defines(list)
    # ---------------------------------------------------------------- Required
    methodHTTP = requires(str)
    isCollection = requires(bool)
    target = requires(TypeModel)
    
class ElementTarget(Context):
    '''
    The element context.
    '''
    # ---------------------------------------------------------------- Defined
    name = defines(str)
    model = defines(TypeModel)
    
# --------------------------------------------------------------------

class PathTargetHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the paths adjustments based on target models.
    '''
    
    def __init__(self):
        super().__init__(Invoker=Invoker)

    def process(self, chain, register:Register, Element:ElementTarget, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provides the paths adjustments based on target models.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        assert issubclass(Element, ElementTarget), 'Invalid element %s' % Element
        assert isinstance(register.invokers, list), 'Invalid invokers %s' % register.invokers

        for invoker in register.invokers:
            assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
            
            if invoker.methodHTTP == HTTP_GET:
                if not invoker.isCollection:
                    for el in invoker.path:
                        assert isinstance(el, ElementTarget), 'Invalid element %s' % el
                        if el.model == invoker.target: break
                    else:
                        for el in reversed(invoker.path):
                            if el.name:
                                el.name = '%s%s' % (el.name, invoker.target.name)
                                break
                    continue
                
            elif invoker.methodHTTP == HTTP_PUT:
                if invoker.target is not None:
                    assert isinstance(invoker.target, TypeModel), 'Invalid target %s' % invoker.target
                    
                    for el in invoker.path:
                        assert isinstance(el, ElementTarget), 'Invalid element %s' % el
                        if el.model == invoker.target: break
                    else:
                        for el in reversed(invoker.path):
                            if el.name:
                                el.name = '%s%s' % (el.name, invoker.target.name)
                                break
                continue
            
            elif invoker.methodHTTP != HTTP_POST: continue
            assert isinstance(invoker.target, TypeModel), 'Invalid target %s' % invoker.target
            
            if invoker.path is None: invoker.path = []
            invoker.path.append(Element(name=invoker.target.name, model=invoker.target))
                
