from sqlalchemy import (
    String,
    and_,
    bindparam,
    column,
    literal,
    select,
    table,
    text,
    union,
)
from sqlalchemy.dialects.postgresql import ARRAY

tables = table(
    "tables",
    column("table_schema"),
    column("table_name"),
    schema="information_schema",
)

pg_class = table(
    "pg_class",
    column("oid"),
    column("relname"),
    column("relnamespace"),
    column("relacl"),
    column("relkind"),
    column("relowner"),
)

pg_namespace = table(
    "pg_namespace",
    column("oid"),
    column("nspname"),
    column("nspowner"),
    column("nspacl"),
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

pg_views = table(
    "pg_views",
    column("schemaname"),
    column("viewname"),
    column("definition"),
)

pg_matviews = table(
    "pg_matviews",
    column("schemaname"),
    column("matviewname"),
    column("definition"),
)


roles_query = text(
    """
        SELECT r.rolname, r.rolsuper, r.rolinherit,
          r.rolcreaterole, r.rolcreatedb, r.rolcanlogin,
          r.rolconnlimit, r.rolvaliduntil,
          ARRAY(SELECT b.rolname
                FROM pg_catalog.pg_auth_members m
                JOIN pg_catalog.pg_roles b ON (m.roleid = b.oid)
                WHERE m.member = r.oid) as memberof
        , r.rolreplication
        , r.rolbypassrls
        FROM pg_catalog.pg_roles r
        WHERE r.rolname !~ '^pg_'
        ORDER BY 1;
        """
)


def _schema_not_pg(column=pg_namespace.c.nspname):
    return and_(
        column != "information_schema",
        column.not_like("pg_%"),
    )


_schema_not_public = pg_namespace.c.nspname != "public"
_table_not_pg = pg_class.c.relname.not_like("pg_%")

schemas_query = (
    select(pg_namespace.c.nspname).where(_schema_not_pg()).where(_schema_not_public)
)


schema_exists_query = text(
    "SELECT schema_name FROM information_schema.schemata WHERE schema_name = :schema"
)


table_exists_query = (
    select(tables)
    .where(tables.c.table_schema == bindparam("schema"))
    .where(tables.c.table_name == bindparam("name"))
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

object_acl_query = union(
    select(
        pg_namespace.c.nspname.label("schema"),
        pg_class.c.relname.label("name"),
        pg_class.c.relkind.label("relkind"),
        pg_authid.c.rolname.label("owner"),
        pg_class.c.relacl.cast(ARRAY(String)).label("acl"),
    )
    .select_from(
        pg_class.join(pg_namespace, pg_class.c.relnamespace == pg_namespace.c.oid).join(
            pg_authid, pg_class.c.relowner == pg_authid.c.oid
        )
    )
    .where(pg_class.c.relkind.in_(["r", "S", "f", "n", "T", "v"]))
    .where(_table_not_pg)
    .where(_schema_not_pg()),
    select(
        literal(None).label("schema"),
        pg_namespace.c.nspname.label("name"),
        literal("n").label("relkind"),
        pg_authid.c.rolname.label("owner"),
        pg_namespace.c.nspacl.cast(ARRAY(String)),
    )
    .select_from(
        pg_namespace.join(pg_authid, pg_namespace.c.nspowner == pg_authid.c.oid)
    )
    .where(_schema_not_pg())
    .where(_schema_not_public),
)

objects_query = (
    select(
        pg_namespace.c.nspname.label("schema"),
        pg_class.c.relname.label("object_name"),
        pg_class.c.relkind.label("relkind"),
    )
    .select_from(
        pg_class.join(pg_namespace, pg_class.c.relnamespace == pg_namespace.c.oid)
    )
    .where(pg_class.c.relkind.in_(["r", "S", "f", "n", "T", "v"]))
    .where(_table_not_pg)
    .where(_schema_not_pg())
)

views_query = union(
    select(
        pg_views.c.schemaname.label("schema"),
        pg_views.c.viewname.label("name"),
        pg_views.c.definition.label("definition"),
        literal(False).label("materialized"),
    ).where(_schema_not_pg(pg_views.c.schemaname)),
    select(
        pg_matviews.c.schemaname.label("schema"),
        pg_matviews.c.matviewname.label("name"),
        pg_matviews.c.definition.label("definition"),
        literal(True).label("materialized"),
    ).where(_schema_not_pg(pg_matviews.c.schemaname)),
)
