'''
Created on May 17, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the invokers created based on services.
'''

from ally.api.operator.type import TypeService, TypeCall
from ally.api.type import typeFor, Type
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.support.api.util_service import iterateInputs
from ally.support.util_context import attributesOf, hasAttribute
from ally.support.util_spec import IDo
from ally.support.util_sys import locationStack
from collections import Iterable

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Defined
    invokers = defines(list, doc='''
    @rtype: list[Context]
    The invokers created based on the services.
    ''')
    doCopyInvoker = defines(IDo, doc='''
    @rtype: callable(destination:Context, source:Context, exclude:set=None) -> Context
    On the first position the destination invoker to copy to and on the second position the source to copy from, returns
    the destination invoker. Accepts also a named argument containing a set of attributes names to exclude.
    ''')
    # ---------------------------------------------------------------- Required
    services = requires(Iterable)
    exclude = requires(set)
    
class InvokerCall(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Defined
    id = defines(str, doc='''
    @rtype: string
    The unique id of the invoker.
    ''')
    service = defines(TypeService, doc='''
    @rtype: TypeService
    The invoker service.
    ''')
    call = defines(TypeCall, doc='''
    @rtype: TypeCall
    The call of the invoker.
    ''')
    method = defines(int, doc='''
    @rtype: integer
    The invoker method.
    ''')
    inputs = defines(tuple, doc='''
    @rtype: tuple(Input)
    The tuple of inputs required for the call.
    ''')
    output = defines(Type, doc='''
    @rtype: Type
    The output type of the call.
    ''')
    location = defines(str, doc='''
    @rtype: string
    The location string to localize the API call.
    ''')
    doInvoke = defines(IDo, doc='''
    @rtype: callable(*args, **keyargs) -> object
    The invoke used for handling the request.
    ''')

# --------------------------------------------------------------------

class InvokerServiceHandler(HandlerProcessor):
    '''
    Implementation for a processor that creates invokers based on service implementations.
    '''

    def process(self, chain, register:Register, Invoker:InvokerCall, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provides the invokers to be registered based on services.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        assert issubclass(Invoker, InvokerCall), 'Invalid invoker %s' % Invoker
        assert isinstance(register.services, Iterable), 'Invalid services %s' % register.services

        if register.invokers is None: register.invokers = []
        for implementation in register.services:
            service = typeFor(implementation)
            assert isinstance(service, TypeService), 'Invalid service implementation %s' % implementation

            for call in service.calls.values():
                assert isinstance(call, TypeCall), 'Invalid call %s' % call
                
                invokerId = '%s.%s.%s' % (service.clazz.__module__, service.clazz.__name__, call.name)
                if invokerId in register.exclude: continue
                
                invoker = Invoker()
                assert isinstance(invoker, InvokerCall), 'Invalid invoker %s' % invoker
                invoker.id = invokerId
                invoker.service = service
                invoker.call = call
                invoker.method = call.method
                invoker.inputs = tuple(iterateInputs(call))
                invoker.output = call.output
                invoker.location = locationStack(getattr(service.clazz, call.name))
                if call.definer.__module__ != service.clazz.__module__ or call.definer.__name__ != service.clazz.__name__:
                    invoker.location = '%s\n,inherited from %s' % (locationStack(service.clazz), invoker.location)
                invoker.doInvoke = getattr(implementation, call.name)
                register.invokers.append(invoker)
        
        if register.invokers: register.doCopyInvoker = self.doCopyInvoker

    # ----------------------------------------------------------------
    
    def doCopyInvoker(self, destination, source, exclude=None):
        '''
        Do copy the invoker.
        '''
        assert isinstance(destination, InvokerCall), 'Invalid destination %s' % destination
        assert isinstance(source, InvokerCall), 'Invalid source %s' % source
        assert exclude is None or isinstance(exclude, set), 'Invalid exclude %s' % exclude
        
        for name in attributesOf(destination):
            if exclude and name in exclude: continue
            value = getattr(destination, name)
            if value is not None: continue
            if not hasAttribute(source, name): continue
            value = getattr(source, name)
            if value is None: continue
            if isinstance(value, (set, list, dict, Context)):
                raise Exception('Cannot copy \'%s\' with value \'%s\'' % (name, value))
            setattr(destination, name, value)
        
        return destination
