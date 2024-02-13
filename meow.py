# DONE: roles-as-references i.e. in_roles=[skeptic_reader]
# DONE: external roles
# DONE: with blocks for role usage
# POC: Snowflake-specific role definition
# TODO: snowflake-specific schema managed_access
# TODO: Grants/Future Grants
# TODO: declarative databases
# from sqlalchemy_declarative_extensions import Database
from sqlalchemy_declarative_extensions import Roles
from sqlalchemy_declarative_extensions.dialects.snowflake import (
    FutureGrant,
    Grant,
    Schema,
    Role,
)
from sqlalchemy_declarative_extensions.schema.base import Schemas

sysadmin = Role("sysadmin", external=True)
securityadmin = Role("securityadmin", external=True)

# with sysadmin:
#     skeptic = Database("skeptic")

with securityadmin:
    skeptic_reader = Role("test$reader")
    skeptic_writer = Role("test$writer", in_roles=[skeptic_reader])
    skeptic_admin = Role("test$admin", in_roles=[sysadmin, skeptic_writer])

    Grant("all", to=skeptic_admin).on_database(skeptic)
    FutureGrant.on_schemas_in_database(skeptic).grant("all", to=skeptic_admin)

googleads_schema = Schema("googleads", managed_access=True)

roles = Roles(ignore_unspecified=True).are(
    sysadmin, securityadmin, skeptic_reader, skeptic_writer, skeptic_admin
)
schemas = Schemas(ignore_unspecified=True).are(googleads_schema)

# isort: skip
# ruff: noqa
import base64
import os
from sqlalchemy import MetaData, create_engine
from sqlalchemy_declarative_extensions import declare_database
from sqlalchemy_declarative_extensions.role.compare import compare_roles
from sqlalchemy_declarative_extensions.schema.compare import compare_schemas
from sqlalchemy_declarative_extensions.grant.compare import compare_grants
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from snowflake.sqlalchemy import URL as SnowflakeURL

p_key = serialization.load_pem_private_key(
    base64.b64decode(os.environ["SNOWFLAKE_PRIVATE_KEY"]),
    password=os.environ["SNOWFLAKE_PRIVATE_KEY_PASSWORD"].encode(),
    backend=default_backend(),
)

private_key_bytes = p_key.private_bytes(
    encoding=serialization.Encoding.DER,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
)

url = SnowflakeURL(
    account=os.environ["SNOWFLAKE_ACCOUNT"],
    user=os.environ["SNOWFLAKE_USERNAME"],
    database=os.environ["SNOWFLAKE_DATABASE"],
    role=os.environ["SNOWFLAKE_ROLE"],
    warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
)
engine = create_engine(url, connect_args={"private_key": private_key_bytes})

metadata = MetaData()
declare_database(metadata, roles=roles, schemas=schemas)

with engine.connect() as conn:
    for op in compare_roles(conn, metadata.info["roles"]):
        for statement in op.to_sql():
            print(statement)
            print()

    for op in compare_schemas(conn, metadata.info["schemas"]):
        statement = op.to_sql()
        print(statement)
        print()

    for op in compare_grants(conn, metadata.info["grants"]):
        statement = op.to_sql()
        print(str(statement))
        print()
