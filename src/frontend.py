import cherrypy
from jinja2 import Environment, FileSystemLoader
import os
import json
import csv
import time
import pygal
from cherrypy.lib import file_generator
import StringIO
import random
import datetime

import datadb
from urlparams import UrlParams

env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))


class Frontend(object):

    def __init__(self, features):
        self.features = features

    @cherrypy.expose
    def normalizeurl(self, *args):
        if len(args) < 2:
            raise Exception('Needs a table already')
        print 'normalized_url args', args
        urlparams = UrlParams(datadb.object_cache, self.features, *args)
        print 'normalized_url', urlparams.get_normalized_url()
        return urlparams.get_normalized_url()

    @cherrypy.expose
    def default(self, *args):
        if len(args) == 0:  # show all dbs
            return self.list_all_dbs()
        elif len(args) == 1:  # show all tables for a db
            return self.list_all_tables(args[0])

        message = ''
        print 'args', args
        urlparams = UrlParams(datadb.object_cache, self.features, *args)
        print 'up', urlparams
        sql = urlparams.to_sql()
        print 'sql', sql

        data, column_names = datadb.execute_on_db_uniq(urlparams.db_uniq, sql)
        # print 'data', data
        column_info = datadb.get_column_info(urlparams.db_uniq, urlparams.table, column_names)  # TODO highlight PK in UI

        if urlparams.output_format == 'json':
            # stringify everything, not to get "is not JSON serializable"
            stringified = []
            for row in data:
                stringified.append([str(x) for x in row])   # TODO better to cast all cols to ::text in SQL?
            return json.dumps(stringified)
        elif urlparams.output_format in ['graph', 'png']:
            return self.plot_graph(data, urlparams)
        elif urlparams.output_format == 'csv':
            return self.to_csv(data, column_names, urlparams)
        else:
            tmpl = env.get_template('index.html')
            return tmpl.render(message=message, dbname=urlparams.dbname, table=urlparams.table, sql=sql, data=data, column_info=column_info)

    def list_all_dbs(self, output_format='html'):
        db_uniqs = datadb.object_cache.cache.keys()
        db_info = []
        for u in db_uniqs:
            splits = u.split(':')
            db_info.append({'hostname': splits[0], 'port': splits[1], 'dbname': splits[2]})
        db_info.sort(key=lambda x:x['dbname'])

        if output_format == 'json':
            return json.dumps(db_info)
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
        else:
            tmpl = env.get_template('tables.html')
            return tmpl.render(message='', dbname=db, hostname=hostname, port=port, tables=tables)

    def plot_graph(self, data, urlparams):
        line_data = []
        pie_data = []

        limit = int(urlparams.limit)
        if urlparams.graphtype == 'pie' and len(data) > limit and limit > 1:    # formulate an artificial 'other' group with values > 'limit'
            sum = 0L
            for k, v in data[limit-1:]:
                sum += v
            data[limit-1:] = [('Other', sum)]

        if urlparams.output_format == 'graph':
            if urlparams.graphtype == 'line':
                line_data = [(int(time.mktime(p[0].timetuple()) * 1000), p[1]) for p in data]
                line_data = json.dumps(line_data)
            elif urlparams.graphtype == 'pie':
                for d in data:
                    pie_data.append({'label': str(d[0]), 'data': [d[1]]})
                pie_data = json.dumps(pie_data)

            tmpl = env.get_template('graph.html')
            return tmpl.render(line_data=line_data, pie_data=pie_data, graph_type=urlparams.graphtype, table=urlparams.table)
        elif urlparams.output_format == 'png':
            chart = None
            if urlparams.graphtype == 'line':
                chart = pygal.Line()
                chart.title = 'Counts of {} over 1{} slots'.format(urlparams.graphkey, urlparams.graphbucket)
                labels = []
                for i, d in enumerate(data):
                    if i % 4 == 0 or i == (len(data)-1):
                        labels.append(str(d[0]))
                chart.x_labels = labels
                chart.add('Count', [v for t, v in data])
            elif urlparams.graphtype == 'pie':
                chart = pygal.Pie()
                chart.title = 'Distribution of {} values'.format(urlparams.graphkey)
                for key, count in data:
                    chart.add(str(key), count)

            random_file_path = '/tmp/pgzebra{}.png'.format(random.random())
            chart.render_to_png(random_file_path)
            output = StringIO.StringIO(open(random_file_path).read())   # should be possible to skip this step also?
            os.unlink(random_file_path)

            cherrypy.response.headers['Content-Type'] = 'image/png'
            return file_generator(output)

    def to_csv(self, data, column_names, urlparams):
        csvfile = StringIO.StringIO()
        writer = csv.writer(csvfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow(column_names)
        writer.writerows(data)
        cherrypy.response.headers['Content-Type'] = 'text/csv'
        cherrypy.response.headers['Content-Disposition'] = 'attachment; filename="{}_{}.csv"'.format(urlparams.table,
                                                                                                     datetime.datetime.now().strftime('%Y-%m-%d_%H%M'))
        return csvfile.getvalue()
