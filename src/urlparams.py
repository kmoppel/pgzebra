from dbobject_cache import DBObjectsCache


class UrlParams(object):

    def __init__(self, object_cache, features, *args):
        """ :type object_cache : dbobject_cache.DBObjectsCache """
        self.object_cache = object_cache
        self.features = features
        self.db_uniq = None
        self.dbname = None
        self.table = None
        self.column_names = []
        self.filters = []     # [(col_short, op, value),]  op: eq/=, gt/>
        self.aggregations = []     # [(operator, column),]  op: count, sum, min, max
        self.joinitems = {}
        self.graphtype = None
        self.graphkey = None
        self.graphbucket = None
        self.limit = features.get('default_limit', 20)
        self.order_by_direction = features.get('default_order_by', 'DESC')
        self.order_by_columns = []
        self.output_format = features.get('default_format', 'html')

        # return args
        args_count = len(args)
        if args_count < 2:
            raise Exception('Invalid arguments!')   # TODO add more checks, lose 500. separate exception subclass?

        self.db_uniq, self.table = object_cache.get_dbuniq_and_table_full_name(args[0], args[1])
        if not (self.db_uniq and self.table):
            raise Exception('DB or Table not found!')   # TODO suggest similar tables if only table
        self.column_names = [x['column_name'] for x in object_cache.cache[self.db_uniq][self.table]]
        self.dbname = self.db_uniq.split(':')[2]

        current_arg_counter = 2
        while current_arg_counter < args_count:
            current_arg = args[current_arg_counter]
            next_arg = None
            next_2nd = None
            has_next = args_count > current_arg_counter + 1
            if has_next: next_arg = args[current_arg_counter + 1]
            has_2nd = args_count > current_arg_counter + 2
            if has_2nd: next_2nd = args[current_arg_counter + 2]

            # output_format
            if current_arg == 'f' or current_arg == 'format':
                if has_next and next_arg in ['c', 'csv', 'j', 'json', 'h', 'html', 'g', 'graph', 'png']:
                    if next_arg[0] == 'c':
                        self.output_format = 'csv'
                    elif next_arg[0] == 'j':
                        self.output_format = 'json'
                    elif next_arg[0] == 'g' and has_2nd and next_2nd in ['l', 'line', 'p', 'pie']:
                        self.output_format = 'graph'
                        self.graphtype = 'pie' if next_2nd[0] == 'p' else 'line'
                        current_arg_counter += 3
                        continue
                    elif next_arg == 'png' and has_2nd and next_2nd in ['l', 'line', 'p', 'pie']:
                        self.output_format = 'png'
                        self.graphtype = 'pie' if next_2nd[0] == 'p' else 'line'
                        current_arg_counter += 3
                        continue
                    else:
                        self.output_format = 'html'
                    current_arg_counter += 2
                    continue

            # limit
            if current_arg == 'l' or current_arg == 'limit':
                if has_next and str(next_arg).isdigit():
                    self.limit = next_arg
                    current_arg_counter += 2
                    continue

            # order by
            #   : o[rderby]
            #   : o/[asc|desc]
            #   : o/[c|m]
            #   : o/[c|m][asc|desc]
            #   : o[rderby]/columnpattern[,pattern2]/[asc|desc]
            # TODO multicolumn, comma separated
            if current_arg == 'o' or current_arg == 'orderby':
                if has_2nd and next_2nd in ['a', 'asc', 'd', 'desc']:
                    if next_arg in ['c', 'created']:
                        self.order_by_columns = [self.object_cache.get_column_single(self.db_uniq, self.table, self.features['created_patterns'])]
                    elif next_arg in ['m', 'modified']:
                        self.order_by_columns = [self.object_cache.get_column_single(self.db_uniq, self.table, self.features['modified_patterns'])]
                    else:
                        self.order_by_columns = self.object_cache.get_column_multi(self.db_uniq, self.table, next_arg)
                    if not self.order_by_columns:
                        raise Exception('Order By column {} not found! Known columns: {}'.format(next_arg, self.column_names))
                    if next_2nd in ['a', 'asc']:
                        self.order_by_direction = 'ASC' if next_2nd[0] == 'a' else 'DESC'
                    current_arg_counter += 3
                    continue
                elif has_next and next_arg in ['a', 'asc', 'd', 'desc']:
                    self.order_by_columns = [self.column_names[0]]  # 1st col by default TODO use PK
                    self.order_by_direction = 'ASC' if next_arg[0] == 'a' else 'DESC'
                    current_arg_counter += 2
                    continue
                elif has_next and next_arg in ['c', 'created','m', 'modified'] and (not has_2nd or next_2nd not in ['a','asc','d','desc']):
                        if next_arg[0] == 'c':
                            self.order_by_columns = [self.object_cache.get_column_single(self.db_uniq, self.table, self.features['created_patterns'])]
                        else:
                            self.order_by_columns = [self.object_cache.get_column_single(self.db_uniq, self.table, self.features['modified_patterns'])]
                        current_arg_counter += 2
                        continue
                elif has_next and object_cache.get_column_multi(self.db_uniq, self.table, next_arg):    # /o/col1,col2
                    columns = object_cache.get_column_multi(self.db_uniq, self.table, next_arg)
                    if columns:
                        self.order_by_columns = columns
                        current_arg_counter += 2
                        continue
                else:
                    self.order_by_columns = [self.column_names[0]]  # 1st col by default TODO use PK
                    current_arg_counter += 1
                    continue

            # filters
            # /column/>/val
            # TODO add special keywords like today?

            if has_next and has_2nd:
                if next_arg.upper() in ['<', '<=', '>', '>=', '=', 'EQ', 'LT', 'LTE', 'GT', 'GTE',
                                        'IS', 'IS NOT', 'ISNOT', 'IN']:
                    next_arg = next_arg.upper()
                    column = self.object_cache.get_column_single(self.db_uniq, self.table, current_arg)
                    if not column:
                        raise Exception('Column {} not found!'.format(current_arg))
                    if next_arg in ['IS', 'IS NOT', 'ISNOT']:
                        if next_2nd.upper() != 'NULL':
                            raise Exception('is/isnot requires NULL as next parameter!')
                        next_2nd = next_2nd.upper()
                    print next_arg
                    next_arg = next_arg.replace('ISNOT', 'IS NOT')
                    next_arg = next_arg.replace('EQ', '=')
                    next_arg = next_arg.replace('LTE', '<=')
                    next_arg = next_arg.replace('LT', '<')
                    next_arg = next_arg.replace('GTE', '>=')
                    next_arg = next_arg.replace('GT', '>')
                    print next_arg
                    if next_arg == 'IN':
                        self.filters.append((column, next_arg, '(' + next_2nd + ')'))
                    else:
                        self.filters.append((column, next_arg, next_2nd))
                    current_arg_counter += 3
                    continue

            # simple aggregations
            # count, sum, min, max
            if current_arg == 'agg' and has_2nd and next_arg in ['count', 'sum', 'min', 'max']:
                agg_col = self.object_cache.get_column_single(self.db_uniq, self.table, next_2nd)
                self.aggregations.append((next_arg, agg_col))
                current_arg_counter += 3
                continue

            # simple graphs
            # /gkey/col
            if current_arg in ['gk', 'gkey'] and has_next:
                self.graphkey = self.object_cache.get_column_single(self.db_uniq, self.table, next_arg)
                current_arg_counter += 2
                continue
            # /gbucket/1h   [1month,1d,1h,1min]
            if current_arg in ['gb', 'gbucket'] and has_next and next_arg in ['month', 'day', 'hour', 'min', 'minute']:
                self.graphbucket = next_arg
                current_arg_counter += 2
                continue


            print 'WARNING: did not make use of ', current_arg
            current_arg_counter += 1

    def do_pre_sql_check(self): # TODO sql injection analyze. use psycopg2 mogrify?
        if self.graphtype == 'line' and not self.graphbucket:
            raise Exception('gbucket/gb parameter missing! [ allowed values: month, week, day, hour, minute]')

    def to_sql(self):
        self.do_pre_sql_check()
        sql = 'SELECT '
        if self.aggregations:
            i = 0
            for agg_op, column in self.aggregations:
                sql += ('' if i == 0 else ', ') + agg_op + '(' + column + ')'
                i += 1
        elif self.output_format in ['graph', 'png']:
            if self.graphtype == 'line':
                sql += "date_trunc('{}', {}), count(*)".format(self.graphbucket, self.graphkey)
            else:
                sql += "{}, count(*)".format(self.graphkey)
        else:
            sql += ', '.join(self.column_names)

        sql += ' FROM ' + self.table
        if self.filters:
            sql += ' WHERE '
            i = 0
            for fcol, fop, fval in self.filters:
                col_full_name = self.object_cache.get_column_single(self.db_uniq, self.table, fcol)
                if not col_full_name:
                    raise Exception('Column {} not found! Known columns: {}'.format(fcol, self.column_names))
                sql += '{}{} {} {}'.format((' AND ' if i > 0 else ''), col_full_name, fop.upper(), fval)
                i += 1

        if self.graphkey:
            if self.graphtype == 'line':
                sql += ' GROUP BY 1 ORDER BY 1'
            elif self.graphtype == 'pie':
                sql += ' GROUP BY 1 ORDER BY 2 DESC'    # LIMIT {}'.format(self.limit)
        elif not self.aggregations:
            if self.order_by_columns:
                if isinstance(self.order_by_columns, list):
                    sql += ' ORDER BY '
                    order_bys = []
                    for col in self.order_by_columns:
                        order_bys.append('{} {}'.format(col, self.order_by_direction.upper()))
                    sql += ', '.join(order_bys)
                else:
                    sql += ' ORDER BY {} {}'.format(self.order_by_columns, self.order_by_direction.upper())
            sql += ' LIMIT {}'.format(self.limit)
        return sql

    def get_normalized_url(self):
        url = '/' + '/'.join([self.dbname, self.table, 'output', self.output_format])
        if self.output_format in ['graph', 'png']:
            url += '/' + self.graphtype
            if self.graphkey:
                url += '/{}/{}'.format('graphkey', self.graphkey)
            if self.graphbucket:
                url += '/{}/{}'.format('gbucket', self.graphbucket)
        for column, op, value in self.filters:
            url += '/{}/{}/{}'.format(column, op, value)
        if self.output_format not in ['graph', 'png']:
            if self.order_by_columns:
                url += ('/{}/{}/{}'.format('orderby', ','.join(self.order_by_columns), self.order_by_direction)).lower()
            elif self.order_by_direction:
                url += ('/{}/{}'.format('orderby', self.order_by_direction)).lower()
        url += '/{}/{}'.format('limit', self.limit)
        return url

    def __str__(self):
        return 'UrlParams: db = {}, table = {}, columns = {}, filters = {}, order_by_columns = {},' \
            ' output_format = {}, graphtype = {}, gkey = {}, gbucket = {}, limit = {}'.format(self.db_uniq, self.table,
                                                                                 self.column_names, self.filters,
                                                                                 self.order_by_columns, self.output_format,
                                                                                 self.graphtype, self.graphkey,
                                                                                 self.graphbucket, self.limit)


if __name__ == '__main__':
    db_objects_cache = DBObjectsCache()
    db_objects_cache.add_table_to_cache('local', 5432, 'postgres',
                                        'public.table1',
                                        DBObjectsCache.formulate_table(['col1', 'col2', 't_created']))
    print db_objects_cache

    features = {
        'default_order_by': 'DESC',
        'default_limit': '20',
        'created_patterns': 'created,timestamp,time',
        'modified_patterns': 'modified,updated,timestamp',
    }
    # up = UrlParams(db_objects_cache, features, 'pos', 'ta*1', 'l', '100', 'o', 'd')
    # up = UrlParams(db_objects_cache, features, 'pos', 'ta*1', 'o', 'm', 'f', 'h', 'col1', '<=', '1')
    # up = UrlParams(db_objects_cache, features, 'pos', 'ta*1', 'col1', '<=', '100', 'agg', 'count', 'c1', 'agg', 'max', 'c1')
    # up = UrlParams(db_objects_cache, features, 'pos', 'ta*1', 'f', 'g', 'l', 'gkey', 'created', 'gbucket', 'hour')
    up = UrlParams(db_objects_cache, features, 'pos', 'ta*1', 'f', 'g', 'pie', 'gkey', 'l1')
    print up
    print up.get_normalized_url()
    print up.to_sql()
