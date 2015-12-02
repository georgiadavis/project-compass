#!/usr/bin/env python

import os
import cgi
import urllib
import webapp2
import jinja2
from google.appengine.api import images
from google.appengine.api import users
from google.appengine.ext import ndb

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(
    loader = jinja2.FileSystemLoader(template_dir),
    extensions = ['jinja2.ext.autoescape'],
    autoescape = True)

DEFAULT_MAP_NAME = 'default'

def map_key(map_name=DEFAULT_MAP_NAME):
    """Constructs Datastore key for PhotoMap entity."""
    return ndb.Key('PhotoMap', map_name)

class Author(ndb.Model):
    """Sub model for representing an author."""
    identity = ndb.StringProperty(indexed = True)
    name = ndb.StringProperty(indexed = False)
    email = ndb.StringProperty(indexed = False)

class Photo(ndb.Model):
    """Models a PhotoMap entry with an author, image, location, description, and date"""
    author = ndb.StructuredProperty(Author)
    image = ndb.BlobProperty()
    location = ndb.StringProperty()
    description = ndb.StringProperty()
    date = ndb.DateTimeProperty(auto_now_add = True)

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, template_values):
        t = jinja_env.get_template(template)
        return t.render(template_values)

    def render(self, template, template_values):
        self.write(self.render_str(template, template_values))

    def get_user_info(self):
        my_id = '109483363884786481827' # user ID for anthony.fumagalli@knowlabs.com
        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            user_name = user.nickname()
            user_id = user.user_id()
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login with Google'
            user_name = 'Anonymous'
            user_id = None
        if user_name == "anthony.fumagalli@knowlabs.com":
        #if user_id == my_id:
            admin = True
        else:
            admin = False
        return url, url_linktext, user_name, admin

class Image(Handler):
    def get(self):
        photo_key = ndb.Key(urlsafe=self.request.get('img_id'))
        photo = photo_key.get()
        if photo.image:
            self.response.headers['Content-Type'] = 'image/png'
            self.response.out.write(photo.image)
        else:
            self.response.out.write('No image')

class MainPage(Handler):
    def get(self):
        map_name = self.request.get('map_name', DEFAULT_MAP_NAME)
        url, url_linktext, user_name, admin = self.get_user_info()
        photos_query = Photo.query(
            ancestor = map_key(map_name)).order(-Photo.date)
        photos = photos_query.fetch()

        template_values = {
            'map_name': map_name,
            'user_name': user_name,
            'url': url,
            'url_linktext': url_linktext,
            'admin': admin
        }
        self.render('index.html', template_values)

class PhotoMap(Handler):
    def post(self):
        map_name = self.request.get('map_name', DEFAULT_MAP_NAME)
        photo = Photo(parent = map_key(map_name))
        user = users.get_current_user()
        if user:
            photo.author = Author(
                identity = user.user_id(),
                name = user.nickname(),
                email = user.email())
        photo.image = self.request.get('img')
        photo.location = self.request.get('location')
        photo.description = self.request.get('description')
        photo.put()
        self.redirect('/?' + urllib.urlencode(
            {'map_name': map_name}))

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/img', Image),
    ('/post', PhotoMap)
], debug=True)
