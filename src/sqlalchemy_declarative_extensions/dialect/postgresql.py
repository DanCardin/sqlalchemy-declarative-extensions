from sqlalchemy import column, select, String, table
from sqlalchemy.dialects.postgresql import ARRAY

pg_namespace = table(
    "pg_namespace",
    column("oid"),
    column("nspname"),
)

pg_roles = table(
    "pg_roles",
    column("oid"),
    column("rolname"),
)

pg_default_acl = table(
    "pg_default_acl",
    column("defaclrole"),
    column("defaclnamespace"),
    column("defaclobjtype"),
    column("defaclacl"),
)

pg_authid = table(
    "pg_authid",
    column("oid"),
    column("rolname"),
)


default_acl_query = select(
    pg_authid.c.rolname.label("role_name"),
    pg_namespace.c.nspname.label("schema_name"),
    pg_default_acl.c.defaclobjtype.label("object_type"),
    pg_default_acl.c.defaclacl.cast(ARRAY(String)).label("acl"),
).select_from(
    pg_default_acl.join(pg_authid, pg_default_acl.c.defaclrole == pg_authid.c.oid).join(
        pg_namespace, pg_default_acl.c.defaclnamespace == pg_namespace.c.oid
    )
)
