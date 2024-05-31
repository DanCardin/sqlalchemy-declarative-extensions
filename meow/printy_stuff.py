from sqlalchemy_declarative_extensions.database.compare import compare_databases
from sqlalchemy_declarative_extensions.grant.compare import compare_grants
from sqlalchemy_declarative_extensions.role.compare import compare_roles
from sqlalchemy_declarative_extensions.schema.compare import compare_schemas


def print_sql(engine, metadata):
    with engine.connect() as conn:
        for op in compare_databases(conn, metadata.info["databases"]):
            for statement in op.to_sql():
                print(str(statement))
        print()

        role_ops = compare_roles(conn, metadata.info["roles"])
        for op in role_ops:
            for statement in op.to_sql():
                print(statement)
        print()

        for op in compare_grants(conn, metadata.info["grants"]):
            for statement in op.to_sql():
                print(str(statement))
        print()

        for op in compare_schemas(conn, metadata.info["schemas"]):
            for statement in op.to_sql():
                print(statement)
        print()
