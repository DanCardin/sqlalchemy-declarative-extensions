from sqlalchemy import bindparam, column, select, table

views = table(
    "views",
    column("table_schema"),
    column("table_name"),
    column("view_definition"),
    schema="INFORMATION_SCHEMA",
)

tables = table(
    "tables",
    column("table_schema"),
    column("table_name"),
    schema="information_schema",
)

schemata = table(
    "schemata",
    column("schema_name"),
    schema="information_schema",
)

views_query = (
    select(
        views.c.table_schema.label("schema"),
        views.c.table_name.label("name"),
        views.c.view_definition.label("definition"),
    )
    .where(views.c.view_definition.is_not(None))
    .where(views.c.table_schema.not_in(["sys"]))
)

table_exists_query = (
    select(tables)
    .where(tables.c.table_schema == bindparam("schema"))
    .where(tables.c.table_name == bindparam("name"))
)

schema_exists_query = select(schemata).where(
    schemata.c.schema_name == bindparam("schema")
)
