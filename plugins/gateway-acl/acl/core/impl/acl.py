'''
Created on Aug 27, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Implementation for handling ACL service.
'''

from ..spec import IAclPermissionProvider
from acl.api.access import Access, Entry, Property
from acl.api.filter import Filter
from acl.meta.access import EntryMapped, PropertyMapped, AccessMapped
from acl.meta.acl import WithAclAccess
from acl.meta.acl_intern import Path
from acl.meta.filter import FilterMapped
from ally.api.error import IdError, InputError
from ally.api.type import typeFor
from ally.internationalization import _
from ally.support.api.util_service import modelId
from sql_alchemy.support.mapper import MappedSupport, mappingFor
from sql_alchemy.support.util_service import SessionSupport, iterateCollection
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.util import aliased
from sqlalchemy.sql.expression import distinct

# --------------------------------------------------------------------

PathFilter = aliased(Path)
# Alias to use for the path join.

class AclServiceAlchemy(SessionSupport, IAclPermissionProvider):
    '''
    Provides support for handling the ACL data. By ACL object is meant the object that has been configured to have the
    access mapping on it.
    '''
    
    def __init__(self, Acl, AclAccess):
        '''
        Construct the ACL service alchemy.
        
        @param Acl: Base class
            The ACL mapped class that organizes the ACL structure.
        '''
        assert isinstance(Acl, MappedSupport), 'Invalid mapped class %s' % Acl
        assert issubclass(AclAccess, WithAclAccess), 'Invalid acl access class %s' % AclAccess
        pks = [pk for pk in mappingFor(Acl).columns if pk.primary_key]
        assert pks, 'Cannot detect any primary key for %s' % Acl
        assert not len(pks) > 1, 'To many primary keys %s for %s' % (pks, Acl)
        
        self.Acl = Acl
        self.AclId = pks[0]
        self.AclIdentifier = modelId(Acl)
        self.AclAccess = AclAccess
        self.EntryFilter = AclAccess.EntryFilter
        self.PropertyFilter = AclAccess.PropertyFilter
    
    def getAcls(self, accessId, **options):
        '''
        @see: IACLPrototype.getAcls
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        
        sql = self.session().query(self.AclIdentifier).join(self.AclAccess)
        sql = sql.filter(self.AclAccess.accessId == accessId)
        return iterateCollection(sql, **options)
    
    def getAccesses(self, identifier, **options):
        '''
        @see: IACLPrototype.getAccesses
        '''
        sql = self.session().query(self.AclAccess.accessId).join(self.Acl)
        sql = sql.filter(self.AclIdentifier == identifier)
        return iterateCollection(sql, **options)
    
    def getEntriesFiltered(self, identifier, accessId, **options):
        '''
        @see: IACLPrototype.getEntriesFiltered
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        
        sql = self.session().query(distinct(EntryMapped.Position))
        sql = sql.join(self.EntryFilter).join(self.AclAccess).join(self.Acl)
        sql = sql.filter(self.AclAccess.accessId == accessId).filter(self.AclIdentifier == identifier)
        sql = sql.order_by(EntryMapped.Position)
        return iterateCollection(sql, **options)
    
    def getEntryFilters(self, identifier, accessId, entryPosition, **options):
        '''
        @see: IACLPrototype.getEntryFilters
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        assert isinstance(entryPosition, int), 'Invalid entry position %s' % entryPosition
        
        sql = self.session().query(FilterMapped.Name)
        sql = sql.join(self.EntryFilter).join(self.AclAccess).join(self.Acl).join(EntryMapped)
        sql = sql.filter(self.AclAccess.accessId == accessId).filter(self.AclIdentifier == identifier)
        sql = sql.filter(EntryMapped.Position == entryPosition)
        sql = sql.order_by(FilterMapped.Name)
        return iterateCollection(sql, **options)
    
    def getPropertiesFiltered(self, identifier, accessId, **options):
        '''
        @see: IACLPrototype.getPropertiesFiltered
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        
        sql = self.session().query(distinct(PropertyMapped.Name))
        sql = sql.join(self.PropertyFilter).join(self.AclAccess).join(self.Acl)
        sql = sql.filter(self.AclAccess.accessId == accessId).filter(self.AclIdentifier == identifier)
        sql = sql.order_by(PropertyMapped.Name)
        return iterateCollection(sql, **options)
    
    def getPropertyFilters(self, identifier, accessId, propertyName, **options):
        '''
        @see: IACLPrototype.getPropertyFilters
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        assert isinstance(propertyName, str), 'Invalid property name %s' % propertyName
        
        sql = self.session().query(FilterMapped.Name)
        sql = sql.join(self.PropertyFilter).join(self.AclAccess).join(self.Acl).join(PropertyMapped)
        sql = sql.filter(self.AclAccess.accessId == accessId).filter(self.AclIdentifier == identifier)
        sql = sql.filter(PropertyMapped.Name == propertyName)
        return iterateCollection(sql, **options)
    
    def addAcl(self, accessId, identifier):
        '''
        @see: IACLPrototype.addAcl
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        
        try: access = self.session().query(AccessMapped).filter(AccessMapped.Id == accessId).one()
        except: raise IdError(Access)
        assert isinstance(access, AccessMapped), 'Invalid access %s' % access
        
        sql = self.session().query(self.AclId)
        sql = sql.filter(self.AclIdentifier == identifier)
        try: aclId, = sql.one()
        except: raise IdError(typeFor(self.Acl))
        
        ids = [accessId]
        if access.Shadowing: ids.append(access.Shadowing)
        for id, in self.session().query(AccessMapped.Id).filter(AccessMapped.Shadowing == accessId).all(): ids.append(id)
    
        for accessId in ids:
            sql = self.session().query(self.AclAccess)
            sql = sql.filter(self.AclAccess.accessId == accessId).filter(self.AclAccess.aclId == aclId)
            if sql.count() > 0: continue
            
            aclAccess = self.AclAccess()
            aclAccess.accessId = accessId
            aclAccess.aclId = aclId
    
            self.session().add(aclAccess)
            
    def remAcl(self, accessId, identifier):
        '''
        @see: IACLPrototype.remAcl
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        
        sql = self.session().query(self.AclAccess).join(self.Acl)
        sql = sql.filter(self.AclAccess.accessId == accessId).filter(self.AclIdentifier == identifier)
        try: aclAccess = sql.one()
        except NoResultFound: return False
        
        self.session().delete(aclAccess)
        return True
    
    def addEntryFilter(self, accessId, identifier, entryPosition, filterName):
        '''
        @see: IACLPrototype.addEntryFilter
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        assert isinstance(entryPosition, int), 'Invalid entry position %s' % entryPosition
        assert isinstance(filterName, str), 'Invalid filter name %s' % filterName
        
        filterId, targetTypeId = self.filterObtain(filterName)
        sql = self.session().query(EntryMapped.id)
        sql = sql.filter(EntryMapped.accessId == accessId).filter(EntryMapped.Position == entryPosition)
        sql = sql.filter(EntryMapped.typeId == targetTypeId)
        if not sql.count(): raise InputError(_('Invalid filter for entry position'))
        
        self.assignEntryFilter(accessId, identifier, entryPosition, filterId)
        
    def remEntryFilter(self, accessId, identifier, entryPosition, filterName):
        '''
        @see: IACLPrototype.remEntryFilter
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        assert isinstance(entryPosition, int), 'Invalid entry position %s' % entryPosition
        assert isinstance(filterName, str), 'Invalid filter name %s' % filterName
        
        sql = self.session().query(self.EntryFilter).join(self.AclAccess).join(self.Acl).join(EntryMapped).join(FilterMapped)
        sql = sql.filter(self.AclAccess.accessId == accessId).filter(self.AclIdentifier == identifier)
        sql = sql.filter(EntryMapped.Position == entryPosition).filter(FilterMapped.Name == filterName)
        try: entryFilter = sql.one()
        except NoResultFound: return False
        
        self.session().delete(entryFilter)
        return True
    
    def addPropertyFilter(self, accessId, identifier, propertyName, filterName):
        '''
        @see: IACLPrototype.addPropertyFilter
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        assert isinstance(propertyName, str), 'Invalid property name %s' % propertyName
        assert isinstance(filterName, str), 'Invalid filter name %s' % filterName
        
        filterId, targetTypeId = self.filterObtain(filterName)
        sql = self.session().query(PropertyMapped.id)
        sql = sql.filter(PropertyMapped.accessId == accessId).filter(PropertyMapped.Name == propertyName)
        sql = sql.filter(PropertyMapped.typeId == targetTypeId)
        if not sql.count(): raise InputError(_('Invalid filter for property name'))
        
        self.assignPropertyFilter(accessId, identifier, propertyName, filterId)
        
    def remPropertyFilter(self, accessId, identifier, propertyName, filterName):
        '''
        @see: IACLPrototype.remPropertyFilter
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        assert isinstance(propertyName, str), 'Invalid property name %s' % propertyName
        assert isinstance(filterName, str), 'Invalid filter name %s' % filterName
        
        sql = self.session().query(self.PropertyFilter).join(self.AclAccess).join(self.Acl)
        sql = sql.join(PropertyMapped).join(FilterMapped)
        sql = sql.filter(self.AclAccess.accessId == accessId).filter(self.AclIdentifier == identifier)
        sql = sql.filter(PropertyMapped.Name == propertyName).filter(FilterMapped.Name == filterName)
        try: propertyFilter = sql.one()
        except NoResultFound: return False
        
        self.session().delete(propertyFilter)
        return True
    
    def registerFilter(self, accessId, identifier, filterName, place=None):
        '''
        @see: IACLPrototype.registerFilter
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        assert isinstance(filterName, str), 'Invalid filter name %s' % filterName
        
        try: access = self.session().query(AccessMapped).filter(AccessMapped.Id == accessId).one()
        except NoResultFound: raise IdError(Access)
        assert isinstance(access, AccessMapped), 'Invalid access %s' % access

        filterId, targetTypeId = self.filterObtain(filterName)
        sql = self.session().query(EntryMapped)
        sql = sql.filter(EntryMapped.accessId == accessId)
        entries = {entry.Position: entry for entry in sql.all()}
        
        filterEntries = []  # The compatible entries with the filter.
        for entry in entries.values():
            assert isinstance(entry, EntryMapped), 'Invalid entry %s' % entry
            if entry.typeId == targetTypeId: filterEntries.append(entry)
        
        sql = self.session().query(PropertyMapped)
        sql = sql.filter(PropertyMapped.accessId == accessId)
        properties = {prop.Name: prop for prop in sql.all()}
        
        filterProperties = []  # The compatible properties with the filter.
        for prop in properties.values():
            assert isinstance(prop, PropertyMapped), 'Invalid property %s' % prop
            if prop.typeId == targetTypeId: filterProperties.append(prop)
        
        if not filterEntries and not filterProperties: return False
        if len(filterEntries) + len(filterProperties) > 1:
            if place is None:
                raise InputError(_('Filter matches multiple entries and/or properties, a place is required to be specified'))
            filterEntries, filterProperties = self.determineFilterPlace(access, targetTypeId, place, entries, properties)
        
        for entry in filterEntries:
            self.assignEntryFilter(accessId, identifier, entry.Position, filterId)
            if entry.Shadowing is not None:  # Registering the filter also for the shadowing entry.
                self.assignEntryFilter(access.Shadowing, identifier, entry.Shadowing, filterId)
                    
        for prop in filterProperties:
            self.assignPropertyFilter(accessId, identifier, prop.Name, filterId)
            if access.Shadowing is not None:  # Registering the filter also for the shadowing property.
                self.assignPropertyFilter(access.Shadowing, identifier, prop.Name, filterId)
        
        if access.Shadowing is None:
            # Registering the filter also for the shadows, if any, of this access.
            sql = self.session().query(EntryMapped).select_from(AccessMapped).join(EntryMapped)
            sql = sql.filter(AccessMapped.Shadowing == accessId)
            
            shadows = {}
            for sentry in sql.all():
                assert isinstance(sentry, EntryMapped), 'Invalid entry %s' % sentry
                sentries = shadows.get(sentry.accessId)
                if sentries is None: sentries = shadows[sentry.accessId] = {}
                sentries[sentry.Shadowing] = sentry.Position
            
            for shadowId, sentries in shadows.items():
                for entry in filterEntries:
                    self.assignEntryFilter(shadowId, identifier, sentries[entry.Position], filterId)
                for prop in filterProperties:
                    self.assignPropertyFilter(shadowId, identifier, prop.Name, filterId)
 
        return True
    
    # --------------------------------------------------------------------
    
    def iteratePermissions(self, acl):
        '''
        @see: IACLPermissionProvider.iteratePermissions
        '''
        sql = self.session().query(AccessMapped, self.AclIdentifier, PathFilter.path, EntryMapped.Position, PropertyMapped.Name)
        sql = sql.select_from(self.AclAccess).join(self.Acl).join(AccessMapped).join(Path, AccessMapped.pathId == Path.id)
        sql = sql.outerjoin(self.EntryFilter).outerjoin(EntryMapped)
        sql = sql.outerjoin(self.PropertyFilter).outerjoin(PropertyMapped)
        sql = sql.outerjoin(FilterMapped, (self.EntryFilter.filterId == FilterMapped.id) | 
                                          (self.PropertyFilter.filterId == FilterMapped.id))
        sql = sql.outerjoin(PathFilter, FilterMapped.pathId == PathFilter.id)
        sql = sql.filter(self.AclIdentifier.in_(acl)).order_by(Path.priority, Path.path, self.AclAccess.accessId)
        
        current, filters = None, None
        for access, identifier, filterPath, entryPosition, propertyName in sql.yield_per(10):
            assert isinstance(access, AccessMapped), 'Invalid access %s' % access
            
            if current and current != access:
                yield current, filters
                current = None
            if current is None: current, filters = access, {}
            
            filtersAcl = filters.get(identifier)
            if filtersAcl is None: filtersAcl = filters[identifier] = {}, {}
            if filterPath is not None:
                pathsEntry, pathsProperty = filtersAcl
                
                if entryPosition is not None:
                    paths = pathsEntry.get(entryPosition)
                    if paths is None: paths = pathsEntry[entryPosition] = set()
                    paths.add(filterPath)
                
                if propertyName is not None:
                    paths = pathsProperty.get(propertyName)
                    if paths is None: paths = pathsProperty[propertyName] = set()
                    paths.add(filterPath)
        
        if current: yield current, filters
    
    # --------------------------------------------------------------------
    
    def aclAccessId(self, accessId, identifier):
        '''
        Provides the ACL access object.
        
        @param accessId: integer
            The access id.
        @param identifier: object
            The ACL object identifier.
        @return: integer
            The acl access id.
        '''
        sql = self.session().query(self.AclAccess.id).join(self.Acl)
        sql = sql.filter(self.AclAccess.accessId == accessId).filter(self.AclIdentifier == identifier)
        try: aclAccessId, = sql.one()
        except NoResultFound: raise InputError(_('Access not allowed'))
        return aclAccessId
    
    def filterObtain(self, filterName):
        '''
        Obtains the filter data.
        
        @param filterName: string
            The filter name to obtain data for,
        @return: tuple(integer, integer)
            Provides the filter id and target type id for the filter.
        '''
        assert isinstance(filterName, str), 'Invalid filter name %s' % filterName
        
        sql = self.session().query(FilterMapped.id, FilterMapped.typeId)
        sql = sql.filter(FilterMapped.Name == filterName)
        try: return sql.one()
        except NoResultFound: raise IdError(Filter)
    
    def assignEntryFilter(self, accessId, identifier, entryPosition, filterId):
        '''
        Register the filter at the provided entry position.
        
        @param accessId: integer
            The access id to register the filter with.
        @param identifier: object
            The ACL object identifier.
        @param entryPosition: integer
            The entry position to register the filter at.
        @param filterId: integer
            The filter id to register
        @param data: key arguments
            The data used to identify the category, by default a 'categoryId' is expected.
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        assert isinstance(entryPosition, int), 'Invalid position %s' % entryPosition
        assert isinstance(filterId, int), 'Invalid filter id %s' % filterId
        
        sql = self.session().query(EntryMapped.id).join(AccessMapped)
        sql = sql.filter(AccessMapped.Id == accessId).filter(EntryMapped.Position == entryPosition)
        try: entryId, = sql.one()
        except NoResultFound: raise IdError(Entry.Position)
        
        aclAccessId = self.aclAccessId(accessId, identifier)
        
        sql = self.session().query(self.EntryFilter)
        sql = sql.filter(self.EntryFilter.aclAccessId == aclAccessId)
        sql = sql.filter(self.EntryFilter.entryId == entryId).filter(self.EntryFilter.filterId == filterId)
        if sql.count() > 0: return  # Already assigned.
        
        entryFilter = self.EntryFilter()
        entryFilter.aclAccessId = aclAccessId
        entryFilter.entryId = entryId
        entryFilter.filterId = filterId
        
        self.session().add(entryFilter)
        
    def assignPropertyFilter(self, accessId, identifier, propertyName, filterId):
        '''
        Register the filter at the provided property name.
        
        @param accessId: integer
            The access id to register the filter with.
        @param identifier: object
            The ACL object identifier.
        @param propertyName: string
            The property name to register the filter at.
        @param filterId: integer
            The filter id to register
        @param data: key arguments
            The data used to identify the category, by default a 'categoryId' is expected.
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        assert isinstance(propertyName, str), 'Invalid property name %s' % propertyName
        assert isinstance(filterId, int), 'Invalid filter id %s' % filterId
        
        sql = self.session().query(PropertyMapped.id).join(AccessMapped)
        sql = sql.filter(AccessMapped.Id == accessId).filter(PropertyMapped.Name == propertyName)
        try: propertyId, = sql.one()
        except NoResultFound: raise IdError(Property.Name)
        
        aclAccessId = self.aclAccessId(accessId, identifier)
        
        sql = self.session().query(self.PropertyFilter)
        sql = sql.filter(self.PropertyFilter.aclAccessId == aclAccessId)
        sql = sql.filter(self.PropertyFilter.propertyId == propertyId).filter(self.PropertyFilter.filterId == filterId)
        if sql.count() > 0: return  # Already assigned.

        propertyFilter = self.PropertyFilter()
        propertyFilter.aclAccessId = aclAccessId
        propertyFilter.propertyId = propertyId
        propertyFilter.filterId = filterId
        
        self.session().add(propertyFilter)
        
    def determineFilterPlace(self, access, targetTypeId, place, entries, properties):
        '''
        Determines the filter position and properties based on the provided place hint.
        
        @param access: AccessMapped
            The access to determine the place for.
        @param targetTypeId: integer
            The filter target type id to determine place for.
        @param place: string
            The place pattern.
        @param entries: dictionary{integer: EntryMapped}
            The entries for access indexed by position.
        @param properties: dictionary{string: PropertyMapped}
            The properties for access indexed by name.
        @return: tuple(list[EntryMapped], list[PropertyMapped])
            The entries and properties where the filter is placed.
        '''
        assert isinstance(access, AccessMapped), 'Invalid access %s' % access
        assert isinstance(targetTypeId, int), 'Invalid filter target type id %s' % targetTypeId
        assert isinstance(place, str), 'Invalid place %s' % place
        assert isinstance(entries, dict), 'Invalid entries %s' % entries
        assert isinstance(properties, dict), 'Invalid properties %s' % properties
        
        place = place.strip().split('#', 1)
        if len(place) > 1: placeEntries, placeProperties = place
        else: placeEntries, placeProperties = place[0], ''
        
        filterEntries, filterProperties = [], []
        
        try:
            if placeEntries:
                markers, items = placeEntries.strip().strip('/').split('/'), access.Path.split('/')
            
                if len(items) == len(markers):
                    position = 0
                    for mark, item in zip(markers, items):
                        if item == '*':
                            position += 1
                            if mark == '@':
                                entry = entries.get(position)
                                if entry.typeId != targetTypeId:
                                    raise InputError(_('Invalid filter path place preference at position %(position)s, '
                                                       'it is not compatible with the filter'), position=position)
                                filterEntries.append(entry)
                                continue
                            
                        if mark != item:
                            raise InputError(_('Invalid filter path place item %(item)s, needs to match %(path)s'),
                                             item=mark, path=access.Path)
                else:
                    raise InputError(_('Invalid filter path place, needs to match %(path)s'), path=access.Path)
                
            if placeProperties:
                for name in placeProperties.strip().split(','):
                    prop = properties.get(name.strip())
                    if prop is None: raise InputError(_('Unknown filter property place \'%(name)s\''), name=name)
                    assert isinstance(prop, PropertyMapped), 'Invalid property %s' % prop
                    if prop.typeId != targetTypeId:
                        raise InputError(_('Invalid filter property place %(name)s, it is not compatible '
                                           'with the filter'), name=name)
                    filterProperties.append(prop)
                    
            if not filterEntries and not filterProperties:
                raise InputError(_('Invalid filter place \'%(place)s\' has not valid location preference'), place=place)
                
        except InputError as e:
            assert isinstance(e, InputError)
            # We generate a samples for place
            position, items, inPath, props = 0, [], False, []
            for item in access.Path.split('/'):
                if item == '*':
                    position += 1
                    entry = entries.get(position)
                    if entry.typeId == targetTypeId:
                        items.append('@')
                        inPath = True
                        continue
                items.append(item)
                
            for name, prop in properties.items():
                if prop.typeId == targetTypeId: props.append(name)
            
            if inPath: place = '/'.join(items)
            else: place = ''
            if props: place = '%s#%s' % (place, ','.join(props))
            
            e.update(_('Use place \'%(sample)s\' in order to add the filter on all available places'), sample=place)
            raise e
                
        return filterEntries, filterProperties
