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


## Input syntax [ URL based ]


#### Basic usage

` / somedb / sometable `


#### Filtering

` / somedb / sometable / somecolumn / comparison_operator / value `

* all URL segments of 3 [when 1st seg. not conflicting with a few reserved keywords ] are handled as filter
* multiple filters possible
* for date columns some special shortcuts can be used

    - current_month (beginning date), current_week (beginning date), current_day/current_date, current_timestamp/now
    - -/+X(days|hours|minutes|seconds)  e.g. - / created / >= /-5days => WHERE order_created >= current_date - '5 days'::interval

#### Limiting

` / somedb / sometable / l[imit] / value `


#### Ordering

` / somedb / sometable / o[rderby] ` - 1st column will be used + default sort order from the config

` / somedb / sometable / o[rderby] / [ a[sc] | d[esc] ] ` - 1st column with explicit ordering

` / somedb / sometable / o[rderby] / somecol / [ a[sc] | d[esc] ] ` - single column ordering with explicit ordering

` / somedb / sometable / o[rderby] / somecol1[,somecol2,..] ` - multicolumn ordering


#### Simple aggregations

` / somedb / sometable / agg / agg_func / somecol ` - where agg_func in ['count', 'sum', 'min', 'max']


#### Simple graphing

###### Line graph of single column's counts over time, with month to minute grouping ($graphbucket param). The $graphkey column needs to be of type date/timestamp!

` / somedb / sometable / f[ormat] / g[raph] / l[ine] / [ gk | graphkey] / temporal_col / [ gb | graphbucket ] / [month|day|hour|min|minute] `

###### Pie graph showing distribution of provided column's values. The column can be of any type.

` / somedb / sometable / f[ormat] / g[raph] / p[pie] / [ gk | graphkey] / somecol `

` / somedb / sometable / f[ormat] / g[raph] / p[pie] / [ gk | graphkey] / somecol / l[imit] / value`

**NB! For aggregates and graphs also filters can (and should) be used.** For pie graphs "limit" also works.


## Output formats

* HTML table [ default ]
* JSON - ` / f[ormat] / j[son] `
* CSV - ` / f[ormat] / c[sv] `
* Graph - HTML + JS based - ` / f[ormat] / g[raph] `
* Graph - pure PNG ` / f[ormat] / png `


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


**/somedb/order/o/a**

> SELECT o_id,colX,.. FROM schema.order_history ORDER BY o_id ASC LIMIT 10

Simple select with ascending primary key ordering [given that PK is the 1st columns]


**/somedb/order/agg/count/id/created/>/current_date**

> SELECT count(o_id) FROM schema.order_history WHERE oh_created > current_date

Simple aggregates support is provided. Multiple aggregates can be used in one query.

* count
* sum
* min
* max


**/somedb/order/f/g/line/gk/created/gb/month/created/>/current_date**

> SELECT date_trunc('month', oh_created), count(*) FROM order_history WHERE oh_created > current_date GROUP BY 1 ORDER BY 1

Displays a "line graph" of counts of "graphkey" over timeslots specified by "graphbucket" column. Filtering is possible as usual.

NB! Missing buckets will be filled with 0-s.


**/somedb/order/f/g/pie/gk/country/created/>/current_date**

> SELECT oh_country, count(*) FROM order_history WHERE oh_created > current_date GROUP BY 1 ORDER BY 2 DESC LIMIT 10

NB! Displays a "pie graph" of $graphkey's distribution. Values not fitting into "limit" will be summarized into "Other".
