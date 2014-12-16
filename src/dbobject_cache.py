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

    def add_table_to_cache(self, db, host, port, table_name, table_info):
        db_uniq = '{}:{}:{}'.format(db, host, port)
        if db_uniq not in self.cache:
            self.cache[db_uniq] = {}
        self.cache[db_uniq][table_name] = table_info   # just overwriting without warning for now


    @staticmethod
    def formulate_table(columns):   # TODO extend
        columns_with_additional_info = []
        for col in columns:
            columns_with_additional_info.append({'column_name': col, 'is_pk': False, 'fks': None})
        return columns_with_additional_info

    def get_db_and_table_names(self, db_short, table_short):
        ret_db = None
        ret_table = None

        db_pattern = re.compile(db_short.replace('*', '.*'))
        for db_uniq in self.cache:
            if db_pattern.search(db_uniq):
                if not ret_db or len(ret_db) > db_uniq:     # taking the shortest. TODO add warning in UI + sorting
                    ret_db = db_uniq
                table_pattern = re.compile(table_short.replace('*', '.*'))
                for full_table_name in self.cache[ret_db]:
                    if table_pattern.search(full_table_name):
                        if not ret_table or len(full_table_name) > ret_table:
                            ret_table = full_table_name

        return ret_db, ret_table

    def get_column(self, db, table, col_short):
        ret_col = None

        col_pattern = re.compile(col_short.replace('*', '.*'))
        for col in self.cache[db][table]:
            col_name = col['column_name']
            if col_pattern.search(col_name):
                if not ret_col or len(ret_col) > col_name:     # taking the shortest. TODO add warning in UI + sorting
                    ret_col = col_name

        return ret_col


    def __str__(self):
        return str(self.cache)



if __name__ == '__main__':
    db_objects_cache = DBObjectsCache()
    # print DBObjectsCache.formulate_table(['col1', 'col2'])
    db_objects_cache.add_table_to_cache('postgres', 'local', 5432,
                                        'public.table1',
                                        DBObjectsCache.formulate_table(['col1', 'col2']))
    print db_objects_cache
    print db_objects_cache.get_db_and_table_names('pos', 'ta*1')