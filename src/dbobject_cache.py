import re


db_objects_cache = None   # global cache for table/column names, FKs
"""
{
'db1:host:port': {'sch1.table1': [ { 'column_name': 'col1', 'is_pk': True, 'fks':[{'tableref':'tblx', 'colref'}, ] }}}
}
"""

class DBObjectsCache(object):

    def __init__(self):
        self.cache = {}

    def add_table_to_cache(self, host, port, db, table_name, table_info):
        db_uniq = '{}:{}:{}'.format(host, port, db)
        if db_uniq not in self.cache:
            self.cache[db_uniq] = {}
        self.cache[db_uniq][table_name] = table_info   # just overwriting without warning for now


    @staticmethod
    def formulate_table(columns):   # TODO extend
        columns_with_additional_info = []
        for col in columns:
            columns_with_additional_info.append({'column_name': col, 'is_pk': False, 'fks': None})
        return columns_with_additional_info

    def get_dbuniq_and_table_full_name(self, db_short, table_short=None):
        ret_db = None
        ret_table = None

        db_pattern = re.compile(db_short.replace('*', '.*'))
        for db_uniq in self.cache:
            # print 'db_uniq', db_uniq
            if db_pattern.search(db_uniq):
                if not ret_db or len(ret_db) > db_uniq:     # taking the shortest. TODO add warning in UI
                    ret_db = db_uniq
                if not table_short:
                    continue
                table_pattern = re.compile(table_short.replace('*', '.*'))
                for full_table_name in self.cache[ret_db]:
                    if table_pattern.search(full_table_name):
                        if not ret_table or len(full_table_name) > ret_table:
                            ret_table = full_table_name

        return ret_db, ret_table

    def get_all_tables_for_dbuniq(self, dbuniq):
        return self.cache[dbuniq].keys()

    def get_column_single(self, db, table, col_short):
        """ matches fragments to full name. shortest match wins. can be a list of comma separated names"""
        ret_col = None
        col_short_patterns = col_short.lower().split(',')

        for col_pattern in col_short_patterns:
            col_pattern = re.compile(col_pattern.replace('*', '.*'))
            for col in self.cache[db][table]:
                col_name = col['column_name']
                if col_pattern.search(col_name):
                    if not ret_col or len(ret_col) > col_name:     # taking the shortest. TODO add warning in UI
                        ret_col = col_name

        return ret_col

    def get_column_multi(self, db, table, col_short):
        """ matches fragments to full name. returns multiple columns preserving order. shortest match wins. can be a list of comma separated names"""
        ret_col = []
        col_short_patterns = col_short.lower().split(',')

        for col_pattern in col_short_patterns:
            col_name = self.get_column_single(db, table, col_pattern)
            if col_name and col_name not in ret_col:
                ret_col.append(col_name)
                continue

        return ret_col


    def __str__(self):
        return str(self.cache)



if __name__ == '__main__':
    db_objects_cache = DBObjectsCache()
    # print DBObjectsCache.formulate_table(['col1', 'col2'])
    db_objects_cache.add_table_to_cache('local', 5432, 'postgres',
                                        'public.table1',
                                        DBObjectsCache.formulate_table(['col1', 'col2']))
    print db_objects_cache
    print db_objects_cache.get_dbuniq_and_table_full_name('pos', 'ta*1')
    print db_objects_cache.get_column_multi('local:5432:postgres', 'public.table1', 'col1,col2')