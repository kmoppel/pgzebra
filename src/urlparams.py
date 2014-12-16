from dbobject_cache import DBObjectsCache

class UrlParams(object):

    def __init__(self, object_cache, features, *args):
        """ :type object_cache : dbobject_cache.DBObjectsCache """
        self.object_cache = object_cache
        self.features = features
        self.db = None
        self.table = None
        self.column_names = []
        self.filters = []     # [(col_short, op, value),]  op: eq/=, gt/>
        self.joinitems = {}
        self.limit = features.get('default_limit', 20)
        self.order_by_direction = features.get('default_order_by', 'DESC')
        self.order_by_column = None

        # return args
        args_count = len(args)
        if args_count < 2:
            raise Exception('Invalid arguments!')   # TODO add more checks, lose 500. separate exception subclass?

        self.db, self.table = object_cache.get_db_and_table_names(args[0], args[1])
        if not (self.db and self.table):
            raise Exception('DB or Table not found!')   # TODO suggest similar tables if only table
        self.column_names = [x['column_name'] for x in object_cache.cache[self.db][self.table]]

        current_arg_counter = 2
        while current_arg_counter < args_count:
            current_arg = args[current_arg_counter].lower()
            next_arg = None
            next_2nd = None
            has_next = args_count > current_arg_counter + 1
            if has_next: next_arg = args[current_arg_counter + 1].lower()
            has_2nd = args_count > current_arg_counter + 2
            if has_2nd: next_2nd = args[current_arg_counter + 2].lower()

            # limit
            if current_arg == 'l' or current_arg == 'limit':
                if has_next and str(next_arg).isdigit():
                    self.limit = next_arg
                    current_arg_counter += 2
                    continue

            # order by
            #   : o/[asc|desc]
            #   : o/[c|m]/[asc|desc]    TODO
            #   : o[rderby]/column/[asc|desc]
            if current_arg == 'o' or current_arg == 'orderby':
                if has_next and next_arg in ['a', 'asc', 'd', 'desc']:
                        self.order_by_column = self.column_names[0]  # 1st col by default TODO use PK
                        if next_arg in ['a', 'asc']:
                            self.order_by_direction = 'ASC'
                        else:
                            self.order_by_direction = 'DESC'
                        current_arg_counter += 2
                        continue
                elif has_2nd:
                    if next_2nd in ['a', 'asc', 'd', 'desc']:
                        self.order_by_column = self.object_cache.get_column(self.db, self.table, next_arg)
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

            #
            # filters
            # if args[current_arg_counter]
            current_arg_counter += 1


    def to_sql(self):
        sql = 'SELECT '
        sql += ', '.join(self.column_names)
        sql += ' FROM ' + self.table
        if self.filters:
            sql += ' WHERE '
            i = 0
            for fcol, fop, fval in self.filters:
                col_full_name = self.object_cache.get_column(self.db, self.table, fcol)
                if not col_full_name:
                    raise Exception('Column {} not found! Known columns: {}'.format(fcol, self.column_names))
                sql += '{}{} {} {}'.format((' AND ' if i > 0 else ''), col_full_name, fop, fval)
                i += 1
        if self.order_by_column:
            sql += ' ORDER BY {} {}'.format(self.order_by_column, self.order_by_direction)
        sql += ' LIMIT {}'.format(self.limit)
        return sql


    def __str__(self):
        return 'db {}, table {}, columns {}'.format(self.db, self.table, self.column_names)


if __name__ == '__main__':
    db_objects_cache = DBObjectsCache()
    db_objects_cache.add_table_to_cache('postgres', 'local', 5432,
                                        'public.table1',
                                        DBObjectsCache.formulate_table(['col1', 'col2']))
    print db_objects_cache

    features = {
        'default_order_by': 'DESC',
        'default_limit': '20',
        'created_patterns': 'created,timestamp,time',
        'modified_patterns': 'modified,updated,timestamp',
    }
    up = UrlParams(db_objects_cache, features, 'pos', 'ta*1', 'l', '100', 'o', 'd')
    up = UrlParams(db_objects_cache, features, 'pos', 'ta*1')
    print up
    print up.to_sql()
    up.filters.append(('col1', '=', '1'))
    up.filters.append(('col1', '=', '1'))
    print up.to_sql()
