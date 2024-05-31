# DONE: roles-as-references i.e. in_roles=[skeptic_reader]
# DONE: external roles
# DONE: with blocks for role usage
# DONE: snowflake-specific schema managed_access
# DONE: declarative databases
# POC: Snowflake-specific role definition
# POC: Grants / Default Grants
from sqlalchemy import MetaData
from sqlalchemy_declarative_extensions import declare_database
from sqlalchemy_declarative_extensions import Roles, Databases, Database, Schemas
from sqlalchemy_declarative_extensions.dialects.snowflake import (
    DefaultGrant,
    Grant,
    Schema,
    Role,
    SchemaGrants,
    DatabaseGrants,
    TableGrants,
    TaskGrants,
)

# grant role skeptic$reader to role sysadmin;
sysadmin = Role("sysadmin", in_roles=["skeptic$reader"], external=True)
securityadmin = Role("securityadmin", external=True)

with sysadmin:
    skeptic = Database("skeptic")

with securityadmin:
    skeptic_reader = Role("skeptic$reader")
    skeptic_writer = Role("skeptic$writer", in_roles=[skeptic_reader])
    skeptic_admin = Role("skeptic$admin", in_roles=[sysadmin, skeptic_writer])

    grants = [
        # grant usage, operate on warehouse skeptic_wh to role skeptic$reader;
        Grant.new("usage", to=skeptic_reader).on_warehouses("skeptic_wh"),
        # grant usage on database skeptic to role skeptic$reader;
        Grant.new(DatabaseGrants.usage, to=skeptic_reader).on_databases("skeptic"),
        # grant usage on  schemas in database skeptic to role skeptic$reader;
        DefaultGrant.on_schemas_in_database("skeptic").grant(
            SchemaGrants.usage, to=skeptic_reader
        ),
        # grant USAGE on  functions in database skeptic to role skeptic$reader;
        DefaultGrant.on_functions_in_database("skeptic").grant(
            "usage", to=skeptic_reader
        ),
        # grant USAGE on  PROCEDURES in database skeptic to role skeptic$reader;
        DefaultGrant.on_procedures_in_database("skeptic").grant(
            "usage", to=skeptic_reader
        ),
        # grant select, references on  TABLES in database skeptic to role skeptic$reader;
        DefaultGrant.on_schemas_in_database("skeptic").grant(
            TableGrants.select, TableGrants.references, to=skeptic_reader
        ),
        # grant monitor on  TASKS in database skeptic to role skeptic$reader;
        DefaultGrant.on_tasks_in_database("skeptic").grant(
            TaskGrants.monitor, to=skeptic_reader
        ),
        # grant select, references on  VIEWS in database skeptic to role skeptic$reader;
        DefaultGrant.on_views_in_database("skeptic").grant(
            "select", "references", to=skeptic_reader
        ),
        # grant usage, read on  stages in database skeptic to role skeptic$reader;
        DefaultGrant.on_stages_in_database("skeptic").grant(
            "usage", "read", to=skeptic_reader
        ),
        # grant usage on  file formats in database skeptic to role skeptic$reader;
        DefaultGrant.on_file_formats_in_database("skeptic").grant(
            "usage", to=skeptic_reader
        ),
        # grant select on  streams in database skeptic to role skeptic$reader;
        DefaultGrant.on_streams_in_database("skeptic").grant(
            "select", to=skeptic_reader
        ),
    ]

with skeptic_admin:
    googleads_schema = Schema("googleads", managed_access=True)

roles = Roles(ignore_unspecified=True).are(
    sysadmin, securityadmin, skeptic_reader, skeptic_writer, skeptic_admin
)
schemas = Schemas(ignore_unspecified=True).are(googleads_schema)
databases = Databases(ignore_unspecified=True).are(skeptic)

metadata = MetaData()
declare_database(
    metadata,
    roles=roles,
    schemas=schemas,
    grants=grants,
    databases=databases,
)

# ruff: noqa
from meow.snowflake_stuff import engine
from meow.printy_stuff import print_sql

print_sql(engine, metadata)
