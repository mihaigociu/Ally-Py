'''
Created on Aug 19, 2013

@package: support sqlalchemy
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides a SQL alchemy transaction handling, this processor can be generally used in assembly that work with database.
'''

from ally.design.processor.execution import Chain
from ally.design.processor.handler import HandlerProcessor
from sql_alchemy.support.session import rollback, commit, setKeepAlive, \
    endSessions

# --------------------------------------------------------------------

class TransactionHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the SQLAlchemy transaction handling.
    '''

    def process(self, chain, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Process the chain in a single transaction.
        '''
        assert isinstance(chain, Chain), 'Invalid processors chain %s' % chain

        setKeepAlive(True)
        chain.onError(self.processRollback)
        chain.onFinalize(self.processCommit)
    
    def processRollback(self, error, **keyargs):
        '''
        Process the transaction error.
        '''
        endSessions(rollback)
    
    def processCommit(self, final, **keyargs):
        '''
        Process the end of the transaction.
        '''
        setKeepAlive(False)
        endSessions(commit)
            
