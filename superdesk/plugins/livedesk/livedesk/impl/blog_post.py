'''
Created on May 4, 2012

@package: livedesk
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor


Contains the SQL alchemy meta for livedesk blog posts API.
'''

from ..api.blog_post import IBlogPostService, QBlogPostUnpublished, \
    QBlogPostPublished
from ..meta.blog_post import BlogPostMapped, BlogPostEntry
from ally.container import wire
from ally.container.ioc import injected
from ally.exception import InputError, Ref
from ally.internationalization import _
from ally.support.sqlalchemy.functions import current_timestamp
from ally.support.sqlalchemy.session import SessionSupport
from ally.support.sqlalchemy.util_service import buildQuery, buildLimits
from livedesk.api.blog_post import QBlogPost, QWithCId, BlogPost
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.util import aliased
from sqlalchemy.sql import functions as fn
from superdesk.collaborator.meta.collaborator import CollaboratorMapped
from superdesk.person.meta.person import PersonMapped
from superdesk.post.api.post import IPostService, Post, QPostUnpublished
from superdesk.post.meta.type import PostTypeMapped

# --------------------------------------------------------------------

UserPerson = aliased(PersonMapped)

@injected
class BlogPostServiceAlchemy(SessionSupport, IBlogPostService):
    '''
    Implementation for @see: IBlogPostService
    '''

    postService = IPostService; wire.entity('postService')

    def __init__(self):
        '''
        Construct the blog post service.
        '''
        assert isinstance(self.postService, IPostService), 'Invalid post service %s' % self.postService
        SessionSupport.__init__(self)

    def getById(self, blogId, postId):
        '''
        @see: IBlogPostService.getById
        '''
        sql = self.session().query(BlogPostMapped)
        sql = sql.filter(BlogPostMapped.Blog == blogId)
        sql = sql.filter(BlogPostMapped.Id == postId)

        try: return sql.one()
        except NoResultFound: raise InputError(Ref(_('No such blog post'), ref=BlogPostMapped.Id))

    def getPublished(self, blogId, typeId=None, creatorId=None, authorId=None, offset=None, limit=None, q=None):
        '''
        @see: IBlogPostService.getPublished
        '''
        assert q is None or isinstance(q, QBlogPostPublished), 'Invalid query %s' % q
        sql = self._buildQuery(blogId, typeId, creatorId, authorId, q)
        sql = sql.filter(BlogPostMapped.PublishedOn != None)

        sql = sql.order_by(BlogPostMapped.PublishedOn.desc())
        sql = sql.order_by(BlogPostMapped.Id.desc())
        sql = buildLimits(sql, offset, limit)
        return self._trimmDeleted(sql.all())

    def getPublishedCount(self, blogId, typeId=None, creatorId=None, authorId=None, q=None):
        '''
        @see: IBlogPostService.getPublishedCount
        '''
        assert q is None or isinstance(q, QBlogPostPublished), 'Invalid query %s' % q
        sql = self._buildQuery(blogId, typeId, creatorId, authorId, q)
        sql = sql.filter(BlogPostMapped.PublishedOn != None)

        return sql.count()

    def getUnpublished(self, blogId, typeId=None, creatorId=None, authorId=None, offset=None, limit=None, q=None):
        '''
        @see: IBlogPostService.getUnpublished
        '''
        assert q is None or isinstance(q, QBlogPostUnpublished), 'Invalid query %s' % q
        sql = self._buildQuery(blogId, typeId, creatorId, authorId, q)
        sql = sql.filter(BlogPostMapped.PublishedOn == None)

        sql = sql.order_by(BlogPostMapped.CreatedOn.desc())
        sql = sql.order_by(BlogPostMapped.Id.desc())
        sql = buildLimits(sql, offset, limit)
        return self._trimmDeleted(sql.all())

    def getOwned(self, blogId, creatorId, typeId=None, offset=None, limit=None, q=None):
        '''
        @see: IBlogPostService.getUnpublishedOwned
        '''
        assert q is None or isinstance(q, QBlogPost), 'Invalid query %s' % q
        sql = self._buildQuery(blogId, typeId, creatorId, None, q)
        if q and QBlogPost.isPublished in q:
            if q.isPublished.value: sql = sql.filter(BlogPostMapped.PublishedOn != None)
            else: sql = sql.filter(BlogPostMapped.PublishedOn == None)
        sql = sql.filter(BlogPostMapped.Author == None)

        sql = sql.order_by(BlogPostMapped.CreatedOn.desc())
        sql = sql.order_by(BlogPostMapped.Id.desc())
        sql = buildLimits(sql, offset, limit)
        return self._trimmDeleted(sql.all())

    def getAll(self, blogId, typeId=None, creatorId=None, authorId=None, offset=None, limit=None, q=None):
        '''
        @see: IBlogPostService.getAll
        '''
        assert q is None or isinstance(q, QBlogPost), 'Invalid query %s' % q
        sql = self._buildQuery(blogId, typeId, creatorId, authorId, q)

        sql = sql.order_by(BlogPostMapped.PublishedOn.desc())
        sql = sql.order_by(BlogPostMapped.Id.desc())
        sql = buildLimits(sql, offset, limit)
        return self._trimmDeleted(sql.all())
    
    def insert(self, blogId, post):
        '''
        @see: IBlogPostService.insert
        '''
        assert isinstance(post, Post), 'Invalid post %s' % post

        postEntry = BlogPostEntry(Blog=blogId, blogPostId=self.postService.insert(post))
        postEntry.CId = self._nextCId()
        self.session().add(postEntry)

        return postEntry.blogPostId

    def publish(self, blogId, postId):
        '''
        @see: IBlogPostService.publish
        '''
        post = self.getById(blogId, postId)
        assert isinstance(post, Post)

        if post.PublishedOn: raise InputError(Ref(_('Already published'), ref=Post.PublishedOn))

        post.PublishedOn = current_timestamp()
        self.postService.update(post)

        postEntry = BlogPostEntry(Blog=blogId, blogPostId=post.Id)
        postEntry.CId = self._nextCId()
        self.session().merge(postEntry)

        return postId

    def insertAndPublish(self, blogId, post):
        '''
        @see: IBlogPostService.insertAndPublish
        '''
        assert isinstance(post, Post), 'Invalid post %s' % post

        post.PublishedOn = current_timestamp()

        postEntry = BlogPostEntry(Blog=blogId, blogPostId=self.postService.insert(post))
        postEntry.CId = self._nextCId()
        self.session().add(postEntry)

        return postEntry.blogPostId

    def update(self, blogId, post):
        '''
        @see: IBlogPostService.update
        '''
        assert isinstance(post, Post), 'Invalid post %s' % post

        self.postService.update(post)

        postEntry = BlogPostEntry(Blog=blogId, blogPostId=post.Id)
        postEntry.CId = self._nextCId()
        self.session().merge(postEntry)

    def delete(self, id):
        '''
        @see: IBlogPostService.delete
        '''
        if self.postService.delete(id):
            postEntry = self.session().query(BlogPostEntry).get(id)
            if postEntry:
                assert isinstance(postEntry, BlogPostEntry)
                postEntry.CId = self._nextCId()
                self.session().flush((postEntry,))
            return True
        return False

    # ----------------------------------------------------------------

    def _buildQuery(self, blogId, typeId=None, creatorId=None, authorId=None, q=None):
        '''
        Builds the general query for posts.
        '''
        sql = self.session().query(BlogPostMapped)
        sql = sql.filter(BlogPostMapped.Blog == blogId)
        
        if typeId: sql = sql.join(PostTypeMapped).filter(PostTypeMapped.Key == typeId)
        if creatorId: sql = sql.filter(BlogPostMapped.Creator == creatorId)
        if authorId:
            sql = sql.filter((BlogPostMapped.Author == authorId) |
                             ((CollaboratorMapped.Id == authorId) &
                              (CollaboratorMapped.Person == BlogPostMapped.Creator)))
        addDeleted = False
        if q:
            sql = buildQuery(sql, q, BlogPostMapped)
            addDeleted = QPostUnpublished.deletedOn in q or QWithCId.cId in q
        if not addDeleted: sql = sql.filter(BlogPostMapped.DeletedOn == None)
        
        return sql

    def _trimmDeleted(self, posts):
        '''
        Trim the information from the deleted posts.
        '''
        for post in posts:
            assert isinstance(post, BlogPost)
            if BlogPost.DeletedOn in post and post.DeletedOn is not None:
                trimmed = BlogPost()
                trimmed.Id = post.Id
                trimmed.CId = post.CId
                trimmed.DeletedOn = post.DeletedOn
                yield trimmed
            else:
                yield post

    def _nextCId(self):
        '''
        Provides the next change Id.
        '''
        max = self.session().query(fn.max(BlogPostMapped.CId)).scalar()
        if max: return max + 1
        return 1
