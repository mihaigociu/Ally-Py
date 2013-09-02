'''
Created on Jun 9, 2011

@package: ally base
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides implementations that provide general behavior or functionality.
'''

from collections import Iterable, Iterator, namedtuple, deque
from inspect import isclass
from weakref import WeakKeyDictionary
import re

# --------------------------------------------------------------------

class Uninstantiable:
    '''
    Extending this class will not allow for the creation of any instance of the class.
    This has to be the first class inherited in order to properly work.
    '''

    def __new__(cls, *args, **keyargs):
        '''
        Does not allow you to create an instance.
        '''
        raise Exception('Cannot create an instance of \'%s\' class' % cls.__name__)

class Singletone:
    '''
    Extending this class will always return the same instance.
    '''

    def __new__(cls):
        '''
        Will always return the same instance.
        '''
        try: return cls._ally_singletone
        except AttributeError: cls._ally_singletone = super().__new__(cls)
        return cls._ally_singletone

class MetaClassUnextendable(type):
    '''
    Provides a meta class that doesn't allow for any class extension.
    '''

    def __new__(cls, name, bases, namespace):
        raise TypeError('Cannot extend class in %s' % bases)

# --------------------------------------------------------------------

def tupleify(*names):
    '''
    Creates a tuple based on a provided class. This method is just to be able to cover up the "namedtuple" from collections
    in order to allow type hinting to work.
    
    @param names: arguments[string]
        The field names in the proper order @see: namedtuple
    '''
    def decorator(clazz):
        assert isclass(clazz), 'Invalid class %s' % clazz
        return namedtuple(clazz.__name__, names)
    return decorator

class Referencer:
    '''
    Creates a referencer for the provided class. The referencer can be used in order to get class function references.
    '''
    
    __slots__ = ('_ally_referencer_class',)
    
    def __init__(self, clazz):
        '''
        Construct the referencer.
                
        @param clazz: class
            The class to create the referencer for.
        '''
        assert isclass(clazz), 'Invalid class %s' % clazz
        self._ally_referencer_class = clazz
    
    def __getattr__(self, name):
        '''
        Provides the reference for the function name.
        
        @param name: string
            The function name to provide the reference for.
        @return: tuple(class, string)
            The reference tuple.
        '''
        function = getattr(self._ally_referencer_class, name)
        if not callable(function): raise AttributeError('Invalid function name \'%s\'' % name)
        return self._ally_referencer_class, name

def ref(clazz):
    '''
    Creates a referencer for the provided class. The referencer can be used in order to get class function references.
    example:
        ref(MyClass).doSomething = tuple(MyClass, 'doSomething')
        
    @param clazz: class
        The class to create the referencer for.
    @return: Referencer
        The referencer for the provided class.
    '''
    references = globals().get('_ally_referenceres')
    if references is None: references = globals()['_ally_referenceres'] = WeakKeyDictionary()
    referencer = references.get(clazz)
    if referencer is None: referencer = references[clazz] = Referencer(clazz)
    return referencer

def iterRef(refs):
    '''
    Iterates the provided references by grouping based on class.
    
    @param refs: Iterable(tuple(class, string))
        The references to group by class.
    @return: dictionary{class: list[string]}
        The dictionary that has as a key the class then the list with the function names for that class.
    '''
    assert isinstance(refs, Iterable), 'Invalid references %s' % refs
    indexed = {}
    for ref in refs:
        assert isinstance(ref, tuple), 'Invalid reference %s' % ref
        clazz, name = ref
        assert isclass(clazz), 'Invalid reference class %s' % clazz
        assert isinstance(name, str), 'Invalid reference function name %s' % name
        names = indexed.get(clazz)
        if names is None: names = indexed[clazz] = []
        names.append(name)
    return indexed

def iterRefClass(refsClass):
    '''
    Iterates the provided references or classes by grouping based on class.
    
    @param refsClass: Iterable(class|tuple(class, string))
        The references or classes to group by class.
    @return: dictionary{class: list[string]|None}
        The dictionary that provides hat has as a key the class then the list with the function names for that class.
        If there are no functions for the class then instead of the list a None value will be provided.
    '''
    assert isinstance(refsClass, Iterable), 'Invalid references %s' % refsClass
    refs, classes = [], set()
    for ref in refsClass:
        if isclass(ref): classes.add(ref)
        else: refs.append(ref)
    indexed = iterRef(refs)
    if not classes.isdisjoint(indexed):
        for clazz, ref in indexed.items():
            if clazz in classes:
                raise ValueError('Cannot have also reference and also a simple class for %s, please either '
                                 'remove reference %s or the class' % (clazz, ref))
    indexed.update((clazz, None) for clazz in classes)
    return indexed

# --------------------------------------------------------------------

class immut(dict):
    '''The immutable dictionary class'''

    __slots__ = ('__hash__value',)

    def __new__(cls, *args, **keyargs):
        if not (args or keyargs):
            try: return cls.__empty__
            except AttributeError: cls.__empty__ = dict.__new__(cls)
            return cls.__empty__
        return dict.__new__(cls, *args, **keyargs)

    def update(self, *args, **keyargs): raise AttributeError('Operation not allowed on immutable dictionary')
    __setitem__ = __delitem__ = setdefault = pop = popitem = clear = update

    def __hash__(self):
        '''
        Provides the hash code for a immutable dictionary.
        '''
        try: return self.__hash__value
        except AttributeError: self.__hash__value = hash(tuple(p for p in self.items()))
        return self.__hash__value

class FlagSet(set):
    '''
    Extension of a set that provides easy management for string flags.
    '''
    __slots__ = ()
    
    def __init__(self, flags):
        super().__init__(flags)
        if __debug__:
            for flag in self: assert isinstance(flag, str), 'Invalid flag %s' % flag
                
    def checkOnce(self, flag):
        '''
        Checks if the provided flag is in this flag set after the check the flag will get removed.
        
        @param flag: string
            The flag to check.
        @return: boolean
            True if the flag was contained, False otherwise.
        '''
        assert isinstance(flag, str), 'Invalid flag %s' % flag
        try: self.remove(flag)
        except KeyError: return False
        return True

# --------------------------------------------------------------------

def firstOf(coll):
    '''
    Provides the first element from the provided collection.
    
    @param coll: list|tuple|iterable
        The collection to provide the first item.
    '''
    if isinstance(coll, (list, tuple)): return coll[0]
    coll = iter(coll)
    return next(coll)

def firstCheck(iterator):
    '''
    Checks the first element from the provided iterator. It will return a tuple containing as the first value a boolean
    with False if the element is not the first element in the provided iterator and True if is the first one. On the last
    position of the tuple it will return the actual value provided by the iterator.
    
    @param iterator: Iterator(object)
        The iterator to wrap for the first element check.
    @return: Iterator(tuple(boolean, object))
        A tuple containing as the first value a boolean with False if the element is not the first element in the
        provided iterator and True if is the first one
    '''
    first = True
    for item in iterator:
        yield first, item
        first = False
            
def lastCheck(iterator):
    '''
    Checks the last element from the provided iterator. It will return a tuple containing as the first value a boolean
    with False if the element is not the last element in the provided iterator and True if is the last one. On the last
    position of the tuple it will return the actual value provided by the iterator.
    
    @param iterator: Iterator(object)
        The iterator to wrap for the last element check.
    @return: Iterator(tuple(boolean, object))
        A tuple containing as the first value a boolean with False if the element is not the last element in the
        provided iterator and True if is the last one
    '''
    if not isinstance(iterator, Iterator): iterator = iter(iterator)

    item, stop = next(iterator), False
    while True:
        try:
            itemNext = next(iterator)
            yield False, item
            item = itemNext
        except StopIteration:
            if stop: raise
            stop = True
            yield True, item
            
def firstLastCheck(iterator):
    '''
    Checks the first and last element from the provided iterator. It will return a tuple containing as the 
    first value a boolean with False if the element is not the first in the iterator and True if is the first one, on the
    second position a boolean with False if the element is not the last element in the provided iterator and True if is
    the last one. On the last position of the tuple it will return the actual value provided by the iterator.
    
    @param iterator: Iterator(object)
        The iterator to wrap for the last element check.
    @return: Iterator(tuple(boolean, boolean, object))
        A tuple containing as the first value  a boolean with False if the element is not the first in the iterator
        and True if is the first one, on the second position a boolean with False if the element is not the last element
        in the provided iterator and True if is the last one. On the last position of the tuple it will return the
        actual value provided by the iterator.
    '''
    if not isinstance(iterator, Iterator): iterator = iter(iterator)

    item, stop, isFirst = next(iterator), False, True
    while True:
        try:
            itemNext = next(iterator)
            yield isFirst, False, item
            item = itemNext
        except StopIteration:
            if stop: raise
            stop = True
            yield isFirst, True, item
        isFirst = False

# --------------------------------------------------------------------

def modifyFirst(value, upper=False):
    '''
    Modifies the first letter to an upper or lower letter.
    
    @param value: string
        The value to convert.
    @param upper: boolean
        If true converts the letter to upper, otherwise to a lower one.
    @return: string
        The converted value.
    '''
    assert isinstance(value, str), 'Invalid value %s' % value
    assert value, 'At least one letter is required'
    if upper: return '%s%s' % (value[0].upper(), value[1:])
    return '%s%s' % (value[0].lower(), value[1:])

def toUnderscore(value):
    '''
    Converts from a camel case string to an underscore one.
    
    @param value: string
        The value to convert.
    @return: string
        The converted value.
    '''
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', re.sub('(.)([A-Z][a-z]+)', r'\1_\2', value)).lower()

class TextTable:
    '''
    Provides the text table rendering.
    '''
    
    def __init__(self, *headers):
        '''
        Construct the text table.
        
        @param headers: arguments[string]
            The headers of the table.
        '''
        assert headers, 'At least one header is required'
        
        self._headers = headers
        self._sizes = []
        self._rows = []
        self._processing = deque()
        
        for header in headers:
            assert isinstance(header, str), 'Invalid header %s' % header
            self._sizes.append(len(header) + 2)
            
    def add(self, *row):
        '''
        Adds a new row to the table.
        
        @param row: arguments[string]
            The row items.
        '''
        assert row, 'At least one row item is required'
        
        isFirst = True
        self._processing.append(row)
        while self._processing:
            row = self._processing.popleft()
            if len(row) == 1:
                item = row[0]
                assert isinstance(item, str), 'Invalid item %s' % item
                
                if isFirst:
                    lines = item.split('\n')
                    if len(lines) > 1:
                        self._processing.extend((line,) for line in lines)
                        continue
                    
                litem, total = self._len(item), sum(self._sizes)
                if litem > total:
                    gain = int(litem / len(self._sizes))
                    for k in range(len(self._sizes)): self._sizes[k] += gain
                    self._sizes[-1] += litem - (len(self._sizes) * gain)
                
            else:
                if isFirst:
                    extended = [list(row)]
                    for k, item in enumerate(row):
                        assert isinstance(item, str), 'Invalid item %s' % item 
                        lines = item.split('\n')
                        if len(lines) > 1:
                            for j, line in enumerate(lines):
                                while len(extended) <= j: extended.append([''] * len(self._sizes))
                                extended[j][k] = line
                    if len(extended) > 1:
                        self._processing.extend(extended)
                        continue

                for k, item in enumerate(row):
                    assert isinstance(item, str), 'Invalid item %s' % item
                
                    self._sizes[k] = max(self._sizes[k], self._len(item))
                
            self._rows.append((bool(self._processing), row))
            isFirst = False
            
    def render(self, out):
        '''
        Renders the table into the provided output.
        '''
        self._line(out)
        out.write('\n')
        self._row(out, (('{: ^%s}' % (self._sizes[k] - 1)).format(header) for k, header in enumerate(self._headers)))
        out.write('\n')
        self._line(out, line='=')
        out.write('\n')
        for hasNext, row in self._rows:
            if len(row) == 1: self._item(out, row[0])
            else: self._row(out, row)
            out.write('\n')
            if not hasNext:
                self._line(out)
                out.write('\n')
        
    # ----------------------------------------------------------------
    
    def _len(self, item):
        '''
        Provides the item length.
        '''
        return max(len(line) for line in item.split('\n')) + 2
    
    def _line(self, out, line='-', intersetion='+'):
        '''
        Renders a line.
        '''
        for size in self._sizes:
            out.write(intersetion)
            out.write(line * size)
        out.write(intersetion)
        
    def _row(self, out, row, vertical='|', ident=' '):
        '''
        Renders the row values.
        '''
        out.write(vertical)
        for k, item in enumerate(row):
            out.write(ident)
            out.write(item)
            out.write(ident * (self._sizes[k] - len(item) - 1))
            out.write(vertical)
    
    def _item(self, out, item, vertical='|', ident=' '):
        '''
        Renders the row values.
        '''
        out.write(vertical)
        out.write(ident)
        out.write(item)
        out.write(ident * (sum(self._sizes) - len(item) - 2 + len(self._sizes)))
        out.write(vertical)
