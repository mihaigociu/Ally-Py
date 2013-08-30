'''
Created on Jul 18, 2013

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides definition specifications. 
'''

from ally.support.util_context import IPrepare
import abc

# --------------------------------------------------------------------

class IVerifier(IPrepare):
    '''
    Description verifier for definition specification.
    '''
    
    @abc.abstractmethod
    def isValid(self, definition):
        '''
        Checks if the provided definition is valid for the verifier.
        
        @param definition: Context
            The definition to check.
        @return: boolean
            True if the definition is checked by the verifier, False otherwise.
        '''

class IValue(metaclass=abc.ABCMeta):
    '''
    Description value provider for definition specification.
    '''
    
    def prepare(self, resolvers):
        '''
        Prepare the resolvers contexts for the value fetching.
        
        @param resolvers: dictionary{string, IResolver}
            The resolvers to prepare.
        '''
    
    @abc.abstractmethod
    def get(self, definition):
        '''
        Provides the values associated with the definition.
        
        @param definition: Context
            The definition to get the values for.
        @return: object
            The definition value.
        '''  
