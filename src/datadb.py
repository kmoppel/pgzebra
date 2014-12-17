import psycopg2
import psycopg2.extras

from dbobject_cache import DBObjectsCache


object_cache = None
''' :type object_cache: DBObjectsCache'''
db_credentials = {}


def execute_on_host(hostname, port, dbname, user, password, sql, params=None):
    data = []
    conn = None
    if user is None and password is None:
        user, password = db_credentials['{}:{}:{}'.format(dbname, hostname, port)]
    try:
        conn = psycopg2.connect(host=hostname, port=port, dbname=dbname, user=user, password=password, connect_timeout='3')
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql, params)
        data = cur.fetchall()
    except Exception as e:
        print 'ERROR execution failed on {}:{} - {}'.format(hostname, port, e.message)
    finally:
        if conn and not conn.closed:
            conn.close()
    return data


def execute_on_db_uniq(db_uniq, sql, params=None):
    """ db_uniq = dbname:hostname:port """
    data = []
    column_names = []
    conn = None
    user, password = db_credentials[db_uniq]
    hostname = db_uniq.split(':')[0]
    port = db_uniq.split(':')[1]
    dbname = db_uniq.split(':')[2]
    try:
        conn = psycopg2.connect(host=hostname, port=port, dbname=dbname, user=user, password=password, connect_timeout='3')
        # cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur = conn.cursor()
        cur.execute(sql, params)
        data = cur.fetchall()
        column_names = [x[0] for x in cur.description]
    except Exception as e:
        print 'ERROR execution failed on {}:{} - {}'.format(hostname, port, e.message)
    finally:
        if conn and not conn.closed:
            conn.close()
    return data, column_names


def get_column_info(dbuniq, table_name, column_names):
    ret = []
    for cn in column_names:
        ci = {'column_name': cn}
        for cache_info in object_cache.cache[dbuniq][table_name]:
            if cn == cache_info['column_name']:
                ci = cache_info
                break
        ret.append(ci)
    return ret


def get_list_of_dbs_on_instance(host, port, db, user, password):
    sql = """select datname from pg_database where not datistemplate and datname != 'postgres'"""
    return [x['datname'] for x in execute_on_host(host, port, db, user, password, sql)]


def add_db_to_object_cache(object_cache, host, port, db, user, password, tables=True, views=False):
    sql = """
    select
     quote_ident(t.table_schema)||'.'||quote_ident(t.table_name) as full_table_name,
     array_agg(c.column_name::text order by ordinal_position) as columns
    from
      information_schema.tables t
      left join
      information_schema.columns c
      on t.table_schema = c.table_schema and t.table_name = c.table_name
    where
      t.table_type = ANY(%s)
      and not t.table_schema in ('information_schema', 'pg_catalog')
    group by
      1
    """
    table_type = []
    if tables: table_type.append('BASE TABLE')
    if views: table_type.append('VIEW')
    if len(table_type) == 0:
        raise Exception('Views and/or Tables exposing must be enabled!')

    data = execute_on_host(host, port, db, user, password, sql, (table_type,))
    for td in data:
        # print td
        object_cache.add_table_to_cache(host, port, db,
                                        td['full_table_name'], DBObjectsCache.formulate_table(td['columns']))   # TODO
        db_credentials['{}:{}:{}'.format(host, port, db)] = (user, password)


def initialize_db_object_cache(settings):
    """
    read and store all tables/columns for all db
    """
    expose_tables = settings['features'].get('expose_tables', True)
    expose_views = settings['features'].get('expose_views', False)
    expose_all_dbs = settings['features'].get('expose_all_dbs', True)
    instances = settings['instances']

    global object_cache
    ''' :type : DBObjectsCache'''
    if not object_cache:
        object_cache = DBObjectsCache()

    for inst_name, inst_data in instances.iteritems():

        if not expose_all_dbs and 'databases' not in inst_data:
            raise Exception('Explicit list of allowed DBs needed for {}'.format(inst_name))

        dbs = []
        if 'databases' not in inst_data:
            dbs = get_list_of_dbs_on_instance(inst_data['hostname'], inst_data['port'], 'postgres',
                                              inst_data['user'], inst_data['password'])
        else:
            dbs = inst_data['databases']

        for db in dbs:
            print 'initializing cache for cluster {}, db {}'.format(inst_name, db)
            add_db_to_object_cache(object_cache, inst_data['hostname'], inst_data['port'], db,
                                         inst_data['user'], inst_data['password'],
                                         expose_tables, expose_views)


if __name__ == '__main__':
    # print get_list_of_dbs_on_instance('localhost', 5432, 'postgres', 'postgres', 'postgres')
    object_cache = DBObjectsCache()
    add_db_to_object_cache(object_cache, 'localhost', 5432, 'postgres', 'postgres', 'postgres')
    print object_cache
    print object_cache.get_dbuniq_and_table_full_name('pos', 'fk')