'''
Created on Jan 19, 2012

@package: ally api
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the decorators used for APIs in a much easier to use form.
'''

from .operator.descriptor import processWithProperties, processAsQuery, \
    processAsService
from .operator.extract import Prototype, extractCriterias, extractProperties, \
    extractInputOuput, processGenericCall, inheritedTypesFrom
from .operator.type import TypeCall, TypeModel, TypeProperty, TypeCriteria, \
    TypeQuery, TypeService, TypeExtension, TypeOption
from .type import typeFor
from ally.api.operator.type import TypePropertyContainer
from ally.api.type import List, Input
from ally.support.util_sys import locationStack
from inspect import isclass, isfunction
from re import match
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# Defines the naming rules for the API configured classes.
RULE_MODEL = ('^[A-Z]{1,}[A-Za-z0-9]*$',
              'The model name needs to start with an upper case and be camel letter format, got "%s"')

RULE_MODEL_PROPERTY = ('^[A-Z]{1,}[A-Za-z0-9]*$',
                       'The model property name needs to start with an upper case and be camel letter format, got "%s"')

RULE_CRITERIA_PROPERTY = ('^[a-z]{1,}[\w]*$',
                          'The criteria property name needs to start with a lower case, got "%s"')

RULE_QUERY_CRITERIA = ('^[a-z]{1,}[\w]*$',
                       'The query criteria name needs to start with a lower case, got "%s"')

RULE_EXTENSION_PROPERTY = ('^[a-z]{1,}[\w]*$',
                           'The extension property name needs to start with a lower case, got "%s"')

RULE_OPTION_PROPERTY = ('^[a-z]{1,}[\w]*$',
                        'The option property name needs to start with a lower case, got "%s"')

RULE_CALL_ARGUMENTS = ('^[a-z]{1,}[\w]*$',
                        'The call argument name needs to start with a lower case, got "%s", at:%s')
# The available method actions.
GET = 1 << 1
INSERT = 1 << 2
UPDATE = 1 << 3
DELETE = 1 << 4


# The function name to method mapping.
NAME_TO_METHOD = {
                  '(^get[\w]*$)|(^find[\w]*$)|(^is[\w]*$)':GET,
                  '(^insert[\w]*$)|(^persist[\w]*$)':INSERT,
                  '(^update[\w]*$)|(^merge[\w]*$)|(^add[\w]*$)|(^assign[\w]*$)':UPDATE,
                  '(^delete[\w]*$)|(^remove[\w]*$)':DELETE
                  }

# --------------------------------------------------------------------

def model(*args, id=None, name=None, **hints):
    '''
    Used for decorating classes that are API models.
    
    ex:
        @model
        class Entity:
    
            Name = String
        
        @model(name=Entity)
        class Entity2(Entity):
    
            NewProperty = Integer

    @param id: string|None
        The name of the property to be considered the model id, if the id is not specified then the model will
        be limited in usage.
    @param name: string|None
        Provide a name under which the model will be known. If not provided the name of the model is the class name.
    @param hints: key word arguments
        Provides hints for the model.
        @keyword replace: class
            The model class to be replaced by this model class, should only be used whenever you need to prototype a
            model in order to be fully defined latter.
    '''
    def decorator(clazz):
        assert isclass(clazz), 'Invalid class %s' % clazz
        nonlocal id, name, hints
        
        if name is not None:
            if isclass(name):
                typ = typeFor(name)
                assert isinstance(typ, TypeModel), 'Invalid class %s to extract name, is not a model class' % name
                name = typ.name
            assert isinstance(name, str), 'Invalid model name %s' % name
        else:
            name = clazz.__name__
        if not match(RULE_MODEL[0], name): raise Exception(RULE_MODEL[1] % name)
        
        model = clazz._ally_type = TypeModel(clazz, name)
    
        for typ in inheritedTypesFrom(clazz, TypeModel):
            assert isinstance(typ, TypeModel)
            if id is None and isinstance(typ.propertyId, TypeProperty):
                assert isinstance(typ.propertyId, TypeProperty)
                id = typ.propertyId.name
                log.info('Inherited id \'%s\'from %s, at:%s', id, typ, locationStack(clazz))
            model.hints.update(hitem for hitem in typ.hints.items() if hitem[0] not in model.hints)
        model.hints.update(hints)
        
        toSelf = []
        for name, typ in extractProperties(clazz, TypeModel).items():
            if not match(RULE_MODEL_PROPERTY[0], name): raise Exception(RULE_MODEL_PROPERTY[1] % name)
            if isinstance(typ, TypeModel):
                assert isinstance(typ, TypeModel)
                if typ == model:
                    toSelf.append(name)
                    continue
                
                if not typ.propertyId:
                    raise Exception('Cannot use %s for property \'%s\', because the model has no id defined' % (typ, name))
                model.properties[name] = TypePropertyContainer(model, name, typ.propertyId, typ)
            elif not typ.isPrimitive:
                raise Exception('Invalid type %s for property \'%s\', only primitives or models allowed' % (typ, name))
            else: model.properties[name] = TypeProperty(model, name, typ)
    
        if id is not None:
            assert isinstance(id, str), 'Invalid property id %s' % id
            assert id in model.properties, 'Invalid property id %s is not in model properties' % id
    
            model.propertyId = model.properties[id]
            if isinstance(model.propertyId.type, List):
                raise Exception('The id cannot be a List type, got %s' % model.propertyId.type)
            if isinstance(model.propertyId, TypePropertyContainer):
                raise Exception('The id cannot be a model reference, got %s' % model.propertyId.container)
            
        for name in toSelf:
            if not model.propertyId:
                raise Exception('Cannot use self %s for property \'%s\', because there is no id defined' % (model, name))
            model.properties[name] = TypePropertyContainer(model, name, model.propertyId, model)
                
        return processWithProperties(clazz, model)
    if args: return decorator(*args)
    return decorator

def criteria(*args, main=None):
    '''
    Used for decorating classes that are API criteria's.
    
    ex:
        @criteria(main='order')
        class OrderBy:
    
            order = bool
            
    @param main: string|tuple(string)|list[string]|None
        Provide the name of the property/properties that is to be considered the main property for the criteria. 
        The main property/properties is the property/properties used whenever the criteria is used without a property. 
        If the main property is None then it will be inherited if is the case from super criteria's otherwise is left
        unset.
    '''
    def decorator(clazz):
        assert isclass(clazz), 'Invalid class %s' % clazz
        nonlocal main
    
        criteria = clazz._ally_type = TypeCriteria(clazz)
        for name, typ in extractProperties(clazz, TypeCriteria).items():
            if not match(RULE_CRITERIA_PROPERTY[0], name): raise Exception(RULE_CRITERIA_PROPERTY[1] % name)
            if not typ.isPrimitive:
                raise Exception('Invalid type %s for property \'%s\', only primitives allowed' % (typ, name))
            criteria.properties[name] = TypeProperty(criteria, name, typ, isContainable=False)
    
        if main is not None:
            if isinstance(main, str): main = (main,)
        else:
            for typ in inheritedTypesFrom(clazz, TypeCriteria):
                assert isinstance(typ, TypeCriteria)
                if typ.main:
                    main = tuple(typ.main)
                    break
            else: main = ()
        
        for name in main:
            assert name in criteria.properties, 'Invalid main property name \'%s\'' % name
            criteria.main[name] = criteria.properties[name]
    
        return processWithProperties(clazz, criteria)
    if args: return decorator(*args)
    return decorator

def query(owner):
    '''
    Used for decorating classes that are API queries.
    
    @param owner: TypeModel container
        The model that is the target of this query.
    
    ex:
        @query(Theme)
        class ThemeQuery:
            
            name = OrderBy
    '''
    target = typeFor(owner)
    assert isinstance(target, TypeModel), 'Invalid owner %s, has no type model' % owner

    def decorator(clazz):
        assert isclass(clazz), 'Invalid class %s' % clazz

        query = clazz._ally_type = TypeQuery(clazz, target)
        for name, criteria in extractCriterias(clazz).items():
            if not match(RULE_QUERY_CRITERIA[0], name): raise Exception(RULE_QUERY_CRITERIA[1] % name)
            query.properties[name] = TypeProperty(query, name, typeFor(criteria), isContainable=False)

        return processAsQuery(clazz, query)
    return decorator

def call(*args, method=None, **hints):
    '''
    Used for decorating service methods that are used as APIs.
    
    ex:
        Using the annotations:
            @call
            def updateX(self, x:int)->None:
                doc string
                <no method body required>
                
        Using specified types:
            @call(Entity, Entity.x, String, webName='unassigned')
            def findBy(self, x, name):
                doc string
                <no method body required>
                
            @call(Entity, Entity, OtherEntity, method=UPDATE)
            def assign(self, entity, toEntity):
                doc string
                <no method body required>

    @param method: integer
        One of the config module constants GET, INSERT, UPDATE, DELETE.
    @param hints: key arguments
        Provides hints for the call, the hints are used for assembly.
            @keyword exposed: boolean
                Indicates that the call is exposed for external interactions, usually all defined methods in a service
                that are not decorated with call are considered unexposed calls.
    '''
    function = None
    if not args: types = None
    elif not isfunction(args[0]): types = args
    else:
        types = None
        assert len(args) == 1, \
        'Expected only one argument that is the decorator function, got %s arguments' % len(args)
        function = args[0]

    def decorator(function):
        assert isfunction(function), 'Invalid function %s' % function
        nonlocal method
        name = function.__name__
        if method is None:
            for regex, m in NAME_TO_METHOD.items():
                if match(regex, name):
                    method = m
                    break
            else: raise Exception('Cannot deduce method for function name \'%s\'' % name)

        inputs, output = extractInputOuput(function, types, modelToId=method in (GET, DELETE))
        for inp in inputs:
            assert isinstance(inp, Input), 'Invalid input %s' % inp
            if not match(RULE_CALL_ARGUMENTS[0], inp.name):
                raise Exception(RULE_CALL_ARGUMENTS[1] % (inp.name, locationStack(function)))
        
        function.__isabstractmethod__ = True  # Flag that notifies the ABCMeta that is is an actual abstract method.
        function._ally_call = name, method, inputs, output, hints
        return function

    if function is not None: return decorator(function)
    return decorator

def prototype(*args, method=None, **hints):
    '''
    Used for decorating prototype class methods that are used as APIs. The usage is the same
    as for @see: call, with the exception that as annotations also callable functions are allowed
    that are going to be invoked with the replacements when the prototype is used in a service.
    '''
    function = None
    if not args: types = None
    elif not isfunction(args[0]): types = args
    else:
        types = None
        assert len(args) == 1, \
        'Expected only one argument that is the decorator function, got %s arguments' % len(args)
        function = args[0]

    def decorator(function):
        assert isfunction(function), 'Invalid function %s' % function
        nonlocal method
        name = function.__name__
        if method is None:
            for regex, m in NAME_TO_METHOD.items():
                if match(regex, name):
                    method = m
                    break
            else: raise Exception('Cannot deduce method for function name \'%s\'' % name)
        
        def prototype(prototype):
            assert isinstance(prototype, Prototype), 'Invalid replaces %s' % prototype
            inputs, output = extractInputOuput(function, types, modelToId=method in (GET, DELETE), prototype=prototype)
            for inp in inputs:
                assert isinstance(inp, Input), 'Invalid input %s' % inp
                if not match(RULE_CALL_ARGUMENTS[0], inp.name):
                    raise Exception(RULE_CALL_ARGUMENTS[1] % (inp.name, locationStack(function)))
            return name, method, inputs, output, hints
        
        function.__isabstractmethod__ = True  # Flag that notifies the ABCMeta that is is an actual abstract method.
        function._ally_call_prototype = prototype
        return function
        
    if function is not None: return decorator(function)
    return decorator

def service(*generic):
    '''
    Used for decorating classes that are API services.
    
    ex:
        @service
        class IEntityService:
    
            @call(Number, Entity.x)
            def multipy(self, x):
            
        
        @service((Entity, Issue))
        class IInheritingService(IEntityService):
    
            @call(Number, Issue.x)
            def multipy(self, x):
            
    @param generic: arguments((replaced:class|prototype:string, replacer:class))
        The classes that will be generically replaced or prototype names that will be replaced.
    '''
    generics, replaces = {}, {}
    if generic:
        if len(generic) == 1 and isclass(generic[0]): clazz = generic[0]
        else:
            for gen in generic:
                assert isinstance(gen, (tuple, list)), 'Invalid generic entry %s' % gen
                assert len(gen) == 2, 'Invalid generic entry %s has to many entries %s, expected 2' % (gen, len(gen))
                replaced, replacer = gen
                assert isclass(replacer) and isinstance(typeFor(replacer), (TypeModel, TypeQuery)), \
                'Invalid replacer class %s in generic entry %s' % (replacer, gen)
                if isinstance(replaced, str):
                    replaces[replaced] = replacer
                    continue
                assert isclass(replaced) and isinstance(typeFor(replaced), (TypeModel, TypeQuery)), \
                'Invalid replaced class %s in generic entry %s' % (replaced, gen)
                assert issubclass(replacer, replaced), \
                'Invalid replacer class %s does not extend the replaced class %s' % (replacer, replaced)
                generics[replaced] = replacer
            clazz = None
    else: clazz = None

    def decorator(clazz):
        assert isclass(clazz), 'Invalid class %s' % clazz
    
        prototype = None
        service = clazz._ally_type = TypeService(clazz)
        for name, function in clazz.__dict__.items():
            if not isfunction(function): continue
            try: service.calls[name] = TypeCall(service, clazz, *function._ally_call)
            except AttributeError: raise Exception('No call for method at:%s' % locationStack(function))
            del function._ally_call

        classes = list(clazz.__bases__)
        while classes:
            base = classes.pop()
            inherited = typeFor(base)
            if inherited is None:
                if base == object: continue
                for name, function in base.__dict__.items():
                    if not isfunction(function) or name in service.calls: continue
                    try: callPrototype = function._ally_call_prototype
                    except AttributeError: pass
                    else:
                        if prototype is None: prototype = Prototype(replaces, clazz)
                        service.calls[name] = TypeCall(service, base, *callPrototype(prototype))
                        continue
                    try: service.calls[name] = TypeCall(service, base, *function._ally_call)
                    except AttributeError: raise Exception('No call for inherited method at:%s' % locationStack(function))
                classes.extend(base.__bases__)
                
            elif not isinstance(inherited, TypeService): raise Exception('Unexpected inherited type %s' % inherited)
            
            else:
                assert isinstance(inherited, TypeService)
                for name, cal in inherited.calls.items():
                    assert isinstance(cal, TypeCall)
                    if name not in service.calls:
                        service.calls[name] = TypeCall(service, cal.definer, *processGenericCall(cal, generics))
    
        return processAsService(clazz, service)
    if clazz: return decorator(clazz)
    return decorator

def extension(*args):
    '''
    Used for decorating classes that are API extensions. The extension is used as a model but only with primitive
    properties that is rendered in the response in different manners. Also the extension is not specified in the API
    and can be returned by the implementation in a dynamic manner.
    
    ex:
        @extension
        class CollectionWithTotal(Iterable):
    
            total = int
            
            def __init__(self, iter):
                self.iter = iter
                
            def __iter__(self): return self.iter()
    '''
    def decorator(clazz):
        assert isclass(clazz), 'Invalid class %s' % clazz
    
        extension = clazz._ally_type = TypeExtension(clazz)
    
        for name, typ in extractProperties(clazz, TypeExtension).items():
            if not match(RULE_EXTENSION_PROPERTY[0], name): raise Exception(RULE_EXTENSION_PROPERTY[1] % name)
            if not typ.isPrimitive:
                raise Exception('Invalid type %s for property \'%s\', only primitives are allowed' % (typ, name))
            extension.properties[name] = TypeProperty(extension, name, typ, isContainable=False)
    
        return processWithProperties(clazz, extension)
    if args: return decorator(*args)
    return decorator

def option(*args):
    '''
    Used for decorating classes that are API options. The option is used to group multiple key argument declarations that
    tend to repeat in services.
    
    ex:
        @option
        class Slice:
    
            offset = int
            limit = int
    '''
    def decorator(clazz):
        assert isclass(clazz), 'Invalid class %s' % clazz
        
        option = clazz._ally_type = TypeOption(clazz)
    
        for name, typ in extractProperties(clazz, TypeOption).items():
            if not match(RULE_OPTION_PROPERTY[0], name): raise Exception(RULE_OPTION_PROPERTY[1] % name)
            if not typ.isPrimitive:
                raise Exception('Invalid type %s for property \'%s\', only primitives are allowed' % (typ, name))
            option.properties[name] = TypeProperty(option, name, typ, isContainable=False)
    
        return processWithProperties(clazz, option)
    if args: return decorator(*args)
    return decorator

# --------------------------------------------------------------------

def hints(*targets, **hints):
    '''
    Places hints on the provided target type.
    
    @param targets: arguments[container TypeModel or TypeCall]
        The target call or model to place the hints.
    @param hints: key arguments
        The hints to place on the targets.
    '''
    assert targets, 'At least a target is required'
    assert hints, 'At least a hint is required'
    
    for target in targets:
        typ = typeFor(target)
        if isinstance(typ, TypeCall):
            assert isinstance(typ, TypeCall)
            typ.hints.update(hints)
        else:
            assert isinstance(typ, TypeModel), 'Invalid target %s' % target
            typ.hints.update(hints)
