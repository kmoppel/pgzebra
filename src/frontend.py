import cherrypy
from jinja2 import Environment, FileSystemLoader
import os
import json
import csv
import time

import datadb
from urlparams import UrlParams

env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))


class Frontend(object):

    def __init__(self, features):
        self.features = features

    @cherrypy.expose
    def default(self, *args):
        if len(args) == 0:  # show all dbs
            return self.list_all_dbs()
        elif len(args) == 1:  # show all tables for a db
            return self.list_all_tables(args[0])

        message = ''
        print 'args', args
        up = UrlParams(datadb.object_cache, self.features, *args)
        print 'up', up
        sql = up.to_sql()
        # print 'sql', sql
        data, column_names = datadb.execute_on_db_uniq(up.db_uniq, sql)
        # print 'data', data
        column_info = datadb.get_column_info(up.db_uniq, up.table, column_names)  # TODO highlight PK in UI

        if up.output_format == 'json':
            # stringify everything, not to get "is not JSON serializable"
            stringified = []
            for row in data:
                stringified.append([str(x) for x in row])   # TODO better to cast all cols to ::text in SQL?
            return json.dumps(stringified)
        elif up.output_format == 'graph':
            return self.plot_graph(data, up.graphtype)
        elif up.output_format == 'csv':
            return json.dumps(data)     # TODO
        else:
            tmpl = env.get_template('index.html')
            return tmpl.render(message=message, dbname=up.dbname, table=up.table, sql=sql, data=data, column_info=column_info)

    def list_all_dbs(self, output_format='html'):
        db_uniqs = datadb.object_cache.cache.keys()
        db_info = []
        for u in db_uniqs:
            splits = u.split(':')
            db_info.append({'hostname': splits[0], 'port': splits[1], 'dbname': splits[2]})
        db_info.sort(key=lambda x:x['dbname'])

        if output_format == 'json':
            return json.dumps(db_info)
        elif output_format == 'csv':
            return json.dumps(db_info)     # TODO
        else:
            tmpl = env.get_template('dbs.html')
            return tmpl.render(message='', db_info=db_info)

    def list_all_tables(self, dbname, output_format='html'):
        db_uniq, table = datadb.object_cache.get_dbuniq_and_table_full_name(dbname)
        hostname, port, db = tuple(db_uniq.split(':'))
        tables = datadb.object_cache.get_all_tables_for_dbuniq(db_uniq)
        tables.sort()
        # print 'tables', tables

        if output_format == 'json':
            return json.dumps(tables)
        elif output_format == 'csv':
            return json.dumps(tables)     # TODO
        else:
            tmpl = env.get_template('tables.html')
            return tmpl.render(message='', dbname=db, hostname=hostname, port=port, tables=tables)

    def plot_graph(self, data, graph_type):
        if graph_type == 'line':
            data = [(int(time.mktime(p[0].timetuple()) * 1000), p[1]) for p in data]
        data = json.dumps(data)

        # return str(data)
        tmpl = env.get_template('graph.html')  # maybe create the image file on server and just serve it? http://pygal.org/chart_types/#idline-charts
        return tmpl.render(data=data, graph_type=graph_type)