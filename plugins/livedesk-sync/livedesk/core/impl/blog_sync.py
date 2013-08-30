'''
Created on April 26, 2013

@package: livedesk
@copyright: 2013 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Mugur Rus

API implementation of liveblog sync.
'''

import socket
import json
import logging
import time
import codecs
from hashlib import sha1
from sched import scheduler
from threading import Thread
from urllib.request import urlopen, Request
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
from datetime import datetime
from livedesk.api.blog_sync import IBlogSyncService, QBlogSync, BlogSync
from superdesk.source.api.source import ISourceService, Source, QSource
from livedesk.api.blog_post import BlogPost, IBlogPostService
from sqlalchemy.sql.functions import current_timestamp
from superdesk.collaborator.api.collaborator import ICollaboratorService, Collaborator
from ally.container import wire, app
from ally.container.ioc import injected
from ally.container.support import setup
from superdesk.user.api.user import IUserService, QUser, User
from ally.exception import InputError
from urllib.error import HTTPError

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

@injected
@setup(name='blogSynchronizer')
class BlogSyncProcess:
    '''
    Blog sync process.
    '''

    blogSyncService = IBlogSyncService; wire.entity('blogSyncService')
    # blog sync service used to retrieve blogs set on auto publishing

    sourceService = ISourceService; wire.entity('sourceService')
    # source service used to retrieve source data

    blogPostService = IBlogPostService; wire.entity('blogPostService')
    # blog post service used to insert blog posts

    collaboratorService = ICollaboratorService; wire.entity('collaboratorService')
    # blog post service used to retrive collaborator

    userService = IUserService; wire.entity('userService')

    syncThreads = {}
    # dictionary of threads that perform synchronization

    sync_interval = 10; wire.config('sync_interval', doc='''
    The number of seconds to perform sync for blogs.''')
    date_time_format = '%Y-%m-%d %H:%M:%S'; wire.config('date_time_format', doc='''
    The date time format used in REST requests.''')
    published_posts_path = 'Post/Published'; wire.config('published_posts_path', doc='''
    The partial path used to construct the URL for published posts retrieval''')

    acceptType = 'text/json'
    # mime type accepted for response from remote blog
    encodingType = 'UTF-8'
    # character encoding type accepted for response from remove blog

    @app.deploy
    def startSyncThread(self):
        '''
        Starts the sync thread.
        '''
        schedule = scheduler(time.time, time.sleep)
        def syncBlogs():
            self.syncBlogs()
            schedule.enter(self.sync_interval, 1, syncBlogs, ())
        schedule.enter(self.sync_interval, 1, syncBlogs, ())
        scheduleRunner = Thread(name='blogs sync', target=schedule.run)
        scheduleRunner.daemon = True
        scheduleRunner.start()
        log.info('Started the blogs automatic synchronization.')

    def syncBlogs(self):
        '''
        Read all blog sync entries for which auto was set true and sync
        the corresponding blogs.
        '''
        for blogSync in self.blogSyncService.getAll(q=QBlogSync(auto=True)):
            assert isinstance(blogSync, BlogSync)
            syncThread = self.syncThreads.get(blogSync.Blog, None)
            if syncThread is not None and syncThread.is_alive(): continue
            self.syncThreads[blogSync.Blog] = Thread(name='blog %d sync' % blogSync.Blog,
                                                     target=self._syncBlog, args=(blogSync,))
            self.syncThreads[blogSync.Blog].daemon = True
            self.syncThreads[blogSync.Blog].start()
            log.info('Thread %s started for blog id %d', self.syncThreads[blogSync.Blog], blogSync.Blog)

    def _syncBlog(self, blogSync):
        '''
        Synchronize the blog for the given sync entry.

        @param blogSync: BlogSync
            The blog sync entry declaring the blog and source from which the blog
            has to be updated.
        '''
        assert isinstance(blogSync, BlogSync), 'Invalid blog sync %s' % blogSync
        source = self.sourceService.getById(blogSync.Source)
        assert isinstance(source, Source)
        (scheme, netloc, path, params, query, fragment) = urlparse(source.URI)

        q = parse_qsl(query, keep_blank_values=True)
        q.append(('asc', 'cId'))
        q.append(('cId.since', blogSync.CId if blogSync.CId is not None else 0))
        if blogSync.SyncStart is not None:
            q.append(('updatedOn.since', blogSync.SyncStart.strftime(self.date_time_format)))
        url = urlunparse((scheme, netloc, path + '/' + self.published_posts_path, params, urlencode(q), fragment))
        req = Request(url, headers={'Accept' : self.acceptType, 'Accept-Charset' : self.encodingType,
                                    'X-Filter' : '*,Author.Source.*,Author.User.*'})
        try: resp = urlopen(req)
        except (HTTPError, socket.error) as e:
            log.error('Read error on %s: %s' % (source.URI, e))
            return

        try: msg = json.load(codecs.getreader(self.encodingType)(resp))
        except ValueError as e:
            log.error('Invalid JSON data %s: %s' % (e, msg))
            return
        for post in msg['PostList']:
            try:
                if post['IsPublished'] != 'True': continue

                lPost = BlogPost()
                lPost.Type = post['Type']['Key']
                lPost.Creator = blogSync.Creator
                lPost.Author = self._getCollaboratorForAuthor(post['Author'], source)
                lPost.Meta = post['Meta'] if 'Meta' in post else None
                lPost.ContentPlain = post['ContentPlain'] if 'ContentPlain' in post else None
                lPost.Content = post['Content'] if 'Content' in post else None
                lPost.CreatedOn = lPost.PublishedOn = current_timestamp()

                # prepare the blog sync model to update the change identifier
                blogSync.CId = int(post['CId']) if blogSync.CId is None or int(post['CId']) > blogSync.CId else blogSync.CId
                blogSync.SyncStart = datetime.strptime(post['PublishedOn'], '%m/%d/%y %I:%M %p')

                # insert post from remote source
                self.blogPostService.insert(blogSync.Blog, lPost)
                # update blog sync entry
                self.blogSyncService.update(blogSync)
            except KeyError as e:
                log.error('Post from source %s is missing attribute %s' % (source.URI, e))
            except Exception as e:
                log.error('Error in source %s post: %s' % (source.URI, e))

    def _getCollaboratorForAuthor(self, author, source):
        '''
        Returns a collaborator identifier for the user/source defined in the post.
        If the post was not created by a user it returns a collaborator for the
        source identified in the post and the default user. The default user should
        be the sync entry creator. If the source from the post does not exist
        locally raises Exception.

        @param author: dict
            The author data in JSON decoded format
        @param source: Source
            The source from which the blog synchronization is done
        @return: integer
            The collaborator identifier.
        '''
        assert isinstance(source, Source)
        try:
            uJSON = author['User']
            u = User()
            u.Name = sha1((uJSON.get('Name', '') + source.URI).encode(self.encodingType)).hexdigest()
            u.FirstName, u.LastName = uJSON.get('FirstName', ''), uJSON.get('LastName', '')
            u.EMail, u.Password = uJSON.get('EMail', ''), '*'
            try: userId = self.userService.insert(u)
            except InputError:
                localUser = self.userService.getAll(q=QUser(name=u.Name))
                userId = localUser[0].Id
            c = Collaborator()
            c.User, c.Source = userId, source.Id
            try: return self.collaboratorService.insert(c)
            except InputError:
                collabs = self.collaboratorService.getAll(userId, source.Id)
                return collabs[0].Id
        except KeyError:
            q = QSource(name=author['Source']['Name'], isModifiable=False)
            sources = self.sourceService.getAll(q=q)
            if not sources: raise Exception('Invalid source %s' % q.name)
            collabs = self.collaboratorService.getAll(userId=None, sourceId=sources[0].Id)
            if collabs: return collabs[0].Id
            else:
                c = Collaborator()
                c.Source = sources[0].Id
                return self.collaboratorService.insert(c)
