#!/usr/bin/env python

import os
import cgi
import json
import urllib
import urllib2
import webapp2
import jinja2
from xml.dom import minidom
from google.appengine.api import images
from google.appengine.api import users
from google.appengine.ext import ndb

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(
    loader = jinja2.FileSystemLoader(template_dir),
    extensions = ['jinja2.ext.autoescape'],
    autoescape = False)

DEFAULT_MAP_NAME = 'default'

def map_key(map_name=DEFAULT_MAP_NAME):
    """Constructs Datastore key for PhotoMap entity."""
    return ndb.Key('PhotoMap', map_name)

def get_coords(address):
    url = "https://maps.googleapis.com/maps/api/geocode/xml?address=%s" % address
    try:
        response = urllib2.urlopen(url)
        xmlgeocode = response.read()
    except urllib2.URLError:
        return
    if xmlgeocode:
        d = minidom.parseString(xmlgeocode)
        coords = d.getElementsByTagName("status")[0].childNodes[0].nodeValue
        if coords == "OK":
            lat = d.getElementsByTagName("lat")[0].childNodes[0].nodeValue
            lng = d.getElementsByTagName("lng")[0].childNodes[0].nodeValue
            return ndb.GeoPt(lat, lng)
        return
    return

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
    coords = ndb.GeoPtProperty()
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
        photos_list = list(photos)

        points = []
        html = []
        for photo in photos_list:
            if photo.coords:
                coords = [photo.coords.lat, photo.coords.lon]
                points.append(coords)
            img_html = "<img src='/img?img_id=%s'> <br>" % photo.key.urlsafe()
            loc_html = "<b> %s </b> <br>" % photo.location
            desc_html = "<p> %s </p>" % photo.description
            all_html = img_html + loc_html + desc_html
            html.append(str(all_html))

        template_values = {
            'map_name': map_name,
            'user_name': user_name,
            'url': url,
            'url_linktext': url_linktext,
            'admin': admin,
            'photos': photos_list,
            'points': points,
            'content': html
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
        image = self.request.get('img')
        image = images.resize(image, 100, 100)
        photo.image = image
        loc = self.request.get('location')
        photo.location = loc
        loc = loc.replace(" ", "+")
        photo.coords = get_coords(loc)
        photo.description = self.request.get('description')
        photo.put()
        self.redirect('/?' + urllib.urlencode(
            {'map_name': map_name}))

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/img', Image),
    ('/post', PhotoMap)
], debug=True)
