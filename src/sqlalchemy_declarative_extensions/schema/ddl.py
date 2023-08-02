from sqlalchemy.schema import CreateSchema

from sqlalchemy_declarative_extensions.dialects import check_schema_exists
from sqlalchemy_declarative_extensions.schema import Schema


def schema_ddl(schema: Schema):
    ddl = CreateSchema(schema.name)
    return ddl.execute_if(callable_=check_schema)


def check_schema(ddl, target, connection, **_):
    schema = ddl.element
    return check_schema_exists(connection, name=schema)
