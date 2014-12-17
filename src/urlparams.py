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
        self.limit = features.get('default_limit', 20)
        self.order_by_direction = features.get('default_order_by', 'DESC')
        self.order_by_column = None
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
            current_arg = args[current_arg_counter].lower()
            next_arg = None
            next_2nd = None
            has_next = args_count > current_arg_counter + 1
            if has_next: next_arg = args[current_arg_counter + 1].lower()
            has_2nd = args_count > current_arg_counter + 2
            if has_2nd: next_2nd = args[current_arg_counter + 2].lower()

            # output_format
            if current_arg == 'f' or current_arg == 'format':
                if has_next and next_arg in ['c', 'csv', 'j', 'json', 'h', 'html']:
                    if next_arg[0] == 'c':
                        self.output_format = 'csv'
                    elif next_arg[0] == 'j':
                        self.output_format = 'json'
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
            #   : o[rderby]/columnpattern/[asc|desc]
            # TODO multicolumn, comma separated
            if current_arg == 'o' or current_arg == 'orderby':
                if has_next and next_arg in ['a', 'asc', 'd', 'desc']:
                        self.order_by_column = self.column_names[0]  # 1st col by default TODO use PK
                        if next_arg[0] == 'a':
                            self.order_by_direction = 'ASC'
                        else:
                            self.order_by_direction = 'DESC'
                        current_arg_counter += 2
                        continue
                elif has_next and next_arg in ['c', 'created','m', 'modified'] and (not has_2nd or next_2nd not in ['a','asc','d','desc']):
                        if next_arg[0] == 'c':
                            self.order_by_column = self.object_cache.get_column(self.db_uniq, self.table, self.features['created_patterns'])
                        else:
                            self.order_by_column = self.object_cache.get_column(self.db_uniq, self.table, self.features['modified_patterns'])
                        current_arg_counter += 2
                        continue
                elif has_2nd:
                    if next_2nd in ['a', 'asc', 'd', 'desc']:
                        if next_arg in ['c', 'created']:
                            self.order_by_column = self.object_cache.get_column(self.db_uniq, self.table, self.features['created_patterns'])
                        elif next_arg in ['m', 'modified']:
                            self.order_by_column = self.object_cache.get_column(self.db_uniq, self.table, self.features['modified_patterns'])
                        else:
                            self.order_by_column = self.object_cache.get_column(self.db_uniq, self.table, next_arg)
                        if not self.order_by_column:
                            raise Exception('Order By column {} not found! Known columns: {}'.format(next_arg, self.column_names))
                        if next_2nd in ['a', 'asc']:
                            self.order_by_direction = 'ASC'
                        else:
                            self.order_by_direction = 'DESC'
                        current_arg_counter += 3
                        continue
                else:
                    self.order_by_column = self.column_names[0]  # 1st col by default TODO use PK
                    continue

            # filters
            # /column/>/val
            # TODO add special keywords like today?
            # TODO add also lt,gt,eq
            if has_next and next_arg in ['<', '<=', '>', '>=', '='] and has_2nd:
                column = self.object_cache.get_column(self.db_uniq, self.table, current_arg)
                self.filters.append((column, next_arg, next_2nd))
                current_arg_counter += 3
                continue

            # simple aggregations
            # count, sum, min, max
            if current_arg == 'agg' and has_2nd and next_arg in ['count', 'sum', 'min', 'max']:
                self.aggregations.append((next_arg, next_2nd))
                current_arg_counter += 3
                continue

            print 'WARNING: did not make use of ', current_arg
            current_arg_counter += 1

    def to_sql(self):   # TODO sql injection analyze. use psycopg2 mogrify?
        sql = 'SELECT '
        if self.aggregations:
            i = 0
            for agg_op, column in self.aggregations:
                sql += ('' if i == 0 else ', ') + agg_op + '(' + column + ')'
                i += 1
        else:
            sql += ', '.join(self.column_names)

        sql += ' FROM ' + self.table
        if self.filters:
            sql += ' WHERE '
            i = 0
            for fcol, fop, fval in self.filters:
                col_full_name = self.object_cache.get_column(self.db_uniq, self.table, fcol)
                if not col_full_name:
                    raise Exception('Column {} not found! Known columns: {}'.format(fcol, self.column_names))
                sql += '{}{} {} {}'.format((' AND ' if i > 0 else ''), col_full_name, fop, fval)
                i += 1
        if not self.aggregations:
            if self.order_by_column:
                sql += ' ORDER BY {} {}'.format(self.order_by_column, self.order_by_direction)
            sql += ' LIMIT {}'.format(self.limit)
        return sql

    def __str__(self):
        return 'UrlParams: db {}, table {}, columns {}, output_format {}'.format(self.db_uniq, self.table,
                                                                                 self.column_names, self.output_format)

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
    up = UrlParams(db_objects_cache, features, 'pos', 'ta*1', 'col1', '<=', '100', 'agg', 'count', 'c1', 'agg', 'max', 'c1')
    print up
    print up.to_sql()
