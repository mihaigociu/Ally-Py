'''
Created on Aug 12, 2013

@package: gateway acl
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Indexes the filters invokers.
'''

from acl.api.filter import IFilterService, Filter
from acl.core.spec import uniqueNameFor
from ally.api.operator.type import TypeProperty
from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.design.processor.attribute import requires, optional
from ally.design.processor.context import Context
from ally.design.processor.execution import Abort
from ally.design.processor.handler import HandlerProcessor, Handler
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

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
    # ---------------------------------------------------------------- Optional
    filterInjected = optional(dict)
    # ---------------------------------------------------------------- Required
    path = requires(list)
    filterName = requires(str)
    location = requires(str)

class Element(Context):
    '''
    The element context.
    '''
    # ---------------------------------------------------------------- Required
    name = requires(str)
    property = requires(TypeProperty)

# --------------------------------------------------------------------

@injected
@setup(Handler, name='indexFilter')
class IndexFilterHandler(HandlerProcessor):
    '''
    Implementation for a processor that indexes the filters invokers.
    '''
    
    filterService = IFilterService; wire.entity('filterService')
    
    def __init__(self):
        assert isinstance(self.filterService, IFilterService), 'Invalid filter service %s' % self.filterService
        super().__init__(Invoker=Invoker, Element=Element)

    def process(self, chain, register:Register, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Merge the filter invokers.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        if not register.invokers: return
        
        invokers = {}
        for invoker in register.invokers:
            assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
            if invoker.filterName is None: continue
            
            finvokers = invokers.get(invoker.filterName)
            if finvokers is None: finvokers = invokers[invoker.filterName] = []
            finvokers.append(invoker)
        
        aborted, invokersFilters = [], []
        for name, finvokers in invokers.items():
            if len(finvokers) > 1:
                log.error('Cannot use filters invokers because they have the same name \'%s\', at:%s',
                          name, ''.join(invk.location for invk in invokers))
                aborted.extend(finvokers)
            invokersFilters.append(finvokers[0])
        
        filters = []
        for invoker in invokersFilters:
            filtre = Filter()
            filters.append(filtre)
            filtre.Name = invoker.filterName
            
            items = []
            for el in invoker.path:
                assert isinstance(el, Element), 'Invalid element %s' % el
                if el.property:
                    if Invoker.filterInjected in invoker and invoker.filterInjected and el in invoker.filterInjected:
                        items.append(invoker.filterInjected[el])
                    else:
                        if filtre.Type is not None:
                            log.error('Cannot use filter invoker because there are to many possible targets, at:%s',
                                      invoker.location)
                            aborted.append(invoker)
                            break
                        filtre.Type = uniqueNameFor(el.property)
                        items.append('*')
                else:
                    assert isinstance(el.name, str), 'Invalid element name %s' % el.name
                    items.append(el.name)
            else:
                filtre.Path = '/'.join(items)
                if filtre.Type is None:
                    log.error('Cannot use filter invoker because there is no target, at:%s', invoker.location)
                    aborted.append(invoker)
            
        if aborted: raise Abort(*aborted)
        
        self.mergeFilters(filters)
            
    # ----------------------------------------------------------------
    
    def mergeFilters(self, filters):
        '''
        Persist the filter.
        '''
        for filtre in filters:
            assert isinstance(filtre, Filter), 'Invalid filter %s' % filtre
        
            try: present = self.filterService.getById(filtre.Name)
            except: assert log.debug('There is no filter for \'%s\'', filtre.Name) or True
            else:
                assert isinstance(present, Filter), 'Invalid filter %s' % present
                if present.Type == filtre.Type: continue
                log.info('Removing filter %s since is not compatible with the current structure', present)
                self.filterService.delete(filtre.Name)
            
            self.filterService.insert(filtre)
            assert log.debug('Added filter %s', filtre) or True
