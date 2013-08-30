'''
Created on Mar 14, 2013

@package: content article
@copyright: 2013 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Rus Mugurel

Contains SQL alchemy meta for article API.
'''

from ally.support.sqlalchemy.mapper import validate
from superdesk.meta.metadata_superdesk import Base
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.dialects.mysql.base import INTEGER
from sqlalchemy.types import TEXT, DateTime
from content.article.api.article import Article
from content.packager.meta.item import ItemMapped
from ally.container.binder_op import validateManaged
from sqlalchemy.ext.hybrid import hybrid_property
from superdesk.user.meta.user import UserMapped
from superdesk.person.meta.person import PersonMapped

# --------------------------------------------------------------------

@validate(exclude=['Item', 'PublishedOn'])
class ArticleMapped(Base, Article):
    '''
    Provides the mapping for Article.
    '''
    __tablename__ = 'article'
    __table_args__ = dict(mysql_engine='InnoDB', mysql_charset='utf8')

    Id = Column('id', INTEGER(unsigned=True), primary_key=True)
    Item = Column('fk_item_id', ForeignKey(ItemMapped.GUId, ondelete='RESTRICT'), nullable=False)
    Creator = Column('fk_creator_id', ForeignKey(UserMapped.Id, ondelete='RESTRICT'), nullable=False)
    Author = Column('fk_author_id', ForeignKey(PersonMapped.Id, ondelete='RESTRICT'), nullable=False)
    Content = Column('content', TEXT, nullable=False)
    PublishedOn = Column('published_on', DateTime)
    @hybrid_property
    def IsPublished(self):
        return self.PublishedOn is not None

    # Expression for hybrid ------------------------------------
    IsPublished.expression(lambda cls: cls.PublishedOn != None)

validateManaged(ArticleMapped.Item)
validateManaged(ArticleMapped.PublishedOn)
