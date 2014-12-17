#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cherrypy
import os
import yaml
from argparse import ArgumentParser

import datadb
import frontend


DEFAULT_CONF_FILE = 'pgzebra.yaml'


def main():
    parser = ArgumentParser(description='PgZebra Restful Table Interface')
    parser.add_argument('-c', '--config', help='Path to config file. (default: %s)'.format(DEFAULT_CONF_FILE), dest='config',
                        default=DEFAULT_CONF_FILE)
    parser.add_argument('-p', '--port', help='server port', dest='port', type=int)

    args = parser.parse_args()

    args.config = os.path.expanduser(args.config)

    settings = None
    if os.path.exists(args.config):
        print "trying to read config file from {}".format(args.config)
        with open(args.config, 'rb') as fd:
            settings = yaml.load(fd)

    if settings is None:
        print 'Config file missing - Yaml file could not be found'
        parser.print_help()
        return

    print 'instances found'
    print settings['instances'].keys()
    print 'features'
    print settings['features']

    datadb.initialize_db_object_cache(settings)

    current_dir = os.path.dirname(os.path.abspath(__file__))

    conf = {'global':
                {
                    'server.socket_host': '0.0.0.0',
                    'server.socket_port': args.port or settings.get('port', 8081)
                },
            '/':
                {
                    'tools.staticdir.root': current_dir
                },
            '/static':
                {
                    'tools.staticdir.dir': 'static',
                    'tools.staticdir.on': True
                },
            }

    root = frontend.Frontend(settings['features'])

    cherrypy.quickstart(root, config=conf)


if __name__ == '__main__':
    main()
