from sqlalchemy import text
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.elements import TextClause


def clear_roles(engine):
    roles = engine.execute(
        text(
            "SELECT rolname from pg_roles "
            "WHERE rolname != 'user' "
            "AND rolname not like 'pg_%'"
            "ORDER BY rolname"
        )
    )

    connected_name = engine.pmr_credentials.username
    for role, *_ in roles:
        engine.execute(text(f'REASSIGN OWNED BY {role} TO "{connected_name}"'))
        engine.execute(text(f"DROP ROLE {role}"))


def render_sql(text: TextClause) -> str:
    statement = text.compile(
        dialect=postgresql.dialect(),  # type: ignore
        compile_kwargs={"literal_binds": True},
    )
    return str(statement)


def successful_test_run(pytester, *, count=None, skipped_count=0, in_process=False):
    pytester.copy_example()
    result = pytester.inline_run("-vv", "--capture=no", "--log-cli-level=WARNING")
    result.assertoutcome(passed=count, skipped=skipped_count, failed=0)
