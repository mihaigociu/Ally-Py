'''
Created on Jul 18, 2013

@package: ally base
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides utility functions for processor contexts.
'''

from .util import Singletone
from ally.design.processor.context import Context, Object, attributeOf
from ally.design.processor.spec import ContextMetaClass, IAttribute, IResolver
from collections import Iterable
import abc

# --------------------------------------------------------------------

class IPrepare(metaclass=abc.ABCMeta):
    '''
    Specification for classes that perform different actions that require context classes. 
    '''
    
    @abc.abstractmethod
    def prepare(self, resolvers):
        '''
        Prepare the resolvers contexts.
        
        @param resolvers: dictionary{string, IResolver}
            The resolvers to prepare.
        '''

# --------------------------------------------------------------------

def attributesOf(context, withAttrs=False):
    '''
    Provides the context attributes names and attributes.
    
    @param context: ContextMetaClass|Context
        The context or context class to provide the attributes names for.
    @param withAttrs: boolean
        Flag indicating that the attributes should be iterated also.
    @return: set(string)|Iterable(tuple(string, IAttribute))
        The set with attribute names if 'withAttrs' flag is False otherwise an iterable with the names and attribute.
    '''
    if isinstance(context, Context): context = context.__class__
    assert isinstance(context, ContextMetaClass), 'Invalid context %s' % context
    if withAttrs: return context.__attributes__.items()
    return set(context.__attributes__)

def asData(context, *classes):
    '''
    Provides the data that is represented in the provided context classes.
    
    @param context: object
        The context object to get the data from.
    @param classes: arguments[ContextMetaClass]
        The context classes to construct the data based on.
    '''
    assert isinstance(context, Context), 'Invalid context %s' % context

    common = set(context.__attributes__)
    for clazz in classes:
        assert isinstance(clazz, ContextMetaClass), 'Invalid context class %s' % clazz
        common.intersection_update(clazz.__attributes__)
        
    data = {}
    for name in common:
        if context.__attributes__[name] in context: data[name] = getattr(context, name)

    return data

def hasAttribute(context, name):
    '''
    Checks if the context has an attribute for name.
    
    @param context: ContextMetaClass|Context
        The context or context class to check the attribute for.
    @param name: string
        The attribute name to check.
    @return: boolean
        True if the context has the attribute, False otherwise.
    '''
    if isinstance(context, Context): context = context.__class__
    assert isinstance(context, ContextMetaClass), 'Invalid context %s' % context
    assert isinstance(name, str), 'Invalid name %s' % name
    return name in context.__attributes__

# --------------------------------------------------------------------

def pushIn(dest, *srcs, interceptor=None, exclude=None, only=None):
    '''
    Pushes in the destination context data from the source context(s).
    
    @param dest: object
        The destination context object to get the data from.
    @param srcs: arguments[Context|dictionary{string: object}]
        Sources to copy data from, attention the order is important since if the first context has no value
        for an attribute then the second one is checked and so on.
    @param interceptor: callable(object) -> object|None
        An interceptor callable to be called before setting the value on the destination.
    @param exclude: string|ContextMetaClass|Iterable(string|ContextMetaClass)|None
        The attribute(s) of ContextMetaClass to be excluded from the push.
    @param only: string|ContextMetaClass|Iterable(string|ContextMetaClass)|None
        The attribute(s) of ContextMetaClass to be pushed only.
    @return: object
        The destination context after copy.
    '''
    assert isinstance(dest, Object), 'Invalid destination context %s' % dest
    assert srcs, 'At least one source is required'
    assert interceptor is None or callable(interceptor), 'Invalid interceptor %s' % interceptor
    
    if exclude is not None:
        excludes = set()
        if isinstance(exclude, ContextMetaClass): excludes.update(exclude.__attributes__) 
        elif isinstance(exclude, str): excludes.add(exclude)
        else:
            assert isinstance(exclude, Iterable), 'Invalid exclude %s' % exclude
            for name in exclude:
                if isinstance(name, ContextMetaClass): excludes.update(name.__attributes__)
                else:
                    assert isinstance(name, str), 'Invalid exclude name %s' % name
                    excludes.add(name)
    else: excludes = frozenset()
    
    if only is not None:
        attributes = set(dest.__attributes__)
        if isinstance(only, ContextMetaClass): attributes.intersection_update(only.__attributes__) 
        elif isinstance(only, str): attributes.intersection_update((only,))
        else:
            assert isinstance(only, Iterable), 'Invalid only %s' % only
            for name in only:
                if isinstance(name, ContextMetaClass): attributes.intersection_update(name.__attributes__)
                else:
                    assert isinstance(name, str), 'Invalid only name %s' % name
                    attributes.intersection_update((name,))
    else: attributes = dest.__attributes__
    
    for name in attributes:
        if name in excludes: continue
        found = False
        for src in srcs:
            if isinstance(src, Context):
                attribute = src.__attributes__.get(name)
                if attribute and attribute in src: found, value = True, getattr(src, name)
            else:
                assert isinstance(src, dict), 'Invalid source %s' % src
                if name in src: found, value = True, src[name]
            
            if found:
                if interceptor is not None: value = interceptor(value)
                setattr(dest, name, value)
                break
    
    return dest

def cloneCollection(value):
    '''
    Interceptor to be used on the 'pushIn' function that creates new collections with the same items.
    The collections copied are: set, dict, list.
    
    @param value: object
        The value to intercept.
    @return: object
        The clone collection if is the case or the same value.
    '''
    if value is None: return
    clazz = value.__class__
    if clazz == set: return set(value)
    elif clazz == dict: return dict(value)
    elif clazz == list: return list(value)
    return value

# --------------------------------------------------------------------

def iterate(context, nextCall, maximum=1000):
    '''
    Iterates all the contexts found based on the next call, also the first context (the provided one will be iterated).
    
    @param context: Context
        The first context to start the iteration.
    @param nextCall: callable(Context) -> Context|None
        The call used to fetch the next context from the current one.
    @return: Iterator(Context)
        The iterated contexts.
    '''
    assert isinstance(context, Context), 'Invalid context %s' % context
    assert callable(nextCall), 'Invalid next callable %s' % nextCall
    
    while context is not None:
        assert isinstance(context, Context), 'Invalid context %s' % context
        if maximum <= 0: break
        yield context
        maximum -= 1
        context = nextCall(context)

def listing(context, search, attribute=None, **keyargs):
    '''
    Lists all the contexts found based on the search attribute, also the first context (the provided one will be listed).
    
    @param context: Context
        The first context to start the listing.
    @param search: Context.attribute(Context)
        The context attribute to do the listing based on.
    @param attribute: Context.attribute|None
        The context attribute to provide the value for, if None the contexts will be placed in the list.
    @return: list[object]
        The found contexts or values.
    '''
    assert isinstance(context, Context), 'Invalid context %s' % context
    sattr = attributeOf(search)
    assert isinstance(sattr, IAttribute), 'Invalid search attribute %s' % search
    if attribute:
        attr = attributeOf(attribute)
        assert isinstance(attr, IAttribute), 'Invalid attribute %s' % attribute
    else: attr = None
    
    contexts = iterate(context, lambda context: getattr(context, sattr.__name__) if sattr in context else None, **keyargs)
    if attr: return [getattr(context, attr.__name__) for context in contexts]
    return list(contexts)

def findFirst(context, search, attrOrCall, **keyargs):
    '''
    Finds the first value that is not None for the provided attribute, the search will be made based on the search 
    attribute which must be for a context.
    
    @param context: Context
        The context to search in.
    @param search: Context.attribute(Context)
        The context attribute to search based on.
    @param attribute: Context.attribute|callable(Context) -> object
        The context attribute to provide the first value for, or a call that takes the context as a value
        an whenever returns a not None value it means the value has been found.
    @return: object|None
        The found value or None if no value could be found.
    '''
    assert isinstance(context, Context), 'Invalid context %s' % context
    sattr = attributeOf(search)
    assert isinstance(sattr, IAttribute), 'Invalid search attribute %s' % search
    if callable(attrOrCall): call = attrOrCall
    else:
        attr = attributeOf(attrOrCall)
        assert isinstance(attr, IAttribute), 'Invalid attribute or call %s' % attrOrCall
        call = lambda context: getattr(context, attr.__name__)
    
    for context in iterate(context, lambda context: getattr(context, sattr.__name__) if sattr in context else None, **keyargs):
        assert isinstance(context, Context), 'Invalid context %s' % context
        value = call(context)
        if value is not None: return value

# --------------------------------------------------------------------

class PlaceHolder(Singletone, IResolver):
    '''
    The context resolver that simply is there by name with not other functionality, this is some times useful
    when there are assemblies that keep in account what is defined or not.
    '''
        
    def copy(self, names=None):
        '''
        @see: IResolver.copy
        '''
        return self

    def merge(self, other, isFirst=True):
        '''
        @see: IResolver.merge
        '''
        return other
        
    def solve(self, other):
        '''
        @see: IResolver.solve
        '''
        return other
        
    def list(self, *flags):
        '''
        @see: IResolver.list
        '''
        assert not flags, 'Unknown flags: %s' % ', '.join(flags)
        return {}
    
    def create(self, *flags):
        '''
        @see: IResolver.create
        '''
        assert not flags, 'Unknown flags: %s' % ', '.join(flags)
        return {}
