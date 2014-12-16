import cherrypy
from jinja2 import Environment, FileSystemLoader
import os

import datadb
from urlparams import UrlParams

env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))


class Frontend(object):

    def __init__(self, features):
        self.features = features

    @cherrypy.expose
    def default(self, *args):
        print 'args', args
        up = UrlParams(datadb.object_cache, self.features, *args)
        print 'up', up

        tmpl = env.get_template('index.html')
        return tmpl.render(message='Hello')

