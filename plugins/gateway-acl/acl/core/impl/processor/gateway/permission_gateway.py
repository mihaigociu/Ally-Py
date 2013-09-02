'''
Created on Aug 23, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Processor that adds the Gateway objects based on ACL permissions.
'''

from acl.api.access import Access
from ally.container.support import setup
from ally.design.processor.attribute import defines, requires, optional
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor, Handler
from collections import Iterable
from gateway.api.gateway import Gateway
import itertools
import re

# --------------------------------------------------------------------

HEADER_FILTER_INPUT = 'Filter-Input'
# The header name used to place the input filter.
PROPERTY_NAME = 'Property'
# The header filter input value associated with properties.

# --------------------------------------------------------------------
    
class Solicit(Context):
    '''
    The solicit context.
    '''
    # ---------------------------------------------------------------- Defined
    gateways = defines(Iterable, doc='''
    @rtype: Iterable(Gateway)
    The ACL gateways.
    ''')
    # ---------------------------------------------------------------- Optional
    rootURI = optional(str)
    replacements = optional(dict)
    # ---------------------------------------------------------------- Required
    permissions = requires(Iterable)

class Permission(Context):
    '''
    The permission context.
    '''
    # ---------------------------------------------------------------- Required
    access = requires(Access)
    filters = requires(dict)
    
# --------------------------------------------------------------------

@setup(Handler, name='registerPermissionGateway')
class RegisterPermissionGatewayHandler(HandlerProcessor):
    '''
    Provides the handler that adds the Gateway objects based on ACL permissions.
    '''
    
    def __init__(self):
        super().__init__(Permission=Permission)
    
    def process(self, chain, solicit:Solicit, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Adds the access permissions gateways.
        '''
        assert isinstance(solicit, Solicit), 'Invalid solicit %s' % solicit
        if not solicit.permissions: return
        
        if Solicit.rootURI in solicit: rootURI = solicit.rootURI
        else: rootURI = None
        if Solicit.replacements in solicit: replacements = solicit.replacements
        else: replacements = None
        
        gateways = self.iterateGateways(solicit.permissions, rootURI, replacements)
        if solicit.gateways is not None: solicit.gateways = itertools.chain(solicit.gateways, gateways)
        else: solicit.gateways = gateways
        
    # ----------------------------------------------------------------
    
    def iterateGateways(self, permissions, rootURI=None, replacements=None):
        '''
        Iterate the gateways for permissions.
        '''
        assert isinstance(permissions, Iterable), 'Invalid permissions %s' % permissions
        
        for perm in permissions:
            assert isinstance(perm, Permission), 'Invalid permission %s' % perm
            assert isinstance(perm.access, Access), 'Invalid permission access %s' % perm.access
            assert isinstance(perm.filters, dict), 'Invalid permission filters %s' % perm.filters
            assert isinstance(perm.access.Path, str), 'Invalid access path %s' % perm.access.Path
        
            pattern = '%s[\\/]?(?:\\.|$)' % '([^\\/]+)'.join(re.escape(pitem) for pitem in perm.access.Path.split('*'))
            if rootURI:
                assert isinstance(rootURI, str), 'Invalid root URI %s' % rootURI
                pattern = '%s\/%s' % (re.escape(rootURI), pattern)
            
            gateway = Gateway()
            gateway.Pattern = '^%s' % pattern
            gateway.Methods = [perm.access.Method]
            
            filtersEntry = filtersProperty = None
            for pathsEntry, pathsProperty in perm.filters.values():
                assert isinstance(pathsEntry, dict), 'Invalid indexed path entries %s' % pathsEntry
                # If there is a group with no filters will automatically cancel all other groups filters.
                if filtersEntry is None: filtersEntry = pathsEntry
                elif filtersEntry:
                    nfilters = {}
                    for position, paths in pathsEntry.items():
                        assert isinstance(paths, set), 'Invalid indexed paths %s' % paths
                        cpaths = filtersEntry.get(position)
                        if cpaths:
                            paths.update(cpaths)
                            nfilters[position] = paths
                    filtersEntry = nfilters
                    
                if filtersProperty is None: filtersProperty = pathsProperty
                elif filtersProperty:
                    nfilters = {}
                    for name, paths in pathsProperty.items():
                        assert isinstance(paths, set), 'Invalid indexed paths %s' % paths
                        cpaths = filtersProperty.get(name)
                        if cpaths:
                            paths.update(cpaths)
                            nfilters[position] = paths
                    filtersProperty = nfilters
                
                if not filtersEntry and not filtersProperty: break  # There are no more filters to process.
            
            if filtersEntry:
                for position in sorted(filtersEntry):
                    for path in sorted(filtersEntry[position]):
                        if gateway.Filters is None: gateway.Filters = []
                        assert isinstance(path, str), 'Invalid path %s' % path
                        if replacements: path = path % replacements
                        if rootURI: path = '%s/%s' % (rootURI, path)
                        gateway.Filters.append('%s:%s' % (position, path))
                        
            if filtersProperty:
                values = [PROPERTY_NAME]
                for name in sorted(filtersProperty):
                    paths = sorted(filtersProperty[name])
                    if rootURI:
                        for k, path in enumerate(paths): 
                            if replacements: path = path % replacements
                            paths[k] = '%s/%s' % (rootURI, path)
                    values.append('%s=%s' % (name, '|'.join(paths)))
                if gateway.PutHeaders is None: gateway.PutHeaders = {}
                gateway.PutHeaders[HEADER_FILTER_INPUT] = ';'.join(values)
            
            yield gateway
