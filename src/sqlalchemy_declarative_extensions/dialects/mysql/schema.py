from sqlalchemy import bindparam, column, table

from sqlalchemy_declarative_extensions.sqlalchemy import select

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
    .where(views.c.view_definition.isnot(None))
    .where(views.c.table_schema.notin_(["sys"]))
)

schema_exists_query = select(schemata).where(
    schemata.c.schema_name == bindparam("schema")
)
