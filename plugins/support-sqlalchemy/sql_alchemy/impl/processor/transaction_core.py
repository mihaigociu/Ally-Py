'''
Created on Jan 5, 2012

@package: support sqlalchemy
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides automatic session handling for SQL alchemy in ally core.
'''

from ally.api.config import DELETE, GET
from ally.api.error import InputError, IdError
from ally.core.spec.codes import INPUT_ERROR, Coded
from ally.design.processor.attribute import optional, defines, requires
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain, Error
from ally.design.processor.handler import HandlerProcessor
from ally.internationalization import _
from sql_alchemy.support.session import rollback, commit, setKeepAlive, \
    endSessions
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import NoResultFound
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
        
class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    invoker = requires(Context)
    
class Response(Coded):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Defined
    errorInput = defines(InputError, doc='''
    @rtype: InputError
    The input error translated from SQL alchemy error.
    ''')
    # ---------------------------------------------------------------- Optional
    isSuccess = optional(bool)

# --------------------------------------------------------------------

class TransactionCoreHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the SQLAlchemy session handling in ally core.
    '''
    
    def __init__(self):
        super().__init__(request=Request, response=Response, Invoker=Invoker)

    def process(self, chain, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Wraps the invoking and all processors after in a single transaction.
        '''
        assert isinstance(chain, Chain), 'Invalid processors chain %s' % chain

        setKeepAlive(True)
        chain.onError(self.processError)
        chain.onFinalize(self.processFinalize)
    
    def processError(self, error, request, response, **keyargs):
        '''
        Process the transaction error.
        '''
        assert isinstance(error, Error), 'Invalid error %s' % error
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response
        assert isinstance(error.exception, Exception), 'Invalid error exception %s' % error.exception
        assert isinstance(request.invoker, Invoker), 'Invalid invoker %s' % request.invoker
        
        exc = None
        if isinstance(error.exception, NoResultFound): exc = IdError()
        elif isinstance(error.exception, IntegrityError):
            exc = InputError(_('There is already an entity having this unique properties'))
        elif isinstance(error.exception, OperationalError):
            if request.invoker.method == DELETE: exc = InputError(_('Cannot delete because is used'))
            elif request.invoker.method != GET: exc = InputError(_('An entity relation identifier is not valid'))
            
        if exc is not None:
            log.info('SQL Alchemy handled exception occurred',
                     exc_info=(type(error.exception), error.exception, error.exception.__traceback__))
            INPUT_ERROR.set(response)
            exc.with_traceback(error.exception.__traceback__)
            response.errorInput = exc
            error.retry()
    
    def processFinalize(self, final, response, **keyargs):
        '''
        Process the finalize of the transaction.
        '''
        assert isinstance(response, Response), 'Invalid response %s' % response
        setKeepAlive(False)
        
        if Response.isSuccess in response:
            if response.isSuccess is True: endSessions(commit)
            else: endSessions(rollback)
        else: endSessions(commit)  # Commit if there is no success flag
            
