'''
Created on Aug 30, 2013

@package: support sqlalchemy
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides utility methods for SQL alchemy meta definitions.
'''

from ally.api.operator.type import TypeModel, TypeProperty
from ally.api.type import typeFor
from ally.support.util import modifyFirst, toUnderscore
from ally.support.util_sys import callerLocals
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.sql.expression import select

# --------------------------------------------------------------------

def relationshipModel(mappedId, *spec, converter=None):
    '''
    Creates a relationship with the model, this should only be used in case the mapped model database id is different from the
    actual model id.
    
    @param mappedId: InstrumentedAttribute
        The mapped model id to create the relation with.
    @param spec: arguments containing
        column: string
            The column name containing the foreign key relation, attention if target is provided then
            also column needs to be provided, if None provided it will create one automatically.
        target: string
            The SQL alchemy relationship target name, if None provided it will create one automatically.
    @param converter: object
        The converter used to convert from model id to database id.
    '''
    assert isinstance(mappedId, InstrumentedAttribute), 'Invalid mapped id %s' % mappedId
    register = callerLocals()
    assert '__module__' in register, 'This function should only be used inside meta class definitions'
    rtype = typeFor(mappedId.class_)
    assert isinstance(rtype, TypeModel), 'Invalid class %s' % mappedId.class_
    assert isinstance(rtype.propertyId, TypeProperty), 'No property id for %s' % rtype
    assert rtype.propertyId.name != mappedId.property.key, 'Same database id with the model id \'%s\' for %s' % mappedId.class_
    
    column = target = None
    if spec:
        column, *spec = spec
        assert isinstance(column, str), 'Invalid column %s' % column
        if spec:
            target, = spec
            assert isinstance(target, str) and target, 'Invalid target %s' % target
    
    if target is None:
        target = modifyFirst(rtype.name, False)
        if column is None:
            column = '%sId' % target
            register[column] = Column('fk_%s_id' % toUnderscore(target), ForeignKey(mappedId, ondelete='CASCADE'), nullable=False)
        register[target] = relationship(mappedId.class_, uselist=False, lazy='joined', viewonly=True)
    
    def fget(self):
        rel = getattr(self, target)
        if rel: return getattr(rel, rtype.propertyId.name)
    
    if converter is None: converter = lambda value: select([mappedId], getattr(mappedId.class_, rtype.propertyId.name) == value)
    
    def fset(self, value):
        setattr(self, column, converter(value))
    
    def expr(cls):
        return getattr(mappedId.class_, rtype.propertyId.name)
    
    return hybrid_property(fget, fset, expr=expr)
    
