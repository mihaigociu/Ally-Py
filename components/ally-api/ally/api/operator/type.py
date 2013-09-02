'''
Created on Mar 13, 2012

@package: ally api
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the operator types.
'''

from ..type import Type, typeFor, TypeClass
from ally.api.type import Input
from collections import OrderedDict
from inspect import ismethod, isclass

# --------------------------------------------------------------------

class TypeProperty(Type):
    '''
    The property type definition.
    '''

    def __init__(self, parent, name, type, isContainable=True):
        '''
        Constructs the property type for the provided property name and parent container type.
        @see: Type.__init__
        
        @param parent: TypeContainer
            The container of the property type.
        @param name: string
            The property name that this type represents.
        @param type: Type|None
            The type to associate with the property type, if not provided then the container property type is used.
        @param isContainable: boolean
            If true than this type is containable in types like List and Iter.
        '''
        assert isinstance(parent, TypeContainer), 'Invalid container type %s' % parent
        assert isinstance(name, str), 'Invalid property name %s' % name
        assert isinstance(type, Type), 'Invalid type %s' % type
        super().__init__(False, isContainable)

        self.parent = parent
        self.name = name
        self.type = type

    def isOf(self, type):
        '''
        @see: Type.isOf
        '''
        return self == type or self.type.isOf(type)

    def isValid(self, obj):
        '''
        @see: Type.isValid
        '''
        return self.type.isValid(obj)
    
    def rebase(self, parent):
        '''
        Create a new type property based on this property but having as a parent the provided parent container.
        
        @param parent: TypeContainer
            The container of the property type.
        @return: TypeProperty
            The new rebased type property.
        '''
        assert isinstance(parent, TypeContainer), 'Invalid container type %s' % parent
        return TypeProperty(parent, self.name, self.type, isContainable=self.isContainable)

    def __hash__(self):
        '''
        @see: Type.__hash__
        '''
        return hash((self.parent, self.name))

    def __eq__(self, other):
        '''
        @see: Type.__eq__
        '''
        if other.__class__ == self.__class__:
            return self.parent == other.parent and self.name == other.name
        return False

    def __str__(self):
        '''
        @see: Type.__str__
        '''
        return '%s.%s' % (self.parent, self.name)

class TypePropertyContainer(TypeProperty):
    '''
    The property type definition that is targeting another container but the actual represented value is not of container type.
    '''

    def __init__(self, parent, name, type, container, isContainable=True):
        '''
        Constructs the property type that is targeting a container.
        @see: TypeProperty.__init__
        
        @param container: TypeContainer
            The container represented by the property type.
        '''
        assert isinstance(container, TypeContainer), 'Invalid container type %s' % container
        super().__init__(parent, name, type, isContainable)

        self.container = container
        
    def rebase(self, parent):
        '''
        @see: TypeProperty.rebase
        '''
        assert isinstance(parent, TypeContainer), 'Invalid container type %s' % parent
        return TypePropertyContainer(parent, self.name, self.type, self.container, isContainable=self.isContainable)
    
    def __hash__(self):
        '''
        @see: Type.__hash__
        '''
        return hash((self.parent, self.name))
    
    def __eq__(self, other):
        '''
        @see: Type.__eq__
        '''
        if other.__class__ == self.__class__:
            return self.parent == other.parent and self.name == other.name and self.container == other.container
        return False

class TypeContainer(TypeClass):
    '''
    Provides the type for the properties container.
    '''

    def __init__(self, clazz, isContainable=True):
        '''
        Constructs the container type.
        @see: TypeClass.__init__
        
        @param clazz: class
            The class associated with the container.
        @param isContainable: boolean
            If true than this type is containable in types like List and Iter.
        @ivar properties: dictionary{string, TypeProperty}
            A dictionary containing as a key the property name and as a value the property type that
            are associated with the container.
        '''
        super().__init__(clazz, False, isContainable)
        
        self.properties = {}

# --------------------------------------------------------------------

class TypeModel(TypeContainer):
    '''
    Provides the type for the model.
    '''

    def __init__(self, clazz, name):
        '''
        Constructs the model type.
        @see: TypeContainer.__init__
        
        @param name: string
            The name of the model.
        @ivar propertyId: TypeProperty|None
            The type model property id of the model if one is available.
        @ivar hints: dictionary{string, object}
            The hints associated with the model.
        '''
        assert isinstance(name, str) and name, 'Invalid model name %s' % name
        super().__init__(clazz)
        
        self.name = name
        self.propertyId = None
        self.hints = {}

class TypeAlias(TypeModel):
    '''
    Provides the alias type for the model.
    '''
    
    def __init__(self, model, name):
        '''
        Constructs the model type.
        @see: TypeModel.__init__
        
        @param model: TypeModel
            The aliased model.
        @param name: string
            The name of the alias.
        '''
        assert isinstance(model, TypeModel), 'Invalid model %s' % model
        super().__init__(model.clazz, name)
        
        self.model = model
        
        if model.propertyId:
            assert isinstance(model.propertyId, TypeProperty), 'Invalid property id %s' % model.propertyId
            self.propertyId = model.propertyId.rebase(self)
        for name, prop in model.properties.items():
            assert isinstance(prop, TypeProperty), 'Invalid property %s' % prop
            self.properties[name] = prop.rebase(self)
        self.hints.update(model.hints)

# --------------------------------------------------------------------

class TypeCriteria(TypeContainer):
    '''
    Provides the type for the criteria.
    '''

    def __init__(self, clazz):
        '''
        Constructs the criteria type.
        @see: TypeContainer.__init__
        
        @ivar main: dictionary{string, TypeProperty}
            The main properties for the criteria, the main is used whenever a value is set directly on the 
            criteria. The main properties properties and have compatible types.
        '''
        super().__init__(clazz, isContainable=False)
        self.main = {}

class TypeQuery(TypeContainer):
    '''
    Provides the type for the query.
    '''

    def __init__(self, clazz, target):
        '''
        Constructs the query type.
        @see: TypeContainer.__init__
        
        @param target: TypeModel
            The type model that is this type query is owned by.
        '''
        assert isinstance(target, TypeModel), 'Invalid target model %s' % target
        super().__init__(clazz, isContainable=False)

        self.target = target

# --------------------------------------------------------------------

class TypeExtension(TypeContainer):
    '''
    Provides the type for the extensions.
    '''

    def __init__(self, clazz):
        '''
        Constructs the extension type.
        @see: TypeContainer.__init__
        '''
        super().__init__(clazz, isContainable=False)
        
# --------------------------------------------------------------------

class TypeOption(TypeContainer):
    '''
    Provides the type for the option.
    '''

    def __init__(self, clazz):
        '''
        Constructs the option type.
        @see: TypeContainer.__init__
        '''
        super().__init__(clazz, isContainable=False)
        
# --------------------------------------------------------------------

class TypeInput(Type):
    '''
    Provides the type for the service call input.
    '''

    def __init__(self, parent, input):
        '''
        Constructs the service call input type.
        @see: Type.__init__
        
        @param parent: TypeCall
            The parent call type.
        @param input: Input
            The input for input type.
        '''
        assert isinstance(parent, TypeCall), 'Invalid parent %s' % parent
        assert isinstance(input, Input), 'Invalid input %s' % input
        super().__init__(False, False)

        self.parent = parent
        self.input = input

    def isOf(self, type):
        '''
        @see: Type.isOf
        '''
        return self == typeFor(type)

    def isValid(self, obj):
        '''
        @see: Type.isValid
        '''
        return self.input.type.isValid(obj)

    def __hash__(self):
        '''
        @see: Type.__hash__
        '''
        return hash((self.parent, self.input))

    def __eq__(self, other):
        '''
        @see: Type.__eq__
        '''
        if isinstance(other, self.__class__): return self.parent == other.parent and self.input == other.input
        return False

    def __str__(self):
        '''
        @see: Type.__str__
        '''
        return '%s.%s' % (self.parent, self.input.name)
    
class TypeCall(Type):
    '''
    Provides the type for the service call. This class will basically contain all the types that are involved in
    input and output from the call.
    '''

    def __init__(self, parent, definer, name, method, inputs, output, hints=None):
        '''
        Constructs the service call type.
        @see: Type.__init__
        
        @param parent: TypeService
            The parent service type.
        @param definer: class
            The class where the call is actually defined.
        @param name: string
            The name of the function represented by the call.
        @param method: integer
            The method of the call, can be one of GET, INSERT, UPDATE or DELETE constants in this module.
        @param inputs: list[Input]|tuple(Input)
            A list containing all the Input's of the call.
        @param output: Type
            The output type for the service call.
        @param hints: dictionary{string: object}|None
            The hints associated with the call.
        '''
        assert isinstance(parent, TypeService), 'Invalid parent %s' % parent
        assert isclass(definer), 'Invalid definer class %s' % definer
        assert isinstance(name, str) and name.strip(), 'Provide a valid name'
        assert isinstance(method, int), 'Invalid method %s' % method
        assert isinstance(inputs, (list, tuple)), 'Invalid inputs %s, needs to be a list' % inputs
        assert isinstance(output, Type), 'Invalid output type %s' % output
        super().__init__(False, False)

        self.parent = parent
        self.definer = definer
        self.name = name
        self.method = method
        self.output = output
        
        self.inputs = OrderedDict()
        for inp in inputs:
            assert isinstance(inp, Input), 'Not an input %s' % input
            self.inputs[inp.name] = TypeInput(self, inp)
            
        if hints is None: self.hints = {}
        else: 
            assert isinstance(hints, dict), 'Invalid hints %s' % hints
            if __debug__:
                for hintn in hints: assert isinstance(hintn, str), 'Invalid hint name %s' % hintn
            self.hints = dict(hints)

    def isOf(self, type):
        '''
        @see: Type.isOf
        '''
        return self == typeFor(type)

    def isValid(self, obj):
        '''
        @see: Type.isValid
        '''
        if not ismethod(obj): return False
        return isinstance(obj.__self__, self.parent.clazz)

    def __hash__(self):
        '''
        @see: Type.__hash__
        '''
        return hash((self.parent, self.call.name))

    def __eq__(self, other):
        '''
        @see: Type.__eq__
        '''
        if isinstance(other, self.__class__): return self.parent == other.parent and self.call.name == other.call.name
        return False

    def __str__(self):
        '''
        @see: Type.__str__
        '''
        return '%s.%s(%s)->%s' % (self.parent, self.name,
                                  ', '.join(str(typ.input) for typ in self.inputs.values()), self.output)
    
class TypeService(TypeClass):
    '''
    Provides the type for the service.
    '''

    def __init__(self, clazz):
        '''
        Constructs the service type for the provided service.
        @see: TypeClass.__init__
        
        @ivar calls: dictionary{string: TypeCall}
            The type calls of the service.
        '''
        super().__init__(clazz, False, False)
        
        self.calls = {}

# --------------------------------------------------------------------

def typePropFor(obj, prop):
    '''
    Provides the property type of the container object.
    
    @param obj: object|class
        The class or container object to extract the type.
    @param prop: string
        The property name to extract the type for.
    @return: TypeProperty|None
        The obtained property type or None if there is not type.
    '''
    assert isinstance(prop, str), 'Invalid property %s' % prop
    if isclass(obj): clazz = obj
    else: clazz = obj.__class__
    container = typeFor(clazz)
    if isinstance(container, TypeContainer):
        assert isinstance(container, TypeContainer)
        return container.properties.get(prop)
