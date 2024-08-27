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

routine_table = table(
    "routines",
    column("routine_name"),
    column("routine_definition"),
    column("routine_schema"),
    column("routine_type"),
    column("data_type"),
    column("security_type"),
    column("dtd_identifier"),
    column("is_deterministic"),
    column("sql_data_access"),
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
).where(triggers.c.trigger_schema == bindparam("schema"))

schema_exists_query = select(schemata).where(
    schemata.c.schema_name == bindparam("schema")
)

procedures_query = (
    select(
        routine_table.c.routine_name.label("name"),
        routine_table.c.routine_definition.label("definition"),
        routine_table.c.security_type.label("security"),
    )
    .where(routine_table.c.routine_schema == bindparam("schema"))
    .where(routine_table.c.routine_type == "PROCEDURE")
)

functions_query = (
    select(
        routine_table.c.routine_name.label("name"),
        routine_table.c.routine_definition.label("definition"),
        routine_table.c.security_type.label("security"),
        routine_table.c.dtd_identifier.label("return_type"),
        routine_table.c.is_deterministic.label("deterministic"),
        routine_table.c.sql_data_access.label("data_access"),
    )
    .where(routine_table.c.routine_schema == bindparam("schema"))
    .where(routine_table.c.routine_type == "FUNCTION")
)
