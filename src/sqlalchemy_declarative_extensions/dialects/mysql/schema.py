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

triggers = table(
    "triggers",
    column("trigger_schema"),
    column("trigger_name"),
    column("action_timing"),
    column("event_manipulation"),
    column("event_object_table"),
    column("action_statement"),
    schema="INFORMATION_SCHEMA",
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

triggers_query = select(
    triggers.c.trigger_schema.label("schema"),
    triggers.c.trigger_name.label("name"),
    triggers.c.action_timing.label("time"),
    triggers.c.event_manipulation.label("event"),
    triggers.c.event_object_table.label("on_name"),
    triggers.c.action_statement.label("statement"),
).where(triggers.c.trigger_schema != "sys")

schema_exists_query = select(schemata).where(
    schemata.c.schema_name == bindparam("schema")
)
