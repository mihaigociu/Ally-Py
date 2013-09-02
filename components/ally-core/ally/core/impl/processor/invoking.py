'''
Created on Jun 30, 2011

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the invoking handler.
'''

from ally.api.config import GET, INSERT, UPDATE, DELETE
from ally.api.error import InputError
from ally.api.type import Input
from ally.core.error import DevelError
from ally.core.spec.codes import INPUT_ERROR, INSERT_ERROR, INSERT_SUCCESS, \
    UPDATE_SUCCESS, UPDATE_ERROR, DELETE_SUCCESS, DELETE_ERROR, Coded
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.support.api.util_service import isModelId
from ally.support.util_spec import IDo
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Required
    method = requires(int)
    inputs = requires(tuple)
    namedArguments = requires(set)
    location = requires(str)
    doInvoke = requires(IDo)
        
class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    invoker = requires(Context)
    arguments = requires(dict)

class Response(Coded):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Defined
    obj = defines(object, doc='''
    @rtype: object
    The response object.
    ''')
    errorInput = defines(InputError, doc='''
    @rtype: InputError
    The input error that occurred while invoking.
    ''')

# --------------------------------------------------------------------

class InvokingHandler(HandlerProcessor):
    '''
    Implementation for a processor that makes the actual call to the request method corresponding invoke. The invoking will
    use all the obtained arguments from the previous processors and perform specific actions based on the requested method.
    '''

    def __init__(self):
        '''
        Construct the handler.
        '''
        super().__init__(Invoker=Invoker)

        self.invokeCallBack = {
                               GET: self.afterGet,
                               INSERT: self.afterInsert,
                               UPDATE: self.afterUpdate,
                               DELETE: self.afterDelete
                               }

    def process(self, chain, request:Request, response:Response, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Invoke the request invoker.
        '''
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response
        if response.isSuccess is False: return  # Skip in case the response is in error

        invoker = request.invoker
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        if invoker.doInvoke is None: return  # No invoke to process
        
        assert isinstance(invoker.doInvoke, IDo), 'Invalid invoker invoke %s' % invoker.doInvoke
        callBack = self.invokeCallBack.get(invoker.method)
        assert callBack is not None, 'Cannot process invoker, at:%s' % invoker.location
        
        if request.arguments is None: arguments = {}
        else: arguments = dict(request.arguments)
        
        args, keyargs = [], {}
        for inp in invoker.inputs:
            assert isinstance(inp, Input), 'Invalid input %s' % inp
            
            isKeyArg = invoker.namedArguments and inp.name in invoker.namedArguments
            
            if inp.name in arguments: value = arguments[inp.name]
            elif isKeyArg:
                if inp.hasDefault: keyargs[inp.name] = inp.default
                continue
            elif inp.hasDefault:
                args.append(inp.default)
                continue
            else:
                raise DevelError('No value for mandatory input \'%s\', at:%s' % (inp.name, invoker.location))
            
            if isKeyArg: keyargs[inp.name] = value
            else: args.append(value)
        try:
            value = invoker.doInvoke(*args, **keyargs)
            assert log.debug('Successful on calling with arguments %s and key arguments %s, at:%s', invoker,
                             args, keyargs, invoker.location) or True

            callBack(invoker, value, response)
        except InputError as e:
            assert isinstance(e, InputError)
            INPUT_ERROR.set(response)
            response.errorInput = e
            assert log.debug('User input exception: %s', e, exc_info=True) or True

    # ----------------------------------------------------------------

    def afterGet(self, invoker, value, response):
        '''
        Process the after get action on the value.
        
        @param invoker: Invoker
            The invoker used.
        @param value: object
            The value returned.
        @param response: Response
            The response to set the error if is the case.
        @return: boolean
            False if the invoking has failed, True for success.
        '''
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        assert isinstance(response, Response), 'Invalid response %s' % response
        assert invoker.output.isValid(value), 'Invalid return value \'%s\' for invoker %s' % (value, invoker)
        
        response.obj = value

    def afterInsert(self, invoker, value, response):
        '''
        Process the after insert action on the value.
        
        @param invoker: Invoker
            The invoker used.
        @param value: object
            The value returned.
        @param response: Response
            The response to set the error if is the case.
        @return: boolean
            False if the invoking has failed, True for success.
        '''
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        assert isinstance(response, Response), 'Invalid response %s' % response
        assert invoker.output.isValid(value), 'Invalid return value \'%s\' for invoker %s' % (value, invoker)

        if isModelId(invoker.output):
            if value is not None:
                response.obj = value
            else:
                INSERT_ERROR.set(response)
                assert log.debug('Cannot insert resource') or True
                return
        else:
            response.obj = value
        INSERT_SUCCESS.set(response)

    def afterUpdate(self, invoker, value, response):
        '''
        Process the after update action on the value.
        
        @param invoker: Invoker
            The invoker used.
        @param value: object
            The value returned.
        @param response: Response
            The response to set the error if is the case.
        @return: boolean
            False if the invoking has failed, True for success.
        '''
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        assert isinstance(response, Response), 'Invalid response %s' % response
        assert invoker.output.isValid(value), 'Invalid return value \'%s\' for invoker %s' % (value, invoker)

        if invoker.output.isOf(None):
            UPDATE_SUCCESS.set(response)
            assert log.debug('Successful updated resource') or True
        elif invoker.output.isOf(bool):
            if value == True:
                UPDATE_SUCCESS.set(response)
                assert log.debug('Successful updated resource') or True
            else:
                UPDATE_ERROR.set(response)
                assert log.debug('Cannot update resource') or True
        else:
            # If an entity is returned than we will render that.
            UPDATE_SUCCESS.set(response)
            response.obj = value

    def afterDelete(self, invoker, value, response):
        '''
        Process the after delete action on the value.
        
        @param invoker: Invoker
            The invoker used.
        @param value: object
            The value returned.
        @param response: Response
            The response to set the error if is the case.
        @return: boolean
            False if the invoking has failed, True for success.
        '''
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        assert isinstance(response, Response), 'Invalid response %s' % response
        assert invoker.output.isValid(value), 'Invalid return value \'%s\' for invoker %s' % (value, invoker)

        if invoker.output.isOf(bool):
            if value == True:
                DELETE_SUCCESS.set(response)
                assert log.debug('Successfully deleted resource') or True
            else:
                DELETE_ERROR.set(response)
                assert log.debug('Cannot deleted resource') or True
        else:
            # If an entity is returned than we will render that.
            DELETE_SUCCESS.set(response)
            response.obj = value
