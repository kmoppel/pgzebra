pgzebra
=======

Simple RESTful interface to single PostgreSQL tables.

It's a simplistic URL-based data viewing and graphing tool that is easy to setup and use, reflecting table data in a REST-ful way. Only a single table's data is shown at one time. 
Idea also tries to minimize typing by providing some convenience features like matching of db/table names from partially inputted names + default sorting and limiting.

## Techology stack

* Python2
    - CherryPy web framework
    - Jinja2 templating
    - psycopg2 Postgresql driver
    - Pygal for png graphing (optional)
    - pyyaml for parsing the webapp's config file
* jQuery
* DataTables - jQuery plugin for sortable/searchable/pageable tables
* Flot Charts
* Bootstrap

## Sample inputs and outputs (output of query by default shown in the datagrid)
 
**/somedb/tablename_excerpt**

The simplest usecase. database/table names don't have to be precise, only excerpts will do, given they're precise enough to uniquely identify a table 1st matching column is used. as a wildcard '*' can be used

> SELECT col1,colX,.. FROM schema.table_full_name LIMIT 20


**/somedb/order/created/>/current_date**
    
> SELECT col1,colX,.. FROM schema.order_history WHERE oh_created > current_date LIMIT 10

Usage of filtering. All groups of 3 parameters [starting with non-reserved keywords] are handled as filters. Multiple filters possible.

WARNING! Currently filters are passed to the DB "as is" i.e. SQL injection is possible.

**/somedb/order/created/>/current_date/o/c**
    
> SELECT col1,colX,.. FROM schema.order_history WHERE oh_created > current_date ORDER BY o_created DESC LIMIT 10

NB! "/o/c" i.e. "o[rderby] / [c[reated]|m[odified]]" is a Pgzebra concept of ordering by first column matching predefined [see pgzebra.yaml] created/modified patterns

Default "LIMIT" (here 10) comes also from the pgzebra.yaml


**/somedb/order/created/>/current_date/orderby/created/l/10**

> SELECT col1,colX,.. FROM schema.order_history WHERE oh_created > current_date ORDER BY o_created DESC LIMIT 10

The same as previous in longer format + explicit "LIMIT". NB! Default "ORDER BY" direction is "DESC" - can be changed from config file


**/somedb/order/o/a[sc]**

> SELECT o_id,colX,.. FROM schema.order_history ORDER BY o_id ASC LIMIT 10

Simple select with ascending primary key ordering [given that PK is the 1st columns]


**/somedb/order/agg/count/id/created/>/current_date**

> SELECT count(o_id) FROM schema.order_history WHERE oh_created > current_date

Simple aggregates support is provided. Multiple aggregates can be used in one query.

* count
* sum
* min
* max


** / somedb / order / f[ormat] / g[raph] / line / [gk|graphkey] / created / [gb|graphbucket] / [month|day|hour|min|minute] / created / > / current_date

> SELECT ...

Displays a "line graph" of counts of "graphkey" over time.