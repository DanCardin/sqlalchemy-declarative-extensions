from sqlalchemy import bindparam, column, table

from sqlalchemy_declarative_extensions.sqlalchemy import select

schemata = table(
    "schemata",
    column("schema_name"),
    schema="information_schema",
)

schema_exists_query = select(schemata).where(
    schemata.c.schema_name == bindparam("schema")
)

schemas_query = select(schemata).where(schemata.c.schema_name != "INFORMATION_SCHEMA")
