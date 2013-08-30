'''
Created on Aug 19, 2013

@package: gui action
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the SQL alchemy meta for gui actions.
'''

from ..api.action import Action
from .metadata_action import Base
from ally.support.sqlalchemy.mapper import validate
from sqlalchemy.schema import Column
from sqlalchemy.types import String

# --------------------------------------------------------------------

@validate
class ActionMapped(Base, Action):
    '''
    Provides the action mapping.
    '''
    __tablename__ = 'gui_action'
    __table_args__ = dict(mysql_engine='InnoDB')
    
    Path = Column('path', String(255), primary_key=True)
    Label = Column('label', String(255))
    Script = Column('script', String(255))
    NavBar = Column('navbar', String(255))