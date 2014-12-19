pgzebra
=======

Simple RESTful interface to single PostgreSQL tables.

It's a simplistic URL-based data viewing and graphing tool that is easy to setup and use, reflecting table data in a REST-ful way. Only a single table's data is shown at one time. 
Idea also tries to minimize typing by providing some convenience features like matching of db/table names from partially inputted names + default sorting and limiting.

Techology stack: Python (CherryPy web framework, Jinja2 templates, Pygal graphing) + jQuery + Bootstrap + DataTables + Flot Charts

Sample inputs and outputs (in a datagrid):
 
 * Input:
    /somedb/tablename  - the simplest usecase. database/table names don't have to be precise, 1st matching column is used. as a wildcard '*' can be used
    
 Output:
    SELECT col1,colX,.. FROM schema.table_full_name LIMIT 20
  
  * input:
    /somedb/order/created/>/current_data/orderby/created/limit/10
    
  Output:
    SELECT col1,colX,.. FROM schema.order_history WHERE oh_created > current_date ORDER BY o_created DESC LIMIT 10
  

