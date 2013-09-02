'''
Created on Mar 16, 2012

@package: ally api
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the configuration functions.
'''

from ..type import Non, Type, Input, Iter, typeFor
from .type import TypeContainer, TypeCriteria, TypeQuery, TypeModel, \
    TypeProperty, TypeOption, TypePropertyContainer, TypeCall, TypeInput
from ally.support.util_sys import locationStack
from inspect import isfunction, getfullargspec, isclass
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

def inheritedTypesFrom(clazz, forType=Type):
    '''
    Extracts the inherited types for class.
    
    @param clazz: class
        The class to extract the inherited types from.
    @param forType: class
        The type to be extracted, the type needs to be a subclass of Type.
    @return: list[Type]
        A list of the extracted types.
    '''
    assert isclass(clazz), 'Invalid class %s' % clazz
    assert issubclass(forType, Type), 'Invalid for type class %s' % forType

    types = []
    for base in clazz.__bases__:
        type = typeFor(base)
        if type and isinstance(type, forType): types.append(type)

    return types

def extractPropertiesInhertied(clazz, forType=TypeContainer):
    '''
    Extracts the inherited properties definitions from the class.
    
    @param clazz: class
        The class to extract the inherited properties from.
    @param forType: class
        The inherited type to be extracted, the type needs to be a subclass of TypeContainer.
    @return: dictionary{string, Type}
        A inherited properties definitions dictionary containing as a key the property name and as a value the property type.
    '''
    assert isclass(clazz), 'Invalid class %s' % clazz
    assert issubclass(forType, TypeContainer), 'Invalid for type class %s' % forType
    
    definitions = {}
    for container in inheritedTypesFrom(clazz, forType):
        assert isinstance(container, TypeContainer), 'Invalid container %s' % container
        for name, prop in container.properties.items():
            assert isinstance(prop, TypeProperty), 'Invalid property %s' % prop
            if name not in definitions:
                if isinstance(prop, TypePropertyContainer):
                    assert isinstance(prop, TypePropertyContainer)
                    definitions[name] = prop.container
                else: definitions[name] = prop.type
    return definitions

def extractProperties(clazz, forType=TypeContainer):
    '''
    Extracts the properties definitions from the class, including the inherited definitions.
    It will automatically remove the used definitions from the class.
    
    @param clazz: class
        The class to extract the properties from.
    @param forType: class
        The inherited type to be extracted, the type needs to be a subclass of TypeContainer.
    @return: dictionary{string, Type}
        A properties definitions dictionary containing as a key the property name and as a value the property type.
    '''
    assert isclass(clazz), 'Invalid class %s' % clazz
    
    definitions = extractPropertiesInhertied(clazz, forType)
    for name, value in list(clazz.__dict__.items()):
        if name.startswith('_') or isfunction(value): continue
        typ = typeFor(value)
        if typ is None:
            log.warn('Invalid property \'%s\' definition \'%s\' at:%s', name, value, locationStack(clazz))
        else:
            definitions[name] = typ
            delattr(clazz, name)
    
    return definitions

def extractCriterias(clazz):
    '''
    Extract the criteria's that are found in the provided class, including the inherited definitions.
    It will automatically remove the used definitions from the class.
    
    @param clazz: class
        The class to extract the criterias from.
    @return: dictionary{string, TypeCriteria}
        A dictionary containing as the key the criteria name and as a value the criteria type.
    '''
    assert isclass(clazz), 'Invalid class %s' % clazz
    
    definitions = extractPropertiesInhertied(clazz, TypeQuery)
    for name, value in list(clazz.__dict__.items()):
        if name.startswith('_') or isfunction(value): continue
        criteria = typeFor(value)
        if isinstance(criteria, TypeCriteria): 
            assert isinstance(criteria, TypeCriteria)
            definitions[name] = criteria.clazz
            delattr(clazz, name)
        else:
            log.warn('Invalid criteria \'%s\' definition \'%s\' at:%s', name, value, locationStack(clazz))
            
    for name, typ in extractPropertiesInhertied(clazz, TypeQuery).items():
        if not isinstance(typ, TypeCriteria): continue
        assert isinstance(typ, TypeCriteria)
        if name not in definitions: definitions[name] = typ.clazz

    return definitions

def extractInputOuput(function, types=None, modelToId=False, prototype=None):
    '''
    Extracts the input and output for a call based on the provided function.
    
    @param function: function
        The function to extract the call for
    @param types: list[Type or Type container]|None
        The list of types to associate with the function, if they are not provided then the function annotations
        are considered.
    @param modelToId: boolean
        Flag indicating that the extract should convert all inputs that are model types to their actually
        corresponding property type, used in order not to constantly provide the id property of the model when in fact
        we can deduce that the API annotation actually refers to the id and not the model.
    @param prototype: object
        The prototype object used in calling the annotation callables, only if this prototype is provided the callables
        will be invoked.
    @return: tuple(list[Input], Type)
        A tuple containing on the first position the list of inputs for the call, and second the output type of the call.
    '''
    assert isfunction(function), 'Invalid function %s' % function
    assert isinstance(modelToId, bool), 'Invalid model to id flag %s' % modelToId
    fnArgs = getfullargspec(function)
    args, keywords, defaults = fnArgs.args, fnArgs.varkw, fnArgs.defaults
    annotations = fnArgs.annotations

    assert fnArgs.varargs is None, 'No variable arguments are allowed'
    assert 'self' == args[0], 'The call needs to be tagged in a class definition'

    if types:
        assert isinstance(types, (list, tuple)), 'Invalid types list %s' % types
        assert len(args) == len(types), 'The functions parameters are not equal with the provided input types'
        assert not annotations, 'The types for the input arguments cannot be declared as annotations %s and call '\
        'arguments %s' % (annotations, types)
        annotations['return'] = types[0]
        annotations.update({args[k]:types[k] for k in range(1, len(args))})
    
    args = args[1:]  # We remove the self argument

    mandatory = len(args)
    if defaults: mandatory -= len(defaults)
    output, inputs = extractType(Non if 'return' not in annotations else annotations['return'], prototype), []
    for k, arg in enumerate(args):
        if arg not in annotations: raise Exception('There is no type for \'%s\'' % arg)
        typ = extractType(annotations[arg], prototype)
        assert isinstance(typ, Type), 'Could not obtain a valid type \'%s\' for \'%s\' with %s, at:%s' \
                                      % (typ, arg, annotations[arg], locationStack(function))
        if modelToId and isinstance(typ, TypeModel):
            assert isinstance(typ, TypeModel)
            assert typ.propertyId, 'The model %s has not id to use' % typ
            typ = typ.propertyId
        if k < mandatory: inputs.append(Input(arg, typ))
        else: inputs.append(Input(arg, typ, True, defaults[k - mandatory]))
    
    if keywords:
        if keywords not in annotations: raise Exception('There is option type for keywords \'%s\'' % keywords)
        option = extractType(annotations[keywords], prototype)
        assert isinstance(option, TypeOption), 'Invalid option \'%s\' with %s' % (keywords, annotations[keywords])
        obj = option.clazz()
        for name, prop in option.properties.items():
            assert isinstance(prop, TypeProperty), 'Invalid property type %s' % prop
            if name in args:
                raise Exception('There is already the argument name \'%s\' cannot process option %s' % (name, prop))
            inputs.append(Input(name, prop, True, getattr(obj, name)))

    return inputs, output

def extractType(annotation, prototype):
    '''
    Extracts the annotation type.
    
    @param annotation: object
        The annotation object to extract the type for.
    @param prototype: object
        The prototype object used in calling the annotation callables, only if this prototype is provided the callables
        will be invoked.
    @return: Type|None
        The annotation type or None if not found.
    '''
    if annotation is not None:
        typ = typeFor(annotation)
        if typ is None and prototype is not None and callable(annotation):
            return typeFor(annotation(prototype))
        return typ

# --------------------------------------------------------------------

def processGenericCall(call, generic):
    '''
    If either the output or input of the call is based on the provided super model or query then it will create 
    new call that will have the super model or query replaced with the new model or query in the types of the call.
    
    @param call: TypeCall
        The call to be analyzed.
    @param generic: dictionary{class, class}
        The dictionary containing as a key the class to be generically replaced and as a value the class to replace with.
    @return: Call
        If the provided call is not depended on the super model it will be returned as it is, if not a new call
        will be created with all the dependencies from super model replaced with the new model.
    '''
    assert isinstance(call, TypeCall), 'Invalid call %s' % call
    assert isinstance(generic, dict), 'Invalid generic %s' % generic
    output = processGenericType(call.output, generic)
    if not output: output = call.output
    inputs = []
    for itype in call.inputs.values():
        assert isinstance(itype, TypeInput), 'Invalid input type %s' % itype
        assert isinstance(itype.input, Input), 'Invalid input %s' % itype.input
        genericType = processGenericType(itype.input.type, generic)
        if genericType: inputs.append(Input(itype.input.name, genericType, itype.input.hasDefault, itype.input.default))
        else: inputs.append(itype.input)
    return call.name, call.method, inputs, output, call.hints

def processGenericType(forType, generic):
    '''
    Processes the type if is the case into a new type that is extended from the original but having the new
    model or query as reference instead of the super model or query.
    @see: processCallGeneric
    
    @param forType: Type
        The type to process.
    @param generic: dictionary{class, class}
        The dictionary containing as a key the class to be generically replaced and as a value the class to replace with.
    @return: Type|None
        If the provided type was containing references to the super model than it will return a new type
        with the super model references changes to the new model, otherwise returns None.
    '''
    assert isinstance(forType, Type), 'Invalid type %s' % type
    assert isinstance(generic, dict), 'Invalid generic %s' % generic

    if isinstance(forType, TypeProperty) and isinstance(forType.parent, TypeModel):
        assert isinstance(forType, TypeProperty)
        assert isinstance(forType.parent, TypeModel)
        modelClass = generic.get(forType.parent.clazz)
        if modelClass is not None:
            newModel = typeFor(modelClass)
            assert isinstance(newModel, TypeModel), 'Invalid generic model class %s, has no model type' % modelClass
            assert forType.name in newModel.properties, 'The %s cannot be generic for %s' % (newModel, forType.parent)
            return newModel.properties[forType.name]
    elif isinstance(forType, TypeModel):
        assert isinstance(forType, TypeModel)
        modelClass = generic.get(forType.clazz)
        if modelClass is not None:
            newModel = typeFor(modelClass)
            assert isinstance(newModel, TypeModel), 'Invalid generic model class %s, has no model type' % modelClass
            return newModel
    elif isinstance(forType, TypeQuery):
        assert isinstance(forType, TypeQuery)
        queryClass = generic.get(forType.clazz)
        if queryClass is not None:
            newQuery = typeFor(queryClass)
            assert isinstance(newQuery, TypeQuery), 'Invalid generic query class %s, has no query type' % queryClass
            return newQuery
    elif isinstance(forType, Iter):
        assert isinstance(forType, Iter)
        itemType = processGenericType(forType.itemType, generic)
        if itemType: return forType.__class__(itemType)

# --------------------------------------------------------------------

class Prototype:
    '''
    The prototype object passed on to the prototype calls.
    '''
    
    def __new__(cls, replaces, clazz):
        assert isinstance(replaces, dict), 'Invalid replaces %s' % replaces
        assert isclass(clazz), 'Invalid class %s' % clazz
        self = object.__new__(cls)
        self.__dict__.update(replaces)
        self._clazz = clazz
        return self
    
    def __getattr__(self, name):
        if not name.startswith('_'):
            raise Exception('A generic replace is required for \'%s\' at:%s' % (name, locationStack(self._clazz)))
