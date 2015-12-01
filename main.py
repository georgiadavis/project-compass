#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import webapp2
import jinja2
from google.appengine.api import users

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(
    loader = jinja2.FileSystemLoader(template_dir),
    extensions = ['jinja2.ext.autoescape'],
    autoescape = True)

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, template_values):
        t = jinja_env.get_template(template)
        return t.render(template_values)

    def render(self, template, template_values):
        self.write(self.render_str(template, template_values))

    def get_user_info(self):
        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            user_name = user.nickname()
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login with Google'
            user_name = 'Anonymous'
        return url, url_linktext, user_name

class MainHandler(Handler):
    def get(self):
        url, url_linktext, user_name = self.get_user_info()
        if user_name == 'anthony.fumagalli@knowlabs.com':
            admin = True
        else:
            admin = False
        template_values = {
            'user_name': user_name,
            'url': url,
            'url_linktext': url_linktext,
            'admin': admin
        }
        self.render('index.html', template_values)

app = webapp2.WSGIApplication([
    ('/', MainHandler)
], debug=True)
